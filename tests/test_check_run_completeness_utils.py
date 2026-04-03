"""Tests for utility functions in scripts/check_run_completeness.py (TST-032).

Covers:
  - _split_csv: CSV splitting with various edge cases
  - _is_oom_from_log: OOM detection from log content
  - _is_traceback_from_log: Python traceback detection
  - _expected_run_ids: run ID generation from names/tags/seeds
  - _detect_failure_type: failure classification
  - _csv_status / _csv_has_rows: CSV file status checks
  - _validate_csv_content: CSV content validation
"""

import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_run_completeness as crc  # noqa: E402


# ---------------------------------------------------------------------------
# Test: _split_csv
# ---------------------------------------------------------------------------

class TestSplitCsv(unittest.TestCase):
    """Test _split_csv() splits comma-separated strings correctly."""

    def test_split_csv_basic(self):
        result = crc._split_csv("a,b,c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_split_csv_with_spaces(self):
        result = crc._split_csv(" a , b , c ")
        self.assertEqual(result, ["a", "b", "c"])

    def test_split_csv_none_returns_empty(self):
        result = crc._split_csv(None)
        self.assertEqual(result, [])

    def test_split_csv_empty_string_returns_empty(self):
        result = crc._split_csv("")
        self.assertEqual(result, [])

    def test_split_csv_single_value(self):
        result = crc._split_csv("only_one")
        self.assertEqual(result, ["only_one"])

    def test_split_csv_trailing_comma(self):
        result = crc._split_csv("a,b,")
        self.assertEqual(result, ["a", "b"])

    def test_split_csv_leading_comma(self):
        result = crc._split_csv(",a,b")
        self.assertEqual(result, ["a", "b"])

    def test_split_csv_empty_between_commas(self):
        result = crc._split_csv("a,,b")
        self.assertEqual(result, ["a", "b"])


# ---------------------------------------------------------------------------
# Test: _is_oom_from_log
# ---------------------------------------------------------------------------

class TestIsOomFromLog(unittest.TestCase):
    """Test _is_oom_from_log() OOM pattern detection."""

    def test_oom_keyword_lowercase(self):
        self.assertTrue(crc._is_oom_from_log("Process failed with oom error"))

    def test_oom_keyword_uppercase(self):
        self.assertTrue(crc._is_oom_from_log("Process failed with OOM error"))

    def test_out_of_memory_phrase(self):
        self.assertTrue(crc._is_oom_from_log("RuntimeError: out of memory"))

    def test_cuda_out_of_memory(self):
        self.assertTrue(crc._is_oom_from_log("CUDA out of memory. Tried to allocate 2.00 GiB"))

    def test_cuda_out_of_memory_mixed_case(self):
        self.assertTrue(crc._is_oom_from_log("cuda Out Of Memory"))

    def test_no_oom_in_normal_log(self):
        self.assertFalse(crc._is_oom_from_log("Training completed successfully"))

    def test_no_oom_empty_content(self):
        self.assertFalse(crc._is_oom_from_log(""))

    def test_oom_word_boundary_avoids_room(self):
        """'room' should NOT trigger OOM detection due to word boundary."""
        self.assertFalse(crc._is_oom_from_log("There is room for improvement"))

    def test_oom_word_boundary_avoids_bloom(self):
        """'bloom' should NOT trigger OOM detection due to word boundary."""
        self.assertFalse(crc._is_oom_from_log("Using bloom filter for dedup"))


# ---------------------------------------------------------------------------
# Test: _is_traceback_from_log
# ---------------------------------------------------------------------------

class TestIsTracebackFromLog(unittest.TestCase):
    """Test _is_traceback_from_log() traceback detection."""

    def test_standard_traceback(self):
        content = "Traceback (most recent call last):\n  File \"test.py\"\nValueError"
        self.assertTrue(crc._is_traceback_from_log(content))

    def test_traceback_case_insensitive(self):
        content = "traceback (most recent call last):\nsome error"
        self.assertTrue(crc._is_traceback_from_log(content))

    def test_no_traceback_in_clean_log(self):
        self.assertFalse(crc._is_traceback_from_log("Everything ran fine"))

    def test_no_traceback_empty(self):
        self.assertFalse(crc._is_traceback_from_log(""))

    def test_partial_traceback_text_does_not_match(self):
        """Just the word 'Traceback' without the full pattern should not match."""
        self.assertFalse(crc._is_traceback_from_log("Traceback information is available"))


# ---------------------------------------------------------------------------
# Test: _expected_run_ids
# ---------------------------------------------------------------------------

class TestExpectedRunIds(unittest.TestCase):
    """Test _expected_run_ids() generates correct run ID patterns."""

    def test_single_name_no_seeds(self):
        result = crc._expected_run_ids(
            run_names=["fp16_base"],
            run_tag="20260224",
            seeds=[],
        )
        self.assertEqual(result, {"fp16_base": ["fp16_base_20260224"]})

    def test_single_name_with_seeds(self):
        result = crc._expected_run_ids(
            run_names=["fp16_base"],
            run_tag="rt",
            seeds=[1234, 1235],
        )
        self.assertEqual(
            result,
            {"fp16_base": ["fp16_base_s1234_rt", "fp16_base_s1235_rt"]},
        )

    def test_multiple_names_no_seeds(self):
        result = crc._expected_run_ids(
            run_names=["a", "b"],
            run_tag="tag",
            seeds=[],
        )
        self.assertEqual(result, {"a": ["a_tag"], "b": ["b_tag"]})

    def test_multiple_names_with_seeds(self):
        result = crc._expected_run_ids(
            run_names=["x", "y"],
            run_tag="t",
            seeds=[42],
        )
        self.assertEqual(result, {"x": ["x_s42_t"], "y": ["y_s42_t"]})

    def test_empty_run_names(self):
        result = crc._expected_run_ids(
            run_names=[],
            run_tag="tag",
            seeds=[1234],
        )
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# Test: _detect_failure_type
# ---------------------------------------------------------------------------

class TestDetectFailureType(unittest.TestCase):
    """Test _detect_failure_type() classification logic."""

    def test_manifest_oom_takes_priority(self):
        result = crc._detect_failure_type(
            manifest_failure="oom",
            log_content="",
        )
        self.assertEqual(result, "oom")

    def test_log_oom_detected(self):
        result = crc._detect_failure_type(
            manifest_failure="",
            log_content="CUDA out of memory trying to allocate",
        )
        self.assertEqual(result, "oom")

    def test_traceback_detected(self):
        result = crc._detect_failure_type(
            manifest_failure="",
            log_content="Traceback (most recent call last):\nValueError",
        )
        self.assertEqual(result, "traceback")

    def test_oom_in_log_overrides_traceback(self):
        """When both OOM and traceback are in log, OOM takes priority."""
        result = crc._detect_failure_type(
            manifest_failure="",
            log_content="Traceback (most recent call last):\nCUDA out of memory",
        )
        self.assertEqual(result, "oom")

    def test_manifest_failure_passthrough(self):
        result = crc._detect_failure_type(
            manifest_failure="runtime_error",
            log_content="some normal log",
        )
        self.assertEqual(result, "runtime_error")

    def test_no_failure_returns_empty(self):
        result = crc._detect_failure_type(
            manifest_failure="",
            log_content="everything is fine",
        )
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# Test: _csv_status and _csv_has_rows
# ---------------------------------------------------------------------------

class TestCsvStatus(unittest.TestCase):
    """Test _csv_status() and _csv_has_rows() CSV validation."""

    def test_csv_not_found(self):
        path = Path("/tmp/nonexistent_csv_test_12345.csv")
        self.assertEqual(crc._csv_status(path), crc.CSV_NOT_FOUND)

    def test_csv_header_only(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("col_a,col_b\n")
            tmp_path = f.name
        try:
            self.assertEqual(crc._csv_status(Path(tmp_path)), crc.CSV_HEADER_ONLY)
            self.assertFalse(crc._csv_has_rows(Path(tmp_path)))
        finally:
            os.unlink(tmp_path)

    def test_csv_has_data_rows(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("col_a,col_b\n1,2\n")
            tmp_path = f.name
        try:
            self.assertEqual(crc._csv_status(Path(tmp_path)), crc.CSV_HAS_ROWS)
            self.assertTrue(crc._csv_has_rows(Path(tmp_path)))
        finally:
            os.unlink(tmp_path)

    def test_csv_empty_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            tmp_path = f.name
        try:
            self.assertEqual(crc._csv_status(Path(tmp_path)), crc.CSV_HEADER_ONLY)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Test: _validate_csv_content
# ---------------------------------------------------------------------------

class TestValidateCsvContent(unittest.TestCase):
    """Test _validate_csv_content() content completeness checks."""

    def test_valid_csv_no_warnings(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["kv_mode", "seq_len", "gen_len", "tpot_ms"])
            writer.writerow(["fp16", "1024", "128", "5.3"])
            tmp_path = f.name
        try:
            warnings = crc._validate_csv_content(Path(tmp_path), "profile_latency")
            self.assertEqual(warnings, [])
        finally:
            os.unlink(tmp_path)

    def test_csv_missing_columns_produces_warning(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["kv_mode", "seq_len"])  # missing gen_len, tpot_ms
            writer.writerow(["fp16", "1024"])
            tmp_path = f.name
        try:
            warnings = crc._validate_csv_content(Path(tmp_path), "profile_latency")
            self.assertTrue(len(warnings) > 0)
            self.assertTrue(any("missing expected columns" in w for w in warnings))
        finally:
            os.unlink(tmp_path)

    def test_csv_header_only_produces_warning(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["kv_mode", "seq_len", "gen_len", "tpot_ms"])
            tmp_path = f.name
        try:
            warnings = crc._validate_csv_content(Path(tmp_path), "profile_latency")
            self.assertTrue(len(warnings) > 0)
            self.assertTrue(any("no data rows" in w for w in warnings))
        finally:
            os.unlink(tmp_path)

    def test_csv_not_found_produces_warning(self):
        bogus = Path("/tmp/nonexistent_csv_validate_12345.csv")
        warnings = crc._validate_csv_content(bogus, "profile_latency")
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("not found" in w for w in warnings))

    def test_unknown_task_no_column_check(self):
        """For a task not in TASK_TO_EXPECTED_COLUMNS, column check is skipped."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["whatever"])
            writer.writerow(["data"])
            tmp_path = f.name
        try:
            warnings = crc._validate_csv_content(Path(tmp_path), "unknown_task")
            self.assertEqual(warnings, [])
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Test: _latest_failure_type
# ---------------------------------------------------------------------------

class TestLatestFailureType(unittest.TestCase):
    """Test _latest_failure_type() extraction from task info dicts."""

    def test_direct_failure_type(self):
        task_info = {"failure_type": "oom"}
        self.assertEqual(crc._latest_failure_type(task_info), "oom")

    def test_history_fallback(self):
        task_info = {
            "failure_type": "",
            "history": [
                {"status": "failed", "failure_type": "traceback"},
            ],
        }
        self.assertEqual(crc._latest_failure_type(task_info), "traceback")

    def test_history_latest_entry_wins(self):
        task_info = {
            "failure_type": "",
            "history": [
                {"status": "failed", "failure_type": "oom"},
                {"status": "failed", "failure_type": "traceback"},
            ],
        }
        # Reversed iteration means the last entry is checked first
        self.assertEqual(crc._latest_failure_type(task_info), "traceback")

    def test_empty_task_info_returns_empty(self):
        self.assertEqual(crc._latest_failure_type({}), "")

    def test_history_with_only_failed_status_returns_runtime_error(self):
        task_info = {
            "failure_type": "",
            "history": [
                {"status": "failed"},
            ],
        }
        self.assertEqual(crc._latest_failure_type(task_info), "runtime_error")


# ---------------------------------------------------------------------------
# Test: _check_task_state — TST-030: coverage for under-tested states
# (task_artifacts_missing, running, mixed_csv_non_success, missing)
# ---------------------------------------------------------------------------

class TestCheckTaskState(unittest.TestCase):
    """Test _check_task_state() covers all state classification branches.

    TST-030: Previously only success/oom/csv_invalid/traceback had tests.
    This class adds tests for: task_artifacts_missing, running,
    mixed_csv_non_success, missing, and csv_valid_manifest_incomplete.
    """

    def _make_csv(self, run_dir: Path, task: str, *, with_data: bool = True) -> None:
        """Helper: create a CSV matching the task pattern with optional data rows."""
        pattern_map = {
            "profile_latency": "profile_latency_test.csv",
            "eval_longbench": "profile_longbench_test.csv",
            "eval_ruler": "profile_ruler_test.csv",
        }
        filename = pattern_map.get(task, f"profile_{task}_test.csv")
        csv_path = run_dir / filename
        columns = crc.TASK_TO_EXPECTED_COLUMNS.get(task, ["col_a"])
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            if with_data:
                writer.writerow(["dummy"] * len(columns))

    def _make_log(self, logs_dir: Path, run_id: str, task: str, content: str = "") -> None:
        """Helper: create a log file for a given run_id and task."""
        log_dir = logs_dir / run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{task}.log").write_text(content, encoding="utf-8")

    def _make_longbench_artifacts(self, run_dir: Path) -> None:
        """Helper: create expected longbench task-level summary artifacts."""
        (run_dir / "longbench_task_summary_test.csv").write_text("header\ndata\n", encoding="utf-8")

    def _make_ruler_artifacts(self, run_dir: Path) -> None:
        """Helper: create expected ruler task-level summary artifacts."""
        (run_dir / "ruler_task_summary_test.csv").write_text("header\ndata\n", encoding="utf-8")
        (run_dir / "ruler_depth_summary_test.csv").write_text("header\ndata\n", encoding="utf-8")

    # -- state: success (baseline check) --

    def test_state_success_with_manifest_success(self):
        """CSV with data + task artifacts + manifest status=success => success."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency")
            task_info = {"status": "success"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "success")

    # -- state: oom --

    def test_state_oom_from_manifest(self):
        """manifest failure_type=oom => state=oom."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {"failure_type": "oom"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "oom")

    def test_state_oom_from_log(self):
        """Log contains OOM keyword => state=oom."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            logs_dir = Path(td) / "logs"
            self._make_log(logs_dir, "test_run", "profile_latency", "CUDA out of memory")
            task_info = {}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=logs_dir,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "oom")

    # -- state: task_artifacts_missing (TST-030) --

    def test_state_task_artifacts_missing_longbench(self):
        """CSV present + valid but longbench summary artifact missing => task_artifacts_missing."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "eval_longbench")
            # Do NOT create longbench_task_summary_*.csv
            task_info = {"status": "success"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="eval_longbench",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "task_artifacts_missing")
            self.assertTrue(result["has_csv"])
            self.assertFalse(result["has_task_artifacts"])

    def test_state_task_artifacts_missing_ruler_no_depth(self):
        """CSV present but ruler depth_summary missing => task_artifacts_missing."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "eval_ruler")
            # Create task_summary but NOT depth_summary
            (run_dir / "ruler_task_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            task_info = {"status": "success"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="eval_ruler",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "task_artifacts_missing")

    def test_state_task_artifacts_missing_ruler_no_task_summary(self):
        """CSV present but ruler task_summary missing => task_artifacts_missing."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "eval_ruler")
            # Create depth_summary but NOT task_summary
            (run_dir / "ruler_depth_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            task_info = {"status": "success"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="eval_ruler",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "task_artifacts_missing")

    # -- state: running (TST-030) --

    def test_state_running_no_csv(self):
        """No CSV output + manifest status=running => state=running."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {"status": "running"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "running")

    def test_state_failed_no_csv(self):
        """No CSV output + manifest status=failed => state=failed."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {"status": "failed"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "failed")

    # -- state: mixed_csv_non_success (TST-030) --

    def test_state_mixed_csv_non_success_manifest_failed(self):
        """CSV exists + valid but manifest says failed => mixed_csv_non_success."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency")
            task_info = {"status": "failed"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "mixed_csv_non_success")

    def test_state_mixed_csv_non_success_manifest_running(self):
        """CSV + valid data but manifest says running and has_task_artifacts=False
        (since we force longbench without artifacts) => mixed_csv_non_success path
        actually hits task_artifacts_missing first for longbench. Use profile_latency
        where has_task_artifacts is always True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency")
            # CSV valid + task_artifacts=True + manifest running =>
            # csv_valid_manifest_incomplete since all conditions met
            task_info = {"status": "running"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "csv_valid_manifest_incomplete")

    def test_state_mixed_csv_non_success_manifest_empty(self):
        """CSV exists but is header-only + manifest status empty =>
        csv_invalid comes first because has_valid_csv=False."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            # Create a CSV with data but with manifest saying "failed"
            self._make_csv(run_dir, "profile_latency", with_data=True)
            # has_valid_csv=True, has_task_artifacts=True for latency,
            # manifest_status=failed => should hit mixed_csv_non_success
            task_info = {"status": "failed", "failure_type": "runtime_error"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "mixed_csv_non_success")

    # -- state: missing (TST-030) --

    def test_state_missing_no_csv_no_manifest_no_log(self):
        """No CSV, no manifest status, no log evidence => state=missing."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "missing")

    def test_state_missing_no_csv_empty_manifest(self):
        """No CSV + empty manifest fields => missing."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {"status": "", "failure_type": ""}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "missing")

    # -- state: csv_invalid --

    def test_state_csv_invalid_header_only(self):
        """CSV exists but has no data rows => csv_invalid."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency", with_data=False)
            task_info = {"status": "success"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "csv_invalid")

    # -- state: traceback --

    def test_state_traceback_from_log_no_csv(self):
        """No CSV + log contains traceback => traceback."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            logs_dir = Path(td) / "logs"
            self._make_log(
                logs_dir, "test_run", "profile_latency",
                "Traceback (most recent call last):\nValueError: bad input\n",
            )
            task_info = {}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=logs_dir,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "traceback")

    # -- state: csv_valid_manifest_incomplete (CHK-007) --

    def test_state_csv_valid_manifest_incomplete(self):
        """CSV with data + task artifacts + manifest status=running
        => csv_valid_manifest_incomplete."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency")
            task_info = {"status": "running"}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "csv_valid_manifest_incomplete")

    # -- Return dict field assertions --

    def test_return_dict_has_all_expected_fields(self):
        """Verify all TypedDict fields are present in return value."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            expected_keys = {
                "task", "state", "manifest_status", "manifest_failure_type",
                "failure_type", "has_csv", "has_valid_csv", "has_task_artifacts",
                "csv_paths", "csv_content_warnings", "has_log", "log_path",
            }
            self.assertEqual(set(result.keys()), expected_keys)

    # -- logs_dir=None coverage --

    def test_logs_dir_none_has_log_false(self):
        """When logs_dir is None, has_log should be False and log_path empty string."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            task_info = {}
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertFalse(result["has_log"])
            self.assertEqual(result["log_path"], "")

    # -- success inferred from CSV/artifacts alone (CHK-021) --

    def test_state_success_inferred_from_csv_alone(self):
        """CSV valid + task artifacts + empty manifest => success (inferred, CHK-021)."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency")
            task_info = {}  # empty manifest
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "success")

    # -- success via history (has_success_history=True) --

    def test_state_success_via_history(self):
        """CSV valid + task artifacts + history contains success => success."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run_dir"
            run_dir.mkdir()
            self._make_csv(run_dir, "profile_latency")
            task_info = {
                "status": "failed",
                "failure_type": "",
                "history": [{"status": "success"}],
            }
            result = crc._check_task_state(
                run_dir=run_dir,
                logs_dir=None,
                run_id="test_run",
                task="profile_latency",
                task_info=task_info,
            )
            self.assertEqual(result["state"], "success")


# ---------------------------------------------------------------------------
# Test: _has_task_level_artifacts — TST-031
# ---------------------------------------------------------------------------

class TestHasTaskLevelArtifacts(unittest.TestCase):
    """Test _has_task_level_artifacts() for longbench and ruler branches.

    TST-031: These branches had zero tests previously.
    """

    # -- Non-eval tasks always return True --

    def test_non_eval_task_returns_true(self):
        """profile_latency has no task-level artifact checks => always True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "profile_latency"))

    def test_profile_memory_returns_true(self):
        """profile_memory has no task-level artifact checks => always True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "profile_memory"))

    def test_eval_ppl_returns_true(self):
        """eval_ppl has no task-level artifact checks => always True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "eval_ppl"))

    # -- Longbench branch --

    def test_longbench_has_task_summary(self):
        """eval_longbench with task_summary CSV present => True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "longbench_task_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "eval_longbench"))

    def test_longbench_missing_task_summary(self):
        """eval_longbench without task_summary CSV => False."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            self.assertFalse(crc._has_task_level_artifacts(run_dir, "eval_longbench"))

    def test_longbench_multiple_summaries(self):
        """eval_longbench with multiple task_summary CSVs => True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "longbench_task_summary_s1234.csv").write_text("h\n", encoding="utf-8")
            (run_dir / "longbench_task_summary_s1235.csv").write_text("h\n", encoding="utf-8")
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "eval_longbench"))

    # -- Ruler branch --

    def test_ruler_both_summaries_present(self):
        """eval_ruler with both task_summary and depth_summary => True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "ruler_task_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            (run_dir / "ruler_depth_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "eval_ruler"))

    def test_ruler_missing_task_summary(self):
        """eval_ruler without task_summary but with depth_summary => False."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "ruler_depth_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            self.assertFalse(crc._has_task_level_artifacts(run_dir, "eval_ruler"))

    def test_ruler_missing_depth_summary(self):
        """eval_ruler with task_summary but without depth_summary => False."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "ruler_task_summary_test.csv").write_text("h\nd\n", encoding="utf-8")
            self.assertFalse(crc._has_task_level_artifacts(run_dir, "eval_ruler"))

    def test_ruler_both_missing(self):
        """eval_ruler with neither summary => False."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            self.assertFalse(crc._has_task_level_artifacts(run_dir, "eval_ruler"))

    def test_ruler_multiple_summaries(self):
        """eval_ruler with multiple task_summary and depth_summary CSVs => True."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "ruler_task_summary_s1234.csv").write_text("h\n", encoding="utf-8")
            (run_dir / "ruler_task_summary_s1235.csv").write_text("h\n", encoding="utf-8")
            (run_dir / "ruler_depth_summary_s1234.csv").write_text("h\n", encoding="utf-8")
            (run_dir / "ruler_depth_summary_s1235.csv").write_text("h\n", encoding="utf-8")
            self.assertTrue(crc._has_task_level_artifacts(run_dir, "eval_ruler"))


# ---------------------------------------------------------------------------
# Test: _check_group / main integration — TST-033
# (allow_oom_completion, runs_dir missing, logs_dir=None,
#  allow_stress_unexpected_failures)
# ---------------------------------------------------------------------------

class TestCheckGroup(unittest.TestCase):
    """Test _check_group() behavior and main() edge cases.

    TST-033: Covers allow_oom_completion=False impact, runs_dir doesn't
    exist, logs_dir=None complete path, allow_stress_unexpected_failures.
    """

    def _make_run_with_state(
        self,
        runs_dir: Path,
        run_id: str,
        task: str,
        *,
        csv_data: bool = True,
        manifest_status: str = "success",
        manifest_failure_type: str = "",
        task_artifacts: bool = True,
    ) -> None:
        """Helper: set up a run_dir with a CSV and optional manifest."""
        import json as _json

        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create CSV
        pattern_map = {
            "profile_latency": "profile_latency_test.csv",
            "profile_memory": "profile_memory_test.csv",
            "eval_ppl": "profile_ppl_test.csv",
        }
        csv_name = pattern_map.get(task, f"profile_{task}_test.csv")
        columns = crc.TASK_TO_EXPECTED_COLUMNS.get(task, ["col_a"])
        with open(run_dir / csv_name, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            if csv_data:
                writer.writerow(["val"] * len(columns))

        # Create manifest
        manifest = {
            "tasks": {
                task: {
                    "status": manifest_status,
                    "failure_type": manifest_failure_type,
                }
            }
        }
        (run_dir / "run_manifest.json").write_text(
            _json.dumps(manifest), encoding="utf-8"
        )

    def test_allow_oom_completion_false_oom_run_is_incomplete(self):
        """When allow_oom_completion=False, OOM runs should appear in missing_run_names."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            run_id = "myrun_tag1"
            run_dir = runs_dir / run_id
            run_dir.mkdir()
            # No CSV, manifest says OOM
            import json as _json
            manifest = {"tasks": {"profile_latency": {"status": "failed", "failure_type": "oom"}}}
            (run_dir / "run_manifest.json").write_text(_json.dumps(manifest), encoding="utf-8")

            result = crc._check_group(
                group_name="required",
                run_names=["myrun"],
                run_tag="tag1",
                seeds=[],
                tasks=["profile_latency"],
                runs_dir=runs_dir,
                logs_dir=None,
                allow_oom_completion=False,
            )
            self.assertIn("myrun", result["missing_run_names"])
            self.assertTrue(len(result["oom_registry"]) > 0)

    def test_allow_oom_completion_true_oom_run_is_complete(self):
        """When allow_oom_completion=True, OOM runs should NOT appear in missing_run_names."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            run_id = "myrun_tag1"
            run_dir = runs_dir / run_id
            run_dir.mkdir()
            import json as _json
            manifest = {"tasks": {"profile_latency": {"status": "failed", "failure_type": "oom"}}}
            (run_dir / "run_manifest.json").write_text(_json.dumps(manifest), encoding="utf-8")

            result = crc._check_group(
                group_name="stress",
                run_names=["myrun"],
                run_tag="tag1",
                seeds=[],
                tasks=["profile_latency"],
                runs_dir=runs_dir,
                logs_dir=None,
                allow_oom_completion=True,
            )
            self.assertEqual(result["missing_run_names"], [])
            self.assertTrue(len(result["oom_registry"]) > 0)

    def test_logs_dir_none_complete_path(self):
        """_check_group with logs_dir=None should work without errors."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            self._make_run_with_state(runs_dir, "run1_tag1", "profile_latency")

            result = crc._check_group(
                group_name="required",
                run_names=["run1"],
                run_tag="tag1",
                seeds=[],
                tasks=["profile_latency"],
                runs_dir=runs_dir,
                logs_dir=None,
                allow_oom_completion=False,
            )
            self.assertEqual(result["missing_run_names"], [])
            self.assertEqual(len(result["rows"]), 1)
            self.assertFalse(result["rows"][0]["has_log"])

    def test_unexpected_failures_tracked(self):
        """Tasks with non-success/non-oom/non-missing state should be unexpected_failures."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            # Create a run with CSV but manifest says "failed" => mixed_csv_non_success
            self._make_run_with_state(
                runs_dir, "failrun_tag1", "profile_latency",
                manifest_status="failed",
                manifest_failure_type="runtime_error",
            )

            result = crc._check_group(
                group_name="required",
                run_names=["failrun"],
                run_tag="tag1",
                seeds=[],
                tasks=["profile_latency"],
                runs_dir=runs_dir,
                logs_dir=None,
                allow_oom_completion=False,
            )
            self.assertTrue(len(result["unexpected_failures"]) > 0)
            self.assertIn("failrun", result["missing_run_names"])

    def test_check_group_with_seeds(self):
        """_check_group with seeds generates run_ids with seed suffix."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            self._make_run_with_state(runs_dir, "run1_s42_tag1", "profile_latency")
            self._make_run_with_state(runs_dir, "run1_s43_tag1", "profile_latency")

            result = crc._check_group(
                group_name="required",
                run_names=["run1"],
                run_tag="tag1",
                seeds=[42, 43],
                tasks=["profile_latency"],
                runs_dir=runs_dir,
                logs_dir=None,
                allow_oom_completion=False,
            )
            self.assertEqual(result["missing_run_names"], [])
            self.assertEqual(len(result["rows"]), 2)


class TestMainEdgeCases(unittest.TestCase):
    """Test main() edge cases for TST-033.

    Covers: runs_dir doesn't exist (exit 2), allow_stress_unexpected_failures flag.
    """

    def test_runs_dir_not_exists_returns_2(self):
        """main() should return 2 when runs_dir doesn't exist."""
        with tempfile.TemporaryDirectory() as td:
            out_json = Path(td) / "report.json"
            test_args = [
                "check_run_completeness.py",
                "--runs_dir", "/tmp/nonexistent_dir_for_test_12345",
                "--run_tag", "test_tag",
                "--out_json", str(out_json),
            ]
            import unittest.mock
            with unittest.mock.patch("sys.argv", test_args):
                exit_code = crc.main()
            self.assertEqual(exit_code, 2)

    def test_no_tasks_returns_2(self):
        """main() should return 2 when tasks list is empty."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            out_json = Path(td) / "report.json"
            test_args = [
                "check_run_completeness.py",
                "--runs_dir", str(runs_dir),
                "--run_tag", "test_tag",
                "--tasks", "",
                "--out_json", str(out_json),
            ]
            import unittest.mock
            with unittest.mock.patch("sys.argv", test_args):
                exit_code = crc.main()
            self.assertEqual(exit_code, 2)

    def test_invalid_seed_returns_2(self):
        """main() should return 2 when seed value is not a valid integer."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            out_json = Path(td) / "report.json"
            test_args = [
                "check_run_completeness.py",
                "--runs_dir", str(runs_dir),
                "--run_tag", "test_tag",
                "--seeds", "abc",
                "--out_json", str(out_json),
            ]
            import unittest.mock
            with unittest.mock.patch("sys.argv", test_args):
                exit_code = crc.main()
            self.assertEqual(exit_code, 2)

    def test_main_with_logs_dir_empty_string(self):
        """main() should treat empty --logs_dir as None (logs_dir=None path)."""
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            out_json = Path(td) / "report.json"
            test_args = [
                "check_run_completeness.py",
                "--runs_dir", str(runs_dir),
                "--run_tag", "test_tag",
                "--logs_dir", "",
                "--required_run_names", "",
                "--stress_run_names", "",
                "--out_json", str(out_json),
            ]
            import unittest.mock
            with unittest.mock.patch("sys.argv", test_args):
                exit_code = crc.main()
            # With empty run_names, vacuously complete => exit 0
            self.assertEqual(exit_code, 0)

    def test_allow_stress_unexpected_failures_flag(self):
        """When --allow_stress_unexpected_failures is set, stress unexpected
        failures should not cause exit(2)."""
        with tempfile.TemporaryDirectory() as td:
            import json as _json

            runs_dir = Path(td) / "runs"
            runs_dir.mkdir()
            out_json = Path(td) / "report.json"

            # Create a stress run with an unexpected failure (csv present + manifest failed)
            run_dir = runs_dir / "stress_run_tag1"
            run_dir.mkdir()
            csv_path = run_dir / "profile_latency_test.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["kv_mode", "seq_len", "gen_len", "tpot_ms"])
                writer.writerow(["fp16", "1024", "128", "5.3"])
            manifest = {
                "tasks": {
                    "profile_latency": {"status": "failed", "failure_type": "runtime_error"}
                }
            }
            (run_dir / "run_manifest.json").write_text(_json.dumps(manifest), encoding="utf-8")

            # Without the flag, should get exit 2 due to unexpected failures
            test_args_no_flag = [
                "check_run_completeness.py",
                "--runs_dir", str(runs_dir),
                "--run_tag", "tag1",
                "--tasks", "profile_latency",
                "--required_run_names", "",
                "--stress_run_names", "stress_run",
                "--out_json", str(out_json),
            ]
            import unittest.mock
            with unittest.mock.patch("sys.argv", test_args_no_flag):
                exit_code_no_flag = crc.main()
            self.assertEqual(exit_code_no_flag, 2)

            # With the flag, unexpected stress failures should be suppressed
            test_args_with_flag = [
                "check_run_completeness.py",
                "--runs_dir", str(runs_dir),
                "--run_tag", "tag1",
                "--tasks", "profile_latency",
                "--required_run_names", "",
                "--stress_run_names", "stress_run",
                "--allow_stress_unexpected_failures",
                "--out_json", str(out_json),
            ]
            with unittest.mock.patch("sys.argv", test_args_with_flag):
                exit_code_with_flag = crc.main()
            # Still exit 1 because stress_run is missing (not complete),
            # but NOT exit 2 from unexpected_failures
            self.assertEqual(exit_code_with_flag, 1)


class TestDetectFailureTypeTimeoutInterrupt(unittest.TestCase):
    """TST-041 (R12/CHK-002): Timeout and interrupt failure type detection.

    _detect_failure_type should recognize manifest_failure='timeout' and
    'interrupt' as distinct failure types, not classify them as 'unknown'.
    """

    def test_manifest_timeout_recognized(self):
        """manifest_failure='timeout' should return 'timeout'."""
        result = crc._detect_failure_type(
            manifest_failure="timeout",
            log_content="",
        )
        self.assertEqual(result, "timeout")

    def test_manifest_interrupt_recognized(self):
        """manifest_failure='interrupt' should return 'interrupt'."""
        result = crc._detect_failure_type(
            manifest_failure="interrupt",
            log_content="",
        )
        self.assertEqual(result, "interrupt")

    def test_timeout_overrides_traceback_in_log(self):
        """manifest_failure='timeout' takes priority over traceback in log."""
        result = crc._detect_failure_type(
            manifest_failure="timeout",
            log_content="Traceback (most recent call last):\nTimeoutError\n",
        )
        self.assertEqual(result, "timeout")

    def test_interrupt_overrides_oom_in_log(self):
        """manifest_failure='interrupt' takes priority over OOM keywords in log."""
        result = crc._detect_failure_type(
            manifest_failure="interrupt",
            log_content="CUDA out of memory\n",
        )
        self.assertEqual(result, "interrupt")


if __name__ == "__main__":
    unittest.main()
