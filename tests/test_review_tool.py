"""Tests for scripts/review_tool.py (TST-019/038).

Covers:
  - parse_tracker(): correct parsing of issue lines from tracker markdown
  - _update_summary(): summary line generation
  - cmd_phase_gate(): CRITICAL open issues block the gate
  - cmd_stats(): statistics output
  - ISSUE_RE / SECTION_RE regex patterns for issue detection
"""

import io
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

# ---------------------------------------------------------------------------
# sys.path setup — import the script module directly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import review_tool as rt  # noqa: E402


# ---------------------------------------------------------------------------
# Reusable test fixtures
# ---------------------------------------------------------------------------

SAMPLE_TRACKER = textwrap.dedent("""\
    # Review Tracker

    > 6 issues | 2 fixed | 4 open (1 CRIT, 1 HIGH, 1 MED, 1 LOW)
    > Phase Gate: **BLOCKED** — AA-1
    > Last updated: 2026-02-24

    ## Open Issues

    ### AA. Core Module

    - [ ] **AA-1** `[CRIT]` Critical bug in quantization path
    - [x] **AA-2** `[HIGH]` Memory leak fixed — fixed commit abc1234
    - [ ] **AA-3** `[MED]` Improve error messages

    ### AB. Utilities

    - [x] **AB-1** `[LOW]` Typo in docstring — fixed
    - [ ] **AB-2** `[HIGH]` Missing input validation
    - [ ] **AB-3** `[LOW]` Cosmetic log formatting

    ---

    ## Resolved
""")


SAMPLE_TRACKER_NO_BLOCKERS = textwrap.dedent("""\
    # Review Tracker

    > 3 issues | 1 fixed | 2 open (1 HIGH, 1 MED)
    > Phase Gate: **CLEAR** — none
    > Last updated: 2026-02-24

    ## Open Issues

    ### AA. Core Module

    - [x] **AA-1** `[CRIT]` Critical bug resolved — fixed commit abc1234
    - [ ] **AA-2** `[HIGH]` Memory leak still open
    - [ ] **AA-3** `[MED]` Improve error messages

    ---

    ## Resolved
""")


SAMPLE_TRACKER_FP_WONTFIX = textwrap.dedent("""\
    # Review Tracker

    > 4 issues | 1 fixed + 1 false_positive + 1 wont_fix | 1 open (1 MED)
    > Phase Gate: **CLEAR** — none
    > Last updated: 2026-02-24

    ## Open Issues

    ### AA. Core Module

    - [x] **AA-1** `[HIGH]` Resolved normally — fixed
    - [x] **AA-2** `[LOW]` Not a real issue — false_positive
    - [x] **AA-3** `[MED]` Decided not to fix — wont_fix
    - [ ] **AA-4** `[MED]` Still open issue

    ---

    ## Resolved
""")


def _write_tracker(content: str) -> Path:
    """Write tracker content to a temporary file and return the path."""
    fd, tmp_path = tempfile.mkstemp(suffix=".md", prefix="review_tracker_test_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return Path(tmp_path)


# ---------------------------------------------------------------------------
# Test: ISSUE_RE and SECTION_RE regex patterns
# ---------------------------------------------------------------------------

class TestRegexPatterns(unittest.TestCase):
    """Test that ISSUE_RE and SECTION_RE correctly match expected lines."""

    def test_issue_re_matches_open_issue(self):
        line = "- [ ] **AA-1** `[CRIT]` Critical bug in quantization path"
        m = rt.ISSUE_RE.match(line)
        self.assertIsNotNone(m, f"ISSUE_RE should match: {line!r}")
        checkbox, iid, sev, rest = m.groups()
        self.assertEqual(checkbox, " ")
        self.assertEqual(iid, "AA-1")
        self.assertEqual(sev, "CRIT")
        self.assertIn("Critical bug", rest)

    def test_issue_re_matches_resolved_issue(self):
        line = "- [x] **AB-1** `[LOW]` Typo in docstring — fixed"
        m = rt.ISSUE_RE.match(line)
        self.assertIsNotNone(m, f"ISSUE_RE should match: {line!r}")
        checkbox, iid, sev, rest = m.groups()
        self.assertEqual(checkbox, "x")
        self.assertEqual(iid, "AB-1")
        self.assertEqual(sev, "LOW")

    def test_issue_re_does_not_match_plain_text(self):
        line = "This is just a comment line"
        m = rt.ISSUE_RE.match(line)
        self.assertIsNone(m)

    def test_issue_re_does_not_match_malformed_issue(self):
        line = "- [ ] AA-1 [CRIT] Missing bold and backtick"
        m = rt.ISSUE_RE.match(line)
        self.assertIsNone(m)

    def test_section_re_matches_section_header(self):
        line = "### AA. Core Module"
        m = rt.SECTION_RE.match(line)
        self.assertIsNotNone(m, f"SECTION_RE should match: {line!r}")
        self.assertEqual(m.group(1), "AA")
        self.assertEqual(m.group(2).strip(), "Core Module")

    def test_section_re_matches_with_suffix(self):
        line = "### AB. Utilities — `scripts/`"
        m = rt.SECTION_RE.match(line)
        self.assertIsNotNone(m, f"SECTION_RE should match: {line!r}")
        self.assertEqual(m.group(1), "AB")

    def test_section_re_does_not_match_h2(self):
        line = "## Open Issues"
        m = rt.SECTION_RE.match(line)
        self.assertIsNone(m)

    def test_issue_re_matches_fixed_commit_suffix(self):
        line = "- [x] **AA-2** `[HIGH]` Memory leak fixed — fixed commit abc1234"
        m = rt.ISSUE_RE.match(line)
        self.assertIsNotNone(m)
        checkbox, iid, sev, rest = m.groups()
        self.assertEqual(checkbox, "x")
        self.assertEqual(iid, "AA-2")
        self.assertIn("fixed commit abc1234", rest)


# ---------------------------------------------------------------------------
# Test: parse_tracker()
# ---------------------------------------------------------------------------

class TestParseTracker(unittest.TestCase):
    """Test parse_tracker() correctly extracts issues from markdown."""

    def test_parse_returns_correct_count(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            self.assertEqual(len(issues), 6)
        finally:
            os.unlink(path)

    def test_parse_identifies_open_issues(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            open_issues = [i for i in issues if i["status"] == "open"]
            self.assertEqual(len(open_issues), 4)
        finally:
            os.unlink(path)

    def test_parse_identifies_fixed_issues(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            fixed = [i for i in issues if i["status"] == "fixed"]
            self.assertEqual(len(fixed), 2)
        finally:
            os.unlink(path)

    def test_parse_extracts_section_correctly(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            aa_issues = [i for i in issues if i["section"] == "AA"]
            ab_issues = [i for i in issues if i["section"] == "AB"]
            self.assertEqual(len(aa_issues), 3)
            self.assertEqual(len(ab_issues), 3)
        finally:
            os.unlink(path)

    def test_parse_extracts_severity(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            by_id = {i["id"]: i for i in issues}
            self.assertEqual(by_id["AA-1"]["severity"], "CRIT")
            self.assertEqual(by_id["AA-2"]["severity"], "HIGH")
            self.assertEqual(by_id["AA-3"]["severity"], "MED")
            self.assertEqual(by_id["AB-1"]["severity"], "LOW")
        finally:
            os.unlink(path)

    def test_parse_extracts_commit_from_fixed_suffix(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            by_id = {i["id"]: i for i in issues}
            self.assertEqual(by_id["AA-2"]["commit"], "abc1234")
            self.assertEqual(by_id["AA-2"]["status"], "fixed")
        finally:
            os.unlink(path)

    def test_parse_recognizes_false_positive_status(self):
        path = _write_tracker(SAMPLE_TRACKER_FP_WONTFIX)
        try:
            issues = rt.parse_tracker(path)
            by_id = {i["id"]: i for i in issues}
            self.assertEqual(by_id["AA-2"]["status"], "false_positive")
        finally:
            os.unlink(path)

    def test_parse_recognizes_wont_fix_status(self):
        path = _write_tracker(SAMPLE_TRACKER_FP_WONTFIX)
        try:
            issues = rt.parse_tracker(path)
            by_id = {i["id"]: i for i in issues}
            self.assertEqual(by_id["AA-3"]["status"], "wont_fix")
        finally:
            os.unlink(path)

    def test_parse_section_title(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            aa_issues = [i for i in issues if i["section"] == "AA"]
            self.assertTrue(all(i["section_title"] == "Core Module" for i in aa_issues))
        finally:
            os.unlink(path)

    def test_parse_missing_file_exits(self):
        """parse_tracker should sys.exit(2) when file does not exist."""
        bogus_path = Path("/tmp/nonexistent_review_tracker_test_12345.md")
        with self.assertRaises(SystemExit) as ctx:
            rt.parse_tracker(bogus_path)
        self.assertEqual(ctx.exception.code, 2)

    def test_parse_warns_on_malformed_issue_line(self):
        """Lines that start with '- [' but do not match ISSUE_RE trigger a warning."""
        content = textwrap.dedent("""\
            ## Open Issues

            ### AA. Core Module

            - [ ] **AA-1** `[CRIT]` Good issue
            - [ ] AA-2 malformed line that looks like issue
        """)
        path = _write_tracker(content)
        try:
            import warnings as w_mod
            with w_mod.catch_warnings(record=True) as caught:
                w_mod.simplefilter("always")
                issues = rt.parse_tracker(path)
            self.assertEqual(len(issues), 1)
            # Should have emitted a warning for the malformed line
            warn_msgs = [str(w.message) for w in caught]
            self.assertTrue(
                any("did not match" in msg for msg in warn_msgs),
                f"Expected a warning about malformed line, got: {warn_msgs}",
            )
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test: cmd_stats()
# ---------------------------------------------------------------------------

class TestCmdStats(unittest.TestCase):
    """Test cmd_stats() output and return code."""

    def test_stats_returns_zero(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            rc = rt.cmd_stats(issues)
            self.assertEqual(rc, 0)
        finally:
            os.unlink(path)

    def test_stats_output_contains_totals(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_stats(issues)
                output = mock_out.getvalue()
            self.assertIn("6 total", output)
            self.assertIn("open:", output)
            self.assertIn("fixed:", output)
        finally:
            os.unlink(path)

    def test_stats_output_shows_open_by_severity(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_stats(issues)
                output = mock_out.getvalue()
            self.assertIn("CRITICAL", output)
            self.assertIn("HIGH", output)
        finally:
            os.unlink(path)

    def test_stats_includes_wont_fix_when_present(self):
        path = _write_tracker(SAMPLE_TRACKER_FP_WONTFIX)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_stats(issues)
                output = mock_out.getvalue()
            self.assertIn("wont_fix:", output)
        finally:
            os.unlink(path)

    def test_stats_does_not_show_wont_fix_when_zero(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_stats(issues)
                output = mock_out.getvalue()
            self.assertNotIn("wont_fix:", output)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test: cmd_phase_gate()
# ---------------------------------------------------------------------------

class TestCmdPhaseGate(unittest.TestCase):
    """Test cmd_phase_gate() blocking logic."""

    def test_phase_gate_blocked_by_critical(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            rc = rt.cmd_phase_gate(issues)
            self.assertEqual(rc, 1, "Phase gate should return 1 when CRITICAL issues are open")
        finally:
            os.unlink(path)

    def test_phase_gate_blocked_output_mentions_blocker(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_phase_gate(issues)
                output = mock_out.getvalue()
            self.assertIn("BLOCKED", output)
            self.assertIn("AA-1", output)
        finally:
            os.unlink(path)

    def test_phase_gate_clear_when_no_critical(self):
        path = _write_tracker(SAMPLE_TRACKER_NO_BLOCKERS)
        try:
            issues = rt.parse_tracker(path)
            rc = rt.cmd_phase_gate(issues)
            self.assertEqual(rc, 0, "Phase gate should return 0 when no CRITICAL issues are open")
        finally:
            os.unlink(path)

    def test_phase_gate_clear_with_warnings_for_high(self):
        path = _write_tracker(SAMPLE_TRACKER_NO_BLOCKERS)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_phase_gate(issues)
                output = mock_out.getvalue()
            self.assertIn("CLEAR", output)
            self.assertIn("WARNING", output)
        finally:
            os.unlink(path)

    def test_phase_gate_fully_clear_no_high(self):
        """When no CRITICAL and no HIGH are open, output says CLEAR without warnings."""
        content = textwrap.dedent("""\
            ## Open Issues

            ### AA. Core Module

            - [x] **AA-1** `[CRIT]` Resolved — fixed
            - [x] **AA-2** `[HIGH]` Resolved — fixed
            - [ ] **AA-3** `[MED]` Low priority

            ---
        """)
        path = _write_tracker(content)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rc = rt.cmd_phase_gate(issues)
                output = mock_out.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("CLEAR", output)
            self.assertNotIn("WARNING", output)
            self.assertIn("No blocking CRITICAL issues", output)
        finally:
            os.unlink(path)

    def test_phase_gate_multiple_critical_blockers(self):
        content = textwrap.dedent("""\
            ## Open Issues

            ### AA. Core Module

            - [ ] **AA-1** `[CRIT]` First critical issue
            - [ ] **AA-2** `[CRIT]` Second critical issue
            - [ ] **AA-3** `[MED]` Not critical

            ---
        """)
        path = _write_tracker(content)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rc = rt.cmd_phase_gate(issues)
                output = mock_out.getvalue()
            self.assertEqual(rc, 1)
            self.assertIn("2 CRITICAL open", output)
            self.assertIn("AA-1", output)
            self.assertIn("AA-2", output)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test: cmd_open()
# ---------------------------------------------------------------------------

class TestCmdOpen(unittest.TestCase):
    """Test cmd_open() filtering and output."""

    def test_open_lists_only_open_issues(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rc = rt.cmd_open(issues)
                output = mock_out.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("4", output)  # 4 open issues
        finally:
            os.unlink(path)

    def test_open_filter_by_severity(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rc = rt.cmd_open(issues, sev="CRIT")
                output = mock_out.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("1", output)
            self.assertIn("AA-1", output)
        finally:
            os.unlink(path)

    def test_open_filter_by_section(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rc = rt.cmd_open(issues, section="AB")
                output = mock_out.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("AB-2", output)
            self.assertIn("AB-3", output)
        finally:
            os.unlink(path)

    def test_open_invalid_severity_returns_error(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            rc = rt.cmd_open(issues, sev="INVALID")
            self.assertEqual(rc, 1)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test: cmd_progress()
# ---------------------------------------------------------------------------

class TestCmdProgress(unittest.TestCase):
    """Test cmd_progress() section breakdown."""

    def test_progress_returns_zero(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            rc = rt.cmd_progress(issues)
            self.assertEqual(rc, 0)
        finally:
            os.unlink(path)

    def test_progress_output_contains_sections(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            issues = rt.parse_tracker(path)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                rt.cmd_progress(issues)
                output = mock_out.getvalue()
            self.assertIn("AA", output)
            self.assertIn("AB", output)
            self.assertIn("Total", output)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test: _update_summary()
# ---------------------------------------------------------------------------

class TestUpdateSummary(unittest.TestCase):
    """Test _update_summary() regenerates summary lines correctly."""

    def test_update_summary_updates_issue_count(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rt._update_summary(path)
            content = path.read_text(encoding="utf-8")
            # Should contain the updated summary line with correct total
            self.assertIn("> 6 issues", content)
        finally:
            os.unlink(path)

    def test_update_summary_updates_phase_gate_line(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rt._update_summary(path)
            content = path.read_text(encoding="utf-8")
            self.assertIn("> Phase Gate: **BLOCKED**", content)
            self.assertIn("AA-1", content)
        finally:
            os.unlink(path)

    def test_update_summary_clear_when_no_critical(self):
        path = _write_tracker(SAMPLE_TRACKER_NO_BLOCKERS)
        try:
            rt._update_summary(path)
            content = path.read_text(encoding="utf-8")
            self.assertIn("> Phase Gate: **CLEAR**", content)
        finally:
            os.unlink(path)

    def test_update_summary_updates_last_updated_date(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rt._update_summary(path)
            content = path.read_text(encoding="utf-8")
            self.assertRegex(content, r"> Last updated: \d{4}-\d{2}-\d{2}")
        finally:
            os.unlink(path)

    def test_update_summary_includes_wont_fix_in_resolution(self):
        path = _write_tracker(SAMPLE_TRACKER_FP_WONTFIX)
        try:
            rt._update_summary(path)
            content = path.read_text(encoding="utf-8")
            # The summary line should include wont_fix count
            self.assertIn("wont_fix", content)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test: SEV_ORDER and SEV_FULL constants
# ---------------------------------------------------------------------------

class TestSeverityConstants(unittest.TestCase):
    """Verify SEV_ORDER and SEV_FULL are consistent and complete."""

    def test_sev_order_has_four_levels(self):
        self.assertEqual(len(rt.SEV_ORDER), 4)

    def test_sev_full_maps_all_keys(self):
        for key in rt.SEV_ORDER:
            self.assertIn(key, rt.SEV_FULL)

    def test_sev_order_crit_is_highest(self):
        self.assertEqual(rt.SEV_ORDER["CRIT"], 0)

    def test_sev_order_low_is_lowest(self):
        self.assertEqual(rt.SEV_ORDER["LOW"], 3)


# ---------------------------------------------------------------------------
# Test: cmd_add() — including boundary cases (RVW-014, TST-019)
# ---------------------------------------------------------------------------

class TestCmdAdd(unittest.TestCase):
    """Test cmd_add() insertion logic and error paths."""

    def test_add_to_existing_section(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rc = rt.cmd_add(path, "AA-9", "HIGH", "AA. Core Module", "New high issue")
            self.assertEqual(rc, 0)
            content = path.read_text(encoding="utf-8")
            self.assertIn("**AA-9**", content)
            self.assertIn("`[HIGH]`", content)
        finally:
            os.unlink(path)

    def test_add_creates_new_section(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rc = rt.cmd_add(path, "ZZ-1", "MED", "ZZ. Brand New", "A brand new section issue")
            self.assertEqual(rc, 0)
            content = path.read_text(encoding="utf-8")
            self.assertIn("### ZZ. Brand New", content)
            self.assertIn("**ZZ-1**", content)
        finally:
            os.unlink(path)

    def test_add_duplicate_id_returns_error(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rc = rt.cmd_add(path, "AA-1", "HIGH", "AA. Core Module", "Duplicate")
            self.assertEqual(rc, 1)
        finally:
            os.unlink(path)

    def test_add_missing_open_issues_section_returns_error(self):
        """cmd_add returns error when '## Open Issues' is missing."""
        content = textwrap.dedent("""\
            # Review Tracker

            > 0 issues | | 0 open ()
            > Phase Gate: **CLEAR** — none
            > Last updated: 2026-02-24

            ### AA. Core Module

            ---
        """)
        path = _write_tracker(content)
        try:
            rc = rt.cmd_add(path, "AA-1", "HIGH", "AA. Core Module", "Test issue")
            self.assertEqual(rc, 1, "Should fail when '## Open Issues' is missing")
        finally:
            os.unlink(path)

    def test_add_no_separator_returns_error(self):
        """RVW-014: cmd_add returns error when no '---' separator after Open Issues."""
        content = textwrap.dedent("""\
            # Review Tracker

            > 0 issues | | 0 open ()
            > Phase Gate: **CLEAR** — none
            > Last updated: 2026-02-24

            ## Open Issues

            ### AA. Core Module

        """)
        path = _write_tracker(content)
        try:
            # Adding to existing section should work (appends at end of file)
            # But adding a NEW section with no --- separator should fail
            rc = rt.cmd_add(path, "ZZ-1", "MED", "ZZ. New Section", "Issue without separator")
            self.assertEqual(rc, 1, "Should fail when no '---' separator for new section")
        finally:
            os.unlink(path)

    def test_add_accepts_full_severity_names(self):
        path = _write_tracker(SAMPLE_TRACKER)
        try:
            rc = rt.cmd_add(path, "AA-8", "CRITICAL", "AA. Core Module", "Full sev name")
            self.assertEqual(rc, 0)
            content = path.read_text(encoding="utf-8")
            self.assertIn("`[CRIT]`", content)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
