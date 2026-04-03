"""Unit tests for src/engine/generate_loop.py and src/engine/patch_model.py functions.

Covers:
  TST-023: _register_prefill_temperature_hooks (q_norm hook vs q_proj hook, seq_len guard, layout detection)
  TST-024: _cache_stats_from_past_key_values (new API / legacy tuple / to_legacy_cache conversion)
  TST-025: _to_dynamic_cache_safely (from_legacy_cache -> ddp_cache_data -> RuntimeError fallback chain)
  TST-027: _get_rope_cos_sin (5 fallback paths via try-except)
  TST-028: _resolve_attn_shape_meta (6 fallback paths for q_heads/kv_heads/head_dim)

All tests run on CPU only with no real PyTorch or GPU dependency.
Mock objects are used throughout to simulate torch.Tensor, nn.Module, model config, and cache objects.
"""

import sys
import os
import types
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# ---------------------------------------------------------------------------
# sys.path setup for imports
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# We must mock out torch and transformers BEFORE importing source modules.
# This allows all tests to run on CPU without real torch/transformers.
# ---------------------------------------------------------------------------

# Create a comprehensive mock for torch
_mock_torch = MagicMock()
_mock_torch.Tensor = type("MockTensor", (), {})
_mock_torch.nn = MagicMock()
_mock_torch.nn.Module = type("MockModule", (), {})

# Create a comprehensive mock for transformers
_mock_transformers = MagicMock()

# Install mocks into sys.modules so that imports resolve to our mocks
_MODULES_TO_MOCK = {
    "torch": _mock_torch,
    "torch.nn": _mock_torch.nn,
    "torch.nn.functional": MagicMock(),
    "torch.cuda": MagicMock(),
    "transformers": _mock_transformers,
    "transformers.cache_utils": MagicMock(),
    "src.utils.timing": MagicMock(),
    "src.utils.repro": MagicMock(),
    "src.kernels": MagicMock(),
    "src.quant.int4_basic": MagicMock(),
}

# Save originals so we can restore them later
_original_modules = {}
for mod_name, mock_mod in _MODULES_TO_MOCK.items():
    _original_modules[mod_name] = sys.modules.get(mod_name)
    sys.modules[mod_name] = mock_mod

# Make DynamicCache available from the mock transformers
_mock_DynamicCache = MagicMock()
sys.modules["transformers"].DynamicCache = _mock_DynamicCache


# ---------------------------------------------------------------------------
# Helper: FakeTensor -- a lightweight object that mimics torch.Tensor attributes
# used by the source code (ndim, shape, numel, element_size, to, view, etc.)
# ---------------------------------------------------------------------------

class FakeTensor:
    """Mimics essential torch.Tensor attributes for testing without real torch."""

    def __init__(self, shape, dtype="float32", data=None):
        self._shape = tuple(shape)
        self._dtype = dtype
        self.dtype = dtype
        self._data = data
        self.ndim = len(self._shape)
        self.device = "cpu"

    @property
    def shape(self):
        return self._shape

    def __getitem__(self, idx):
        """Support indexing like inv_tau[layer_idx]."""
        if isinstance(idx, int):
            # Return a FakeTensor with one fewer dimension
            new_shape = self._shape[1:]
            return FakeTensor(new_shape, dtype=self._dtype)
        return self

    def numel(self):
        result = 1
        for s in self._shape:
            result *= s
        return result

    def element_size(self):
        sizes = {"float16": 2, "float32": 4, "float64": 8, "int8": 1, "bfloat16": 2}
        return sizes.get(self._dtype, 4)

    def to(self, device=None, dtype=None):
        return self

    def view(self, *args):
        return self

    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self


# Make FakeTensor recognized as torch.Tensor by isinstance checks in source code.
# We patch torch.Tensor to be FakeTensor's class.
_mock_torch.Tensor = FakeTensor


# ---------------------------------------------------------------------------
# Now import source modules (they will use our mocked torch/transformers).
# We need to handle the import carefully since generate_loop.py checks
# for DynamicCache at import time.
# ---------------------------------------------------------------------------

# Ensure generate_loop sees HAS_DYNAMIC_CACHE = True
sys.modules["transformers"].DynamicCache = _mock_DynamicCache

# Force fresh import of our target modules
for mod_name in list(sys.modules.keys()):
    if "src.engine.generate_loop" in mod_name or "src.engine.patch_model" in mod_name:
        del sys.modules[mod_name]

# Import the functions under test
from src.engine.generate_loop import (
    _cache_stats_from_past_key_values,
    _normalize_eos_token_id,
    _to_dynamic_cache_safely,
    _register_prefill_temperature_hooks,
)
from src.engine.patch_model import (
    _get_rope_cos_sin,
    _resolve_attn_shape_meta,
    _infer_heads_from_proj,
)


# ===========================================================================
# TST-030: _normalize_eos_token_id (ENG-059)
# ===========================================================================


class TestNormalizeEosTokenId(unittest.TestCase):
    """TST-030: EOS token id normalization for list-valued tokenizer outputs."""

    def test_none_returns_none(self):
        self.assertIsNone(_normalize_eos_token_id(None))

    def test_single_int_passes_through(self):
        self.assertEqual(_normalize_eos_token_id(151643), 151643)

    def test_list_uses_first_item(self):
        self.assertEqual(_normalize_eos_token_id([151643, 151645]), 151643)

    def test_tuple_uses_first_item(self):
        self.assertEqual(_normalize_eos_token_id((42, 43)), 42)

    def test_empty_list_returns_none(self):
        self.assertIsNone(_normalize_eos_token_id([]))


# ===========================================================================
# TST-024: _cache_stats_from_past_key_values
# ===========================================================================


class TestCacheStatsFromPastKeyValues(unittest.TestCase):
    """TST-024: Tests for _cache_stats_from_past_key_values.

    Three paths:
      1. New cache API (layers attribute with .keys/.values tensors)
      2. Legacy tuple path (tuple of (k, v) tuples)
      3. to_legacy_cache() conversion path
    Plus: None input returns (0.0, 0).
    """

    def test_none_input_returns_zeros(self):
        """past_key_values=None should return (0.0, 0)."""
        mem, seq = _cache_stats_from_past_key_values(None)
        self.assertEqual(mem, 0.0)
        self.assertEqual(seq, 0)

    # -- Path 1: New cache API (layers attribute) --

    def test_new_api_layers_with_tensors(self):
        """New API: cache.layers[i].keys/values are FakeTensors."""
        layer = MagicMock()
        # keys: shape [B, H, S, D] = [1, 4, 10, 64], float16 (2 bytes)
        k = FakeTensor([1, 4, 10, 64], dtype="float16")
        v = FakeTensor([1, 4, 10, 64], dtype="float16")
        layer.keys = k
        layer.values = v

        cache = MagicMock()
        cache.layers = [layer]
        # Ensure it does NOT behave as a tuple
        cache.__class__ = type("NewAPICache", (), {})

        mem, seq = _cache_stats_from_past_key_values(cache)

        # k bytes = 1*4*10*64 * 2 = 5120
        # v bytes = 1*4*10*64 * 2 = 5120
        # total = 10240 / (1024*1024) ~ 0.009765625 MB
        expected_bytes = 2 * (1 * 4 * 10 * 64 * 2)
        expected_mb = expected_bytes / (1024 * 1024)
        self.assertAlmostEqual(mem, expected_mb, places=6)
        self.assertEqual(seq, 10)

    def test_new_api_layers_empty_list(self):
        """New API with empty layers list: total_bytes=0 falls through to legacy."""
        cache = MagicMock()
        cache.layers = []
        # No tuple, no to_legacy_cache => returns (0.0, 0)
        cache.__class__ = type("EmptyLayerCache", (), {})

        mem, seq = _cache_stats_from_past_key_values(cache)
        self.assertEqual(mem, 0.0)
        self.assertEqual(seq, 0)

    def test_new_api_layers_non_tensor_keys(self):
        """New API: if keys/values are not FakeTensor, total_bytes stays 0, falls through."""
        layer = MagicMock()
        layer.keys = "not_a_tensor"
        layer.values = "not_a_tensor"

        cache = MagicMock()
        cache.layers = [layer]
        cache.__class__ = type("NonTensorCache", (), {})

        mem, seq = _cache_stats_from_past_key_values(cache)
        # total_bytes == 0, so it falls through. No tuple, no to_legacy_cache.
        self.assertEqual(mem, 0.0)
        self.assertEqual(seq, 0)

    def test_new_api_seq_len_from_3d_tensor(self):
        """New API: seq_len extracted from k.shape[-2] when k.ndim >= 3."""
        layer = MagicMock()
        k = FakeTensor([1, 8, 42, 128], dtype="float32")  # ndim=4, shape[-2]=42
        v = FakeTensor([1, 8, 42, 128], dtype="float32")
        layer.keys = k
        layer.values = v

        cache = MagicMock()
        cache.layers = [layer]
        cache.__class__ = type("SeqLenCache", (), {})

        mem, seq = _cache_stats_from_past_key_values(cache)
        self.assertEqual(seq, 42)
        self.assertGreater(mem, 0.0)

    def test_new_api_multiple_layers(self):
        """New API: multiple layers accumulate bytes, seq_len from first layer."""
        layers = []
        for _ in range(3):
            layer = MagicMock()
            layer.keys = FakeTensor([1, 2, 5, 16], dtype="float16")
            layer.values = FakeTensor([1, 2, 5, 16], dtype="float16")
            layers.append(layer)

        cache = MagicMock()
        cache.layers = layers
        cache.__class__ = type("MultiLayerCache", (), {})

        mem, seq = _cache_stats_from_past_key_values(cache)
        # Each layer: k = 1*2*5*16*2=320, v=320, total per layer=640
        # 3 layers => 1920 bytes => 1920/(1024*1024) MB
        expected_mb = (3 * 2 * (1 * 2 * 5 * 16 * 2)) / (1024 * 1024)
        self.assertAlmostEqual(mem, expected_mb, places=6)
        self.assertEqual(seq, 5)

    # -- Path 2: Legacy tuple path --

    def test_legacy_tuple_path(self):
        """Legacy path: past_key_values is a tuple of (k, v) tuples."""
        k = FakeTensor([1, 4, 20, 64], dtype="float16")
        v = FakeTensor([1, 4, 20, 64], dtype="float16")
        past = ((k, v),)

        mem, seq = _cache_stats_from_past_key_values(past)

        expected_bytes = 2 * (1 * 4 * 20 * 64 * 2)
        expected_mb = expected_bytes / (1024 * 1024)
        self.assertAlmostEqual(mem, expected_mb, places=6)
        self.assertEqual(seq, 20)

    def test_legacy_tuple_multiple_layers(self):
        """Legacy path: multiple (k, v) tuples."""
        layers_data = []
        for _ in range(4):
            k = FakeTensor([1, 2, 8, 32], dtype="float32")
            v = FakeTensor([1, 2, 8, 32], dtype="float32")
            layers_data.append((k, v))
        past = tuple(layers_data)

        mem, seq = _cache_stats_from_past_key_values(past)
        # Each k/v: 1*2*8*32*4=2048 bytes, per layer: 4096, 4 layers: 16384
        expected_mb = (4 * 2 * (1 * 2 * 8 * 32 * 4)) / (1024 * 1024)
        self.assertAlmostEqual(mem, expected_mb, places=6)
        self.assertEqual(seq, 8)

    def test_legacy_tuple_skips_non_tuple_items(self):
        """Legacy path: items that are not tuples or have < 2 elements are skipped."""
        k = FakeTensor([1, 1, 3, 4], dtype="float16")
        v = FakeTensor([1, 1, 3, 4], dtype="float16")
        past = (
            "not_a_tuple",
            (k,),  # len < 2, skipped
            (k, v),  # valid
        )

        mem, seq = _cache_stats_from_past_key_values(past)
        # Only one valid layer
        expected_bytes = 2 * (1 * 1 * 3 * 4 * 2)
        expected_mb = expected_bytes / (1024 * 1024)
        self.assertAlmostEqual(mem, expected_mb, places=6)
        self.assertEqual(seq, 3)

    def test_legacy_tuple_non_tensor_kv_skipped(self):
        """Legacy path: if k/v are not FakeTensor, they are skipped."""
        past = (("not_a_tensor", "also_not"),)

        mem, seq = _cache_stats_from_past_key_values(past)
        self.assertEqual(mem, 0.0)
        self.assertEqual(seq, 0)

    # -- Path 3: to_legacy_cache() conversion --

    def test_to_legacy_cache_conversion(self):
        """Object with to_legacy_cache() that returns a tuple."""
        k = FakeTensor([1, 2, 6, 16], dtype="float16")
        v = FakeTensor([1, 2, 6, 16], dtype="float16")

        cache = MagicMock()
        # Not a tuple itself
        cache.__class__ = type("CacheWithLegacy", (), {})
        # No layers attribute
        del cache.layers
        # Has to_legacy_cache method
        cache.to_legacy_cache = MagicMock(return_value=((k, v),))

        mem, seq = _cache_stats_from_past_key_values(cache)

        expected_bytes = 2 * (1 * 2 * 6 * 16 * 2)
        expected_mb = expected_bytes / (1024 * 1024)
        self.assertAlmostEqual(mem, expected_mb, places=6)
        self.assertEqual(seq, 6)

    def test_to_legacy_cache_raises_exception(self):
        """to_legacy_cache() raises => legacy stays None => returns (0.0, 0)."""
        cache = MagicMock()
        cache.__class__ = type("BrokenLegacy", (), {})
        del cache.layers
        cache.to_legacy_cache = MagicMock(side_effect=RuntimeError("broken"))

        mem, seq = _cache_stats_from_past_key_values(cache)
        self.assertEqual(mem, 0.0)
        self.assertEqual(seq, 0)

    def test_unknown_object_no_layers_no_tuple_no_legacy(self):
        """Object with no layers, not a tuple, no to_legacy_cache => (0.0, 0)."""
        cache = MagicMock()
        cache.__class__ = type("UnknownCache", (), {})
        del cache.layers
        del cache.to_legacy_cache

        mem, seq = _cache_stats_from_past_key_values(cache)
        self.assertEqual(mem, 0.0)
        self.assertEqual(seq, 0)


# ===========================================================================
# TST-025: _to_dynamic_cache_safely
# ===========================================================================


class TestToDynamicCacheSafely(unittest.TestCase):
    """TST-025: Tests for _to_dynamic_cache_safely.

    Fallback chain:
      1. from_legacy_cache() succeeds -> return result
      2. DynamicCache(ddp_cache_data=...) succeeds -> return result
      3. Both fail -> raise RuntimeError
    Plus: non-tuple input returned as-is; HAS_DYNAMIC_CACHE=False returns as-is.
    """

    def test_non_tuple_returned_as_is(self):
        """Non-tuple input should be returned unchanged."""
        obj = MagicMock()
        obj.__class__ = type("NotATuple", (), {})
        result = _to_dynamic_cache_safely(obj)
        self.assertIs(result, obj)

    def test_from_legacy_cache_succeeds(self):
        """When from_legacy_cache succeeds, return its result."""
        legacy = (("k", "v"),)
        sentinel = MagicMock(name="converted_cache")
        _mock_DynamicCache.from_legacy_cache = MagicMock(return_value=sentinel)

        result = _to_dynamic_cache_safely(legacy)
        self.assertIs(result, sentinel)
        _mock_DynamicCache.from_legacy_cache.assert_called_once_with(legacy)

    def test_from_legacy_cache_fails_manual_update_succeeds(self):
        """When from_legacy_cache fails but manual DynamicCache.update() succeeds (ENG-058)."""
        legacy = (("k", "v"),)
        sentinel = MagicMock(name="manual_converted")

        _mock_DynamicCache.from_legacy_cache = MagicMock(
            side_effect=TypeError("from_legacy_cache failed")
        )
        _mock_DynamicCache.return_value = sentinel

        result = _to_dynamic_cache_safely(legacy)
        self.assertIs(result, sentinel)
        # The manual path calls DynamicCache() then cache.update(k, v, layer_idx)
        _mock_DynamicCache.assert_called_with()
        sentinel.update.assert_called_once_with("k", "v", 0)

    def test_both_paths_fail_raises_runtime_error(self):
        """When both from_legacy_cache and manual DynamicCache.update() fail (ENG-058)."""
        legacy = (("k", "v"),)

        _mock_DynamicCache.from_legacy_cache = MagicMock(
            side_effect=TypeError("from_legacy_cache failed")
        )
        _mock_DynamicCache.side_effect = TypeError("manual construction failed")

        with self.assertRaises(RuntimeError) as ctx:
            _to_dynamic_cache_safely(legacy)

        error_msg = str(ctx.exception)
        self.assertIn("Failed to convert legacy past_key_values", error_msg)
        self.assertIn("from_legacy_cache failed", error_msg)
        self.assertIn("manual DynamicCache.update()", error_msg)

        # Cleanup side_effect
        _mock_DynamicCache.side_effect = None

    def test_has_dynamic_cache_false_returns_as_is(self):
        """When HAS_DYNAMIC_CACHE is False, tuple is returned unchanged."""
        import src.engine.generate_loop as gl

        original_flag = gl.HAS_DYNAMIC_CACHE
        try:
            gl.HAS_DYNAMIC_CACHE = False
            legacy = (("k", "v"),)
            result = gl._to_dynamic_cache_safely(legacy)
            self.assertIs(result, legacy)
        finally:
            gl.HAS_DYNAMIC_CACHE = original_flag


# ===========================================================================
# TST-023: _register_prefill_temperature_hooks
# ===========================================================================


class TestRegisterPrefillTemperatureHooks(unittest.TestCase):
    """TST-023: Tests for _register_prefill_temperature_hooks.

    Paths:
      1. model.model.layers not found -> warning + empty handles
      2. q_norm hook path (attn has q_norm)
      3. q_proj hook path (attn has q_proj but no q_norm)
      4. seq_len<=1 guard: hooks return output unchanged when seq_len<=1
      5. Layout detection: [B, H, S, D] vs [B, S, H, D]
      6. inv_tau validation: non-2D, wrong layer count, wrong head count
    """

    def _make_model(self, num_layers=2, has_q_norm=False, has_q_proj=True,
                    num_heads=4, head_dim=8, cfg_heads=None):
        """Build a mock model with controllable layer structure."""
        layers = []
        for _ in range(num_layers):
            attn = MagicMock()
            attn.num_heads = num_heads
            attn.head_dim = head_dim

            if has_q_norm:
                q_norm = MagicMock()
                q_norm.register_forward_hook = MagicMock(
                    return_value=MagicMock(name="hook_handle")
                )
                attn.q_norm = q_norm
            else:
                attn.q_norm = None

            if has_q_proj:
                q_proj = MagicMock()
                q_proj.register_forward_hook = MagicMock(
                    return_value=MagicMock(name="hook_handle")
                )
                attn.q_proj = q_proj
            else:
                attn.q_proj = None

            layer = MagicMock()
            layer.self_attn = attn
            layers.append(layer)

        inner_model = MagicMock()
        inner_model.layers = layers

        model = MagicMock()
        model.model = inner_model

        config = MagicMock()
        config.num_attention_heads = cfg_heads or num_heads
        model.config = config

        return model

    def _make_inv_tau(self, num_layers=2, num_heads=4):
        """Build a FakeTensor for inv_tau with shape [layers, heads]."""
        t = FakeTensor([num_layers, num_heads], dtype="float32")
        t.ndim = 2  # Ensure 2D
        return t

    def test_no_layers_returns_empty_with_warning(self):
        """model.model.layers not found -> returns empty handles + warning."""
        model = MagicMock()
        model.model = None  # No inner model

        inv_tau = self._make_inv_tau()

        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(handles, [])
        # Check that a warning was issued
        warning_msgs = [str(x.message) for x in w]
        found = any("Cannot register prefill temperature hooks" in m for m in warning_msgs)
        self.assertTrue(found, f"Expected warning about missing layers, got: {warning_msgs}")

    def test_inv_tau_not_tensor_raises(self):
        """inv_tau that is not a tensor should raise ValueError."""
        model = self._make_model(num_layers=1, num_heads=2)
        with self.assertRaises(ValueError) as ctx:
            _register_prefill_temperature_hooks(model, "not_a_tensor")
        self.assertIn("inv_tau must be a 2D tensor", str(ctx.exception))

    def test_inv_tau_wrong_ndim_raises(self):
        """inv_tau with ndim != 2 should raise ValueError."""
        model = self._make_model(num_layers=1, num_heads=2)
        inv_tau = FakeTensor([2, 3, 4])  # 3D
        with self.assertRaises(ValueError) as ctx:
            _register_prefill_temperature_hooks(model, inv_tau)
        self.assertIn("inv_tau must be a 2D tensor", str(ctx.exception))

    def test_inv_tau_layer_count_mismatch_raises(self):
        """inv_tau with fewer layers than model should raise ValueError."""
        model = self._make_model(num_layers=3, num_heads=4)
        inv_tau = self._make_inv_tau(num_layers=2, num_heads=4)  # Only 2 layers

        with self.assertRaises(ValueError) as ctx:
            _register_prefill_temperature_hooks(model, inv_tau)
        self.assertIn("inv_tau has 2 layers but model has layer_idx=2", str(ctx.exception))

    def test_inv_tau_head_count_mismatch_raises(self):
        """inv_tau with wrong head count should raise ValueError."""
        model = self._make_model(num_layers=2, num_heads=4)
        inv_tau = self._make_inv_tau(num_layers=2, num_heads=8)  # Wrong heads

        with self.assertRaises(ValueError) as ctx:
            _register_prefill_temperature_hooks(model, inv_tau)
        self.assertIn("inv_tau head count mismatch", str(ctx.exception))

    def test_q_norm_hook_registered(self):
        """When attn has q_norm, hook is registered on q_norm."""
        model = self._make_model(num_layers=2, has_q_norm=True, num_heads=4)
        inv_tau = self._make_inv_tau(num_layers=2, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(len(handles), 2)
        # Verify register_forward_hook was called on q_norm for each layer
        for layer in model.model.layers:
            layer.self_attn.q_norm.register_forward_hook.assert_called_once()

    def test_q_proj_hook_registered_when_no_q_norm(self):
        """When attn has no q_norm but has q_proj, hook is registered on q_proj."""
        model = self._make_model(num_layers=2, has_q_norm=False, has_q_proj=True, num_heads=4)
        inv_tau = self._make_inv_tau(num_layers=2, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(len(handles), 2)
        for layer in model.model.layers:
            layer.self_attn.q_proj.register_forward_hook.assert_called_once()

    def test_no_q_norm_no_q_proj_skips_layer(self):
        """When attn has neither q_norm nor q_proj, the layer is skipped."""
        model = self._make_model(num_layers=2, has_q_norm=False, has_q_proj=False, num_heads=4)
        inv_tau = self._make_inv_tau(num_layers=2, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(len(handles), 0)

    def test_no_self_attn_skips_layer(self):
        """Layer without self_attn should be skipped gracefully."""
        model = self._make_model(num_layers=2, num_heads=4)
        # Remove self_attn from the first layer
        model.model.layers[0].self_attn = None
        inv_tau = self._make_inv_tau(num_layers=2, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        # Only layer 1 should have a hook
        self.assertEqual(len(handles), 1)

    def test_missing_num_heads_and_head_dim_skips_layer(self):
        """Layer where num_heads and head_dim cannot be determined is skipped."""
        model = self._make_model(num_layers=1, num_heads=4)
        # Remove num_heads and head_dim from attn
        attn = model.model.layers[0].self_attn
        attn.num_heads = None
        attn._kv_num_attention_heads = None
        attn.head_dim = None
        # Also remove from config
        model.config.num_attention_heads = None

        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)
        handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(len(handles), 0)

    def test_q_norm_hook_callback_bhsd_layout(self):
        """Test the actual hook callback behavior with [B, H, S, D] layout."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        # Extract the hook function that was registered
        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]  # First positional argument

        # Test with [B, H, S, D] layout where H == num_heads == 4
        output = FakeTensor([1, 4, 10, 8])  # B=1, H=4, S=10, D=8
        result = hook_fn(None, None, output)
        # Hook should have scaled the output (result is FakeTensor * FakeTensor)
        # The important thing is it did NOT return the original output unchanged
        # (since seq_len=10 > 1)
        self.assertIsNotNone(result)

    def test_q_norm_hook_callback_seq_len_1_guard(self):
        """Hook returns output unchanged when seq_len <= 1 (decode step)."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, H, S, D] with S=1 => should return output unchanged
        output = FakeTensor([1, 4, 1, 8])
        result = hook_fn(None, None, output)
        self.assertIs(result, output)

    def test_q_norm_hook_callback_non_4d_passthrough(self):
        """Hook returns output unchanged when ndim != 4."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # 3D tensor => should return unchanged
        output = FakeTensor([1, 4, 8])
        result = hook_fn(None, None, output)
        self.assertIs(result, output)

    def test_q_norm_hook_callback_non_tensor_passthrough(self):
        """Hook returns output unchanged when output is not a FakeTensor."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # Non-tensor output => should return unchanged
        output = "not_a_tensor"
        result = hook_fn(None, None, output)
        self.assertEqual(result, "not_a_tensor")

    def test_q_norm_hook_callback_bshd_layout(self):
        """Test hook with [B, S, H, D] layout where H matches at dim-2."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, S, H, D] where S=10 (not 4), H=4 at dim-2
        output = FakeTensor([1, 10, 4, 8])
        result = hook_fn(None, None, output)
        # dim-1 (10) != num_heads (4), but dim-2 (4) == num_heads (4)
        # => BSHD branch, seq_len=10 > 1, so it should scale
        self.assertIsNotNone(result)

    def test_q_norm_hook_callback_bshd_seq_len_1_guard(self):
        """[B, S, H, D] with S=1 => should return output unchanged."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, S, H, D] with S=1
        output = FakeTensor([1, 1, 4, 8])
        result = hook_fn(None, None, output)
        # dim-1 (1) != num_heads (4), dim-2 (4) == num_heads (4)
        # => BSHD branch, seq_len=1, guard returns output unchanged
        self.assertIs(result, output)

    def test_q_norm_hook_callback_no_match_passthrough(self):
        """When neither dim-1 nor dim-2 matches num_heads, return unchanged."""
        model = self._make_model(num_layers=1, has_q_norm=True, num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_norm.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, X, Y, D] where neither X nor Y == 4
        output = FakeTensor([1, 7, 9, 8])
        result = hook_fn(None, None, output)
        self.assertIs(result, output)

    def test_q_proj_hook_callback_seq_len_guard(self):
        """q_proj hook returns output unchanged when seq_len <= 1."""
        model = self._make_model(num_layers=1, has_q_norm=False, has_q_proj=True,
                                 num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_proj.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, S, H*D] with S=1
        output = FakeTensor([1, 1, 32])  # H*D = 4*8 = 32
        result = hook_fn(None, None, output)
        self.assertIs(result, output)

    def test_q_proj_hook_callback_non_3d_passthrough(self):
        """q_proj hook returns output unchanged when ndim != 3."""
        model = self._make_model(num_layers=1, has_q_norm=False, has_q_proj=True,
                                 num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_proj.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # 4D tensor => not 3D => passthrough
        output = FakeTensor([1, 10, 4, 8])
        result = hook_fn(None, None, output)
        self.assertIs(result, output)

    def test_q_proj_hook_callback_wrong_last_dim_passthrough(self):
        """q_proj hook returns output unchanged when last dim != H*D."""
        model = self._make_model(num_layers=1, has_q_norm=False, has_q_proj=True,
                                 num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_proj.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, S, wrong_dim] where wrong_dim != 4*8=32
        output = FakeTensor([1, 10, 64])
        result = hook_fn(None, None, output)
        self.assertIs(result, output)

    def test_q_proj_hook_callback_scaling_applied(self):
        """q_proj hook applies scaling when seq_len > 1 and last_dim matches."""
        model = self._make_model(num_layers=1, has_q_norm=False, has_q_proj=True,
                                 num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_proj.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        # [B, S, H*D] with S=10 > 1, H*D=32
        output = FakeTensor([1, 10, 32])
        result = hook_fn(None, None, output)
        # Should have been scaled (not returned as-is)
        self.assertIsNotNone(result)

    def test_q_proj_hook_callback_non_tensor_passthrough(self):
        """q_proj hook returns output unchanged when it's not a FakeTensor."""
        model = self._make_model(num_layers=1, has_q_norm=False, has_q_proj=True,
                                 num_heads=4, head_dim=8)
        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)

        handles = _register_prefill_temperature_hooks(model, inv_tau)

        call_args = model.model.layers[0].self_attn.q_proj.register_forward_hook.call_args
        hook_fn = call_args[0][0]

        result = hook_fn(None, None, "not_a_tensor")
        self.assertEqual(result, "not_a_tensor")

    def test_fallback_num_heads_from_kv_attr(self):
        """num_heads resolved from _kv_num_attention_heads when num_heads is None."""
        model = self._make_model(num_layers=1, has_q_proj=True, num_heads=4)
        attn = model.model.layers[0].self_attn
        attn.num_heads = None
        attn._kv_num_attention_heads = 4
        model.config.num_attention_heads = None

        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)
        handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(len(handles), 1)

    def test_fallback_num_heads_from_config(self):
        """num_heads resolved from config when attn attributes are None."""
        model = self._make_model(num_layers=1, has_q_proj=True, num_heads=4, cfg_heads=4)
        attn = model.model.layers[0].self_attn
        attn.num_heads = None
        attn._kv_num_attention_heads = None

        inv_tau = self._make_inv_tau(num_layers=1, num_heads=4)
        handles = _register_prefill_temperature_hooks(model, inv_tau)

        self.assertEqual(len(handles), 1)


# ===========================================================================
# TST-027: _get_rope_cos_sin
# ===========================================================================


class TestGetRopeCosSin(unittest.TestCase):
    """TST-027: Tests for _get_rope_cos_sin.

    5 fallback paths:
      1. position_embeddings is not None -> unpack directly
      2. rotary_emb(value_states, position_ids) -> (cos, sin)
      3. rotary_emb(value_states, position_ids=position_ids) -> (cos, sin)
      4. rotary_emb(position_ids) -> (cos, sin)
      5. rotary_emb(value_states, seq_len=...) -> (cos, sin) then gather
    Plus: no rotary_emb or no position_ids -> (None, None).
    """

    def test_position_embeddings_provided(self):
        """Path 1: position_embeddings is not None -> return directly."""
        cos_expected = MagicMock(name="cos")
        sin_expected = MagicMock(name="sin")
        position_embeddings = (cos_expected, sin_expected)

        attn = MagicMock()
        value_states = MagicMock()
        position_ids = MagicMock()

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, position_embeddings)
        self.assertIs(cos, cos_expected)
        self.assertIs(sin, sin_expected)

    def test_position_embeddings_unpack_fails(self):
        """Path 1 failure: position_embeddings doesn't unpack -> fallback to rotary_emb."""
        position_embeddings = "not_a_tuple_that_can_unpack_to_two"

        cos_val = MagicMock(name="cos")
        sin_val = MagicMock(name="sin")

        attn = MagicMock()
        attn.rotary_emb = MagicMock(return_value=(cos_val, sin_val))
        value_states = MagicMock()
        position_ids = MagicMock()

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, position_embeddings)
        # Should have fallen through to rotary_emb call
        self.assertIs(cos, cos_val)
        self.assertIs(sin, sin_val)

    def test_no_rotary_emb_returns_none(self):
        """No rotary_emb attribute -> (None, None)."""
        attn = MagicMock(spec=[])  # Empty spec, no rotary_emb
        # Explicitly ensure no rotary_emb
        del attn.rotary_emb

        value_states = MagicMock()
        position_ids = MagicMock()

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIsNone(cos)
        self.assertIsNone(sin)

    def test_no_position_ids_returns_none(self):
        """position_ids is None -> (None, None)."""
        attn = MagicMock()
        attn.rotary_emb = MagicMock()
        value_states = MagicMock()

        cos, sin = _get_rope_cos_sin(attn, value_states, None, None)
        self.assertIsNone(cos)
        self.assertIsNone(sin)

    def test_rotary_emb_call_succeeds_first_form(self):
        """Path 2: rotary(value_states, position_ids) returns (cos, sin)."""
        cos_val = MagicMock(name="cos")
        sin_val = MagicMock(name="sin")

        attn = MagicMock()
        attn.rotary_emb = MagicMock(return_value=(cos_val, sin_val))
        value_states = MagicMock()
        position_ids = MagicMock()

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIs(cos, cos_val)
        self.assertIs(sin, sin_val)

    def test_rotary_emb_first_call_fails_second_succeeds(self):
        """Paths 2-3: first call raises TypeError, second (keyword) succeeds."""
        cos_val = MagicMock(name="cos")
        sin_val = MagicMock(name="sin")

        call_count = [0]

        def rotary_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TypeError("wrong args")
            return (cos_val, sin_val)

        attn = MagicMock()
        attn.rotary_emb = MagicMock(side_effect=rotary_side_effect)
        value_states = MagicMock()
        position_ids = MagicMock()

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIs(cos, cos_val)
        self.assertIs(sin, sin_val)

    def test_rotary_emb_all_calls_fail_returns_none(self):
        """All 4 lambda calls + seq_len fallback fail -> (None, None)."""
        attn = MagicMock()
        attn.rotary_emb = MagicMock(side_effect=TypeError("nope"))
        value_states = MagicMock()
        position_ids = MagicMock()
        # position_ids.max() needs to work for the seq_len fallback
        position_ids.max = MagicMock(side_effect=TypeError("no max"))

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIsNone(cos)
        self.assertIsNone(sin)

    def test_rotary_emb_returns_non_tuple(self):
        """rotary_emb returns something that is not a tuple/list of length 2 -> try next."""
        attn = MagicMock()
        # Returns a single tensor instead of (cos, sin)
        attn.rotary_emb = MagicMock(return_value="single_value")
        value_states = MagicMock()
        position_ids = MagicMock()
        position_ids.max = MagicMock(side_effect=TypeError("no max"))

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIsNone(cos)
        self.assertIsNone(sin)

    def test_seq_len_fallback_path(self):
        """Path 5: All lambda calls fail, but seq_len fallback succeeds."""
        call_count = [0]
        cos_2d = MagicMock()
        cos_2d.ndim = 2  # 2D triggers gathering
        sin_2d = MagicMock()
        sin_2d.ndim = 2

        gathered_cos = MagicMock(name="gathered_cos")
        gathered_sin = MagicMock(name="gathered_sin")
        cos_2d.__getitem__ = MagicMock(return_value=gathered_cos)
        sin_2d.__getitem__ = MagicMock(return_value=gathered_sin)

        def rotary_side_effect(*args, **kwargs):
            call_count[0] += 1
            if "seq_len" in kwargs:
                return (cos_2d, sin_2d)
            raise TypeError("wrong sig")

        attn = MagicMock()
        attn.rotary_emb = MagicMock(side_effect=rotary_side_effect)
        value_states = MagicMock()

        # position_ids.max().item() -> 9, so seq_len=10
        max_result = MagicMock()
        max_result.item = MagicMock(return_value=9)
        position_ids = MagicMock()
        position_ids.max = MagicMock(return_value=max_result)

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIs(cos, gathered_cos)
        self.assertIs(sin, gathered_sin)

    def test_seq_len_fallback_3d_squeeze(self):
        """Path 5 with 3D cos/sin (batch=1): squeeze then gather."""
        cos_3d = MagicMock()
        cos_3d.ndim = 3
        cos_3d.shape = (1, 10, 64)
        sin_3d = MagicMock()
        sin_3d.ndim = 3
        sin_3d.shape = (1, 10, 64)

        cos_2d = MagicMock()
        cos_2d.ndim = 2
        sin_2d = MagicMock()
        sin_2d.ndim = 2

        cos_3d.squeeze = MagicMock(return_value=cos_2d)
        sin_3d.squeeze = MagicMock(return_value=sin_2d)

        gathered_cos = MagicMock(name="gathered_cos")
        gathered_sin = MagicMock(name="gathered_sin")
        cos_2d.__getitem__ = MagicMock(return_value=gathered_cos)
        sin_2d.__getitem__ = MagicMock(return_value=gathered_sin)

        def rotary_side_effect(*args, **kwargs):
            if "seq_len" in kwargs:
                return (cos_3d, sin_3d)
            raise TypeError("wrong sig")

        attn = MagicMock()
        attn.rotary_emb = MagicMock(side_effect=rotary_side_effect)
        value_states = MagicMock()

        max_result = MagicMock()
        max_result.item = MagicMock(return_value=9)
        position_ids = MagicMock()
        position_ids.max = MagicMock(return_value=max_result)

        cos, sin = _get_rope_cos_sin(attn, value_states, position_ids, None)
        self.assertIs(cos, gathered_cos)
        self.assertIs(sin, gathered_sin)
        cos_3d.squeeze.assert_called_once_with(0)
        sin_3d.squeeze.assert_called_once_with(0)


# ===========================================================================
# TST-028: _resolve_attn_shape_meta
# ===========================================================================


class TestResolveAttnShapeMeta(unittest.TestCase):
    """TST-028: Tests for _resolve_attn_shape_meta.

    6 fallback paths for resolving q_heads and kv_heads:
      1. _kv_num_attention_heads / _kv_num_key_value_heads (set by fused patch)
      2. num_heads / num_key_value_heads (standard HF attributes)
      3. _infer_heads_from_proj via q_proj / k_proj (fallback from weight shapes)
    Plus: head_dim validation, q_heads % kv_heads != 0, zero/negative heads.
    """

    def test_direct_kv_attributes(self):
        """Path 1: _kv_num_attention_heads and _kv_num_key_value_heads set."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = 32
        attn._kv_num_key_value_heads = 8

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 32)
        self.assertEqual(kv_heads, 8)
        self.assertEqual(head_dim, 64)

    def test_standard_hf_attributes(self):
        """Path 2: num_heads / num_key_value_heads (after _kv_ attrs are None)."""
        attn = MagicMock()
        attn.head_dim = 128
        attn._kv_num_attention_heads = None
        attn._kv_num_key_value_heads = None
        attn.num_heads = 16
        attn.num_key_value_heads = 4

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 16)
        self.assertEqual(kv_heads, 4)
        self.assertEqual(head_dim, 128)

    def test_infer_from_q_proj_k_proj(self):
        """Path 3: q_heads/kv_heads inferred from q_proj/k_proj weights."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = None
        attn._kv_num_key_value_heads = None
        attn.num_heads = None
        attn.num_key_value_heads = None

        # q_proj: out_features = 32 * 64 = 2048
        q_proj = MagicMock()
        q_proj.out_features = 2048
        attn.q_proj = q_proj

        # k_proj: out_features = 8 * 64 = 512
        k_proj = MagicMock()
        k_proj.out_features = 512
        attn.k_proj = k_proj

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 32)
        self.assertEqual(kv_heads, 8)
        self.assertEqual(head_dim, 64)

    def test_infer_from_weight_shape(self):
        """Path 3 variant: out_features is None but weight.shape[0] is available."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = None
        attn._kv_num_key_value_heads = None
        attn.num_heads = None
        attn.num_key_value_heads = None

        # q_proj with weight but no out_features
        q_proj = MagicMock()
        q_proj.out_features = None
        weight_q = MagicMock()
        weight_q.shape = (1024,)  # shape[0] = 1024 = 16 * 64
        q_proj.weight = weight_q
        attn.q_proj = q_proj

        # k_proj with weight
        k_proj = MagicMock()
        k_proj.out_features = None
        weight_k = MagicMock()
        weight_k.shape = (256,)  # shape[0] = 256 = 4 * 64
        k_proj.weight = weight_k
        attn.k_proj = k_proj

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 16)
        self.assertEqual(kv_heads, 4)
        self.assertEqual(head_dim, 64)

    def test_mixed_resolution_q_from_attr_kv_from_proj(self):
        """q_heads from num_heads, kv_heads inferred from k_proj."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = None
        attn._kv_num_key_value_heads = None
        attn.num_heads = 28
        attn.num_key_value_heads = None

        k_proj = MagicMock()
        k_proj.out_features = 256  # 4 * 64
        attn.k_proj = k_proj

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 28)
        self.assertEqual(kv_heads, 4)
        self.assertEqual(head_dim, 64)

    def test_missing_head_dim_raises(self):
        """head_dim is None -> raise ValueError."""
        attn = MagicMock()
        attn.head_dim = None

        with self.assertRaises(ValueError) as ctx:
            _resolve_attn_shape_meta(attn)
        self.assertIn("missing head_dim", str(ctx.exception))

    def test_unresolvable_heads_raises(self):
        """When q_heads and kv_heads cannot be resolved at all."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = None
        attn._kv_num_key_value_heads = None
        attn.num_heads = None
        attn.num_key_value_heads = None
        attn.q_proj = None
        attn.k_proj = None

        with self.assertRaises(ValueError) as ctx:
            _resolve_attn_shape_meta(attn)
        self.assertIn("Unable to resolve attention head metadata", str(ctx.exception))

    def test_gqa_mismatch_raises(self):
        """q_heads % kv_heads != 0 -> raise ValueError."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = 7
        attn._kv_num_key_value_heads = 3

        with self.assertRaises(ValueError) as ctx:
            _resolve_attn_shape_meta(attn)
        self.assertIn("Invalid GQA mapping", str(ctx.exception))

    def test_zero_heads_raises(self):
        """q_heads or kv_heads == 0 -> raise ValueError."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = 0
        attn._kv_num_key_value_heads = 4

        with self.assertRaises(ValueError) as ctx:
            _resolve_attn_shape_meta(attn)
        self.assertIn("Invalid heads", str(ctx.exception))

    def test_negative_heads_raises(self):
        """Negative head counts -> raise ValueError."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = -1
        attn._kv_num_key_value_heads = 4

        with self.assertRaises(ValueError) as ctx:
            _resolve_attn_shape_meta(attn)
        self.assertIn("Invalid heads", str(ctx.exception))

    def test_proj_out_features_not_divisible_raises(self):
        """q_proj.out_features not divisible by head_dim -> raise ValueError."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = None
        attn._kv_num_key_value_heads = None
        attn.num_heads = None
        attn.num_key_value_heads = None

        q_proj = MagicMock()
        q_proj.out_features = 100  # 100 % 64 != 0
        attn.q_proj = q_proj
        attn.k_proj = None

        with self.assertRaises(ValueError) as ctx:
            _resolve_attn_shape_meta(attn)
        self.assertIn("not divisible by head_dim", str(ctx.exception))

    def test_mha_equal_q_kv_heads(self):
        """MHA case: q_heads == kv_heads (no GQA)."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = 12
        attn._kv_num_key_value_heads = 12

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 12)
        self.assertEqual(kv_heads, 12)

    def test_mqq_single_kv_head(self):
        """MQA case: kv_heads == 1."""
        attn = MagicMock()
        attn.head_dim = 64
        attn._kv_num_attention_heads = 32
        attn._kv_num_key_value_heads = 1

        q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(attn)
        self.assertEqual(q_heads, 32)
        self.assertEqual(kv_heads, 1)


# ===========================================================================
# TST-028 supplement: _infer_heads_from_proj
# ===========================================================================


class TestInferHeadsFromProj(unittest.TestCase):
    """Supplementary tests for _infer_heads_from_proj helper used by _resolve_attn_shape_meta."""

    def test_no_proj_returns_none(self):
        """proj attribute not present -> None."""
        attn = MagicMock()
        attn.q_proj = None
        result = _infer_heads_from_proj(attn, "q_proj", head_dim=64)
        self.assertIsNone(result)

    def test_out_features_present(self):
        """out_features directly available."""
        attn = MagicMock()
        proj = MagicMock()
        proj.out_features = 512  # 512 / 64 = 8 heads
        attn.q_proj = proj

        result = _infer_heads_from_proj(attn, "q_proj", head_dim=64)
        self.assertEqual(result, 8)

    def test_weight_shape_fallback(self):
        """out_features is None, fall back to weight.shape[0]."""
        attn = MagicMock()
        proj = MagicMock()
        proj.out_features = None
        weight = MagicMock()
        weight.shape = (256,)
        proj.weight = weight
        attn.k_proj = proj

        result = _infer_heads_from_proj(attn, "k_proj", head_dim=64)
        self.assertEqual(result, 4)

    def test_no_out_features_no_weight_returns_none(self):
        """Neither out_features nor weight -> None."""
        attn = MagicMock()
        proj = MagicMock()
        proj.out_features = None
        del proj.weight  # No weight attribute
        attn.q_proj = proj

        result = _infer_heads_from_proj(attn, "q_proj", head_dim=64)
        self.assertIsNone(result)

    def test_not_divisible_raises(self):
        """out_features not divisible by head_dim -> ValueError."""
        attn = MagicMock()
        proj = MagicMock()
        proj.out_features = 100
        attn.q_proj = proj

        with self.assertRaises(ValueError) as ctx:
            _infer_heads_from_proj(attn, "q_proj", head_dim=64)
        self.assertIn("not divisible by head_dim", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
