"""Tests for scripts/check_run_completeness.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "check_run_completeness.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestCheckRunCompleteness(unittest.TestCase):
    def test_required_success_and_stress_oom_are_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runs_dir = root / "runs"
            logs_dir = root / "logs"
            out_json = root / "report.json"
            run_tag = "rt1"

            req_id = f"req_a_{run_tag}"
            req_dir = runs_dir / req_id
            _write(req_dir / "profile_latency_ok.csv", "x\n1\n")
            _write(req_dir / "profile_memory_ok.csv", "x\n1\n")
            _write(
                req_dir / "run_manifest.json",
                json.dumps(
                    {
                        "run_name": "req_a",
                        "run_tag": run_tag,
                        "tasks": {
                            "profile_latency": {"status": "success", "attempts": 1},
                            "profile_memory": {"status": "success", "attempts": 1},
                        },
                    }
                ),
            )

            stress_id = f"stress_b32_{run_tag}"
            stress_dir = runs_dir / stress_id
            _write(
                stress_dir / "run_manifest.json",
                json.dumps(
                    {
                        "run_name": "stress_b32",
                        "run_tag": run_tag,
                        "tasks": {
                            "profile_latency": {"status": "failed", "failure_type": "oom"},
                            "profile_memory": {"status": "failed", "failure_type": "oom"},
                        },
                    }
                ),
            )
            _write(logs_dir / stress_id / "profile_latency.log", "OOM\n")
            _write(logs_dir / stress_id / "profile_memory.log", "OOM\n")

            cmd = [
                sys.executable,
                str(SCRIPT_PATH),
                "--runs_dir",
                str(runs_dir),
                "--logs_dir",
                str(logs_dir),
                "--run_tag",
                run_tag,
                "--tasks",
                "profile_latency,profile_memory",
                "--required_run_names",
                "req_a",
                "--stress_run_names",
                "stress_b32",
                "--out_json",
                str(out_json),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)
            report = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(report["required_complete"])
            self.assertTrue(report["stress_complete"])
            self.assertEqual(len(report["unexpected_failures"]), 0)

    def test_skipped_status_with_csv_is_treated_as_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runs_dir = root / "runs"
            logs_dir = root / "logs"
            out_json = root / "report.json"
            run_tag = "rt_skip"

            req_id = f"req_skip_{run_tag}"
            req_dir = runs_dir / req_id
            _write(req_dir / "profile_latency_ok.csv", "x\n1\n")
            _write(req_dir / "profile_memory_ok.csv", "x\n1\n")
            _write(
                req_dir / "run_manifest.json",
                json.dumps(
                    {
                        "run_name": "req_skip",
                        "run_tag": run_tag,
                        "tasks": {
                            "profile_latency": {"status": "skipped", "attempts": 1},
                            "profile_memory": {"status": "skipped", "attempts": 1},
                        },
                    }
                ),
            )
            _write(logs_dir / req_id / "profile_latency.log", "already complete\n")
            _write(logs_dir / req_id / "profile_memory.log", "already complete\n")

            cmd = [
                sys.executable,
                str(SCRIPT_PATH),
                "--runs_dir",
                str(runs_dir),
                "--logs_dir",
                str(logs_dir),
                "--run_tag",
                run_tag,
                "--tasks",
                "profile_latency,profile_memory",
                "--required_run_names",
                "req_skip",
                "--out_json",
                str(out_json),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)
            report = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(report["required_complete"])
            self.assertEqual(len(report["unexpected_failures"]), 0)

    def test_unexpected_failure_returns_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runs_dir = root / "runs"
            logs_dir = root / "logs"
            out_json = root / "report.json"
            run_tag = "rt2"

            req_id = f"req_bad_{run_tag}"
            req_dir = runs_dir / req_id
            _write(
                req_dir / "run_manifest.json",
                json.dumps(
                    {
                        "run_name": "req_bad",
                        "run_tag": run_tag,
                        "tasks": {
                            "profile_latency": {"status": "failed", "failure_type": "runtime_error"},
                        },
                    }
                ),
            )
            _write(
                logs_dir / req_id / "profile_latency.log",
                "Traceback (most recent call last):\nValueError: bad\n",
            )

            cmd = [
                sys.executable,
                str(SCRIPT_PATH),
                "--runs_dir",
                str(runs_dir),
                "--logs_dir",
                str(logs_dir),
                "--run_tag",
                run_tag,
                "--tasks",
                "profile_latency",
                "--required_run_names",
                "req_bad",
                "--out_json",
                str(out_json),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, msg=result.stdout + "\n" + result.stderr)
            report = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertGreater(len(report["unexpected_failures"]), 0)


if __name__ == "__main__":
    unittest.main()
