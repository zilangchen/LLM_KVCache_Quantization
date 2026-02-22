#!/usr/bin/env python3
"""
Unit tests for KIVI-style KV Cache.

Tests:
- Basic append + get_kv round-trip
- Per-channel K scale persistence across decode steps
- Per-token V scale independence
- INT8 and INT4 variants
- Cache capacity growth
- Memory reporting
- Interface compatibility with INT8KVCache
- Edge cases
"""

import sys
import unittest
from pathlib import Path

import torch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.cache.kivi_style_cache import KIVIStyleKVCache


class TestKIVICacheBasic(unittest.TestCase):
    """Basic functionality tests."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=2,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=512,
            quant_bits=8,
        )
        defaults.update(kwargs)
        return KIVIStyleKVCache(**defaults)

    def test_init(self):
        cache = self._make_cache()
        self.assertEqual(cache.num_layers, 2)
        self.assertEqual(cache.get_seq_len(), 0)

    def test_single_append_and_get(self):
        """Append a single prefill chunk and retrieve it."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)
        self.assertEqual(cache.get_seq_len(), S)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, S, D))
        self.assertEqual(v_out.shape, (B, H, S, D))

    def test_round_trip_error_int8(self):
        """INT8 round-trip error should be reasonable."""
        cache = self._make_cache(quant_bits=8)
        B, H, S, D = 1, 4, 32, 64
        torch.manual_seed(42)
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        k_err = (k - k_out).abs().mean() / k.abs().mean()
        v_err = (v - v_out).abs().mean() / v.abs().mean()
        self.assertLess(k_err.item(), 0.05, "K round-trip error too large")
        self.assertLess(v_err.item(), 0.05, "V round-trip error too large")

    def test_round_trip_error_int4(self):
        """INT4 round-trip error should be larger but bounded."""
        cache = self._make_cache(quant_bits=4)
        B, H, S, D = 1, 2, 16, 32
        torch.manual_seed(42)
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        k_err = (k - k_out).abs().mean() / k.abs().mean()
        v_err = (v - v_out).abs().mean() / v.abs().mean()
        self.assertLess(k_err.item(), 0.25, "INT4 K error too large")
        self.assertLess(v_err.item(), 0.25, "INT4 V error too large")

    def test_multi_layer(self):
        """Test appending to multiple layers."""
        cache = self._make_cache(num_layers=4)
        B, H, S, D = 1, 2, 4, 16
        for layer_id in range(4):
            k = torch.randn(B, H, S, D)
            v = torch.randn(B, H, S, D)
            cache.append(layer_id, k, v)

        for layer_id in range(4):
            k_out, v_out = cache.get_kv(layer_id)
            self.assertEqual(k_out.shape, (B, H, S, D))


class TestKIVICacheDecodeAppend(unittest.TestCase):
    """Test prefill + decode append pattern."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=2,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=512,
            quant_bits=8,
        )
        defaults.update(kwargs)
        return KIVIStyleKVCache(**defaults)

    def test_prefill_then_decode(self):
        """Prefill with S tokens, then append 1 token at a time (decode)."""
        cache = self._make_cache()
        B, H, D = 1, 2, 16

        # Prefill: 8 tokens
        k_prefill = torch.randn(B, H, 8, D)
        v_prefill = torch.randn(B, H, 8, D)
        cache.append(0, k_prefill, v_prefill)
        self.assertEqual(cache.get_seq_len(), 8)

        # Decode: 4 tokens one at a time
        for i in range(4):
            k_dec = torch.randn(B, H, 1, D)
            v_dec = torch.randn(B, H, 1, D)
            cache.append(0, k_dec, v_dec)

        self.assertEqual(cache.get_seq_len(), 12)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 12, D))
        self.assertEqual(v_out.shape, (B, H, 12, D))

    def test_k_scale_reused_in_decode(self):
        """K scale from prefill should be reused for decode tokens."""
        cache = self._make_cache()
        B, H, D = 1, 2, 16

        # Prefill
        k_prefill = torch.randn(B, H, 8, D)
        v_prefill = torch.randn(B, H, 8, D)
        cache.append(0, k_prefill, v_prefill)

        # Record the K scale after prefill
        k_scale_after_prefill = cache._k_scale[0].clone()
        self.assertTrue(cache._k_scale_initialized[0])

        # Decode token
        k_dec = torch.randn(B, H, 1, D)
        v_dec = torch.randn(B, H, 1, D)
        cache.append(0, k_dec, v_dec)

        # K scale should NOT change after decode
        self.assertTrue(torch.equal(cache._k_scale[0], k_scale_after_prefill))

    def test_v_scale_independent_per_token(self):
        """Each V token should have its own scale."""
        cache = self._make_cache()
        B, H, D = 1, 2, 16

        # Append tokens with very different V scales
        v1 = torch.randn(B, H, 1, D) * 100  # large scale
        v2 = torch.randn(B, H, 1, D) * 0.01  # tiny scale
        k_dummy = torch.randn(B, H, 1, D)

        cache.append(0, k_dummy, v1)
        cache.append(0, k_dummy, v2)

        # V scales should differ significantly
        vs0 = cache._v_scale[0][0, 0, 0].item()
        vs1 = cache._v_scale[0][0, 0, 1].item()
        self.assertGreater(abs(vs0 - vs1), 0.01)


class TestKIVICacheCapacity(unittest.TestCase):
    """Test cache capacity management."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            quant_bits=8,
        )
        defaults.update(kwargs)
        return KIVIStyleKVCache(**defaults)

    def test_auto_grow(self):
        """Cache should auto-grow when exceeding initial capacity."""
        cache = self._make_cache(max_seq_len=1024)
        B, H, D = 1, 2, 16

        # Append many tokens to force capacity growth
        for _ in range(300):
            k = torch.randn(B, H, 1, D)
            v = torch.randn(B, H, 1, D)
            cache.append(0, k, v)

        self.assertEqual(cache.get_seq_len(), 300)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape[2], 300)

    def test_max_seq_len_enforced(self):
        """Exceeding max_seq_len should raise ValueError."""
        cache = self._make_cache(max_seq_len=10)
        B, H, D = 1, 2, 16
        k = torch.randn(B, H, 11, D)
        v = torch.randn(B, H, 11, D)
        with self.assertRaises(ValueError):
            cache.append(0, k, v)


class TestKIVICacheInterface(unittest.TestCase):
    """Test interface compatibility."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=2,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=256,
            quant_bits=8,
        )
        defaults.update(kwargs)
        return KIVIStyleKVCache(**defaults)

    def test_clear(self):
        """clear() should reset seq_len but keep buffers."""
        cache = self._make_cache()
        k = torch.randn(1, 2, 8, 16)
        v = torch.randn(1, 2, 8, 16)
        cache.append(0, k, v)
        self.assertEqual(cache.get_seq_len(), 8)

        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)

    def test_release(self):
        """release() should free all buffers."""
        cache = self._make_cache()
        k = torch.randn(1, 2, 8, 16)
        v = torch.randn(1, 2, 8, 16)
        cache.append(0, k, v)

        cache.release()
        self.assertEqual(cache.get_seq_len(), 0)
        self.assertIsNone(cache._k_cache[0])

    def test_get_memory_mb(self):
        """get_memory_mb should return a positive value after append."""
        cache = self._make_cache()
        k = torch.randn(1, 2, 32, 64)
        v = torch.randn(1, 2, 32, 64)
        cache.append(0, k, v)
        mem = cache.get_memory_mb()
        self.assertGreater(mem, 0.0)

    def test_decode_stats(self):
        """Decode stats interface should work."""
        cache = self._make_cache()
        cache.record_fused_decode(0, "torch_ref")
        stats = cache.get_decode_stats()
        self.assertEqual(stats["fused_decode_calls"], 1)
        self.assertEqual(stats["torch_ref_calls"], 1)

        cache.reset_decode_stats()
        stats = cache.get_decode_stats()
        self.assertEqual(stats["fused_decode_calls"], 0)

    def test_decode_attn_impl_is_torch_ref(self):
        """KIVI cache should always use torch_ref."""
        cache = self._make_cache()
        self.assertEqual(cache.decode_attn_impl, "torch_ref")

    def test_no_inv_tau(self):
        """KIVI cache should not have inv_tau."""
        cache = self._make_cache()
        self.assertIsNone(cache.inv_tau)
        self.assertFalse(cache.use_attn_temperature)

    def test_empty_cache_raises(self):
        """get_kv on empty layer should raise."""
        cache = self._make_cache()
        with self.assertRaises(ValueError):
            cache.get_kv(0)

    def test_invalid_layer_raises(self):
        """append with invalid layer_id should raise."""
        cache = self._make_cache()
        k = torch.randn(1, 2, 4, 16)
        v = torch.randn(1, 2, 4, 16)
        with self.assertRaises(ValueError):
            cache.append(-1, k, v)
        with self.assertRaises(ValueError):
            cache.append(2, k, v)  # num_layers=2, so layer_id=2 is out of range


class TestKIVICacheInit(unittest.TestCase):
    """Test constructor validation."""

    def test_invalid_num_layers(self):
        with self.assertRaises(ValueError):
            KIVIStyleKVCache(num_layers=0, device="cpu")

    def test_invalid_quant_bits(self):
        with self.assertRaises(ValueError):
            KIVIStyleKVCache(num_layers=1, device="cpu", quant_bits=3)


if __name__ == "__main__":
    unittest.main()
