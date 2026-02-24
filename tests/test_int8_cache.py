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


if __name__ == "__main__":
    unittest.main()
