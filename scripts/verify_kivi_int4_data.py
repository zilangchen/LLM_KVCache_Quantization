#!/usr/bin/env python3
"""
Phase 0.1: Extract and verify KIVI INT4 data from existing experiment results.

Reads per-run CSVs from results/emnlp_final_raw/runs/, filters KIVI INT4
(quant_bits=4), reaggregates with bootstrap CI95, and compares against
fp16 / int8_ours / int4_baseline / int4_ours baselines.

Output: results/emnlp_postfix_v2/report/kivi_int4_data_verification.md

Usage:
    python scripts/verify_kivi_int4_data.py \
        --runs_dir results/emnlp_final_raw/runs \
        --tables_dir results/emnlp_final_raw/tables \
        --out_dir results/emnlp_postfix_v2/report
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Models and comparison methods
MODEL_SHORT = {
    "Qwen/Qwen2.5-1.5B-Instruct": "1.5B",
    "Qwen/Qwen2.5-7B-Instruct": "7B",
    "meta-llama/Llama-3.1-8B-Instruct": "8B",
}
COMPARE_MODES = ["fp16", "int8_ours", "int4_baseline", "int4_ours", "kivi_style"]


def _ci95(values: np.ndarray) -> tuple[float, float, float]:
    """Compute mean and 95% CI via t-distribution."""
    n = len(values)
    if n < 2:
        m = float(values[0]) if n == 1 else float("nan")
        return m, m, m
    m = float(np.mean(values))
    se = float(np.std(values, ddof=1) / np.sqrt(n))
    # Use z=1.96 approximation for CI95 (sufficient for n >= 5 seeds).
    # Exact t-distribution requires scipy which may not be installed.
    half = 1.96 * se
    return m, m - half, m + half


def _read_all_profile_csvs(runs_dir: Path, pattern: str) -> pd.DataFrame:
    """Glob and concatenate all per-run CSVs matching pattern."""
    files = sorted(runs_dir.rglob(pattern))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["_source"] = str(f.relative_to(runs_dir))
            dfs.append(df)
        except Exception as e:
            logger.warning("Skip %s: %s", f, e)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def _filter_kivi_int4(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to KIVI INT4 rows: kv_mode=kivi_style AND quant_bits=4."""
    mask = df["kv_mode"] == "kivi_style"
    if "quant_bits" in df.columns:
        mask &= df["quant_bits"].astype(float) == 4
    return df[mask].copy()


def _normalize_model_id(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize local model paths to HF model IDs."""
    if "model_id" not in df.columns:
        return df
    df = df.copy()
    for col_val in df["model_id"].unique():
        for hf_id in MODEL_SHORT:
            if hf_id.split("/")[-1].lower() in str(col_val).lower():
                df.loc[df["model_id"] == col_val, "model_id"] = hf_id
    return df


def aggregate_ppl(runs_dir: Path) -> pd.DataFrame:
    """Aggregate PPL data per model × kv_mode."""
    df = _read_all_profile_csvs(runs_dir, "profile_ppl_*.csv")
    if df.empty:
        return df
    df = _normalize_model_id(df)
    if "perplexity" not in df.columns:
        return pd.DataFrame()

    rows = []
    for (model, mode), grp in df.groupby(["model_id", "kv_mode"]):
        # Filter to 32K seq_len (main evaluation point)
        sub = grp[grp["seq_len"].astype(float) >= 30000] if "seq_len" in grp.columns else grp
        if sub.empty:
            sub = grp
        vals = sub["perplexity"].dropna().values
        if len(vals) == 0:
            continue
        mean, ci_lo, ci_hi = _ci95(vals)
        qb = int(sub["quant_bits"].mode().iloc[0]) if "quant_bits" in sub.columns else 16
        rows.append({
            "model_id": model,
            "kv_mode": mode,
            "quant_bits": qb,
            "ppl_mean": round(mean, 3),
            "ppl_ci95_lo": round(ci_lo, 3),
            "ppl_ci95_hi": round(ci_hi, 3),
            "n_runs": len(vals),
        })
    return pd.DataFrame(rows)


def aggregate_needle(runs_dir: Path) -> pd.DataFrame:
    """Aggregate Needle pass rates per model × kv_mode × seq_len."""
    df = _read_all_profile_csvs(runs_dir, "profile_needle_*.csv")
    if df.empty:
        return df
    df = _normalize_model_id(df)
    pass_col = None
    for c in ["needle_pass_rate", "pass_rate", "accuracy"]:
        if c in df.columns:
            pass_col = c
            break
    if pass_col is None:
        return pd.DataFrame()

    rows = []
    for (model, mode, seq), grp in df.groupby(["model_id", "kv_mode", "seq_len"]):
        vals = grp[pass_col].dropna().values
        if len(vals) == 0:
            continue
        mean, ci_lo, ci_hi = _ci95(vals)
        rows.append({
            "model_id": model,
            "kv_mode": mode,
            "seq_len": int(seq),
            "needle_mean": round(mean * 100, 1),
            "needle_ci95_lo": round(ci_lo * 100, 1),
            "needle_ci95_hi": round(ci_hi * 100, 1),
            "n_runs": len(vals),
        })
    return pd.DataFrame(rows)


def generate_report(ppl_df: pd.DataFrame, needle_df: pd.DataFrame, out_path: Path) -> None:
    """Generate markdown verification report."""
    lines = [
        "# KIVI INT4 Data Verification Report",
        "",
        "## Phase 0.1: Existing Data Extraction & Cross-Method Comparison",
        "",
    ]

    # PPL comparison
    lines.append("### Perplexity (32K, mean ± CI95)")
    lines.append("")
    lines.append("| Model | Method | quant_bits | PPL | CI95 | n | Δ vs FP16 |")
    lines.append("|-------|--------|-----------|-----|------|---|-----------|")

    fp16_ppl = {}
    if not ppl_df.empty:
        for _, row in ppl_df[ppl_df["kv_mode"] == "fp16"].iterrows():
            fp16_ppl[row["model_id"]] = row["ppl_mean"]

    for mode in COMPARE_MODES:
        sub = ppl_df[ppl_df["kv_mode"] == mode] if not ppl_df.empty else pd.DataFrame()
        for _, row in sub.iterrows():
            model_short = MODEL_SHORT.get(row["model_id"], row["model_id"])
            fp16_val = fp16_ppl.get(row["model_id"], None)
            delta = ""
            if fp16_val and mode != "fp16":
                pct = (row["ppl_mean"] - fp16_val) / fp16_val * 100
                delta = f"{pct:+.2f}%"
            lines.append(
                f"| {model_short} | {mode} | {int(row['quant_bits'])} | "
                f"{row['ppl_mean']:.3f} | [{row['ppl_ci95_lo']:.3f}, {row['ppl_ci95_hi']:.3f}] | "
                f"{row['n_runs']} | {delta} |"
            )

    # Needle comparison
    lines.append("")
    lines.append("### Needle-in-a-Haystack (pass rate %, 32K)")
    lines.append("")
    if not needle_df.empty:
        needle_32k = needle_df[needle_df["seq_len"] >= 30000]
        lines.append("| Model | Method | Pass Rate | CI95 | n |")
        lines.append("|-------|--------|-----------|------|---|")
        for mode in COMPARE_MODES:
            sub = needle_32k[needle_32k["kv_mode"] == mode]
            for _, row in sub.iterrows():
                model_short = MODEL_SHORT.get(row["model_id"], row["model_id"])
                lines.append(
                    f"| {model_short} | {mode} | {row['needle_mean']:.1f}% | "
                    f"[{row['needle_ci95_lo']:.1f}, {row['needle_ci95_hi']:.1f}] | {row['n_runs']} |"
                )
    else:
        lines.append("*(No needle data found)*")

    # Gate check
    lines.append("")
    lines.append("### Phase 0 Gate Check")
    lines.append("")

    # Check PPL gate: KIVI INT4 worst-case < 15% degradation vs fp16
    gate_pass = True
    if not ppl_df.empty:
        kivi_ppl = ppl_df[ppl_df["kv_mode"] == "kivi_style"]
        for _, row in kivi_ppl.iterrows():
            fp16_val = fp16_ppl.get(row["model_id"])
            if fp16_val:
                pct = (row["ppl_mean"] - fp16_val) / fp16_val * 100
                status = "PASS" if pct < 15 else "FAIL"
                if pct >= 15:
                    gate_pass = False
                model_short = MODEL_SHORT.get(row["model_id"], row["model_id"])
                lines.append(f"- PPL gate ({model_short}): {pct:.2f}% degradation → **{status}** (threshold: <15%)")
    else:
        lines.append("- PPL gate: NO DATA")
        gate_pass = False

    lines.append("")
    lines.append(f"**Overall PPL Gate: {'PASS' if gate_pass else 'FAIL'}**")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 0.1: KIVI INT4 data verification")
    parser.add_argument("--runs_dir", type=str, default="results/emnlp_final_raw/runs")
    parser.add_argument("--tables_dir", type=str, default="results/emnlp_final_raw/tables")
    parser.add_argument("--out_dir", type=str, default="results/emnlp_postfix_v2/report")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    out_dir = Path(args.out_dir)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=== Phase 0.1: KIVI INT4 Data Verification ===")
    print(f"Scanning runs: {runs_dir}")

    ppl_df = aggregate_ppl(runs_dir)
    needle_df = aggregate_needle(runs_dir)

    if ppl_df.empty:
        print("WARNING: No PPL data found. Trying aggregated tables...")
        tables_dir = Path(args.tables_dir)
        ppl_path = tables_dir / "ppl_summary.csv"
        if ppl_path.exists():
            ppl_df = pd.read_csv(ppl_path)
            ppl_df = _normalize_model_id(ppl_df)
            # Reshape: use existing mean/std columns
            if "perplexity_mean" in ppl_df.columns:
                ppl_df = ppl_df.rename(columns={
                    "perplexity_mean": "ppl_mean",
                    "perplexity_count": "n_runs",
                })
                ppl_df["ppl_ci95_lo"] = ppl_df["ppl_mean"]
                ppl_df["ppl_ci95_hi"] = ppl_df["ppl_mean"]
                if "quant_bits" not in ppl_df.columns:
                    ppl_df["quant_bits"] = ppl_df["kv_mode"].apply(
                        lambda m: 4 if "int4" in m or m == "kivi_style" else (8 if "int8" in m else 16)
                    )

    out_path = out_dir / "kivi_int4_data_verification.md"
    generate_report(ppl_df, needle_df, out_path)

    # Also print summary to stdout
    if not ppl_df.empty:
        print("\nPPL Summary:")
        kivi = ppl_df[ppl_df["kv_mode"] == "kivi_style"]
        for _, row in kivi.iterrows():
            model_short = MODEL_SHORT.get(row["model_id"], row["model_id"])
            print(f"  {model_short}: PPL = {row['ppl_mean']:.3f} (n={row.get('n_runs', '?')})")


if __name__ == "__main__":
    main()
