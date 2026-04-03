"""Unit tests for INT8 KV Cache."""

import unittest

import torch

from src.cache.int8_cache import INT8KVCache
from src.quant.int8_basic import (
    dequantize_symmetric_int8,
    quantize_symmetric_int8,
)


class TestINT8KVCacheBasic(unittest.TestCase):
    """Basic append / get / shape tests."""

    def setUp(self):
        self.B, self.H, self.D = 2, 4, 128
        self.num_layers = 2
        self.group_size = 64

    def test_append_get_shapes(self):
        cache = INT8KVCache(
            num_layers=self.num_layers,
            device="cpu",
            group_size=self.group_size,
        )
        k = torch.randn(self.B, self.H, 5, self.D, dtype=torch.float16)
        v = torch.randn(self.B, self.H, 5, self.D, dtype=torch.float16)
        cache.append(0, k, v)
        cache.append(1, k, v)

        self.assertEqual(cache.get_seq_len(), 5)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (self.B, self.H, 5, self.D))
        self.assertEqual(v_out.shape, (self.B, self.H, 5, self.D))
        self.assertEqual(k_out.dtype, torch.float16)

    def test_incremental_append(self):
        cache = INT8KVCache(
            num_layers=self.num_layers,
            device="cpu",
            group_size=self.group_size,
        )
        k1 = torch.randn(self.B, self.H, 3, self.D, dtype=torch.float16)
        v1 = torch.randn(self.B, self.H, 3, self.D, dtype=torch.float16)
        cache.append(0, k1, v1)
        self.assertEqual(cache.get_seq_len(), 3)

        k2 = torch.randn(self.B, self.H, 2, self.D, dtype=torch.float16)
        v2 = torch.randn(self.B, self.H, 2, self.D, dtype=torch.float16)
        cache.append(0, k2, v2)
        self.assertEqual(cache.get_seq_len(), 5)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (self.B, self.H, 5, self.D))

    def test_single_token_append(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
        )
        for step in range(1, 6):
            k = torch.randn(1, self.H, 1, self.D, dtype=torch.float16)
            v = torch.randn(1, self.H, 1, self.D, dtype=torch.float16)
            cache.append(0, k, v)
            self.assertEqual(cache.get_seq_len(), step)

    def test_empty_cache_raises(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size
        )
        with self.assertRaises(ValueError):
            cache.get_kv(0)

    def test_invalid_layer_id(self):
        cache = INT8KVCache(
            num_layers=2, device="cpu", group_size=self.group_size
        )
        k = torch.randn(1, self.H, 1, self.D, dtype=torch.float16)
        v = torch.randn(1, self.H, 1, self.D, dtype=torch.float16)
        with self.assertRaises(ValueError):
            cache.append(-1, k, v)
        with self.assertRaises(ValueError):
            cache.append(2, k, v)


class TestINT8KVCacheCapacity(unittest.TestCase):
    """Capacity management and expansion tests."""

    def test_capacity_doubling(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64
        )
        B, H, D = 1, 2, 128
        k = torch.randn(B, H, 300, D, dtype=torch.float16)
        v = torch.randn(B, H, 300, D, dtype=torch.float16)
        cache.append(0, k, v)
        cap_after_first = cache._layer_capacity[0]
        self.assertGreaterEqual(cap_after_first, 300)

        k2 = torch.randn(B, H, 1, D, dtype=torch.float16)
        v2 = torch.randn(B, H, 1, D, dtype=torch.float16)
        cache.append(0, k2, v2)
        self.assertEqual(cache.get_seq_len(), 301)

    def test_max_seq_len_cap(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
            max_seq_len=100,
        )
        B, H, D = 1, 2, 128
        k = torch.randn(B, H, 50, D, dtype=torch.float16)
        v = torch.randn(B, H, 50, D, dtype=torch.float16)
        cache.append(0, k, v)

        k2 = torch.randn(B, H, 51, D, dtype=torch.float16)
        v2 = torch.randn(B, H, 51, D, dtype=torch.float16)
        with self.assertRaises(ValueError):
            cache.append(0, k2, v2)


class TestINT8KVCacheQuantAccuracy(unittest.TestCase):
    """Quantization accuracy and roundtrip error tests."""

    def test_roundtrip_error_bounded(self):
        torch.manual_seed(42)
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
            clip_percentile=100.0,
        )
        B, H, S, D = 2, 4, 8, 128
        k = torch.randn(B, H, S, D, dtype=torch.float16)
        v = torch.randn(B, H, S, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)

        k_err = (k - k_out).abs().max().item()
        v_err = (v - v_out).abs().max().item()
        # TST-048: Theoretical INT8 symmetric max error ≈ absmax/254 ≈ 0.012 for
        # unit-variance randn.  Tolerance 0.1 is deliberately loose (~8× theoretical)
        # to avoid flaky failures from rare outlier values in random inputs.
        self.assertLess(k_err, 0.1, f"K roundtrip max error too large: {k_err}")
        self.assertLess(v_err, 0.1, f"V roundtrip max error too large: {v_err}")

    def test_static_scale_path(self):
        torch.manual_seed(42)
        B, H, S, D = 1, 2, 4, 128
        group_size = 64
        num_groups = D // group_size
        static_k = torch.full(
            (H, num_groups), 0.01, dtype=torch.float16
        )
        static_v = torch.full(
            (H, num_groups), 0.01, dtype=torch.float16
        )

        cache = INT8KVCache(
            num_layers=1,
            device="cpu",
            group_size=group_size,
            static_k_scale=[static_k],
            static_v_scale=[static_v],
        )
        k = torch.randn(B, H, S, D, dtype=torch.float16) * 0.5
        v = torch.randn(B, H, S, D, dtype=torch.float16) * 0.5
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, k.shape)
        self.assertTrue(torch.isfinite(k_out).all())


class TestINT8KVCacheMemory(unittest.TestCase):
    """Memory tracking tests."""

    def test_memory_positive(self):
        cache = INT8KVCache(
            num_layers=2, device="cpu", group_size=64
        )
        B, H, D = 1, 4, 128
        k = torch.randn(B, H, 10, D, dtype=torch.float16)
        v = torch.randn(B, H, 10, D, dtype=torch.float16)
        cache.append(0, k, v)
        cache.append(1, k, v)
        self.assertGreater(cache.get_memory_mb(), 0.0)

    def test_clear_resets_seq_len(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64
        )
        k = torch.randn(1, 2, 5, 128, dtype=torch.float16)
        v = torch.randn(1, 2, 5, 128, dtype=torch.float16)
        cache.append(0, k, v)
        self.assertEqual(cache.get_seq_len(), 5)
        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

    def test_release_frees_buffers(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64
        )
        k = torch.randn(1, 2, 5, 128, dtype=torch.float16)
        v = torch.randn(1, 2, 5, 128, dtype=torch.float16)
        cache.append(0, k, v)
        cache.release()
        self.assertEqual(cache.get_seq_len(), 0)
        self.assertIsNone(cache._k_cache[0])


class TestINT8KVCacheDecodeStats(unittest.TestCase):
    """Decode statistics tracking tests."""

    def test_stats_tracking(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64
        )
        cache.record_fused_decode(0, "triton_fused")
        cache.record_fused_decode(0, "torch_ref")
        cache.record_triton_kernel_call(0)

        stats = cache.get_decode_stats()
        self.assertEqual(stats["fused_decode_calls"], 2)
        self.assertEqual(stats["triton_decode_calls"], 1)
        self.assertEqual(stats["torch_ref_calls"], 1)
        self.assertEqual(stats["triton_kernel_calls"], 1)

    def test_stats_reset(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64
        )
        cache.record_fused_decode(0, "triton_fused")
        cache.reset_decode_stats()
        stats = cache.get_decode_stats()
        self.assertEqual(stats["fused_decode_calls"], 0)


class TestINT8KVCacheRawTensors(unittest.TestCase):
    """Tests for get_int8_tensors (raw access)."""

    def test_raw_tensors_shape_and_dtype(self):
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64
        )
        B, H, S, D = 1, 4, 8, 128
        num_groups = D // 64
        k = torch.randn(B, H, S, D, dtype=torch.float16)
        v = torch.randn(B, H, S, D, dtype=torch.float16)
        cache.append(0, k, v)

        k_int8, v_int8, k_scale, v_scale = cache.get_int8_tensors(0)
        self.assertEqual(k_int8.dtype, torch.int8)
        self.assertEqual(v_int8.dtype, torch.int8)
        self.assertEqual(k_int8.shape, (B, H, S, D))
        self.assertEqual(k_scale.shape, (B, H, S, num_groups))


class TestINT8AxisIndependence(unittest.TestCase):
    """TST-007 / TST-013: Verify per-token quantization axis independence.

    INT8 group-wise quantization operates along the head_dim axis.
    The scale is computed per (batch, head, seq_position, group), so:
    - Each token (seq position) gets its own independent scale.
    - Modifying one token should not affect another token's quantization.
    - Modifying one channel group should not affect another group's quantization.
    """

    def setUp(self):
        torch.manual_seed(42)
        self.B, self.H, self.S, self.D = 2, 4, 8, 128
        self.group_size = 64

    def test_scale_varies_per_token(self):
        """Scale must vary across seq positions (per-token quantization)."""
        # Construct tensor where each token has a different magnitude
        x = torch.zeros(1, 1, 4, self.D, dtype=torch.float32)
        x[0, 0, 0, :] = 1.0   # token 0: small values
        x[0, 0, 1, :] = 10.0  # token 1: medium values
        x[0, 0, 2, :] = 100.0 # token 2: large values
        x[0, 0, 3, :] = 0.01  # token 3: tiny values

        _, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.D)
        # scale shape: [1, 1, 4, 1] (num_groups=1 when group_size==D)
        # Each token should have a different scale
        scales_flat = scale[0, 0, :, 0]
        self.assertEqual(len(scales_flat.unique()), 4,
                         f"Expected 4 unique scales (one per token), got {scales_flat.unique()}")

    def test_scale_varies_per_group_within_token(self):
        """Scale must vary across groups within the same token (per-group quantization)."""
        x = torch.zeros(1, 1, 1, self.D, dtype=torch.float32)
        # Group 0 (first 64 dims): small
        x[0, 0, 0, :64] = 0.5
        # Group 1 (last 64 dims): large
        x[0, 0, 0, 64:] = 50.0

        _, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)
        # scale shape: [1, 1, 1, 2]
        self.assertNotAlmostEqual(
            scale[0, 0, 0, 0].item(),
            scale[0, 0, 0, 1].item(),
            places=2,
            msg="Scales for groups with different magnitudes should differ",
        )

    def test_modifying_one_token_does_not_affect_others(self):
        """Changing values in one token must not change quantization of other tokens."""
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float32)
        q_orig, s_orig = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)

        # Modify token 3 drastically
        x_mod = x.clone()
        x_mod[:, :, 3, :] = 999.0
        q_mod, s_mod = quantize_symmetric_int8(x_mod, percentile=100.0, group_size=self.group_size)

        # All tokens except token 3 should be identical
        for t in range(self.S):
            if t == 3:
                continue
            self.assertTrue(
                torch.equal(q_orig[:, :, t, :], q_mod[:, :, t, :]),
                f"Quantized values for token {t} changed when only token 3 was modified",
            )
            self.assertTrue(
                torch.equal(s_orig[:, :, t, :], s_mod[:, :, t, :]),
                f"Scale for token {t} changed when only token 3 was modified",
            )

    def test_modifying_one_group_does_not_affect_other_groups(self):
        """Changing values in one group must not change quantization of other groups."""
        x = torch.randn(1, 1, 1, self.D, dtype=torch.float32)
        q_orig, s_orig = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)

        # Modify only group 1 (dims 64..127)
        x_mod = x.clone()
        x_mod[0, 0, 0, 64:] = 999.0
        q_mod, s_mod = quantize_symmetric_int8(x_mod, percentile=100.0, group_size=self.group_size)

        # Group 0 quantized values and scale must be unchanged
        self.assertTrue(
            torch.equal(q_orig[0, 0, 0, :64], q_mod[0, 0, 0, :64]),
            "Group 0 quantized values changed when only group 1 was modified",
        )
        self.assertEqual(
            s_orig[0, 0, 0, 0].item(),
            s_mod[0, 0, 0, 0].item(),
            "Group 0 scale changed when only group 1 was modified",
        )

    def test_per_token_axis_semantics_4d_tensor(self):
        """TST-013: For [B, H, S, D], quantization along head_dim axis.

        The scale shape should be [B, H, S, num_groups], confirming that
        quantization is per (batch, head, seq_position, group).
        """
        B, H, S, D = 2, 4, 8, 128
        group_size = 32
        num_groups = D // group_size

        x = torch.randn(B, H, S, D, dtype=torch.float32)
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=group_size)

        # Verify scale shape: per-token, per-group
        self.assertEqual(scale.shape, (B, H, S, num_groups))

        # Verify quantized output is int8
        self.assertEqual(q.dtype, torch.int8)

        # Verify values are within INT8 symmetric range
        self.assertTrue((q >= -127).all())
        self.assertTrue((q <= 127).all())


class TestINT8Float16Input(unittest.TestCase):
    """TST-012: Verify quantization works correctly with float16 inputs."""

    def setUp(self):
        torch.manual_seed(42)

    def test_int8_quant_float16_input(self):
        """Quantize/dequantize roundtrip with float16 input tensor."""
        B, H, S, D = 2, 4, 8, 128
        x_fp16 = torch.randn(B, H, S, D, dtype=torch.float16)

        q, scale = quantize_symmetric_int8(x_fp16, percentile=100.0, group_size=64)
        self.assertEqual(q.dtype, torch.int8)
        self.assertEqual(q.shape, x_fp16.shape)
        # Scale should preserve input dtype (fp16)
        self.assertEqual(scale.dtype, torch.float16)

        y = dequantize_symmetric_int8(q, scale)
        self.assertEqual(y.dtype, torch.float16)
        self.assertEqual(y.shape, x_fp16.shape)
        self.assertTrue(torch.isfinite(y).all())

        # Roundtrip error should be bounded
        err = (x_fp16 - y).abs().max().item()
        self.assertLess(err, 0.1, f"INT8 fp16 roundtrip max error too large: {err}")

    def test_int8_quant_float16_vs_float32_consistency(self):
        """Float16 and float32 inputs should produce similar quantized results."""
        B, H, S, D = 1, 2, 4, 128
        x_fp32 = torch.randn(B, H, S, D, dtype=torch.float32)
        x_fp16 = x_fp32.half()

        q32, s32 = quantize_symmetric_int8(x_fp32, percentile=100.0, group_size=128)
        q16, s16 = quantize_symmetric_int8(x_fp16, percentile=100.0, group_size=128)

        # Quantized values should be identical or differ by at most 1
        # (due to fp16 rounding before the round() call)
        diff = (q32.int() - q16.int()).abs()
        self.assertTrue(
            (diff <= 1).all(),
            f"INT8 quant mismatch between fp16/fp32: max diff = {diff.max().item()}",
        )

    def test_int8_cache_float16_input(self):
        """INT8KVCache should accept and roundtrip float16 inputs correctly."""
        B, H, S, D = 2, 4, 8, 128
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
            clip_percentile=100.0,
        )
        k = torch.randn(B, H, S, D, dtype=torch.float16)
        v = torch.randn(B, H, S, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)

        self.assertEqual(k_out.dtype, torch.float16)
        self.assertEqual(v_out.dtype, torch.float16)
        self.assertTrue(torch.isfinite(k_out).all())
        self.assertTrue(torch.isfinite(v_out).all())

    def test_int8_quant_float16_small_values(self):
        """Float16 quantization with very small values (near fp16 subnormal range)."""
        B, H, S, D = 1, 1, 2, 128
        # Values near fp16 smallest normal (~6e-5)
        x = torch.full((B, H, S, D), 1e-4, dtype=torch.float16)
        x[0, 0, 0, 0] = 5e-5

        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=128)
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(torch.isfinite(y).all(), "Dequantized small fp16 values must be finite")

    def test_int8_quant_float16_large_values(self):
        """Float16 quantization with values near fp16 max (~65504)."""
        B, H, S, D = 1, 1, 2, 128
        x = torch.full((B, H, S, D), 60000.0, dtype=torch.float16)

        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=128)
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(torch.isfinite(y).all(), "Dequantized large fp16 values must be finite")
        # All values identical -> all should quantize to 127, dequantize to same value
        self.assertTrue(
            (q == 127).all(),
            f"Uniform large input should all quantize to 127, got unique values: {q.unique().tolist()}",
        )


class TestINT8QuantEdgeCases(unittest.TestCase):
    """TST-017: Edge case tests for INT8 quantization."""

    def test_single_token_quant(self):
        """seq_len=1 should quantize/dequantize without error."""
        torch.manual_seed(0)
        B, H, S, D = 1, 2, 1, 128
        group_size = 64
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=group_size)
        self.assertEqual(q.shape, (B, H, 1, D))
        self.assertEqual(scale.shape, (B, H, 1, D // group_size))
        y = dequantize_symmetric_int8(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertTrue(torch.isfinite(y).all())

    def test_head_dim_1(self):
        """head_dim=1 with group_size=1 should work."""
        torch.manual_seed(0)
        B, H, S, D = 1, 2, 4, 1
        group_size = 1
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=group_size)
        self.assertEqual(q.shape, (B, H, S, 1))
        self.assertEqual(scale.shape, (B, H, S, 1))
        y = dequantize_symmetric_int8(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertTrue(torch.isfinite(y).all())

    def test_all_zeros(self):
        """All-zero input should quantize to all zeros and dequantize back."""
        B, H, S, D = 1, 2, 4, 128
        group_size = 64
        x = torch.zeros(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=group_size)
        self.assertTrue((q == 0).all(), "All-zero input should quantize to all zeros")
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(
            (y == 0).all(),
            "All-zero input should dequantize back to all zeros"
        )

    def test_all_same_value(self):
        """Constant (non-zero) input: all elements identical."""
        B, H, S, D = 1, 2, 4, 128
        group_size = 64
        val = 0.5
        x = torch.full((B, H, S, D), val, dtype=torch.float16)
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=group_size)
        y = dequantize_symmetric_int8(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertTrue(torch.isfinite(y).all())
        # scale = val / 127, dequant = 127 * (val / 127) = val exactly.
        err = (x - y).abs().max().item()
        self.assertLess(err, 0.01, f"Constant input roundtrip error too large: {err}")

    def test_single_token_cache_edge(self):
        """INT8 cache with single-token appends (seq_len=1 per step)."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
        )
        for step in range(1, 6):
            k = torch.randn(B, H, 1, D, dtype=torch.float16)
            v = torch.randn(B, H, 1, D, dtype=torch.float16)
            cache.append(0, k, v)
            self.assertEqual(cache.get_seq_len(), step)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 5, D))
        self.assertTrue(torch.isfinite(k_out).all())

    def test_all_zeros_cache(self):
        """INT8 cache with all-zero input should not corrupt."""
        B, H, D = 1, 2, 128
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
        )
        k = torch.zeros(B, H, 4, D, dtype=torch.float16)
        v = torch.zeros(B, H, 4, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertTrue((k_out == 0).all(), "All-zero K should remain zero after cache roundtrip")
        self.assertTrue((v_out == 0).all(), "All-zero V should remain zero after cache roundtrip")


class TestINT8CacheClearAppendCycle(unittest.TestCase):
    """TST-018: Multi-round clear -> append cycle for INT8 cache.

    Verifies that after clear(), appending new data produces correct results
    without contamination from previous data.
    """

    def test_clear_append_single_cycle(self):
        """Basic clear -> append -> verify cycle."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
            clip_percentile=100.0,
        )

        # Fill with first batch of data.
        k1 = torch.randn(B, H, 4, D, dtype=torch.float16)
        v1 = torch.randn(B, H, 4, D, dtype=torch.float16)
        cache.append(0, k1, v1)
        self.assertEqual(cache.get_seq_len(), 4)

        # Clear and verify seq_len resets.
        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

        # Append new data.
        k2 = torch.randn(B, H, 3, D, dtype=torch.float16)
        v2 = torch.randn(B, H, 3, D, dtype=torch.float16)
        cache.append(0, k2, v2)
        self.assertEqual(cache.get_seq_len(), 3)

        # Verify the retrieved data matches new input (within quantization error).
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 3, D))
        self.assertEqual(v_out.shape, (B, H, 3, D))
        k_err = (k2 - k_out).abs().max().item()
        v_err = (v2 - v_out).abs().max().item()
        self.assertLess(k_err, 0.1, f"K error too large after clear+append: {k_err}")
        self.assertLess(v_err, 0.1, f"V error too large after clear+append: {v_err}")

    def test_multi_cycle_no_contamination(self):
        """Multiple clear -> append cycles; each cycle should be independent."""
        torch.manual_seed(42)
        B, H, D = 1, 2, 128
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
            clip_percentile=100.0,
        )

        num_cycles = 5
        for cycle in range(num_cycles):
            # Use a distinct seed per cycle so data is different each time.
            torch.manual_seed(cycle * 100)
            seq_len = 3 + cycle  # Vary sequence length across cycles.
            k = torch.randn(B, H, seq_len, D, dtype=torch.float16)
            v = torch.randn(B, H, seq_len, D, dtype=torch.float16)

            cache.append(0, k, v)
            self.assertEqual(
                cache.get_seq_len(), seq_len,
                f"Cycle {cycle}: seq_len mismatch after append"
            )

            k_out, v_out = cache.get_kv(0)
            self.assertEqual(k_out.shape, (B, H, seq_len, D))
            self.assertEqual(v_out.shape, (B, H, seq_len, D))

            # Verify roundtrip error is bounded (not contaminated by old data).
            k_err = (k - k_out).abs().max().item()
            v_err = (v - v_out).abs().max().item()
            self.assertLess(
                k_err, 0.1,
                f"Cycle {cycle}: K error too large ({k_err}), possible contamination"
            )
            self.assertLess(
                v_err, 0.1,
                f"Cycle {cycle}: V error too large ({v_err}), possible contamination"
            )

            # Clear for next cycle.
            cache.clear()
            self.assertEqual(cache.get_seq_len(), 0)

    def test_clear_append_multi_layer(self):
        """Clear -> append cycle across multiple layers."""
        torch.manual_seed(7)
        B, H, D = 1, 2, 128
        num_layers = 3
        cache = INT8KVCache(
            num_layers=num_layers, device="cpu", group_size=64,
            clip_percentile=100.0,
        )

        # Fill all layers.
        for layer in range(num_layers):
            k = torch.randn(B, H, 4, D, dtype=torch.float16)
            v = torch.randn(B, H, 4, D, dtype=torch.float16)
            cache.append(layer, k, v)

        cache.clear()

        # Append new data to all layers.
        new_tensors = {}
        for layer in range(num_layers):
            torch.manual_seed(layer + 200)
            k = torch.randn(B, H, 2, D, dtype=torch.float16)
            v = torch.randn(B, H, 2, D, dtype=torch.float16)
            cache.append(layer, k, v)
            new_tensors[layer] = (k, v)

        # Verify each layer contains only the new data.
        for layer in range(num_layers):
            k_exp, v_exp = new_tensors[layer]
            k_out, v_out = cache.get_kv(layer)
            self.assertEqual(k_out.shape, (B, H, 2, D))
            k_err = (k_exp - k_out).abs().max().item()
            v_err = (v_exp - v_out).abs().max().item()
            self.assertLess(k_err, 0.1, f"Layer {layer}: K contamination after clear")
            self.assertLess(v_err, 0.1, f"Layer {layer}: V contamination after clear")

    def test_clear_append_with_incremental_tokens(self):
        """Clear then re-append token-by-token (simulating autoregressive decode)."""
        torch.manual_seed(55)
        B, H, D = 1, 2, 128
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=64,
            clip_percentile=100.0,
        )

        # First round: append 5 tokens one by one.
        for _ in range(5):
            k = torch.randn(B, H, 1, D, dtype=torch.float16)
            v = torch.randn(B, H, 1, D, dtype=torch.float16)
            cache.append(0, k, v)
        self.assertEqual(cache.get_seq_len(), 5)

        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

        # Second round: append 3 tokens one by one with known values.
        expected_k_parts = []
        expected_v_parts = []
        for i in range(3):
            torch.manual_seed(300 + i)
            k = torch.randn(B, H, 1, D, dtype=torch.float16)
            v = torch.randn(B, H, 1, D, dtype=torch.float16)
            cache.append(0, k, v)
            expected_k_parts.append(k)
            expected_v_parts.append(v)

        self.assertEqual(cache.get_seq_len(), 3)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 3, D))

        expected_k = torch.cat(expected_k_parts, dim=2)
        expected_v = torch.cat(expected_v_parts, dim=2)
        k_err = (expected_k - k_out).abs().max().item()
        v_err = (expected_v - v_out).abs().max().item()
        self.assertLess(k_err, 0.1, f"Token-by-token K error after clear: {k_err}")
        self.assertLess(v_err, 0.1, f"Token-by-token V error after clear: {v_err}")


class TestINT8OutlierHandling(unittest.TestCase):
    """QNT-007: INT8 quantization must handle outlier values gracefully.

    When input contains very large or very small values (outliers), the
    quantization should clip to the INT8 range [-127, 127] rather than
    overflowing. Dequantized values must remain finite, and the quantized
    tensor must stay within the valid INT8 symmetric range.
    """

    def setUp(self):
        torch.manual_seed(42)
        self.B, self.H, self.S, self.D = 1, 2, 4, 128
        self.group_size = 64

    def test_large_positive_outlier_clipped(self):
        """A single very large positive value should be clipped to 127 in INT8."""
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float32)
        # Inject an extreme outlier
        x[0, 0, 0, 0] = 1e6
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)
        # Quantized values must be within [-127, 127]
        self.assertTrue((q >= -127).all(), "Quantized values must be >= -127")
        self.assertTrue((q <= 127).all(), "Quantized values must be <= 127")
        # The outlier element should be clipped to exactly 127
        self.assertEqual(q[0, 0, 0, 0].item(), 127,
                         "Large positive outlier should be clipped to 127")
        # Dequantized output must be finite
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(torch.isfinite(y).all(), "Dequantized output must be finite")

    def test_large_negative_outlier_clipped(self):
        """A single very large negative value should be clipped to -127 in INT8."""
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float32)
        x[0, 0, 1, 10] = -1e6
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)
        self.assertTrue((q >= -127).all())
        self.assertTrue((q <= 127).all())
        self.assertEqual(q[0, 0, 1, 10].item(), -127,
                         "Large negative outlier should be clipped to -127")
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(torch.isfinite(y).all())

    def test_mixed_extreme_outliers(self):
        """Multiple extreme outliers (both positive and negative) should all be clipped."""
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float32)
        # Inject multiple outliers across different positions
        x[0, 0, 0, 0] = 1e8
        x[0, 0, 0, 1] = -1e8
        x[0, 1, 2, 63] = 5e7
        x[0, 1, 3, 127] = -5e7
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)
        self.assertTrue((q >= -127).all(), "All quantized values must be >= -127")
        self.assertTrue((q <= 127).all(), "All quantized values must be <= 127")
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(torch.isfinite(y).all(), "All dequantized values must be finite")

    def test_outlier_does_not_corrupt_non_outlier_quantization(self):
        """Outlier in one group should not corrupt quantization of another group.

        Because quantization is per-group, an outlier in group 0 should only
        affect group 0's scale, not group 1's.
        """
        x = torch.randn(1, 1, 1, self.D, dtype=torch.float32) * 0.1
        # Inject outlier only in group 0 (first 64 dims)
        x[0, 0, 0, 0] = 1e6
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)

        # Group 0 scale should be very large (dominated by outlier)
        # Group 1 scale should be small (normal randn * 0.1)
        scale_g0 = scale[0, 0, 0, 0].item()
        scale_g1 = scale[0, 0, 0, 1].item()
        self.assertGreater(scale_g0, scale_g1 * 100,
                           "Outlier group scale should be much larger than non-outlier group scale")

        # Dequantize and check that group 1 values are still close to original
        y = dequantize_symmetric_int8(q, scale)
        group1_err = (x[0, 0, 0, 64:] - y[0, 0, 0, 64:]).abs().max().item()
        self.assertLess(group1_err, 0.01,
                        f"Non-outlier group roundtrip error too large: {group1_err}")

    def test_outlier_with_percentile_clipping(self):
        """Percentile clipping (< 100%) should suppress outlier influence on scale.

        With percentile=99.9, the scale is determined by the 99.9th percentile
        of abs values rather than the absolute max. This means the outlier value
        will be clipped more aggressively (quantized to +/-127), and the
        non-outlier values should have better quantization accuracy.
        """
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float32)
        x[0, 0, 0, 0] = 1e6  # extreme outlier

        # Quantize with percentile clipping
        q_clip, scale_clip = quantize_symmetric_int8(
            x, percentile=99.9, group_size=self.group_size
        )
        # Quantize without clipping
        q_full, scale_full = quantize_symmetric_int8(
            x, percentile=100.0, group_size=self.group_size
        )

        # Both must be within INT8 range
        self.assertTrue((q_clip >= -127).all())
        self.assertTrue((q_clip <= 127).all())
        self.assertTrue((q_full >= -127).all())
        self.assertTrue((q_full <= 127).all())

        # With percentile clipping, the scale for the outlier's group should
        # be smaller (tighter around non-outlier values)
        # This means non-outlier values get more quantization resolution
        scale_clip_g0 = scale_clip[0, 0, 0, 0].item()
        scale_full_g0 = scale_full[0, 0, 0, 0].item()
        self.assertLess(scale_clip_g0, scale_full_g0,
                        "Percentile-clipped scale should be smaller than full-range scale")

    def test_fp16_outlier_near_max_range(self):
        """fp16 max is ~65504. Values near this should still quantize correctly."""
        x = torch.full(
            (self.B, self.H, self.S, self.D), 60000.0, dtype=torch.float16
        )
        # Add a few outlier positions at the extreme
        x[0, 0, 0, 0] = torch.tensor(65000.0, dtype=torch.float16)

        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=self.group_size)
        self.assertTrue((q >= -127).all())
        self.assertTrue((q <= 127).all())
        y = dequantize_symmetric_int8(q, scale)
        self.assertTrue(torch.isfinite(y).all(),
                        "Dequantized near-fp16-max values must be finite")

    def test_cache_with_outlier_input(self):
        """INT8KVCache should handle outlier inputs without crashing or producing NaN."""
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )
        k = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float16)
        v = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float16)
        # Inject outliers (staying within fp16 range to avoid inf)
        k[0, 0, 0, 0] = 60000.0
        k[0, 0, 1, 10] = -60000.0
        v[0, 1, 2, 50] = 50000.0

        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)

        self.assertEqual(k_out.shape, k.shape)
        self.assertEqual(v_out.shape, v.shape)
        self.assertTrue(torch.isfinite(k_out).all(),
                        "K output must be finite even with outlier input")
        self.assertTrue(torch.isfinite(v_out).all(),
                        "V output must be finite even with outlier input")


# ===========================================================================
# TST-005: B1 fix verification -- batch>1 cache correctness
# ===========================================================================


class TestINT8CacheBatchGreaterThanOne(unittest.TestCase):
    """TST-005: Verify batch=2 cache append/get_kv behaves consistently with batch=1.

    The B1 fix ensures that multi-batch INT8 cache operations produce the same
    per-sample quantization results as single-batch operations. Each sample in
    the batch should be quantized independently; batch dim must not cause
    cross-contamination or shape errors.
    """

    def setUp(self):
        torch.manual_seed(42)
        self.H, self.D = 4, 128
        self.group_size = 64

    def test_batch2_append_get_kv_shapes(self):
        """batch=2: shapes must be correct after append and get_kv."""
        B = 2
        cache = INT8KVCache(num_layers=1, device="cpu", group_size=self.group_size)
        k = torch.randn(B, self.H, 8, self.D, dtype=torch.float16)
        v = torch.randn(B, self.H, 8, self.D, dtype=torch.float16)
        cache.append(0, k, v)

        self.assertEqual(cache.get_seq_len(), 8)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, self.H, 8, self.D))
        self.assertEqual(v_out.shape, (B, self.H, 8, self.D))

    def test_batch2_incremental_append(self):
        """batch=2: incremental (prefill + decode) append must work."""
        B = 2
        cache = INT8KVCache(num_layers=1, device="cpu", group_size=self.group_size)

        # Prefill
        k1 = torch.randn(B, self.H, 5, self.D, dtype=torch.float16)
        v1 = torch.randn(B, self.H, 5, self.D, dtype=torch.float16)
        cache.append(0, k1, v1)

        # Decode 3 tokens one at a time
        for _ in range(3):
            k = torch.randn(B, self.H, 1, self.D, dtype=torch.float16)
            v = torch.randn(B, self.H, 1, self.D, dtype=torch.float16)
            cache.append(0, k, v)

        self.assertEqual(cache.get_seq_len(), 8)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, self.H, 8, self.D))

    def test_batch2_vs_batch1_per_sample_consistency(self):
        """Each sample in batch=2 must match independent batch=1 processing.

        We compare: run batch=2 as a single cache operation vs. run each
        sample independently with batch=1. The quantized outputs should be
        identical (not just similar), because INT8 group-wise quantization
        is per (batch, head, seq, group) -- independent across batch dim.
        """
        B = 2
        torch.manual_seed(42)
        k_full = torch.randn(B, self.H, 8, self.D, dtype=torch.float16)
        v_full = torch.randn(B, self.H, 8, self.D, dtype=torch.float16)

        # Run with batch=2
        cache_b2 = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )
        cache_b2.append(0, k_full, v_full)
        k_b2, v_b2 = cache_b2.get_kv(0)

        # Run each sample independently with batch=1
        for b in range(B):
            cache_b1 = INT8KVCache(
                num_layers=1, device="cpu", group_size=self.group_size,
                clip_percentile=100.0,
            )
            k_single = k_full[b : b + 1]
            v_single = v_full[b : b + 1]
            cache_b1.append(0, k_single, v_single)
            k_b1, v_b1 = cache_b1.get_kv(0)

            # The outputs for each sample should be identical
            self.assertTrue(
                torch.equal(k_b2[b : b + 1], k_b1),
                f"Sample {b}: batch=2 K differs from batch=1 K",
            )
            self.assertTrue(
                torch.equal(v_b2[b : b + 1], v_b1),
                f"Sample {b}: batch=2 V differs from batch=1 V",
            )

    def test_batch2_roundtrip_error_bounded(self):
        """batch=2: quantization round-trip error must be bounded per sample."""
        B = 2
        torch.manual_seed(42)
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )
        k = torch.randn(B, self.H, 8, self.D, dtype=torch.float16)
        v = torch.randn(B, self.H, 8, self.D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)

        for b in range(B):
            k_err = (k[b] - k_out[b]).abs().max().item()
            v_err = (v[b] - v_out[b]).abs().max().item()
            self.assertLess(
                k_err, 0.1,
                f"Sample {b}: K roundtrip max error {k_err:.4f} exceeds threshold",
            )
            self.assertLess(
                v_err, 0.1,
                f"Sample {b}: V roundtrip max error {v_err:.4f} exceeds threshold",
            )

    def test_batch2_clear_and_reappend(self):
        """batch=2: clear() + re-append should not leave stale batch=2 data."""
        B = 2
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )

        # First round
        k1 = torch.randn(B, self.H, 4, self.D, dtype=torch.float16)
        v1 = torch.randn(B, self.H, 4, self.D, dtype=torch.float16)
        cache.append(0, k1, v1)
        self.assertEqual(cache.get_seq_len(), 4)

        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

        # Second round with different data
        torch.manual_seed(99)
        k2 = torch.randn(B, self.H, 3, self.D, dtype=torch.float16)
        v2 = torch.randn(B, self.H, 3, self.D, dtype=torch.float16)
        cache.append(0, k2, v2)
        self.assertEqual(cache.get_seq_len(), 3)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, self.H, 3, self.D))
        k_err = (k2 - k_out).abs().max().item()
        v_err = (v2 - v_out).abs().max().item()
        self.assertLess(k_err, 0.1, f"K error after clear+reappend: {k_err}")
        self.assertLess(v_err, 0.1, f"V error after clear+reappend: {v_err}")

    def test_batch2_multi_layer(self):
        """batch=2 across multiple layers: all layers should work correctly."""
        B = 2
        num_layers = 3
        cache = INT8KVCache(
            num_layers=num_layers, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )

        tensors = {}
        for layer in range(num_layers):
            torch.manual_seed(layer * 10)
            k = torch.randn(B, self.H, 6, self.D, dtype=torch.float16)
            v = torch.randn(B, self.H, 6, self.D, dtype=torch.float16)
            cache.append(layer, k, v)
            tensors[layer] = (k, v)

        for layer in range(num_layers):
            k_exp, v_exp = tensors[layer]
            k_out, v_out = cache.get_kv(layer)
            self.assertEqual(k_out.shape, (B, self.H, 6, self.D))
            k_err = (k_exp - k_out).abs().max().item()
            v_err = (v_exp - v_out).abs().max().item()
            self.assertLess(k_err, 0.1, f"Layer {layer} K error: {k_err}")
            self.assertLess(v_err, 0.1, f"Layer {layer} V error: {v_err}")

    def test_batch2_decode_single_token(self):
        """batch=2: single-token decode appends should not corrupt data."""
        B = 2
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )

        all_k = []
        all_v = []
        for step in range(5):
            torch.manual_seed(step * 7)
            k = torch.randn(B, self.H, 1, self.D, dtype=torch.float16)
            v = torch.randn(B, self.H, 1, self.D, dtype=torch.float16)
            cache.append(0, k, v)
            all_k.append(k)
            all_v.append(v)

        self.assertEqual(cache.get_seq_len(), 5)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, self.H, 5, self.D))

        # Each token's error should be bounded
        for i, (k_ref, v_ref) in enumerate(zip(all_k, all_v)):
            k_err = (k_ref - k_out[:, :, i : i + 1, :]).abs().max().item()
            v_err = (v_ref - v_out[:, :, i : i + 1, :]).abs().max().item()
            self.assertLess(
                k_err, 0.1,
                f"Token {i}: K error {k_err:.4f} exceeds threshold",
            )
            self.assertLess(
                v_err, 0.1,
                f"Token {i}: V error {v_err:.4f} exceeds threshold",
            )


class TestINT8KDecodeQuantError(unittest.TestCase):
    """TST-006: K decode quantization error boundary test.

    Verifies that when a single token is appended (simulating the decode phase),
    the K quantization error is bounded and comparable to the prefill phase error.
    This catches regressions where decode-phase quantization behaves differently
    from prefill (e.g., scale drift, buffer corruption, or per-token axis bugs).
    """

    def setUp(self):
        torch.manual_seed(42)
        self.B, self.H, self.D = 1, 4, 128
        self.group_size = 64

    def test_decode_k_error_bounded(self):
        """Single-token append (decode) K error must be bounded by INT8 theory."""
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )
        # Prefill: append a short prefix first
        k_prefill = torch.randn(self.B, self.H, 8, self.D, dtype=torch.float16)
        v_prefill = torch.randn(self.B, self.H, 8, self.D, dtype=torch.float16)
        cache.append(0, k_prefill, v_prefill)

        # Decode: append a single new token
        k_decode = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16)
        v_decode = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16)
        cache.append(0, k_decode, v_decode)

        self.assertEqual(cache.get_seq_len(), 9)

        # Retrieve full KV and check the decode token's error
        k_out, _ = cache.get_kv(0)
        k_decode_out = k_out[:, :, 8:9, :]  # the last (decode) token

        decode_err = (k_decode - k_decode_out).abs().max().item()
        # INT8 symmetric max error ~ absmax / 127. For unit-variance randn fp16,
        # absmax ~ 3-4, so max error ~ 0.03. Tolerance 0.1 is deliberately loose.
        self.assertLess(
            decode_err, 0.1,
            f"Decode K quantization max error too large: {decode_err}"
        )
        # Also verify finiteness
        self.assertTrue(
            torch.isfinite(k_decode_out).all(),
            "Decode K output must be finite"
        )

    def test_decode_error_vs_prefill_error(self):
        """Decode-phase K error should be in the same ballpark as prefill error.

        If decode error is drastically larger (e.g. >5x), it suggests a bug in
        how scales are computed or applied for single-token appends.
        """
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )
        # Prefill phase
        k_prefill = torch.randn(self.B, self.H, 16, self.D, dtype=torch.float16)
        v_prefill = torch.randn(self.B, self.H, 16, self.D, dtype=torch.float16)
        cache.append(0, k_prefill, v_prefill)

        k_out_prefill, _ = cache.get_kv(0)
        prefill_err = (k_prefill - k_out_prefill).abs().max().item()

        # Decode phase: 4 single-token appends
        decode_errs = []
        for step in range(4):
            torch.manual_seed(100 + step)
            k_tok = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16)
            v_tok = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16)
            cache.append(0, k_tok, v_tok)

            k_all, _ = cache.get_kv(0)
            pos = 16 + step
            k_tok_out = k_all[:, :, pos:pos + 1, :]
            tok_err = (k_tok - k_tok_out).abs().max().item()
            decode_errs.append(tok_err)

        avg_decode_err = sum(decode_errs) / len(decode_errs)
        # Decode error should not be drastically worse than prefill error.
        # Allow up to 5x ratio (generous, accounts for variance in single tokens).
        ratio = avg_decode_err / max(prefill_err, 1e-8)
        self.assertLess(
            ratio, 5.0,
            f"Avg decode K error ({avg_decode_err:.6f}) is {ratio:.1f}x the "
            f"prefill K error ({prefill_err:.6f}); decode quantization may be broken"
        )

    def test_decode_k_error_with_static_scale(self):
        """Decode K error with static scales should also be bounded."""
        num_groups = self.D // self.group_size
        static_k = torch.full(
            (self.H, num_groups), 0.01, dtype=torch.float16
        )
        static_v = torch.full(
            (self.H, num_groups), 0.01, dtype=torch.float16
        )
        cache = INT8KVCache(
            num_layers=1, device="cpu", group_size=self.group_size,
            static_k_scale=[static_k],
            static_v_scale=[static_v],
        )
        # Prefill
        k_pre = torch.randn(self.B, self.H, 4, self.D, dtype=torch.float16) * 0.5
        v_pre = torch.randn(self.B, self.H, 4, self.D, dtype=torch.float16) * 0.5
        cache.append(0, k_pre, v_pre)

        # Decode token
        k_dec = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16) * 0.5
        v_dec = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16) * 0.5
        cache.append(0, k_dec, v_dec)

        k_out, _ = cache.get_kv(0)
        k_dec_out = k_out[:, :, 4:5, :]
        dec_err = (k_dec - k_dec_out).abs().max().item()
        self.assertLess(
            dec_err, 0.5,
            f"Static-scale decode K error too large: {dec_err}"
        )
        self.assertTrue(torch.isfinite(k_dec_out).all())

    def test_multi_layer_decode_k_error(self):
        """Decode K error should be bounded across all layers."""
        num_layers = 3
        cache = INT8KVCache(
            num_layers=num_layers, device="cpu", group_size=self.group_size,
            clip_percentile=100.0,
        )
        # Prefill all layers
        for layer in range(num_layers):
            k = torch.randn(self.B, self.H, 8, self.D, dtype=torch.float16)
            v = torch.randn(self.B, self.H, 8, self.D, dtype=torch.float16)
            cache.append(layer, k, v)

        # Decode: single token per layer
        decode_tokens = {}
        for layer in range(num_layers):
            torch.manual_seed(500 + layer)
            k = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16)
            v = torch.randn(self.B, self.H, 1, self.D, dtype=torch.float16)
            cache.append(layer, k, v)
            decode_tokens[layer] = k

        for layer in range(num_layers):
            k_out, _ = cache.get_kv(layer)
            k_dec_out = k_out[:, :, 8:9, :]
            err = (decode_tokens[layer] - k_dec_out).abs().max().item()
            self.assertLess(
                err, 0.1,
                f"Layer {layer} decode K error too large: {err}"
            )


class TestINT8KVCacheInputValidation(unittest.TestCase):
    """TST-023 (R12): Regression tests for input shape validation (KVC-022).

    FP16KVCache and KIVIStyleKVCache raise ValueError for ndim!=4 input.
    INT8KVCache should also reject 3D tensors rather than letting them
    silently corrupt the quantize function with shape errors.
    """

    def test_3d_tensor_append_raises(self):
        """3D tensor (missing batch dim) should raise ValueError or similar."""
        cache = INT8KVCache(num_layers=1, device="cpu", group_size=64)
        k_3d = torch.randn(4, 5, 128, dtype=torch.float16)  # [H, S, D]
        v_3d = torch.randn(4, 5, 128, dtype=torch.float16)
        with self.assertRaises((ValueError, RuntimeError)):
            cache.append(0, k_3d, v_3d)

    def test_2d_tensor_append_raises(self):
        """2D tensor should be rejected."""
        cache = INT8KVCache(num_layers=1, device="cpu", group_size=64)
        k_2d = torch.randn(5, 128, dtype=torch.float16)
        v_2d = torch.randn(5, 128, dtype=torch.float16)
        with self.assertRaises((ValueError, RuntimeError)):
            cache.append(0, k_2d, v_2d)

    def test_5d_tensor_append_raises(self):
        """5D tensor should be rejected."""
        cache = INT8KVCache(num_layers=1, device="cpu", group_size=64)
        k_5d = torch.randn(1, 2, 4, 5, 128, dtype=torch.float16)
        v_5d = torch.randn(1, 2, 4, 5, 128, dtype=torch.float16)
        with self.assertRaises((ValueError, RuntimeError)):
            cache.append(0, k_5d, v_5d)


if __name__ == "__main__":
    unittest.main()
