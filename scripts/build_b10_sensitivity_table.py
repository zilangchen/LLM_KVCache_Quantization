#!/usr/bin/env python3
"""
B10: Build calibration sensitivity analysis table.

Reads PPL, Needle, and LongBench results from B10 sensitivity experiments
(varying calibration sample count: 16, 64, 256) and generates summary
CSV + LaTeX table for the paper appendix.

Usage:
    python scripts/build_b10_sensitivity_table.py \
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

logger = logging.getLogger("build_b10_sensitivity")

# Model configs
MODELS = {
    "1p5b": {
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "label": "Qwen2.5-1.5B",
        "run_tag": "exp_b10_1p5b",
    },
    "7b": {
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "label": "Qwen2.5-7B",
        "run_tag": "exp_b10_7b",
    },
}

SAMPLE_COUNTS = [16, 64, 256]

# Also compare against mainline (128 samples, default)
MAINLINE_CALIB_SAMPLES = 128


def _find_csvs(runs_dir: Path, run_tag: str, run_name: str, task_prefix: str) -> List[Path]:
    """Find all CSVs matching a run_tag/run_name/task pattern.

    Run directories follow the naming convention:
        {run_name}_s{seed}_{run_tag}
    e.g. int8_ours_b10_s16_long_s1234_exp_b10_1p5b
    """
    # Primary: match {run_name}_s{seed}_{run_tag} directory structure
    pattern = f"{run_name}_*_{run_tag}/profile_{task_prefix}_*.csv"
    candidates = list(runs_dir.glob(pattern))
    if not candidates:
        # Fallback: broader match without run_tag constraint
        pattern2 = f"{run_name}_*/profile_{task_prefix}_*.csv"
        candidates = list(runs_dir.glob(pattern2))
    return candidates


def _read_ppl(csvs: List[Path]) -> Optional[float]:
    """Read perplexity from PPL CSV(s). Returns mean across seeds."""
    vals = []
    for p in csvs:
        try:
            df = pd.read_csv(p)
            if "perplexity" in df.columns:
                vals.extend(df["perplexity"].dropna().tolist())
        except Exception:
            continue
    return sum(vals) / len(vals) if vals else None


def _read_needle(csvs: List[Path]) -> Optional[float]:
    """Read needle pass rate from Needle CSV(s). Returns mean across seeds."""
    vals = []
    for p in csvs:
        try:
            df = pd.read_csv(p)
            if "pass_rate" in df.columns:
                vals.extend(df["pass_rate"].dropna().tolist())
            elif "needle_pass_rate" in df.columns:
                vals.extend(df["needle_pass_rate"].dropna().tolist())
        except Exception:
            continue
    return sum(vals) / len(vals) if vals else None  # Already in percentage


def _read_longbench(csvs: List[Path]) -> Optional[float]:
    """Read LongBench score from LongBench CSV(s). Returns mean across seeds."""
    vals = []
    for p in csvs:
        try:
            df = pd.read_csv(p)
            if "score" in df.columns:
                vals.extend(df["score"].dropna().tolist())
            elif "longbench_score" in df.columns:
                vals.extend(df["longbench_score"].dropna().tolist())
        except Exception:
            continue
    return sum(vals) / len(vals) if vals else None


def build_sensitivity_table(runs_dir: Path, out_dir: Path) -> None:
    """Build B10 sensitivity analysis table."""
    out_dir.mkdir(parents=True, exist_ok=True)

    for model_key, model_info in MODELS.items():
        run_tag = model_info["run_tag"]
        label = model_info["label"]

        rows = []
        for n_samples in SAMPLE_COUNTS:
            run_name = f"int8_ours_b10_s{n_samples}_long"

            # Find result CSVs
            ppl_csvs = _find_csvs(runs_dir, run_tag, run_name, "ppl")
            needle_csvs = _find_csvs(runs_dir, run_tag, run_name, "needle")
            lb_csvs = _find_csvs(runs_dir, run_tag, run_name, "longbench")

            ppl_val = _read_ppl(ppl_csvs)
            needle_val = _read_needle(needle_csvs)
            lb_val = _read_longbench(lb_csvs)

            rows.append({
                "samples": n_samples,
                "ppl": ppl_val,
                "needle_pct": needle_val,
                "longbench": lb_val,
                "ppl_display": f"{ppl_val:.2f}" if ppl_val else "---",
                "needle_display": f"{needle_val:.1f}" if needle_val else "---",
                "longbench_display": f"{lb_val:.4f}" if lb_val else "---",
            })

        df = pd.DataFrame(rows)

        # Save CSV
        csv_path = out_dir / f"b10_sensitivity_{model_key}.csv"
        df.to_csv(csv_path, index=False)
        logger.info("Saved: %s", csv_path)

        # Save LaTeX
        tex_path = out_dir / f"b10_sensitivity_{model_key}.tex"
        _write_latex(df, tex_path, label)


def _write_latex(df: pd.DataFrame, path: Path, model_label: str) -> None:
    """Write sensitivity table as LaTeX."""
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{Calibration Sensitivity Analysis --- {model_label}}}",
        rf"\label{{tab:b10_sens_{model_label.lower().replace('.', '').replace('-', '_')}}}",
        r"\begin{tabular}{rccc}",
        r"\toprule",
        r"Samples & PPL ($\downarrow$) & Needle (\%) & LongBench \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        lines.append(
            f"  {int(row['samples'])} & {row['ppl_display']} "
            f"& {row['needle_display']} & {row['longbench_display']} \\\\"
        )

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Saved LaTeX: %s", path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build B10 calibration sensitivity table")
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

    build_sensitivity_table(args.runs_dir, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
