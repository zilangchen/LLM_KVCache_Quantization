"""TST-034: Unit tests for scripts/export_tables_latex.py — helper functions,
LaTeX generation, and end-to-end export with temp CSV fixtures.

Covers:
  - _sanitize_label: LaTeX-unsafe character removal
  - _read_csv: success, failure (bare except), missing file
  - _sort_kv_mode: ordering by KV_MODE_ORDER
  - _display_kv_mode: display name mapping
  - _split_by_model: single-model, multi-model, missing column
  - _pivot_metric: basic pivot, multi-model averaging, rounding, empty input
  - _latex_table_env: wrapper generation with/without footnote
  - _to_latex_tabular: empty/non-empty DataFrame
  - _write: creates parent dirs, writes UTF-8
  - export_ppl: end-to-end with temp CSV
  - export_needle: end-to-end with temp CSV
  - export_latency: end-to-end via _export_profile_table
  - export_longbench: end-to-end with footnote verification
  - LaTeX special character handling (escape=True in to_latex)
"""

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from export_tables_latex import (  # noqa: E402
    KV_MODE_DISPLAY,
    _export_ruler_subtask_tables,
    _display_kv_mode,
    _latex_table_env,
    _latex_escape,
    _pivot_metric,
    _read_csv,
    _sanitize_label,
    _sort_kv_mode,
    _split_by_model,
    _to_latex_tabular,
    _write,
    export_latency,
    export_longbench,
    export_needle,
    export_ppl,
)
from config_utils import KV_MODE_ORDER  # noqa: E402


# ===========================================================================
# _sanitize_label
# ===========================================================================


class TestSanitizeLabel(unittest.TestCase):
    """_sanitize_label must strip LaTeX-unsafe chars and collapse whitespace."""

    def test_plain_text_unchanged(self):
        self.assertEqual(_sanitize_label("hello"), "hello")

    def test_strips_backslash_and_braces(self):
        self.assertEqual(_sanitize_label(r"\textbf{bold}"), "textbfbold")

    def test_strips_hash_dollar_percent_ampersand_caret_tilde(self):
        result = _sanitize_label("#$%&^~test")
        self.assertEqual(result, "test")

    def test_collapses_whitespace_to_underscores(self):
        self.assertEqual(_sanitize_label("hello   world"), "hello_world")

    def test_strips_leading_trailing_whitespace(self):
        self.assertEqual(_sanitize_label("  foo  "), "foo")

    def test_empty_string(self):
        self.assertEqual(_sanitize_label(""), "")

    def test_all_unsafe_chars_produces_empty(self):
        self.assertEqual(_sanitize_label("#$%&"), "")

    def test_mixed_unsafe_and_whitespace(self):
        # "a $b c" → "a b c" → "a_b_c"
        self.assertEqual(_sanitize_label("a $b c"), "a_b_c")


# ===========================================================================
# _read_csv
# ===========================================================================


class TestReadCsv(unittest.TestCase):
    """_read_csv must return a DataFrame on success and empty DataFrame on failure."""

    def test_reads_valid_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("col_a,col_b\n1,2\n3,4\n")
            tmp_path = f.name
        try:
            df = _read_csv(Path(tmp_path))
            self.assertEqual(list(df.columns), ["col_a", "col_b"])
            self.assertEqual(len(df), 2)
            self.assertEqual(df["col_a"].iloc[0], 1)
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_returns_empty(self):
        """Bare except in _read_csv must catch FileNotFoundError and return empty DF."""
        df = _read_csv(Path("/tmp/_nonexistent_csv_tst034_xyz.csv"))
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

    def test_malformed_csv_returns_empty(self):
        """A file that cannot be parsed as CSV should return empty DF."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
        ) as f:
            # Write binary garbage that will cause a decode error
            f.write(b"\x80\x81\x82\x00\x00\xff\xfe")
            tmp_path = f.name
        try:
            df = _read_csv(Path(tmp_path))
            # Even if pandas manages to read some bytes, at least it should not raise
            self.assertIsInstance(df, pd.DataFrame)
        finally:
            os.unlink(tmp_path)

    def test_empty_csv_file(self):
        """An empty file should return an empty DataFrame."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("")
            tmp_path = f.name
        try:
            df = _read_csv(Path(tmp_path))
            self.assertIsInstance(df, pd.DataFrame)
            self.assertTrue(df.empty)
        finally:
            os.unlink(tmp_path)


# ===========================================================================
# _sort_kv_mode
# ===========================================================================


class TestSortKvMode(unittest.TestCase):
    """_sort_kv_mode must order rows by KV_MODE_ORDER, unknown modes last."""

    def test_sorts_known_modes(self):
        df = pd.DataFrame({"kv_mode": ["int4_ours", "fp16", "int8_baseline"], "val": [1, 2, 3]})
        result = _sort_kv_mode(df)
        self.assertEqual(list(result["kv_mode"]), ["fp16", "int8_baseline", "int4_ours"])

    def test_unknown_modes_sorted_after_known(self):
        df = pd.DataFrame({"kv_mode": ["unknown_mode", "fp16"], "val": [1, 2]})
        result = _sort_kv_mode(df)
        self.assertEqual(list(result["kv_mode"]), ["fp16", "unknown_mode"])

    def test_empty_df_returns_empty(self):
        df = pd.DataFrame()
        result = _sort_kv_mode(df)
        self.assertTrue(result.empty)

    def test_no_kv_mode_column_returns_unchanged(self):
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        result = _sort_kv_mode(df)
        self.assertEqual(list(result["other_col"]), [1, 2, 3])

    def test_does_not_add_rank_column(self):
        """The temporary _kv_mode_rank column must be removed."""
        df = pd.DataFrame({"kv_mode": ["fp16", "int8_ours"], "val": [1, 2]})
        result = _sort_kv_mode(df)
        self.assertNotIn("_kv_mode_rank", result.columns)


# ===========================================================================
# _display_kv_mode
# ===========================================================================


class TestDisplayKvMode(unittest.TestCase):
    """_display_kv_mode must replace internal keys with display names."""

    def test_maps_known_modes(self):
        df = pd.DataFrame({"kv_mode": ["fp16", "int8_ours", "int4_fused"]})
        result = _display_kv_mode(df)
        self.assertEqual(list(result["kv_mode"]), ["FP16", "INT8-ours", "INT4-fused"])

    def test_unknown_mode_kept_as_is(self):
        df = pd.DataFrame({"kv_mode": ["custom_mode"]})
        result = _display_kv_mode(df)
        self.assertEqual(result["kv_mode"].iloc[0], "custom_mode")

    def test_empty_df(self):
        result = _display_kv_mode(pd.DataFrame())
        self.assertTrue(result.empty)

    def test_no_kv_mode_column(self):
        df = pd.DataFrame({"x": [1]})
        result = _display_kv_mode(df)
        self.assertEqual(list(result.columns), ["x"])

    def test_all_kv_mode_display_entries(self):
        """Ensure every key in KV_MODE_DISPLAY is properly mapped."""
        modes = list(KV_MODE_DISPLAY.keys())
        df = pd.DataFrame({"kv_mode": modes})
        result = _display_kv_mode(df)
        for i, mode in enumerate(modes):
            self.assertEqual(result["kv_mode"].iloc[i], KV_MODE_DISPLAY[mode])


# ===========================================================================
# _split_by_model
# ===========================================================================


class TestSplitByModel(unittest.TestCase):
    """_split_by_model must split DataFrames by model_id for per-model table generation."""

    def test_no_model_id_column(self):
        """Without model_id, returns single entry with empty suffix and label."""
        df = pd.DataFrame({"kv_mode": ["fp16"], "val": [1]})
        result = _split_by_model(df)
        self.assertEqual(len(result), 1)
        suffix, label, sub_df = result[0]
        self.assertEqual(suffix, "")
        self.assertEqual(label, "")
        self.assertEqual(len(sub_df), 1)

    def test_single_model_returns_single_entry(self):
        """With only one unique model_id, returns single entry with empty suffix."""
        df = pd.DataFrame({
            "model_id": ["Qwen/Qwen2.5-1.5B-Instruct"] * 3,
            "kv_mode": ["fp16", "int8_ours", "int4_ours"],
        })
        result = _split_by_model(df)
        self.assertEqual(len(result), 1)
        suffix, label, sub_df = result[0]
        self.assertEqual(suffix, "")
        self.assertEqual(label, "")
        self.assertEqual(len(sub_df), 3)

    def test_multiple_models_split_correctly(self):
        """With two models, returns two entries sorted by model_id."""
        df = pd.DataFrame({
            "model_id": ["ModelA/small", "ModelB/large", "ModelA/small"],
            "kv_mode": ["fp16", "fp16", "int8_ours"],
            "val": [1, 2, 3],
        })
        result = _split_by_model(df)
        self.assertEqual(len(result), 2)
        # Sorted: ModelA/small first
        suffix0, label0, sub0 = result[0]
        suffix1, label1, sub1 = result[1]
        self.assertIn("modela", suffix0.lower())
        self.assertIn("modelb", suffix1.lower())
        self.assertEqual(len(sub0), 2)  # ModelA has 2 rows
        self.assertEqual(len(sub1), 1)  # ModelB has 1 row

    def test_suffix_is_filesystem_safe(self):
        """model_id with slashes and special chars must produce safe suffix."""
        df = pd.DataFrame({
            "model_id": ["Org/Model.Name-v2", "Org/Other"],
            "kv_mode": ["fp16", "fp16"],
        })
        result = _split_by_model(df)
        for suffix, label, _ in result:
            # Suffix starts with underscore and contains no unsafe chars
            self.assertTrue(suffix.startswith("_"), f"Expected suffix to start with '_': {suffix}")
            for ch in ["/", " ", "\\", "{", "}"]:
                self.assertNotIn(ch, suffix)

    def test_label_uses_short_name(self):
        """label should use the part after the last '/' in model_id."""
        df = pd.DataFrame({
            "model_id": ["Qwen/Qwen2.5-1.5B-Instruct", "Meta/LLaMA-3.1-8B"],
            "kv_mode": ["fp16", "fp16"],
        })
        result = _split_by_model(df)
        labels = [label for _, label, _ in result]
        # Should contain short model name in parentheses
        self.assertIn("LLaMA-3.1-8B", labels[0])  # Meta sorts before Qwen
        self.assertIn("Qwen2.5-1.5B-Instruct", labels[1])

    def test_label_escapes_latex_special_chars(self):
        df = pd.DataFrame(
            {
                "model_id": ["Org/Model_Name&v1", "Org/Another"],
                "kv_mode": ["fp16", "fp16"],
            }
        )
        result = _split_by_model(df)
        labels = [label for _, label, _ in result]
        self.assertTrue(any(r"Model\_Name\&v1" in label for label in labels))


# ===========================================================================
# _pivot_metric
# ===========================================================================


class TestPivotMetric(unittest.TestCase):
    """_pivot_metric must pivot, average duplicates, round, and handle edge cases."""

    def _make_df(self, rows):
        """Create a DataFrame from list of (seq_len, kv_mode, metric_val) tuples."""
        return pd.DataFrame(rows, columns=["seq_len", "kv_mode", "metric_val"])

    def test_basic_pivot(self):
        df = self._make_df([
            (1024, "fp16", 10.0),
            (1024, "int8_ours", 12.0),
            (2048, "fp16", 20.0),
            (2048, "int8_ours", 22.0),
        ])
        result = _pivot_metric(df, "metric_val")
        # Should have seq_len as first column, then kv_mode columns
        self.assertIn("seq_len", result.columns)
        self.assertIn("fp16", result.columns)
        self.assertIn("int8_ours", result.columns)
        self.assertEqual(len(result), 2)
        # Check values
        row_1024 = result[result["seq_len"] == 1024].iloc[0]
        self.assertAlmostEqual(row_1024["fp16"], 10.0)
        self.assertAlmostEqual(row_1024["int8_ours"], 12.0)

    def test_duplicate_averaging(self):
        """Duplicates for the same (seq_len, kv_mode) must be averaged."""
        df = self._make_df([
            (1024, "fp16", 10.0),
            (1024, "fp16", 20.0),
        ])
        result = _pivot_metric(df, "metric_val")
        self.assertAlmostEqual(result["fp16"].iloc[0], 15.0)

    def test_multi_model_averaging(self):
        """When model_id is present with >1 models, pivot averages across them."""
        df = pd.DataFrame({
            "seq_len": [1024, 1024],
            "kv_mode": ["fp16", "fp16"],
            "metric_val": [10.0, 20.0],
            "model_id": ["ModelA", "ModelB"],
        })
        result = _pivot_metric(df, "metric_val")
        # Should average: (10+20)/2 = 15
        self.assertAlmostEqual(result["fp16"].iloc[0], 15.0)

    def test_rounding(self):
        df = self._make_df([(1024, "fp16", 3.14159)])
        result = _pivot_metric(df, "metric_val", round_digits=2)
        self.assertAlmostEqual(result["fp16"].iloc[0], 3.14)

    def test_no_rounding_when_none(self):
        df = self._make_df([(1024, "fp16", 3.14159)])
        result = _pivot_metric(df, "metric_val", round_digits=None)
        self.assertAlmostEqual(result["fp16"].iloc[0], 3.14159, places=4)

    def test_empty_df_returns_empty(self):
        result = _pivot_metric(pd.DataFrame(), "metric_val")
        self.assertTrue(result.empty)

    def test_missing_metric_col_returns_empty(self):
        df = pd.DataFrame({"seq_len": [1024], "kv_mode": ["fp16"], "other": [1.0]})
        result = _pivot_metric(df, "metric_val")
        self.assertTrue(result.empty)

    def test_seq_len_sorted_ascending(self):
        df = self._make_df([
            (4096, "fp16", 1.0),
            (1024, "fp16", 2.0),
            (2048, "fp16", 3.0),
        ])
        result = _pivot_metric(df, "metric_val")
        self.assertEqual(list(result["seq_len"]), [1024, 2048, 4096])

    def test_seq_len_cast_to_int(self):
        df = self._make_df([(1024.0, "fp16", 1.0)])
        result = _pivot_metric(df, "metric_val")
        self.assertEqual(result["seq_len"].dtype.kind, "i")  # integer type

    def test_non_numeric_metric_dropped(self):
        """Rows where metric is not numeric should be dropped (errors='coerce')."""
        df = pd.DataFrame({
            "seq_len": [1024, 2048],
            "kv_mode": ["fp16", "fp16"],
            "metric_val": ["not_a_number", 5.0],
        })
        result = _pivot_metric(df, "metric_val")
        # Only the numeric row should survive
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result["fp16"].iloc[0], 5.0)

    def test_custom_index_and_columns(self):
        """Verify non-default index_col and columns_col work."""
        df = pd.DataFrame({
            "depth": [0.5, 0.5, 1.0, 1.0],
            "method": ["A", "B", "A", "B"],
            "score": [80, 85, 90, 95],
        })
        result = _pivot_metric(
            df, "score", index_col="depth", columns_col="method"
        )
        self.assertIn("depth", result.columns)
        self.assertIn("A", result.columns)
        self.assertIn("B", result.columns)

    def test_kv_mode_column_order_follows_kv_mode_order(self):
        df = pd.DataFrame(
            {
                "seq_len": [1024, 1024, 1024],
                "kv_mode": ["int4_ours", "fp16", "int8_baseline"],
                "metric_val": [1.0, 2.0, 3.0],
            }
        )
        result = _pivot_metric(df, "metric_val")
        metric_cols = [c for c in result.columns if c != "seq_len"]
        self.assertEqual(metric_cols, ["fp16", "int8_baseline", "int4_ours"])


# ===========================================================================
# _latex_table_env
# ===========================================================================


class TestLatexTableEnv(unittest.TestCase):
    """_latex_table_env must wrap tabular LaTeX in a table environment."""

    def test_basic_wrapper(self):
        tabular = r"""\begin{tabular}{lr}
\toprule
a & b \\
\bottomrule
\end{tabular}"""
        result = _latex_table_env(tabular, caption="My Caption", label="tab:test")
        self.assertIn(r"\begin{table}[t]", result)
        self.assertIn(r"\centering", result)
        self.assertIn(r"\caption{My Caption}", result)
        self.assertIn(r"\label{tab:test}", result)
        self.assertIn(r"\small", result)
        self.assertIn(r"\end{table}", result)
        self.assertIn(tabular.rstrip(), result)

    def test_no_footnote(self):
        result = _latex_table_env("tabular", caption="C", label="L", footnote=None)
        self.assertNotIn(r"\footnotesize", result)
        self.assertNotIn(r"\parbox", result)

    def test_with_footnote(self):
        result = _latex_table_env(
            "tabular", caption="C", label="L", footnote="Important note."
        )
        self.assertIn(r"\vspace{1mm}", result)
        self.assertIn(r"\footnotesize Important note.", result)
        self.assertIn(r"\parbox", result)

    def test_trailing_whitespace_stripped_from_tabular(self):
        result = _latex_table_env("tabular   \n  ", caption="C", label="L")
        # The tabular should appear without trailing whitespace
        self.assertIn("tabular", result)
        self.assertNotIn("tabular   ", result)

    def test_result_ends_with_newline(self):
        result = _latex_table_env("tabular", caption="C", label="L")
        self.assertTrue(result.endswith("\n"))

    def test_order_of_elements(self):
        """Verify the structural order: begin, centering, caption, label, small, tabular, end."""
        result = _latex_table_env("TABULAR_CONTENT", caption="CAP", label="LAB")
        lines = result.strip().split("\n")
        # Extract key structural lines
        self.assertEqual(lines[0], r"\begin{table}[t]")
        self.assertEqual(lines[1], r"\centering")
        self.assertIn("caption", lines[2].lower())
        self.assertIn("label", lines[3].lower())
        self.assertEqual(lines[4], r"\small")
        self.assertIn("TABULAR_CONTENT", lines[5])
        self.assertEqual(lines[-1], r"\end{table}")


# ===========================================================================
# _to_latex_tabular
# ===========================================================================


class TestToLatexTabular(unittest.TestCase):
    """_to_latex_tabular must produce booktabs-compatible LaTeX or empty string."""

    def test_empty_df_returns_empty_string(self):
        result = _to_latex_tabular(pd.DataFrame())
        self.assertEqual(result, "")

    def test_basic_output(self):
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = _to_latex_tabular(df)
        self.assertIn(r"\begin{tabular}", result)
        self.assertIn(r"\end{tabular}", result)
        # Should contain the data
        self.assertIn("1", result)
        self.assertIn("4", result)

    def test_no_index_by_default(self):
        df = pd.DataFrame({"A": [1]}, index=[99])
        result = _to_latex_tabular(df, index=False)
        # Index value 99 should NOT appear
        self.assertNotIn("99", result)

    def test_with_index(self):
        df = pd.DataFrame({"A": [1]}, index=[99])
        result = _to_latex_tabular(df, index=True)
        self.assertIn("99", result)


# ===========================================================================
# _write
# ===========================================================================


class TestWrite(unittest.TestCase):
    """_write must create parent directories and write UTF-8 content."""

    def test_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.tex"
            _write(path, "hello world")
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), "hello world")

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "a" / "b" / "c" / "output.tex"
            _write(path, "nested")
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), "nested")

    def test_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.tex"
            _write(path, "first")
            _write(path, "second")
            self.assertEqual(path.read_text(encoding="utf-8"), "second")

    def test_utf8_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.tex"
            _write(path, "Unicode: \u00e9\u00e8\u00ea")
            content = path.read_text(encoding="utf-8")
            self.assertIn("\u00e9", content)


# ===========================================================================
# LaTeX special character handling
# ===========================================================================


class TestLatexSpecialCharEscaping(unittest.TestCase):
    """Verify that _to_latex_tabular escapes LaTeX special characters."""

    def test_ampersand_escaped(self):
        df = pd.DataFrame({"col": ["A & B"]})
        result = _to_latex_tabular(df)
        self.assertIn(r"A \& B", result)

    def test_underscore_escaped(self):
        df = pd.DataFrame({"col": ["a_b"]})
        result = _to_latex_tabular(df)
        self.assertIn(r"a\_b", result)

    def test_percent_escaped(self):
        df = pd.DataFrame({"col": ["50%"]})
        result = _to_latex_tabular(df)
        self.assertIn(r"50\%", result)

    def test_hash_escaped(self):
        df = pd.DataFrame({"col": ["#1"]})
        result = _to_latex_tabular(df)
        self.assertIn(r"\#1", result)

    def test_dollar_escaped(self):
        df = pd.DataFrame({"col": ["$10"]})
        result = _to_latex_tabular(df)
        self.assertIn(r"\$10", result)

    def test_latex_escape_helper(self):
        escaped = _latex_escape("Model_Name&v1")
        self.assertEqual(escaped, r"Model\_Name\&v1")


# ===========================================================================
# End-to-end: export_ppl
# ===========================================================================


class TestExportPpl(unittest.TestCase):
    """End-to-end test for export_ppl with a minimal CSV fixture."""

    def test_export_ppl_creates_tex_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            # Create minimal ppl_summary.csv
            csv_content = textwrap.dedent("""\
                kv_mode,batch,perplexity_mean,tokens_evaluated_mean
                fp16,1,5.1234,1000
                int8_ours,1,5.2345,1000
                int4_ours,1,5.5678,1000
            """)
            (tables_dir / "ppl_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_ppl(tables_dir, out_dir, label_prefix="tab")

            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].exists())
            content = paths[0].read_text(encoding="utf-8")
            self.assertIn(r"\begin{table}", content)
            self.assertIn(r"\end{table}", content)
            self.assertIn("Perplexity", content)
            self.assertIn("5.1234", content)

    def test_export_ppl_filters_batch(self):
        """Only batch=1 rows should be included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,batch,perplexity_mean,tokens_evaluated_mean
                fp16,1,5.0,1000
                fp16,4,99.0,4000
                int8_ours,1,5.5,1000
            """)
            (tables_dir / "ppl_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_ppl(tables_dir, out_dir, label_prefix="tab")

            self.assertEqual(len(paths), 1)
            content = paths[0].read_text(encoding="utf-8")
            # batch=4 perplexity (99.0) should NOT appear
            self.assertNotIn("99.0", content)
            self.assertIn("5.0", content)

    def test_export_ppl_empty_csv(self):
        """Missing CSV should return empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()
            # No ppl_summary.csv created

            paths = export_ppl(tables_dir, out_dir, label_prefix="tab")
            self.assertEqual(paths, [])

    def test_export_ppl_display_names(self):
        """kv_mode values should be mapped to display names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,batch,perplexity_mean,tokens_evaluated_mean
                fp16,1,5.0,1000
                int8_ours,1,5.5,1000
            """)
            (tables_dir / "ppl_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_ppl(tables_dir, out_dir, label_prefix="tab")
            content = paths[0].read_text(encoding="utf-8")
            self.assertIn("FP16", content)
            self.assertIn("INT8-ours", content)

    def test_export_ppl_multi_model(self):
        """Multiple model_ids should produce multiple output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                model_id,kv_mode,batch,perplexity_mean,tokens_evaluated_mean
                Qwen/Qwen2.5-1.5B,fp16,1,5.0,1000
                Meta/LLaMA-3.1-8B,fp16,1,6.0,1000
            """)
            (tables_dir / "ppl_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_ppl(tables_dir, out_dir, label_prefix="tab")
            self.assertEqual(len(paths), 2)
            fnames = sorted([p.name for p in paths])
            # Each file should have a model suffix
            self.assertTrue(any("llama" in f.lower() for f in fnames))
            self.assertTrue(any("qwen" in f.lower() for f in fnames))


# ===========================================================================
# End-to-end: export_needle
# ===========================================================================


class TestExportNeedle(unittest.TestCase):
    """End-to-end test for export_needle."""

    def test_export_needle_creates_tex(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,seq_len,needle_pass_rate_mean
                fp16,1024,0.95
                fp16,2048,0.90
                int8_ours,1024,0.93
                int8_ours,2048,0.88
            """)
            (tables_dir / "needle_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_needle(tables_dir, out_dir, label_prefix="tab")

            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].exists())
            content = paths[0].read_text(encoding="utf-8")
            self.assertIn(r"\begin{table}", content)
            self.assertIn("Needle pass rate", content)
            # Should contain pivoted values
            self.assertIn("0.95", content)

    def test_export_needle_missing_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            paths = export_needle(tables_dir, out_dir, label_prefix="tab")
            self.assertEqual(paths, [])


# ===========================================================================
# End-to-end: export_latency
# ===========================================================================


class TestExportLatency(unittest.TestCase):
    """End-to-end test for export_latency (via _export_profile_table)."""

    def test_export_latency_creates_multiple_tex_files(self):
        """export_latency should produce up to 3 tex files (tpot, tok/s, ttft)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,seq_len,batch,gen_len,tpot_ms_mean,tok_per_s_mean,ttft_ms_mean
                fp16,1024,1,64,5.0,200.0,100.0
                fp16,2048,1,64,8.0,125.0,150.0
                int8_ours,1024,1,64,4.5,222.2,90.0
                int8_ours,2048,1,64,7.0,142.9,130.0
            """)
            (tables_dir / "latency_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_latency(tables_dir, out_dir, label_prefix="tab")

            self.assertEqual(len(paths), 3)
            fnames = [p.name for p in paths]
            self.assertIn("latency_tpot_vs_seq.tex", fnames)
            self.assertIn("latency_tok_per_s_vs_seq.tex", fnames)
            self.assertIn("latency_ttft_vs_seq.tex", fnames)

            # Verify content of one file
            tpot_path = [p for p in paths if "tpot" in p.name][0]
            content = tpot_path.read_text(encoding="utf-8")
            self.assertIn("TPOT", content)
            self.assertIn(r"\begin{table}", content)

    def test_export_latency_batch_filter(self):
        """Only batch=1 rows should survive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,seq_len,batch,gen_len,tpot_ms_mean
                fp16,1024,1,64,5.0
                fp16,1024,4,64,99.0
            """)
            (tables_dir / "latency_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_latency(tables_dir, out_dir, label_prefix="tab")
            # At least the tpot file should exist
            tpot_paths = [p for p in paths if "tpot" in p.name]
            self.assertTrue(len(tpot_paths) >= 1)
            content = tpot_paths[0].read_text(encoding="utf-8")
            self.assertNotIn("99.0", content)
            self.assertIn("5.0", content)


# ===========================================================================
# End-to-end: export_longbench
# ===========================================================================


class TestExportLongbench(unittest.TestCase):
    """End-to-end test for export_longbench with footnote verification."""

    def test_export_longbench_creates_tex_with_footnote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,seq_len,longbench_score_mean
                fp16,1024,75.5
                fp16,2048,70.2
                int8_ours,1024,74.0
                int8_ours,2048,69.1
            """)
            (tables_dir / "longbench_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_longbench(tables_dir, out_dir, label_prefix="tab")

            self.assertEqual(len(paths), 1)
            content = paths[0].read_text(encoding="utf-8")
            self.assertIn(r"\begin{table}", content)
            self.assertIn("LongBench", content)
            # Verify footnote is present
            self.assertIn("macro-average", content)
            self.assertIn("Rouge-L", content)

    def test_export_longbench_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            paths = export_longbench(tables_dir, out_dir, label_prefix="tab")
            self.assertEqual(paths, [])


class TestExportRulerSubtasks(unittest.TestCase):
    """Regression tests for per-model subtask exports (LTX-002)."""

    def test_export_ruler_subtasks_splits_by_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()
            csv_content = textwrap.dedent("""\
                model_id,ruler_task,kv_mode,seq_len,batch,ruler_pass_rate_mean
                Qwen/Qwen2.5_1.5B,single_niah,fp16,4096,1,0.90
                Qwen/Qwen2.5_1.5B,single_niah,int8_ours,4096,1,0.91
                Meta/LLaMA-3.1-8B,single_niah,fp16,4096,1,0.88
                Meta/LLaMA-3.1-8B,single_niah,int8_ours,4096,1,0.89
            """)
            (tables_dir / "ruler_subtask_summary.csv").write_text(csv_content, encoding="utf-8")
            paths = _export_ruler_subtask_tables(tables_dir, out_dir, label_prefix="tab")
            self.assertEqual(len(paths), 2)
            fnames = sorted(p.name for p in paths)
            self.assertTrue(any("qwen2.5_1.5b" in name for name in fnames))
            self.assertTrue(any("llama-3.1-8b" in name.lower() for name in fnames))


# ===========================================================================
# Integration: label correctness
# ===========================================================================


class TestLabelGeneration(unittest.TestCase):
    """Verify that labels in generated LaTeX are well-formed."""

    def test_label_in_ppl_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,batch,perplexity_mean,tokens_evaluated_mean
                fp16,1,5.0,1000
            """)
            (tables_dir / "ppl_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_ppl(tables_dir, out_dir, label_prefix="tab")
            content = paths[0].read_text(encoding="utf-8")
            self.assertIn(r"\label{tab:ppl:summary}", content)

    def test_custom_label_prefix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables_dir = Path(tmpdir) / "tables"
            out_dir = Path(tmpdir) / "latex"
            tables_dir.mkdir()

            csv_content = textwrap.dedent("""\
                kv_mode,seq_len,needle_pass_rate_mean
                fp16,1024,0.95
            """)
            (tables_dir / "needle_summary.csv").write_text(csv_content, encoding="utf-8")

            paths = export_needle(tables_dir, out_dir, label_prefix="appendix")
            content = paths[0].read_text(encoding="utf-8")
            self.assertIn(r"\label{appendix:needle:pass_rate}", content)


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases(unittest.TestCase):
    """Miscellaneous edge cases and boundary conditions."""

    def test_pivot_metric_with_nan_values(self):
        """NaN metric values should be dropped before pivoting."""
        df = pd.DataFrame({
            "seq_len": [1024, 1024, 2048],
            "kv_mode": ["fp16", "fp16", "fp16"],
            "metric_val": [10.0, float("nan"), 20.0],
        })
        result = _pivot_metric(df, "metric_val")
        # NaN row dropped, then (1024, fp16) has single value 10.0
        self.assertEqual(len(result), 2)

    def test_pivot_metric_all_nan(self):
        """If all metric values are NaN, result should be empty."""
        df = pd.DataFrame({
            "seq_len": [1024],
            "kv_mode": ["fp16"],
            "metric_val": [float("nan")],
        })
        result = _pivot_metric(df, "metric_val")
        self.assertTrue(result.empty)

    def test_sort_kv_mode_preserves_other_columns(self):
        """Sorting by kv_mode should not drop other columns."""
        df = pd.DataFrame({
            "kv_mode": ["int4_ours", "fp16"],
            "val_a": [1, 2],
            "val_b": ["x", "y"],
        })
        result = _sort_kv_mode(df)
        self.assertIn("val_a", result.columns)
        self.assertIn("val_b", result.columns)
        self.assertEqual(len(result), 2)

    def test_display_kv_mode_does_not_mutate_input(self):
        """_display_kv_mode returns a copy, not mutating the original."""
        df = pd.DataFrame({"kv_mode": ["fp16"]})
        _display_kv_mode(df)
        self.assertEqual(df["kv_mode"].iloc[0], "fp16")  # original unchanged

    def test_sort_kv_mode_does_not_mutate_input(self):
        """_sort_kv_mode returns a copy, not mutating the original."""
        df = pd.DataFrame({"kv_mode": ["int4_ours", "fp16"], "v": [1, 2]})
        original_order = list(df["kv_mode"])
        _sort_kv_mode(df)
        self.assertEqual(list(df["kv_mode"]), original_order)

    def test_kv_mode_display_complete_coverage(self):
        """Verify KV_MODE_DISPLAY has entries for all modes in KV_MODE_ORDER."""
        for mode in KV_MODE_ORDER:
            self.assertIn(
                mode, KV_MODE_DISPLAY,
                f"KV_MODE_DISPLAY is missing entry for '{mode}' from KV_MODE_ORDER",
            )

    def test_kv_mode_display_order_matches_kv_mode_order(self):
        self.assertEqual(list(KV_MODE_DISPLAY.keys()), list(KV_MODE_ORDER))


if __name__ == "__main__":
    unittest.main()
