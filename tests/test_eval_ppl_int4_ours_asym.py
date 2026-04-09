#!/usr/bin/env python3
"""Regression tests for scripts/eval_ppl.py int4_ours_asym calibration path (TST-086).

Covers the ``int4_ours_asym`` / ``int4_ours_asym_ba`` branch of
``build_kv_cache`` (L404-457) which is the sole source of INT4-RoleAlign PPL
numbers in the paper. Additionally provides regression coverage for
EVL-149/EVL-152 (relative path resolution + fail-fast) on the same branch.

Test matrix:
    1. ``test_role_aware_schema_parses_k_v_percentiles`` — v4 role_aware schema
    2. ``test_k_calibration_fallback_emits_warning`` — v3 fallback + UserWarning
    3. ``test_ours_asym_ba_inv_tau_role_aware_path`` — BA variant, inv_tau in role_aware
    4. ``test_ours_asym_ba_inv_tau_k_calibration_path`` — BA variant, inv_tau in k_calibration
    5. ``test_ours_asym_ba_inv_tau_top_level_v2_path`` — BA variant, inv_tau at top-level
    6. ``test_ours_asym_no_inv_tau_when_not_ba`` — non-BA must ignore inv_tau
    7. ``test_use_attn_temperature_only_for_ba`` — use_attn_temperature gate
    8. ``test_default_percentiles_when_no_calib_file`` — calib_file=None -> 100.0 defaults
    9. ``test_relative_calib_path_resolves_from_project_root`` — EVL-149 regression
   10. ``test_missing_calib_file_raises_fail_fast`` — EVL-149 fail-fast upgrade
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# -- Mock setup identical to test_eval_ppl_guardrails.py so cross-test imports
# -- don't pollute sys.modules. tearDownModule restores originals.

_MOCKED_MODULES: list = []
_ORIGINAL_MODULES: dict = {}
_ATTR_ORIGINALS: list = []


def _ensure_mock(module_name: str) -> None:
    if module_name in sys.modules:
        _ORIGINAL_MODULES[module_name] = sys.modules[module_name]
    else:
        _MOCKED_MODULES.append(module_name)
    sys.modules[module_name] = MagicMock()


def _ensure_mock_if_missing(module_name: str) -> bool:
    """Mock module only if it cannot be imported. Preserves real packages on
    environments where the dependency is installed (e.g., remote GPU servers
    with real tqdm/datasets). Returns True if mocked, False if real import succeeded."""
    try:
        __import__(module_name)
        return False
    except ImportError:
        _ensure_mock(module_name)
        return True


def _patch_attr(mod, attr, mock_val):
    _ATTR_ORIGINALS.append((mod, attr, getattr(mod, attr, None)))
    setattr(mod, attr, mock_val)


def tearDownModule():
    for name in _MOCKED_MODULES:
        sys.modules.pop(name, None)
    for name, orig in _ORIGINAL_MODULES.items():
        sys.modules[name] = orig
    for mod, attr, orig_val in _ATTR_ORIGINALS:
        if orig_val is None:
            try:
                delattr(mod, attr)
            except AttributeError:
                pass
        else:
            setattr(mod, attr, orig_val)


# Mock third-party modules only when they are actually missing.
# On remote GPU servers with a real tqdm install, mocking would break
# huggingface_hub (which does `from tqdm.auto import tqdm as base_tqdm` and
# uses the class as a type annotation via `Optional[tqdm]`).
# On local dev without tqdm/triton/datasets, the conditional mock kicks in.
_tqdm_mocked = _ensure_mock_if_missing("tqdm")
if _tqdm_mocked:
    # When mocking tqdm, we must also mock its submodules because
    # MagicMock() is not a package and cannot satisfy `from tqdm.X import Y`.
    for _name in ("tqdm.auto", "tqdm.contrib", "tqdm.contrib.concurrent"):
        _ensure_mock(_name)
    sys.modules["tqdm"].tqdm = MagicMock()
    sys.modules["tqdm.auto"].tqdm = MagicMock()
    sys.modules["tqdm.contrib.concurrent"].thread_map = MagicMock()

# triton / datasets / pynvml: same conditional approach.
_ensure_mock_if_missing("triton")
if "triton" in _MOCKED_MODULES:
    _ensure_mock("triton.language")
_ensure_mock_if_missing("datasets")
if "datasets" in _MOCKED_MODULES and isinstance(sys.modules["datasets"], MagicMock):
    sys.modules["datasets"].load_dataset = MagicMock()
_ensure_mock_if_missing("pynvml")


# Spy class that records constructor kwargs for later assertions.
# This replaces the real RoleAwareAsymKVCache in sys.modules so that
# build_kv_cache's local ``from src.cache.role_aware_asym_cache import
# RoleAwareAsymKVCache`` picks it up.
class SpyRoleAwareAsymKVCache:
    last_kwargs: dict = {}
    call_count: int = 0

    def __init__(self, **kwargs):
        SpyRoleAwareAsymKVCache.last_kwargs = dict(kwargs)
        SpyRoleAwareAsymKVCache.call_count += 1


# TST-086/Codex-P1: All sys.modules mutations MUST go through _ensure_mock
# so tearDownModule can restore original modules after this file's tests run.
# Previously, raw assignments like `sys.modules[k] = MagicMock()` and
# `sys.modules.setdefault(k, MagicMock())` bypassed the _MOCKED_MODULES /
# _ORIGINAL_MODULES tracking, causing cross-test pollution when pytest runs
# this file before test_role_aware_asym_cache.py / test_utils.py /
# test_config_utils.py (they would import MagicMock instead of real code).

# Inject a fake src.cache.role_aware_asym_cache module exposing the spy.
# Must use _ensure_mock for tracking, then install the spy class on the mock.
_ensure_mock("src.cache.role_aware_asym_cache")
sys.modules["src.cache.role_aware_asym_cache"].RoleAwareAsymKVCache = SpyRoleAwareAsymKVCache

# Mock src.* attribute patches needed by eval_ppl import.
# Using _ensure_mock (not setdefault) so teardown is properly registered.
_ensure_mock("src.utils.hf")
_hf_mod = sys.modules["src.utils.hf"]
_patch_attr(_hf_mod, "resolve_pretrained_path", MagicMock())

_ensure_mock("src.utils.repro")
repro_mod = sys.modules["src.utils.repro"]
_patch_attr(repro_mod, "build_config_snapshot", MagicMock())
_patch_attr(repro_mod, "get_git_commit", MagicMock(return_value="mock_commit"))
_patch_attr(repro_mod, "get_hardware_info", MagicMock(return_value={"gpu": "mock", "gpu_memory": "0"}))
_patch_attr(repro_mod, "resolve_quant_bits", MagicMock(return_value=4))
_patch_attr(repro_mod, "set_seed", MagicMock())
_patch_attr(repro_mod, "write_config_snapshot", MagicMock())

_ensure_mock("scripts.config_utils")
cfg_mod = sys.modules["scripts.config_utils"]
_patch_attr(cfg_mod, "load_config", MagicMock(return_value={}))
_patch_attr(cfg_mod, "normalize_kv_params", MagicMock())
_patch_attr(cfg_mod, "resolve_run_config", MagicMock(return_value={}))


import torch  # noqa: E402  (after mocks)
import eval_ppl as ep  # noqa: E402


def _make_mock_model(num_layers: int = 28):
    """Build a MagicMock model with real torch.device so .device.type works."""
    model = MagicMock()
    model.config = MagicMock()
    model.config.num_hidden_layers = num_layers
    model.device = torch.device("cpu")
    return model


def _default_build_kwargs(calib_file, kv_mode, use_attn_temperature=False):
    """Common kwargs for build_kv_cache calls; only the vars we care about vary."""
    return dict(
        kv_mode=kv_mode,
        model=_make_mock_model(),
        group_size=16,
        clip_percentile=99.5,
        calib_file=calib_file,
        use_attn_temperature=use_attn_temperature,
        use_static_scales=True,
        adaptive_static_scales=False,
        adaptive_static_margin=1.0,
        adaptive_static_k=True,
        adaptive_static_v=True,
        decode_attn_impl="torch_ref",
    )


def _write_calib(data: dict) -> str:
    """Write a JSON calib fixture to a temp file and return the absolute path."""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="calib_")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


def _stub_load_calibration():
    """Neutralize load_calibration so int4_ours_asym hits L404-457 unimpeded."""
    return patch.object(
        ep,
        "load_calibration",
        return_value=(None, None, None, 16, 99.5, 0.0, False),
    )


class TestInt4OursAsymCalibrationPaths(unittest.TestCase):
    """TST-086: cover all 3 schema branches for int4_ours_asym(_ba)."""

    def setUp(self):
        SpyRoleAwareAsymKVCache.last_kwargs = {}
        SpyRoleAwareAsymKVCache.call_count = 0
        self._tmp_files: list = []

    def tearDown(self):
        for p in self._tmp_files:
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass

    def _fixture(self, data: dict) -> str:
        path = _write_calib(data)
        self._tmp_files.append(path)
        return path

    # ----- Test 1: v4 role_aware schema
    def test_role_aware_schema_parses_k_v_percentiles(self):
        calib = self._fixture({
            "role_aware": {"k_percentile": 99.0, "v_percentile": 99.5}
        })
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(calib, "int4_ours_asym"))
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertAlmostEqual(kw["k_percentile"], 99.0)
        self.assertAlmostEqual(kw["v_percentile"], 99.5)
        self.assertIsNone(kw["inv_tau"])
        self.assertEqual(kw["framework"], "ours_asym")

    # ----- Test 2: v3 k_calibration fallback emits UserWarning
    def test_k_calibration_fallback_emits_warning(self):
        calib = self._fixture({
            "k_calibration": {"k_percentile": 98.5},
            "v_calibration": {"v_percentile": 99.0},
        })
        with _stub_load_calibration():
            with self.assertWarns(UserWarning) as ctx:
                ep.build_kv_cache(**_default_build_kwargs(calib, "int4_ours_asym"))
        self.assertIn("fallback", str(ctx.warning).lower())
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertAlmostEqual(kw["k_percentile"], 98.5)
        self.assertAlmostEqual(kw["v_percentile"], 99.0)

    # ----- Test 3: ours_asym_ba inv_tau from role_aware section
    def test_ours_asym_ba_inv_tau_role_aware_path(self):
        inv_tau_raw = [[0.5] * 12 for _ in range(28)]
        calib = self._fixture({
            "role_aware": {
                "k_percentile": 99.0,
                "v_percentile": 99.5,
                "inv_tau": inv_tau_raw,
            }
        })
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(
                calib, "int4_ours_asym_ba", use_attn_temperature=True
            ))
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertIsNotNone(kw["inv_tau"])
        self.assertIsInstance(kw["inv_tau"], torch.Tensor)
        self.assertEqual(tuple(kw["inv_tau"].shape), (28, 12))
        self.assertEqual(kw["framework"], "ours_asym_ba")
        self.assertTrue(kw["use_attn_temperature"])

    # ----- Test 4: ours_asym_ba inv_tau from k_calibration (v3)
    def test_ours_asym_ba_inv_tau_k_calibration_path(self):
        inv_tau_raw = [[0.6] * 12 for _ in range(28)]
        calib = self._fixture({
            "k_calibration": {"k_percentile": 98.5, "inv_tau": inv_tau_raw},
            "v_calibration": {"v_percentile": 99.0},
        })
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(
                calib, "int4_ours_asym_ba", use_attn_temperature=True
            ))
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertIsNotNone(kw["inv_tau"])
        self.assertEqual(tuple(kw["inv_tau"].shape), (28, 12))
        # UserWarning is emitted because role_aware absent => fallback branch
        self.assertAlmostEqual(kw["k_percentile"], 98.5)

    # ----- Test 5: ours_asym_ba inv_tau from top-level (v2 schema)
    def test_ours_asym_ba_inv_tau_top_level_v2_path(self):
        inv_tau_raw = [[0.7] * 12 for _ in range(28)]
        calib = self._fixture({
            "k_calibration": {"k_percentile": 98.5},
            "v_calibration": {"v_percentile": 99.0},
            "inv_tau": inv_tau_raw,
        })
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(
                calib, "int4_ours_asym_ba", use_attn_temperature=True
            ))
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertIsNotNone(kw["inv_tau"])
        # Value should be 0.7 (top-level)
        self.assertAlmostEqual(float(kw["inv_tau"][0, 0]), 0.7)

    # ----- Test 6: non-BA must NOT load inv_tau even if JSON has it
    def test_ours_asym_no_inv_tau_when_not_ba(self):
        calib = self._fixture({
            "role_aware": {
                "k_percentile": 99.0,
                "v_percentile": 99.5,
                "inv_tau": [[0.5] * 12 for _ in range(28)],
            }
        })
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(
                calib, "int4_ours_asym", use_attn_temperature=True
            ))
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertIsNone(kw["inv_tau"],
                          "non-BA mode must not load inv_tau even if JSON contains it")
        # use_attn_temperature is gated by (mode == ours_asym_ba)
        self.assertFalse(kw["use_attn_temperature"])

    # ----- Test 7: use_attn_temperature gate
    def test_use_attn_temperature_only_for_ba(self):
        calib = self._fixture({
            "role_aware": {"k_percentile": 99.0, "v_percentile": 99.5}
        })
        # CLI says True but mode is non-BA -> should be False
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(
                calib, "int4_ours_asym", use_attn_temperature=True
            ))
        self.assertFalse(SpyRoleAwareAsymKVCache.last_kwargs["use_attn_temperature"])
        # Same mode with BA -> True
        SpyRoleAwareAsymKVCache.last_kwargs = {}
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(
                calib, "int4_ours_asym_ba", use_attn_temperature=True
            ))
        self.assertTrue(SpyRoleAwareAsymKVCache.last_kwargs["use_attn_temperature"])

    # ----- Test 8: default percentiles when calib_file is None
    def test_default_percentiles_when_no_calib_file(self):
        with _stub_load_calibration():
            ep.build_kv_cache(**_default_build_kwargs(None, "int4_ours_asym"))
        kw = SpyRoleAwareAsymKVCache.last_kwargs
        self.assertAlmostEqual(kw["k_percentile"], 100.0)
        self.assertAlmostEqual(kw["v_percentile"], 100.0)
        self.assertIsNone(kw["inv_tau"])


class TestInt4OursAsymEvl149Regression(unittest.TestCase):
    """EVL-149 regression: relative path resolution + fail-fast."""

    def setUp(self):
        SpyRoleAwareAsymKVCache.last_kwargs = {}
        SpyRoleAwareAsymKVCache.call_count = 0

    def test_relative_calib_path_resolves_from_project_root(self):
        """cd / && pass relative path -> should resolve from repo root, not CWD."""
        # Put fixture under artifacts/ so a relative path resolves via project_root
        rel_dir = PROJECT_ROOT / "artifacts" / "tmp_test_evl149"
        rel_dir.mkdir(parents=True, exist_ok=True)
        fixture_path = rel_dir / "relative_calib.json"
        fixture_path.write_text(json.dumps({
            "role_aware": {"k_percentile": 97.5, "v_percentile": 98.0}
        }))
        rel_arg = "artifacts/tmp_test_evl149/relative_calib.json"

        original_cwd = os.getcwd()
        try:
            os.chdir("/tmp")  # simulate remote CWD != repo root
            with _stub_load_calibration():
                ep.build_kv_cache(**_default_build_kwargs(rel_arg, "int4_ours_asym"))
            kw = SpyRoleAwareAsymKVCache.last_kwargs
            # If EVL-149 were broken, percentiles would stay at 100.0 (default)
            self.assertAlmostEqual(kw["k_percentile"], 97.5,
                                   msg="EVL-149 regression: relative path not resolved from project root")
            self.assertAlmostEqual(kw["v_percentile"], 98.0)
        finally:
            os.chdir(original_cwd)
            try:
                fixture_path.unlink()
                rel_dir.rmdir()
            except OSError:
                pass

    def test_missing_calib_file_raises_fail_fast(self):
        """EVL-149 fail-fast: user-provided calib_file that cannot be resolved -> FileNotFoundError."""
        bogus_rel = "artifacts/__definitely_does_not_exist__.json"
        with _stub_load_calibration():
            with self.assertRaises(FileNotFoundError) as ctx:
                ep.build_kv_cache(**_default_build_kwargs(bogus_rel, "int4_ours_asym"))
        self.assertIn("not found", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
