"""Unit tests for scripts/generate_thesis_report.py."""

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_thesis_report as gtr  # noqa: E402


class TestGenerateThesisReport(unittest.TestCase):
    def test_claim_validation_pass_with_significance(self):
        rel = pd.DataFrame(
            [
                {
                    "metric": "tpot_ms",
                    "baseline_mode": "int8_baseline",
                    "challenger_mode": "int8_ours",
                    "seq_len": 32704,
                    "gen_len": 64,
                    "batch": 1,
                    "gain_pct": 12.5,
                }
            ]
        )
        sig = pd.DataFrame(
            [
                {
                    "metric": "tpot_ms",
                    "baseline_mode": "int8_baseline",
                    "challenger_mode": "int8_ours",
                    "seq_len": 32704,
                    "gen_len": 64,
                    "batch": 1,
                    "n_pairs": 3,
                    "meets_min_pairs": True,
                    "q_value": 0.02,
                    "p_value": 0.01,
                    "significant_q_alpha": True,
                    "favors_challenger": True,
                }
            ]
        )
        claims = [
            gtr.ClaimSpec(
                claim_id="C1",
                title="TPOT claim",
                metric="tpot_ms",
                baseline_mode="int8_baseline",
                challenger_mode="int8_ours",
                min_gain_pct=5.0,
                require_q_significance=True,
                target_seq_len=32704,
                target_gen_len=64,
                target_batch=1,
            )
        ]
        out = gtr.build_claim_validation(
            relative_gain=rel,
            significance=sig,
            claims=claims,
            alpha=0.05,
        )
        self.assertEqual(len(out), 1)
        row = out.iloc[0]
        self.assertEqual(row["status"], "PASS")
        self.assertTrue(bool(row["practical_pass"]))
        self.assertTrue(bool(row["statistical_pass"]))
        self.assertEqual(row["evidence_strength"], "strong")

    def test_claim_validation_inconclusive_when_significance_missing(self):
        rel = pd.DataFrame(
            [
                {
                    "metric": "tpot_ms",
                    "baseline_mode": "int8_baseline",
                    "challenger_mode": "int8_ours",
                    "seq_len": 32704,
                    "gen_len": 64,
                    "batch": 1,
                    "gain_pct": 10.0,
                }
            ]
        )
        sig = pd.DataFrame()
        claims = [
            gtr.ClaimSpec(
                claim_id="C1",
                title="TPOT claim",
                metric="tpot_ms",
                baseline_mode="int8_baseline",
                challenger_mode="int8_ours",
                min_gain_pct=5.0,
                require_q_significance=True,
                target_seq_len=32704,
                target_gen_len=64,
                target_batch=1,
            )
        ]
        out = gtr.build_claim_validation(
            relative_gain=rel,
            significance=sig,
            claims=claims,
            alpha=0.05,
        )
        self.assertEqual(len(out), 1)
        row = out.iloc[0]
        self.assertEqual(row["status"], "INCONCLUSIVE")
        self.assertFalse(bool(row["statistical_pass"]))

    def test_statistical_decision_labels(self):
        sig = pd.DataFrame(
            [
                {
                    "metric": "tpot_ms",
                    "baseline_mode": "int8_baseline",
                    "challenger_mode": "int8_ours",
                    "gain_pct_mean": 8.0,
                    "meets_min_pairs": True,
                    "significant_q_alpha": True,
                    "favors_challenger": True,
                    "q_value": 0.01,
                    "n_pairs": 3,
                },
                {
                    "metric": "perplexity",
                    "baseline_mode": "int8_baseline",
                    "challenger_mode": "int8_ours",
                    "gain_pct_mean": -3.0,
                    "meets_min_pairs": True,
                    "significant_q_alpha": True,
                    "favors_challenger": False,
                    "q_value": 0.01,
                    "n_pairs": 3,
                },
                {
                    "metric": "needle_pass_rate",
                    "baseline_mode": "int8_baseline",
                    "challenger_mode": "int8_ours",
                    "gain_pct_mean": 0.0,
                    "meets_min_pairs": False,
                    "significant_q_alpha": False,
                    "favors_challenger": False,
                    "q_value": 0.8,
                    "n_pairs": 1,
                },
            ]
        )
        out = gtr.build_statistical_decisions(
            significance=sig,
            practical_thresholds=gtr.DEFAULT_PRACTICAL_THRESHOLDS,
        )
        self.assertEqual(len(out), 3)
        by_metric = {row["metric"]: row for _, row in out.iterrows()}
        self.assertEqual(by_metric["tpot_ms"]["decision"], "robust_support")
        self.assertEqual(by_metric["perplexity"]["decision"], "significant_contradiction")
        self.assertEqual(by_metric["needle_pass_rate"]["decision"], "insufficient_pairs")

    def test_reproducibility_gate_flags_unexpected_failures(self):
        claim_validation = pd.DataFrame([{"claim_id": "C1", "status": "PASS"}])
        execution = pd.DataFrame(
            [
                {"execution_state": "success"},
                {"execution_state": "success"},
                {"execution_state": "oom_failure"},
            ]
        )
        failures = pd.DataFrame(
            [
                {
                    "run_name": "int8_baseline_throughput_8k_b32",
                    "failure_category": "oom",
                    "is_throughput_run": True,
                },
                {
                    "run_name": "int8_ours_curve_16k",
                    "failure_category": "traceback",
                    "is_throughput_run": False,
                },
            ]
        )
        gate = gtr.build_reproducibility_gate(
            claim_validation=claim_validation,
            execution_coverage=execution,
            failure_registry=failures,
        )
        self.assertEqual(len(gate), 4)
        g3 = gate[gate["gate_id"] == "G3"].iloc[0]
        self.assertEqual(g3["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
