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
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
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


def _save_table(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def _plot_lines(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
) -> None:
    if df.empty:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    for label, sub in sorted(df.groupby(hue)):
        sub = sub.sort_values(x)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate results into tables and plots")
    parser.add_argument("--runs_dir", type=str, default="results/runs")
    parser.add_argument("--tables_dir", type=str, default="results/tables")
    parser.add_argument("--plots_dir", type=str, default="results/plots")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    tables_dir = Path(args.tables_dir)
    plots_dir = Path(args.plots_dir)

    if not runs_dir.exists():
        print(f"runs_dir not found: {runs_dir}")
        return 2

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
        ],
    )
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
        ],
    )
    if not latency_summary.empty:
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
            )

        # Batch throughput curve (throughput vs batch).
        target_seq = _pick_seq_len_for_batch_curves(latency_summary, preferred=8192)
        if target_seq is not None and {"batch", "tok_per_s_mean", "kv_mode"}.issubset(latency_summary.columns):
            lat_batch = latency_summary[latency_summary["seq_len"] == target_seq]
            if "gen_len" in lat_batch.columns and (lat_batch["gen_len"] == 128).any():
                lat_batch = lat_batch[lat_batch["gen_len"] == 128]
            if not lat_batch.empty:
                _save_table(lat_batch, tables_dir / "throughput_by_batch.csv")
                _plot_lines(
                    lat_batch,
                    x="batch",
                    y="tok_per_s_mean",
                    hue="kv_mode",
                    title=f"Throughput vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="Tokens per second (total, mean)",
                    out_path=plots_dir / "throughput_tok_per_s_vs_batch.png",
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
            )

        target_seq = _pick_seq_len_for_batch_curves(memory_summary, preferred=8192)
        if target_seq is not None and {"batch", "gpu_mem_peak_mb_mean", "kv_mode"}.issubset(memory_summary.columns):
            mem_batch = memory_summary[memory_summary["seq_len"] == target_seq]
            if "gen_len" in mem_batch.columns and (mem_batch["gen_len"] == 128).any():
                mem_batch = mem_batch[mem_batch["gen_len"] == 128]
            if not mem_batch.empty:
                _plot_lines(
                    mem_batch,
                    x="batch",
                    y="gpu_mem_peak_mb_mean",
                    hue="kv_mode",
                    title=f"Peak GPU Memory vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="Peak GPU memory (MB, mean)",
                    out_path=plots_dir / "memory_peak_vs_batch.png",
                )
        if target_seq is not None and {"batch", "kv_cache_mem_mb_mean", "kv_mode"}.issubset(memory_summary.columns):
            mem_batch = memory_summary[memory_summary["seq_len"] == target_seq]
            if "gen_len" in mem_batch.columns and (mem_batch["gen_len"] == 128).any():
                mem_batch = mem_batch[mem_batch["gen_len"] == 128]
            if not mem_batch.empty:
                _plot_lines(
                    mem_batch,
                    x="batch",
                    y="kv_cache_mem_mb_mean",
                    hue="kv_mode",
                    title=f"KV Cache Memory vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="KV cache memory (MB, mean)",
                    out_path=plots_dir / "memory_kv_cache_vs_batch.png",
                )

    # PPL
    ppl = _read_csvs(runs_dir, ["profile_ppl_*.csv"])
    ppl = _to_numeric(ppl, ["seq_len", "batch", "perplexity", "tokens_evaluated"])
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
            )

    # Needle (summary)
    needle = _read_csvs(runs_dir, ["profile_needle_*.csv"])
    needle = _to_numeric(needle, ["seq_len", "needle_pass_rate"])
    needle_keys = [c for c in ["model_id", "hardware", "kv_mode", "seq_len"] if c in needle.columns]
    needle_summary = _agg_mean_std(needle, needle_keys, ["needle_pass_rate"])
    if not needle_summary.empty:
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

    print(f"Wrote tables to {tables_dir} and plots to {plots_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
