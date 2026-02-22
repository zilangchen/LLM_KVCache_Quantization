"""Unit tests for statistical routines in scripts/aggregate_results.py."""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

import aggregate_results as agg  # noqa: E402


class TestAggregateResultsStats(unittest.TestCase):
    def test_exact_signflip_pvalue_known_case(self):
        diffs = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64)
        p_value, method, n_perm = agg._paired_signflip_pvalue(  # pylint: disable=protected-access
            diffs, n_permutations=5000, seed=1234
        )
        self.assertEqual(method, "exact_signflip")
        self.assertEqual(n_perm, 16)
        # Exact two-sided sign-flip p-value for n=4 all-positive diffs is 2/16.
        self.assertAlmostEqual(p_value, 0.125, places=12)

    def test_bootstrap_ci_contains_mean(self):
        values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        low, high = agg._bootstrap_ci_mean(  # pylint: disable=protected-access
            values, n_bootstrap=5000, ci_level=0.95, seed=42
        )
        mean = float(np.mean(values))
        self.assertLessEqual(low, mean)
        self.assertGreaterEqual(high, mean)
        self.assertLess(low, high)

    def test_bh_fdr_adjustment(self):
        df = pd.DataFrame({"p_value": [0.01, 0.04, 0.03, 0.20]})
        out = agg._add_bh_fdr_qvalues(df, p_col="p_value", q_col="q_value")  # pylint: disable=protected-access
        q = out["q_value"].to_numpy(dtype=np.float64)
        self.assertAlmostEqual(q[0], 0.04, places=12)
        self.assertAlmostEqual(q[1], 0.05333333333333334, places=12)
        self.assertAlmostEqual(q[2], 0.05333333333333334, places=12)
        self.assertAlmostEqual(q[3], 0.20, places=12)

    def test_significance_summary_with_paired_seeds(self):
        # Lower is better metric (e.g., TPOT): challenger beats baseline for all seeds.
        df = pd.DataFrame(
            [
                {"kv_mode": "int8_baseline", "seed": 1234, "seq_len": 4096, "tpot_ms": 10.0},
                {"kv_mode": "int8_ours", "seed": 1234, "seq_len": 4096, "tpot_ms": 8.0},
                {"kv_mode": "int8_baseline", "seed": 1235, "seq_len": 4096, "tpot_ms": 10.0},
                {"kv_mode": "int8_ours", "seed": 1235, "seq_len": 4096, "tpot_ms": 9.0},
                {"kv_mode": "int8_baseline", "seed": 1236, "seq_len": 4096, "tpot_ms": 10.0},
                {"kv_mode": "int8_ours", "seed": 1236, "seq_len": 4096, "tpot_ms": 9.0},
            ]
        )
        summary, paired = agg._significance_summary(  # pylint: disable=protected-access
            df,
            metric_col="tpot_ms",
            key_cols=["seq_len"],
            pairings=[("int8_baseline", "int8_ours")],
            metric_name="tpot_ms",
            higher_is_better=False,
            min_pairs=3,
            alpha=0.05,
            ci_level=0.95,
            n_bootstrap=3000,
            n_permutations=3000,
            random_seed=1234,
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(len(paired), 3)
        row = summary.iloc[0]
        self.assertEqual(row["n_pairs"], 3)
        self.assertEqual(row["n_unique_seeds"], 3)
        self.assertTrue(bool(row["meets_min_pairs"]))
        self.assertEqual(row["inference_status"], "ok")
        self.assertTrue(bool(row["favors_challenger"]))
        self.assertGreater(float(row["mean_favorable_diff"]), 0.0)
        self.assertGreaterEqual(float(row["probability_of_superiority"]), 0.99)

    def test_significance_summary_insufficient_pairs(self):
        df = pd.DataFrame(
            [
                {"kv_mode": "int8_baseline", "seed": 1234, "seq_len": 4096, "needle_pass_rate": 80.0},
                {"kv_mode": "int8_ours", "seed": 1234, "seq_len": 4096, "needle_pass_rate": 82.0},
            ]
        )
        summary, paired = agg._significance_summary(  # pylint: disable=protected-access
            df,
            metric_col="needle_pass_rate",
            key_cols=["seq_len"],
            pairings=[("int8_baseline", "int8_ours")],
            metric_name="needle_pass_rate",
            higher_is_better=True,
            min_pairs=3,
            alpha=0.05,
            ci_level=0.95,
            n_bootstrap=2000,
            n_permutations=2000,
            random_seed=1234,
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(len(paired), 1)
        row = summary.iloc[0]
        self.assertEqual(row["inference_status"], "insufficient_pairs_for_test")
        self.assertFalse(bool(row["meets_min_pairs"]))
        self.assertTrue(np.isnan(float(row["p_value"])))

    def test_execution_coverage_and_failure_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runs_dir = root / "runs"
            logs_dir = root / "logs"
            run_id = "int8_baseline_throughput_8k_b32_demo"
            run_dir = runs_dir / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "run_manifest.json").write_text(
                """
{
  "run_name": "int8_baseline_throughput_8k_b32",
  "run_tag": "demo",
  "tasks": {
    "profile_latency": {
      "status": "failed",
      "failure_type": "oom",
      "attempts": 1,
      "returncode": 73
    }
  }
}
""".strip(),
                encoding="utf-8",
            )
            log_path = logs_dir / run_id / "profile_latency.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("OOM\n", encoding="utf-8")

            coverage = agg._collect_execution_coverage(runs_dir, logs_dir)  # pylint: disable=protected-access
            self.assertEqual(len(coverage), 1)
            self.assertEqual(coverage.iloc[0]["execution_state"], "oom_failure")

            failures = agg._build_failure_registry(coverage)  # pylint: disable=protected-access
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures.iloc[0]["failure_category"], "oom")


if __name__ == "__main__":
    unittest.main()
