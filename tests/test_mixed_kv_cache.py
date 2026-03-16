#!/usr/bin/env python3
"""
Unit tests for Mixed KV Cache (K-INT8/V-INT4).

Tests:
- Basic append + get_kv round-trip
- K precision (INT8) > V precision (INT4) for same input
- Memory reporting
- Interface compatibility
- Multi-layer and multi-step decode
"""

import sys
import unittest
from pathlib import Path

import torch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.cache.mixed_kv_cache import MixedKVCache


class TestMixedKVCacheBasic(unittest.TestCase):
    """Basic functionality tests."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=2,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=512,
            k_group_size=16,
        )
        defaults.update(kwargs)
        return MixedKVCache(**defaults)

    def test_init(self):
        cache = self._make_cache()
        self.assertEqual(cache.num_layers, 2)
        self.assertEqual(cache.get_seq_len(), 0)

    def test_single_append_and_get(self):
        """Append and retrieve — shapes should match."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, S, D))
        self.assertEqual(v_out.shape, (B, H, S, D))
        self.assertTrue(torch.isfinite(k_out).all())
        self.assertTrue(torch.isfinite(v_out).all())

    def test_k_higher_precision_than_v(self):
        """K (INT8) should have lower quantization error than V (INT4)."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 32, 16
        torch.manual_seed(42)
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        k_mse = ((k - k_out) ** 2).mean().item()
        v_mse = ((v - v_out) ** 2).mean().item()

        # INT8 K should have lower MSE than INT4 V
        self.assertLess(k_mse, v_mse,
                        f"K MSE ({k_mse:.6f}) should be < V MSE ({v_mse:.6f})")

    def test_multi_step_decode(self):
        """Append prefill + decode tokens sequentially."""
        cache = self._make_cache()
        B, H, D = 1, 2, 16

        # Prefill
        k_pre = torch.randn(B, H, 16, D)
        v_pre = torch.randn(B, H, 16, D)
        cache.append(0, k_pre, v_pre)
        self.assertEqual(cache.get_seq_len(), 16)

        # Decode step 1
        k_dec = torch.randn(B, H, 1, D)
        v_dec = torch.randn(B, H, 1, D)
        cache.append(0, k_dec, v_dec)
        self.assertEqual(cache.get_seq_len(), 17)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 17, D))
        self.assertEqual(v_out.shape, (B, H, 17, D))

    def test_multi_layer(self):
        """Append to multiple layers independently."""
        cache = self._make_cache(num_layers=4)
        B, H, S, D = 1, 2, 8, 16

        for layer_id in range(4):
            k = torch.randn(B, H, S, D)
            v = torch.randn(B, H, S, D)
            cache.append(layer_id, k, v)

        for layer_id in range(4):
            k_out, v_out = cache.get_kv(layer_id)
            self.assertEqual(k_out.shape, (B, H, S, D))

    def test_clear(self):
        """Clear should reset cache."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        cache.append(0, torch.randn(B, H, S, D), torch.randn(B, H, S, D))
        self.assertEqual(cache.get_seq_len(), S)

        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

    def test_memory_mb(self):
        """Memory should be positive after append."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 64, 16
        cache.append(0, torch.randn(B, H, S, D), torch.randn(B, H, S, D))
        self.assertGreater(cache.get_memory_mb(), 0)

    def test_interface_compatibility(self):
        """Should have same interface as KIVIStyleKVCache."""
        cache = self._make_cache()
        self.assertEqual(cache.decode_attn_impl, "torch_ref")
        self.assertIsNone(cache.inv_tau)
        self.assertFalse(cache.use_attn_temperature)

    def test_shape_mismatch_raises(self):
        """k/v shape mismatch should raise."""
        cache = self._make_cache()
        with self.assertRaises(ValueError):
            cache.append(0, torch.randn(1, 2, 8, 16), torch.randn(1, 2, 4, 16))


if __name__ == "__main__":
    unittest.main()
