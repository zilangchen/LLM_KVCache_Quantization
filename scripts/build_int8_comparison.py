#!/usr/bin/env python3
"""
Build INT8-ours vs INT8-baseline comparison table for EMNLP 2026 paper.

Task A5 (B11): Cross-model INT8 analysis at 32K sequence length.

Reads aggregated CSVs from a results tag (default: emnlp_final_raw) and
produces:
  1. A concise comparison CSV  (int8_comparison_32k.csv)
  2. A LaTeX table              (int8_comparison_32k.tex)

Columns in output:
  Model | Metric | INT8-baseline (mean +/- std) | INT8-ours (mean +/- std) |
  Delta | Rel. Delta (%) | p-value | Significant (BH-FDR alpha=0.05)

Usage:
  python scripts/build_int8_comparison.py \
      --tables_dir results/emnlp_final_raw/tables \
      --out_dir results/emnlp_final_raw/analysis

  # Or use defaults (auto-detect latest results tag):
  python scripts/build_int8_comparison.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

MODELS = [
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
]

MODEL_SHORT = {
    "Qwen/Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5-7B",
    "meta-llama/Llama-3.1-8B-Instruct": "LLaMA-3.1-8B",
}

# Primary seq_len for the comparison (32K context)
TARGET_SEQ_LEN = 32704

# Metrics to extract: (metric_name, source_csv, value_col, std_col, higher_is_better, filter_kwargs)
METRIC_DEFS: List[Dict[str, Any]] = [
    {
        "label": "PPL",
        "source": "ppl_summary.csv",
        "mean_col": "perplexity_mean",
        "std_col": "perplexity_std",
        "count_col": "perplexity_count",
        "filters": {"kv_mode": None, "seq_len": 32768},  # PPL uses 32768 not 32704
        "higher_is_better": False,
        "fmt": ".4f",
    },
    {
        "label": "Needle Pass Rate (%)",
        "source": "needle_summary.csv",
        "mean_col": "needle_pass_rate_mean",
        "std_col": "needle_pass_rate_std",
        "count_col": "needle_pass_rate_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN},
        "higher_is_better": True,
        "fmt": ".1f",
    },
    {
        "label": "LongBench Score",
        "source": "longbench_summary.csv",
        "mean_col": "longbench_score_mean",
        "std_col": "longbench_score_std",
        "count_col": "longbench_score_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN},
        "higher_is_better": True,
        "fmt": ".5f",
    },
    {
        "label": "LongBench F1 Macro",
        "source": "longbench_summary.csv",
        "mean_col": "longbench_f1_macro_mean",
        "std_col": "longbench_f1_macro_std",
        "count_col": "longbench_f1_macro_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN},
        "higher_is_better": True,
        "fmt": ".3f",
    },
    {
        "label": "RULER Pass Rate (%)",
        "source": "ruler_summary.csv",
        "mean_col": "ruler_pass_rate_mean",
        "std_col": "ruler_pass_rate_std",
        "count_col": "ruler_pass_rate_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN},
        "higher_is_better": True,
        "fmt": ".2f",
    },
    {
        "label": "TPOT (ms)",
        "source": "latency_summary.csv",
        "mean_col": "tpot_ms_mean",
        "std_col": "tpot_ms_std",
        "count_col": "tpot_ms_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN, "batch": 1, "gen_len": 64},
        "higher_is_better": False,
        "fmt": ".2f",
    },
    {
        "label": "Tok/s",
        "source": "latency_summary.csv",
        "mean_col": "tok_per_s_mean",
        "std_col": "tok_per_s_std",
        "count_col": "tok_per_s_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN, "batch": 1, "gen_len": 64},
        "higher_is_better": True,
        "fmt": ".2f",
    },
    {
        "label": "GPU Peak (MB)",
        "source": "memory_summary.csv",
        "mean_col": "gpu_mem_peak_mb_mean",
        "std_col": "gpu_mem_peak_mb_std",
        "count_col": "gpu_mem_peak_mb_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN, "batch": 1, "gen_len": 64},
        "higher_is_better": False,
        "fmt": ".0f",
    },
    {
        "label": "KV Cache (MB)",
        "source": "memory_summary.csv",
        "mean_col": "kv_cache_mem_mb_mean",
        "std_col": "kv_cache_mem_mb_std",
        "count_col": "kv_cache_mem_mb_count",
        "filters": {"kv_mode": None, "seq_len": TARGET_SEQ_LEN, "batch": 1, "gen_len": 64},
        "higher_is_better": False,
        "fmt": ".0f",
    },
]

# Significance metric name mapping (significance_summary uses different names)
SIG_METRIC_MAP = {
    "PPL": "perplexity",
    "Needle Pass Rate (%)": "needle_pass_rate",
    "LongBench Score": "longbench_score",
    "LongBench F1 Macro": "longbench_f1_macro",
    "RULER Pass Rate (%)": "ruler_pass_rate",
    "TPOT (ms)": "tpot_ms",
    "Tok/s": "tok_per_s",
    "GPU Peak (MB)": "gpu_mem_peak_mb",
    "KV Cache (MB)": "kv_cache_mem_mb",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_csv(tables_dir: Path, filename: str) -> pd.DataFrame:
    """Load a CSV, warn if missing."""
    path = tables_dir / filename
    if not path.exists():
        logger.warning("Missing table: %s", path)
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Normalize column types
    for col in ("seq_len", "batch", "gen_len"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _extract_value(
    df: pd.DataFrame,
    model_id: str,
    kv_mode: str,
    mean_col: str,
    std_col: str,
    count_col: str,
    filters: Dict[str, Any],
) -> Tuple[Optional[float], Optional[float], Optional[int]]:
    """Extract mean, std, count for a given model/mode/filters combination.

    For int8_ours with multiple group_size configs, take the row with the
    largest count (most seeds) as the primary result.
    """
    mask = (df["model_id"] == model_id) & (df["kv_mode"] == kv_mode)
    for col, val in filters.items():
        if col == "kv_mode" or val is None:
            continue
        if col in df.columns:
            mask &= df[col] == val
    subset = df.loc[mask]
    if subset.empty:
        return None, None, None

    # If multiple rows (e.g., different group_size for int8_ours),
    # prefer the one with the highest count (most data points)
    if count_col in subset.columns and len(subset) > 1:
        subset = subset.sort_values(count_col, ascending=False)

    row = subset.iloc[0]
    mean_val = float(row[mean_col]) if pd.notna(row.get(mean_col)) else None
    std_val = float(row[std_col]) if std_col in row.index and pd.notna(row.get(std_col)) else None
    count_val = int(row[count_col]) if count_col in row.index and pd.notna(row.get(count_col)) else None
    return mean_val, std_val, count_val


def _load_significance(
    tables_dir: Path,
) -> pd.DataFrame:
    """Load significance_summary.csv, filtered to int8_baseline vs int8_ours."""
    df = _load_csv(tables_dir, "significance_summary.csv")
    if df.empty:
        return df
    mask = (df["baseline_mode"] == "int8_baseline") & (df["challenger_mode"] == "int8_ours")
    return df.loc[mask].copy()


def _get_significance(
    sig_df: pd.DataFrame,
    model_id: str,
    metric_label: str,
    seq_len: int,
) -> Tuple[Optional[float], Optional[bool]]:
    """Return (p_value, is_significant) from significance summary."""
    if sig_df.empty:
        return None, None

    sig_metric = SIG_METRIC_MAP.get(metric_label)
    if sig_metric is None:
        return None, None

    mask = (
        (sig_df["model_id"] == model_id)
        & (sig_df["metric"] == sig_metric)
    )
    # seq_len matching: significance may use string or int
    if "seq_len" in sig_df.columns:
        sig_df_copy = sig_df.copy()
        sig_df_copy["seq_len"] = pd.to_numeric(sig_df_copy["seq_len"], errors="coerce")
        mask = mask & (sig_df_copy["seq_len"] == seq_len)
        subset = sig_df_copy.loc[mask]
    else:
        subset = sig_df.loc[mask]

    if subset.empty:
        return None, None

    row = subset.iloc[0]
    p_val = float(row["p_value"]) if pd.notna(row.get("p_value")) else None
    sig = row.get("significant_q_alpha", "")
    is_sig = str(sig).strip().lower() == "true"
    return p_val, is_sig


def _fmt(val: Optional[float], fmt: str) -> str:
    """Format a float or return '--'."""
    if val is None:
        return "--"
    return f"{val:{fmt}}"


def _fmt_mean_std(mean: Optional[float], std: Optional[float], fmt: str) -> str:
    """Format mean +/- std."""
    if mean is None:
        return "--"
    m = f"{mean:{fmt}}"
    if std is not None and std > 0:
        s = f"{std:{fmt}}"
        return f"{m} +/- {s}"
    return m


def _latex_escape(text: str) -> str:
    """Escape underscores for LaTeX."""
    return text.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


# ── Main Logic ─────────────────────────────────────────────────────────────────

def build_comparison(tables_dir: Path) -> pd.DataFrame:
    """Build the full comparison DataFrame."""
    # Pre-load all source CSVs
    csv_cache: Dict[str, pd.DataFrame] = {}
    for mdef in METRIC_DEFS:
        src = mdef["source"]
        if src not in csv_cache:
            csv_cache[src] = _load_csv(tables_dir, src)

    # Load significance
    sig_df = _load_significance(tables_dir)

    rows = []
    for model_id in MODELS:
        model_short = MODEL_SHORT[model_id]
        for mdef in METRIC_DEFS:
            df = csv_cache[mdef["source"]]
            if df.empty:
                continue

            label = mdef["label"]
            fmt = mdef["fmt"]
            higher_is_better = mdef["higher_is_better"]

            # Determine seq_len for significance lookup
            filters_seq = mdef["filters"].get("seq_len", TARGET_SEQ_LEN)

            # Extract baseline
            bl_mean, bl_std, bl_count = _extract_value(
                df, model_id, "int8_baseline",
                mdef["mean_col"], mdef["std_col"], mdef["count_col"],
                mdef["filters"],
            )
            # Extract ours
            ours_mean, ours_std, ours_count = _extract_value(
                df, model_id, "int8_ours",
                mdef["mean_col"], mdef["std_col"], mdef["count_col"],
                mdef["filters"],
            )

            # Compute delta and relative delta
            delta = None
            rel_delta_pct = None
            direction = ""
            if bl_mean is not None and ours_mean is not None:
                delta = ours_mean - bl_mean
                if bl_mean != 0:
                    rel_delta_pct = (delta / abs(bl_mean)) * 100.0
                # Direction interpretation
                if higher_is_better:
                    direction = "better" if delta > 0 else ("worse" if delta < 0 else "same")
                else:
                    direction = "better" if delta < 0 else ("worse" if delta > 0 else "same")

            # Significance
            p_val, is_sig = _get_significance(sig_df, model_id, label, filters_seq)

            rows.append({
                "model": model_short,
                "model_id": model_id,
                "metric": label,
                "int8_baseline_mean": bl_mean,
                "int8_baseline_std": bl_std,
                "int8_baseline_n": bl_count,
                "int8_ours_mean": ours_mean,
                "int8_ours_std": ours_std,
                "int8_ours_n": ours_count,
                "delta": delta,
                "rel_delta_pct": rel_delta_pct,
                "direction": direction,
                "p_value": p_val,
                "significant_BH_FDR": is_sig,
                "higher_is_better": higher_is_better,
            })

    return pd.DataFrame(rows)


def export_csv(df: pd.DataFrame, out_path: Path) -> None:
    """Write the comparison table to CSV."""
    df.to_csv(out_path, index=False, float_format="%.6f")
    logger.info("CSV written: %s (%d rows)", out_path, len(df))


def export_latex(df: pd.DataFrame, out_path: Path) -> None:
    """Write a publication-ready LaTeX booktabs table."""
    models = df["model"].unique()

    lines = []
    lines.append(r"\begin{table*}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{INT8-ours vs INT8-baseline comparison at 32K sequence length.}")
    lines.append(r"\label{tab:int8_comparison_32k}")
    lines.append(r"\small")
    lines.append(r"\begin{tabular}{ll rr rr c}")
    lines.append(r"\toprule")
    lines.append(
        r"\textbf{Model} & \textbf{Metric} & "
        r"\textbf{INT8-base} & \textbf{INT8-ours} & "
        r"\textbf{$\Delta$} & \textbf{$\Delta$\%} & \textbf{Sig.} \\"
    )
    lines.append(r"\midrule")

    for i, model in enumerate(models):
        mdf = df[df["model"] == model]
        if i > 0:
            lines.append(r"\midrule")

        for j, (_, row) in enumerate(mdf.iterrows()):
            model_col = _latex_escape(model) if j == 0 else ""
            metric = _latex_escape(row["metric"])

            bl_str = _fmt(row["int8_baseline_mean"], ".3f") if row["int8_baseline_mean"] is not None else "--"
            ours_str = _fmt(row["int8_ours_mean"], ".3f") if row["int8_ours_mean"] is not None else "--"

            delta_str = _fmt(row["delta"], "+.3f") if row["delta"] is not None else "--"
            rel_str = _fmt(row["rel_delta_pct"], "+.1f") if row["rel_delta_pct"] is not None else "--"

            sig_str = ""
            if row.get("significant_BH_FDR") is True:
                sig_str = r"$\checkmark$"
            elif row.get("p_value") is not None:
                sig_str = ""  # not significant
            else:
                sig_str = "--"

            # Bold the better value
            if row["direction"] == "better":
                ours_str = r"\textbf{" + ours_str + "}"
            elif row["direction"] == "worse":
                bl_str = r"\textbf{" + bl_str + "}"

            lines.append(
                f"  {model_col} & {metric} & {bl_str} & {ours_str} "
                f"& {delta_str} & {rel_str} & {sig_str} \\\\"
            )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(
        r"\vspace{2pt}\par\footnotesize "
        r"$\Delta$\%: relative change (ours$-$baseline)/|baseline|. "
        r"Sig.: significant at BH-FDR $\alpha=0.05$ (permutation test). "
        r"Bold: better value."
    )
    lines.append(r"\end{table*}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("LaTeX written: %s", out_path)


def print_summary(df: pd.DataFrame) -> None:
    """Print a human-readable summary to stdout."""
    print("\n" + "=" * 100)
    print("INT8-ours vs INT8-baseline Comparison @ 32K seq_len")
    print("=" * 100)

    for model in df["model"].unique():
        mdf = df[df["model"] == model]
        print(f"\n--- {model} ---")
        print(f"{'Metric':<25s}  {'Baseline':>14s}  {'Ours':>14s}  {'Delta':>10s}  {'Rel%':>8s}  {'p-val':>8s}  {'Sig':>5s}")
        print("-" * 95)
        for _, row in mdf.iterrows():
            bl = _fmt(row["int8_baseline_mean"], ".4f")
            ours = _fmt(row["int8_ours_mean"], ".4f")
            delta = _fmt(row["delta"], "+.4f")
            rel = _fmt(row["rel_delta_pct"], "+.2f") if row["rel_delta_pct"] is not None else "--"
            p = f"{row['p_value']:.4f}" if row.get("p_value") is not None else "--"
            sig = "YES" if row.get("significant_BH_FDR") else ("NO" if row.get("p_value") is not None else "--")
            print(f"{row['metric']:<25s}  {bl:>14s}  {ours:>14s}  {delta:>10s}  {rel:>8s}  {p:>8s}  {sig:>5s}")

    print("\n" + "=" * 100)

    # Summary verdicts
    print("\nKey findings:")
    tpot_rows = df[df["metric"] == "TPOT (ms)"]
    for _, row in tpot_rows.iterrows():
        if row["rel_delta_pct"] is not None:
            print(f"  TPOT {row['model']}: {row['rel_delta_pct']:+.1f}% "
                  f"({'faster' if row['delta'] < 0 else 'slower'}, "
                  f"sig={'YES' if row.get('significant_BH_FDR') else 'NO'})")

    ppl_rows = df[df["metric"] == "PPL"]
    for _, row in ppl_rows.iterrows():
        if row["rel_delta_pct"] is not None:
            print(f"  PPL  {row['model']}: {row['rel_delta_pct']:+.2f}% "
                  f"({'degradation' if row['delta'] > 0 else 'improvement'})")

    quality_metrics = ["Needle Pass Rate (%)", "LongBench Score", "RULER Pass Rate (%)"]
    print("\n  Quality preservation (ours vs baseline at 32K):")
    for metric in quality_metrics:
        mrows = df[df["metric"] == metric]
        deltas = [r["rel_delta_pct"] for _, r in mrows.iterrows() if r["rel_delta_pct"] is not None]
        if deltas:
            avg_delta = sum(deltas) / len(deltas)
            print(f"    {metric}: avg rel. delta = {avg_delta:+.2f}%")


# ── CLI ────────────────────────────────────────────────────────────────────────

def _find_default_tables_dir() -> Optional[Path]:
    """Auto-detect the latest results tag with tables."""
    results_dir = Path("results")
    if not results_dir.exists():
        return None
    # Prefer emnlp_final_raw
    for candidate in ["emnlp_final_raw", "final_journal_v2", "final_journal_v1"]:
        path = results_dir / candidate / "tables"
        if path.exists():
            return path
    return None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Build INT8-ours vs INT8-baseline comparison table.",
    )
    parser.add_argument(
        "--tables_dir",
        type=Path,
        default=None,
        help="Path to aggregated tables directory (default: auto-detect)",
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=None,
        help="Output directory for CSV + LaTeX (default: <tables_dir>/../analysis)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress stdout summary",
    )
    args = parser.parse_args()

    # Resolve tables_dir
    tables_dir = args.tables_dir
    if tables_dir is None:
        tables_dir = _find_default_tables_dir()
    if tables_dir is None or not tables_dir.exists():
        logger.error("Cannot find tables directory. Use --tables_dir.")
        sys.exit(1)
    logger.info("Using tables from: %s", tables_dir)

    # Resolve out_dir
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = tables_dir.parent / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build
    df = build_comparison(tables_dir)

    if df.empty:
        logger.error("No data extracted. Check table paths and content.")
        sys.exit(1)

    # Export
    csv_path = out_dir / "int8_comparison_32k.csv"
    tex_path = out_dir / "int8_comparison_32k.tex"

    export_csv(df, csv_path)
    export_latex(df, tex_path)

    if not args.quiet:
        print_summary(df)

    print(f"\nOutputs:\n  CSV:   {csv_path}\n  LaTeX: {tex_path}")


if __name__ == "__main__":
    main()
