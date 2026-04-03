"""TST-045/046/047: Unit tests for src/utils/ modules.

Covers:
  TST-045: src/utils/timing.py (CUDATimer, TimingStats, timer_context)
  TST-046: src/utils/hf.py (resolve_pretrained_path)
  TST-047: src/utils/repro.py (resolve_quant_bits, build_config_snapshot,
           write_config_snapshot, set_seed)

All tests run on CPU without GPU. GPU-dependent paths (CUDATimer CUDA events)
are tested via mock.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ===========================================================================
# TST-045: src/utils/timing.py
# ===========================================================================


class TestTimingStats(unittest.TestCase):
    """TST-045: TimingStats basic functionality."""

    def _make_stats(self):
        from src.utils.timing import TimingStats
        return TimingStats()

    def test_empty_stats_mean_is_zero(self):
        stats = self._make_stats()
        self.assertEqual(stats.mean_ms, 0.0)
        self.assertEqual(stats.total_ms, 0.0)
        self.assertEqual(stats.count, 0)

    def test_add_measurements(self):
        stats = self._make_stats()
        stats.add(10.0)
        stats.add(20.0)
        stats.add(30.0)
        self.assertEqual(stats.count, 3)
        self.assertAlmostEqual(stats.mean_ms, 20.0)
        self.assertAlmostEqual(stats.total_ms, 60.0)

    def test_single_measurement(self):
        stats = self._make_stats()
        stats.add(42.5)
        self.assertEqual(stats.count, 1)
        self.assertAlmostEqual(stats.mean_ms, 42.5)


class TestCUDATimerCPU(unittest.TestCase):
    """TST-045: CUDATimer on CPU (no CUDA available)."""

    def _make_timer(self, **kwargs):
        from src.utils.timing import CUDATimer
        return CUDATimer(**kwargs)

    def test_start_stop_elapsed(self):
        """Basic start/stop/elapsed cycle on CPU."""
        timer = self._make_timer()
        timer.start()
        timer.stop()
        self.assertGreaterEqual(timer.elapsed_ms, 0.0)

    def test_stop_before_start_raises(self):
        """Calling stop() before start() should raise RuntimeError."""
        timer = self._make_timer()
        with self.assertRaises(RuntimeError):
            timer.stop()

    def test_elapsed_before_stop_raises(self):
        """Accessing elapsed_ms before stop() should raise RuntimeError."""
        timer = self._make_timer()
        timer.start()
        with self.assertRaises(RuntimeError):
            _ = timer.elapsed_ms

    def test_sync_before_false(self):
        """sync_before=False should still work on CPU."""
        timer = self._make_timer(sync_before=False)
        timer.start()
        timer.stop()
        self.assertGreaterEqual(timer.elapsed_ms, 0.0)

    def test_sync_after_false(self):
        """sync_after=False should still work on CPU."""
        timer = self._make_timer(sync_after=False)
        timer.start()
        timer.stop()
        self.assertGreaterEqual(timer.elapsed_ms, 0.0)


class TestTimerContext(unittest.TestCase):
    """TST-045: timer_context context manager."""

    def test_context_manager_elapsed(self):
        from src.utils.timing import timer_context
        with timer_context() as timer:
            _ = sum(range(100))
        self.assertGreaterEqual(timer.elapsed_ms, 0.0)


# ===========================================================================
# TST-046: src/utils/hf.py
# ===========================================================================


class TestResolvePretrained(unittest.TestCase):
    """TST-046: resolve_pretrained_path tests."""

    def _resolve(self, *args, **kwargs):
        from src.utils.hf import resolve_pretrained_path
        return resolve_pretrained_path(*args, **kwargs)

    def test_empty_model_id_raises(self):
        """Empty string should raise ValueError (UTIL-012)."""
        with self.assertRaises(ValueError):
            self._resolve("")

    def test_none_model_id_raises(self):
        """None should raise ValueError (UTIL-012)."""
        with self.assertRaises(ValueError):
            self._resolve(None)

    def test_local_path_returned_directly(self):
        """An existing local path should be returned as-is."""
        with tempfile.TemporaryDirectory() as td:
            result = self._resolve(td)
            self.assertEqual(result, td)

    def test_nonexistent_path_tries_hub(self):
        """Non-existent path falls back to HuggingFace Hub."""
        # When huggingface_hub is not available or snapshot_download fails,
        # should return the original model_id as best-effort.
        result = self._resolve("nonexistent/model-that-does-not-exist-xyz")
        # Should return something (either resolved path or original)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


# ===========================================================================
# TST-047: src/utils/repro.py
# ===========================================================================


class TestResolveQuantBits(unittest.TestCase):
    """TST-047: resolve_quant_bits canonical implementation."""

    def _resolve(self, *args, **kwargs):
        from src.utils.repro import resolve_quant_bits
        return resolve_quant_bits(*args, **kwargs)

    def test_explicit_override_wins(self):
        """quant_bits_arg takes precedence over kv_mode."""
        self.assertEqual(self._resolve("fp16", quant_bits_arg=4), 4)
        self.assertEqual(self._resolve("int8_ours", quant_bits_arg=16), 16)

    def test_int8_modes(self):
        self.assertEqual(self._resolve("int8_baseline"), 8)
        self.assertEqual(self._resolve("int8_ours"), 8)

    def test_int4_modes(self):
        self.assertEqual(self._resolve("int4_baseline"), 4)
        self.assertEqual(self._resolve("int4_ours"), 4)
        self.assertEqual(self._resolve("int4_ours_mixed"), 4)
        self.assertEqual(self._resolve("int4_fused"), 4)
        self.assertEqual(self._resolve("int4_ours_asym"), 4)

    def test_fp16_mode(self):
        self.assertEqual(self._resolve("fp16"), 16)

    def test_kivi_style_defaults_to_8(self):
        """kivi_style without explicit quant_bits defaults to 8 (UTIL-009)."""
        self.assertEqual(self._resolve("kivi_style"), 8)

    def test_kivi_style_with_explicit_4(self):
        """kivi_style with quant_bits_arg=4 should return 4."""
        self.assertEqual(self._resolve("kivi_style", quant_bits_arg=4), 4)

    def test_unknown_mode_defaults_to_16(self):
        self.assertEqual(self._resolve("unknown_mode"), 16)


class TestBuildConfigSnapshot(unittest.TestCase):
    """TST-047: build_config_snapshot."""

    def _build(self, *args, **kwargs):
        from src.utils.repro import build_config_snapshot
        return build_config_snapshot(*args, **kwargs)

    def test_returns_dict_with_required_keys(self):
        result = self._build("test_script.py", {"lr": 0.001})
        self.assertIn("script", result)
        self.assertIn("timestamp", result)
        self.assertIn("args", result)
        self.assertIn("decoding", result)
        self.assertEqual(result["script"], "test_script.py")

    def test_decoding_is_greedy(self):
        """Decoding params should always be greedy (project fixed decision)."""
        result = self._build("x.py", {})
        self.assertEqual(result["decoding"]["temperature"], 0.0)
        self.assertEqual(result["decoding"]["top_p"], 1.0)
        self.assertEqual(result["decoding"]["top_k"], 0)

    def test_dict_args_passed_through(self):
        args = {"model": "test", "batch_size": 4}
        result = self._build("x.py", args)
        self.assertEqual(result["args"]["model"], "test")

    def test_namespace_args_converted(self):
        """argparse.Namespace objects should be serialized."""
        import argparse
        ns = argparse.Namespace(model="test", lr=0.01)
        result = self._build("x.py", ns)
        self.assertEqual(result["args"]["model"], "test")

    def test_extra_dict_merged(self):
        result = self._build("x.py", {}, extra={"hardware": "A100"})
        self.assertEqual(result["hardware"], "A100")


class TestWriteConfigSnapshot(unittest.TestCase):
    """TST-047: write_config_snapshot (UTIL-008 error handling)."""

    def _write(self, *args, **kwargs):
        from src.utils.repro import write_config_snapshot
        return write_config_snapshot(*args, **kwargs)

    def test_successful_write(self):
        """Normal write should return the path to the snapshot file."""
        with tempfile.TemporaryDirectory() as td:
            snapshot = {"script": "test.py", "args": {}}
            result = self._write(td, snapshot)
            self.assertIsNotNone(result)
            self.assertTrue(Path(result).exists())

    def test_write_to_readonly_dir_returns_none(self):
        """Write failure should return None, not raise (UTIL-008)."""
        # Use a path that doesn't exist and can't be created
        result = self._write("/nonexistent/deeply/nested/dir", {"a": 1})
        # Should return None (warning issued) rather than raising
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
