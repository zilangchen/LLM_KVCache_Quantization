"""Extended tests for scripts/run_experiments.py (TST-040).

Supplements test_run_experiments_resilience.py with additional
_classify_failure paths that were previously uncovered:
  - returncode=130 -> "interrupt"
  - returncode=0 with no log indicators -> "unknown"
  - Log contains "CUDA out of memory" -> "oom"
  - Log contains "outofmemoryerror" -> "oom"
  - Log contains only "out of memory" -> "oom"
  - Word-boundary: "bloom" should not trigger OOM
  - returncode != 0 with no log match -> "runtime_error"
  - No returncode (None) with clean log -> "unknown"
"""

import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_experiments as rex  # noqa: E402


# ---------------------------------------------------------------------------
# TST-054: _same_commit_prefix
# ---------------------------------------------------------------------------

class TestSameCommitPrefix(unittest.TestCase):
    """Test _same_commit_prefix() for hash comparison edge cases."""

    def test_identical_full_hashes(self):
        h = "abcdef1234567890abcdef1234567890abcdef12"
        self.assertTrue(rex._same_commit_prefix(h, h))

    def test_matching_first_8_chars(self):
        self.assertTrue(rex._same_commit_prefix("abcdef12xxx", "abcdef12yyy"))

    def test_different_hashes(self):
        self.assertFalse(rex._same_commit_prefix("abcdef12xxx", "12345678yyy"))

    def test_short_matching_hashes(self):
        self.assertTrue(rex._same_commit_prefix("abcdef12", "abcdef12"))

    def test_empty_a_returns_false(self):
        self.assertFalse(rex._same_commit_prefix("", "abcdef12"))

    def test_empty_b_returns_false(self):
        self.assertFalse(rex._same_commit_prefix("abcdef12", ""))

    def test_both_empty_returns_false(self):
        self.assertFalse(rex._same_commit_prefix("", ""))

    def test_unknown_a_returns_false(self):
        self.assertFalse(rex._same_commit_prefix("unknown", "abcdef12"))

    def test_unknown_b_returns_false(self):
        self.assertFalse(rex._same_commit_prefix("abcdef12", "unknown"))

    def test_whitespace_stripped(self):
        self.assertTrue(rex._same_commit_prefix("  abcdef12  ", "abcdef12"))

    def test_case_sensitive(self):
        """Hash comparison is case-sensitive (git hashes are lowercase)."""
        self.assertFalse(rex._same_commit_prefix("ABCDEF12xxx", "abcdef12xxx"))

    def test_prefix_shorter_than_8(self):
        """When hashes are shorter than 8 chars, comparison uses available chars."""
        self.assertTrue(rex._same_commit_prefix("abc", "abc"))


class TestClassifyFailureExtended(unittest.TestCase):
    """Test _classify_failure() for all classification paths."""

    # -- returncode=73 -> "oom" (already covered in resilience tests,
    #    included here for completeness of this self-contained suite) --

    def test_returncode_73_is_oom(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=73)
            self.assertEqual(result, "oom")

    # -- returncode=130 -> "interrupt" --

    def test_returncode_130_is_interrupt(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=130)
            self.assertEqual(result, "interrupt")

    def test_returncode_130_overrides_log_content(self):
        """returncode=130 should be classified as interrupt even with traceback in log."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text(
                "Traceback (most recent call last):\nKeyboardInterrupt\n",
                encoding="utf-8",
            )
            result = rex._classify_failure(log_path=log, returncode=130)
            self.assertEqual(result, "interrupt")

    # -- Log OOM detection --

    def test_log_cuda_out_of_memory(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text(
                "RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB\n",
                encoding="utf-8",
            )
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "oom")

    def test_log_generic_out_of_memory(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Error: out of memory\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "oom")

    def test_log_outofmemoryerror(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("torch.cuda.OutOfMemoryError: ...\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "oom")

    def test_log_oom_word_boundary(self):
        """The standalone word 'oom' (case-insensitive) should trigger OOM."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Process killed due to OOM\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "oom")

    def test_log_bloom_does_not_trigger_oom(self):
        """'bloom' should NOT be classified as OOM (word boundary check)."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text(
                "Loading bloom model from huggingface hub\nsome normal error\n",
                encoding="utf-8",
            )
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertNotEqual(result, "oom")

    def test_log_room_does_not_trigger_oom(self):
        """'room' should NOT be classified as OOM (word boundary check)."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("There is room for improvement\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertNotEqual(result, "oom")

    # -- Traceback detection --

    def test_log_traceback_detection(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text(
                "Traceback (most recent call last):\n"
                "  File \"foo.py\", line 42\n"
                "ValueError: bad input\n",
                encoding="utf-8",
            )
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "traceback")

    def test_oom_in_traceback_classified_as_oom(self):
        """When both traceback and OOM keywords are in log, OOM wins."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text(
                "Traceback (most recent call last):\n"
                "RuntimeError: CUDA out of memory\n",
                encoding="utf-8",
            )
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "oom")

    # -- runtime_error: non-zero returncode with no specific pattern --

    def test_nonzero_returncode_no_pattern_is_runtime_error(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Some generic error message\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "runtime_error")

    def test_returncode_2_with_clean_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Command exited with code 2\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=2)
            self.assertEqual(result, "runtime_error")

    # -- returncode=0 path: "unknown" --

    def test_returncode_0_with_clean_log_is_unknown(self):
        """returncode=0 with no error patterns should return 'unknown'."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Process completed normally\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=0)
            self.assertEqual(result, "unknown")

    def test_returncode_0_but_log_has_oom_is_oom(self):
        """returncode=0 but log contains OOM markers should still classify as OOM."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("CUDA out of memory during cleanup\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=0)
            self.assertEqual(result, "oom")

    # -- returncode=None path --

    def test_returncode_none_clean_log_is_unknown(self):
        """When returncode is None and log is clean, result should be 'unknown'."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Normal log output\n", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=None)
            self.assertEqual(result, "unknown")

    def test_returncode_none_with_traceback_log(self):
        """When returncode is None but log has traceback, classify as traceback."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text(
                "Traceback (most recent call last):\nRuntimeError\n",
                encoding="utf-8",
            )
            result = rex._classify_failure(log_path=log, returncode=None)
            self.assertEqual(result, "traceback")

    # -- Empty log file --

    def test_empty_log_nonzero_returncode(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("", encoding="utf-8")
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "runtime_error")

    # -- Missing log file --

    def test_missing_log_file(self):
        """When log file does not exist, _read_text_best_effort returns '' and
        classification falls through to returncode-based logic."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "nonexistent.log"
            result = rex._classify_failure(log_path=log, returncode=1)
            self.assertEqual(result, "runtime_error")


# ---------------------------------------------------------------------------
# Test: resolve_quant_params
# ---------------------------------------------------------------------------

class TestResolveQuantParams(unittest.TestCase):
    """Test resolve_quant_params() parameter resolution and validation."""

    def test_defaults_from_quant_defaults(self):
        result = rex.resolve_quant_params(
            {},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["clip_percentile_k"], 99.5)
        self.assertEqual(result["group_size_k"], 64)

    def test_run_entry_overrides_defaults(self):
        result = rex.resolve_quant_params(
            {"clip_percentile_k": 95.0, "group_size_k": 32},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["clip_percentile_k"], 95.0)
        self.assertEqual(result["group_size_k"], 32)
        # v values should still come from defaults
        self.assertEqual(result["clip_percentile_v"], 99.5)
        self.assertEqual(result["group_size_v"], 64)

    def test_invalid_clip_percentile_raises(self):
        with self.assertRaises(ValueError):
            rex.resolve_quant_params(
                {"clip_percentile_k": 0.0},  # out of range (0, 100]
                {"clip_percentile_v": 99.5, "group_size_k": 64, "group_size_v": 64},
            )

    def test_invalid_group_size_type_raises(self):
        with self.assertRaises(ValueError):
            rex.resolve_quant_params(
                {"group_size_k": 64.5},  # not an int
                {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
                 "group_size_v": 64},
            )

    def test_negative_group_size_raises(self):
        with self.assertRaises(ValueError):
            rex.resolve_quant_params(
                {"group_size_k": -1},
                {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
                 "group_size_v": 64},
            )

    def test_clip_percentile_100_is_valid(self):
        result = rex.resolve_quant_params(
            {"clip_percentile_k": 100.0},
            {"clip_percentile_v": 99.5, "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["clip_percentile_k"], 100.0)

    def test_clip_percentile_v_override(self):
        result = rex.resolve_quant_params(
            {"clip_percentile_v": 90.0},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["clip_percentile_v"], 90.0)
        self.assertEqual(result["clip_percentile_k"], 99.5)

    def test_group_size_v_override(self):
        result = rex.resolve_quant_params(
            {"group_size_v": 128},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["group_size_v"], 128)
        self.assertEqual(result["group_size_k"], 64)

    def test_boolean_clip_percentile_raises(self):
        """bool is technically int subclass; should be rejected for clip_percentile."""
        with self.assertRaises(ValueError):
            rex.resolve_quant_params(
                {"clip_percentile_k": True},
                {"clip_percentile_v": 99.5, "group_size_k": 64, "group_size_v": 64},
            )

    def test_boolean_group_size_raises(self):
        """bool should be rejected for group_size even though isinstance(True, int)."""
        with self.assertRaises(ValueError):
            rex.resolve_quant_params(
                {"group_size_k": True},
                {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
                 "group_size_v": 64},
            )

    def test_zero_group_size_raises(self):
        with self.assertRaises(ValueError):
            rex.resolve_quant_params(
                {"group_size_k": 0},
                {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
                 "group_size_v": 64},
            )

    def test_all_params_from_run_entry(self):
        result = rex.resolve_quant_params(
            {"clip_percentile_k": 95.0, "clip_percentile_v": 95.0,
             "group_size_k": 32, "group_size_v": 32},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["clip_percentile_k"], 95.0)
        self.assertEqual(result["clip_percentile_v"], 95.0)
        self.assertEqual(result["group_size_k"], 32)
        self.assertEqual(result["group_size_v"], 32)

    def test_empty_run_entry_uses_all_defaults(self):
        result = rex.resolve_quant_params(
            {},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        self.assertEqual(result["clip_percentile_k"], 99.5)
        self.assertEqual(result["clip_percentile_v"], 99.5)
        self.assertEqual(result["group_size_k"], 64)
        self.assertEqual(result["group_size_v"], 64)

    def test_return_dict_has_expected_keys(self):
        result = rex.resolve_quant_params(
            {},
            {"clip_percentile_k": 99.5, "clip_percentile_v": 99.5,
             "group_size_k": 64, "group_size_v": 64},
        )
        for key in ("clip_percentile_k", "clip_percentile_v",
                     "group_size_k", "group_size_v"):
            self.assertIn(key, result)


# ---------------------------------------------------------------------------
# TST-039: _validate_append_commit
# ---------------------------------------------------------------------------

class TestValidateAppendCommit(unittest.TestCase):
    """Test _validate_append_commit() for all validation paths.

    TST-039: This function checks that appending to an existing run_dir is
    safe by comparing git commits and env hashes from the manifest and
    existing CSV files against the current session.
    """

    def test_no_manifest_no_csvs_returns_ok(self):
        """Empty run_dir with no manifest or CSVs => append is allowed."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12",
                current_env_hash="hash1234",
            )
            self.assertTrue(ok)
            self.assertEqual(reason, "")

    def test_manifest_same_commit_returns_ok(self):
        """Manifest with same git_commit prefix => append allowed."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            manifest = {"git_commit": "abcdef12", "env_hash": "hash1234"}
            manifest_path.write_text(_json.dumps(manifest), encoding="utf-8")
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12_extra",
                current_env_hash="hash1234",
            )
            self.assertTrue(ok)
            self.assertEqual(reason, "")

    def test_manifest_different_commit_returns_blocked(self):
        """Manifest with different git_commit => append blocked."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            manifest = {"git_commit": "abcdef12", "env_hash": "hash1234"}
            manifest_path.write_text(_json.dumps(manifest), encoding="utf-8")
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="99999999",
                current_env_hash="hash1234",
            )
            self.assertFalse(ok)
            self.assertIn("append blocked", reason)
            self.assertIn("git_commit", reason)

    def test_manifest_different_env_hash_returns_blocked(self):
        """Manifest with different env_hash => append blocked."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            manifest = {"git_commit": "abcdef12", "env_hash": "hash_old"}
            manifest_path.write_text(_json.dumps(manifest), encoding="utf-8")
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12_extra",
                current_env_hash="hash_new",
            )
            self.assertFalse(ok)
            self.assertIn("append blocked", reason)
            self.assertIn("env_hash", reason)

    def test_csv_with_same_commit_returns_ok(self):
        """CSV files with matching git_commit => append allowed."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            # No manifest
            # Create a CSV with git_commit column
            csv_path = run_dir / "profile_latency_test.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["kv_mode", "seq_len", "git_commit"])
                writer.writeheader()
                writer.writerow({"kv_mode": "fp16", "seq_len": "1024", "git_commit": "abcdef12"})
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12_extra",
                current_env_hash="hash1234",
            )
            self.assertTrue(ok)
            self.assertEqual(reason, "")

    def test_csv_with_different_commit_returns_blocked(self):
        """CSV files with different git_commit => append blocked."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            csv_path = run_dir / "profile_latency_test.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["kv_mode", "seq_len", "git_commit"])
                writer.writeheader()
                writer.writerow({"kv_mode": "fp16", "seq_len": "1024", "git_commit": "11111111"})
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="99999999",
                current_env_hash="hash1234",
            )
            self.assertFalse(ok)
            self.assertIn("append blocked", reason)
            self.assertIn("CSV git_commit", reason)

    def test_manifest_no_commit_field_skips_commit_check(self):
        """Manifest without git_commit field => commit check skipped, env_hash checked."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            manifest = {"env_hash": "hash1234"}  # no git_commit
            manifest_path.write_text(_json.dumps(manifest), encoding="utf-8")
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12",
                current_env_hash="hash1234",
            )
            self.assertTrue(ok)

    def test_manifest_empty_commit_skips_commit_check(self):
        """Manifest with empty git_commit => commit check skipped."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            manifest = {"git_commit": "", "env_hash": "hash1234"}
            manifest_path.write_text(_json.dumps(manifest), encoding="utf-8")
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12",
                current_env_hash="hash1234",
            )
            self.assertTrue(ok)

    def test_manifest_empty_env_hash_skips_env_check(self):
        """Manifest with empty env_hash => env_hash check skipped."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            manifest = {"git_commit": "abcdef12", "env_hash": ""}
            manifest_path.write_text(_json.dumps(manifest), encoding="utf-8")
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12_extra",
                current_env_hash="whatever",
            )
            self.assertTrue(ok)

    def test_multiple_csv_patterns_checked(self):
        """CSV files across multiple patterns should all be checked."""
        import json as _json
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            manifest_path = run_dir / "run_manifest.json"
            # First CSV matches commit
            csv1 = run_dir / "profile_latency_test.csv"
            with open(csv1, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["git_commit"])
                writer.writeheader()
                writer.writerow({"git_commit": "abcdef12"})
            # Second CSV has different commit
            csv2 = run_dir / "profile_memory_test.csv"
            with open(csv2, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["git_commit"])
                writer.writeheader()
                writer.writerow({"git_commit": "99999999"})
            ok, reason = rex._validate_append_commit(
                run_dir=run_dir,
                manifest_path=manifest_path,
                current_git_commit="abcdef12_extra",
                current_env_hash="hash1234",
            )
            self.assertFalse(ok)
            self.assertIn("CSV git_commit", reason)


# ---------------------------------------------------------------------------
# TST-039: resolve_calib_params
# ---------------------------------------------------------------------------

class TestResolveCalibParams(unittest.TestCase):
    """Test resolve_calib_params() parameter resolution.

    TST-039: This function had zero tests. Tests cover:
    - Default value resolution from quant_defaults
    - Run entry overrides
    - kivi_style default calib_strategy
    - Non-kivi mode calib_strategy resolution
    - All fields present in return dict
    """

    def test_defaults_from_quant_defaults(self):
        """When run_entry is empty, all values should come from quant_defaults."""
        defaults = {
            "calib_file": "path/to/calib.json",
            "use_attn_temperature": True,
            "use_static_scales": False,
            "adaptive_static_scales": True,
            "adaptive_static_margin": 1.5,
            "adaptive_static_k": False,
            "adaptive_static_v": False,
            "calib_strategy": "percentile",
        }
        result = rex.resolve_calib_params({}, defaults, kv_mode="int8_ours")
        self.assertEqual(result["calib_file"], "path/to/calib.json")
        self.assertTrue(result["use_attn_temperature"])
        self.assertFalse(result["use_static_scales"])
        self.assertTrue(result["adaptive_static_scales"])
        self.assertEqual(result["adaptive_static_margin"], 1.5)
        self.assertFalse(result["adaptive_static_k"])
        self.assertFalse(result["adaptive_static_v"])
        self.assertEqual(result["calib_strategy"], "percentile")

    def test_run_entry_overrides_defaults(self):
        """run_entry values should override quant_defaults."""
        defaults = {
            "calib_file": "default.json",
            "use_attn_temperature": False,
            "use_static_scales": True,
            "calib_strategy": "percentile",
        }
        run_entry = {
            "calib_file": "custom.json",
            "use_attn_temperature": True,
            "use_static_scales": False,
            "calib_strategy": "kl_attn",
        }
        result = rex.resolve_calib_params(run_entry, defaults, kv_mode="int8_ours")
        self.assertEqual(result["calib_file"], "custom.json")
        self.assertTrue(result["use_attn_temperature"])
        self.assertFalse(result["use_static_scales"])
        self.assertEqual(result["calib_strategy"], "kl_attn")

    def test_kivi_style_default_calib_strategy(self):
        """For kivi_style, default calib_strategy should be 'kivi_asymmetric'."""
        defaults = {"calib_strategy": "percentile"}
        result = rex.resolve_calib_params({}, defaults, kv_mode="kivi_style")
        self.assertEqual(result["calib_strategy"], "kivi_asymmetric")

    def test_kivi_style_run_entry_overrides_calib_strategy(self):
        """Even for kivi_style, run_entry calib_strategy should override default."""
        defaults = {"calib_strategy": "percentile"}
        run_entry = {"calib_strategy": "custom_strategy"}
        result = rex.resolve_calib_params(run_entry, defaults, kv_mode="kivi_style")
        self.assertEqual(result["calib_strategy"], "custom_strategy")

    def test_non_kivi_mode_uses_quant_defaults_strategy(self):
        """For non-kivi mode, calib_strategy comes from quant_defaults if not in run_entry."""
        defaults = {"calib_strategy": "percentile"}
        result = rex.resolve_calib_params({}, defaults, kv_mode="int8_ours")
        self.assertEqual(result["calib_strategy"], "percentile")

    def test_empty_defaults_returns_none_and_defaults(self):
        """With empty defaults and run_entry, booleans should have Python defaults."""
        result = rex.resolve_calib_params({}, {}, kv_mode="fp16")
        self.assertIsNone(result["calib_file"])
        self.assertFalse(result["use_attn_temperature"])
        self.assertTrue(result["use_static_scales"])
        self.assertFalse(result["adaptive_static_scales"])
        self.assertEqual(result["adaptive_static_margin"], 1.0)
        self.assertTrue(result["adaptive_static_k"])
        self.assertTrue(result["adaptive_static_v"])
        self.assertIsNone(result["calib_strategy"])

    def test_all_expected_keys_present(self):
        """Return dict should contain all expected calib parameter keys."""
        result = rex.resolve_calib_params({}, {}, kv_mode="fp16")
        expected_keys = {
            "calib_file",
            "use_attn_temperature",
            "use_static_scales",
            "adaptive_static_scales",
            "adaptive_static_margin",
            "adaptive_static_k",
            "adaptive_static_v",
            "calib_strategy",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_adaptive_static_margin_from_run_entry(self):
        """adaptive_static_margin should be overrideable from run_entry."""
        result = rex.resolve_calib_params(
            {"adaptive_static_margin": 2.5},
            {"adaptive_static_margin": 1.0},
            kv_mode="int8_ours",
        )
        self.assertEqual(result["adaptive_static_margin"], 2.5)

    def test_adaptive_static_k_v_from_run_entry(self):
        """adaptive_static_k and adaptive_static_v overrides from run_entry."""
        result = rex.resolve_calib_params(
            {"adaptive_static_k": False, "adaptive_static_v": False},
            {"adaptive_static_k": True, "adaptive_static_v": True},
            kv_mode="int8_ours",
        )
        self.assertFalse(result["adaptive_static_k"])
        self.assertFalse(result["adaptive_static_v"])

    def test_kivi_style_no_defaults_calib_strategy_fallback(self):
        """For kivi_style, if quant_defaults has no calib_strategy,
        the default should still be kivi_asymmetric."""
        result = rex.resolve_calib_params({}, {}, kv_mode="kivi_style")
        self.assertEqual(result["calib_strategy"], "kivi_asymmetric")

    def test_calib_file_none_when_not_specified(self):
        """calib_file should be None when not in run_entry or defaults."""
        result = rex.resolve_calib_params({}, {}, kv_mode="int4_ours")
        self.assertIsNone(result["calib_file"])


if __name__ == "__main__":
    unittest.main()
