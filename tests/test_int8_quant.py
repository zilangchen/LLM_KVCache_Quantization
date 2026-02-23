"""Unit tests for INT8 quantization functions."""

import unittest

import torch

from src.quant.int8_basic import (
    dequantize_symmetric_int8,
    quantize_symmetric_int8,
    quantize_symmetric_int8_with_scale,
)


class TestQuantDequantRoundtrip(unittest.TestCase):
    """Roundtrip quantize -> dequantize error tests."""

    def setUp(self):
        torch.manual_seed(42)
        self.B, self.H, self.S, self.D = 2, 4, 8, 128

    def test_roundtrip_normal_distribution(self):
        x = torch.randn(
            self.B, self.H, self.S, self.D, dtype=torch.float16
        )
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=64)
        y = dequantize_symmetric_int8(q, scale)

        self.assertEqual(y.shape, x.shape)
        self.assertEqual(y.dtype, torch.float16)
        max_err = (x - y).abs().max().item()
        self.assertLess(max_err, 0.1)

    def test_roundtrip_uniform_distribution(self):
        x = torch.rand(
            self.B, self.H, self.S, self.D, dtype=torch.float16
        ) * 2 - 1
        q, scale = quantize_symmetric_int8(x, percentile=100.0, group_size=64)
        y = dequantize_symmetric_int8(q, scale)

        rel_err = ((x - y).abs() / (x.abs() + 1e-6)).mean().item()
        self.assertLess(rel_err, 0.05)


class TestGroupSize(unittest.TestCase):
    """Test various group_size values."""

    def setUp(self):
        torch.manual_seed(42)
        self.x = torch.randn(1, 2, 4, 128, dtype=torch.float16)

    def test_group_size_8(self):
        q, s = quantize_symmetric_int8(self.x, group_size=8)
        self.assertEqual(s.shape[-1], 128 // 8)
        y = dequantize_symmetric_int8(q, s)
        self.assertEqual(y.shape, self.x.shape)

    def test_group_size_16(self):
        q, s = quantize_symmetric_int8(self.x, group_size=16)
        self.assertEqual(s.shape[-1], 128 // 16)
        y = dequantize_symmetric_int8(q, s)
        self.assertEqual(y.shape, self.x.shape)

    def test_group_size_32(self):
        q, s = quantize_symmetric_int8(self.x, group_size=32)
        self.assertEqual(s.shape[-1], 128 // 32)
        y = dequantize_symmetric_int8(q, s)
        self.assertEqual(y.shape, self.x.shape)

    def test_group_size_64(self):
        q, s = quantize_symmetric_int8(self.x, group_size=64)
        self.assertEqual(s.shape[-1], 128 // 64)
        y = dequantize_symmetric_int8(q, s)
        self.assertEqual(y.shape, self.x.shape)

    def test_group_size_128(self):
        q, s = quantize_symmetric_int8(self.x, group_size=128)
        self.assertEqual(s.shape[-1], 1)
        y = dequantize_symmetric_int8(q, s)
        self.assertEqual(y.shape, self.x.shape)

    def test_group_size_minus1_per_token(self):
        q, s = quantize_symmetric_int8(self.x, group_size=-1)
        self.assertEqual(s.shape[-1], 1)

    def test_invalid_group_size(self):
        with self.assertRaises(ValueError):
            quantize_symmetric_int8(self.x, group_size=13)

    def test_smaller_group_lower_error(self):
        torch.manual_seed(0)
        x = torch.randn(1, 2, 4, 128, dtype=torch.float16)

        q64, s64 = quantize_symmetric_int8(x, group_size=64)
        y64 = dequantize_symmetric_int8(q64, s64)
        err64 = (x - y64).abs().mean().item()

        q128, s128 = quantize_symmetric_int8(x, group_size=128)
        y128 = dequantize_symmetric_int8(q128, s128)
        err128 = (x - y128).abs().mean().item()

        self.assertLessEqual(
            err64, err128 * 1.1,
            "Finer group should not produce significantly higher error",
        )


class TestPercentileClipping(unittest.TestCase):
    """Test percentile clipping behavior."""

    def setUp(self):
        torch.manual_seed(42)

    def test_percentile_100_no_clipping(self):
        x = torch.randn(1, 2, 4, 128, dtype=torch.float16)
        q, s = quantize_symmetric_int8(x, percentile=100.0, group_size=128)
        self.assertEqual(q.dtype, torch.int8)
        self.assertTrue(q.abs().max().item() <= 127)

    def test_percentile_clips_outliers(self):
        x = torch.randn(1, 2, 1, 128, dtype=torch.float16)
        x[0, 0, 0, 0] = 100.0

        q_noclip, s_noclip = quantize_symmetric_int8(
            x, percentile=100.0, group_size=128
        )
        q_clip, s_clip = quantize_symmetric_int8(
            x, percentile=99.0, group_size=128
        )
        self.assertLess(
            s_clip.max().item(),
            s_noclip.max().item(),
            "Clipping should reduce scale",
        )

    def test_outlier_clipping_improves_non_outlier_reconstruction(self):
        x = torch.randn(1, 1, 1, 128, dtype=torch.float16)
        x[0, 0, 0, 0] = 120.0
        q_noclip, s_noclip = quantize_symmetric_int8(x, percentile=100.0, group_size=128)
        y_noclip = dequantize_symmetric_int8(q_noclip, s_noclip)
        q_clip, s_clip = quantize_symmetric_int8(x, percentile=99.0, group_size=128)
        y_clip = dequantize_symmetric_int8(q_clip, s_clip)

        # Exclude the outlier itself and compare average reconstruction error.
        err_noclip = (x[..., 1:] - y_noclip[..., 1:]).abs().mean()
        err_clip = (x[..., 1:] - y_clip[..., 1:]).abs().mean()
        self.assertLess(err_clip.item(), err_noclip.item())

    def test_percentile_values(self):
        x = torch.randn(1, 2, 4, 128, dtype=torch.float16)
        for pct in [99.0, 99.5, 99.9, 100.0]:
            q, s = quantize_symmetric_int8(x, percentile=pct, group_size=64)
            self.assertEqual(q.dtype, torch.int8)
            self.assertTrue(torch.isfinite(s).all())


class TestStaticScale(unittest.TestCase):
    """Test quantize_symmetric_int8_with_scale."""

    def setUp(self):
        torch.manual_seed(42)
        self.B, self.H, self.S, self.D = 1, 2, 4, 128
        self.group_size = 64
        self.num_groups = self.D // self.group_size

    def test_with_2d_scale(self):
        x = torch.randn(
            self.B, self.H, self.S, self.D, dtype=torch.float16
        )
        scale = torch.full(
            (self.H, self.num_groups), 0.01, dtype=torch.float16
        )
        q, s_out = quantize_symmetric_int8_with_scale(
            x, scale, self.group_size
        )
        self.assertEqual(q.dtype, torch.int8)
        self.assertEqual(q.shape, x.shape)
        self.assertEqual(s_out.shape[-1], self.num_groups)

    def test_with_4d_scale(self):
        x = torch.randn(
            self.B, self.H, self.S, self.D, dtype=torch.float16
        )
        scale = torch.full(
            (self.B, self.H, self.S, self.num_groups),
            0.01,
            dtype=torch.float16,
        )
        q, s_out = quantize_symmetric_int8_with_scale(
            x, scale, self.group_size
        )
        self.assertEqual(q.dtype, torch.int8)
        y = dequantize_symmetric_int8(q, s_out)
        self.assertEqual(y.shape, x.shape)

    def test_with_3d_scale(self):
        x = torch.randn(self.B, self.H, self.S, self.D, dtype=torch.float16)
        scale = torch.full((self.B, self.H, self.num_groups), 0.01, dtype=torch.float16)
        q, s_out = quantize_symmetric_int8_with_scale(x, scale, self.group_size)
        y = dequantize_symmetric_int8(q, s_out)
        self.assertEqual(y.shape, x.shape)

    def test_static_vs_dynamic_different_results(self):
        x = torch.randn(
            self.B, self.H, self.S, self.D, dtype=torch.float16
        )
        q_dyn, s_dyn = quantize_symmetric_int8(
            x, percentile=100.0, group_size=self.group_size
        )
        scale_static = torch.full(
            (self.H, self.num_groups), 0.005, dtype=torch.float16
        )
        q_static, s_static = quantize_symmetric_int8_with_scale(
            x, scale_static, self.group_size
        )
        self.assertFalse(
            torch.equal(q_dyn, q_static),
            "Different scales should produce different quantized values",
        )


class TestEdgeCases(unittest.TestCase):
    """Edge case and dtype tests."""

    def test_all_zeros(self):
        x = torch.zeros(1, 2, 4, 128, dtype=torch.float16)
        q, s = quantize_symmetric_int8(x, group_size=64)
        y = dequantize_symmetric_int8(q, s)
        self.assertTrue(torch.allclose(y, x, atol=1e-4))

    def test_constant_value(self):
        x = torch.full((1, 2, 4, 128), 0.5, dtype=torch.float16)
        q, s = quantize_symmetric_int8(x, group_size=64)
        y = dequantize_symmetric_int8(q, s)
        max_err = (x - y).abs().max().item()
        self.assertLess(max_err, 0.01)

    def test_non_float_input_raises(self):
        x = torch.randint(0, 10, (1, 2, 4, 128), dtype=torch.int32)
        with self.assertRaises(ValueError):
            quantize_symmetric_int8(x, group_size=64)

    def test_output_dtype_matches_input(self):
        x = torch.randn(1, 2, 4, 128, dtype=torch.float16)
        q, s = quantize_symmetric_int8(x, group_size=64)
        y = dequantize_symmetric_int8(q, s)
        self.assertEqual(y.dtype, torch.float16)

    def test_quantized_range(self):
        x = torch.randn(2, 4, 8, 128, dtype=torch.float16) * 10
        q, s = quantize_symmetric_int8(x, group_size=64)
        self.assertTrue(q.min().item() >= -127)
        self.assertTrue(q.max().item() <= 127)

    def test_scale_positive(self):
        x = torch.randn(1, 2, 4, 128, dtype=torch.float16)
        _, s = quantize_symmetric_int8(x, group_size=64)
        self.assertTrue((s > 0).all(), "All scales must be positive")


if __name__ == "__main__":
    unittest.main()
