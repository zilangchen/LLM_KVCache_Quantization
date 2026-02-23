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
        # With Phipson-Smyth +1 correction: p = (exceed + 1) / (n_enum + 1).
        # For n=4 all-positive diffs: only sign=(+1,+1,+1,+1) yields |mean|>=|observed|,
        # so exceed=1 (the observed itself), p = (1+1)/(16+1) = 2/17.
        self.assertAlmostEqual(p_value, 2.0 / 17.0, places=12)

    def test_exact_signflip_pvalue_mixed_signs(self):
        diffs = np.array([3.0, 2.0, -1.0, 0.5], dtype=np.float64)
        p_value, method, n_perm = agg._paired_signflip_pvalue(  # pylint: disable=protected-access
            diffs, n_permutations=5000, seed=1234
        )
        self.assertEqual(method, "exact_signflip")
        self.assertEqual(n_perm, 16)

        observed = abs(float(np.mean(diffs)))
        n = len(diffs)
        idx = np.arange(1 << n, dtype=np.uint32)[:, None]
        bits = ((idx >> np.arange(n, dtype=np.uint32)) & 1).astype(np.int8)
        signs = bits * 2 - 1
        perm_means = np.abs((signs * diffs[None, :]).mean(axis=1))
        # Phipson-Smyth +1 correction: p = (exceed + 1) / (n_enum + 1)
        exceed = int(np.sum(perm_means >= (observed - 1e-12)))
        n_enum = len(perm_means)
        expected_p = float((exceed + 1) / (n_enum + 1))
        self.assertAlmostEqual(p_value, expected_p, places=12)

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

    def test_main_claims_table_includes_external_validity_metrics(self):
        latency_summary = pd.DataFrame(
            [
                {
                    "kv_mode": "int8_ours",
                    "seq_len": 32704,
                    "batch": 1,
                    "gen_len": 64,
                    "tpot_ms_mean": 4.5,
                    "ttft_ms_mean": 12.0,
                    "tok_per_s_mean": 220.0,
                }
            ]
        )
        memory_summary = pd.DataFrame(
            [
                {
                    "kv_mode": "int8_ours",
                    "seq_len": 32704,
                    "batch": 1,
                    "gen_len": 64,
                    "gpu_mem_peak_mb_mean": 8120.0,
                    "kv_cache_mem_mb_mean": 1530.0,
                }
            ]
        )
        needle_summary = pd.DataFrame(
            [
                {
                    "kv_mode": "int8_ours",
                    "seq_len": 32704,
                    "needle_pass_rate_mean": 92.0,
                    "needle_exact_match_rate_mean": 91.0,
                }
            ]
        )
        ppl_summary = pd.DataFrame(
            [
                {
                    "kv_mode": "int8_ours",
                    "ppl_mode": "kv_cache",
                    "tokens_evaluated_mean": 1000000,
                    "perplexity_mean": 8.12,
                }
            ]
        )
        longbench_summary = pd.DataFrame(
            [
                {
                    "kv_mode": "int8_ours",
                    "seq_len": 32704,
                    "longbench_score_mean": 88.5,
                }
            ]
        )
        ruler_summary = pd.DataFrame(
            [
                {
                    "kv_mode": "int8_ours",
                    "seq_len": 32704,
                    "ruler_pass_rate_mean": 90.4,
                }
            ]
        )

        out = agg._main_claims_32k_table(  # pylint: disable=protected-access
            latency_summary=latency_summary,
            memory_summary=memory_summary,
            needle_summary=needle_summary,
            ppl_summary=ppl_summary,
            longbench_summary=longbench_summary,
            ruler_summary=ruler_summary,
            target_seq_len=32704,
        )
        self.assertEqual(len(out), 1)
        row = out.iloc[0]
        self.assertAlmostEqual(float(row["longbench_score_mean"]), 88.5, places=6)
        self.assertAlmostEqual(float(row["ruler_pass_rate_mean"]), 90.4, places=6)

    def test_export_per_model_layered_tables(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tables_dir = root / "tables"
            tables_dir.mkdir(parents=True, exist_ok=True)
            source = pd.DataFrame(
                [
                    {
                        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                        "kv_mode": "int8_ours",
                        "seq_len": 4096,
                        "needle_pass_rate_mean": 91.2,
                    },
                    {
                        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
                        "kv_mode": "int8_ours",
                        "seq_len": 4096,
                        "needle_pass_rate_mean": 92.6,
                    },
                ]
            )
            source.to_csv(tables_dir / "needle_summary.csv", index=False)

            manifest = agg._export_per_model_layered_tables(tables_dir)  # pylint: disable=protected-access
            self.assertEqual(len(manifest), 2)
            self.assertTrue(
                (tables_dir / "per_model" / "Qwen__Qwen2.5-1.5B-Instruct" / "needle_summary.csv").exists()
            )
            self.assertTrue(
                (tables_dir / "per_model" / "meta-llama__Llama-3.1-8B-Instruct" / "needle_summary.csv").exists()
            )


if __name__ == "__main__":
    unittest.main()
