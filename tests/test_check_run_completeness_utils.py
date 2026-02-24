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


if __name__ == "__main__":
    unittest.main()
