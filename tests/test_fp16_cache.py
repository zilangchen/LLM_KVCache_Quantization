"""Unit tests for FP16 KV Cache."""

import unittest

import torch

from src.cache.fp16_cache import FP16KVCache


class TestFP16KVCacheBasic(unittest.TestCase):
    """Basic append / get / shape tests."""

    def setUp(self):
        self.B, self.H, self.D = 2, 4, 128
        self.num_layers = 2

    def test_append_get_exact_match(self):
        cache = FP16KVCache(num_layers=self.num_layers, device="cpu")
        k = torch.randn(self.B, self.H, 5, self.D, dtype=torch.float16)
        v = torch.randn(self.B, self.H, 5, self.D, dtype=torch.float16)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        self.assertTrue(
            torch.equal(k, k_out),
            "FP16 cache should preserve exact values",
        )
        self.assertTrue(
            torch.equal(v, v_out),
            "FP16 cache should preserve exact values",
        )

    def test_seq_len_tracking(self):
        cache = FP16KVCache(num_layers=self.num_layers, device="cpu")
        self.assertEqual(cache.get_seq_len(), 0)

        k = torch.randn(self.B, self.H, 3, self.D, dtype=torch.float16)
        v = torch.randn(self.B, self.H, 3, self.D, dtype=torch.float16)
        cache.append(0, k, v)
        self.assertEqual(cache.get_seq_len(), 3)

    def test_incremental_append(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        tokens = []
        for step in range(5):
            k = torch.randn(1, self.H, 1, self.D, dtype=torch.float16)
            v = torch.randn(1, self.H, 1, self.D, dtype=torch.float16)
            cache.append(0, k, v)
            tokens.append((k, v))
            self.assertEqual(cache.get_seq_len(), step + 1)

        k_out, v_out = cache.get_kv(0)
        expected_k = torch.cat([t[0] for t in tokens], dim=2)
        expected_v = torch.cat([t[1] for t in tokens], dim=2)
        self.assertTrue(torch.equal(k_out, expected_k))
        self.assertTrue(torch.equal(v_out, expected_v))

    def test_multi_layer(self):
        cache = FP16KVCache(num_layers=3, device="cpu")
        for layer in range(3):
            k = torch.randn(1, self.H, 4, self.D, dtype=torch.float16)
            v = torch.randn(1, self.H, 4, self.D, dtype=torch.float16)
            cache.append(layer, k, v)
            k_out, v_out = cache.get_kv(layer)
            self.assertTrue(torch.equal(k, k_out))
            self.assertTrue(torch.equal(v, v_out))


class TestFP16KVCacheValidation(unittest.TestCase):
    """Input validation tests."""

    def test_invalid_num_layers(self):
        with self.assertRaises(ValueError):
            FP16KVCache(num_layers=0, device="cpu")
        with self.assertRaises(ValueError):
            FP16KVCache(num_layers=-1, device="cpu")

    def test_invalid_layer_id(self):
        cache = FP16KVCache(num_layers=2, device="cpu")
        k = torch.randn(1, 2, 1, 64, dtype=torch.float16)
        v = torch.randn(1, 2, 1, 64, dtype=torch.float16)
        with self.assertRaises(ValueError):
            cache.append(-1, k, v)
        with self.assertRaises(ValueError):
            cache.append(2, k, v)

    def test_empty_cache_get_raises(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        with self.assertRaises(ValueError):
            cache.get_kv(0)

    def test_shape_mismatch_raises(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        k = torch.randn(1, 2, 3, 64, dtype=torch.float16)
        v = torch.randn(1, 2, 3, 32, dtype=torch.float16)
        with self.assertRaises(ValueError):
            cache.append(0, k, v)

    def test_non_4d_raises(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        k = torch.randn(2, 3, 64, dtype=torch.float16)
        v = torch.randn(2, 3, 64, dtype=torch.float16)
        with self.assertRaises(ValueError):
            cache.append(0, k, v)


class TestFP16KVCacheCapacity(unittest.TestCase):
    """Capacity management tests."""

    def test_initial_min_capacity(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        k = torch.randn(1, 2, 10, 64, dtype=torch.float16)
        v = torch.randn(1, 2, 10, 64, dtype=torch.float16)
        cache.append(0, k, v)
        self.assertGreaterEqual(cache._layer_capacity[0], 256)

    def test_capacity_growth(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        B, H, D = 1, 2, 64
        k = torch.randn(B, H, 300, D, dtype=torch.float16)
        v = torch.randn(B, H, 300, D, dtype=torch.float16)
        cache.append(0, k, v)
        cap1 = cache._layer_capacity[0]

        k2 = torch.randn(B, H, cap1 + 1, D, dtype=torch.float16)
        v2 = torch.randn(B, H, cap1 + 1, D, dtype=torch.float16)
        cache.release()
        cache.append(0, k2, v2)
        cap2 = cache._layer_capacity[0]
        self.assertGreater(cap2, cap1)

    def test_max_seq_len_cap(self):
        cache = FP16KVCache(
            num_layers=1, device="cpu", max_seq_len=50
        )
        k = torch.randn(1, 2, 30, 64, dtype=torch.float16)
        v = torch.randn(1, 2, 30, 64, dtype=torch.float16)
        cache.append(0, k, v)

        k2 = torch.randn(1, 2, 21, 64, dtype=torch.float16)
        v2 = torch.randn(1, 2, 21, 64, dtype=torch.float16)
        with self.assertRaises(ValueError):
            cache.append(0, k2, v2)

    def test_invalid_max_seq_len(self):
        with self.assertRaises(ValueError):
            FP16KVCache(num_layers=1, device="cpu", max_seq_len=0)
        with self.assertRaises(ValueError):
            FP16KVCache(num_layers=1, device="cpu", max_seq_len=-5)


class TestFP16KVCacheMemory(unittest.TestCase):
    """Memory tracking and lifecycle tests."""

    def test_memory_positive(self):
        cache = FP16KVCache(num_layers=2, device="cpu")
        k = torch.randn(1, 4, 10, 128, dtype=torch.float16)
        v = torch.randn(1, 4, 10, 128, dtype=torch.float16)
        cache.append(0, k, v)
        cache.append(1, k, v)
        self.assertGreater(cache.get_memory_mb(), 0.0)

    def test_clear_preserves_buffers(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        k = torch.randn(1, 2, 5, 64, dtype=torch.float16)
        v = torch.randn(1, 2, 5, 64, dtype=torch.float16)
        cache.append(0, k, v)
        mem_before = cache.get_memory_mb()
        cache.clear()
        self.assertEqual(cache.get_seq_len(), 0)
        self.assertAlmostEqual(
            cache.get_memory_mb(), mem_before,
            msg="clear() should keep buffers allocated",
        )

    def test_release_frees_buffers(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        k = torch.randn(1, 2, 5, 64, dtype=torch.float16)
        v = torch.randn(1, 2, 5, 64, dtype=torch.float16)
        cache.append(0, k, v)
        cache.release()
        self.assertEqual(cache.get_seq_len(), 0)
        self.assertEqual(cache.get_memory_mb(), 0.0)

    def test_repr(self):
        cache = FP16KVCache(num_layers=2, device="cpu")
        r = repr(cache)
        self.assertIn("FP16KVCache", r)
        self.assertIn("num_layers=2", r)


class TestFP16KVCacheHFFormat(unittest.TestCase):
    """HuggingFace format conversion tests."""

    def test_to_tuple_roundtrip(self):
        cache = FP16KVCache(num_layers=2, device="cpu")
        B, H, S, D = 1, 4, 8, 64
        for layer in range(2):
            k = torch.randn(B, H, S, D, dtype=torch.float16)
            v = torch.randn(B, H, S, D, dtype=torch.float16)
            cache.append(layer, k, v)

        tup = cache.to_tuple()
        self.assertEqual(len(tup), 2)
        for k, v in tup:
            self.assertEqual(k.shape, (B, H, S, D))
            self.assertEqual(v.shape, (B, H, S, D))

    def test_from_tuple(self):
        B, H, S, D = 1, 4, 8, 64
        past = tuple(
            (
                torch.randn(B, H, S, D, dtype=torch.float16),
                torch.randn(B, H, S, D, dtype=torch.float16),
            )
            for _ in range(3)
        )
        cache = FP16KVCache.from_tuple(past, device="cpu")
        self.assertEqual(cache.num_layers, 3)
        self.assertEqual(cache.get_seq_len(), S)

        for layer in range(3):
            k_out, v_out = cache.get_kv(layer)
            self.assertTrue(torch.equal(k_out, past[layer][0]))
            self.assertTrue(torch.equal(v_out, past[layer][1]))

    def test_to_tuple_empty_raises(self):
        cache = FP16KVCache(num_layers=1, device="cpu")
        with self.assertRaises(ValueError):
            cache.to_tuple()


if __name__ == "__main__":
    unittest.main()
