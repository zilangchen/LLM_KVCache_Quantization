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


if __name__ == "__main__":
    unittest.main()
