#!/usr/bin/env python3
"""TST-078: Tests for RoleAwareAsymKVCache — thesis core claim dependency."""

import sys
import unittest
from unittest.mock import MagicMock

# Lightweight import — avoid GPU dependency
try:
    import torch
    from src.cache.role_aware_asym_cache import RoleAwareAsymKVCache
    _SKIP = False
except ImportError:
    _SKIP = True


@unittest.skipIf(_SKIP, "torch or src.cache not importable")
class TestRoleAwareAsymCacheMetadata(unittest.TestCase):
    """Test framework metadata and ba_calibrated flag."""

    def test_default_framework_is_ours_asym(self):
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu")
        self.assertEqual(cache.framework, "ours_asym")

    def test_custom_framework(self):
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu", framework="ours_asym_ba")
        self.assertEqual(cache.framework, "ours_asym_ba")

    def test_ba_calibrated_false_when_default_percentiles(self):
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu",
                                      k_percentile=100.0, v_percentile=100.0)
        self.assertFalse(cache.ba_calibrated)

    def test_ba_calibrated_true_when_k_percentile_differs(self):
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu",
                                      k_percentile=99.9, v_percentile=100.0)
        self.assertTrue(cache.ba_calibrated)

    def test_ba_calibrated_true_when_v_percentile_differs(self):
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu",
                                      k_percentile=100.0, v_percentile=99.5)
        self.assertTrue(cache.ba_calibrated)

    def test_ba_calibrated_true_when_both_differ(self):
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu",
                                      k_percentile=99.9, v_percentile=99.5)
        self.assertTrue(cache.ba_calibrated)

    def test_inherits_kivi_style(self):
        from src.cache.kivi_style_cache import KIVIStyleKVCache
        cache = RoleAwareAsymKVCache(num_layers=2, device="cpu")
        self.assertIsInstance(cache, KIVIStyleKVCache)


@unittest.skipIf(_SKIP, "torch or src.cache not importable")
class TestRoleAwareAsymCacheRoundTrip(unittest.TestCase):
    """Test append→get_kv round-trip on CPU."""

    def test_append_and_get_kv(self):
        cache = RoleAwareAsymKVCache(
            num_layers=2, device="cpu", quant_bits=4,
            k_percentile=99.9, v_percentile=99.9,
        )
        # Simulate prefill: [B=1, H=2, S=4, D=8]
        k = torch.randn(1, 2, 4, 8)
        v = torch.randn(1, 2, 4, 8)
        cache.append(0, k, v)

        k_out, v_out = cache.get_kv(0)
        self.assertEqual(k_out.shape, (1, 2, 4, 8))
        self.assertEqual(v_out.shape, (1, 2, 4, 8))
        self.assertEqual(cache.get_seq_len(), 4)


if __name__ == "__main__":
    unittest.main()
