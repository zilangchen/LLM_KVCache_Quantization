import unittest

import torch

from src.cache.int4_cache import INT4KVCache
from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    pack_int4,
    quantize_symmetric_int4,
    quantize_symmetric_int4_with_scale,
    unpack_int4,
)
from src.quant.int8_basic import (
    dequantize_symmetric_int8,
    quantize_symmetric_int8,
)


class TestInt4Basic(unittest.TestCase):
    def test_pack_unpack_roundtrip(self):
        torch.manual_seed(0)
        # Full signed INT4 range [-8, 7] (torch.randint upper bound is exclusive)
        x = torch.randint(-8, 8, (2, 3, 4, 128), dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked))

    def test_quant_dequant_shapes(self):
        torch.manual_seed(0)
        B, H, S, D = 2, 4, 3, 128
        group_size = 32
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int4(x, percentile=99.9, group_size=group_size)
        self.assertEqual(q.shape, x.shape)
        self.assertEqual(q.dtype, torch.int8)
        # ENG-066: scale is now float32 for INT4 precision chain.
        self.assertEqual(scale.dtype, torch.float32)
        self.assertEqual(scale.shape, (B, H, S, D // group_size))

        y = dequantize_symmetric_int4(q, scale)
        self.assertEqual(y.shape, x.shape)
        # ENG-066: dequantize follows scale dtype, which is now float32.
        self.assertEqual(y.dtype, torch.float32)
        self.assertTrue(torch.isfinite(y).all().item())

        # TST-047: Quantization error upper bound assertion.
        # INT4 symmetric theoretical max error ≈ absmax/14 ≈ 0.21 for unit-variance
        # randn.  Tolerance 0.5 is ~2.4× theoretical to tolerate rare outliers.
        err = (x - y).abs().max().item()
        self.assertLess(err, 0.5, f"INT4 quant roundtrip max error too large: {err}")


class TestInt4KVCache(unittest.TestCase):
    def test_cache_append_get_bitpacked(self):
        torch.manual_seed(0)
        B, H, D = 2, 4, 128
        cache = INT4KVCache(
            num_layers=2,
            device="cpu",
            clip_percentile=99.9,
            group_size=32,
            bit_packed=True,
        )

        k1 = torch.randn(B, H, 3, D, dtype=torch.float16)
        v1 = torch.randn(B, H, 3, D, dtype=torch.float16)
        cache.append(0, k1, v1)
        cache.append(1, k1, v1)
        self.assertEqual(cache.get_seq_len(), 3)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, k1.shape)
        self.assertEqual(v_out.shape, v1.shape)
        self.assertEqual(k_out.dtype, torch.float16)
        self.assertEqual(v_out.dtype, torch.float16)

        # Append more tokens and ensure lengths grow.
        k2 = torch.randn(B, H, 2, D, dtype=torch.float16)
        v2 = torch.randn(B, H, 2, D, dtype=torch.float16)
        cache.append(0, k2, v2)
        cache.append(1, k2, v2)
        self.assertEqual(cache.get_seq_len(), 5)

        k_out2, v_out2 = cache.get_kv(0)
        self.assertEqual(k_out2.shape, (B, H, 5, D))
        self.assertEqual(v_out2.shape, (B, H, 5, D))

        self.assertGreater(cache.get_memory_mb(), 0.0)


class TestINT4vsINT8ErrorRatio(unittest.TestCase):
    """TST-016: Verify that INT4 quantization has higher error than INT8.

    Fewer bits means coarser quantization, so INT4 roundtrip error should
    be >= INT8 roundtrip error on identical input tensors.
    """

    def _roundtrip_errors(self, tensor: torch.Tensor, group_size: int):
        """Return (int4_max_err, int8_max_err) for the same input tensor."""
        # INT4 roundtrip
        q4, s4 = quantize_symmetric_int4(tensor, percentile=100.0, group_size=group_size)
        y4 = dequantize_symmetric_int4(q4, s4)
        err4 = (tensor - y4).abs().max().item()

        # INT8 roundtrip
        q8, s8 = quantize_symmetric_int8(tensor, percentile=100.0, group_size=group_size)
        y8 = dequantize_symmetric_int8(q8, s8)
        err8 = (tensor - y8).abs().max().item()

        return err4, err8

    def test_int4_error_ge_int8_randn(self):
        """INT4 max error >= INT8 max error on unit-variance randn input."""
        torch.manual_seed(42)
        B, H, S, D = 2, 4, 8, 128
        group_size = 32
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        err4, err8 = self._roundtrip_errors(x, group_size)
        self.assertGreaterEqual(
            err4, err8,
            f"INT4 error ({err4:.6f}) should be >= INT8 error ({err8:.6f})"
        )

    def test_int4_error_ge_int8_uniform(self):
        """INT4 max error >= INT8 max error on uniform [-1, 1] input."""
        torch.manual_seed(123)
        B, H, S, D = 1, 2, 4, 128
        group_size = 32
        x = (torch.rand(B, H, S, D, dtype=torch.float16) * 2.0 - 1.0)
        err4, err8 = self._roundtrip_errors(x, group_size)
        self.assertGreaterEqual(
            err4, err8,
            f"INT4 error ({err4:.6f}) should be >= INT8 error ({err8:.6f})"
        )

    def test_int4_error_significantly_larger(self):
        """INT4 error should be meaningfully larger than INT8 error.

        Theoretical ratio: INT4 uses [-7,7] (step ~absmax/7) vs INT8 [-127,127]
        (step ~absmax/127), so INT4 error should be roughly 127/7 ~ 18x larger.
        We use a conservative lower bound of 3x to avoid flakiness.
        """
        torch.manual_seed(99)
        B, H, S, D = 2, 4, 16, 128
        group_size = 32
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        err4, err8 = self._roundtrip_errors(x, group_size)
        # INT8 error could be tiny; guard against division by zero.
        if err8 > 1e-7:
            ratio = err4 / err8
            self.assertGreater(
                ratio, 3.0,
                f"INT4/INT8 error ratio ({ratio:.2f}) should be > 3x "
                f"(err4={err4:.6f}, err8={err8:.6f})"
            )

    def test_int4_error_ge_int8_multiple_seeds(self):
        """INT4 error >= INT8 error holds across multiple seeds."""
        B, H, S, D = 1, 2, 4, 128
        group_size = 32
        for seed in range(10):
            torch.manual_seed(seed)
            x = torch.randn(B, H, S, D, dtype=torch.float16)
            err4, err8 = self._roundtrip_errors(x, group_size)
            self.assertGreaterEqual(
                err4, err8,
                f"Seed {seed}: INT4 error ({err4:.6f}) < INT8 error ({err8:.6f})"
            )


class TestINT4QuantEdgeCases(unittest.TestCase):
    """TST-017: Edge case tests for INT4 quantization."""

    def test_single_token(self):
        """seq_len=1 should quantize/dequantize without error."""
        torch.manual_seed(0)
        B, H, S, D = 1, 2, 1, 128
        group_size = 32
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=group_size)
        self.assertEqual(q.shape, (B, H, 1, D))
        self.assertEqual(scale.shape, (B, H, 1, D // group_size))
        y = dequantize_symmetric_int4(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertTrue(torch.isfinite(y).all())

    def test_head_dim_1(self):
        """head_dim=1 with group_size=1 should work."""
        torch.manual_seed(0)
        B, H, S, D = 1, 2, 4, 1
        group_size = 1
        x = torch.randn(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=group_size)
        self.assertEqual(q.shape, (B, H, S, 1))
        self.assertEqual(scale.shape, (B, H, S, 1))
        y = dequantize_symmetric_int4(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertTrue(torch.isfinite(y).all())

    def test_all_zeros(self):
        """All-zero input should quantize to all zeros and dequantize back."""
        B, H, S, D = 1, 2, 4, 128
        group_size = 32
        x = torch.zeros(B, H, S, D, dtype=torch.float16)
        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=group_size)
        # Quantized values should all be zero.
        self.assertTrue((q == 0).all(), "All-zero input should quantize to all zeros")
        y = dequantize_symmetric_int4(q, scale)
        self.assertTrue(
            (y == 0).all(),
            "All-zero input should dequantize back to all zeros"
        )

    def test_all_same_value(self):
        """Constant (non-zero) input: all elements identical."""
        B, H, S, D = 1, 2, 4, 128
        group_size = 32
        val = 0.5
        x = torch.full((B, H, S, D), val, dtype=torch.float16)
        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=group_size)
        y = dequantize_symmetric_int4(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertTrue(torch.isfinite(y).all())
        # All elements should dequantize to the same value (quantized to 7).
        # scale = val / 7, dequant = 7 * (val / 7) = val exactly.
        err = (x - y).abs().max().item()
        self.assertLess(err, 0.01, f"Constant input roundtrip error too large: {err}")

    def test_single_token_cache(self):
        """INT4 cache with single-token appends."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=True,
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
        """INT4 cache with all-zero input should not corrupt."""
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=True,
        )
        k = torch.zeros(B, H, 4, D, dtype=torch.float16)
        v = torch.zeros(B, H, 4, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertTrue((k_out == 0).all(), "All-zero K should remain zero after cache roundtrip")
        self.assertTrue((v_out == 0).all(), "All-zero V should remain zero after cache roundtrip")


class TestInt4AxisIndependence(unittest.TestCase):
    """TST-007 / TST-013: Verify per-token/per-group quantization axis independence for INT4.

    INT4 group-wise quantization operates along the head_dim axis.
    The scale is computed per (batch, head, seq_position, group), so:
    - Each token (seq position) gets its own independent scale.
    - Modifying one token should not affect another token's quantization.
    - Modifying one channel group should not affect another group's quantization.
    """

    def setUp(self):
        torch.manual_seed(42)
        self.B, self.H, self.S, self.D = 2, 4, 8, 128
        self.group_size = 32

    def test_scale_varies_per_token(self):
        """Scale must vary across seq positions (per-token quantization)."""
        x = torch.zeros(1, 1, 4, self.D, dtype=torch.float32)
        x[0, 0, 0, :] = 1.0
        x[0, 0, 1, :] = 10.0
        x[0, 0, 2, :] = 100.0
        x[0, 0, 3, :] = 0.01

        _, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=self.D)
        # scale shape: [1, 1, 4, 1] (num_groups=1 when group_size==D)
        scales_flat = scale[0, 0, :, 0]
        self.assertEqual(len(scales_flat.unique()), 4,
                         f"Expected 4 unique scales (one per token), got {scales_flat.unique()}")

    def test_scale_varies_per_group_within_token(self):
        """Scale must vary across groups within the same token."""
        x = torch.zeros(1, 1, 1, self.D, dtype=torch.float32)
        # Group 0 (first 32 dims): small
        x[0, 0, 0, :32] = 0.5
        # Group 1 (dims 32..63): large
        x[0, 0, 0, 32:64] = 50.0

        _, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=self.group_size)
        # scale shape: [1, 1, 1, 4]
        self.assertNotAlmostEqual(
            scale[0, 0, 0, 0].item(),
            scale[0, 0, 0, 1].item(),
            places=2,
            msg="Scales for groups with different magnitudes should differ",
        )

    def test_modifying_one_token_does_not_affect_others(self):
        """Changing values in one token must not change quantization of other tokens."""
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float32)
        q_orig, s_orig = quantize_symmetric_int4(x, percentile=100.0, group_size=self.group_size)

        # Modify token 3 drastically
        x_mod = x.clone()
        x_mod[:, :, 3, :] = 999.0
        q_mod, s_mod = quantize_symmetric_int4(x_mod, percentile=100.0, group_size=self.group_size)

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
        q_orig, s_orig = quantize_symmetric_int4(x, percentile=100.0, group_size=self.group_size)

        # Modify only group 2 (dims 64..95)
        x_mod = x.clone()
        x_mod[0, 0, 0, 64:96] = 999.0
        q_mod, s_mod = quantize_symmetric_int4(x_mod, percentile=100.0, group_size=self.group_size)

        # Groups 0, 1, and 3 must be unchanged
        for g_idx, (start, end) in enumerate([(0, 32), (32, 64), (96, 128)]):
            g_pos = [0, 1, 3][g_idx]
            self.assertTrue(
                torch.equal(q_orig[0, 0, 0, start:end], q_mod[0, 0, 0, start:end]),
                f"Group {g_pos} (dims {start}:{end}) quantized values changed "
                f"when only group 2 was modified",
            )
            self.assertEqual(
                s_orig[0, 0, 0, g_pos].item(),
                s_mod[0, 0, 0, g_pos].item(),
                f"Group {g_pos} scale changed when only group 2 was modified",
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
        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=group_size)

        # Verify scale shape: per-token, per-group
        self.assertEqual(scale.shape, (B, H, S, num_groups))

        # Verify quantized output is int8 (storing INT4 values)
        self.assertEqual(q.dtype, torch.int8)

        # Verify values are within INT4 symmetric range [-7, 7]
        self.assertTrue((q >= -7).all(), f"Values below -7 found: min = {q.min().item()}")
        self.assertTrue((q <= 7).all(), f"Values above 7 found: max = {q.max().item()}")


class TestInt4Float16Input(unittest.TestCase):
    """TST-012: Verify INT4 quantization works correctly with float16 inputs."""

    def setUp(self):
        torch.manual_seed(42)

    def test_int4_quant_float16_input(self):
        """Quantize/dequantize roundtrip with float16 input tensor."""
        B, H, S, D = 2, 4, 8, 128
        x_fp16 = torch.randn(B, H, S, D, dtype=torch.float16)

        q, scale = quantize_symmetric_int4(x_fp16, percentile=100.0, group_size=32)
        self.assertEqual(q.dtype, torch.int8)
        self.assertEqual(q.shape, x_fp16.shape)
        # ENG-066: Scale is now float32 for INT4 precision chain.
        self.assertEqual(scale.dtype, torch.float32)

        y = dequantize_symmetric_int4(q, scale)
        # ENG-066: dequantize follows scale dtype (now float32).
        self.assertEqual(y.dtype, torch.float32)
        self.assertEqual(y.shape, x_fp16.shape)
        self.assertTrue(torch.isfinite(y).all())

        # Roundtrip error should be bounded (INT4 is less precise)
        err = (x_fp16.float() - y).abs().max().item()
        self.assertLess(err, 0.5, f"INT4 fp16 roundtrip max error too large: {err}")

    def test_int4_quant_float16_vs_float32_consistency(self):
        """Float16 and float32 inputs should produce similar quantized results."""
        B, H, S, D = 1, 2, 4, 128
        x_fp32 = torch.randn(B, H, S, D, dtype=torch.float32)
        x_fp16 = x_fp32.half()

        q32, s32 = quantize_symmetric_int4(x_fp32, percentile=100.0, group_size=128)
        q16, s16 = quantize_symmetric_int4(x_fp16, percentile=100.0, group_size=128)

        # Quantized values should be identical or differ by at most 1
        diff = (q32.int() - q16.int()).abs()
        self.assertTrue(
            (diff <= 1).all(),
            f"INT4 quant mismatch between fp16/fp32: max diff = {diff.max().item()}",
        )

    def test_int4_cache_float16_input(self):
        """INT4KVCache should accept and roundtrip float16 inputs correctly."""
        B, H, S, D = 2, 4, 8, 128
        cache = INT4KVCache(
            num_layers=1, device="cpu", group_size=32,
            clip_percentile=100.0, bit_packed=True,
        )
        k = torch.randn(B, H, S, D, dtype=torch.float16)
        v = torch.randn(B, H, S, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)

        self.assertEqual(k_out.dtype, torch.float16)
        self.assertEqual(v_out.dtype, torch.float16)
        self.assertTrue(torch.isfinite(k_out).all())
        self.assertTrue(torch.isfinite(v_out).all())

    def test_int4_quant_float16_small_values(self):
        """Float16 quantization with very small values (near fp16 subnormal range)."""
        B, H, S, D = 1, 1, 2, 128
        x = torch.full((B, H, S, D), 1e-4, dtype=torch.float16)
        x[0, 0, 0, 0] = 5e-5

        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=128)
        y = dequantize_symmetric_int4(q, scale)
        self.assertTrue(torch.isfinite(y).all(), "Dequantized small fp16 values must be finite")

    def test_int4_quant_float16_large_values(self):
        """Float16 quantization with values near fp16 max (~65504)."""
        B, H, S, D = 1, 1, 2, 128
        x = torch.full((B, H, S, D), 60000.0, dtype=torch.float16)

        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=128)
        y = dequantize_symmetric_int4(q, scale)
        self.assertTrue(torch.isfinite(y).all(), "Dequantized large fp16 values must be finite")
        # All values identical -> all should quantize to 7, dequantize to same value
        self.assertTrue(
            (q == 7).all(),
            f"Uniform large input should all quantize to 7, got unique values: {q.unique().tolist()}",
        )


class TestInt4BoundaryValues(unittest.TestCase):
    """TST-014: Boundary value tests for INT4 pack/unpack and quantization.

    INT4 signed range is [-8, 7].
    Symmetric quantization clamps to [-7, 7].
    Pack/unpack uses offset +8 to map [-8, 7] -> [0, 15] for nibble storage.
    """

    def test_pack_unpack_min_value_neg8(self):
        """Pack/unpack roundtrip for minimum INT4 value (-8)."""
        x = torch.full((1, 1, 1, 2), -8, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Roundtrip failed for -8: got {unpacked}")

    def test_pack_unpack_max_value_7(self):
        """Pack/unpack roundtrip for maximum INT4 value (7)."""
        x = torch.full((1, 1, 1, 2), 7, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Roundtrip failed for 7: got {unpacked}")

    def test_pack_unpack_zero(self):
        """Pack/unpack roundtrip for zero."""
        x = torch.full((1, 1, 1, 2), 0, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Roundtrip failed for 0: got {unpacked}")

    def test_pack_unpack_neg7(self):
        """Pack/unpack roundtrip for -7 (symmetric min)."""
        x = torch.full((1, 1, 1, 4), -7, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Roundtrip failed for -7: got {unpacked}")

    def test_pack_unpack_neg1(self):
        """Pack/unpack roundtrip for -1 (near-zero boundary)."""
        x = torch.full((1, 1, 1, 4), -1, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Roundtrip failed for -1: got {unpacked}")

    def test_pack_unpack_pos1(self):
        """Pack/unpack roundtrip for +1 (near-zero boundary)."""
        x = torch.full((1, 1, 1, 4), 1, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Roundtrip failed for +1: got {unpacked}")

    def test_pack_unpack_all_boundary_values_in_one_tensor(self):
        """Pack/unpack with all boundary values mixed in a single tensor."""
        # [-8, -7, -1, 0, 1, 6, 7, -8] covers all interesting boundaries
        x = torch.tensor([[-8, -7, -1, 0, 1, 6, 7, -8]], dtype=torch.int8)
        x = x.view(1, 1, 1, 8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Mixed boundary roundtrip failed: expected {x}, got {unpacked}")

    def test_pack_unpack_full_range_sweep(self):
        """Pack/unpack roundtrip for every value in [-8, 7]."""
        # 16 values, paired into 8 packed bytes
        values = list(range(-8, 8))  # [-8, -7, ..., 6, 7]
        x = torch.tensor(values, dtype=torch.int8).view(1, 1, 1, 16)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        f"Full range sweep failed: expected {values}, got {unpacked.tolist()}")

    def test_pack_unpack_adjacent_boundary_pairs(self):
        """Pack/unpack with boundary values in adjacent nibble pairs."""
        # Test pairs that exercise the pack encoding boundary:
        # (-8, 7), (7, -8), (-8, -8), (7, 7), (0, 0), (-1, 1)
        pairs = [(-8, 7), (7, -8), (-8, -8), (7, 7), (0, 0), (-1, 1)]
        for lo, hi in pairs:
            x = torch.tensor([[lo, hi]], dtype=torch.int8).view(1, 1, 1, 2)
            packed = pack_int4(x)
            unpacked = unpack_int4(packed)
            self.assertTrue(
                torch.equal(x, unpacked),
                f"Pair ({lo}, {hi}) roundtrip failed: got {unpacked.tolist()}",
            )

    def test_symmetric_quant_clamps_to_neg7_pos7(self):
        """Symmetric INT4 quantization must clamp output to [-7, 7], not [-8, 7]."""
        B, H, S, D = 1, 1, 1, 128
        # Large magnitude input to force clamping
        x = torch.randn(B, H, S, D, dtype=torch.float32) * 1000.0
        q, _ = quantize_symmetric_int4(x, percentile=100.0, group_size=D)
        self.assertTrue((q >= -7).all(), f"Symmetric quant produced values < -7: min = {q.min().item()}")
        self.assertTrue((q <= 7).all(), f"Symmetric quant produced values > 7: max = {q.max().item()}")

    def test_quant_boundary_value_exactness(self):
        """Quantizing exact boundary values should produce correct quantized output."""
        D = 128
        group_size = D
        # All 7.0 -> should quantize to 7 (scale = 7.0/7.0 = 1.0)
        x_max = torch.full((1, 1, 1, D), 7.0, dtype=torch.float32)
        q, s = quantize_symmetric_int4(x_max, percentile=100.0, group_size=group_size)
        self.assertTrue((q == 7).all(), f"All-7.0 input should quantize to 7, got {q.unique().tolist()}")

        # All -7.0 -> should quantize to -7 (scale = 7.0/7.0 = 1.0)
        x_min = torch.full((1, 1, 1, D), -7.0, dtype=torch.float32)
        q, s = quantize_symmetric_int4(x_min, percentile=100.0, group_size=group_size)
        self.assertTrue((q == -7).all(), f"All-(-7.0) input should quantize to -7, got {q.unique().tolist()}")

        # All 0.0 -> should quantize to 0
        x_zero = torch.full((1, 1, 1, D), 0.0, dtype=torch.float32)
        q, s = quantize_symmetric_int4(x_zero, percentile=100.0, group_size=group_size)
        self.assertTrue((q == 0).all(), f"All-zero input should quantize to 0, got {q.unique().tolist()}")

    def test_quant_dequant_boundary_roundtrip(self):
        """Quantize then dequantize boundary values and verify reconstruction quality."""
        D = 128
        group_size = D
        # Values at symmetric boundaries
        x = torch.zeros(1, 1, 1, D, dtype=torch.float32)
        x[0, 0, 0, 0] = 3.5   # exactly half a step for scale=1.0 -> rounds to 4
        x[0, 0, 0, 1] = -3.5  # rounds to -4
        x[0, 0, 0, 2] = 0.0   # exact zero
        x[0, 0, 0, 3] = 3.5   # max value in this tensor is 3.5 -> scale = 3.5/7 = 0.5
        # With scale=0.5: 3.5/0.5=7 -> clamp(7)=7; -3.5/0.5=-7 -> clamp(-7)=-7; 0/0.5=0

        q, scale = quantize_symmetric_int4(x, percentile=100.0, group_size=group_size)
        y = dequantize_symmetric_int4(q, scale)

        self.assertTrue(torch.isfinite(y).all())
        # The zero value must dequantize exactly to zero
        self.assertEqual(y[0, 0, 0, 2].item(), 0.0,
                         "Zero input must dequantize to exactly 0.0")

    def test_pack_unpack_large_batch(self):
        """Pack/unpack with realistic batch dimensions and boundary values."""
        B, H, S, D = 2, 4, 8, 128
        # Fill with random INT4 values including boundaries
        torch.manual_seed(12345)
        x = torch.randint(-8, 8, (B, H, S, D), dtype=torch.int8)
        # Force some boundary values
        x[0, 0, 0, 0] = -8
        x[0, 0, 0, 1] = 7
        x[1, 3, 7, 126] = -8
        x[1, 3, 7, 127] = 7

        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked),
                        "Large batch pack/unpack roundtrip failed")


class TestINT4CacheClearAppendCycle(unittest.TestCase):
    """TST-018: Multi-round clear -> append cycle for INT4 cache.

    Verifies that after clear(), appending new data produces correct results
    without contamination from previous data.
    """

    def test_clear_append_single_cycle(self):
        """Basic clear -> append -> verify cycle."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=True,
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
        self.assertLess(k_err, 0.5, f"K error too large after clear+append: {k_err}")
        self.assertLess(v_err, 0.5, f"V error too large after clear+append: {v_err}")

    def test_multi_cycle_no_contamination(self):
        """Multiple clear -> append cycles; each cycle should be independent."""
        torch.manual_seed(42)
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=True,
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
                k_err, 0.5,
                f"Cycle {cycle}: K error too large ({k_err}), possible contamination"
            )
            self.assertLess(
                v_err, 0.5,
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
        cache = INT4KVCache(
            num_layers=num_layers,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=True,
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
            self.assertLess(k_err, 0.5, f"Layer {layer}: K contamination after clear")
            self.assertLess(v_err, 0.5, f"Layer {layer}: V contamination after clear")


class TestInt4CacheBitPackedFalse(unittest.TestCase):
    """TST-064: Tests for INT4KVCache with bit_packed=False.

    When bit_packed=False, INT4 quantized values are stored as plain int8
    (one value per byte, no nibble packing). This exercises a different
    code path than the default bit_packed=True.
    """

    def test_basic_append_get_unpacked(self):
        """Append and retrieve with bit_packed=False should roundtrip correctly."""
        torch.manual_seed(0)
        B, H, D = 2, 4, 128
        cache = INT4KVCache(
            num_layers=2,
            device="cpu",
            clip_percentile=99.9,
            group_size=32,
            bit_packed=False,
        )

        k1 = torch.randn(B, H, 3, D, dtype=torch.float16)
        v1 = torch.randn(B, H, 3, D, dtype=torch.float16)
        cache.append(0, k1, v1)
        cache.append(1, k1, v1)
        self.assertEqual(cache.get_seq_len(), 3)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, k1.shape)
        self.assertEqual(v_out.shape, v1.shape)
        self.assertEqual(k_out.dtype, torch.float16)
        self.assertEqual(v_out.dtype, torch.float16)
        self.assertTrue(torch.isfinite(k_out).all())
        self.assertTrue(torch.isfinite(v_out).all())

    def test_unpacked_storage_dim_equals_head_dim(self):
        """With bit_packed=False, stored head_dim should equal original head_dim."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=False,
        )
        k = torch.randn(B, H, 4, D, dtype=torch.float16)
        v = torch.randn(B, H, 4, D, dtype=torch.float16)
        cache.append(0, k, v)

        # With bit_packed=False, the internal int8 tensor should have head_dim=D
        self.assertEqual(cache._k_cache[0].shape[-1], D)
        self.assertEqual(cache._v_cache[0].shape[-1], D)

    def test_unpacked_roundtrip_error_bounded(self):
        """Roundtrip error with bit_packed=False should be bounded."""
        torch.manual_seed(42)
        B, H, D = 2, 4, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=False,
        )
        k = torch.randn(B, H, 8, D, dtype=torch.float16)
        v = torch.randn(B, H, 8, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)

        k_err = (k - k_out).abs().max().item()
        v_err = (v - v_out).abs().max().item()
        self.assertLess(k_err, 0.5, f"bit_packed=False K roundtrip error too large: {k_err}")
        self.assertLess(v_err, 0.5, f"bit_packed=False V roundtrip error too large: {v_err}")

    def test_unpacked_incremental_append(self):
        """Incrementally append single tokens with bit_packed=False."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=False,
        )
        for step in range(1, 6):
            k = torch.randn(B, H, 1, D, dtype=torch.float16)
            v = torch.randn(B, H, 1, D, dtype=torch.float16)
            cache.append(0, k, v)
            self.assertEqual(cache.get_seq_len(), step)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 5, D))
        self.assertTrue(torch.isfinite(k_out).all())

    def test_unpacked_odd_head_dim(self):
        """With bit_packed=False, odd head_dim should work (no packing constraint)."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 33  # odd head_dim
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=33,
            bit_packed=False,
        )
        k = torch.randn(B, H, 4, D, dtype=torch.float16)
        v = torch.randn(B, H, 4, D, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 4, D))
        self.assertTrue(torch.isfinite(k_out).all())

    def test_unpacked_clear_and_reappend(self):
        """Clear then reappend with bit_packed=False should not corrupt data."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache = INT4KVCache(
            num_layers=1,
            device="cpu",
            clip_percentile=100.0,
            group_size=32,
            bit_packed=False,
        )
        k1 = torch.randn(B, H, 4, D, dtype=torch.float16)
        v1 = torch.randn(B, H, 4, D, dtype=torch.float16)
        cache.append(0, k1, v1)
        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

        k2 = torch.randn(B, H, 3, D, dtype=torch.float16)
        v2 = torch.randn(B, H, 3, D, dtype=torch.float16)
        cache.append(0, k2, v2)
        self.assertEqual(cache.get_seq_len(), 3)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 3, D))

    def test_unpacked_memory_larger_than_packed(self):
        """With bit_packed=False, memory usage should be >= packed (same data stored in full bytes)."""
        torch.manual_seed(0)
        B, H, D = 1, 2, 128
        cache_packed = INT4KVCache(
            num_layers=1, device="cpu", clip_percentile=100.0,
            group_size=32, bit_packed=True,
        )
        cache_unpacked = INT4KVCache(
            num_layers=1, device="cpu", clip_percentile=100.0,
            group_size=32, bit_packed=False,
        )
        k = torch.randn(B, H, 8, D, dtype=torch.float16)
        v = torch.randn(B, H, 8, D, dtype=torch.float16)
        cache_packed.append(0, k, v)
        cache_unpacked.append(0, k, v)

        mem_packed = cache_packed.get_memory_mb()
        mem_unpacked = cache_unpacked.get_memory_mb()
        # Unpacked stores each int4 as a full byte, packed stores 2 per byte
        self.assertGreaterEqual(
            mem_unpacked, mem_packed,
            f"Unpacked ({mem_unpacked:.4f} MB) should use >= memory than packed ({mem_packed:.4f} MB)"
        )


class TestKIVICacheGrowBoundary(unittest.TestCase):
    """TST-065: KVC-017 grow path boundary test for KIVIStyleKVCache.

    Tests that when appending would cause target_len to exceed max_seq_len,
    the _ensure_capacity grow path raises ValueError instead of silently
    allowing out-of-bounds writes.
    """

    def test_grow_exceeds_max_seq_len_raises(self):
        """Appending beyond max_seq_len during grow should raise ValueError."""
        from src.cache.kivi_style_cache import KIVIStyleKVCache
        B, H, D = 1, 2, 16
        max_len = 10
        cache = KIVIStyleKVCache(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=max_len,
            quant_bits=8,
        )
        # Append 8 tokens (within capacity)
        k1 = torch.randn(B, H, 8, D)
        v1 = torch.randn(B, H, 8, D)
        cache.append(0, k1, v1)
        self.assertEqual(cache.get_seq_len(), 8)

        # Append 3 more tokens -> total=11 > max_seq_len=10 -> should raise
        k2 = torch.randn(B, H, 3, D)
        v2 = torch.randn(B, H, 3, D)
        with self.assertRaises(ValueError) as ctx:
            cache.append(0, k2, v2)
        self.assertIn("exceeds", str(ctx.exception).lower())

    def test_grow_exactly_at_max_seq_len_succeeds(self):
        """Appending exactly to max_seq_len should succeed."""
        from src.cache.kivi_style_cache import KIVIStyleKVCache
        B, H, D = 1, 2, 16
        max_len = 10
        cache = KIVIStyleKVCache(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=max_len,
            quant_bits=8,
        )
        k1 = torch.randn(B, H, 8, D)
        v1 = torch.randn(B, H, 8, D)
        cache.append(0, k1, v1)

        # Append 2 more -> total=10 == max_seq_len -> should succeed
        k2 = torch.randn(B, H, 2, D)
        v2 = torch.randn(B, H, 2, D)
        cache.append(0, k2, v2)
        self.assertEqual(cache.get_seq_len(), 10)

    def test_grow_one_past_max_seq_len_raises(self):
        """Appending 1 token past max_seq_len from exactly-at-limit should raise."""
        from src.cache.kivi_style_cache import KIVIStyleKVCache
        B, H, D = 1, 2, 16
        max_len = 10
        cache = KIVIStyleKVCache(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=max_len,
            quant_bits=8,
        )
        # Fill to exactly max_seq_len
        k1 = torch.randn(B, H, max_len, D)
        v1 = torch.randn(B, H, max_len, D)
        cache.append(0, k1, v1)
        self.assertEqual(cache.get_seq_len(), max_len)

        # One more token should raise
        k2 = torch.randn(B, H, 1, D)
        v2 = torch.randn(B, H, 1, D)
        with self.assertRaises(ValueError):
            cache.append(0, k2, v2)

    def test_initial_allocation_exceeds_max_seq_len_raises(self):
        """First append with seq_len > max_seq_len should raise immediately."""
        from src.cache.kivi_style_cache import KIVIStyleKVCache
        B, H, D = 1, 2, 16
        cache = KIVIStyleKVCache(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=5,
            quant_bits=8,
        )
        k = torch.randn(B, H, 6, D)
        v = torch.randn(B, H, 6, D)
        with self.assertRaises(ValueError):
            cache.append(0, k, v)

    def test_int4_grow_boundary(self):
        """INT4 variant also respects max_seq_len during grow."""
        from src.cache.kivi_style_cache import KIVIStyleKVCache
        B, H, D = 1, 2, 16
        max_len = 12
        cache = KIVIStyleKVCache(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=max_len,
            quant_bits=4,
        )
        k1 = torch.randn(B, H, 10, D)
        v1 = torch.randn(B, H, 10, D)
        cache.append(0, k1, v1)

        # 3 more -> total=13 > max_len=12 -> should raise
        k2 = torch.randn(B, H, 3, D)
        v2 = torch.randn(B, H, 3, D)
        with self.assertRaises(ValueError):
            cache.append(0, k2, v2)


class TestENG066Float32ScaleChain(unittest.TestCase):
    """ENG-066: Verify float32 scale precision chain for INT4."""

    def test_quantize_symmetric_int4_scale_is_float32(self):
        """Scale output from quantize_symmetric_int4 must be float32."""
        x = torch.randn(1, 4, 2, 128, dtype=torch.float16)
        _, scale = quantize_symmetric_int4(x, percentile=99.9, group_size=32)
        self.assertEqual(scale.dtype, torch.float32)

    def test_quantize_with_static_scale_preserves_float32(self):
        """quantize_symmetric_int4_with_scale preserves float32 scale."""
        x = torch.randn(1, 4, 2, 128, dtype=torch.float16)
        static_scale = torch.rand(4, 4, dtype=torch.float32) * 0.1 + 0.01  # [H, G]
        _, scale_out = quantize_symmetric_int4_with_scale(x, static_scale, group_size=32)
        self.assertEqual(scale_out.dtype, torch.float32)

    def test_dequant_output_follows_scale_dtype(self):
        """dequantize output dtype follows scale.dtype (float32)."""
        x = torch.randn(1, 4, 2, 128, dtype=torch.float16)
        q, scale = quantize_symmetric_int4(x, percentile=99.9, group_size=32)
        self.assertEqual(scale.dtype, torch.float32)
        y = dequantize_symmetric_int4(q, scale)
        self.assertEqual(y.dtype, torch.float32)  # follows scale

    def test_int4_cache_get_kv_returns_cache_dtype(self):
        """get_kv() must return self.dtype (fp16) regardless of internal scale precision."""
        cache = INT4KVCache(num_layers=1, device="cpu", group_size=32,
                            dtype=torch.float16, bit_packed=False)
        k = torch.randn(1, 4, 8, 128, dtype=torch.float16)
        v = torch.randn(1, 4, 8, 128, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.dtype, torch.float16)
        self.assertEqual(v_out.dtype, torch.float16)

    def test_int4_cache_internal_scale_is_float32(self):
        """Internal scale buffers should be float32 after ENG-066."""
        cache = INT4KVCache(num_layers=1, device="cpu", group_size=32,
                            dtype=torch.float16, bit_packed=False)
        k = torch.randn(1, 4, 8, 128, dtype=torch.float16)
        v = torch.randn(1, 4, 8, 128, dtype=torch.float16)
        cache.append(0, k, v)
        self.assertEqual(cache._k_scale[0].dtype, torch.float32)
        self.assertEqual(cache._v_scale[0].dtype, torch.float32)


class TestPackInt4Validation(unittest.TestCase):
    """TST-025/TST-026 (R12): Regression tests for pack_int4 edge cases.

    TST-025 (QNT-026): pack_int4 uses ``assert D % 2 == 0`` which vanishes
    under ``python -O``. This test verifies the odd-D case is caught.

    TST-026 (QNT-027): pack_int4 does not validate [-8, 7] range on input.
    Out-of-range values silently corrupt adjacent nibbles. This test documents
    the expected behaviour (error or silent corruption).
    """

    def test_odd_head_dim_raises_or_corrupts(self):
        """pack_int4 with odd last dimension should raise AssertionError.

        Note: under ``python -O`` the assert is stripped and the function
        silently produces a wrong-shape output. This test documents the
        expected AssertionError under normal (non-optimized) execution.
        """
        odd_tensor = torch.randint(-8, 8, (1, 2, 4, 127), dtype=torch.int8)
        with self.assertRaises((AssertionError, RuntimeError)):
            pack_int4(odd_tensor)

    def test_out_of_range_positive_overflow(self):
        """pack_int4 with values > 7 should produce corrupted output.

        This test documents the current behaviour: pack_int4 does NOT
        validate the input range. Values outside [-8, 7] cause nibble
        overflow that corrupts adjacent packed values.
        """
        # Create tensor with value 15 (> 7, overflows 4-bit signed range)
        x = torch.full((1, 1, 1, 2), 15, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        # Roundtrip should NOT reproduce the original because 15 overflows
        # signed 4-bit range. This documents the silent corruption.
        self.assertFalse(
            torch.equal(x, unpacked),
            "Out-of-range values should not roundtrip correctly through pack/unpack"
        )

    def test_out_of_range_negative_underflow(self):
        """pack_int4 with values < -8 should produce corrupted output."""
        x = torch.full((1, 1, 1, 2), -9, dtype=torch.int8)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertFalse(
            torch.equal(x, unpacked),
            "Out-of-range values should not roundtrip correctly through pack/unpack"
        )

    def test_valid_boundary_values_roundtrip(self):
        """Values exactly at [-8, 7] boundaries should roundtrip correctly."""
        x = torch.tensor([[-8, 7, -8, 7]], dtype=torch.int8).reshape(1, 1, 1, 4)
        packed = pack_int4(x)
        unpacked = unpack_int4(packed)
        self.assertTrue(torch.equal(x, unpacked))


if __name__ == "__main__":
    unittest.main()

