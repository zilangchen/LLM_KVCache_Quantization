#!/usr/bin/env python3
"""
Build K/V ablation analysis tables for LongBench and RULER.

Compares K-only (K@INT8, V@FP16), V-only (K@FP16, V@INT4), and
counterfactual K4V8 (K@INT4, V@INT8) ablation results across models.

Supports:
  - LongBench ablation (Phase 2)
  - RULER ablation (Phase 4)
  - Cross-benchmark consistency check

Usage:
    python scripts/build_kv_ablation_table.py \
        --runs_dir results/emnlp_expansion_v1/runs \
        --out_dir results/emnlp_expansion_v1/tables
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger("build_kv_ablation")

# Models for ablation
MODELS = {
    "1p5b": {
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "label": "Qwen2.5-1.5B",
        "run_tag": "exp_1p5b",
    },
    "7b": {
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "label": "Qwen2.5-7B",
        "run_tag": "exp_7b",
    },
    "8b": {
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "label": "LLaMA-3.1-8B",
        "run_tag": "exp_8b",
    },
    "mistral": {
        "model_id": "mistralai/Mistral-7B-Instruct-v0.3",
        "label": "Mistral-7B",
        "run_tag": "exp_mistral",
    },
}

# Ablation methods
ABLATION_METHODS = [
    {"run_name": "k_only_int8_long", "label": "K-only (K@INT8, V@FP16)", "short": "K-only"},
    {"run_name": "v_only_int4_long", "label": "V-only (K@FP16, V@INT4)", "short": "V-only"},
    {"run_name": "k_int4_v_int8_long", "label": "K4V8 (K@INT4, V@INT8)", "short": "K4V8"},
]

# Reference methods (from Closure Pack data, if available)
REFERENCE_METHODS = [
    {"run_name": "fp16_matched_long", "kv_mode": "fp16", "label": "FP16", "alt_run": "fp16_kv_long"},
    {"run_name": "mixed_kv_long", "kv_mode": "int4_mixed_kv", "label": "MixedKV (K8V4)"},
    {"run_name": "kivi_int4_matched_long", "kv_mode": "kivi_style", "label": "KIVI-style"},
]


def _find_csvs(runs_dir: Path, run_name: str, task_prefix: str) -> List[Path]:
    """Find result CSVs matching run_name and task."""
    pattern = f"**/{run_name}/**/profile_{task_prefix}_*.csv"
    return list(runs_dir.glob(pattern))


def _read_metric(csvs: List[Path], metric_col: str) -> Optional[float]:
    """Read a metric from CSVs, returning mean across all seeds."""
    vals = []
    for p in csvs:
        try:
            df = pd.read_csv(p)
            if metric_col in df.columns:
                vals.extend(df[metric_col].dropna().tolist())
        except Exception:
            continue
    return sum(vals) / len(vals) if vals else None


def _read_metric_std(csvs: List[Path], metric_col: str) -> Optional[float]:
    """Read a metric from CSVs, returning std across all seeds."""
    vals = []
    for p in csvs:
        try:
            df = pd.read_csv(p)
            if metric_col in df.columns:
                vals.extend(df[metric_col].dropna().tolist())
        except Exception:
            continue
    if len(vals) > 1:
        mean = sum(vals) / len(vals)
        variance = sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)
        return variance ** 0.5
    return None


def build_ablation_table(
    runs_dir: Path,
    out_dir: Path,
    task: str,
    metric_col: str,
    metric_name: str,
    higher_is_better: bool = True,
) -> None:
    """Build ablation table for a given task/metric."""
    out_dir.mkdir(parents=True, exist_ok=True)

    task_prefix = {"longbench": "longbench", "ruler": "ruler"}[task]

    all_rows = []
    for model_key, model_info in MODELS.items():
        # Skip Mistral for RULER (not in Phase 4)
        if task == "ruler" and model_key == "mistral":
            continue

        label = model_info["label"]

        for method in ABLATION_METHODS:
            csvs = _find_csvs(runs_dir, method["run_name"], task_prefix)
            mean_val = _read_metric(csvs, metric_col)
            std_val = _read_metric_std(csvs, metric_col)

            all_rows.append({
                "model": label,
                "model_key": model_key,
                "method": method["short"],
                "run_name": method["run_name"],
                "mean": mean_val,
                "std": std_val,
                "display": _fmt(mean_val, std_val),
            })

    df = pd.DataFrame(all_rows)

    # Save CSV
    csv_path = out_dir / f"kv_ablation_{task}.csv"
    df.to_csv(csv_path, index=False)
    logger.info("Saved: %s (%d rows)", csv_path, len(df))

    # Per-model LaTeX tables
    for model_key, model_info in MODELS.items():
        if task == "ruler" and model_key == "mistral":
            continue

        model_df = df[df["model_key"] == model_key]
        if model_df.empty:
            continue

        tex_path = out_dir / f"kv_ablation_{task}_{model_key}.tex"
        _write_ablation_latex(model_df, tex_path, model_info["label"], metric_name, higher_is_better)

    # Cross-model summary
    summary_path = out_dir / f"kv_ablation_{task}_summary.csv"
    _write_summary(df, summary_path, higher_is_better)


def _fmt(mean_val: Optional[float], std_val: Optional[float]) -> str:
    """Format mean +/- std."""
    if mean_val is None:
        return "---"
    if std_val is None:
        return f"{mean_val:.4f}"
    return f"{mean_val:.4f} +/- {std_val:.4f}"


def _write_ablation_latex(
    df: pd.DataFrame,
    path: Path,
    model_label: str,
    metric_name: str,
    higher_is_better: bool,
) -> None:
    """Write ablation table as LaTeX."""
    arrow = r"$\uparrow$" if higher_is_better else r"$\downarrow$"
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{K/V Ablation {metric_name} --- {model_label}}}",
        rf"\label{{tab:kv_ablation_{metric_name.lower()}_{model_label.lower().replace('.', '').replace('-', '_')}}}",
        r"\begin{tabular}{lc}",
        r"\toprule",
        rf"Method & {metric_name} ({arrow}) \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        method = str(row["method"]).replace("@", r"@")
        display = str(row["display"]).replace("+/-", r"$\pm$")
        lines.append(f"  {method} & {display} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Saved LaTeX: %s", path)


def _write_summary(df: pd.DataFrame, path: Path, higher_is_better: bool) -> None:
    """Write cross-model summary: does K-only > V-only hold for all models?"""
    summary_rows = []
    for model_key in df["model_key"].unique():
        model_df = df[df["model_key"] == model_key]
        k_only = model_df[model_df["method"] == "K-only"]["mean"].values
        v_only = model_df[model_df["method"] == "V-only"]["mean"].values
        k4v8 = model_df[model_df["method"] == "K4V8"]["mean"].values

        k_val = k_only[0] if len(k_only) > 0 and k_only[0] is not None else None
        v_val = v_only[0] if len(v_only) > 0 and v_only[0] is not None else None
        kv_val = k4v8[0] if len(k4v8) > 0 and k4v8[0] is not None else None

        # K > V sensitivity means: quantizing K hurts more, so K-only (K quantized) should be worse
        # For higher_is_better: k_only < v_only → K more sensitive
        # For lower_is_better (PPL): k_only > v_only → K more sensitive
        if k_val is not None and v_val is not None:
            if higher_is_better:
                k_more_sensitive = k_val < v_val
            else:
                k_more_sensitive = k_val > v_val
        else:
            k_more_sensitive = None

        summary_rows.append({
            "model": model_df["model"].iloc[0],
            "k_only": k_val,
            "v_only": v_val,
            "k4v8": kv_val,
            "k_more_sensitive": k_more_sensitive,
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(path, index=False)
    logger.info("Saved summary: %s", path)

    # Log findings
    n_support = sum(1 for r in summary_rows if r["k_more_sensitive"] is True)
    n_total = sum(1 for r in summary_rows if r["k_more_sensitive"] is not None)
    logger.info("K > V sensitivity: %d/%d models support hypothesis", n_support, n_total)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build K/V ablation analysis tables")
    parser.add_argument("--runs_dir", type=Path, required=True,
                        help="Path to expansion runs directory")
    parser.add_argument("--out_dir", type=Path, required=True,
                        help="Output directory for tables")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # LongBench ablation (Phase 2)
    logger.info("=== Building LongBench ablation tables ===")
    build_ablation_table(
        args.runs_dir, args.out_dir,
        task="longbench",
        metric_col="score",
        metric_name="LongBench",
        higher_is_better=True,
    )

    # RULER ablation (Phase 4)
    logger.info("=== Building RULER ablation tables ===")
    build_ablation_table(
        args.runs_dir, args.out_dir,
        task="ruler",
        metric_col="pass_rate",
        metric_name="RULER",
        higher_is_better=True,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
