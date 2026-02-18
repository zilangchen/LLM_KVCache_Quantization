import unittest

import torch

from src.cache.int4_cache import INT4KVCache
from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    pack_int4,
    quantize_symmetric_int4,
    unpack_int4,
)


class TestInt4Basic(unittest.TestCase):
    def test_pack_unpack_roundtrip(self):
        torch.manual_seed(0)
        x = torch.randint(-7, 8, (2, 3, 4, 128), dtype=torch.int8)
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
        self.assertEqual(scale.dtype, torch.float16)
        self.assertEqual(scale.shape, (B, H, S, D // group_size))

        y = dequantize_symmetric_int4(q, scale)
        self.assertEqual(y.shape, x.shape)
        self.assertEqual(y.dtype, torch.float16)
        self.assertTrue(torch.isfinite(y).all().item())


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


if __name__ == "__main__":
    unittest.main()

