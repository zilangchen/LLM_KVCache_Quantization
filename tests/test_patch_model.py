"""Unit tests for src/engine/patch_model.py functions.

Covers:
  TST-020: _decode_attn_int8_torch_ref  (reference INT8 decode attention)
  TST-021: _apply_rope / _rotate_half   (RoPE reference implementation)
  TST-022: INT8CacheWrapperContainer / INT8CacheWrapper (HF Cache adapter)
  TST-029: _materialize_int4_cache_as_int8  (bit_packed vs unpacked paths)
"""

import math
import unittest

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def _require_torch(cls):
    """Class decorator that skips the entire TestCase when PyTorch is missing."""
    return unittest.skipUnless(HAS_TORCH, "PyTorch is not available")(cls)


# ---------------------------------------------------------------------------
# TST-021: _rotate_half / _apply_rope
# ---------------------------------------------------------------------------


@_require_torch
class TestRotateHalf(unittest.TestCase):
    """Direct tests for _rotate_half helper."""

    def _get_fn(self):
        from src.engine.patch_model import _rotate_half

        return _rotate_half

    def test_basic_shape_preserved(self):
        fn = self._get_fn()
        x = torch.randn(2, 4, 1, 8)
        y = fn(x)
        self.assertEqual(y.shape, x.shape)

    def test_known_values(self):
        """_rotate_half([a, b, c, d]) -> [-c, -d, a, b]."""
        fn = self._get_fn()
        x = torch.tensor([[[[1.0, 2.0, 3.0, 4.0]]]])  # [1,1,1,4]
        y = fn(x)
        expected = torch.tensor([[[[-3.0, -4.0, 1.0, 2.0]]]])
        self.assertTrue(torch.allclose(y, expected))

    def test_involution_property(self):
        """Applying _rotate_half twice is equivalent to negation."""
        fn = self._get_fn()
        x = torch.randn(1, 2, 1, 6)
        y = fn(fn(x))
        self.assertTrue(torch.allclose(y, -x, atol=1e-6))


@_require_torch
class TestApplyRope(unittest.TestCase):
    """Tests for _apply_rope (RoPE embedding application)."""

    def _get_fn(self):
        from src.engine.patch_model import _apply_rope

        return _apply_rope

    def test_identity_rotation(self):
        """cos=1, sin=0 should leave Q/K unchanged (full rotary dim)."""
        fn = self._get_fn()
        B, H, S, D = 1, 2, 1, 8
        q = torch.randn(B, H, S, D, dtype=torch.float32)
        k = torch.randn(B, H, S, D, dtype=torch.float32)
        cos = torch.ones(B, S, D)
        sin = torch.zeros(B, S, D)

        q_out, k_out = fn(q, k, cos, sin)

        self.assertTrue(torch.allclose(q_out, q, atol=1e-5))
        self.assertTrue(torch.allclose(k_out, k, atol=1e-5))

    def test_90_degree_rotation(self):
        """cos=0, sin=1: Q_out = _rotate_half(Q) for full rotary dim.

        For a vector [a, b, c, d] with cos=0 and sin=1:
          q_embed = q * cos + _rotate_half(q) * sin = 0 + _rotate_half(q)
        """
        from src.engine.patch_model import _rotate_half

        fn = self._get_fn()
        B, H, S, D = 1, 1, 1, 4
        q = torch.tensor([[[[1.0, 2.0, 3.0, 4.0]]]])
        k = torch.tensor([[[[5.0, 6.0, 7.0, 8.0]]]])
        cos = torch.zeros(B, S, D)
        sin = torch.ones(B, S, D)

        q_out, k_out = fn(q, k, cos, sin)

        self.assertTrue(torch.allclose(q_out, _rotate_half(q), atol=1e-5))
        self.assertTrue(torch.allclose(k_out, _rotate_half(k), atol=1e-5))

    def test_cos_sin_2d_broadcast(self):
        """cos/sin with ndim==2 should be broadcast correctly."""
        fn = self._get_fn()
        B, H, S, D = 2, 3, 1, 6
        q = torch.randn(B, H, S, D, dtype=torch.float32)
        k = torch.randn(B, H, S, D, dtype=torch.float32)
        cos = torch.ones(S, D)  # 2D
        sin = torch.zeros(S, D)

        q_out, k_out = fn(q, k, cos, sin)
        self.assertTrue(torch.allclose(q_out, q, atol=1e-5))
        self.assertTrue(torch.allclose(k_out, k, atol=1e-5))

    def test_cos_sin_3d_bsz1_broadcast(self):
        """cos/sin with shape [1, S, D] should broadcast across batch."""
        fn = self._get_fn()
        B, H, S, D = 3, 2, 1, 4
        q = torch.randn(B, H, S, D, dtype=torch.float32)
        k = torch.randn(B, H, S, D, dtype=torch.float32)
        cos = torch.ones(1, S, D)
        sin = torch.zeros(1, S, D)

        q_out, k_out = fn(q, k, cos, sin)
        self.assertTrue(torch.allclose(q_out, q, atol=1e-5))

    def test_partial_rotary(self):
        """When rotary_dim < head_dim, the pass-through portion is unchanged."""
        fn = self._get_fn()
        B, H, S, D = 1, 1, 1, 8
        rotary_dim = 4
        q = torch.randn(B, H, S, D, dtype=torch.float32)
        k = torch.randn(B, H, S, D, dtype=torch.float32)
        cos = torch.ones(B, S, rotary_dim)
        sin = torch.zeros(B, S, rotary_dim)

        q_out, k_out = fn(q, k, cos, sin)

        # The pass-through portion [rotary_dim:] should be exactly unchanged.
        self.assertTrue(torch.equal(q_out[..., rotary_dim:], q[..., rotary_dim:]))
        self.assertTrue(torch.equal(k_out[..., rotary_dim:], k[..., rotary_dim:]))
        # The rotary portion should equal original (since cos=1, sin=0).
        self.assertTrue(
            torch.allclose(q_out[..., :rotary_dim], q[..., :rotary_dim], atol=1e-5)
        )

    def test_rotary_dim_exceeds_head_dim_raises(self):
        """rotary_dim > head_dim should raise ValueError."""
        fn = self._get_fn()
        B, H, S, D = 1, 1, 1, 4
        q = torch.randn(B, H, S, D)
        k = torch.randn(B, H, S, D)
        cos = torch.ones(B, S, D + 2)  # rotary_dim = D+2 > D
        sin = torch.zeros(B, S, D + 2)

        with self.assertRaises(ValueError):
            fn(q, k, cos, sin)

    def test_rope_equivariance(self):
        """RoPE(q) . RoPE(k) should differ from q.k by a rotation-invariant amount.

        Specifically, for vectors q and k of the same dimension, the dot product
        RoPE(q, theta) . RoPE(k, theta) should equal q . k for any angle theta,
        because RoPE is a rotation (isometry).
        """
        fn = self._get_fn()
        B, H, S, D = 1, 1, 1, 4
        q = torch.randn(B, H, S, D, dtype=torch.float64)
        k = torch.randn(B, H, S, D, dtype=torch.float64)

        theta = 0.7
        half = D // 2
        cos_vals = torch.full((B, S, D), math.cos(theta), dtype=torch.float64)
        sin_vals = torch.full((B, S, D), math.sin(theta), dtype=torch.float64)

        q_rot, k_rot = fn(q, k, cos_vals, sin_vals)

        dot_original = (q * k).sum()
        dot_rotated = (q_rot * k_rot).sum()

        self.assertTrue(
            torch.allclose(dot_original, dot_rotated, atol=1e-10),
            f"RoPE should preserve dot product: original={dot_original.item()}, "
            f"rotated={dot_rotated.item()}",
        )


# ---------------------------------------------------------------------------
# TST-020: _decode_attn_int8_torch_ref
# ---------------------------------------------------------------------------


@_require_torch
class TestDecodeAttnInt8TorchRef(unittest.TestCase):
    """Tests for the reference INT8 decode attention implementation."""

    def _get_fn(self):
        from src.engine.patch_model import _decode_attn_int8_torch_ref

        return _decode_attn_int8_torch_ref

    # -- helpers --

    @staticmethod
    def _make_simple_tensors(
        B=1,
        Hq=1,
        Hkv=1,
        S=4,
        D=4,
        G=1,
        dtype=None,
        ctx_len=None,
    ):
        """Create small, deterministic tensors for decode attention testing.

        K/V int8 values are small integers, scales are 1.0 so dequant == cast.
        """
        if dtype is None:
            dtype = torch.float16
        if ctx_len is None:
            ctx_len = S
        q = torch.randn(B, Hq, D, dtype=dtype)
        k_int8 = torch.randint(-3, 4, (B, Hkv, S, D), dtype=torch.int8)
        v_int8 = torch.randint(-3, 4, (B, Hkv, S, D), dtype=torch.int8)
        group_size = D // G
        k_scale = torch.ones(B, Hkv, S, G, dtype=dtype)
        v_scale = torch.ones(B, Hkv, S, G, dtype=dtype)
        context_lens = torch.full((B,), ctx_len, dtype=torch.int32)
        sm_scale = 1.0 / math.sqrt(D)
        return q, k_int8, v_int8, k_scale, v_scale, context_lens, sm_scale

    # -- shape tests --

    def test_output_shape_single_head(self):
        fn = self._get_fn()
        q, k, v, ks, vs, cl, sm = self._make_simple_tensors(B=1, Hq=1, Hkv=1, S=4, D=4)
        out = fn(q, k, v, ks, vs, cl, sm)
        self.assertEqual(out.shape, (1, 1, 4))

    def test_output_shape_multi_head(self):
        fn = self._get_fn()
        q, k, v, ks, vs, cl, sm = self._make_simple_tensors(B=2, Hq=4, Hkv=4, S=8, D=8)
        out = fn(q, k, v, ks, vs, cl, sm)
        self.assertEqual(out.shape, (2, 4, 8))

    def test_output_shape_gqa(self):
        """GQA: q_heads=4, kv_heads=2 => n_rep=2."""
        fn = self._get_fn()
        q, k, v, ks, vs, cl, sm = self._make_simple_tensors(B=1, Hq=4, Hkv=2, S=6, D=8)
        out = fn(q, k, v, ks, vs, cl, sm)
        self.assertEqual(out.shape, (1, 4, 8))

    # -- correctness tests --

    def test_single_token_context(self):
        """With S=1 and scale=1.0, softmax is trivially 1.0, so output = V."""
        fn = self._get_fn()
        B, H, D = 1, 1, 4
        q = torch.ones(B, H, D, dtype=torch.float16)
        k_int8 = torch.ones(B, H, 1, D, dtype=torch.int8)
        v_int8 = torch.tensor([[[[2, 3, 4, 5]]]], dtype=torch.int8)
        k_scale = torch.ones(B, H, 1, 1, dtype=torch.float16)
        v_scale = torch.ones(B, H, 1, 1, dtype=torch.float16)
        context_lens = torch.tensor([1], dtype=torch.int32)

        out = fn(q, k_int8, v_int8, k_scale, v_scale, context_lens, sm_scale=1.0)

        # Softmax over single token is [1.0], so output should equal V dequantized.
        expected = torch.tensor([[[2.0, 3.0, 4.0, 5.0]]], dtype=torch.float16)
        self.assertTrue(
            torch.allclose(out, expected, atol=0.01),
            f"Expected {expected}, got {out}",
        )

    def test_zero_context_returns_zeros(self):
        """context_len=0 should return all zeros."""
        fn = self._get_fn()
        q, k, v, ks, vs, _, sm = self._make_simple_tensors(B=1, Hq=2, Hkv=2, S=4, D=4)
        context_lens = torch.tensor([0], dtype=torch.int32)
        out = fn(q, k, v, ks, vs, context_lens, sm)
        self.assertTrue(torch.all(out == 0))

    def test_attention_output_weighted_average(self):
        """With known Q, K, V (scale=1), verify output matches manual softmax computation."""
        fn = self._get_fn()
        B, H, D = 1, 1, 2
        S = 2

        q = torch.tensor([[[1.0, 0.0]]], dtype=torch.float16)  # [B, H, D]
        k_int8 = torch.tensor([[[[1, 0], [0, 1]]]], dtype=torch.int8)  # [B,H,S,D]
        v_int8 = torch.tensor([[[[1, 0], [0, 1]]]], dtype=torch.int8)  # [B,H,S,D]
        k_scale = torch.ones(B, H, S, 1, dtype=torch.float16)
        v_scale = torch.ones(B, H, S, 1, dtype=torch.float16)
        context_lens = torch.tensor([2], dtype=torch.int32)
        sm_scale = 1.0

        out = fn(q, k_int8, v_int8, k_scale, v_scale, context_lens, sm_scale)

        # Manual: scores = q . K^T = [1*1+0*0, 1*0+0*1] = [1, 0]
        # After softmax: probs = softmax([1, 0]) = [e/(e+1), 1/(e+1)]
        e = math.e
        p0 = e / (e + 1)
        p1 = 1.0 / (e + 1)
        expected = torch.tensor([[[p0 * 1 + p1 * 0, p0 * 0 + p1 * 1]]], dtype=torch.float16)
        self.assertTrue(
            torch.allclose(out.float(), expected.float(), atol=0.01),
            f"Expected {expected}, got {out}",
        )

    def test_group_wise_scale(self):
        """Verify group-wise dequantization works with G > 1."""
        fn = self._get_fn()
        B, H, D, S, G = 1, 1, 8, 2, 2
        q = torch.randn(B, H, D, dtype=torch.float16)
        k_int8 = torch.randint(-3, 4, (B, H, S, D), dtype=torch.int8)
        v_int8 = torch.randint(-3, 4, (B, H, S, D), dtype=torch.int8)
        k_scale = torch.rand(B, H, S, G, dtype=torch.float16) + 0.1
        v_scale = torch.rand(B, H, S, G, dtype=torch.float16) + 0.1
        context_lens = torch.tensor([S], dtype=torch.int32)
        sm_scale = 1.0 / math.sqrt(D)

        out = fn(q, k_int8, v_int8, k_scale, v_scale, context_lens, sm_scale)
        self.assertEqual(out.shape, (B, H, D))
        # Softmax output should be a proper weighted average => values bounded.
        self.assertFalse(torch.isnan(out).any())
        self.assertFalse(torch.isinf(out).any())

    def test_gqa_repeat_interleave(self):
        """With GQA (q_heads=2, kv_heads=1), the single KV head is repeated for both Q heads."""
        fn = self._get_fn()
        B, Hq, Hkv, S, D = 1, 2, 1, 3, 4

        q = torch.randn(B, Hq, D, dtype=torch.float16)
        k_int8 = torch.randint(-2, 3, (B, Hkv, S, D), dtype=torch.int8)
        v_int8 = torch.randint(-2, 3, (B, Hkv, S, D), dtype=torch.int8)
        k_scale = torch.ones(B, Hkv, S, 1, dtype=torch.float16)
        v_scale = torch.ones(B, Hkv, S, 1, dtype=torch.float16)
        context_lens = torch.tensor([S], dtype=torch.int32)
        sm_scale = 1.0 / math.sqrt(D)

        out = fn(q, k_int8, v_int8, k_scale, v_scale, context_lens, sm_scale)
        self.assertEqual(out.shape, (B, Hq, D))

    def test_batch_independence(self):
        """Different context lengths per batch element should not interfere."""
        fn = self._get_fn()
        B, H, D, S = 2, 1, 4, 6

        q = torch.randn(B, H, D, dtype=torch.float16)
        k_int8 = torch.randint(-2, 3, (B, H, S, D), dtype=torch.int8)
        v_int8 = torch.randint(-2, 3, (B, H, S, D), dtype=torch.int8)
        k_scale = torch.ones(B, H, S, 1, dtype=torch.float16)
        v_scale = torch.ones(B, H, S, 1, dtype=torch.float16)
        context_lens = torch.tensor([3, 6], dtype=torch.int32)
        sm_scale = 1.0 / math.sqrt(D)

        out = fn(q, k_int8, v_int8, k_scale, v_scale, context_lens, sm_scale)
        self.assertEqual(out.shape, (B, H, D))
        # Neither batch element should be NaN.
        self.assertFalse(torch.isnan(out).any())

    # -- validation / error tests --

    def test_invalid_q_ndim_raises(self):
        fn = self._get_fn()
        q = torch.randn(1, 1, 1, 4, dtype=torch.float16)  # 4D, expected 3D
        k = torch.randint(-1, 2, (1, 1, 2, 4), dtype=torch.int8)
        v = torch.randint(-1, 2, (1, 1, 2, 4), dtype=torch.int8)
        ks = torch.ones(1, 1, 2, 1, dtype=torch.float16)
        vs = torch.ones(1, 1, 2, 1, dtype=torch.float16)
        cl = torch.tensor([2], dtype=torch.int32)
        with self.assertRaises(ValueError):
            fn(q, k, v, ks, vs, cl, 1.0)

    def test_head_dim_mismatch_raises(self):
        fn = self._get_fn()
        q = torch.randn(1, 1, 4, dtype=torch.float16)
        k = torch.randint(-1, 2, (1, 1, 2, 6), dtype=torch.int8)  # D=6 != 4
        v = torch.randint(-1, 2, (1, 1, 2, 6), dtype=torch.int8)
        ks = torch.ones(1, 1, 2, 1, dtype=torch.float16)
        vs = torch.ones(1, 1, 2, 1, dtype=torch.float16)
        cl = torch.tensor([2], dtype=torch.int32)
        with self.assertRaises(ValueError):
            fn(q, k, v, ks, vs, cl, 1.0)

    def test_gqa_indivisible_raises(self):
        """q_heads=3, kv_heads=2 is not divisible => should raise."""
        fn = self._get_fn()
        q = torch.randn(1, 3, 4, dtype=torch.float16)
        k = torch.randint(-1, 2, (1, 2, 2, 4), dtype=torch.int8)
        v = torch.randint(-1, 2, (1, 2, 2, 4), dtype=torch.int8)
        ks = torch.ones(1, 2, 2, 1, dtype=torch.float16)
        vs = torch.ones(1, 2, 2, 1, dtype=torch.float16)
        cl = torch.tensor([2], dtype=torch.int32)
        with self.assertRaises(ValueError):
            fn(q, k, v, ks, vs, cl, 1.0)

    def test_output_dtype_matches_query(self):
        fn = self._get_fn()
        for dtype in [torch.float16, torch.bfloat16]:
            q, k, v, ks, vs, cl, sm = self._make_simple_tensors(
                B=1, Hq=1, Hkv=1, S=2, D=4, dtype=dtype
            )
            out = fn(q, k, v, ks, vs, cl, sm)
            self.assertEqual(out.dtype, dtype, f"Output dtype should match query dtype {dtype}")


# ---------------------------------------------------------------------------
# TST-022: INT8CacheWrapper / INT8CacheWrapperContainer
# ---------------------------------------------------------------------------


class _FakeCacheEngine:
    """Minimal mock cache engine for testing wrapper classes.

    Simulates get_int8_tensors, get_kv, append, get_seq_len.
    """

    def __init__(self, num_layers=4, seq_len=10):
        self.num_layers = num_layers
        self._seq_len = seq_len
        self._appended = []
        self._kv_data = {}

    def get_seq_len(self):
        return self._seq_len

    def get_int8_tensors(self, layer_idx):
        return (None, None, None, None)  # Stub

    def get_kv(self, layer_idx):
        return self._kv_data.get(layer_idx, (None, None))

    def append(self, layer_idx, key_states, value_states):
        self._appended.append((layer_idx, key_states, value_states))


class _FakeNonFusedEngine:
    """A mock engine that does NOT have get_int8_tensors or get_int4_tensors.

    This simulates kivi_style or fp16 engines that should be rejected.
    """

    def __init__(self):
        self.num_layers = 2

    def get_seq_len(self):
        return 5


@_require_torch
class TestINT8CacheWrapper(unittest.TestCase):
    """Tests for the per-layer INT8CacheWrapper."""

    def test_get_seq_length(self):
        from src.engine.patch_model import INT8CacheWrapper

        engine = _FakeCacheEngine(num_layers=4, seq_len=42)
        wrapper = INT8CacheWrapper(engine, layer_idx=2)
        self.assertEqual(wrapper.get_seq_length(), 42)
        # layer_idx argument should be ignored; always uses engine.get_seq_len().
        self.assertEqual(wrapper.get_seq_length(layer_idx=99), 42)

    def test_layer_idx_stored(self):
        from src.engine.patch_model import INT8CacheWrapper

        engine = _FakeCacheEngine()
        wrapper = INT8CacheWrapper(engine, layer_idx=7)
        self.assertEqual(wrapper.layer_idx, 7)

    def test_update_delegates_to_engine(self):
        from src.engine.patch_model import INT8CacheWrapper

        engine = _FakeCacheEngine()
        wrapper = INT8CacheWrapper(engine, layer_idx=1)
        k_stub = torch.zeros(1)
        v_stub = torch.ones(1)
        wrapper.update(k_stub, v_stub, layer_idx=1)
        self.assertEqual(len(engine._appended), 1)
        self.assertEqual(engine._appended[0][0], 1)

    def test_getitem(self):
        from src.engine.patch_model import INT8CacheWrapper

        engine = _FakeCacheEngine()
        engine._kv_data[3] = ("k3", "v3")
        wrapper = INT8CacheWrapper(engine, layer_idx=0)
        result = wrapper[3]
        self.assertEqual(result, ("k3", "v3"))

    def test_len(self):
        from src.engine.patch_model import INT8CacheWrapper

        engine = _FakeCacheEngine(num_layers=6)
        wrapper = INT8CacheWrapper(engine, layer_idx=0)
        self.assertEqual(len(wrapper), 6)

    def test_iter(self):
        from src.engine.patch_model import INT8CacheWrapper

        engine = _FakeCacheEngine(num_layers=3)
        for i in range(3):
            engine._kv_data[i] = (f"k{i}", f"v{i}")
        wrapper = INT8CacheWrapper(engine, layer_idx=0)
        items = list(wrapper)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0], ("k0", "v0"))
        self.assertEqual(items[2], ("k2", "v2"))


@_require_torch
class TestINT8CacheWrapperContainer(unittest.TestCase):
    """Tests for the container-level INT8CacheWrapperContainer."""

    def test_basic_creation(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=4)
        container = INT8CacheWrapperContainer(engine, num_layers=4)
        self.assertEqual(len(container), 4)

    def test_rejects_non_fused_engine(self):
        """Engines without get_int8_tensors/get_int4_tensors should be rejected."""
        from src.engine.patch_model import INT8CacheWrapperContainer

        bad_engine = _FakeNonFusedEngine()
        with self.assertRaises(TypeError):
            INT8CacheWrapperContainer(bad_engine, num_layers=2)

    def test_get_seq_length(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=2, seq_len=99)
        container = INT8CacheWrapperContainer(engine, num_layers=2)
        self.assertEqual(container.get_seq_length(), 99)

    def test_getitem_returns_wrapper(self):
        from src.engine.patch_model import INT8CacheWrapper, INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=3)
        container = INT8CacheWrapperContainer(engine, num_layers=3)
        w = container[1]
        self.assertIsInstance(w, INT8CacheWrapper)
        self.assertEqual(w.layer_idx, 1)

    def test_iter(self):
        from src.engine.patch_model import INT8CacheWrapper, INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=3)
        container = INT8CacheWrapperContainer(engine, num_layers=3)
        wrappers = list(container)
        self.assertEqual(len(wrappers), 3)
        for i, w in enumerate(wrappers):
            self.assertIsInstance(w, INT8CacheWrapper)
            self.assertEqual(w.layer_idx, i)

    def test_get_max_cache_shape_returns_none(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=2)
        container = INT8CacheWrapperContainer(engine, num_layers=2)
        self.assertIsNone(container.get_max_cache_shape())

    def test_to_legacy_cache(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=3)
        for i in range(3):
            engine._kv_data[i] = (f"k{i}", f"v{i}")
        container = INT8CacheWrapperContainer(engine, num_layers=3)
        legacy = container.to_legacy_cache()
        self.assertIsInstance(legacy, tuple)
        self.assertEqual(len(legacy), 3)
        self.assertEqual(legacy[0], ("k0", "v0"))

    def test_update_delegates(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=2)
        container = INT8CacheWrapperContainer(engine, num_layers=2)
        k_stub = torch.zeros(1)
        v_stub = torch.ones(1)
        container.update(k_stub, v_stub, layer_idx=0)
        self.assertEqual(len(engine._appended), 1)
        self.assertEqual(engine._appended[0][0], 0)

    def test_get_mask_sizes_no_cache_position(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=2, seq_len=50)
        container = INT8CacheWrapperContainer(engine, num_layers=2)
        kv_length, kv_offset = container.get_mask_sizes(cache_position=None, layer_idx=0)
        self.assertEqual(kv_length, 50)
        self.assertEqual(kv_offset, 0)

    def test_get_mask_sizes_with_cache_position(self):
        from src.engine.patch_model import INT8CacheWrapperContainer

        engine = _FakeCacheEngine(num_layers=2, seq_len=50)
        container = INT8CacheWrapperContainer(engine, num_layers=2)
        cache_position = torch.arange(5)  # 5 new tokens
        kv_length, kv_offset = container.get_mask_sizes(
            cache_position=cache_position, layer_idx=0
        )
        self.assertEqual(kv_length, 55)  # 50 cached + 5 new
        self.assertEqual(kv_offset, 0)


# ---------------------------------------------------------------------------
# TST-029: _materialize_int4_cache_as_int8
# ---------------------------------------------------------------------------


@_require_torch
class TestMaterializeInt4CacheAsInt8(unittest.TestCase):
    """Tests for _materialize_int4_cache_as_int8 (bit_packed vs unpacked paths)."""

    def _get_fn(self):
        from src.engine.patch_model import _materialize_int4_cache_as_int8

        return _materialize_int4_cache_as_int8

    # -- unpacked path (bit_packed=False) --

    def test_unpacked_passthrough(self):
        """When bit_packed=False and shapes match, return input as-is."""
        fn = self._get_fn()
        head_dim = 8
        k = torch.randint(-7, 8, (1, 2, 4, head_dim), dtype=torch.int8)
        v = torch.randint(-7, 8, (1, 2, 4, head_dim), dtype=torch.int8)
        k_out, v_out = fn(k, v, head_dim=head_dim, bit_packed=False)
        self.assertTrue(torch.equal(k_out, k))
        self.assertTrue(torch.equal(v_out, v))

    def test_unpacked_shape_mismatch_k_raises(self):
        """Unpacked path: wrong last dim on k should raise ValueError."""
        fn = self._get_fn()
        head_dim = 8
        k = torch.randint(-7, 8, (1, 2, 4, head_dim + 2), dtype=torch.int8)
        v = torch.randint(-7, 8, (1, 2, 4, head_dim), dtype=torch.int8)
        with self.assertRaises(ValueError):
            fn(k, v, head_dim=head_dim, bit_packed=False)

    def test_unpacked_shape_mismatch_v_raises(self):
        """Unpacked path: wrong last dim on v should raise ValueError."""
        fn = self._get_fn()
        head_dim = 8
        k = torch.randint(-7, 8, (1, 2, 4, head_dim), dtype=torch.int8)
        v = torch.randint(-7, 8, (1, 2, 4, head_dim - 2), dtype=torch.int8)
        with self.assertRaises(ValueError):
            fn(k, v, head_dim=head_dim, bit_packed=False)

    # -- packed path (bit_packed=True) --

    def test_packed_roundtrip(self):
        """Pack int4 values, then materialize should recover them."""
        from src.quant.int4_basic import pack_int4, unpack_int4

        fn = self._get_fn()
        head_dim = 8
        # Original int4 values in [-7, 7]
        k_orig = torch.randint(-7, 8, (1, 2, 4, head_dim), dtype=torch.int8)
        v_orig = torch.randint(-7, 8, (1, 2, 4, head_dim), dtype=torch.int8)

        # Pack: last dim becomes head_dim // 2
        k_packed = pack_int4(k_orig)
        v_packed = pack_int4(v_orig)
        self.assertEqual(k_packed.shape[-1], head_dim // 2)

        # Materialize should unpack back to head_dim
        k_out, v_out = fn(k_packed, v_packed, head_dim=head_dim, bit_packed=True)
        self.assertEqual(k_out.shape[-1], head_dim)
        self.assertEqual(v_out.shape[-1], head_dim)
        self.assertTrue(torch.equal(k_out, k_orig))
        self.assertTrue(torch.equal(v_out, v_orig))

    def test_packed_shape_mismatch_raises(self):
        """Packed path: last_dim * 2 != head_dim should raise ValueError."""
        fn = self._get_fn()
        head_dim = 8
        # Wrong packed dimension: head_dim//2 + 1 = 5
        k = torch.randint(-7, 8, (1, 2, 4, 5), dtype=torch.int8)
        v = torch.randint(-7, 8, (1, 2, 4, 5), dtype=torch.int8)
        with self.assertRaises(ValueError):
            fn(k, v, head_dim=head_dim, bit_packed=True)

    def test_packed_output_shape(self):
        """Packed path: output last dim should be head_dim (= input_dim * 2)."""
        from src.quant.int4_basic import pack_int4

        fn = self._get_fn()
        head_dim = 16
        k_orig = torch.randint(-7, 8, (2, 4, 8, head_dim), dtype=torch.int8)
        v_orig = torch.randint(-7, 8, (2, 4, 8, head_dim), dtype=torch.int8)
        k_packed = pack_int4(k_orig)
        v_packed = pack_int4(v_orig)

        k_out, v_out = fn(k_packed, v_packed, head_dim=head_dim, bit_packed=True)
        self.assertEqual(k_out.shape, k_orig.shape)
        self.assertEqual(v_out.shape, v_orig.shape)

    def test_packed_preserves_asymmetric_range(self):
        """Pack/unpack should handle the full asymmetric INT4 range [-8, 7]."""
        from src.quant.int4_basic import pack_int4

        fn = self._get_fn()
        head_dim = 4
        # Use extreme values including -8
        k = torch.tensor([[[[-8, -7, 0, 7]]]], dtype=torch.int8)
        v = torch.tensor([[[[7, 0, -7, -8]]]], dtype=torch.int8)
        k_packed = pack_int4(k)
        v_packed = pack_int4(v)

        k_out, v_out = fn(k_packed, v_packed, head_dim=head_dim, bit_packed=True)
        self.assertTrue(torch.equal(k_out, k))
        self.assertTrue(torch.equal(v_out, v))


# ---------------------------------------------------------------------------
# Additional: _parse_optional_int_env / _topk_summary (lightweight helpers)
# ---------------------------------------------------------------------------


@_require_torch
class TestTopkSummary(unittest.TestCase):
    """Tests for _topk_summary helper."""

    def _get_fn(self):
        from src.engine.patch_model import _topk_summary

        return _topk_summary

    def test_basic(self):
        fn = self._get_fn()
        t = torch.tensor([1.0, 5.0, 3.0, 2.0])
        result = fn(t, k=2)
        self.assertEqual(len(result["values"]), 2)
        self.assertAlmostEqual(result["values"][0], 5.0, places=4)

    def test_empty_tensor(self):
        fn = self._get_fn()
        t = torch.tensor([])
        result = fn(t, k=3)
        self.assertEqual(result["indices"], [])
        self.assertEqual(result["values"], [])

    def test_k_larger_than_numel(self):
        fn = self._get_fn()
        t = torch.tensor([10.0, 20.0])
        result = fn(t, k=8)
        self.assertEqual(len(result["values"]), 2)


@_require_torch
class TestParseOptionalIntEnv(unittest.TestCase):
    """Tests for _parse_optional_int_env.

    NOTE: Although this function itself does not use torch, importing it from
    src.engine.patch_model transitively requires torch (via src/engine/__init__.py),
    so we skip when torch is unavailable.
    """

    def _get_fn(self):
        from src.engine.patch_model import _parse_optional_int_env

        return _parse_optional_int_env

    def test_missing_env(self):
        import os

        fn = self._get_fn()
        key = "_TEST_PATCH_MODEL_NONEXISTENT_VAR_12345"
        os.environ.pop(key, None)
        self.assertIsNone(fn(key))

    def test_empty_env(self):
        import os

        fn = self._get_fn()
        key = "_TEST_PATCH_MODEL_EMPTY_VAR"
        os.environ[key] = ""
        try:
            self.assertIsNone(fn(key))
        finally:
            del os.environ[key]

    def test_valid_int(self):
        import os

        fn = self._get_fn()
        key = "_TEST_PATCH_MODEL_INT_VAR"
        os.environ[key] = "42"
        try:
            self.assertEqual(fn(key), 42)
        finally:
            del os.environ[key]

    def test_invalid_value(self):
        import os

        fn = self._get_fn()
        key = "_TEST_PATCH_MODEL_BAD_VAR"
        os.environ[key] = "not_a_number"
        try:
            self.assertIsNone(fn(key))
        finally:
            del os.environ[key]


if __name__ == "__main__":
    unittest.main()
