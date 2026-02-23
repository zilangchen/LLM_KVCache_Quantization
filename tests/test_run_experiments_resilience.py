"""Tests for resilience helpers in scripts/run_experiments.py."""

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

import run_experiments as rex  # noqa: E402


class TestRunExperimentsResilience(unittest.TestCase):
    def test_classify_failure_oom_by_returncode(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("", encoding="utf-8")
            kind = rex._classify_failure(log_path=log, returncode=73)  # pylint: disable=protected-access
            self.assertEqual(kind, "oom")

    def test_classify_failure_traceback_from_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "task.log"
            log.write_text("Traceback (most recent call last):\nValueError\n", encoding="utf-8")
            kind = rex._classify_failure(log_path=log, returncode=1)  # pylint: disable=protected-access
            self.assertEqual(kind, "traceback")

    def test_task_is_completed_successfully(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "profile_latency_demo.csv").write_text("x\n1\n", encoding="utf-8")
            manifest = {"tasks": {"profile_latency": {"status": "success"}}}
            ok = rex._task_is_completed_successfully(  # pylint: disable=protected-access
                manifest=manifest,
                run_dir=run_dir,
                task="profile_latency",
            )
            self.assertTrue(ok)

    def test_task_is_completed_successfully_for_legacy_skipped_status(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "profile_latency_demo.csv").write_text("x\n1\n", encoding="utf-8")
            manifest = {"tasks": {"profile_latency": {"status": "skipped"}}}
            ok = rex._task_is_completed_successfully(  # pylint: disable=protected-access
                manifest=manifest,
                run_dir=run_dir,
                task="profile_latency",
            )
            self.assertTrue(ok)

    def test_mark_task_success_clears_failure_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "run_manifest.json"
            log_path = root / "logs" / "profile_latency.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            manifest = {
                "tasks": {
                    "profile_latency": {
                        "status": "failed",
                        "failure_type": "oom",
                        "error": "failed once",
                    }
                }
            }

            rex._mark_task_status(  # pylint: disable=protected-access
                manifest_path,
                manifest,
                task="profile_latency",
                status="success",
                cmd=["python", "scripts/profile_latency.py"],
                log_path=log_path,
                returncode=0,
                attempt_idx=2,
            )

            updated = rex._read_json(manifest_path)  # pylint: disable=protected-access
            self.assertIsInstance(updated, dict)
            task = updated["tasks"]["profile_latency"]
            self.assertEqual(task.get("status"), "success")
            self.assertNotIn("failure_type", task)
            self.assertNotIn("error", task)

    def test_mark_task_success_without_history_for_skip_resume(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "run_manifest.json"
            log_path = root / "logs" / "profile_latency.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            manifest = {
                "tasks": {
                    "profile_latency": {
                        "status": "success",
                        "history": [{"status": "success", "attempt": 1}],
                    }
                }
            }

            rex._mark_task_status(  # pylint: disable=protected-access
                manifest_path,
                manifest,
                task="profile_latency",
                status="success",
                cmd=["python", "scripts/profile_latency.py"],
                log_path=log_path,
                returncode=0,
                record_history=False,
            )

            updated = rex._read_json(manifest_path)  # pylint: disable=protected-access
            self.assertIsInstance(updated, dict)
            task = updated["tasks"]["profile_latency"]
            self.assertEqual(task.get("status"), "success")
            self.assertEqual(len(task.get("history", [])), 1)

    def test_init_manifest_append_history_records_kv_and_quant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "run_manifest.json"
            args = argparse.Namespace(tasks="eval_ppl", config="configs/exp_matrix.yaml")
            manifest = rex._init_manifest(  # pylint: disable=protected-access
                manifest_path=manifest_path,
                run_id="demo_rt",
                run_name="demo",
                run_tag="rt",
                kv_mode="kivi_style",
                seed=1234,
                replica_id=0,
                model_id="Qwen/Qwen2.5-1.5B-Instruct",
                model_revision=None,
                run_quant_bits=4,
                args=args,
                append_mode=True,
                git_commit_full="abcdef123456",
                env_info={"env_hash": "abc"},
            )
            self.assertIn("append_history", manifest)
            self.assertEqual(manifest["quant_bits"], 4)
            self.assertEqual(manifest["append_history"][-1]["kv_mode"], "kivi_style")

    def test_init_manifest_append_mismatch_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "run_manifest.json"
            args = argparse.Namespace(tasks="eval_ppl", config="configs/exp_matrix.yaml")
            rex._init_manifest(  # pylint: disable=protected-access
                manifest_path=manifest_path,
                run_id="demo_rt",
                run_name="demo",
                run_tag="rt",
                kv_mode="int8_ours",
                seed=1234,
                replica_id=0,
                model_id="Qwen/Qwen2.5-1.5B-Instruct",
                model_revision=None,
                run_quant_bits=8,
                args=args,
                append_mode=False,
                git_commit_full="abcdef123456",
                env_info={"env_hash": "abc"},
            )
            with self.assertRaises(ValueError):
                rex._init_manifest(  # pylint: disable=protected-access
                    manifest_path=manifest_path,
                    run_id="demo_rt",
                    run_name="demo",
                    run_tag="rt",
                    kv_mode="kivi_style",
                    seed=1234,
                    replica_id=0,
                    model_id="Qwen/Qwen2.5-1.5B-Instruct",
                    model_revision=None,
                    run_quant_bits=8,
                    args=args,
                    append_mode=True,
                    git_commit_full="abcdef123456",
                    env_info={"env_hash": "abc"},
                )

    def test_ruler_peak_gen_tokens_defaults_include_cwe_floor(self):
        peak = rex._ruler_peak_gen_tokens_for_gate(  # pylint: disable=protected-access
            ruler_tasks_arg=None,
            ruler_max_new_tokens=32,
        )
        self.assertEqual(peak, 128)

    def test_ruler_peak_gen_tokens_respects_explicit_tasks(self):
        peak = rex._ruler_peak_gen_tokens_for_gate(  # pylint: disable=protected-access
            ruler_tasks_arg="s_niah,mk_niah,vt",
            ruler_max_new_tokens=32,
        )
        self.assertEqual(peak, 32)

    def test_ruler_peak_gen_tokens_uses_runtime_max_new_tokens(self):
        peak = rex._ruler_peak_gen_tokens_for_gate(  # pylint: disable=protected-access
            ruler_tasks_arg="cwe",
            ruler_max_new_tokens=256,
        )
        self.assertEqual(peak, 256)

    def test_compute_ruler_truncation_warning_for_long_case(self):
        warning = rex._compute_ruler_truncation_warning(  # pylint: disable=protected-access
            run_name="int4_baseline_long",
            seq_len=32704,
            gen_len=64,
            max_position_embeddings=32768,
            ruler_context_len=32704,
            ruler_max_new_tokens=32,
            ruler_tasks_arg=None,
        )
        self.assertIsInstance(warning, str)
        self.assertIn("safe_prompt_budget=32640", warning)
        self.assertIn("int4_baseline_long", warning)

    def test_compute_ruler_truncation_warning_none_when_safe(self):
        warning = rex._compute_ruler_truncation_warning(  # pylint: disable=protected-access
            run_name="int8_ours_curve_8k",
            seq_len=8192,
            gen_len=64,
            max_position_embeddings=32768,
            ruler_context_len=8192,
            ruler_max_new_tokens=32,
            ruler_tasks_arg="s_niah,mk_niah,vt",
        )
        self.assertIsNone(warning)


if __name__ == "__main__":
    unittest.main()
