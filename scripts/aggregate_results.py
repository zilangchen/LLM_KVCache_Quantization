#!/usr/bin/env python3
"""
Aggregate structured CSV outputs under results/runs/ into summary tables and plots.

Outputs:
  - results/tables/*.csv
  - results/plots/*.png

This script is intentionally "dumb but robust": it infers which CSVs to load by
filename prefixes produced by the repo's scripts (profile_latency, profile_memory,
profile_ppl, profile_needle, needle_details).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _read_csvs(runs_dir: Path, patterns: Iterable[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for pattern in patterns:
        # Results are written under per-run subdirectories (e.g., results/runs/<run_id>/profile_*.csv).
        # Use recursive glob so aggregation works regardless of directory layout.
        for path in sorted(runs_dir.rglob(pattern)):
            try:
                df = pd.read_csv(path)
            except Exception:
                continue
            try:
                df["source_file"] = str(path.relative_to(runs_dir))
            except Exception:
                df["source_file"] = str(path)
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _to_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _agg_mean_std(df: pd.DataFrame, keys: List[str], values: List[str]) -> pd.DataFrame:
    keep_values = [c for c in values if c in df.columns]
    if df.empty or not keep_values:
        return pd.DataFrame()
    out = (
        df.groupby(keys, dropna=False)[keep_values]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    # Flatten multi-index columns: tpot_ms_mean, tpot_ms_std, ...
    out.columns = [
        "_".join([c for c in col if c]) if isinstance(col, tuple) else col for col in out.columns
    ]
    return out


def _add_ci95_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add CI95 columns for every *_mean/*_std/*_count triplet in aggregated tables.
    """
    if df.empty:
        return df
    out = df.copy()
    for col in list(out.columns):
        if not col.endswith("_mean"):
            continue
        prefix = col[: -len("_mean")]
        std_col = f"{prefix}_std"
        cnt_col = f"{prefix}_count"
        if std_col not in out.columns or cnt_col not in out.columns:
            continue
        std = pd.to_numeric(out[std_col], errors="coerce")
        cnt = pd.to_numeric(out[cnt_col], errors="coerce")
        mean = pd.to_numeric(out[col], errors="coerce")
        sem = std / np.sqrt(cnt.clip(lower=1))
        ci_half = 1.96 * sem
        ci_half = ci_half.where(cnt > 1, 0.0)
        out[f"{prefix}_ci95_half"] = ci_half
        out[f"{prefix}_ci95_low"] = mean - ci_half
        out[f"{prefix}_ci95_high"] = mean + ci_half
    return out


def _extract_seed_from_run_id(run_id: str) -> float | None:
    if not isinstance(run_id, str):
        return None
    m = re.search(r"_s(\d+)_", run_id)
    if not m:
        return None
    try:
        return float(int(m.group(1)))
    except Exception:
        return None


def _save_table(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def _parse_seq_tag_to_len(seq_tag: str) -> int | None:
    seq_tag = str(seq_tag).strip().lower()
    m = re.fullmatch(r"(\d+)(k?)", seq_tag)
    if not m:
        return None
    value = int(m.group(1))
    if m.group(2) == "k":
        return value * 1024
    return value


def _parse_batch_list(text: str) -> List[int]:
    if not isinstance(text, str) or not text.strip():
        return []
    out: List[int] = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            out.append(int(item))
        except Exception:
            continue
    return sorted(set(out))


def _format_batch_list(values: Iterable[int]) -> str:
    uniq = sorted({int(v) for v in values})
    return ",".join(str(v) for v in uniq)


def _log_contains_oom(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return bool(re.search(r"\bOOM\b|out of memory", content, flags=re.IGNORECASE))


def _collect_throughput_attempts(runs_dir: Path, logs_dir: Path | None) -> pd.DataFrame:
    """
    Parse attempted throughput runs from runs/<run_dir_name>.
    Expected naming pattern includes: <kv_mode>_throughput_<seq_tag>_b<batch>
    """
    rows = []
    pattern = re.compile(
        r"(?P<kv_mode>[A-Za-z0-9_]+)_throughput_(?P<seq_tag>[0-9]+k?)_b(?P<batch>[0-9]+)"
    )
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        m = pattern.search(run_dir.name)
        if not m:
            continue
        seq_len = _parse_seq_tag_to_len(m.group("seq_tag"))
        if seq_len is None:
            continue
        kv_mode = m.group("kv_mode")
        batch = int(m.group("batch"))
        has_latency_csv = any(run_dir.glob("profile_latency_*.csv"))
        latency_log = (
            logs_dir / run_dir.name / "profile_latency.log"
            if logs_dir is not None
            else Path("")
        )
        has_oom = _log_contains_oom(latency_log) if logs_dir is not None else False
        status = "ok" if has_latency_csv else ("oom" if has_oom else "missing")
        rows.append(
            {
                "run_dir": run_dir.name,
                "kv_mode": kv_mode,
                "seq_len": seq_len,
                "batch": batch,
                "has_latency_csv": bool(has_latency_csv),
                "status": status,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _build_throughput_capacity_summary(
    lat_batch: pd.DataFrame,
    attempts: pd.DataFrame,
    *,
    target_seq: int,
) -> pd.DataFrame:
    if attempts.empty:
        return pd.DataFrame()

    work_attempts = attempts.copy()
    work_attempts["seq_len"] = pd.to_numeric(work_attempts["seq_len"], errors="coerce")
    work_attempts["batch"] = pd.to_numeric(work_attempts["batch"], errors="coerce")
    work_attempts = work_attempts[work_attempts["seq_len"] == float(target_seq)]
    if work_attempts.empty:
        return pd.DataFrame()

    work_latency = lat_batch.copy()
    if not work_latency.empty and {"kv_mode", "batch"}.issubset(work_latency.columns):
        work_latency["batch"] = pd.to_numeric(work_latency["batch"], errors="coerce")
        work_latency = work_latency.dropna(subset=["batch"])
    else:
        work_latency = pd.DataFrame(columns=["kv_mode", "batch"])

    rows = []
    for kv_mode, sub in sorted(work_attempts.groupby("kv_mode")):
        attempted_batches = sorted(int(x) for x in sub["batch"].dropna().unique())
        successful_batches = sorted(
            int(x)
            for x in work_latency.loc[work_latency["kv_mode"] == kv_mode, "batch"].dropna().unique()
        )
        missing_batches = sorted(set(attempted_batches) - set(successful_batches))
        oom_batches = sorted(
            int(x) for x in sub.loc[sub["status"] == "oom", "batch"].dropna().unique()
        )
        mode_status = "complete"
        if missing_batches:
            mode_status = "oom_or_missing"
            if set(missing_batches).issubset(set(oom_batches)):
                mode_status = "oom_capacity_limit"
            elif not oom_batches:
                mode_status = "missing_results"
        rows.append(
            {
                "seq_len": target_seq,
                "kv_mode": kv_mode,
                "attempted_batches": _format_batch_list(attempted_batches),
                "successful_batches": _format_batch_list(successful_batches),
                "missing_batches": _format_batch_list(missing_batches),
                "oom_batches": _format_batch_list(oom_batches),
                "max_success_batch": max(successful_batches) if successful_batches else np.nan,
                "first_missing_batch": min(missing_batches) if missing_batches else np.nan,
                "first_oom_batch": min(oom_batches) if oom_batches else np.nan,
                "mode_status": mode_status,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["kv_mode"]).reset_index(drop=True)


def _annotate_batch_curve_with_capacity(
    curve_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
) -> pd.DataFrame:
    if curve_df.empty:
        return curve_df
    out = curve_df.copy()
    out["point_status"] = "measured"
    out["status_reason"] = "ok"
    out["capacity_limit_batch"] = np.nan
    out["is_capacity_limit"] = False

    if capacity_df.empty:
        return out

    missing_rows = []
    for _, info in capacity_df.iterrows():
        kv_mode = info.get("kv_mode")
        if not isinstance(kv_mode, str):
            continue
        mode_rows = out[out["kv_mode"] == kv_mode]
        max_success = pd.to_numeric(info.get("max_success_batch"), errors="coerce")
        missing_batches = _parse_batch_list(str(info.get("missing_batches", "")))

        if pd.notna(max_success) and missing_batches and not mode_rows.empty:
            cap_mask = (out["kv_mode"] == kv_mode) & (
                pd.to_numeric(out["batch"], errors="coerce") == float(max_success)
            )
            out.loc[cap_mask, "is_capacity_limit"] = True
            out.loc[cap_mask, "capacity_limit_batch"] = float(max_success)

        if not missing_batches:
            continue

        mode_status = str(info.get("mode_status", "missing"))
        template = mode_rows.iloc[0] if not mode_rows.empty else None
        for batch in missing_batches:
            row = {col: np.nan for col in out.columns}
            row["kv_mode"] = kv_mode
            row["batch"] = batch
            row["point_status"] = "missing"
            row["status_reason"] = mode_status
            row["capacity_limit_batch"] = float(max_success) if pd.notna(max_success) else np.nan
            row["is_capacity_limit"] = False
            if "seq_len" in row:
                row["seq_len"] = info.get("seq_len", np.nan)
            for copy_col in [
                "model_id",
                "hardware",
                "gen_len",
                "group_size",
                "clip_percentile",
            ]:
                if template is not None and copy_col in out.columns:
                    row[copy_col] = template.get(copy_col, np.nan)
            missing_rows.append(row)

    if missing_rows:
        out = pd.concat([out, pd.DataFrame(missing_rows)], ignore_index=True)
    if "batch" in out.columns:
        out = out.sort_values(["kv_mode", "batch"]).reset_index(drop=True)
    return out


def _plot_batch_with_capacity(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    hue: str,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
    yerr: str | None = None,
) -> None:
    if df.empty or y not in df.columns:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plot_df = df.copy()
    plot_df[x] = pd.to_numeric(plot_df[x], errors="coerce")
    plot_df[y] = pd.to_numeric(plot_df[y], errors="coerce")
    plot_df = plot_df.dropna(subset=[x])
    if plot_df.empty:
        return

    measured = plot_df
    if "point_status" in plot_df.columns:
        measured = plot_df[plot_df["point_status"] != "missing"]
    if measured.empty:
        return

    plt.figure(figsize=(8, 5))
    color_map = {}
    for label, sub in sorted(measured.groupby(hue)):
        sub = sub.sort_values(x)
        if yerr and yerr in sub.columns:
            cont = plt.errorbar(
                sub[x],
                sub[y],
                yerr=sub[yerr],
                marker="o",
                label=str(label),
                capsize=3,
            )
            try:
                color_map[str(label)] = cont[0].get_color()
            except Exception:
                pass
        else:
            line = plt.plot(sub[x], sub[y], marker="o", label=str(label))
            if line:
                try:
                    color_map[str(label)] = line[0].get_color()
                except Exception:
                    pass

    # Capacity-limit annotation lines.
    if "is_capacity_limit" in measured.columns:
        limits = measured[measured["is_capacity_limit"] == True]
        y_max = pd.to_numeric(measured[y], errors="coerce").max()
        if pd.notna(y_max):
            used_labels = set()
            for idx, row in limits.iterrows():
                mode = str(row.get(hue))
                x_cap = pd.to_numeric(row.get(x), errors="coerce")
                if pd.isna(x_cap):
                    continue
                color = color_map.get(mode, "gray")
                plt.axvline(x_cap, linestyle="--", linewidth=1.0, alpha=0.25, color=color)
                if mode in used_labels:
                    continue
                y_text = y_max * (0.97 - 0.05 * (len(used_labels) % 6))
                plt.text(
                    x_cap,
                    y_text,
                    f"{mode} cap≤{int(x_cap)}",
                    rotation=90,
                    fontsize=8,
                    color=color,
                    ha="right",
                    va="top",
                    alpha=0.75,
                )
                used_labels.add(mode)

    # Missing / OOM markers.
    if {"point_status", "status_reason"}.issubset(plot_df.columns):
        missing = plot_df[plot_df["point_status"] == "missing"]
        for mode, sub_miss in sorted(missing.groupby(hue)):
            mode_str = str(mode)
            mode_measured = measured[measured[hue] == mode]
            if mode_measured.empty:
                continue
            anchor = pd.to_numeric(mode_measured[y], errors="coerce").dropna()
            if anchor.empty:
                continue
            anchor_y = float(anchor.iloc[-1])
            color = color_map.get(mode_str, "red")
            for _, row in sub_miss.sort_values(x).iterrows():
                x_miss = pd.to_numeric(row.get(x), errors="coerce")
                if pd.isna(x_miss):
                    continue
                reason = str(row.get("status_reason", "missing")).lower()
                marker_text = "OOM" if "oom" in reason else "MISS"
                marker_color = "red" if marker_text == "OOM" else color
                plt.scatter([x_miss], [anchor_y], marker="x", color=marker_color, s=45, zorder=6)
                plt.text(
                    x_miss,
                    anchor_y,
                    marker_text,
                    fontsize=7,
                    color=marker_color,
                    ha="left",
                    va="bottom",
                )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_lines(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
    yerr: str | None = None,
) -> None:
    if df.empty:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    for label, sub in sorted(df.groupby(hue)):
        sub = sub.sort_values(x)
        if yerr and yerr in sub.columns:
            plt.errorbar(
                sub[x],
                sub[y],
                yerr=sub[yerr],
                marker="o",
                label=str(label),
                capsize=3,
            )
        else:
            plt.plot(sub[x], sub[y], marker="o", label=str(label))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _maybe_filter_batch_gen_len(
    df: pd.DataFrame,
    *,
    batch: int | None = None,
    gen_len: int | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df
    if batch is not None and "batch" in out.columns:
        out = out[pd.to_numeric(out["batch"], errors="coerce") == float(batch)]
    if gen_len is not None and "gen_len" in out.columns:
        out = out[pd.to_numeric(out["gen_len"], errors="coerce") == float(gen_len)]
    return out


def _pick_seq_len_for_batch_curves(df: pd.DataFrame, *, preferred: int = 8192) -> int | None:
    if df.empty or "seq_len" not in df.columns or "batch" not in df.columns:
        return None
    tmp = df.copy()
    tmp["seq_len"] = pd.to_numeric(tmp["seq_len"], errors="coerce")
    tmp["batch"] = pd.to_numeric(tmp["batch"], errors="coerce")
    tmp = tmp.dropna(subset=["seq_len", "batch"])
    if tmp.empty:
        return None

    if (tmp["seq_len"] == float(preferred)).any():
        return int(preferred)

    counts = tmp.groupby("seq_len")["batch"].nunique().sort_values(ascending=False)
    if counts.empty:
        return None
    return int(counts.index[0])


def _significance_summary(
    df: pd.DataFrame,
    metric_col: str,
    key_cols: List[str],
    pairings: List[tuple[str, str]],
    metric_name: str,
) -> pd.DataFrame:
    """
    Build paired-difference summary by seed for selected mode pairings.
    """
    if df.empty or metric_col not in df.columns:
        return pd.DataFrame()
    if "kv_mode" not in df.columns:
        return pd.DataFrame()

    work = df.copy()
    if "seed" not in work.columns:
        if "run_id" in work.columns:
            work["seed"] = work["run_id"].map(_extract_seed_from_run_id)
    work["seed"] = pd.to_numeric(work.get("seed"), errors="coerce")
    work[metric_col] = pd.to_numeric(work[metric_col], errors="coerce")
    work = work.dropna(subset=["seed", metric_col])
    if work.empty:
        return pd.DataFrame()

    keys = [c for c in key_cols if c in work.columns]
    results = []
    for base_mode, ours_mode in pairings:
        sub = work[work["kv_mode"].isin([base_mode, ours_mode])]
        if sub.empty:
            continue
        pivot = (
            sub.pivot_table(
                index=keys + ["seed"],
                columns="kv_mode",
                values=metric_col,
                aggfunc="mean",
            )
        )
        if base_mode not in pivot.columns or ours_mode not in pivot.columns:
            continue
        pivot = pivot.dropna(subset=[base_mode, ours_mode], how="any").reset_index()
        if pivot.empty:
            continue
        pivot["diff"] = pivot[ours_mode] - pivot[base_mode]
        grouped = pivot.groupby(keys, dropna=False)["diff"]
        summary = grouped.agg(["mean", "std", "count"]).reset_index()
        if summary.empty:
            continue
        summary["metric"] = metric_name
        summary["baseline_mode"] = base_mode
        summary["challenger_mode"] = ours_mode
        sem = summary["std"] / np.sqrt(summary["count"].clip(lower=1))
        ci_half = 1.96 * sem
        ci_half = ci_half.where(summary["count"] > 1, 0.0)
        summary["diff_ci95_low"] = summary["mean"] - ci_half
        summary["diff_ci95_high"] = summary["mean"] + ci_half
        summary = summary.rename(
            columns={
                "mean": "diff_mean",
                "std": "diff_std",
                "count": "n_pairs",
            }
        )
        results.append(summary)

    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)


def _relative_gain_table(
    df: pd.DataFrame,
    *,
    metric_col: str,
    metric_name: str,
    key_cols: List[str],
    pairings: List[tuple[str, str]],
    higher_is_better: bool,
) -> pd.DataFrame:
    """
    Build relative-gain table for selected mode pairings on aggregated summaries.
    gain_pct > 0 means challenger is better than baseline under the metric direction.
    """
    if df.empty or metric_col not in df.columns or "kv_mode" not in df.columns:
        return pd.DataFrame()
    keep = [c for c in key_cols if c in df.columns]
    sub = df[keep + ["kv_mode", metric_col]].copy()
    sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
    sub = sub.dropna(subset=[metric_col])
    if sub.empty:
        return pd.DataFrame()

    pivot = sub.pivot_table(index=keep, columns="kv_mode", values=metric_col, aggfunc="mean")
    out_frames: List[pd.DataFrame] = []
    for baseline, challenger in pairings:
        if baseline not in pivot.columns or challenger not in pivot.columns:
            continue
        tmp = pivot[[baseline, challenger]].dropna().reset_index()
        if tmp.empty:
            continue
        base_val = pd.to_numeric(tmp[baseline], errors="coerce")
        chall_val = pd.to_numeric(tmp[challenger], errors="coerce")
        delta_abs = chall_val - base_val
        denom = base_val.abs().replace(0, np.nan)
        delta_pct = (delta_abs / denom) * 100.0
        if higher_is_better:
            gain_pct = delta_pct
        else:
            gain_pct = ((base_val - chall_val) / denom) * 100.0

        row = tmp[keep].copy()
        row["metric"] = metric_name
        row["baseline_mode"] = baseline
        row["challenger_mode"] = challenger
        row["baseline_value"] = base_val
        row["challenger_value"] = chall_val
        row["delta_abs"] = delta_abs
        row["delta_pct"] = delta_pct
        row["gain_pct"] = gain_pct
        out_frames.append(row)

    if not out_frames:
        return pd.DataFrame()
    return pd.concat(out_frames, ignore_index=True)


def _main_claims_32k_table(
    latency_summary: pd.DataFrame,
    memory_summary: pd.DataFrame,
    needle_summary: pd.DataFrame,
    ppl_summary: pd.DataFrame,
    *,
    target_seq_len: int = 32704,
) -> pd.DataFrame:
    """
    Build a one-glance thesis claim table at 32K context (or nearest available point).
    """
    def _pick_seq(df: pd.DataFrame, preferred: int) -> int | None:
        if df.empty or "seq_len" not in df.columns:
            return None
        seq = pd.to_numeric(df["seq_len"], errors="coerce").dropna()
        if seq.empty:
            return None
        if (seq == float(preferred)).any():
            return int(preferred)
        return int(seq.max())

    lat = latency_summary.copy()
    mem = memory_summary.copy()
    ned = needle_summary.copy()
    ppl = ppl_summary.copy()

    lat_seq = _pick_seq(lat, target_seq_len)
    mem_seq = _pick_seq(mem, target_seq_len)
    ned_seq = _pick_seq(ned, target_seq_len)
    if lat_seq is None and mem_seq is None and ned_seq is None:
        return pd.DataFrame()

    if not lat.empty and "batch" in lat.columns:
        lat = lat[pd.to_numeric(lat["batch"], errors="coerce") == 1]
    if not lat.empty and "gen_len" in lat.columns:
        gen = pd.to_numeric(lat["gen_len"], errors="coerce")
        if (gen == 64).any():
            lat = lat[gen == 64]
    if lat_seq is not None and "seq_len" in lat.columns:
        lat = lat[pd.to_numeric(lat["seq_len"], errors="coerce") == float(lat_seq)]

    if not mem.empty and "batch" in mem.columns:
        mem = mem[pd.to_numeric(mem["batch"], errors="coerce") == 1]
    if not mem.empty and "gen_len" in mem.columns:
        gen = pd.to_numeric(mem["gen_len"], errors="coerce")
        if (gen == 64).any():
            mem = mem[gen == 64]
    if mem_seq is not None and "seq_len" in mem.columns:
        mem = mem[pd.to_numeric(mem["seq_len"], errors="coerce") == float(mem_seq)]

    if ned_seq is not None and "seq_len" in ned.columns:
        ned = ned[pd.to_numeric(ned["seq_len"], errors="coerce") == float(ned_seq)]

    # PPL: choose kv_cache row with maximal tokens_evaluated for each mode.
    if not ppl.empty and "ppl_mode" in ppl.columns:
        ppl = ppl[ppl["ppl_mode"] == "kv_cache"]
    if not ppl.empty and "tokens_evaluated_mean" in ppl.columns:
        ppl = (
            ppl.sort_values("tokens_evaluated_mean", ascending=False)
            .drop_duplicates(subset=["kv_mode"], keep="first")
        )

    lat_cols = [c for c in ["kv_mode", "tpot_ms_mean", "ttft_ms_mean", "tok_per_s_mean"] if c in lat.columns]
    mem_cols = [c for c in ["kv_mode", "gpu_mem_peak_mb_mean", "kv_cache_mem_mb_mean"] if c in mem.columns]
    ned_cols = [c for c in ["kv_mode", "needle_pass_rate_mean", "needle_exact_match_rate_mean"] if c in ned.columns]
    ppl_cols = [c for c in ["kv_mode", "perplexity_mean", "tokens_evaluated_mean"] if c in ppl.columns]

    if not lat_cols or not mem_cols:
        return pd.DataFrame()

    out = lat[lat_cols].copy()
    if mem_cols:
        out = out.merge(mem[mem_cols], on="kv_mode", how="outer")
    if ned_cols:
        out = out.merge(ned[ned_cols], on="kv_mode", how="outer")
    if ppl_cols:
        out = out.merge(ppl[ppl_cols], on="kv_mode", how="left")

    out["claim_seq_len"] = int(lat_seq or mem_seq or ned_seq or target_seq_len)
    out = out.sort_values("kv_mode").reset_index(drop=True)
    return out


def _speedup_vs_reference(
    df: pd.DataFrame,
    *,
    metric_col: str,
    reference_mode: str,
    key_cols: List[str],
    higher_is_better: bool = False,
) -> pd.DataFrame:
    """
    Compute relative speedup/gain vs reference mode for each kv_mode and key.
    """
    if df.empty or metric_col not in df.columns or "kv_mode" not in df.columns:
        return pd.DataFrame()
    keep = [c for c in key_cols if c in df.columns]
    sub = df[keep + ["kv_mode", metric_col]].copy()
    sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
    sub = sub.dropna(subset=[metric_col])
    if sub.empty:
        return pd.DataFrame()
    pivot = sub.pivot_table(index=keep, columns="kv_mode", values=metric_col, aggfunc="mean")
    if reference_mode not in pivot.columns:
        return pd.DataFrame()
    ref = pd.to_numeric(pivot[reference_mode], errors="coerce")
    denom = ref.abs().replace(0, np.nan)

    rows: List[pd.DataFrame] = []
    for mode in pivot.columns:
        if mode == reference_mode:
            continue
        val = pd.to_numeric(pivot[mode], errors="coerce")
        if higher_is_better:
            gain = ((val - ref) / denom) * 100.0
        else:
            gain = ((ref - val) / denom) * 100.0
        tmp = gain.reset_index(name="gain_pct")
        tmp["reference_mode"] = reference_mode
        tmp["challenger_mode"] = mode
        tmp["metric"] = metric_col
        rows.append(tmp)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate results into tables and plots")
    parser.add_argument("--runs_dir", type=str, default="results/runs")
    parser.add_argument("--tables_dir", type=str, default="results/tables")
    parser.add_argument("--plots_dir", type=str, default="results/plots")
    parser.add_argument(
        "--logs_dir",
        type=str,
        default="",
        help="Optional logs directory for OOM/missing annotation (default: sibling of runs_dir).",
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    tables_dir = Path(args.tables_dir)
    plots_dir = Path(args.plots_dir)
    logs_dir: Path | None = None
    if args.logs_dir:
        logs_dir = Path(args.logs_dir)
    else:
        sibling_logs = runs_dir.parent / "logs"
        if sibling_logs.exists():
            logs_dir = sibling_logs

    if not runs_dir.exists():
        print(f"runs_dir not found: {runs_dir}")
        return 2

    throughput_attempts = _collect_throughput_attempts(runs_dir, logs_dir)
    throughput_capacity_summary = pd.DataFrame()

    # Latency
    latency = _read_csvs(runs_dir, ["profile_latency_*.csv"])
    latency = _to_numeric(
        latency,
        [
            "seq_len",
            "gen_len",
            "batch",
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
            "tok_per_s_per_seq",
            "gpu_mem_peak_mb",
            "kv_cache_mem_mb",
            "kv_cache_seq_len",
            "prefill_tok_per_s",
        ],
    )
    if "seed" not in latency.columns and "run_id" in latency.columns:
        latency["seed"] = latency["run_id"].map(_extract_seed_from_run_id)
    latency = _to_numeric(latency, ["seed"])
    latency_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "seq_len",
            "gen_len",
            "batch",
            "group_size",
            "clip_percentile",
        ]
        if c in latency.columns
    ]
    latency_summary = _agg_mean_std(
        latency,
        latency_keys,
        [
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
            "tok_per_s_per_seq",
            "gpu_mem_peak_mb",
            "kv_cache_mem_mb",
            "kv_cache_seq_len",
            "prefill_tok_per_s",
        ],
    )
    if not latency_summary.empty:
        latency_summary = _add_ci95_columns(latency_summary)
        _save_table(latency_summary, tables_dir / "latency_summary.csv")
        lat_seq = _maybe_filter_batch_gen_len(latency_summary, batch=1, gen_len=64)
        if "seq_len" in lat_seq.columns and "tpot_ms_mean" in lat_seq.columns:
            _plot_lines(
                lat_seq,
                x="seq_len",
                y="tpot_ms_mean",
                hue="kv_mode",
                title="TPOT vs Seq Len",
                xlabel="Sequence length (tokens)",
                ylabel="TPOT (ms, mean)",
                out_path=plots_dir / "latency_tpot_vs_seq.png",
                yerr="tpot_ms_ci95_half",
            )

        # Batch throughput curve (throughput vs batch).
        target_seq = _pick_seq_len_for_batch_curves(latency_summary, preferred=8192)
        if target_seq is not None and {"batch", "tok_per_s_mean", "kv_mode"}.issubset(latency_summary.columns):
            lat_batch = latency_summary[latency_summary["seq_len"] == target_seq]
            if "gen_len" in lat_batch.columns and (lat_batch["gen_len"] == 128).any():
                lat_batch = lat_batch[lat_batch["gen_len"] == 128]
            if not lat_batch.empty:
                capacity_summary = _build_throughput_capacity_summary(
                    lat_batch,
                    throughput_attempts,
                    target_seq=target_seq,
                )
                throughput_capacity_summary = capacity_summary
                if not capacity_summary.empty:
                    _save_table(capacity_summary, tables_dir / "throughput_capacity_limits.csv")
                lat_batch_annotated = _annotate_batch_curve_with_capacity(
                    lat_batch,
                    capacity_summary,
                )
                _save_table(lat_batch_annotated, tables_dir / "throughput_by_batch.csv")
                _plot_batch_with_capacity(
                    lat_batch_annotated,
                    x="batch",
                    y="tok_per_s_mean",
                    hue="kv_mode",
                    title=f"Throughput vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="Tokens per second (total, mean)",
                    out_path=plots_dir / "throughput_tok_per_s_vs_batch.png",
                    yerr="tok_per_s_ci95_half",
                )
                if "tok_per_s_per_seq_mean" in lat_batch.columns:
                    _plot_batch_with_capacity(
                        lat_batch_annotated,
                        x="batch",
                        y="tok_per_s_per_seq_mean",
                        hue="kv_mode",
                        title=f"Throughput per Sequence vs Batch (seq_len={target_seq})",
                        xlabel="Batch size",
                        ylabel="Tokens/s/seq (mean)",
                        out_path=plots_dir / "throughput_tok_per_s_per_seq_vs_batch.png",
                        yerr="tok_per_s_per_seq_ci95_half",
                    )

                if "prefill_tok_per_s_mean" in lat_batch.columns:
                    _plot_batch_with_capacity(
                        lat_batch_annotated,
                        x="batch",
                        y="prefill_tok_per_s_mean",
                        hue="kv_mode",
                        title=f"Prefill Throughput vs Batch (seq_len={target_seq})",
                        xlabel="Batch size",
                        ylabel="Prefill tokens/s (mean)",
                        out_path=plots_dir / "prefill_tok_per_s_vs_batch.png",
                        yerr="prefill_tok_per_s_ci95_half",
                    )
        # Relative TPOT gain vs FP16 (batch=1, curve points).
        tpot_gain = _speedup_vs_reference(
            _maybe_filter_batch_gen_len(latency_summary, batch=1, gen_len=64),
            metric_col="tpot_ms_mean",
            reference_mode="fp16",
            key_cols=["seq_len", "gen_len", "batch"],
            higher_is_better=False,
        )
        if not tpot_gain.empty and {"seq_len", "gain_pct", "challenger_mode"}.issubset(tpot_gain.columns):
            _save_table(tpot_gain, tables_dir / "latency_tpot_gain_vs_fp16.csv")
            _plot_lines(
                tpot_gain,
                x="seq_len",
                y="gain_pct",
                hue="challenger_mode",
                title="TPOT Gain vs FP16",
                xlabel="Sequence length (tokens)",
                ylabel="Gain vs FP16 (%)",
                out_path=plots_dir / "latency_tpot_gain_vs_fp16.png",
            )

    # Memory
    memory = _read_csvs(runs_dir, ["profile_memory_*.csv"])
    memory = _to_numeric(
        memory,
        [
            "seq_len",
            "gen_len",
            "batch",
            "gpu_mem_peak_mb",
            "kv_cache_mem_mb",
            "kv_cache_seq_len",
            "torch_peak_mb",
            "nvml_peak_mb",
            "tok_per_s",
            "tok_per_s_per_seq",
        ],
    )
    if "seed" not in memory.columns and "run_id" in memory.columns:
        memory["seed"] = memory["run_id"].map(_extract_seed_from_run_id)
    memory = _to_numeric(memory, ["seed"])
    memory_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "seq_len",
            "gen_len",
            "batch",
            "group_size",
            "clip_percentile",
        ]
        if c in memory.columns
    ]
    memory_summary = _agg_mean_std(
        memory,
        memory_keys,
        ["gpu_mem_peak_mb", "kv_cache_mem_mb", "kv_cache_seq_len", "torch_peak_mb", "nvml_peak_mb"],
    )
    if not memory_summary.empty:
        memory_summary = _add_ci95_columns(memory_summary)
        _save_table(memory_summary, tables_dir / "memory_summary.csv")
        mem_seq = _maybe_filter_batch_gen_len(memory_summary, batch=1, gen_len=64)
        if "seq_len" in mem_seq.columns and "gpu_mem_peak_mb_mean" in mem_seq.columns:
            _plot_lines(
                mem_seq,
                x="seq_len",
                y="gpu_mem_peak_mb_mean",
                hue="kv_mode",
                title="Peak GPU Memory vs Seq Len",
                xlabel="Sequence length (tokens)",
                ylabel="Peak GPU memory (MB, mean)",
                out_path=plots_dir / "memory_peak_vs_seq.png",
                yerr="gpu_mem_peak_mb_ci95_half",
            )
        if "seq_len" in mem_seq.columns and "kv_cache_mem_mb_mean" in mem_seq.columns:
            _plot_lines(
                mem_seq,
                x="seq_len",
                y="kv_cache_mem_mb_mean",
                hue="kv_mode",
                title="KV Cache Resident Memory vs Seq Len",
                xlabel="Sequence length (tokens)",
                ylabel="KV cache memory (MB, mean)",
                out_path=plots_dir / "memory_kv_cache_vs_seq.png",
                yerr="kv_cache_mem_mb_ci95_half",
            )

        target_seq = _pick_seq_len_for_batch_curves(memory_summary, preferred=8192)
        if target_seq is not None and {"batch", "gpu_mem_peak_mb_mean", "kv_mode"}.issubset(memory_summary.columns):
            mem_batch = memory_summary[memory_summary["seq_len"] == target_seq]
            if "gen_len" in mem_batch.columns and (mem_batch["gen_len"] == 128).any():
                mem_batch = mem_batch[mem_batch["gen_len"] == 128]
            if not mem_batch.empty:
                mem_batch_annotated = _annotate_batch_curve_with_capacity(
                    mem_batch,
                    throughput_capacity_summary,
                )
                _plot_batch_with_capacity(
                    mem_batch_annotated,
                    x="batch",
                    y="gpu_mem_peak_mb_mean",
                    hue="kv_mode",
                    title=f"Peak GPU Memory vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="Peak GPU memory (MB, mean)",
                    out_path=plots_dir / "memory_peak_vs_batch.png",
                    yerr="gpu_mem_peak_mb_ci95_half",
                )
        if target_seq is not None and {"batch", "kv_cache_mem_mb_mean", "kv_mode"}.issubset(memory_summary.columns):
            mem_batch = memory_summary[memory_summary["seq_len"] == target_seq]
            if "gen_len" in mem_batch.columns and (mem_batch["gen_len"] == 128).any():
                mem_batch = mem_batch[mem_batch["gen_len"] == 128]
            if not mem_batch.empty:
                mem_batch_annotated = _annotate_batch_curve_with_capacity(
                    mem_batch,
                    throughput_capacity_summary,
                )
                _plot_batch_with_capacity(
                    mem_batch_annotated,
                    x="batch",
                    y="kv_cache_mem_mb_mean",
                    hue="kv_mode",
                    title=f"KV Cache Memory vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="KV cache memory (MB, mean)",
                    out_path=plots_dir / "memory_kv_cache_vs_batch.png",
                    yerr="kv_cache_mem_mb_ci95_half",
                )

    # PPL
    ppl = _read_csvs(runs_dir, ["profile_ppl_*.csv"])
    ppl = _to_numeric(ppl, ["seq_len", "batch", "perplexity", "tokens_evaluated", "seed", "replica_id"])
    if "seed" not in ppl.columns and "run_id" in ppl.columns:
        ppl["seed"] = ppl["run_id"].map(_extract_seed_from_run_id)
    ppl = _to_numeric(ppl, ["seed"])
    ppl_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "ppl_mode",
            "seq_len",
            "batch",
            "group_size",
            "clip_percentile",
            "chunk_size",
        ]
        if c in ppl.columns
    ]
    ppl_summary = _agg_mean_std(ppl, ppl_keys, ["perplexity", "tokens_evaluated"])
    if not ppl_summary.empty:
        ppl_summary = _add_ci95_columns(ppl_summary)
        _save_table(ppl_summary, tables_dir / "ppl_summary.csv")
        if "seq_len" in ppl_summary.columns and "perplexity_mean" in ppl_summary.columns:
            _plot_lines(
                ppl_summary,
                x="seq_len",
                y="perplexity_mean",
                hue="kv_mode",
                title="Perplexity vs Evaluated Tokens",
                xlabel="Evaluated tokens (seq_len)",
                ylabel="Perplexity (mean)",
                out_path=plots_dir / "ppl_vs_tokens.png",
                yerr="perplexity_ci95_half",
            )

    # Needle (summary)
    needle = _read_csvs(runs_dir, ["profile_needle_*.csv"])
    needle = _to_numeric(
        needle,
        ["seq_len", "needle_pass_rate", "needle_exact_match_rate", "seed"],
    )
    if "seed" not in needle.columns and "run_id" in needle.columns:
        needle["seed"] = needle["run_id"].map(_extract_seed_from_run_id)
    needle = _to_numeric(needle, ["seed"])
    needle_keys = [c for c in ["model_id", "hardware", "kv_mode", "seq_len"] if c in needle.columns]
    needle_summary = _agg_mean_std(
        needle,
        needle_keys,
        ["needle_pass_rate", "needle_exact_match_rate"],
    )
    if not needle_summary.empty:
        needle_summary = _add_ci95_columns(needle_summary)
        _save_table(needle_summary, tables_dir / "needle_summary.csv")
        if "seq_len" in needle_summary.columns and "needle_pass_rate_mean" in needle_summary.columns:
            _plot_lines(
                needle_summary,
                x="seq_len",
                y="needle_pass_rate_mean",
                hue="kv_mode",
                title="Needle Pass Rate vs Context Len",
                xlabel="Context length (tokens)",
                ylabel="Pass rate (%)",
                out_path=plots_dir / "needle_pass_rate_vs_context.png",
                yerr="needle_pass_rate_ci95_half",
            )
        if "needle_exact_match_rate_mean" in needle_summary.columns:
            exact = needle_summary.dropna(subset=["needle_exact_match_rate_mean"], how="all")
            if not exact.empty:
                _plot_lines(
                    exact,
                    x="seq_len",
                    y="needle_exact_match_rate_mean",
                    hue="kv_mode",
                    title="Needle Exact Match Rate vs Context Len",
                    xlabel="Context length (tokens)",
                    ylabel="Exact match rate (%)",
                    out_path=plots_dir / "needle_exact_match_vs_context.png",
                    yerr="needle_exact_match_rate_ci95_half",
                )

    # Needle details (curve over depth)
    needle_details = _read_csvs(runs_dir, ["needle_details_*.csv"])
    needle_details = _to_numeric(needle_details, ["context_len", "depth", "passed"])
    if not needle_details.empty and {"kv_mode", "context_len", "depth", "passed"}.issubset(needle_details.columns):
        curve = (
            needle_details.groupby(["kv_mode", "context_len", "depth"], dropna=False)["passed"]
            .mean()
            .reset_index()
            .rename(columns={"passed": "pass_rate"})
        )
        _save_table(curve, tables_dir / "needle_curve_by_depth.csv")
        for context_len, sub_ctx in sorted(curve.groupby("context_len")):
            out_path = plots_dir / f"needle_curve_depth_ctx{int(context_len)}.png"
            _plot_lines(
                sub_ctx,
                x="depth",
                y="pass_rate",
                hue="kv_mode",
                title=f"Needle Pass Rate vs Depth (context_len={int(context_len)})",
                xlabel="Needle depth (%)",
                ylabel="Pass rate (0-1, mean)",
                out_path=out_path,
            )

    # Significance / paired-difference summaries by seed.
    pairings = [
        ("int8_baseline", "int8_ours"),
        ("int4_fused", "int4_ours"),
    ]
    sig_frames = []
    sig_latency = _significance_summary(
        latency,
        metric_col="tpot_ms",
        key_cols=["seq_len", "gen_len", "batch"],
        pairings=pairings,
        metric_name="tpot_ms",
    )
    if not sig_latency.empty:
        sig_frames.append(sig_latency)
    sig_ppl = _significance_summary(
        ppl,
        metric_col="perplexity",
        key_cols=["seq_len", "ppl_mode", "chunk_size"],
        pairings=pairings,
        metric_name="perplexity",
    )
    if not sig_ppl.empty:
        sig_frames.append(sig_ppl)
    sig_needle = _significance_summary(
        needle,
        metric_col="needle_pass_rate",
        key_cols=["seq_len"],
        pairings=pairings,
        metric_name="needle_pass_rate",
    )
    if not sig_needle.empty:
        sig_frames.append(sig_needle)

    if sig_frames:
        significance_summary = pd.concat(sig_frames, ignore_index=True)
        _save_table(significance_summary, tables_dir / "significance_summary.csv")

    # Relative gain summary table for thesis discussion.
    pairings = [
        ("int8_baseline", "int8_ours"),
        ("int4_fused", "int4_ours"),
        ("int4_ours", "int4_ours_mixed"),
        ("fp16", "int8_ours"),
        ("fp16", "int4_ours"),
    ]
    gain_frames = []
    gain_frames.append(
        _relative_gain_table(
            latency_summary,
            metric_col="tpot_ms_mean",
            metric_name="tpot_ms",
            key_cols=["seq_len", "gen_len", "batch"],
            pairings=pairings,
            higher_is_better=False,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            latency_summary,
            metric_col="tok_per_s_mean",
            metric_name="tok_per_s",
            key_cols=["seq_len", "gen_len", "batch"],
            pairings=pairings,
            higher_is_better=True,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            memory_summary,
            metric_col="kv_cache_mem_mb_mean",
            metric_name="kv_cache_mem_mb",
            key_cols=["seq_len", "gen_len", "batch"],
            pairings=pairings,
            higher_is_better=False,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            ppl_summary,
            metric_col="perplexity_mean",
            metric_name="perplexity",
            key_cols=["seq_len", "ppl_mode", "chunk_size"],
            pairings=pairings,
            higher_is_better=False,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            needle_summary,
            metric_col="needle_pass_rate_mean",
            metric_name="needle_pass_rate",
            key_cols=["seq_len"],
            pairings=pairings,
            higher_is_better=True,
        )
    )
    gain_frames = [g for g in gain_frames if not g.empty]
    if gain_frames:
        gain_summary = pd.concat(gain_frames, ignore_index=True)
        _save_table(gain_summary, tables_dir / "relative_gain_summary.csv")

    main_claims = _main_claims_32k_table(
        latency_summary=latency_summary,
        memory_summary=memory_summary,
        needle_summary=needle_summary,
        ppl_summary=ppl_summary,
        target_seq_len=32704,
    )
    if not main_claims.empty:
        _save_table(main_claims, tables_dir / "thesis_main_claims_32k.csv")

    print(f"Wrote tables to {tables_dir} and plots to {plots_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
