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
        # TST-050: INT8 asymmetric KIVI relative error bound.  Theoretical per-channel
        # NRMAE ≈ 1/(2*127) ≈ 0.004 for unit-variance randn.  Tolerance 0.05 is ~12×
        # to account for per-channel/per-token quantization granularity variation.
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
        # TST-050: INT4 asymmetric KIVI relative error bound.  Theoretical per-channel
        # NRMAE ≈ 1/(2*7) ≈ 0.071 for unit-variance randn.  Tolerance 0.25 is ~3.5×
        # to account for small tensor sizes and asymmetric quantization overhead.
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

    def test_decode_token_error_with_prefill_scale_is_bounded(self):
        """Decode token quantization with reused prefill scale should stay bounded."""
        cache = self._make_cache(quant_bits=8)
        B, H, D = 1, 2, 16
        torch.manual_seed(0)
        k_prefill = torch.randn(B, H, 16, D)
        v_prefill = torch.randn(B, H, 16, D)
        cache.append(0, k_prefill, v_prefill)

        k_dec = torch.randn(B, H, 1, D)
        v_dec = torch.randn(B, H, 1, D)
        cache.append(0, k_dec, v_dec)
        k_out, _ = cache.get_kv(0)
        k_last = k_out[:, :, -1:, :]
        rel_err = (k_last - k_dec).abs().mean() / (k_dec.abs().mean() + 1e-8)
        self.assertLess(rel_err.item(), 0.10)

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
        """clear() should reset seq_len/scales and support re-append."""
        cache = self._make_cache()
        k = torch.randn(1, 2, 8, 16)
        v = torch.randn(1, 2, 8, 16)
        cache.append(0, k, v)
        self.assertEqual(cache.get_seq_len(), 8)
        self.assertTrue(cache._k_scale_initialized[0])

        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)
        self.assertFalse(cache._k_scale_initialized[0])
        self.assertIsNone(cache._k_scale[0])
        self.assertIsNone(cache._k_zp[0])

        # Re-append should reinitialize K scale without crashing.
        cache.append(0, k, v)
        self.assertTrue(cache._k_scale_initialized[0])
        self.assertEqual(cache.get_seq_len(), 8)

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

    def test_invalid_shape_wrong_rank(self):
        """TST-069: 3D input (missing batch dim) should raise ValueError."""
        cache = self._make_cache()
        with self.assertRaises((ValueError, TypeError)):
            cache.append(0, torch.randn(1, 2, 16), torch.randn(1, 2, 16))

    def test_invalid_shape_kv_mismatch(self):
        """TST-069: K/V shape mismatch should raise ValueError."""
        cache = self._make_cache()
        with self.assertRaises((ValueError, TypeError)):
            cache.append(0, torch.randn(1, 2, 4, 16), torch.randn(1, 3, 4, 16))

    def test_invalid_shape_transposed_after_init(self):
        """TST-069: Transposed-like shape after cache init should raise."""
        cache = self._make_cache()
        cache.append(0, torch.randn(1, 2, 4, 16), torch.randn(1, 2, 4, 16))
        with self.assertRaises((ValueError, RuntimeError)):
            cache.append(0, torch.randn(1, 16, 2, 4), torch.randn(1, 16, 2, 4))

    def test_zero_batch_raises(self):
        cache = self._make_cache()
        with self.assertRaises(ValueError):
            cache.append(0, torch.randn(0, 2, 4, 16), torch.randn(0, 2, 4, 16))

    def test_float16_input_supported(self):
        cache = self._make_cache(dtype=torch.float16)
        k = torch.randn(1, 2, 8, 16, dtype=torch.float16)
        v = torch.randn(1, 2, 8, 16, dtype=torch.float16)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.dtype, torch.float16)
        self.assertEqual(v_out.dtype, torch.float16)

    def test_multi_clear_append_cycles(self):
        cache = self._make_cache()
        for _ in range(3):
            k = torch.randn(1, 2, 4, 16)
            v = torch.randn(1, 2, 4, 16)
            cache.append(0, k, v)
            self.assertEqual(cache.get_seq_len(), 4)
            cache.clear()
            self.assertEqual(cache.get_seq_len(), 0)

    def test_int4_storage_is_bit_packed(self):
        cache = self._make_cache(quant_bits=4)
        k = torch.randn(1, 2, 8, 16)
        v = torch.randn(1, 2, 8, 16)
        cache.append(0, k, v)
        # Stored head_dim should be packed to D/2.
        self.assertEqual(cache._k_cache[0].shape[-1], 8)
        self.assertEqual(cache._v_cache[0].shape[-1], 8)
        # Dequantized output shape should remain original D.
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape[-1], 16)
        self.assertEqual(v_out.shape[-1], 16)


class TestKIVICacheInit(unittest.TestCase):
    """Test constructor validation."""

    def test_invalid_num_layers(self):
        with self.assertRaises(ValueError):
            KIVIStyleKVCache(num_layers=0, device="cpu")

    def test_invalid_quant_bits(self):
        with self.assertRaises(ValueError):
            KIVIStyleKVCache(num_layers=1, device="cpu", quant_bits=3)


# ===========================================================================
# TST-004: End-to-end integration tests for KIVI + asymmetric_quant
# ===========================================================================


class TestKIVICacheEndToEnd(unittest.TestCase):
    """TST-004: Prefill -> decode -> get_kv full pipeline with asymmetric quant."""

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

    def test_prefill_decode_get_kv_int8(self):
        """Full prefill -> multi-step decode -> get_kv pipeline (INT8)."""
        cache = self._make_cache(quant_bits=8)
        B, H, D = 1, 2, 16
        torch.manual_seed(42)

        # Prefill: 16 tokens
        k_prefill = torch.randn(B, H, 16, D)
        v_prefill = torch.randn(B, H, 16, D)
        cache.append(0, k_prefill, v_prefill)
        self.assertEqual(cache.get_seq_len(), 16)
        self.assertTrue(cache._k_scale_initialized[0])

        # Decode: 8 tokens one at a time
        decode_ks = []
        decode_vs = []
        for _ in range(8):
            k_dec = torch.randn(B, H, 1, D)
            v_dec = torch.randn(B, H, 1, D)
            cache.append(0, k_dec, v_dec)
            decode_ks.append(k_dec)
            decode_vs.append(v_dec)

        self.assertEqual(cache.get_seq_len(), 24)

        # get_kv should return the full sequence
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 24, D))
        self.assertEqual(v_out.shape, (B, H, 24, D))
        self.assertTrue(torch.isfinite(k_out).all())
        self.assertTrue(torch.isfinite(v_out).all())

        # Prefill K round-trip error should be bounded
        k_prefill_out = k_out[:, :, :16, :]
        k_err = (k_prefill - k_prefill_out).abs().mean() / k_prefill.abs().mean()
        self.assertLess(k_err.item(), 0.05, "Prefill K round-trip error too large")

        # V round-trip error for prefill tokens
        v_prefill_out = v_out[:, :, :16, :]
        v_err = (v_prefill - v_prefill_out).abs().mean() / v_prefill.abs().mean()
        self.assertLess(v_err.item(), 0.05, "Prefill V round-trip error too large")

    def test_prefill_decode_get_kv_int4(self):
        """Full prefill -> decode -> get_kv pipeline (INT4 with bit packing)."""
        cache = self._make_cache(quant_bits=4)
        B, H, D = 1, 2, 16
        torch.manual_seed(42)

        k_prefill = torch.randn(B, H, 8, D)
        v_prefill = torch.randn(B, H, 8, D)
        cache.append(0, k_prefill, v_prefill)

        for _ in range(4):
            cache.append(0, torch.randn(B, H, 1, D), torch.randn(B, H, 1, D))

        self.assertEqual(cache.get_seq_len(), 12)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 12, D))
        self.assertEqual(v_out.shape, (B, H, 12, D))
        self.assertTrue(torch.isfinite(k_out).all())
        self.assertTrue(torch.isfinite(v_out).all())

        # INT4 has larger error budget
        k_err = (k_prefill - k_out[:, :, :8, :]).abs().mean() / k_prefill.abs().mean()
        self.assertLess(k_err.item(), 0.25, "INT4 prefill K error too large")

    def test_multi_layer_prefill_decode(self):
        """Prefill and decode across multiple layers."""
        num_layers = 4
        cache = self._make_cache(num_layers=num_layers)
        B, H, D = 1, 2, 16
        torch.manual_seed(7)

        # Prefill all layers
        for layer_id in range(num_layers):
            k = torch.randn(B, H, 8, D)
            v = torch.randn(B, H, 8, D)
            cache.append(layer_id, k, v)

        # Decode one token per layer
        for layer_id in range(num_layers):
            k = torch.randn(B, H, 1, D)
            v = torch.randn(B, H, 1, D)
            cache.append(layer_id, k, v)

        self.assertEqual(cache.get_seq_len(), 9)
        for layer_id in range(num_layers):
            k_out, v_out = cache.get_kv(layer_id)
            self.assertEqual(k_out.shape, (B, H, 9, D))
            self.assertTrue(torch.isfinite(k_out).all())
            self.assertTrue(torch.isfinite(v_out).all())


class TestKIVIAsymmetricScaleZP(unittest.TestCase):
    """TST-004: Verify asymmetric quantization scale/zp computation correctness."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=1,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=512,
            quant_bits=8,
        )
        defaults.update(kwargs)
        return KIVIStyleKVCache(**defaults)

    def test_k_scale_zp_shape_and_dtype(self):
        """K scale/zp should be [B, H, D] in float32."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_scale = cache._k_scale[0]
        k_zp = cache._k_zp[0]
        self.assertEqual(k_scale.shape, (B, H, D))
        self.assertEqual(k_zp.shape, (B, H, D))
        # ENG-009: scales must be float32
        self.assertEqual(k_scale.dtype, torch.float32)
        self.assertEqual(k_zp.dtype, torch.float32)

    def test_v_scale_zp_shape_and_dtype(self):
        """V scale/zp should be [B, H, S] in float32."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        v_scale = cache._v_scale[0][:, :, :S]
        v_zp = cache._v_zp[0][:, :, :S]
        self.assertEqual(v_scale.shape, (B, H, S))
        self.assertEqual(v_zp.shape, (B, H, S))
        self.assertEqual(v_scale.dtype, torch.float32)
        self.assertEqual(v_zp.dtype, torch.float32)

    def test_k_scale_positive(self):
        """K scale should be strictly positive (no zero division)."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)
        self.assertTrue((cache._k_scale[0] > 0).all())

    def test_v_scale_positive(self):
        """V scale should be strictly positive."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)
        v_scale = cache._v_scale[0][:, :, :S]
        self.assertTrue((v_scale > 0).all())

    def test_asymmetric_zp_is_nonzero_for_biased_input(self):
        """For biased (non-zero-mean) input, zero-point should be nonzero."""
        cache = self._make_cache()
        B, H, S, D = 1, 2, 8, 16
        # Create strongly biased K (mean = 10.0)
        k = torch.randn(B, H, S, D) + 10.0
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_zp = cache._k_zp[0]
        # For strongly biased data, zero_point should be significantly nonzero
        self.assertGreater(k_zp.abs().mean().item(), 0.1,
                           "Zero-point should be nonzero for biased input")

    def test_decode_reuses_prefill_k_scale(self):
        """Decode tokens must reuse prefill K scale, not recompute."""
        cache = self._make_cache()
        B, H, D = 1, 2, 16
        torch.manual_seed(0)

        # Prefill
        k_pf = torch.randn(B, H, 8, D)
        v_pf = torch.randn(B, H, 8, D)
        cache.append(0, k_pf, v_pf)
        k_scale_pf = cache._k_scale[0].clone()
        k_zp_pf = cache._k_zp[0].clone()

        # Decode (even with very different scale data)
        k_dec = torch.randn(B, H, 1, D) * 100.0
        v_dec = torch.randn(B, H, 1, D) * 100.0
        cache.append(0, k_dec, v_dec)

        # K scale/zp should NOT have changed
        self.assertTrue(torch.equal(cache._k_scale[0], k_scale_pf))
        self.assertTrue(torch.equal(cache._k_zp[0], k_zp_pf))

    def test_v_per_token_independence(self):
        """Each V token's scale should be independently computed."""
        cache = self._make_cache()
        B, H, D = 1, 2, 16

        # Append two tokens with very different magnitudes
        v1 = torch.randn(B, H, 1, D) * 0.01
        v2 = torch.randn(B, H, 1, D) * 100.0
        k_dummy = torch.randn(B, H, 1, D)

        cache.append(0, k_dummy, v1)
        cache.append(0, k_dummy.clone(), v2)

        vs0 = cache._v_scale[0][:, :, 0].mean().item()
        vs1 = cache._v_scale[0][:, :, 1].mean().item()
        # The scale for the large-magnitude token should be much larger
        self.assertGreater(vs1 / (vs0 + 1e-10), 10.0,
                           "V scale should differ significantly for different magnitude tokens")

    def test_dequant_reconstruction_within_bounds(self):
        """Asymmetric dequant: x_hat = q * scale + zp should reconstruct within bounds."""
        cache = self._make_cache(quant_bits=8)
        B, H, S, D = 1, 4, 32, 64
        torch.manual_seed(42)
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        # INT8 asymmetric: expected NRMAE < 0.005 for unit-variance randn,
        # tolerance 0.05 to account for per-channel/per-token granularity.
        k_nrmae = (k - k_out).abs().mean() / k.abs().mean()
        v_nrmae = (v - v_out).abs().mean() / v.abs().mean()
        self.assertLess(k_nrmae.item(), 0.05, f"K NRMAE = {k_nrmae.item():.4f}")
        self.assertLess(v_nrmae.item(), 0.05, f"V NRMAE = {v_nrmae.item():.4f}")

    def test_clear_resets_scale_zp(self):
        """After clear(), K scale/zp should be reset so next prefill recomputes.

        V scale/zp are re-allocated (empty) to maintain _ensure_capacity invariant
        when buffers are kept. K scale/zp are set to None since they are only
        computed during prefill.
        """
        cache = self._make_cache()
        B, H, D = 1, 2, 16
        k = torch.randn(B, H, 4, D)
        v = torch.randn(B, H, 4, D)
        cache.append(0, k, v)
        self.assertTrue(cache._k_scale_initialized[0])

        cache.clear()
        self.assertFalse(cache._k_scale_initialized[0])
        self.assertIsNone(cache._k_scale[0])
        self.assertIsNone(cache._k_zp[0])
        # V scale/zp are re-allocated (not None) when buffers were allocated,
        # to maintain the _ensure_capacity invariant.
        self.assertIsNotNone(cache._v_scale[0])
        self.assertIsNotNone(cache._v_zp[0])

        # Re-append should work and recompute K scale
        k2 = torch.randn(B, H, 4, D) * 5.0
        v2 = torch.randn(B, H, 4, D) * 5.0
        cache.append(0, k2, v2)
        self.assertTrue(cache._k_scale_initialized[0])
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, 4, D))
        self.assertTrue(torch.isfinite(k_out).all())


class TestKIVICacheInvTau(unittest.TestCase):
    """Tests for inv_tau / use_attn_temperature support (Phase 1A)."""

    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=2,
            device="cpu",
            dtype=torch.float32,
            max_seq_len=512,
            quant_bits=4,
        )
        defaults.update(kwargs)
        return KIVIStyleKVCache(**defaults)

    def test_inv_tau_none_by_default(self):
        """Without inv_tau, cache should have inv_tau=None."""
        cache = self._make_cache()
        self.assertIsNone(cache.inv_tau)
        self.assertFalse(cache.use_attn_temperature)

    def test_inv_tau_stored(self):
        """inv_tau tensor should be stored on cache."""
        inv_tau = torch.ones(2, 4)  # [num_layers, num_heads]
        cache = self._make_cache(inv_tau=inv_tau, use_attn_temperature=True)
        self.assertIsNotNone(cache.inv_tau)
        self.assertTrue(cache.use_attn_temperature)
        self.assertEqual(cache.inv_tau.shape, (2, 4))

    def test_inv_tau_does_not_affect_quantization(self):
        """inv_tau is for Q pre-scaling only; should not change K/V quantization."""
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)

        # Without inv_tau
        cache1 = self._make_cache()
        cache1.append(0, k.clone(), v.clone())
        k1, v1 = cache1.get_kv(0)

        # With inv_tau
        inv_tau = torch.ones(2, 4) * 1.5
        cache2 = self._make_cache(inv_tau=inv_tau, use_attn_temperature=True)
        cache2.append(0, k.clone(), v.clone())
        k2, v2 = cache2.get_kv(0)

        # Quantized K/V should be identical (inv_tau only affects Q)
        torch.testing.assert_close(k1, k2, rtol=0, atol=0)
        torch.testing.assert_close(v1, v2, rtol=0, atol=0)

    def test_v_percentile_override(self):
        """External v_percentile should be usable for Phase 1B calibrated V."""
        cache = self._make_cache(v_percentile=99.0)
        self.assertEqual(cache.v_percentile, 99.0)

        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D) * 10
        v = torch.randn(B, H, S, D) * 10
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, S, D))
        self.assertTrue(torch.isfinite(v_out).all())


class TestKIVIResidualBuffer(unittest.TestCase):
    """Tests for KIVI residual buffer (§3.3 enhancement)."""

    def _make_cache(self, residual_length=4, quant_bits=8):
        return KIVIStyleKVCache(
            num_layers=2, device="cpu", quant_bits=quant_bits,
            residual_length=residual_length,
        )

    def test_residual_zero_is_noop(self):
        """residual_length=0 should behave identically to original KIVI."""
        cache = KIVIStyleKVCache(num_layers=1, device="cpu", residual_length=0)
        B, H, S, D = 1, 2, 8, 16
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (B, H, S, D))
        self.assertEqual(cache.get_seq_len(), S)

    def test_decode_tokens_go_to_residual_first(self):
        """First r decode tokens should stay in FP16 buffer."""
        cache = self._make_cache(residual_length=3)
        B, H, D = 1, 2, 16

        # Prefill
        prefill_k = torch.randn(B, H, 4, D)
        prefill_v = torch.randn(B, H, 4, D)
        cache.append(0, prefill_k, prefill_v)
        self.assertEqual(cache.get_seq_len(), 4)  # all in quantized cache

        # Decode 3 tokens (should go to residual buffer)
        for i in range(3):
            dk = torch.randn(B, H, 1, D)
            dv = torch.randn(B, H, 1, D)
            cache.append(0, dk, dv)

        # Total seq_len should be 4 (quantized) + 3 (residual) = 7
        self.assertEqual(cache.get_seq_len(), 7)

        # get_kv should return all 7 tokens
        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape[2], 7)
        self.assertEqual(v_out.shape[2], 7)

    def test_residual_eviction(self):
        """When buffer is full, oldest token should be evicted to quantized cache."""
        cache = self._make_cache(residual_length=2)
        B, H, D = 1, 2, 16

        # Prefill
        cache.append(0, torch.randn(B, H, 4, D), torch.randn(B, H, 4, D))
        self.assertEqual(cache.get_seq_len(), 4)

        # Fill residual buffer (2 tokens)
        cache.append(0, torch.randn(B, H, 1, D), torch.randn(B, H, 1, D))
        cache.append(0, torch.randn(B, H, 1, D), torch.randn(B, H, 1, D))
        self.assertEqual(cache.get_seq_len(), 6)

        # 3rd decode token: evicts oldest residual → quantized cache grows by 1
        cache.append(0, torch.randn(B, H, 1, D), torch.randn(B, H, 1, D))
        self.assertEqual(cache.get_seq_len(), 7)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape[2], 7)

    def test_clear_resets_residual(self):
        """clear() should reset residual buffer."""
        cache = self._make_cache(residual_length=3)
        B, H, D = 1, 2, 16
        cache.append(0, torch.randn(B, H, 4, D), torch.randn(B, H, 4, D))
        cache.append(0, torch.randn(B, H, 1, D), torch.randn(B, H, 1, D))
        self.assertEqual(cache.get_seq_len(), 5)

        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)
        self.assertEqual(cache._residual_lens[0], 0)


    def test_kvc092_single_token_prefill_initializes_scale(self):
        """KVC-092 regression: a single-token prefill (new_seq_len=1) must go through
        normal quantization path to initialize K scale, not into residual buffer."""
        cache = self._make_cache(residual_length=3, quant_bits=8)
        B, H, D = 1, 2, 16

        # Single-token "prefill" — must initialize K scale, not enter residual
        single_k = torch.randn(B, H, 1, D)
        single_v = torch.randn(B, H, 1, D)
        cache.append(0, single_k, single_v)

        # K scale should now be initialized
        self.assertTrue(cache._k_scale_initialized[0],
            "Single-token prefill must initialize K scale")
        # Seq len should be 1 (in quantized cache, not residual)
        self.assertEqual(cache._layer_seq_lens[0], 1)
        self.assertEqual(cache._residual_lens[0], 0)

    def test_kvc090_evicted_token_is_oldest_not_shifted(self):
        """KVC-090 regression: evicted token must be the actual oldest buffer token,
        not the shifted slot-1 data.  Before the fix, evict_k/v were views that got
        overwritten by the in-place shift, silently losing the oldest token."""
        cache = self._make_cache(residual_length=2, quant_bits=8)
        B, H, D = 1, 2, 16

        # Prefill
        cache.append(0, torch.randn(B, H, 4, D), torch.randn(B, H, 4, D))

        # Decode: fill buffer with known tokens
        token_a = torch.full((B, H, 1, D), 1.0)
        token_b = torch.full((B, H, 1, D), 2.0)
        cache.append(0, token_a.clone(), token_a.clone())  # slot 0
        cache.append(0, token_b.clone(), token_b.clone())  # slot 1

        # Buffer is now full [token_a, token_b].
        # Decode one more → token_a should be evicted (quantized), buffer becomes [token_b, token_c]
        token_c = torch.full((B, H, 1, D), 3.0)
        cache.append(0, token_c.clone(), token_c.clone())

        k_out, v_out = cache.get_kv(0)
        # Total: 4 prefill + 1 evicted (quantized) + 2 residual = 7
        self.assertEqual(k_out.shape[2], 7)

        # The evicted quantized token (position 4) should be closest to token_a (1.0),
        # NOT token_b (2.0).  INT8 quantize-dequantize introduces small error,
        # so check that the mean is closer to 1.0 than to 2.0.
        evicted_k = k_out[:, :, 4:5, :].float().mean().item()
        self.assertAlmostEqual(evicted_k, 1.0, delta=0.3,
            msg=f"Evicted token k mean={evicted_k:.3f}, expected ~1.0 (token_a)")


if __name__ == "__main__":
    unittest.main()
