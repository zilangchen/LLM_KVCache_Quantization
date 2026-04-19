#!/usr/bin/env python3
"""Regression tests for eval_ppl same-format allocator kv_mode builder path."""

import json
import importlib.machinery
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


_MOCKED_MODULES: list[str] = []
_ORIGINAL_MODULES: dict[str, object] = {}


def _ensure_mock(module_name: str) -> None:
    if module_name in sys.modules:
        _ORIGINAL_MODULES[module_name] = sys.modules[module_name]
    else:
        _MOCKED_MODULES.append(module_name)
    sys.modules[module_name] = MagicMock()


def tearDownModule():
    for name in _MOCKED_MODULES:
        sys.modules.pop(name, None)
    for name, original in _ORIGINAL_MODULES.items():
        sys.modules[name] = original


for module_name in (
    "triton",
    "triton.language",
    "datasets",
    "pynvml",
    "src.utils.hf",
    "src.utils.repro",
    "scripts.config_utils",
):
    _ensure_mock(module_name)

sys.modules["datasets"].load_dataset = MagicMock()
sys.modules["datasets"].__spec__ = importlib.machinery.ModuleSpec("datasets", loader=None)
sys.modules["src.utils.hf"].resolve_pretrained_path = MagicMock()
sys.modules["src.utils.repro"].build_config_snapshot = MagicMock()
sys.modules["src.utils.repro"].get_git_commit = MagicMock(return_value="mock_commit")
sys.modules["src.utils.repro"].get_hardware_info = MagicMock(return_value={"gpu": "mock", "gpu_memory": "0"})
sys.modules["src.utils.repro"].resolve_quant_bits = MagicMock(return_value=4)
sys.modules["src.utils.repro"].set_seed = MagicMock()
sys.modules["src.utils.repro"].write_config_snapshot = MagicMock()
sys.modules["scripts.config_utils"].load_config = MagicMock(return_value={})
sys.modules["scripts.config_utils"].normalize_kv_params = MagicMock()
sys.modules["scripts.config_utils"].resolve_run_config = MagicMock(return_value={})


class SpyRoleAwareAllocatorKVCache:
    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        SpyRoleAwareAllocatorKVCache.last_kwargs = dict(kwargs)


_ensure_mock("src.cache.role_aware_allocator_cache")
sys.modules["src.cache.role_aware_allocator_cache"].RoleAwareAllocatorKVCache = SpyRoleAwareAllocatorKVCache
sys.modules["src.cache.role_aware_allocator_cache"].load_per_layer_bits_from_policy = (
    lambda policy_json, project_root: [
        tuple(entry) for entry in json.loads(Path(policy_json).read_text(encoding="utf-8"))["per_layer_bits"]
    ]
)

import torch  # noqa: E402
import eval_ppl as ep  # noqa: E402


def _make_mock_model(num_layers: int = 28):
    model = MagicMock()
    model.config = MagicMock()
    model.config.num_hidden_layers = num_layers
    model.device = torch.device("cpu")
    return model


def _default_build_kwargs(calib_file, policy_json):
    return dict(
        kv_mode="int4_ours_asym_alloc",
        model=_make_mock_model(),
        group_size=16,
        clip_percentile=99.5,
        calib_file=calib_file,
        use_attn_temperature=False,
        use_static_scales=True,
        adaptive_static_scales=False,
        adaptive_static_margin=1.0,
        adaptive_static_k=True,
        adaptive_static_v=True,
        decode_attn_impl="torch_ref",
        policy_json=policy_json,
    )


def _write_json(data: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    return path


class TestInt4OursAsymAllocBuilder(unittest.TestCase):
    def setUp(self):
        SpyRoleAwareAllocatorKVCache.last_kwargs = {}
        self._tmp_paths: list[str] = []

    def tearDown(self):
        for path in self._tmp_paths:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

    def _fixture(self, data: dict) -> str:
        path = _write_json(data)
        self._tmp_paths.append(path)
        return path

    def test_rolealign_allocator_builder_reads_calib_and_policy(self):
        calib = self._fixture({"role_aware": {"k_percentile": 99.0, "v_percentile": 99.5}})
        policy = self._fixture({"per_layer_bits": [(4, 4), (8, 4), (4, 8)]})
        with patch.object(
            ep,
            "load_calibration",
            return_value=(None, None, None, 16, 99.5, 0.0, False),
        ):
            ep.build_kv_cache(**_default_build_kwargs(calib, policy))
        kwargs = SpyRoleAwareAllocatorKVCache.last_kwargs
        self.assertEqual(kwargs["framework"], "ours_asym_allocator")
        self.assertEqual(kwargs["per_layer_bits"], [(4, 4), (8, 4), (4, 8)])
        self.assertAlmostEqual(kwargs["k_percentile"], 99.0)
        self.assertAlmostEqual(kwargs["v_percentile"], 99.5)

    def test_rolealign_allocator_builder_requires_policy_json(self):
        calib = self._fixture({"role_aware": {"k_percentile": 99.0, "v_percentile": 99.5}})
        with patch.object(
            ep,
            "load_calibration",
            return_value=(None, None, None, 16, 99.5, 0.0, False),
        ):
            with self.assertRaises(ValueError):
                ep.build_kv_cache(**_default_build_kwargs(calib, None))
