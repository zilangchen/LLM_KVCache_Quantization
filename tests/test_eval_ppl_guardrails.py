#!/usr/bin/env python3
"""Guardrail tests for scripts/eval_ppl.py (EVL-086, EVL-132)."""

import ast
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


_MOCKED_MODULES: list[str] = []


def _ensure_mock(module_name: str) -> None:
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()
        _MOCKED_MODULES.append(module_name)


for _name in (
    "torch",
    "tqdm",
    "transformers",
    "transformers.cache_utils",
    "datasets",
    "src.cache",
    "src.engine.patch_model",
    "src.engine.generate_loop",
    "src.utils.hf",
    "src.utils.repro",
    "scripts.config_utils",
):
    _ensure_mock(_name)

# Populate names imported via "from ... import ...".
sys.modules["tqdm"].tqdm = MagicMock()
sys.modules["datasets"].load_dataset = MagicMock()

cache_mod = sys.modules["src.cache"]
cache_mod.FP16KVCache = MagicMock()
cache_mod.INT8KVCache = MagicMock()
cache_mod.INT4KVCache = MagicMock()
cache_mod.KIVIStyleKVCache = MagicMock()

sys.modules["src.engine.patch_model"].apply_int8_fused_patch = MagicMock()
sys.modules["src.engine.generate_loop"]._register_prefill_temperature_hooks = MagicMock()
sys.modules["src.utils.hf"].resolve_pretrained_path = MagicMock()

repro_mod = sys.modules["src.utils.repro"]
repro_mod.build_config_snapshot = MagicMock()
repro_mod.get_git_commit = MagicMock(return_value="mock_commit")
repro_mod.get_hardware_info = MagicMock(return_value={"gpu": "mock", "gpu_memory": "0"})
repro_mod.resolve_quant_bits = MagicMock(return_value=8)
repro_mod.set_seed = MagicMock()
repro_mod.write_config_snapshot = MagicMock()

cfg_mod = sys.modules["scripts.config_utils"]
cfg_mod.load_config = MagicMock(return_value={})
cfg_mod.normalize_kv_params = MagicMock()
cfg_mod.resolve_run_config = MagicMock(return_value={})


import eval_ppl as ep  # noqa: E402


class TestEvalPplCliDefaults(unittest.TestCase):
    """EVL-086: verify --use_attn_temperature parser default is False."""

    def test_use_attn_temperature_default_false(self):
        source = Path(ep.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        default_value = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
                continue
            if not node.args:
                continue
            first_arg = node.args[0]
            if not isinstance(first_arg, ast.Constant) or first_arg.value != "--use_attn_temperature":
                continue
            for kw in node.keywords:
                if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                    default_value = kw.value.value
                    break
        self.assertIs(default_value, False)


class TestEvalPplFiniteGuard(unittest.TestCase):
    """EVL-132: non-finite PPL must fail with non-zero exit."""

    def _make_args(self):
        return ep.argparse.Namespace(
            out_dir=str(PROJECT_ROOT / "artifacts" / "tmp_guardrail"),
            kv_mode="int8_ours",
            run_name="unit_test",
            seed=1234,
            replica_id=0,
            seq_len=128,
        )

    def test_finite_ppl_no_exception(self):
        args = self._make_args()
        with patch.object(ep, "_write_task_failure") as mocked:
            ep._handle_non_finite_ppl(
                args=args,
                ppl_val=12.34,
                total_nll=123.0,
                total_tokens=10,
            )
            mocked.assert_not_called()

    def test_nan_ppl_exits_nonzero(self):
        args = self._make_args()
        with patch.object(ep, "_write_task_failure") as mocked:
            with self.assertRaises(SystemExit) as ctx:
                ep._handle_non_finite_ppl(
                    args=args,
                    ppl_val=float("nan"),
                    total_nll=float("nan"),
                    total_tokens=10,
                )
            self.assertEqual(ctx.exception.code, ep.EXIT_EXCEPTION)
            mocked.assert_called_once()


class TestCalibFileWarning(unittest.TestCase):
    """F2/EVL-037: calibrated modes must warn when --calib_file is unspecified."""

    def test_int8_ours_warns_without_calib_file(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ep.load_calibration(
                kv_mode="int8_ours",
                calib_file=None,
                use_attn_temperature=False,
                use_static_scales=True,
                group_size=128,
                clip_percentile=99.9,
                device="cpu",
            )
        warning_messages = [str(x.message) for x in w]
        matched = any("No --calib_file specified" in m for m in warning_messages)
        self.assertTrue(matched, f"Expected calib_file warning, got: {warning_messages}")

    def test_explicit_calib_file_no_warning(self):
        import warnings
        import tempfile, json, os
        # Create a minimal calib file
        calib_data = {
            "version": 1, "model_id": "test",
            "k_scale": [], "v_scale": [], "inv_tau": [],
            "group_size_k": 128, "group_size_v": 128,
            "clip_percentile_k": 99.9, "clip_percentile_v": 99.9,
        }
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(calib_data, f)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                ep.load_calibration(
                    kv_mode="int8_ours",
                    calib_file=path,
                    use_attn_temperature=False,
                    use_static_scales=True,
                    group_size=128,
                    clip_percentile=99.9,
                    device="cpu",
                )
            warning_messages = [str(x.message) for x in w]
            matched = any("No --calib_file specified" in m for m in warning_messages)
            self.assertFalse(matched, f"Should not warn with explicit calib_file, got: {warning_messages}")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
