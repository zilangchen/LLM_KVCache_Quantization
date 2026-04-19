#!/usr/bin/env python3
"""Tests for same-format allocator-enabled RoleAlign asymmetric KV cache."""

import sys
import unittest
from pathlib import Path

import torch

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cache.role_aware_allocator_cache import RoleAwareAllocatorKVCache


class TestRoleAwareAllocatorCache(unittest.TestCase):
    def _make_cache(self, **kwargs):
        defaults = dict(
            num_layers=4,
            device="cpu",
            dtype=torch.float32,
            per_layer_bits=[(4, 4), (8, 8), (8, 4), (4, 8)],
            k_percentile=99.9,
            v_percentile=99.9,
        )
        defaults.update(kwargs)
        return RoleAwareAllocatorKVCache(**defaults)

    def test_mixed_bit_pairs_round_trip_shapes(self):
        cache = self._make_cache()
        k = torch.randn(1, 2, 4, 8)
        v = torch.randn(1, 2, 4, 8)
        for layer_id in range(4):
            cache.append(layer_id, k, v)
            k_out, v_out = cache.get_kv(layer_id)
            self.assertEqual(k_out.shape, k.shape)
            self.assertEqual(v_out.shape, v.shape)

    def test_supports_fp16_passthrough_pair(self):
        cache = self._make_cache(num_layers=1, per_layer_bits=[(16, 16)])
        k = torch.randn(1, 2, 4, 8)
        v = torch.randn(1, 2, 4, 8)
        cache.append(0, k, v)
        k_out, v_out = cache.get_kv(0)
        self.assertTrue(torch.allclose(k_out, k, atol=0.0, rtol=0.0))
        self.assertTrue(torch.allclose(v_out, v, atol=0.0, rtol=0.0))

    def test_invalid_per_layer_bits_length_raises(self):
        with self.assertRaises(ValueError):
            self._make_cache(num_layers=2, per_layer_bits=[(4, 4)])

    def test_unsupported_pair_raises(self):
        with self.assertRaises(ValueError):
            self._make_cache(per_layer_bits=[(3, 4), (4, 4), (4, 4), (4, 4)])

    def test_framework_metadata(self):
        cache = self._make_cache(framework="ours_asym_allocator_ba")
        self.assertEqual(cache.framework, "ours_asym_allocator_ba")

    def test_residual_length_nonzero_rejected(self):
        with self.assertRaises(ValueError):
            self._make_cache(residual_length=16)
