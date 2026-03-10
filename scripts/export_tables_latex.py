#!/usr/bin/env python3
"""
Export aggregated CSV summary tables to LaTeX tables (booktabs).

This script is intended to take the outputs from `scripts/aggregate_results.py`
and convert them into thesis-ready LaTeX `table` environments.

Inputs (expected under --tables_dir):
  - latency_summary.csv
  - memory_summary.csv
  - needle_summary.csv
  - ppl_summary.csv
  - longbench_summary.csv
  - ruler_summary.csv

Outputs (written under --out_dir):
  - latency_tpot_vs_seq.tex
  - latency_tok_per_s_vs_seq.tex
  - latency_ttft_vs_seq.tex
  - memory_kv_cache_mem_vs_seq.tex
  - memory_gpu_peak_vs_seq.tex
  - needle_pass_rate_vs_seq.tex
  - ppl_summary.tex
  - longbench_score_vs_seq.tex
  - ruler_pass_rate_vs_seq.tex
  - all_tables.tex (\\input includes)

Notes:
  - Requires LaTeX packages: booktabs
  - For wide tables, you may want to wrap with \\resizebox{\\linewidth}{!}{...}
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

from config_utils import KV_MODE_ORDER

logger = logging.getLogger(__name__)


def _sanitize_label(text: str) -> str:
    """Remove or replace characters that are unsafe inside LaTeX \\label{}."""
    # Strip backslashes and braces which would break \label{...}
    text = re.sub(r'[{}\\#$%&^~]', '', text)
    # Collapse whitespace to underscores
    text = re.sub(r'\s+', '_', text.strip())
    return text


def _latex_escape(text: str) -> str:
    """Escape text for safe insertion into LaTeX caption/table content."""
    out = str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def _pretty_kv_mode_name(mode: str) -> str:
    mode = str(mode)
    if mode == "fp16":
        return "FP16"
    if mode == "kivi_style":
        return "KIVI-style"
    if mode.startswith("int") and "_" in mode:
        bit, suffix = mode.split("_", 1)
        return f"{bit.upper()}-{suffix.replace('_', '-')}"
    return mode


# LTX-014: derive display mapping from the single source of truth KV_MODE_ORDER.
KV_MODE_DISPLAY: Dict[str, str] = {
    mode: _pretty_kv_mode_name(mode) for mode in KV_MODE_ORDER
}


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        logger.warning("Failed to read CSV %s: %s", path, exc)
        return pd.DataFrame()


def _sort_kv_mode(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "kv_mode" not in df.columns:
        return df
    order = {m: i for i, m in enumerate(KV_MODE_ORDER)}
    df = df.copy()
    df["_kv_mode_rank"] = df["kv_mode"].map(order).fillna(9999).astype(int)
    df = df.sort_values(["_kv_mode_rank", "kv_mode"])
    return df.drop(columns=["_kv_mode_rank"])


def _display_kv_mode(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "kv_mode" not in df.columns:
        return df
    df = df.copy()
    df["kv_mode"] = df["kv_mode"].map(KV_MODE_DISPLAY).fillna(df["kv_mode"])
    return df


def _split_by_model(
    df: pd.DataFrame,
) -> List[tuple]:
    """Split a DataFrame by model_id for per-model table generation.

    Returns a list of ``(model_suffix, model_label, sub_df)`` tuples.
    When only one model is present (or model_id is absent), returns a single
    entry with empty suffix and label so callers can iterate uniformly.

    - ``model_suffix``: filesystem-safe string for filenames (e.g. ``"_qwen2.5_1.5b"``),
      empty when there is only one model.
    - ``model_label``: LaTeX-safe string for labels/captions, empty for single model.
    """
    if "model_id" not in df.columns or df["model_id"].nunique() <= 1:
        return [("", "", df)]

    result: List[tuple] = []
    for model_id in sorted(df["model_id"].dropna().unique()):
        sub = df[df["model_id"] == model_id].copy()
        # Build filesystem-safe suffix: "Qwen/Qwen2.5-1.5B-Instruct" → "_qwen2.5_1.5b_instruct"
        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", str(model_id)).strip("_").lower()
        suffix = f"_{safe}"
        # Short display name for captions: keep text after last "/"
        short_name = str(model_id).rsplit("/", 1)[-1]
        label = f" ({_latex_escape(short_name)})"
        result.append((suffix, label, sub))
    return result


def _pivot_metric(
    df: pd.DataFrame,
    metric_col: str,
    *,
    index_col: str = "seq_len",
    columns_col: str = "kv_mode",
    round_digits: Optional[int] = None,
) -> pd.DataFrame:
    if df.empty or metric_col not in df.columns:
        return pd.DataFrame()

    keep = [c for c in [index_col, columns_col, metric_col] if c in df.columns]
    sub = df[keep].copy()
    sub[index_col] = pd.to_numeric(sub[index_col], errors="coerce")
    sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
    sub = sub.dropna(subset=[index_col, columns_col, metric_col])

    # Warn if model_id column exists: groupby will silently average across models.
    if "model_id" in df.columns and df["model_id"].nunique() > 1:
        logger.warning(
            "pivot of '%s' contains %d distinct model_id values; "
            "groupby().mean() will average across models. Consider filtering first.",
            metric_col,
            df["model_id"].nunique(),
        )

    # Handle duplicates defensively (e.g., multiple clip/group configs in one tables_dir).
    sub = (
        sub.groupby([index_col, columns_col], dropna=False, as_index=False)[metric_col]
        .mean()
    )

    pivot = sub.pivot(index=index_col, columns=columns_col, values=metric_col).reset_index()
    pivot = pivot.sort_values(index_col)

    # LTX-001: enforce canonical kv_mode column order instead of lexicographic order.
    metric_cols = [c for c in pivot.columns if c != index_col]
    raw_rank = {mode: idx for idx, mode in enumerate(KV_MODE_ORDER)}
    display_rank = {KV_MODE_DISPLAY[mode]: idx for idx, mode in enumerate(KV_MODE_ORDER)}

    def _rank_col(col: object) -> tuple[int, str]:
        key = str(col)
        if key in raw_rank:
            return raw_rank[key], key
        if key in display_rank:
            return display_rank[key], key
        return len(KV_MODE_ORDER) + 1, key

    ordered_metric_cols = sorted(metric_cols, key=_rank_col)
    pivot = pivot[[index_col] + ordered_metric_cols]

    if round_digits is not None:
        metric_cols = [c for c in pivot.columns if c != index_col]
        pivot[metric_cols] = pivot[metric_cols].round(round_digits)

    # Make seq_len an int when possible.
    try:
        pivot[index_col] = pivot[index_col].astype(int)
    except Exception:
        pass
    return pivot


def _latex_table_env(
    tabular_latex: str,
    *,
    caption: str,
    label: str,
    footnote: Optional[str] = None,
) -> str:
    tabular_latex = tabular_latex.rstrip()
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\small",
        tabular_latex,
    ]
    if footnote:
        lines.append(r"\vspace{1mm}")
        lines.append(rf"\parbox{{\linewidth}}{{\footnotesize {footnote}}}")
    lines.append(r"\end{table}")
    lines.append("")
    return "\n".join(lines)


def _to_latex_tabular(df: pd.DataFrame, *, index: bool = False) -> str:
    if df.empty:
        return ""
    return df.to_latex(
        index=index,
        escape=True,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _export_profile_table(
    tables_dir: Path,
    out_dir: Path,
    *,
    label_prefix: str,
    csv_name: str,
    label_category: str,
    metrics: List[tuple],
) -> List[Path]:
    """Shared logic for exporting latency / memory profile tables.

    Parameters
    ----------
    csv_name : str
        Filename under *tables_dir* (e.g. ``"latency_summary.csv"``).
    label_category : str
        Category token inserted into ``\\label`` (e.g. ``"latency"``).
    metrics : list of (metric_col, filename, caption, round_digits) tuples.
    """
    paths: List[Path] = []
    src = tables_dir / csv_name
    df = _read_csv(src)
    if df.empty:
        return paths

    # Default thesis tables assume batch=1 and fixed curve gen_len=64.
    if "batch" in df.columns:
        df = df[pd.to_numeric(df["batch"], errors="coerce") == 1]
    if "gen_len" in df.columns:
        gen = pd.to_numeric(df["gen_len"], errors="coerce")
        if (gen == 64).any():
            df = df[gen == 64]

    df = _sort_kv_mode(df)
    df = _display_kv_mode(df)

    for model_suffix, model_label, model_df in _split_by_model(df):
        for metric, fname, caption, digits in metrics:
            pivot = _pivot_metric(model_df, metric, round_digits=digits)
            if pivot.empty:
                continue
            tabular = _to_latex_tabular(pivot, index=False)
            safe_suffix = _sanitize_label(model_suffix)
            label = f"{label_prefix}:{label_category}:{metric}{safe_suffix}"
            # Insert model suffix into filename: "foo.tex" → "foo_model.tex"
            stem, ext = fname.rsplit(".", 1) if "." in fname else (fname, "tex")
            out_fname = f"{stem}{model_suffix}.{ext}" if model_suffix else fname
            latex = _latex_table_env(
                tabular,
                caption=f"{caption}{model_label}",
                label=label,
            )
            out_path = out_dir / out_fname
            _write(out_path, latex)
            paths.append(out_path)
    return paths


def export_latency(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    return _export_profile_table(
        tables_dir,
        out_dir,
        label_prefix=label_prefix,
        csv_name="latency_summary.csv",
        label_category="latency",
        metrics=[
            ("tpot_ms_mean", "latency_tpot_vs_seq.tex", "TPOT vs context length (ms/token)", 2),
            ("tok_per_s_mean", "latency_tok_per_s_vs_seq.tex", "Throughput vs context length (tok/s)", 2),
            ("ttft_ms_mean", "latency_ttft_vs_seq.tex", "TTFT vs context length (ms)", 2),
        ],
    )


def export_memory(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    return _export_profile_table(
        tables_dir,
        out_dir,
        label_prefix=label_prefix,
        csv_name="memory_summary.csv",
        label_category="memory",
        metrics=[
            ("kv_cache_mem_mb_mean", "memory_kv_cache_mem_vs_seq.tex", "KV cache resident memory vs context length (MB)", 0),
            ("gpu_mem_peak_mb_mean", "memory_gpu_peak_vs_seq.tex", "Peak GPU memory vs context length (MB)", 0),
        ],
    )


def export_needle(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    paths: List[Path] = []
    src = tables_dir / "needle_summary.csv"
    df = _read_csv(src)
    if df.empty:
        return paths

    df = _sort_kv_mode(df)
    df = _display_kv_mode(df)

    for model_suffix, model_label, model_df in _split_by_model(df):
        pivot = _pivot_metric(model_df, "needle_pass_rate_mean", round_digits=2)
        if pivot.empty:
            continue
        tabular = _to_latex_tabular(pivot, index=False)
        safe_suffix = _sanitize_label(model_suffix)
        label = f"{label_prefix}:needle:pass_rate{safe_suffix}"
        latex = _latex_table_env(
            tabular,
            caption=f"Needle pass rate vs context length (\\%){model_label}",
            label=label,
        )
        fname = f"needle_pass_rate_vs_seq{model_suffix}.tex" if model_suffix else "needle_pass_rate_vs_seq.tex"
        out_path = out_dir / fname
        _write(out_path, latex)
        paths.append(out_path)
    return paths


def export_ppl(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    paths: List[Path] = []
    src = tables_dir / "ppl_summary.csv"
    df = _read_csv(src)
    if df.empty:
        return paths

    if "batch" in df.columns:
        df = df[pd.to_numeric(df["batch"], errors="coerce") == 1]

    df = _sort_kv_mode(df)
    df = _display_kv_mode(df)

    for model_suffix, model_label, model_df in _split_by_model(df):
        cols = [c for c in ["kv_mode", "perplexity_mean", "tokens_evaluated_mean"] if c in model_df.columns]
        if not cols:
            continue
        out = model_df[cols].copy()
        if "perplexity_mean" in out.columns:
            out["perplexity_mean"] = pd.to_numeric(out["perplexity_mean"], errors="coerce").round(4)
        if "tokens_evaluated_mean" in out.columns:
            out["tokens_evaluated_mean"] = pd.to_numeric(out["tokens_evaluated_mean"], errors="coerce").round(0)
            try:
                out["tokens_evaluated_mean"] = out["tokens_evaluated_mean"].astype("Int64")
            except Exception:
                pass

        tabular = _to_latex_tabular(out, index=False)
        safe_suffix = _sanitize_label(model_suffix)
        label = f"{label_prefix}:ppl:summary{safe_suffix}"
        latex = _latex_table_env(
            tabular,
            caption=f"Perplexity summary (kv\\_cache mode){model_label}",
            label=label,
        )
        fname = f"ppl_summary{model_suffix}.tex" if model_suffix else "ppl_summary.tex"
        out_path = out_dir / fname
        _write(out_path, latex)
        paths.append(out_path)
    return paths


def export_longbench(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    paths: List[Path] = []
    src = tables_dir / "longbench_summary.csv"
    df = _read_csv(src)
    if df.empty:
        return paths

    if "batch" in df.columns:
        batch = pd.to_numeric(df["batch"], errors="coerce")
        if (batch == 1).any():
            df = df[batch == 1]

    df = _sort_kv_mode(df)
    df = _display_kv_mode(df)

    longbench_footnote = (
        "LongBench score is the macro-average of task-level official metrics "
        "(Rouge-L for summarization, token-F1 for question answering, "
        "Accuracy for classification, Edit Similarity for code completion)."
    )

    for model_suffix, model_label, model_df in _split_by_model(df):
        pivot = _pivot_metric(model_df, "longbench_score_mean", round_digits=2)
        if pivot.empty:
            continue
        tabular = _to_latex_tabular(pivot, index=False)
        safe_suffix = _sanitize_label(model_suffix)
        label = f"{label_prefix}:longbench:score{safe_suffix}"
        latex = _latex_table_env(
            tabular,
            caption=f"LongBench macro score vs context length (\\%){model_label}",
            label=label,
            footnote=longbench_footnote,
        )
        fname = f"longbench_score_vs_seq{model_suffix}.tex" if model_suffix else "longbench_score_vs_seq.tex"
        out_path = out_dir / fname
        _write(out_path, latex)
        paths.append(out_path)
    return paths


def _export_ruler_subtask_tables(
    tables_dir: Path,
    out_dir: Path,
    *,
    label_prefix: str,
    batch_filter_df: Optional[pd.DataFrame] = None,
) -> List[Path]:
    """Export per-subtask RULER tables if ruler_subtask_summary.csv is available.

    Returns a list of written paths (empty if subtask data is unavailable).
    """
    paths: List[Path] = []
    subtask_src = tables_dir / "ruler_subtask_summary.csv"
    stdf = _read_csv(subtask_src)
    if stdf.empty or "ruler_task" not in stdf.columns:
        return paths

    if "batch" in stdf.columns:
        batch = pd.to_numeric(stdf["batch"], errors="coerce")
        if (batch == 1).any():
            stdf = stdf[batch == 1]

    # Canonical subtask display names
    subtask_display = {
        "single_niah": "S-NIAH",
        "multi_keys_niah": "MK-NIAH",
        "variable_tracking": "VT",
        "common_words_extraction": "CWE",
    }

    stdf = _sort_kv_mode(stdf)
    stdf = _display_kv_mode(stdf)

    for model_suffix, model_label, model_df in _split_by_model(stdf):
        for task_key, task_label in subtask_display.items():
            task_df = model_df[model_df["ruler_task"] == task_key]
            if task_df.empty:
                continue
            pivot = _pivot_metric(task_df, "ruler_pass_rate_mean", round_digits=2)
            if pivot.empty:
                continue
            tabular = _to_latex_tabular(pivot, index=False)
            safe_key = _sanitize_label(task_key)
            safe_suffix = _sanitize_label(model_suffix)
            label = f"{label_prefix}:ruler:{safe_key}{safe_suffix}"
            latex = _latex_table_env(
                tabular,
                caption=f"RULER {task_label} pass rate vs context length (\\%){model_label}",
                label=label,
            )
            fname = (
                f"ruler_{safe_key}_vs_seq{model_suffix}.tex"
                if model_suffix
                else f"ruler_{safe_key}_vs_seq.tex"
            )
            out_path = out_dir / fname
            _write(out_path, latex)
            paths.append(out_path)

    return paths


def export_ruler(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    paths: List[Path] = []
    src = tables_dir / "ruler_summary.csv"
    df = _read_csv(src)
    if df.empty:
        return paths

    if "batch" in df.columns:
        batch = pd.to_numeric(df["batch"], errors="coerce")
        if (batch == 1).any():
            df = df[batch == 1]

    df = _sort_kv_mode(df)
    df = _display_kv_mode(df)

    # --- Per-subtask tables (from ruler_subtask_summary.csv if available) ---
    subtask_paths = _export_ruler_subtask_tables(
        tables_dir, out_dir, label_prefix=label_prefix,
    )
    paths.extend(subtask_paths)

    # --- Overall pass rate table (per-model when multiple models present) ---
    # TODO(EXP-003): When ruler_subtask_summary.csv is available, the per-subtask
    # tables above will provide S-NIAH / MK-NIAH / VT / CWE breakdowns.  Until
    # then, include a footnote directing readers to the full aggregated results.
    ruler_footnote: Optional[str] = None
    if not subtask_paths:
        ruler_footnote = (
            "This table shows overall pass rate only. "
            "Detailed per-subtask results (S-NIAH, MK-NIAH, VT, CWE) "
            "are available in the full aggregated results "
            "(\\texttt{ruler\\_subtask\\_summary.csv})."
        )

    for model_suffix, model_label, model_df in _split_by_model(df):
        pivot = _pivot_metric(model_df, "ruler_pass_rate_mean", round_digits=2)
        if pivot.empty:
            continue
        tabular = _to_latex_tabular(pivot, index=False)
        safe_suffix = _sanitize_label(model_suffix)
        label = f"{label_prefix}:ruler:pass_rate{safe_suffix}"
        latex = _latex_table_env(
            tabular,
            caption=f"RULER pass rate vs context length (\\%){model_label}",
            label=label,
            footnote=ruler_footnote,
        )
        fname = f"ruler_pass_rate_vs_seq{model_suffix}.tex" if model_suffix else "ruler_pass_rate_vs_seq.tex"
        out_path = out_dir / fname
        _write(out_path, latex)
        paths.append(out_path)
    return paths


def export_main_claims(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    paths: List[Path] = []
    src = tables_dir / "thesis_main_claims_32k.csv"
    df = _read_csv(src)
    if df.empty:
        return paths
    df = _sort_kv_mode(df)
    df = _display_kv_mode(df)

    keep_cols = [
        c
        for c in [
            "kv_mode",
            "claim_seq_len",
            "tpot_ms_mean",
            "kv_cache_mem_mb_mean",
            "needle_pass_rate_mean",
            "needle_exact_match_rate_mean",
            "longbench_score_mean",
            "ruler_pass_rate_mean",
            "perplexity_mean",
        ]
        if c in df.columns
    ]
    if not keep_cols:
        return paths

    for model_suffix, model_label, model_df in _split_by_model(df):
        out = model_df[keep_cols].copy()
        for col, digits in [
            ("tpot_ms_mean", 2),
            ("kv_cache_mem_mb_mean", 0),
            ("needle_pass_rate_mean", 2),
            ("needle_exact_match_rate_mean", 2),
            ("longbench_score_mean", 2),
            ("ruler_pass_rate_mean", 2),
            ("perplexity_mean", 4),
        ]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce").round(digits)

        tabular = _to_latex_tabular(out, index=False)
        safe_suffix = _sanitize_label(model_suffix)
        label = f"{label_prefix}:main:claims32k{safe_suffix}"
        latex = _latex_table_env(
            tabular,
            caption=f"Main claims at long context (32K or nearest available point){model_label}",
            label=label,
        )
        fname = f"main_claims_32k{model_suffix}.tex" if model_suffix else "main_claims_32k.tex"
        out_path = out_dir / fname
        _write(out_path, latex)
        paths.append(out_path)
    return paths


def export_relative_gain(tables_dir: Path, out_dir: Path, *, label_prefix: str) -> List[Path]:
    paths: List[Path] = []
    src = tables_dir / "relative_gain_summary.csv"
    df = _read_csv(src)
    if df.empty:
        return paths

    # Keep thesis-critical pairs and metrics for a compact table.
    df = df[
        df["metric"].isin(
            [
                "tpot_ms",
                "kv_cache_mem_mb",
                "perplexity",
                "needle_pass_rate",
                "longbench_score",
                "ruler_pass_rate",
            ]
        )
    ]
    df = df[df["baseline_mode"].isin(["int8_baseline", "int4_baseline", "int4_fused", "kivi_style"])]
    df = df[df["challenger_mode"].isin(["int8_ours", "int4_ours", "int8_baseline"])]
    if "seq_len" in df.columns:
        seq = pd.to_numeric(df["seq_len"], errors="coerce")
        if (seq == 32704).any():
            df = df[seq == 32704]
    if "batch" in df.columns:
        batch = pd.to_numeric(df["batch"], errors="coerce")
        if (batch == 1).any():
            df = df[batch == 1]
    if df.empty:
        return paths

    df["baseline_mode"] = df["baseline_mode"].map(KV_MODE_DISPLAY).fillna(df["baseline_mode"])
    df["challenger_mode"] = df["challenger_mode"].map(KV_MODE_DISPLAY).fillna(df["challenger_mode"])

    for model_suffix, model_label, model_df in _split_by_model(df):
        keep = [
            c
            for c in [
                "metric",
                "seq_len",
                "baseline_mode",
                "challenger_mode",
                "baseline_value",
                "challenger_value",
                "gain_pct",
            ]
            if c in model_df.columns
        ]
        out = model_df[keep].copy()
        for col, digits in [("baseline_value", 4), ("challenger_value", 4), ("gain_pct", 2)]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce").round(digits)

        tabular = _to_latex_tabular(out, index=False)
        safe_suffix = _sanitize_label(model_suffix)
        label = f"{label_prefix}:summary:gain{safe_suffix}"
        latex = _latex_table_env(
            tabular,
            caption=f"Relative gain summary on key pairs (positive gain means challenger is better){model_label}",
            label=label,
        )
        fname = f"relative_gain_summary{model_suffix}.tex" if model_suffix else "relative_gain_summary.tex"
        out_path = out_dir / fname
        _write(out_path, latex)
        paths.append(out_path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Export aggregated CSV tables to LaTeX")
    parser.add_argument("--tables_dir", type=str, default="results/tables")
    parser.add_argument("--out_dir", type=str, default="results/latex_tables")
    parser.add_argument("--label_prefix", type=str, default="tab")
    args = parser.parse_args()

    tables_dir = Path(args.tables_dir)
    out_dir = Path(args.out_dir)
    label_prefix = _sanitize_label(str(args.label_prefix).strip()) or "tab"

    if not tables_dir.exists():
        print(f"tables_dir not found: {tables_dir}")
        return 2

    written: List[Path] = []
    written += export_latency(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_memory(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_needle(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_ppl(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_longbench(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_ruler(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_main_claims(tables_dir, out_dir, label_prefix=label_prefix)
    written += export_relative_gain(tables_dir, out_dir, label_prefix=label_prefix)

    # Convenience include file.
    all_tex = out_dir / "all_tables.tex"
    lines: List[str] = [
        "% Auto-generated by scripts/export_tables_latex.py",
        "% Requires: \\usepackage{booktabs}",
        "",
    ]
    for path in written:
        rel = path.name
        lines.append(rf"\input{{{rel}}}")
    lines.append("")
    _write(all_tex, "\n".join(lines))

    print(f"Wrote {len(written)} table(s) to: {out_dir}")
    print(f"Wrote include file to: {all_tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
