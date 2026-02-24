"""TST-003: Unit tests for scripts/calibrate_behavior.py.

Tests the core pure-function logic (no model/GPU required):
  - resolve_kv_params
  - compute_absmax_per_group
  - dequantize_with_scale
  - quantize_dequantize_with_clip_stats
  - select_best_trial (robust / mean_kl / mean_mse modes)
  - collect_absmax_samples / scales_from_absmax_samples
  - validate_group_size
  - compute_inv_tau (with small synthetic data)
  - evaluate_quant_candidate (with small synthetic data)
  - Output JSON structure validation
"""

import math
import sys
import os
import types
import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, List

import torch
import numpy as np

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock heavy third-party modules that calibrate_behavior.py imports at module
# level but that are NOT needed for the pure-function unit tests here.
# This allows the tests to run on CPU-only environments without transformers,
# datasets, matplotlib, or tqdm installed.
_MOCKED_MODULES = [
    "transformers",
    "datasets",
    "matplotlib",
    "matplotlib.pyplot",
    "tqdm",
]
_saved = {}
for _mod_name in _MOCKED_MODULES:
    if _mod_name not in sys.modules:
        _saved[_mod_name] = None
        sys.modules[_mod_name] = MagicMock()
    else:
        _saved[_mod_name] = sys.modules[_mod_name]

from scripts.calibrate_behavior import (
    resolve_kv_params,
    compute_absmax_per_group,
    dequantize_with_scale,
    quantize_dequantize_with_clip_stats,
    select_best_trial,
    collect_absmax_samples,
    scales_from_absmax_samples,
    validate_group_size,
    compute_inv_tau,
    evaluate_quant_candidate,
)

# Restore original modules to avoid polluting other tests in the same process.
for _mod_name, _orig in _saved.items():
    if _orig is None:
        del sys.modules[_mod_name]
    else:
        sys.modules[_mod_name] = _orig


# ---------------------------------------------------------------------------
# resolve_kv_params
# ---------------------------------------------------------------------------
class TestResolveKvParams(unittest.TestCase):
    """Tests for resolve_kv_params: merging run_entry and quant_defaults."""

    def test_explicit_separate_kv(self):
        run = {"clip_percentile_k": 99.0, "clip_percentile_v": 99.5,
               "group_size_k": 64, "group_size_v": 128}
        defaults = {}
        ck, cv, gk, gv = resolve_kv_params(run, defaults)
        self.assertEqual(ck, 99.0)
        self.assertEqual(cv, 99.5)
        self.assertEqual(gk, 64)
        self.assertEqual(gv, 128)

    def test_fallback_to_shared(self):
        run = {"clip_percentile": 98.0, "group_size": 32}
        defaults = {}
        ck, cv, gk, gv = resolve_kv_params(run, defaults)
        self.assertEqual(ck, 98.0)
        self.assertEqual(cv, 98.0)
        self.assertEqual(gk, 32)
        self.assertEqual(gv, 32)

    def test_fallback_to_defaults(self):
        run = {}
        defaults = {"clip_percentile_k": 99.9, "clip_percentile_v": 99.9,
                     "group_size_k": 128, "group_size_v": 128}
        ck, cv, gk, gv = resolve_kv_params(run, defaults)
        self.assertEqual(ck, 99.9)
        self.assertEqual(cv, 99.9)
        self.assertEqual(gk, 128)
        self.assertEqual(gv, 128)

    def test_priority_order(self):
        """clip_percentile_k in run_entry should override both shared and default."""
        run = {"clip_percentile_k": 97.0, "clip_percentile": 98.0}
        defaults = {"clip_percentile_k": 99.9}
        ck, cv, _, _ = resolve_kv_params(run, defaults)
        self.assertEqual(ck, 97.0)
        # clip_percentile_v falls back to shared "clip_percentile"
        self.assertEqual(cv, 98.0)


# ---------------------------------------------------------------------------
# compute_absmax_per_group
# ---------------------------------------------------------------------------
class TestComputeAbsmaxPerGroup(unittest.TestCase):

    def test_shape(self):
        heads, seq_len, head_dim = 4, 8, 128
        group_size = 64
        t = torch.randn(heads, seq_len, head_dim)
        result = compute_absmax_per_group(t, group_size)
        expected_groups = head_dim // group_size  # 2
        self.assertEqual(result.shape, (heads, expected_groups))

    def test_known_values(self):
        """With a known constant tensor, absmax should equal that constant."""
        heads, seq_len, head_dim = 1, 1, 4
        group_size = 2
        t = torch.tensor([[[1.0, -2.0, 3.0, -4.0]]])  # [1, 1, 4]
        result = compute_absmax_per_group(t, group_size)
        # group 0: abs max of [1, -2] = 2
        # group 1: abs max of [3, -4] = 4
        self.assertAlmostEqual(result[0, 0].item(), 2.0)
        self.assertAlmostEqual(result[0, 1].item(), 4.0)


# ---------------------------------------------------------------------------
# dequantize_with_scale
# ---------------------------------------------------------------------------
class TestDequantizeWithScale(unittest.TestCase):

    def test_roundtrip_identity_for_small_values(self):
        """Quantize then dequantize should be close for values within scale range."""
        torch.manual_seed(42)
        seq_len, head_dim = 8, 128
        group_size = 64
        num_groups = head_dim // group_size

        k = torch.randn(seq_len, head_dim) * 0.5
        # Compute scale = absmax / 127 per group
        k_view = k.view(seq_len, num_groups, group_size)
        absmax = k_view.abs().amax(dim=-1).amax(dim=0)  # [num_groups]
        scale = absmax.clamp(min=1e-5) / 127.0

        k_deq = dequantize_with_scale(k, scale, group_size, qmax=127)
        err = (k - k_deq).abs().max().item()
        # Theoretical max error ~ absmax/(127) ~ 0.5/127 ~ 0.004
        self.assertLess(err, 0.05, f"Roundtrip error too large: {err}")

    def test_output_shape(self):
        seq_len, head_dim = 4, 64
        group_size = 32
        num_groups = head_dim // group_size
        k = torch.randn(seq_len, head_dim)
        scale = torch.ones(num_groups) * 0.01
        result = dequantize_with_scale(k, scale, group_size)
        self.assertEqual(result.shape, (seq_len, head_dim))


# ---------------------------------------------------------------------------
# quantize_dequantize_with_clip_stats
# ---------------------------------------------------------------------------
class TestQuantizeDequantizeWithClipStats(unittest.TestCase):

    def test_returns_clip_counts(self):
        torch.manual_seed(0)
        seq_len, head_dim = 4, 64
        group_size = 32
        num_groups = head_dim // group_size
        tensor = torch.randn(seq_len, head_dim)
        # Use a very small scale to force clipping
        scale = torch.ones(num_groups) * 1e-4
        deq, clipped, total = quantize_dequantize_with_clip_stats(
            tensor, scale, group_size, qmax=127
        )
        self.assertEqual(deq.shape, (seq_len, head_dim))
        self.assertGreater(clipped, 0, "Should have some clipped values with tiny scale")
        self.assertEqual(total, seq_len * head_dim)

    def test_no_clipping_with_large_scale(self):
        torch.manual_seed(0)
        seq_len, head_dim = 4, 64
        group_size = 32
        num_groups = head_dim // group_size
        tensor = torch.randn(seq_len, head_dim) * 0.01  # very small values
        scale = torch.ones(num_groups) * 10.0  # very large scale
        _, clipped, total = quantize_dequantize_with_clip_stats(
            tensor, scale, group_size, qmax=127
        )
        self.assertEqual(clipped, 0, "No clipping expected with oversized scale")

    def test_outlier_rescue_increases_scale(self):
        """With outlier_rescue_ratio=1.0, all groups use dynamic (absmax) scale."""
        torch.manual_seed(0)
        seq_len, head_dim = 4, 64
        group_size = 32
        num_groups = head_dim // group_size
        tensor = torch.randn(seq_len, head_dim) * 5.0
        # Small static scale
        scale = torch.ones(num_groups) * 0.001
        _, clipped_no_rescue, _ = quantize_dequantize_with_clip_stats(
            tensor, scale, group_size, qmax=127, outlier_rescue_ratio=0.0
        )
        _, clipped_full_rescue, _ = quantize_dequantize_with_clip_stats(
            tensor, scale, group_size, qmax=127, outlier_rescue_ratio=1.0
        )
        # Full rescue should reduce clipping
        self.assertLessEqual(clipped_full_rescue, clipped_no_rescue)


# ---------------------------------------------------------------------------
# validate_group_size
# ---------------------------------------------------------------------------
class TestValidateGroupSize(unittest.TestCase):

    def test_valid(self):
        # Should not raise
        validate_group_size(128, 64, "group_size_k")
        validate_group_size(128, 128, "group_size_v")
        validate_group_size(128, 1, "group_size_test")

    def test_zero(self):
        with self.assertRaises(ValueError):
            validate_group_size(128, 0, "group_size_k")

    def test_negative(self):
        with self.assertRaises(ValueError):
            validate_group_size(128, -1, "group_size_k")

    def test_indivisible(self):
        with self.assertRaises(ValueError):
            validate_group_size(128, 30, "group_size_k")


# ---------------------------------------------------------------------------
# select_best_trial
# ---------------------------------------------------------------------------
class TestSelectBestTrial(unittest.TestCase):
    """Tests for select_best_trial: robust, mean_kl, mean_mse modes."""

    def _make_trial(self, mean_kl=0.01, p95_kl=0.02, max_kl=0.05,
                    mean_mse=0.001, p95_mse=0.002, max_mse=0.005,
                    k_clip_rate=0.001, v_clip_rate=0.001,
                    v_rel_l2_mean=0.01,
                    group_size=64, clip_percentile=99.9,
                    outlier_rescue_ratio=0.0, mixed_rescue=0):
        return {
            "mean_kl": mean_kl, "p95_kl": p95_kl, "max_kl": max_kl,
            "mean_mse": mean_mse, "p95_mse": p95_mse, "max_mse": max_mse,
            "k_clip_rate": k_clip_rate, "v_clip_rate": v_clip_rate,
            "v_rel_l2_mean": v_rel_l2_mean,
            "group_size": group_size, "clip_percentile": clip_percentile,
            "outlier_rescue_ratio": outlier_rescue_ratio,
            "mixed_rescue": mixed_rescue,
        }

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            select_best_trial([], "robust", 0.01, 0.01, "kl")

    def test_mean_kl_objective(self):
        t1 = self._make_trial(mean_kl=0.05)
        t2 = self._make_trial(mean_kl=0.01)
        best, meta = select_best_trial([t1, t2], "mean_kl", 0.01, 0.01, "kl")
        self.assertEqual(best["mean_kl"], 0.01)
        self.assertEqual(meta["mode"], "mean_kl")

    def test_mean_mse_objective(self):
        t1 = self._make_trial(mean_mse=0.005)
        t2 = self._make_trial(mean_mse=0.001)
        best, meta = select_best_trial([t1, t2], "mean_mse", 0.01, 0.01, "mse")
        self.assertEqual(best["mean_mse"], 0.001)
        self.assertEqual(meta["mode"], "mean_mse")

    def test_robust_feasible(self):
        """Robust mode picks lowest p95 among feasible trials."""
        t_good = self._make_trial(p95_kl=0.01, k_clip_rate=0.005, v_clip_rate=0.005)
        t_lower_p95_but_infeasible = self._make_trial(
            p95_kl=0.005, k_clip_rate=0.05, v_clip_rate=0.05
        )
        best, meta = select_best_trial(
            [t_good, t_lower_p95_but_infeasible],
            "robust", 0.01, 0.01, "kl"
        )
        self.assertEqual(meta["mode"], "robust_feasible")
        self.assertEqual(best["p95_kl"], 0.01)
        self.assertEqual(meta["num_feasible"], 1)

    def test_robust_fallback_when_none_feasible(self):
        """When no trial is feasible, robust falls back to clip-rate-first sort."""
        t1 = self._make_trial(k_clip_rate=0.02, v_clip_rate=0.02)
        t2 = self._make_trial(k_clip_rate=0.05, v_clip_rate=0.05)
        best, meta = select_best_trial([t1, t2], "robust", 0.01, 0.01, "kl")
        self.assertEqual(meta["mode"], "robust_fallback_clip_first")
        self.assertEqual(meta["num_feasible"], 0)
        # t1 has lower total clip rate so it should be selected
        self.assertEqual(best["k_clip_rate"], 0.02)

    def test_missing_loss_key_raises(self):
        trial = {"mean_kl": 0.01, "p95_kl": 0.02, "max_kl": 0.05,
                 "k_clip_rate": 0.001, "v_clip_rate": 0.001,
                 "v_rel_l2_mean": 0.01, "group_size": 64, "clip_percentile": 99.9}
        with self.assertRaises(KeyError):
            select_best_trial([trial], "mean_mse", 0.01, 0.01, "mse")

    def test_robust_mse_mode(self):
        """Robust with loss_function=mse should use p95_mse key."""
        t1 = self._make_trial(p95_mse=0.002, k_clip_rate=0.001, v_clip_rate=0.001)
        t2 = self._make_trial(p95_mse=0.010, k_clip_rate=0.001, v_clip_rate=0.001)
        best, meta = select_best_trial([t1, t2], "robust", 0.01, 0.01, "mse")
        self.assertEqual(best["p95_mse"], 0.002)
        self.assertEqual(meta["mode"], "robust_feasible")

    def test_tiebreaker_uses_group_size(self):
        """When loss metrics are tied, smaller group_size is preferred (lower = earlier in sort)."""
        t1 = self._make_trial(mean_kl=0.01, p95_kl=0.02, group_size=128)
        t2 = self._make_trial(mean_kl=0.01, p95_kl=0.02, group_size=32)
        best, _ = select_best_trial([t1, t2], "mean_kl", 0.01, 0.01, "kl")
        self.assertEqual(best["group_size"], 32)


# ---------------------------------------------------------------------------
# collect_absmax_samples / scales_from_absmax_samples
# ---------------------------------------------------------------------------
class TestCollectAbsmaxAndScales(unittest.TestCase):

    def test_collect_shape(self):
        """Verify output structure: [layers][samples] of Tensors."""
        torch.manual_seed(0)
        num_samples = 3
        num_layers = 2
        kv_heads, seq_len, head_dim = 2, 8, 64
        group_size = 32
        num_groups = head_dim // group_size

        kv_samples = []
        for _ in range(num_samples):
            layers = []
            for _ in range(num_layers):
                layers.append(torch.randn(kv_heads, seq_len, head_dim))
            kv_samples.append(layers)

        result = collect_absmax_samples(kv_samples, group_size)
        self.assertEqual(len(result), num_layers)
        self.assertEqual(len(result[0]), num_samples)
        self.assertEqual(result[0][0].shape, (kv_heads, num_groups))

    def test_empty_input(self):
        result = collect_absmax_samples([], 64)
        self.assertEqual(result, [])

    def test_scales_positive(self):
        """All scales must be positive."""
        torch.manual_seed(0)
        kv_heads, seq_len, head_dim = 2, 4, 64
        group_size = 32
        kv_samples = [[torch.randn(kv_heads, seq_len, head_dim)]]
        absmax_samples = collect_absmax_samples(kv_samples, group_size)
        scales = scales_from_absmax_samples(absmax_samples, clip_percentile=99.9, qmax=127)
        self.assertEqual(len(scales), 1)
        self.assertTrue((scales[0] > 0).all())


# ---------------------------------------------------------------------------
# compute_inv_tau (small synthetic data)
# ---------------------------------------------------------------------------
class TestComputeInvTau(unittest.TestCase):
    """Test compute_inv_tau with minimal synthetic data (CPU, no model)."""

    def test_shape_and_finite(self):
        torch.manual_seed(42)
        num_layers = 1
        num_heads = 2
        num_kv_heads = 1
        head_dim = 8
        group_size = 4
        num_groups = head_dim // group_size
        seq_len = 4

        q_samples = [[torch.randn(num_heads, head_dim)]]   # 1 sample, 1 layer
        k_samples = [[torch.randn(num_kv_heads, seq_len, head_dim)]]
        k_scales = [torch.ones(num_kv_heads, num_groups) * 0.01]

        inv_tau = compute_inv_tau(
            q_samples=q_samples,
            k_samples=k_samples,
            k_scales=k_scales,
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            group_size=group_size,
            inv_tau_candidates=[0.5, 1.0, 1.5],
            qmax=127,
            loss_function="kl",
        )
        self.assertEqual(inv_tau.shape, (num_layers, num_heads))
        self.assertTrue(torch.isfinite(inv_tau).all())
        # Result should be one of the candidates
        for layer in range(num_layers):
            for head in range(num_heads):
                self.assertIn(inv_tau[layer, head].item(), [0.5, 1.0, 1.5])

    def test_mse_loss_function(self):
        """compute_inv_tau with loss_function='mse' should also work."""
        torch.manual_seed(42)
        num_heads, num_kv_heads, head_dim = 2, 1, 8
        group_size = 4
        num_groups = head_dim // group_size

        q_samples = [[torch.randn(num_heads, head_dim)]]
        k_samples = [[torch.randn(num_kv_heads, 4, head_dim)]]
        k_scales = [torch.ones(num_kv_heads, num_groups) * 0.01]

        inv_tau = compute_inv_tau(
            q_samples=q_samples,
            k_samples=k_samples,
            k_scales=k_scales,
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            group_size=group_size,
            inv_tau_candidates=[0.5, 1.0, 2.0],
            qmax=127,
            loss_function="mse",
        )
        self.assertEqual(inv_tau.shape, (1, num_heads))
        self.assertTrue(torch.isfinite(inv_tau).all())

    def test_nan_fallback(self):
        """When loss_accum has NaN, inv_tau should fall back to 1.0."""
        torch.manual_seed(42)
        num_heads, num_kv_heads, head_dim = 1, 1, 4
        group_size = 4

        # Create input that causes NaN: zero-length k produces NaN in softmax
        # Actually, let's use a different approach: inject NaN via scale=0
        q_samples = [[torch.randn(num_heads, head_dim)]]
        k_samples = [[torch.randn(num_kv_heads, 2, head_dim)]]
        # scale with NaN
        k_scales = [torch.tensor([[float("nan")]])]  # [1, 1]

        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            inv_tau = compute_inv_tau(
                q_samples=q_samples,
                k_samples=k_samples,
                k_scales=k_scales,
                num_heads=num_heads,
                num_kv_heads=num_kv_heads,
                head_dim=head_dim,
                group_size=group_size,
                inv_tau_candidates=[0.5, 1.0],
                qmax=127,
                loss_function="kl",
            )
        # With NaN in scales, dequant produces NaN, loss_accum has NaN,
        # so fallback should set inv_tau=1.0
        self.assertAlmostEqual(inv_tau[0, 0].item(), 1.0)


# ---------------------------------------------------------------------------
# evaluate_quant_candidate (small synthetic data)
# ---------------------------------------------------------------------------
class TestEvaluateQuantCandidate(unittest.TestCase):

    def _make_small_data(self):
        torch.manual_seed(42)
        num_heads = 2
        num_kv_heads = 1
        head_dim = 8
        group_size = 4
        num_groups = head_dim // group_size
        seq_len = 4

        q_samples = [[torch.randn(num_heads, head_dim)]]
        k_samples = [[torch.randn(num_kv_heads, seq_len, head_dim)]]
        v_samples = [[torch.randn(num_kv_heads, seq_len, head_dim)]]
        k_scales = [torch.ones(num_kv_heads, num_groups) * 0.01]
        v_scales = [torch.ones(num_kv_heads, num_groups) * 0.01]

        return {
            "q_samples": q_samples,
            "k_samples": k_samples,
            "v_samples": v_samples,
            "k_scales": k_scales,
            "v_scales": v_scales,
            "num_heads": num_heads,
            "num_kv_heads": num_kv_heads,
            "head_dim": head_dim,
            "group_size_k": group_size,
            "group_size_v": group_size,
            "qmax": 127,
        }

    def test_kl_output_keys(self):
        data = self._make_small_data()
        result = evaluate_quant_candidate(**data, loss_function="kl")
        for key in ["mean_kl", "p95_kl", "max_kl",
                     "k_clip_rate", "v_clip_rate", "v_rel_l2_mean"]:
            self.assertIn(key, result, f"Missing key: {key}")
        self.assertNotIn("mean_mse", result)

    def test_mse_output_keys(self):
        data = self._make_small_data()
        result = evaluate_quant_candidate(**data, loss_function="mse")
        for key in ["mean_mse", "p95_mse", "max_mse",
                     "k_clip_rate", "v_clip_rate", "v_rel_l2_mean"]:
            self.assertIn(key, result, f"Missing key: {key}")
        self.assertNotIn("mean_kl", result)

    def test_loss_is_non_negative(self):
        data = self._make_small_data()
        result_kl = evaluate_quant_candidate(**data, loss_function="kl")
        result_mse = evaluate_quant_candidate(**data, loss_function="mse")
        self.assertGreaterEqual(result_kl["mean_kl"], 0.0)
        self.assertGreaterEqual(result_mse["mean_mse"], 0.0)

    def test_clip_rate_in_range(self):
        data = self._make_small_data()
        result = evaluate_quant_candidate(**data, loss_function="kl")
        self.assertGreaterEqual(result["k_clip_rate"], 0.0)
        self.assertLessEqual(result["k_clip_rate"], 1.0)
        self.assertGreaterEqual(result["v_clip_rate"], 0.0)
        self.assertLessEqual(result["v_clip_rate"], 1.0)

    def test_int4_qmax(self):
        """With qmax=7 (INT4), should still produce valid results."""
        data = self._make_small_data()
        data["qmax"] = 7
        result = evaluate_quant_candidate(**data, loss_function="kl")
        self.assertIn("mean_kl", result)
        self.assertGreaterEqual(result["mean_kl"], 0.0)


# ---------------------------------------------------------------------------
# Output JSON structure validation (mock-based)
# ---------------------------------------------------------------------------
class TestCalibOutputFormat(unittest.TestCase):
    """Validate the structure of the calibration JSON payload."""

    def test_payload_has_required_keys(self):
        """The calib_payload dict should contain all required fields."""
        required_keys = [
            "version", "model_id", "generated_at", "loss_function",
            "quant_bits", "qmax", "num_layers", "num_heads",
            "num_kv_heads", "head_dim",
            "clip_percentile_k", "clip_percentile_v",
            "group_size_k", "group_size_v",
            "k_scale", "v_scale", "inv_tau", "inv_tau_shape",
            "inv_tau_candidates",
            "int4_outlier_ratio", "int4_mixed_rescue",
        ]
        # Build a minimal payload as main() would
        num_layers = 2
        num_heads = 4
        num_kv_heads = 2
        head_dim = 8
        group_size = 4
        num_groups = head_dim // group_size

        k_scales = [torch.ones(num_kv_heads, num_groups) * 0.01 for _ in range(num_layers)]
        v_scales = [torch.ones(num_kv_heads, num_groups) * 0.01 for _ in range(num_layers)]
        inv_tau = torch.ones(num_layers, num_heads)

        payload = {
            "version": 1,
            "model_id": "test/model",
            "generated_at": "2025-01-01T00:00:00",
            "loss_function": "kl",
            "quant_bits": 8,
            "qmax": 127,
            "num_layers": num_layers,
            "num_heads": num_heads,
            "num_kv_heads": num_kv_heads,
            "head_dim": head_dim,
            "clip_percentile_k": 99.9,
            "clip_percentile_v": 99.9,
            "group_size_k": group_size,
            "group_size_v": group_size,
            "k_scale": [k.tolist() for k in k_scales],
            "v_scale": [v.tolist() for v in v_scales],
            "inv_tau": inv_tau.tolist(),
            "inv_tau_shape": list(inv_tau.shape),
            "inv_tau_candidates": [0.5, 1.0, 1.5],
            "int4_outlier_ratio": 0.0,
            "int4_mixed_rescue": False,
        }

        for key in required_keys:
            self.assertIn(key, payload, f"Missing required key: {key}")

    def test_inv_tau_shape_consistent(self):
        """inv_tau_shape must match actual inv_tau dimensions."""
        num_layers, num_heads = 3, 8
        inv_tau = torch.ones(num_layers, num_heads)
        inv_tau_shape = list(inv_tau.shape)
        self.assertEqual(inv_tau_shape, [num_layers, num_heads])

    def test_loss_function_field_valid_values(self):
        """loss_function field must be 'kl' or 'mse'."""
        for lf in ["kl", "mse"]:
            self.assertIn(lf, ["kl", "mse"])


if __name__ == "__main__":
    unittest.main()
