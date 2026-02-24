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


if __name__ == "__main__":
    unittest.main()
