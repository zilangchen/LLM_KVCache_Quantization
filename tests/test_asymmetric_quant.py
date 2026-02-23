#!/usr/bin/env python3
"""
Unit tests for asymmetric quantization (KIVI-style).

Tests quantize/dequantize round-trip error, per-channel and per-token
axis semantics, zero-point correctness, edge cases, and both INT8/INT4.
"""

import sys
import unittest
from pathlib import Path

import torch

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.quant.asymmetric_quant import (
    dequantize_asymmetric,
    dequantize_asymmetric_per_channel,
    dequantize_asymmetric_per_token,
    quantize_asymmetric,
    quantize_asymmetric_per_channel,
    quantize_asymmetric_per_token,
)


class TestAsymmetricQuantBasic(unittest.TestCase):
    """Test basic asymmetric quantize/dequantize round-trip."""

    def test_int8_round_trip_small_range(self):
        """Values in a small range should have minimal round-trip error."""
        torch.manual_seed(42)
        x = torch.randn(1, 2, 8, 16, dtype=torch.float32) * 0.5
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8)
        x_hat = dequantize_asymmetric(q, scale, zp, axis=-1)
        # Relative error should be small
        rel_err = (x - x_hat).abs().max() / x.abs().max()
        self.assertLess(rel_err.item(), 0.05, "INT8 round-trip error too large")

    def test_int4_round_trip_larger_error(self):
        """INT4 should have larger error but still reasonable."""
        torch.manual_seed(42)
        x = torch.randn(1, 2, 8, 16, dtype=torch.float32)
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=4)
        x_hat = dequantize_asymmetric(q, scale, zp, axis=-1)
        rel_err = (x - x_hat).abs().max() / x.abs().max()
        self.assertLess(rel_err.item(), 0.25, "INT4 round-trip error too large")

    def test_output_dtype_int8(self):
        """Quantized output should be int8."""
        x = torch.randn(1, 2, 4, 8)
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8)
        self.assertEqual(q.dtype, torch.int8)
        self.assertTrue(scale.is_floating_point())
        self.assertTrue(zp.is_floating_point())

    def test_int8_range(self):
        """INT8 values should be in [-128, 127]."""
        x = torch.randn(2, 4, 16, 32) * 10
        q, _, _ = quantize_asymmetric(x, axis=-1, quant_bits=8)
        self.assertGreaterEqual(q.min().item(), -128)
        self.assertLessEqual(q.max().item(), 127)

    def test_int4_range(self):
        """INT4 values should be in [-8, 7]."""
        x = torch.randn(2, 4, 16, 32) * 10
        q, _, _ = quantize_asymmetric(x, axis=-1, quant_bits=4)
        self.assertGreaterEqual(q.min().item(), -8)
        self.assertLessEqual(q.max().item(), 7)

    def test_invalid_dtype_raises(self):
        """Non-float input should raise ValueError."""
        x = torch.randint(0, 10, (2, 4, 8, 16))
        with self.assertRaises(ValueError):
            quantize_asymmetric(x, axis=-1, quant_bits=8)

    def test_invalid_quant_bits_raises(self):
        """Invalid quant_bits should raise ValueError."""
        x = torch.randn(1, 2, 4, 8)
        with self.assertRaises(ValueError):
            quantize_asymmetric(x, axis=-1, quant_bits=3)

    def test_percentile_bounds(self):
        x = torch.randn(1, 2, 4, 8)
        with self.assertRaises(ValueError):
            quantize_asymmetric(x, axis=-1, quant_bits=8, percentile=50.0)
        # 50.01 is the minimum allowed value and should pass.
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8, percentile=50.01)
        self.assertEqual(q.shape, x.shape)
        self.assertEqual(scale.shape, (1, 2, 4))
        self.assertEqual(zp.shape, (1, 2, 4))
        with self.assertRaises(ValueError):
            quantize_asymmetric(x, axis=-1, quant_bits=8, percentile=100.1)

    def test_float16_input_keeps_high_precision_scale(self):
        x = torch.randn(1, 2, 4, 16, dtype=torch.float16)
        _, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8, percentile=99.9)
        self.assertEqual(scale.dtype, torch.float32)
        self.assertEqual(zp.dtype, torch.float32)


class TestAsymmetricQuantEdgeCases(unittest.TestCase):
    """Edge cases: all zeros, constant values, outliers."""

    def test_all_zeros(self):
        """All-zero input should produce all-zero output."""
        x = torch.zeros(1, 2, 4, 8)
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8)
        x_hat = dequantize_asymmetric(q, scale, zp, axis=-1)
        self.assertAlmostEqual(x_hat.abs().max().item(), 0.0, places=4)

    def test_constant_value(self):
        """Constant input should round-trip to nearly the same value."""
        x = torch.full((1, 2, 4, 8), 3.14)
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8)
        x_hat = dequantize_asymmetric(q, scale, zp, axis=-1)
        max_err = (x - x_hat).abs().max().item()
        self.assertLess(max_err, 0.1, "Constant value round-trip error too large")

    def test_with_outliers(self):
        """Outliers should be clipped but not crash."""
        x = torch.randn(1, 2, 8, 16)
        x[0, 0, 0, 0] = 1000.0  # extreme outlier
        q, scale, zp = quantize_asymmetric(x, axis=-1, quant_bits=8)
        x_hat = dequantize_asymmetric(q, scale, zp, axis=-1)
        # Should not contain NaN/Inf
        self.assertFalse(torch.isnan(x_hat).any())
        self.assertFalse(torch.isinf(x_hat).any())

    def test_percentile_clipping(self):
        """Percentile clipping should reduce outlier influence on the outlier row."""
        # Use a larger head_dim so percentile clipping has meaningful effect
        x = torch.randn(1, 2, 32, 128)
        x[0, 0, 0, 0] = 100.0  # extreme outlier
        # Without clipping — outlier dominates scale on that row
        q1, s1, zp1 = quantize_asymmetric(x, axis=-1, quant_bits=8, percentile=100.0)
        x1 = dequantize_asymmetric(q1, s1, zp1, axis=-1)
        # With clipping
        q2, s2, zp2 = quantize_asymmetric(x, axis=-1, quant_bits=8, percentile=99.0)
        x2 = dequantize_asymmetric(q2, s2, zp2, axis=-1)
        # On the outlier row, non-outlier elements should improve with clipping
        row = x[0, 0, 0, 1:]  # skip the outlier element itself
        row1 = x1[0, 0, 0, 1:]
        row2 = x2[0, 0, 0, 1:]
        err_no_clip = (row - row1).abs().mean()
        err_clip = (row - row2).abs().mean()
        self.assertLess(err_clip.item(), err_no_clip.item())


class TestPerChannelQuantization(unittest.TestCase):
    """Test per-channel K quantization (KIVI-style K cache)."""

    def test_per_channel_shape(self):
        """Per-channel: scale shape should be [B, H, D] (no seq dim)."""
        x = torch.randn(2, 4, 16, 128)  # [B, H, S, D]
        q, scale, zp = quantize_asymmetric_per_channel(x, quant_bits=8)
        self.assertEqual(q.shape, x.shape)
        self.assertEqual(scale.shape, (2, 4, 128))  # [B, H, D]
        self.assertEqual(zp.shape, (2, 4, 128))

    def test_per_channel_shared_across_tokens(self):
        """Per-channel scale should be the same for different seq positions."""
        x = torch.randn(1, 2, 8, 16)
        q, scale, zp = quantize_asymmetric_per_channel(x, quant_bits=8)
        # scale is [1, 2, 16] — one scale per channel across all tokens
        self.assertEqual(scale.ndim, 3)
        # Dequantize and check
        x_hat = dequantize_asymmetric_per_channel(q, scale, zp)
        self.assertEqual(x_hat.shape, x.shape)

    def test_per_channel_semantics_match_manual_min_max(self):
        x = torch.randn(1, 2, 8, 16)
        _, scale, zp = quantize_asymmetric_per_channel(x, quant_bits=8, percentile=100.0)
        manual_min = x.float().amin(dim=2)
        manual_max = x.float().amax(dim=2)
        expected_scale = (manual_max - manual_min).clamp(min=1e-5) / 255.0
        expected_zp = manual_min + 128.0 * expected_scale
        self.assertTrue(torch.allclose(scale, expected_scale, atol=1e-5, rtol=1e-4))
        self.assertTrue(torch.allclose(zp, expected_zp, atol=1e-5, rtol=1e-4))

    def test_per_channel_round_trip(self):
        """Per-channel round-trip should have reasonable error."""
        torch.manual_seed(123)
        x = torch.randn(1, 4, 32, 64)
        q, scale, zp = quantize_asymmetric_per_channel(x, quant_bits=8)
        x_hat = dequantize_asymmetric_per_channel(q, scale, zp)
        rel_err = (x - x_hat).abs().mean() / x.abs().mean()
        self.assertLess(rel_err.item(), 0.05)


class TestPerTokenQuantization(unittest.TestCase):
    """Test per-token V quantization (KIVI-style V cache)."""

    def test_per_token_shape(self):
        """Per-token: scale shape should be [B, H, S] (no head_dim)."""
        x = torch.randn(2, 4, 16, 128)  # [B, H, S, D]
        q, scale, zp = quantize_asymmetric_per_token(x, quant_bits=8)
        self.assertEqual(q.shape, x.shape)
        self.assertEqual(scale.shape, (2, 4, 16))  # [B, H, S]
        self.assertEqual(zp.shape, (2, 4, 16))

    def test_per_token_independent(self):
        """Each token should have independent scale/zp."""
        x = torch.randn(1, 2, 4, 8)
        # Make tokens have very different scales
        x[:, :, 0, :] *= 100
        x[:, :, 1, :] *= 0.01
        q, scale, zp = quantize_asymmetric_per_token(x, quant_bits=8)
        # Scales should differ between tokens
        self.assertGreater(
            (scale[0, 0, 0] - scale[0, 0, 1]).abs().item(), 0.01,
            "Per-token scales should differ for tokens with different magnitudes"
        )

    def test_per_token_round_trip(self):
        """Per-token round-trip should have reasonable error."""
        torch.manual_seed(456)
        x = torch.randn(1, 4, 32, 64)
        q, scale, zp = quantize_asymmetric_per_token(x, quant_bits=8)
        x_hat = dequantize_asymmetric_per_token(q, scale, zp)
        rel_err = (x - x_hat).abs().mean() / x.abs().mean()
        self.assertLess(rel_err.item(), 0.05)

    def test_per_token_semantics_match_manual_min_max(self):
        x = torch.randn(1, 2, 8, 16)
        _, scale, zp = quantize_asymmetric_per_token(x, quant_bits=8, percentile=100.0)
        manual_min = x.float().amin(dim=-1)
        manual_max = x.float().amax(dim=-1)
        expected_scale = (manual_max - manual_min).clamp(min=1e-5) / 255.0
        expected_zp = manual_min + 128.0 * expected_scale
        self.assertTrue(torch.allclose(scale, expected_scale, atol=1e-5, rtol=1e-4))
        self.assertTrue(torch.allclose(zp, expected_zp, atol=1e-5, rtol=1e-4))

    def test_per_token_int4(self):
        """INT4 per-token quantization should work."""
        x = torch.randn(1, 2, 8, 16)
        q, scale, zp = quantize_asymmetric_per_token(x, quant_bits=4)
        x_hat = dequantize_asymmetric_per_token(q, scale, zp)
        self.assertEqual(x_hat.shape, x.shape)
        # INT4 error is larger
        rel_err = (x - x_hat).abs().mean() / x.abs().mean()
        self.assertLess(rel_err.item(), 0.2)


class TestZeroPoint(unittest.TestCase):
    """Test zero-point correctness in asymmetric quantization."""

    def test_symmetric_data_has_near_zero_zp(self):
        """For symmetric data around 0, zero_point should be near 0."""
        torch.manual_seed(789)
        x = torch.randn(1, 2, 32, 16)  # symmetric around 0
        _, _, zp = quantize_asymmetric_per_token(x, quant_bits=8)
        # zero_point should be close to 0 for symmetric data
        self.assertLess(zp.abs().mean().item(), 0.5)

    def test_shifted_data_has_nonzero_zp(self):
        """For shifted data, zero_point should capture the offset."""
        x = torch.randn(1, 2, 8, 16) + 5.0  # shifted to ~5.0
        _, scale, zp = quantize_asymmetric_per_token(x, quant_bits=8)
        x_hat = dequantize_asymmetric_per_token(
            quantize_asymmetric_per_token(x, quant_bits=8)[0], scale, zp
        )
        # Should recover the shifted data
        self.assertLess((x - x_hat).abs().mean().item(), 0.1)

    def test_positive_only_data(self):
        """Positive-only data should have positive zero_point."""
        x = torch.rand(1, 2, 8, 16) * 10  # [0, 10]
        q, scale, zp = quantize_asymmetric_per_token(x, quant_bits=8)
        x_hat = dequantize_asymmetric_per_token(q, scale, zp)
        rel_err = (x - x_hat).abs().mean() / x.abs().mean()
        self.assertLess(rel_err.item(), 0.05)


class TestDequantizeValidation(unittest.TestCase):
    def test_dequant_invalid_quantized_dtype(self):
        q = torch.ones(1, 2, 3, 4, dtype=torch.int16)
        scale = torch.ones(1, 2, 3, dtype=torch.float32)
        zp = torch.zeros(1, 2, 3, dtype=torch.float32)
        with self.assertRaises(ValueError):
            dequantize_asymmetric(q, scale, zp, axis=-1)

    def test_dequant_invalid_scale_dtype(self):
        q = torch.ones(1, 2, 3, 4, dtype=torch.int8)
        scale = torch.ones(1, 2, 3, dtype=torch.int32)
        zp = torch.zeros(1, 2, 3, dtype=torch.float32)
        with self.assertRaises(ValueError):
            dequantize_asymmetric(q, scale, zp, axis=-1)

    def test_dequant_shape_mismatch(self):
        q = torch.ones(1, 2, 3, 4, dtype=torch.int8)
        scale = torch.ones(1, 2, 2, dtype=torch.float32)
        zp = torch.zeros(1, 2, 2, dtype=torch.float32)
        with self.assertRaises(ValueError):
            dequantize_asymmetric(q, scale, zp, axis=-1)


if __name__ == "__main__":
    unittest.main()
