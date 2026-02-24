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

KV_MODE_DISPLAY: Dict[str, str] = {
    "fp16": "FP16",
    "int8_baseline": "INT8-baseline",
    "int8_ours": "INT8-ours",
    "int8_fused": "INT8-fused",
    "int4_baseline": "INT4-baseline",
    "int4_ours": "INT4-ours",
    "int4_ours_mixed": "INT4-ours-mixed",
    "int4_fused": "INT4-fused",
    "kivi_style": "KIVI-style",
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

    if round_digits is not None:
        metric_cols = [c for c in pivot.columns if c != index_col]
        pivot[metric_cols] = pivot[metric_cols].round(round_digits)

    # Make seq_len an int when possible.
    try:
        pivot[index_col] = pivot[index_col].astype(int)
    except Exception:
        pass
    return pivot


def _latex_table_env(tabular_latex: str, *, caption: str, label: str) -> str:
    tabular_latex = tabular_latex.rstrip()
    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            rf"\caption{{{caption}}}",
            rf"\label{{{label}}}",
            r"\small",
            tabular_latex,
            r"\end{table}",
            "",
        ]
    )


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

    for metric, fname, caption, digits in metrics:
        pivot = _pivot_metric(df, metric, round_digits=digits)
        if pivot.empty:
            continue
        tabular = _to_latex_tabular(pivot, index=False)
        label = f"{label_prefix}:{label_category}:{metric}"
        latex = _latex_table_env(tabular, caption=caption, label=label)
        out_path = out_dir / fname
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

    pivot = _pivot_metric(df, "needle_pass_rate_mean", round_digits=2)
    if pivot.empty:
        return paths
    tabular = _to_latex_tabular(pivot, index=False)
    label = f"{label_prefix}:needle:pass_rate"
    latex = _latex_table_env(tabular, caption="Needle pass rate vs context length (%)", label=label)
    out_path = out_dir / "needle_pass_rate_vs_seq.tex"
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

    cols = [c for c in ["kv_mode", "perplexity_mean", "tokens_evaluated_mean"] if c in df.columns]
    if not cols:
        return paths
    out = df[cols].copy()
    if "perplexity_mean" in out.columns:
        out["perplexity_mean"] = pd.to_numeric(out["perplexity_mean"], errors="coerce").round(4)
    if "tokens_evaluated_mean" in out.columns:
        out["tokens_evaluated_mean"] = pd.to_numeric(out["tokens_evaluated_mean"], errors="coerce").round(0)
        try:
            out["tokens_evaluated_mean"] = out["tokens_evaluated_mean"].astype("Int64")
        except Exception:
            pass

    tabular = _to_latex_tabular(out, index=False)
    label = f"{label_prefix}:ppl:summary"
    latex = _latex_table_env(tabular, caption="Perplexity summary (kv_cache mode)", label=label)
    out_path = out_dir / "ppl_summary.tex"
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

    pivot = _pivot_metric(df, "longbench_score_mean", round_digits=2)
    if pivot.empty:
        return paths
    tabular = _to_latex_tabular(pivot, index=False)
    label = f"{label_prefix}:longbench:score"
    latex = _latex_table_env(
        tabular,
        caption="LongBench macro score vs context length (%)",
        label=label,
    )
    out_path = out_dir / "longbench_score_vs_seq.tex"
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

    pivot = _pivot_metric(df, "ruler_pass_rate_mean", round_digits=2)
    if pivot.empty:
        return paths
    tabular = _to_latex_tabular(pivot, index=False)
    label = f"{label_prefix}:ruler:pass_rate"
    latex = _latex_table_env(
        tabular,
        caption="RULER pass rate vs context length (%)",
        label=label,
    )
    out_path = out_dir / "ruler_pass_rate_vs_seq.tex"
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
    out = df[keep_cols].copy()
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
    label = f"{label_prefix}:main:claims32k"
    latex = _latex_table_env(
        tabular,
        caption="Main claims at long context (32K or nearest available point)",
        label=label,
    )
    out_path = out_dir / "main_claims_32k.tex"
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
    df = df[df["baseline_mode"].isin(["int8_baseline", "int4_fused"])]
    df = df[df["challenger_mode"].isin(["int8_ours", "int4_ours"])]
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

    out = df.copy()
    out["baseline_mode"] = out["baseline_mode"].map(KV_MODE_DISPLAY).fillna(out["baseline_mode"])
    out["challenger_mode"] = out["challenger_mode"].map(KV_MODE_DISPLAY).fillna(out["challenger_mode"])
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
        if c in out.columns
    ]
    out = out[keep].copy()
    for col, digits in [("baseline_value", 4), ("challenger_value", 4), ("gain_pct", 2)]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(digits)

    tabular = _to_latex_tabular(out, index=False)
    label = f"{label_prefix}:summary:gain"
    latex = _latex_table_env(
        tabular,
        caption="Relative gain summary on key pairs (positive gain means challenger is better)",
        label=label,
    )
    out_path = out_dir / "relative_gain_summary.tex"
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
