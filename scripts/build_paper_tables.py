#!/usr/bin/env python3
"""
Build final EMNLP 2026 paper tables by merging two independent experiment pools:

  1. INT8 Mainline (ch4.2-4.4): results/emnlp_final_raw/tables/
  2. MixedKV Extension (ch4.5):  results/emnlp_postfix_v2/tables/

Outputs (CSV + LaTeX .tex) into results/paper_tables/:
  - table1_main_quality_{model}.csv/.tex     — Main quality results (ch4.2)
  - table2_int8_ablation_{model}.csv/.tex    — INT8 ours vs baseline (ch4.2)
  - table3_mixedkv_{model}.csv/.tex          — MixedKV comparison (ch4.5)
  - table4_latency_memory_{model}.csv/.tex   — Latency & memory (ch4.3)

Usage:
  # On remote server (default paths):
  python scripts/build_paper_tables.py

  # On local dev machine:
  python scripts/build_paper_tables.py --local

  # Custom paths:
  python scripts/build_paper_tables.py \
      --mainline_dir results/emnlp_final_raw/tables \
      --mixedkv_dir results/emnlp_postfix_v2/tables \
      --out_dir results/paper_tables
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("build_paper_tables")

# ---------------------------------------------------------------------------
# Import shared utilities from config_utils (same directory)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_utils import KV_MODE_ORDER  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# kv_modes for each table
TABLE1_KV_MODES = [
    "fp16",
    "int8_baseline",
    "int8_ours",
    "int4_baseline",
    "int4_fused",
    "int4_ours",
    "kivi_style",
    "int4_mixed_kv",
]

TABLE2_KV_MODES = [
    "int8_baseline",
    "int8_ours",
]

TABLE3_KV_MODES = [
    "fp16",
    "kivi_style",
    "int4_mixed_kv",
]

TABLE4_KV_MODES = [
    "fp16",
    "int8_baseline",
    "int8_ours",
    "int4_baseline",
    "int4_fused",
    "int4_ours",
    "kivi_style",
    "int4_mixed_kv",
]

# Core 3 models (mainline pool)
CORE_MODELS = [
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
]

# Table 3 includes Mistral (from MixedKV pool)
TABLE3_MODELS = CORE_MODELS + [
    "mistralai/Mistral-7B-Instruct-v0.3",
]

# Short display names for paper tables
MODEL_SHORT_NAMES: Dict[str, str] = {
    "Qwen/Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5-7B",
    "meta-llama/Llama-3.1-8B-Instruct": "LLaMA-3.1-8B",
    "mistralai/Mistral-7B-Instruct-v0.3": "Mistral-7B",
}

# Filesystem-safe model suffixes for filenames
MODEL_FILE_SUFFIX: Dict[str, str] = {
    "Qwen/Qwen2.5-1.5B-Instruct": "qwen25_1p5b",
    "Qwen/Qwen2.5-7B-Instruct": "qwen25_7b",
    "meta-llama/Llama-3.1-8B-Instruct": "llama31_8b",
    "mistralai/Mistral-7B-Instruct-v0.3": "mistral_7b",
}

# Canonical KV mode display names for paper (matches export_tables_latex.py)
KV_MODE_DISPLAY: Dict[str, str] = {
    "fp16": "FP16",
    "int8_baseline": "INT8-baseline",
    "int8_ours": "INT8-ours",
    "int8_fused": "INT8-fused",
    "int4_baseline": "INT4-baseline",
    "int4_fused": "INT4-fused",
    "int4_ours": "INT4-ours",
    "int4_ours_mixed": "INT4-ours-mixed",
    "kivi_style": "KIVI-style",
    "int4_kivi_aligned": "KV-RoleAlign (K)",
    "int4_mixed_kv": "MixedKV (K8V4)",
}

# Preferred context length for single-point tables (32K)
PREFERRED_SEQ_LEN = 32704

# ---------------------------------------------------------------------------
# CSV I/O helpers
# ---------------------------------------------------------------------------


def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file, returning empty DataFrame on failure."""
    if not path.exists():
        logger.warning("CSV not found: %s", path)
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        logger.info("Loaded %d rows from %s", len(df), path)
        return df
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return pd.DataFrame()


def _save_csv(df: pd.DataFrame, path: Path) -> None:
    """Save DataFrame to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved CSV: %s (%d rows)", path, len(df))


# ---------------------------------------------------------------------------
# Sorting and formatting helpers
# ---------------------------------------------------------------------------

_KV_MODE_RANK = {mode: idx for idx, mode in enumerate(KV_MODE_ORDER)}


def _sort_kv_mode(df: pd.DataFrame) -> pd.DataFrame:
    """Sort DataFrame by canonical kv_mode ordering."""
    if df.empty or "kv_mode" not in df.columns:
        return df
    df = df.copy()
    df["_rank"] = df["kv_mode"].map(_KV_MODE_RANK).fillna(9999).astype(int)
    df = df.sort_values("_rank").drop(columns=["_rank"]).reset_index(drop=True)
    return df


def _display_kv_mode(mode: str) -> str:
    """Convert internal kv_mode name to paper display name."""
    return KV_MODE_DISPLAY.get(mode, mode)


def _display_model(model_id: str) -> str:
    """Convert full model_id to short paper name."""
    return MODEL_SHORT_NAMES.get(model_id, model_id)


def _model_suffix(model_id: str) -> str:
    """Filesystem-safe model suffix for filenames."""
    return MODEL_FILE_SUFFIX.get(model_id, re.sub(r"[^a-zA-Z0-9]", "_", model_id).lower())


def _fmt_mean_std(mean_val, std_val, decimals: int = 2) -> str:
    """Format mean +/- std as 'X.XX +/- Y.YY', or '---' if missing."""
    if pd.isna(mean_val):
        return "---"
    m = f"{mean_val:.{decimals}f}"
    if pd.isna(std_val):
        return m
    return f"{m} $\\pm$ {std_val:.{decimals}f}"


def _fmt_pct(val, decimals: int = 1) -> str:
    """Format a percentage value, or '---' if missing."""
    if pd.isna(val):
        return "---"
    return f"{val:.{decimals}f}"


def _fmt_delta(val, decimals: int = 2, higher_is_better: bool = True) -> str:
    """Format a delta value with +/- sign, or '---' if missing."""
    if pd.isna(val):
        return "---"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.{decimals}f}"


# ---------------------------------------------------------------------------
# Data loading: merge two experiment pools
# ---------------------------------------------------------------------------


def _load_summary(tables_dir: Path, name: str) -> pd.DataFrame:
    """Load a *_summary.csv from a tables directory."""
    return _read_csv(tables_dir / f"{name}_summary.csv")


def _pick_seq(df: pd.DataFrame, preferred: int = 32704) -> Optional[int]:
    """Pick a sequence length from the data, preferring the given value."""
    if df.empty or "seq_len" not in df.columns:
        return None
    seq = pd.to_numeric(df["seq_len"], errors="coerce").dropna().unique()
    if len(seq) == 0:
        return None
    if float(preferred) in seq:
        return preferred
    return int(max(seq))


def _filter_seq(df: pd.DataFrame, seq_len: Optional[int]) -> pd.DataFrame:
    """Filter DataFrame to a single seq_len."""
    if df.empty or seq_len is None or "seq_len" not in df.columns:
        return df
    return df[pd.to_numeric(df["seq_len"], errors="coerce") == float(seq_len)].copy()


def _filter_batch_gen(df: pd.DataFrame, batch: int = 1, gen_len: int = 64) -> pd.DataFrame:
    """Filter latency/memory data to batch=1, gen_len=64 for single-request metrics."""
    out = df.copy()
    if "batch" in out.columns:
        out = out[pd.to_numeric(out["batch"], errors="coerce") == float(batch)]
    if "gen_len" in out.columns:
        gen = pd.to_numeric(out["gen_len"], errors="coerce")
        if (gen == float(gen_len)).any():
            out = out[gen == float(gen_len)]
    return out


def _filter_ppl_kvcache(df: pd.DataFrame) -> pd.DataFrame:
    """Filter PPL data to kv_cache mode only (exclude vanilla mode)."""
    if df.empty or "ppl_mode" not in df.columns:
        return df
    return df[df["ppl_mode"] == "kv_cache"].copy()


def _filter_mixed_kv_runs(df: pd.DataFrame) -> pd.DataFrame:
    """For int4_mixed_kv: ONLY keep runs whose run_name contains 'mixed_kv'.

    This excludes k4v8 counterfactual data that may co-exist in the postfix pool.
    Rows with other kv_modes are passed through unchanged.
    """
    if df.empty:
        return df
    if "run_name" not in df.columns:
        # If no run_name column, filter by kv_mode alone (already filtered upstream)
        return df
    mask_mixed = df["kv_mode"] == "int4_mixed_kv"
    if not mask_mixed.any():
        return df
    mixed_rows = df[mask_mixed]
    mixed_filtered = mixed_rows[mixed_rows["run_name"].str.contains("mixed_kv", na=False)]
    n_dropped = len(mixed_rows) - len(mixed_filtered)
    if n_dropped > 0:
        logger.info(
            "Filtered out %d int4_mixed_kv rows without 'mixed_kv' in run_name", n_dropped
        )
    other_rows = df[~mask_mixed]
    return pd.concat([other_rows, mixed_filtered], ignore_index=True)


def load_merged_data(
    mainline_dir: Path,
    mixedkv_dir: Path,
) -> Dict[str, pd.DataFrame]:
    """Load and merge summary CSVs from both experiment pools.

    Returns a dict with keys: ppl, needle, longbench, ruler, latency, memory.
    Each DataFrame combines mainline data (for non-mixed_kv modes) and
    MixedKV extension data (for int4_mixed_kv mode).
    """
    tables = {}
    summary_names = ["ppl", "needle", "longbench", "ruler", "latency", "memory"]

    for name in summary_names:
        main_df = _load_summary(mainline_dir, name)
        mix_df = _load_summary(mixedkv_dir, name)

        # From mainline: everything except int4_mixed_kv
        if not main_df.empty and "kv_mode" in main_df.columns:
            main_filtered = main_df[main_df["kv_mode"] != "int4_mixed_kv"].copy()
        else:
            main_filtered = main_df

        # From MixedKV pool: only int4_mixed_kv rows (with run_name filter)
        if not mix_df.empty and "kv_mode" in mix_df.columns:
            mix_filtered = mix_df[mix_df["kv_mode"] == "int4_mixed_kv"].copy()
            mix_filtered = _filter_mixed_kv_runs(mix_filtered)
        else:
            mix_filtered = pd.DataFrame()

        # Merge
        frames = [f for f in [main_filtered, mix_filtered] if not f.empty]
        if frames:
            merged = pd.concat(frames, ignore_index=True)
            tables[name] = merged
            logger.info(
                "%s: %d rows (mainline=%d, mixed_kv=%d)",
                name, len(merged), len(main_filtered), len(mix_filtered),
            )
        else:
            tables[name] = pd.DataFrame()
            logger.warning("No data for %s from either pool", name)

    return tables


# ---------------------------------------------------------------------------
# Table 1: Main Quality Results (ch4.2)
# ---------------------------------------------------------------------------


def build_table1(
    data: Dict[str, pd.DataFrame],
    models: List[str],
    out_dir: Path,
    preferred_seq: int = PREFERRED_SEQ_LEN,
) -> None:
    """Build Table 1: Main Quality Results.

    Rows: kv_modes (8 modes including int4_mixed_kv)
    Columns: PPL (mean +/- std), Needle (%), LongBench (mean +/- std), RULER (mean +/- std)
    One sub-table per model.
    """
    logger.info("--- Building Table 1: Main Quality Results ---")

    ppl = _filter_ppl_kvcache(data.get("ppl", pd.DataFrame()))
    needle = data.get("needle", pd.DataFrame())
    longbench = data.get("longbench", pd.DataFrame())
    ruler = data.get("ruler", pd.DataFrame())

    # Pick a single representative seq_len (prefer 32K)
    ppl_seq = _pick_seq(ppl, preferred_seq)
    needle_seq = _pick_seq(needle, preferred_seq)
    lb_seq = _pick_seq(longbench, preferred_seq)
    ruler_seq = _pick_seq(ruler, preferred_seq)

    ppl_at_seq = _filter_seq(ppl, ppl_seq)
    needle_at_seq = _filter_seq(needle, needle_seq)
    lb_at_seq = _filter_seq(longbench, lb_seq)
    ruler_at_seq = _filter_seq(ruler, ruler_seq)

    for model_id in models:
        suffix = _model_suffix(model_id)
        model_label = _display_model(model_id)

        rows = []
        for kv_mode in TABLE1_KV_MODES:
            row: Dict[str, object] = {"kv_mode": kv_mode}

            # PPL
            ppl_m = _extract_metric(ppl_at_seq, model_id, kv_mode, "perplexity_mean")
            ppl_s = _extract_metric(ppl_at_seq, model_id, kv_mode, "perplexity_std")
            row["ppl_mean"] = ppl_m
            row["ppl_std"] = ppl_s
            row["ppl_display"] = _fmt_mean_std(ppl_m, ppl_s)

            # Needle
            needle_m = _extract_metric(needle_at_seq, model_id, kv_mode, "needle_pass_rate_mean")
            row["needle_pct"] = needle_m
            row["needle_display"] = _fmt_pct(needle_m if pd.isna(needle_m) else needle_m * 100.0)

            # LongBench
            lb_m = _extract_metric(lb_at_seq, model_id, kv_mode, "longbench_score_mean")
            lb_s = _extract_metric(lb_at_seq, model_id, kv_mode, "longbench_score_std")
            row["longbench_mean"] = lb_m
            row["longbench_std"] = lb_s
            row["longbench_display"] = _fmt_mean_std(lb_m, lb_s, decimals=3)

            # RULER
            rul_m = _extract_metric(ruler_at_seq, model_id, kv_mode, "ruler_pass_rate_mean")
            rul_s = _extract_metric(ruler_at_seq, model_id, kv_mode, "ruler_pass_rate_std")
            row["ruler_mean"] = rul_m
            row["ruler_std"] = rul_s
            row["ruler_display"] = _fmt_mean_std(rul_m, rul_s, decimals=3)

            rows.append(row)

        df = pd.DataFrame(rows)
        df = _sort_kv_mode(df)

        # Add display column
        df.insert(0, "Method", df["kv_mode"].map(_display_kv_mode))

        # Save CSV
        csv_path = out_dir / f"table1_main_quality_{suffix}.csv"
        _save_csv(df, csv_path)

        # Save LaTeX
        tex_path = out_dir / f"table1_main_quality_{suffix}.tex"
        _write_table1_latex(df, tex_path, model_label, ppl_seq, needle_seq, lb_seq, ruler_seq)


def _write_table1_latex(
    df: pd.DataFrame,
    path: Path,
    model_label: str,
    ppl_seq: Optional[int],
    needle_seq: Optional[int],
    lb_seq: Optional[int],
    ruler_seq: Optional[int],
) -> None:
    """Write Table 1 as a LaTeX booktabs table."""
    seq_note = []
    if ppl_seq:
        seq_note.append(f"PPL@{ppl_seq}")
    if needle_seq:
        seq_note.append(f"Needle@{needle_seq}")
    if lb_seq:
        seq_note.append(f"LongBench@{lb_seq}")
    if ruler_seq:
        seq_note.append(f"RULER@{ruler_seq}")
    seq_info = ", ".join(seq_note) if seq_note else "N/A"

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{Main Quality Results --- {_latex_escape(model_label)} ({_latex_escape(seq_info)})}}",
        rf"\label{{tab:main_quality_{_sanitize_label(model_label)}}}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Method & PPL ($\downarrow$) & Needle (\%) & LongBench & RULER \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        method = _latex_escape(str(row["Method"]))
        ppl_d = str(row["ppl_display"])
        ndl_d = str(row["needle_display"])
        lb_d = str(row["longbench_display"])
        rul_d = str(row["ruler_display"])
        lines.append(f"  {method} & {ppl_d} & {ndl_d} & {lb_d} & {rul_d} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}}",
        r"\end{table}",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Saved LaTeX: %s", path)


# ---------------------------------------------------------------------------
# Table 2: INT8 Ours vs Baseline Ablation (ch4.2)
# ---------------------------------------------------------------------------


def build_table2(
    data: Dict[str, pd.DataFrame],
    models: List[str],
    out_dir: Path,
    preferred_seq: int = PREFERRED_SEQ_LEN,
) -> None:
    """Build Table 2: INT8 ours vs baseline with delta columns.

    Only uses mainline data (emnlp_final_raw).
    """
    logger.info("--- Building Table 2: INT8 Ablation ---")

    ppl = _filter_ppl_kvcache(data.get("ppl", pd.DataFrame()))
    needle = data.get("needle", pd.DataFrame())
    longbench = data.get("longbench", pd.DataFrame())
    ruler = data.get("ruler", pd.DataFrame())

    ppl_seq = _pick_seq(ppl, preferred_seq)
    needle_seq = _pick_seq(needle, preferred_seq)
    lb_seq = _pick_seq(longbench, preferred_seq)
    ruler_seq = _pick_seq(ruler, preferred_seq)

    ppl_at_seq = _filter_seq(ppl, ppl_seq)
    needle_at_seq = _filter_seq(needle, needle_seq)
    lb_at_seq = _filter_seq(longbench, lb_seq)
    ruler_at_seq = _filter_seq(ruler, ruler_seq)

    for model_id in models:
        suffix = _model_suffix(model_id)
        model_label = _display_model(model_id)

        rows = []
        baseline_vals: Dict[str, object] = {}

        for kv_mode in TABLE2_KV_MODES:
            row: Dict[str, object] = {"kv_mode": kv_mode}

            ppl_m = _extract_metric(ppl_at_seq, model_id, kv_mode, "perplexity_mean")
            ppl_s = _extract_metric(ppl_at_seq, model_id, kv_mode, "perplexity_std")
            needle_m = _extract_metric(needle_at_seq, model_id, kv_mode, "needle_pass_rate_mean")
            lb_m = _extract_metric(lb_at_seq, model_id, kv_mode, "longbench_score_mean")
            lb_s = _extract_metric(lb_at_seq, model_id, kv_mode, "longbench_score_std")
            rul_m = _extract_metric(ruler_at_seq, model_id, kv_mode, "ruler_pass_rate_mean")
            rul_s = _extract_metric(ruler_at_seq, model_id, kv_mode, "ruler_pass_rate_std")

            row["ppl_mean"] = ppl_m
            row["ppl_std"] = ppl_s
            row["ppl_display"] = _fmt_mean_std(ppl_m, ppl_s)
            row["needle_pct"] = needle_m
            row["needle_display"] = _fmt_pct(needle_m if pd.isna(needle_m) else needle_m * 100.0)
            row["longbench_mean"] = lb_m
            row["longbench_std"] = lb_s
            row["longbench_display"] = _fmt_mean_std(lb_m, lb_s, decimals=3)
            row["ruler_mean"] = rul_m
            row["ruler_std"] = rul_s
            row["ruler_display"] = _fmt_mean_std(rul_m, rul_s, decimals=3)

            if kv_mode == "int8_baseline":
                baseline_vals = {
                    "ppl": ppl_m,
                    "needle": needle_m,
                    "longbench": lb_m,
                    "ruler": rul_m,
                }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Add delta columns (ours - baseline)
        bl_ppl = baseline_vals.get("ppl")
        bl_needle = baseline_vals.get("needle")
        bl_lb = baseline_vals.get("longbench")
        bl_ruler = baseline_vals.get("ruler")

        df["delta_ppl"] = df["ppl_mean"].apply(
            lambda x: (x - bl_ppl) if not pd.isna(x) and not pd.isna(bl_ppl) else None
        )
        df["delta_needle"] = df["needle_pct"].apply(
            lambda x: ((x - bl_needle) * 100.0) if not pd.isna(x) and not pd.isna(bl_needle) else None
        )
        df["delta_longbench"] = df["longbench_mean"].apply(
            lambda x: (x - bl_lb) if not pd.isna(x) and not pd.isna(bl_lb) else None
        )
        df["delta_ruler"] = df["ruler_mean"].apply(
            lambda x: (x - bl_ruler) if not pd.isna(x) and not pd.isna(bl_ruler) else None
        )

        # Format delta display (PPL: lower is better; others: higher is better)
        df["delta_ppl_display"] = df["delta_ppl"].apply(
            lambda x: _fmt_delta(x, decimals=2, higher_is_better=False)
        )
        df["delta_needle_display"] = df["delta_needle"].apply(
            lambda x: _fmt_delta(x, decimals=1)
        )
        df["delta_longbench_display"] = df["delta_longbench"].apply(
            lambda x: _fmt_delta(x, decimals=3)
        )
        df["delta_ruler_display"] = df["delta_ruler"].apply(
            lambda x: _fmt_delta(x, decimals=3)
        )

        df = _sort_kv_mode(df)
        df.insert(0, "Method", df["kv_mode"].map(_display_kv_mode))

        csv_path = out_dir / f"table2_int8_ablation_{suffix}.csv"
        _save_csv(df, csv_path)

        tex_path = out_dir / f"table2_int8_ablation_{suffix}.tex"
        _write_table2_latex(df, tex_path, model_label)


def _write_table2_latex(
    df: pd.DataFrame,
    path: Path,
    model_label: str,
) -> None:
    """Write Table 2 as a LaTeX booktabs table."""
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{INT8 Ablation --- {_latex_escape(model_label)}}}",
        rf"\label{{tab:int8_ablation_{_sanitize_label(model_label)}}}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lcc|cc|cc|cc}",
        r"\toprule",
        r" & \multicolumn{2}{c}{PPL ($\downarrow$)} & \multicolumn{2}{c}{Needle (\%)} "
        r"& \multicolumn{2}{c}{LongBench} & \multicolumn{2}{c}{RULER} \\",
        r"\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(lr){8-9}",
        r"Method & Value & $\Delta$ & Value & $\Delta$ & Value & $\Delta$ & Value & $\Delta$ \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        method = _latex_escape(str(row["Method"]))
        cells = [
            method,
            str(row["ppl_display"]),
            str(row["delta_ppl_display"]),
            str(row["needle_display"]),
            str(row["delta_needle_display"]),
            str(row["longbench_display"]),
            str(row["delta_longbench_display"]),
            str(row["ruler_display"]),
            str(row["delta_ruler_display"]),
        ]
        lines.append("  " + " & ".join(cells) + r" \\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}}",
        r"\end{table}",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Saved LaTeX: %s", path)


# ---------------------------------------------------------------------------
# Table 3: MixedKV Comparison (ch4.5)
# ---------------------------------------------------------------------------


def build_table3(
    data: Dict[str, pd.DataFrame],
    mainline_data: Dict[str, pd.DataFrame],
    mixedkv_data: Dict[str, pd.DataFrame],
    models: List[str],
    out_dir: Path,
    preferred_seq: int = PREFERRED_SEQ_LEN,
) -> None:
    """Build Table 3: MixedKV comparison.

    For Core 3 models: fp16/kivi from mainline, int4_mixed_kv from postfix.
    For Mistral-7B: all data from postfix pool.
    """
    logger.info("--- Building Table 3: MixedKV Comparison ---")

    for model_id in models:
        suffix = _model_suffix(model_id)
        model_label = _display_model(model_id)
        is_core = model_id in CORE_MODELS

        rows = []
        for kv_mode in TABLE3_KV_MODES:
            # Choose data source:
            #   - fp16/kivi for Core 3: mainline
            #   - int4_mixed_kv: always postfix
            #   - everything for Mistral: postfix
            if is_core and kv_mode != "int4_mixed_kv":
                source = mainline_data
            else:
                source = mixedkv_data

            row: Dict[str, object] = {"kv_mode": kv_mode}

            ppl_df = _filter_ppl_kvcache(source.get("ppl", pd.DataFrame()))
            ppl_seq = _pick_seq(ppl_df, preferred_seq)
            ppl_at_seq = _filter_seq(ppl_df, ppl_seq)

            needle_df = source.get("needle", pd.DataFrame())
            needle_seq = _pick_seq(needle_df, preferred_seq)
            needle_at_seq = _filter_seq(needle_df, needle_seq)

            lb_df = source.get("longbench", pd.DataFrame())
            lb_seq = _pick_seq(lb_df, preferred_seq)
            lb_at_seq = _filter_seq(lb_df, lb_seq)

            ruler_df = source.get("ruler", pd.DataFrame())
            ruler_seq = _pick_seq(ruler_df, preferred_seq)
            ruler_at_seq = _filter_seq(ruler_df, ruler_seq)

            ppl_m = _extract_metric(ppl_at_seq, model_id, kv_mode, "perplexity_mean")
            ppl_s = _extract_metric(ppl_at_seq, model_id, kv_mode, "perplexity_std")
            needle_m = _extract_metric(needle_at_seq, model_id, kv_mode, "needle_pass_rate_mean")
            lb_m = _extract_metric(lb_at_seq, model_id, kv_mode, "longbench_score_mean")
            lb_s = _extract_metric(lb_at_seq, model_id, kv_mode, "longbench_score_std")
            rul_m = _extract_metric(ruler_at_seq, model_id, kv_mode, "ruler_pass_rate_mean")
            rul_s = _extract_metric(ruler_at_seq, model_id, kv_mode, "ruler_pass_rate_std")

            row["ppl_mean"] = ppl_m
            row["ppl_std"] = ppl_s
            row["ppl_display"] = _fmt_mean_std(ppl_m, ppl_s)
            row["needle_pct"] = needle_m
            row["needle_display"] = _fmt_pct(needle_m if pd.isna(needle_m) else needle_m * 100.0)
            row["longbench_mean"] = lb_m
            row["longbench_std"] = lb_s
            row["longbench_display"] = _fmt_mean_std(lb_m, lb_s, decimals=3)
            row["ruler_mean"] = rul_m
            row["ruler_std"] = rul_s
            row["ruler_display"] = _fmt_mean_std(rul_m, rul_s, decimals=3)

            rows.append(row)

        df = pd.DataFrame(rows)
        df = _sort_kv_mode(df)
        df.insert(0, "Method", df["kv_mode"].map(_display_kv_mode))

        csv_path = out_dir / f"table3_mixedkv_{suffix}.csv"
        _save_csv(df, csv_path)

        tex_path = out_dir / f"table3_mixedkv_{suffix}.tex"
        _write_table3_latex(df, tex_path, model_label)


def _write_table3_latex(
    df: pd.DataFrame,
    path: Path,
    model_label: str,
) -> None:
    """Write Table 3 as a LaTeX booktabs table."""
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{MixedKV Comparison --- {_latex_escape(model_label)}}}",
        rf"\label{{tab:mixedkv_{_sanitize_label(model_label)}}}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Method & PPL ($\downarrow$) & Needle (\%) & LongBench & RULER \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        method = _latex_escape(str(row["Method"]))
        ppl_d = str(row["ppl_display"])
        ndl_d = str(row["needle_display"])
        lb_d = str(row["longbench_display"])
        rul_d = str(row["ruler_display"])
        lines.append(f"  {method} & {ppl_d} & {ndl_d} & {lb_d} & {rul_d} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}}",
        r"\end{table}",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Saved LaTeX: %s", path)


# ---------------------------------------------------------------------------
# Table 4: Latency & Memory (ch4.3)
# ---------------------------------------------------------------------------


def build_table4(
    data: Dict[str, pd.DataFrame],
    models: List[str],
    out_dir: Path,
    preferred_seq: int = PREFERRED_SEQ_LEN,
) -> None:
    """Build Table 4: Latency and peak memory.

    TPOT (ms) and Peak Memory (MB) per kv_mode x model at 32K, batch=1.
    """
    logger.info("--- Building Table 4: Latency & Memory ---")

    latency = data.get("latency", pd.DataFrame())
    memory = data.get("memory", pd.DataFrame())

    # Filter to batch=1, gen_len=64 for single-request latency
    latency = _filter_batch_gen(latency, batch=1, gen_len=64)
    memory = _filter_batch_gen(memory, batch=1, gen_len=64)

    lat_seq = _pick_seq(latency, preferred_seq)
    mem_seq = _pick_seq(memory, preferred_seq)

    latency = _filter_seq(latency, lat_seq)
    memory = _filter_seq(memory, mem_seq)

    for model_id in models:
        suffix = _model_suffix(model_id)
        model_label = _display_model(model_id)

        rows = []
        for kv_mode in TABLE4_KV_MODES:
            row: Dict[str, object] = {"kv_mode": kv_mode}

            tpot_m = _extract_metric(latency, model_id, kv_mode, "tpot_ms_mean")
            tpot_s = _extract_metric(latency, model_id, kv_mode, "tpot_ms_std")
            ttft_m = _extract_metric(latency, model_id, kv_mode, "ttft_ms_mean")
            ttft_s = _extract_metric(latency, model_id, kv_mode, "ttft_ms_std")
            mem_m = _extract_metric(memory, model_id, kv_mode, "gpu_mem_peak_mb_mean")
            mem_s = _extract_metric(memory, model_id, kv_mode, "gpu_mem_peak_mb_std")
            kv_mem_m = _extract_metric(memory, model_id, kv_mode, "kv_cache_mem_mb_mean")
            kv_mem_s = _extract_metric(memory, model_id, kv_mode, "kv_cache_mem_mb_std")

            row["tpot_mean"] = tpot_m
            row["tpot_std"] = tpot_s
            row["tpot_display"] = _fmt_mean_std(tpot_m, tpot_s)
            row["ttft_mean"] = ttft_m
            row["ttft_std"] = ttft_s
            row["ttft_display"] = _fmt_mean_std(ttft_m, ttft_s)
            row["peak_mem_mean"] = mem_m
            row["peak_mem_std"] = mem_s
            row["peak_mem_display"] = _fmt_mean_std(mem_m, mem_s, decimals=0)
            row["kv_mem_mean"] = kv_mem_m
            row["kv_mem_std"] = kv_mem_s
            row["kv_mem_display"] = _fmt_mean_std(kv_mem_m, kv_mem_s, decimals=0)

            rows.append(row)

        df = pd.DataFrame(rows)
        df = _sort_kv_mode(df)
        df.insert(0, "Method", df["kv_mode"].map(_display_kv_mode))

        csv_path = out_dir / f"table4_latency_memory_{suffix}.csv"
        _save_csv(df, csv_path)

        tex_path = out_dir / f"table4_latency_memory_{suffix}.tex"
        _write_table4_latex(df, tex_path, model_label, lat_seq, mem_seq)


def _write_table4_latex(
    df: pd.DataFrame,
    path: Path,
    model_label: str,
    lat_seq: Optional[int],
    mem_seq: Optional[int],
) -> None:
    """Write Table 4 as a LaTeX booktabs table."""
    seq_note = f"Latency@{lat_seq or '?'}, Memory@{mem_seq or '?'}, batch=1"
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{Latency \& Memory --- {_latex_escape(model_label)} ({_latex_escape(seq_note)})}}",
        rf"\label{{tab:latency_memory_{_sanitize_label(model_label)}}}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Method & TPOT (ms, $\downarrow$) & TTFT (ms, $\downarrow$) "
        r"& Peak Mem (MB, $\downarrow$) & KV Cache (MB, $\downarrow$) \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        method = _latex_escape(str(row["Method"]))
        tpot_d = str(row["tpot_display"])
        ttft_d = str(row["ttft_display"])
        mem_d = str(row["peak_mem_display"])
        kv_d = str(row["kv_mem_display"])
        lines.append(f"  {method} & {tpot_d} & {ttft_d} & {mem_d} & {kv_d} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}}",
        r"\end{table}",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Saved LaTeX: %s", path)


# ---------------------------------------------------------------------------
# Metric extraction helper
# ---------------------------------------------------------------------------


def _extract_metric(
    df: pd.DataFrame,
    model_id: str,
    kv_mode: str,
    column: str,
) -> object:
    """Extract a single metric value from a summary DataFrame.

    Filters by model_id and kv_mode, then returns the value in `column`.
    Returns NaN if not found or multiple rows match (takes first in that case).
    """
    if df.empty or column not in df.columns:
        return float("nan")

    mask = pd.Series(True, index=df.index)
    if "model_id" in df.columns:
        mask &= df["model_id"] == model_id
    if "kv_mode" in df.columns:
        mask &= df["kv_mode"] == kv_mode

    filtered = df[mask]
    if filtered.empty:
        return float("nan")

    val = filtered[column].iloc[0]
    if filtered.shape[0] > 1:
        logger.debug(
            "Multiple rows for model=%s kv_mode=%s col=%s, using first (n=%d)",
            model_id, kv_mode, column, filtered.shape[0],
        )
    return val


# ---------------------------------------------------------------------------
# LaTeX helpers (mirrors export_tables_latex.py conventions)
# ---------------------------------------------------------------------------


def _latex_escape(text: str) -> str:
    """Escape text for safe insertion into LaTeX content."""
    out = str(text)
    for src, dst in [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        out = out.replace(src, dst)
    return out


def _sanitize_label(text: str) -> str:
    """Create a LaTeX-safe label string."""
    text = re.sub(r"[{}\\#$%&^~]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"[^a-zA-Z0-9_.-]", "_", text)
    return text.lower()


# ---------------------------------------------------------------------------
# Per-pool data loaders (for Table 3 which needs separate access)
# ---------------------------------------------------------------------------


def _load_pool(tables_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all summary CSVs from a single tables directory."""
    pool = {}
    for name in ["ppl", "needle", "longbench", "ruler", "latency", "memory"]:
        pool[name] = _load_summary(tables_dir, name)
    return pool


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build EMNLP 2026 paper tables from two experiment pools.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mainline_dir",
        type=Path,
        default=None,
        help="Path to mainline (INT8) aggregated tables directory. "
             "Default: results/emnlp_final_raw/tables/",
    )
    parser.add_argument(
        "--mixedkv_dir",
        type=Path,
        default=None,
        help="Path to MixedKV extension aggregated tables directory. "
             "Default: results/emnlp_postfix_v2/tables/",
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=None,
        help="Output directory for paper tables. Default: results/paper_tables/",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local paths (same relative structure, for dev machine).",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=["1", "2", "3", "4", "all"],
        default=["all"],
        help="Which tables to build (default: all).",
    )
    parser.add_argument(
        "--seq_len",
        type=int,
        default=PREFERRED_SEQ_LEN,
        help=f"Preferred seq_len for single-point tables (default: {PREFERRED_SEQ_LEN}).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    args = parser.parse_args()

    # Logging setup
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Resolve paths
    # On remote server: results/ is under project root
    # On local dev: same relative structure
    project_root = Path(__file__).resolve().parent.parent

    if args.mainline_dir is not None:
        mainline_dir = args.mainline_dir
    else:
        mainline_dir = project_root / "results" / "emnlp_final_raw" / "tables"

    if args.mixedkv_dir is not None:
        mixedkv_dir = args.mixedkv_dir
    else:
        mixedkv_dir = project_root / "results" / "emnlp_postfix_v2" / "tables"

    if args.out_dir is not None:
        out_dir = args.out_dir
    else:
        out_dir = project_root / "results" / "paper_tables"

    preferred_seq = args.seq_len

    logger.info("Mainline dir : %s", mainline_dir)
    logger.info("MixedKV dir  : %s", mixedkv_dir)
    logger.info("Output dir   : %s", out_dir)

    # Validate directories
    if not mainline_dir.is_dir():
        logger.error("Mainline tables directory not found: %s", mainline_dir)
        logger.error(
            "Run aggregate_results.py first, or check --mainline_dir path."
        )
        return 1
    if not mixedkv_dir.is_dir():
        logger.warning(
            "MixedKV tables directory not found: %s  "
            "(Table 3 / int4_mixed_kv data will be missing)", mixedkv_dir
        )
        # Continue — Tables 1/2/4 can still be built from mainline only

    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("Loading data from both pools...")
    merged_data = load_merged_data(mainline_dir, mixedkv_dir)
    mainline_pool = _load_pool(mainline_dir)
    mixedkv_pool = _load_pool(mixedkv_dir) if mixedkv_dir.is_dir() else {}

    build_tables = set(args.tables)
    if "all" in build_tables:
        build_tables = {"1", "2", "3", "4"}

    # Build tables
    if "1" in build_tables:
        build_table1(merged_data, CORE_MODELS, out_dir, preferred_seq=preferred_seq)

    if "2" in build_tables:
        build_table2(merged_data, CORE_MODELS, out_dir, preferred_seq=preferred_seq)

    if "3" in build_tables:
        build_table3(
            merged_data, mainline_pool, mixedkv_pool, TABLE3_MODELS, out_dir,
            preferred_seq=preferred_seq,
        )

    if "4" in build_tables:
        build_table4(merged_data, CORE_MODELS, out_dir, preferred_seq=preferred_seq)

    # Summary
    logger.info("=" * 60)
    logger.info("Paper tables built successfully.")
    logger.info("Output directory: %s", out_dir)
    built_files = sorted(out_dir.glob("table*"))
    for f in built_files:
        logger.info("  %s", f.name)
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
