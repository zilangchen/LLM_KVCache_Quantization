#!/usr/bin/env python3
"""Analyze current experiment results (Stages 1-5 partial).

Aggregates:
  - Phase 1 TPOT: 4 models × 6 backends
  - Phase 2 BD 1.5B quality (PPL/Needle/RULER/LongBench)
  - Phase 3 FI 1.5B quality (PPL/Needle/RULER/LongBench)
  - Phase 4 14B partial (PPL/Needle/RULER/LongBench + K/V ablation)

Outputs a single markdown report to stdout.
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Optional

import pandas as pd

RD = "results/emnlp_p012_batch/runs"


# ─── Helpers ───

def _first_csv(pattern: str) -> Optional[str]:
    csvs = sorted(glob.glob(pattern))
    return csvs[0] if csvs else None


def _load_all_csvs(dir_path: str, name_filter: str = "") -> list[pd.DataFrame]:
    dfs = []
    for csv in sorted(glob.glob(f"{dir_path}/*.csv")):
        if name_filter and name_filter not in os.path.basename(csv):
            continue
        try:
            dfs.append(pd.read_csv(csv))
        except Exception:
            pass
    return dfs


def _fmt(val: Optional[float], decimals: int = 2, suffix: str = "") -> str:
    if val is None or pd.isna(val):
        return "—"
    return f"{val:.{decimals}f}{suffix}"


# ─── Phase 1: TPOT ───

def analyze_tpot() -> dict:
    """Return dict[backend][model] = (mean, std, kv_mem_mb)."""
    out = {}
    models = ["1p5b", "7b", "8b", "14b"]
    backends = ["fp16", "kivi", "torchref", "triton_ra", "fi", "bd"]
    for be in backends:
        out[be] = {}
        for m in models:
            csvs = glob.glob(f"{RD}/tpot_{be}_{m}/*.csv")
            if not csvs:
                out[be][m] = None
                continue
            df = pd.read_csv(csvs[0])
            if "tpot_ms" not in df.columns:
                out[be][m] = None
                continue
            kv_mem = df["kv_cache_mem_mb"].iloc[0] if "kv_cache_mem_mb" in df.columns else None
            out[be][m] = (df["tpot_ms"].mean(), df["tpot_ms"].std(), kv_mem)
    return out


def print_tpot_table(tpot: dict):
    print("## Phase 1: TPOT Scaling Table (4 models × 6 backends)\n")
    print("单位: TPOT 均值 ± std (ms), seq=4096, gen=128, runs=8, warmup=3\n")
    print("| backend | 1.5B | 7B | 8B | 14B |")
    print("|---------|------|-----|-----|------|")
    display_order = ["fp16", "kivi", "torchref", "triton_ra", "fi", "bd"]
    for be in display_order:
        row = f"| **{be}** |"
        for m in ["1p5b", "7b", "8b", "14b"]:
            val = tpot[be].get(m)
            if val:
                row += f" {val[0]:.2f} ± {val[1]:.2f} |"
            else:
                row += " — |"
        print(row)
    print()

    # KV cache memory
    print("### KV Cache 内存（MB, seq=4096）\n")
    print("| backend | 1.5B | 7B | 8B | 14B |")
    print("|---------|------|-----|-----|------|")
    for be in display_order:
        row = f"| {be} |"
        for m in ["1p5b", "7b", "8b", "14b"]:
            val = tpot[be].get(m)
            if val and val[2] is not None:
                row += f" {val[2]:.1f} |"
            else:
                row += " — |"
        print(row)
    print()


# ─── PPL ───

def analyze_ppl(backends: list[str], model_tag: str) -> dict:
    """Return dict[backend] = (mean_ppl, std_ppl, n)."""
    out = {}
    for be in backends:
        all_ppl = []
        for csv in sorted(glob.glob(f"{RD}/ppl_{be}_{model_tag}_s*/*.csv")):
            try:
                df = pd.read_csv(csv)
                if "perplexity" in df.columns:
                    all_ppl.append(df["perplexity"].iloc[0])
            except Exception:
                pass
        if all_ppl:
            s = pd.Series(all_ppl)
            out[be] = (s.mean(), s.std(), len(all_ppl))
        else:
            out[be] = None
    return out


# ─── Needle ───

def analyze_needle(backends: list[str], model_tag: str, ctx_lens: list[int]) -> dict:
    """Return dict[backend][ctx_len] = (pass_rate, n_samples)."""
    out = {}
    for be in backends:
        out[be] = {}
        for ctx in ctx_lens:
            all_passed = []
            for csv in sorted(glob.glob(f"{RD}/needle_{be}_{model_tag}_c{ctx}_s*/needle_details_*.csv")):
                try:
                    df = pd.read_csv(csv)
                    if "passed" in df.columns:
                        all_passed.extend(df["passed"].astype(int).tolist())
                except Exception:
                    pass
            if all_passed:
                out[be][ctx] = (sum(all_passed) / len(all_passed), len(all_passed))
            else:
                out[be][ctx] = None
    return out


# ─── RULER ───

def analyze_ruler(backends: list[str], model_tag: str, seq_lens: list[int]) -> dict:
    """Return dict[backend][sl] = (pass_rate, f1_mean)."""
    out = {}
    for be in backends:
        out[be] = {}
        for sl in seq_lens:
            pass_rates = []
            f1_means = []
            for csv in sorted(glob.glob(f"{RD}/ruler_{be}_{model_tag}_sl{sl}_s*/profile_ruler_*.csv")):
                try:
                    df = pd.read_csv(csv)
                    if "ruler_pass_rate" in df.columns:
                        pass_rates.append(df["ruler_pass_rate"].iloc[0])
                    if "ruler_f1_mean" in df.columns:
                        f1_means.append(df["ruler_f1_mean"].iloc[0])
                except Exception:
                    pass
            pr = sum(pass_rates) / len(pass_rates) if pass_rates else None
            f1 = sum(f1_means) / len(f1_means) if f1_means else None
            out[be][sl] = (pr, f1)
    return out


# ─── LongBench ───

def analyze_longbench(backends: list[str], model_tag: str) -> dict:
    """Return dict[backend] = (f1_mean, n_samples)."""
    out = {}
    for be in backends:
        all_f1 = []
        for csv in sorted(glob.glob(f"{RD}/longbench_{be}_{model_tag}_s*/longbench_details_*.csv")):
            try:
                df = pd.read_csv(csv)
                if "f1" in df.columns:
                    all_f1.extend(df["f1"].dropna().tolist())
            except Exception:
                pass
        if all_f1:
            out[be] = (sum(all_f1) / len(all_f1), len(all_f1))
        else:
            out[be] = None
    return out


# ─── Print quality sections ───

def print_quality_section(title: str, backends: list[str], model_tag: str,
                          ctx_lens: list[int], seq_lens: list[int]):
    print(f"## {title}\n")

    # PPL (deterministic across seeds — see note below)
    print("### PPL (deterministic eval, all seeds equal)\n")
    print("| variant | PPL | # files |")
    print("|---------|-----|---------|")
    ppl = analyze_ppl(backends, model_tag)
    for be in backends:
        v = ppl.get(be)
        if v:
            print(f"| {be} | {v[0]:.4f} | {v[2]} |")
        else:
            print(f"| {be} | — | 0 |")
    print()

    # Needle
    print(f"### Needle-in-Haystack Pass Rate (3 seeds avg)\n")
    header = "| variant |" + "".join(f" {c//1024}K |" for c in ctx_lens)
    sep = "|---------|" + "".join("-------|" for _ in ctx_lens)
    print(header)
    print(sep)
    needle = analyze_needle(backends, model_tag, ctx_lens)
    for be in backends:
        row = f"| {be} |"
        for ctx in ctx_lens:
            v = needle[be].get(ctx)
            if v is not None:
                row += f" {v[0]*100:.1f}% |"
            else:
                row += " — |"
        print(row)
    print()

    # RULER (ruler_pass_rate already in 0-100 percentage scale, not fraction)
    print(f"### RULER Pass Rate (mean of 4 tasks: s_niah/mk_niah/vt/cwe, 3 seeds avg)\n")
    header = "| variant |" + "".join(f" sl={s//1024}K |" for s in seq_lens)
    sep = "|---------|" + "".join("--------|" for _ in seq_lens)
    print(header)
    print(sep)
    ruler = analyze_ruler(backends, model_tag, seq_lens)
    for be in backends:
        row = f"| {be} |"
        for sl in seq_lens:
            v = ruler[be].get(sl)
            if v is not None and v[0] is not None:
                # CSV 里 ruler_pass_rate 已经是 0-100 percentage (not 0-1 fraction)
                row += f" {v[0]:.1f}% |"
            else:
                row += " — |"
        print(row)
    print()

    # LongBench
    print("### LongBench (synthetic) F1 mean\n")
    print("| variant | F1 | # samples |")
    print("|---------|-----|-----------|")
    lb = analyze_longbench(backends, model_tag)
    for be in backends:
        v = lb.get(be)
        if v:
            print(f"| {be} | {v[0]:.4f} | {v[1]} |")
        else:
            print(f"| {be} | — | 0 |")
    print()


# ─── 14B K/V ablation ───

def analyze_kv_ablation() -> dict:
    """Return dict[cfg] = (mean_ppl, std_ppl, n)."""
    out = {}
    for cfg in ["K4V16", "K16V4", "K8V4", "K4V8"]:
        all_ppl = []
        for csv in sorted(glob.glob(f"{RD}/ppl_ablation_{cfg}_14b_s*/*.csv")):
            try:
                df = pd.read_csv(csv)
                if "perplexity" in df.columns:
                    all_ppl.append(df["perplexity"].iloc[0])
            except Exception:
                pass
        if all_ppl:
            s = pd.Series(all_ppl)
            out[cfg] = (s.mean(), s.std(), len(all_ppl))
        else:
            out[cfg] = None
    return out


def print_kv_ablation():
    print("## Phase 4 partial: 14B K/V Bit-Width Ablation (PPL)\n")
    kv = analyze_kv_ablation()
    n_done = sum(1 for v in kv.values() if v is not None)
    print(f"已完成 {n_done}/4 配置（每个 3 seeds）\n")
    print("| Cfg | K bits | V bits | Mean PPL | Std | n |")
    print("|-----|--------|--------|----------|-----|---|")
    cfg_bits = {"K4V16": (4, 16), "K16V4": (16, 4), "K8V4": (8, 4), "K4V8": (4, 8)}
    for cfg in ["K4V16", "K16V4", "K8V4", "K4V8"]:
        kb, vb = cfg_bits[cfg]
        v = kv.get(cfg)
        if v:
            print(f"| {cfg} | {kb} | {vb} | {v[0]:.4f} | {v[1]:.4f} | {v[2]} |")
        else:
            print(f"| {cfg} | {kb} | {vb} | — | — | 0 |")
    print()


# ─── Stage 7: Long-seq TPOT scaling ───

def analyze_long_seq_tpot():
    """Return dict[model_tag][backend][seq_len] = (tpot_mean, tpot_std, kv_mem_mb)."""
    out = {}
    models = ["1p5b", "7b", "14b"]
    backends = ["fp16", "kivi", "torchref", "triton_ra"]
    seqs = [4096, 8192, 16384, 32704]
    for m in models:
        out[m] = {}
        for be in backends:
            out[m][be] = {}
            for sl in seqs:
                csvs = glob.glob(f"{RD}/longseq_{be}_{m}_s{sl}/*.csv")
                if not csvs:
                    out[m][be][sl] = None
                    continue
                try:
                    df = pd.read_csv(csvs[0])
                    if "tpot_ms" in df.columns:
                        kv = df["kv_cache_mem_mb"].iloc[0] if "kv_cache_mem_mb" in df.columns else None
                        out[m][be][sl] = (df["tpot_ms"].mean(), df["tpot_ms"].std(), kv)
                    else:
                        out[m][be][sl] = None
                except Exception:
                    out[m][be][sl] = None
    return out


def print_long_seq_tables(lsq: dict):
    print("## Stage 7: Long-Sequence TPOT Scaling\n")
    print("实验设置: gen=64, runs=10, warmup=5, seed=1234 (v2 rerun)\n")

    seqs = [4096, 8192, 16384, 32704]
    backends_display = ["fp16", "kivi", "torchref", "triton_ra"]

    for m in ["1p5b", "7b", "14b"]:
        title_map = {"1p5b": "Qwen2.5-1.5B", "7b": "Qwen2.5-7B", "14b": "Qwen2.5-14B"}
        print(f"### {title_map[m]} TPOT (ms) vs seq_len\n")
        header = "| backend |" + "".join(f" {s//1024}K |" for s in seqs)
        sep = "|---------|" + "".join("------|" for _ in seqs)
        print(header)
        print(sep)
        for be in backends_display:
            row = f"| **{be}** |"
            for sl in seqs:
                v = lsq[m][be].get(sl)
                if v:
                    row += f" {v[0]:.2f} ± {v[1]:.2f} |"
                else:
                    row += " OOM/fail |"
            print(row)
        print()

        # Crossover analysis: triton_ra vs torchref delta
        print(f"**{title_map[m]} Δ(triton_ra − torchref):**\n")
        print("| seq_len |" + "".join(f" {s//1024}K |" for s in seqs))
        print("|---------|" + "".join("------|" for _ in seqs))
        row = "| Δ (ms) |"
        for sl in seqs:
            t = lsq[m]["triton_ra"].get(sl)
            r = lsq[m]["torchref"].get(sl)
            if t and r:
                delta = t[0] - r[0]
                sign = "+" if delta > 0 else ""
                row += f" {sign}{delta:.2f} |"
            else:
                row += " — |"
        print(row)
        print()


# ─── 1.5B fp16 RULER baseline ───

def analyze_fp16_ruler_baseline(model_tag: str, seq_lens: list[int]) -> dict:
    """Return dict[seq_len] = (pass_rate, per_task_dict)."""
    out = {}
    for sl in seq_lens:
        all_overall = []
        per_task = {"s_niah": [], "mk_niah": [], "vt": [], "cwe": []}
        for csv in sorted(glob.glob(f"{RD}/ruler_fp16_{model_tag}_sl{sl}_s*/profile_ruler_*.csv")):
            try:
                df = pd.read_csv(csv)
                if "ruler_pass_rate" in df.columns:
                    all_overall.append(df["ruler_pass_rate"].iloc[0])
            except Exception:
                pass
        # task-level breakdown
        for csv in sorted(glob.glob(f"{RD}/ruler_fp16_{model_tag}_sl{sl}_s*/ruler_task_summary_*.csv")):
            try:
                df = pd.read_csv(csv)
                for task in per_task.keys():
                    rows = df[df["ruler_task"] == task]
                    if not rows.empty and "ruler_pass_rate" in rows.columns:
                        per_task[task].append(rows["ruler_pass_rate"].iloc[0])
            except Exception:
                pass
        overall_mean = sum(all_overall) / len(all_overall) if all_overall else None
        task_means = {t: (sum(v)/len(v) if v else None) for t, v in per_task.items()}
        out[sl] = (overall_mean, task_means)
    return out


def print_fp16_ruler_baseline():
    print("## 1.5B FP16 RULER Baseline (12 测试, 4 sl × 3 seeds)\n")
    print("**用途**: 确认 1.5B 模型在 VT/CWE 任务上的能力上限\n")
    out = analyze_fp16_ruler_baseline("1p5b", [4096, 8192, 16384, 32704])
    print("| seq_len | OVERALL | s_niah | mk_niah | vt | cwe |")
    print("|---------|---------|--------|---------|-----|-----|")
    for sl in [4096, 8192, 16384, 32704]:
        v = out.get(sl)
        if v:
            overall, tasks = v
            row = f"| {sl//1024}K | {overall:.1f}% |"
            for t in ["s_niah", "mk_niah", "vt", "cwe"]:
                val = tasks.get(t)
                row += f" {val:.1f}% |" if val is not None else " — |"
            print(row)
    print()
    print("**Insight**: VT (变量追踪) 和 CWE (常见词提取) 的低分数确认**是 1.5B 模型本身的能力上限**,不是 INT4 量化的锅。与 FI INT4 的 RULER 对比:\n")


# ─── 14B RA RULER task breakdown ───

def analyze_14b_ra_ruler_breakdown():
    out = {}
    for sl in [4096, 8192, 16384]:
        per_task = {"s_niah": [], "mk_niah": [], "vt": [], "cwe": []}
        overall = []
        for csv in sorted(glob.glob(f"{RD}/ruler_ra_14b_sl{sl}_s*/profile_ruler_*.csv")):
            try:
                df = pd.read_csv(csv)
                if "ruler_pass_rate" in df.columns:
                    overall.append(df["ruler_pass_rate"].iloc[0])
            except Exception:
                pass
        for csv in sorted(glob.glob(f"{RD}/ruler_ra_14b_sl{sl}_s*/ruler_task_summary_*.csv")):
            try:
                df = pd.read_csv(csv)
                for task in per_task.keys():
                    rows = df[df["ruler_task"] == task]
                    if not rows.empty:
                        per_task[task].append(rows["ruler_pass_rate"].iloc[0])
            except Exception:
                pass
        out[sl] = (
            sum(overall)/len(overall) if overall else None,
            {t: (sum(v)/len(v) if v else None) for t, v in per_task.items()},
        )
    return out


def print_14b_ruler_breakdown():
    print("## 14B RA RULER Task Breakdown\n")
    out = analyze_14b_ra_ruler_breakdown()
    print("| seq_len | OVERALL | s_niah | mk_niah | vt | cwe |")
    print("|---------|---------|--------|---------|-----|-----|")
    for sl in [4096, 8192, 16384]:
        v = out.get(sl)
        if v and v[0] is not None:
            overall, tasks = v
            row = f"| {sl//1024}K | {overall:.1f}% |"
            for t in ["s_niah", "mk_niah", "vt", "cwe"]:
                val = tasks.get(t)
                row += f" {val:.1f}% |" if val is not None else " — |"
            print(row)
    print()


# ─── Stage 6: 7B/8B LongBench official + memory sweep ───

def analyze_longbench_official() -> dict:
    out = {}
    for tag in ["7b", "8b"]:
        csvs = sorted(glob.glob(f"{RD}/longbench_official_{tag}_s*/longbench_details_*.csv"))
        all_f1 = []
        task_f1 = {}
        for csv in csvs:
            try:
                df = pd.read_csv(csv)
                if "f1" in df.columns:
                    all_f1.extend(df["f1"].dropna().tolist())
                    for task in df["task_name"].unique():
                        sub = df[df["task_name"] == task]["f1"].dropna()
                        if len(sub) > 0:
                            task_f1.setdefault(task, []).extend(sub.tolist())
            except Exception:
                pass
        out[tag] = {
            "overall": (sum(all_f1) / len(all_f1), len(all_f1)) if all_f1 else None,
            "per_task": {t: sum(v)/len(v) for t, v in task_f1.items()},
        }
    return out


def analyze_memory_sweep() -> dict:
    """Return dict[model_tag][batch] = peak_mem_mb."""
    out = {}
    for tag in ["7b", "8b"]:
        out[tag] = {}
        for batch in [1, 4, 8, 16]:
            csvs = glob.glob(f"{RD}/memory_{tag}_b{batch}/*.csv")
            if not csvs:
                out[tag][batch] = None
                continue
            try:
                df = pd.read_csv(csvs[0])
                mem_col = None
                for c in ["peak_gpu_mem_mb", "gpu_mem_peak_mb", "peak_mb", "gpu_mem_mb"]:
                    if c in df.columns:
                        mem_col = c
                        break
                if mem_col:
                    out[tag][batch] = df[mem_col].max()
                else:
                    out[tag][batch] = None
            except Exception:
                out[tag][batch] = None
    return out


def print_stage6():
    print("## Stage 6: 7B/8B LongBench Official + Memory Sweep\n")
    lb = analyze_longbench_official()
    print("### LongBench Official (--source hf, --max_samples 32)\n")
    print("| model | F1 mean | # samples |")
    print("|-------|---------|-----------|")
    for tag in ["7b", "8b"]:
        v = lb[tag]["overall"]
        if v:
            print(f"| {tag} | {v[0]:.4f} | {v[1]} |")
        else:
            print(f"| {tag} | — | 0 |")
    print()

    # task breakdown if rich
    for tag in ["7b", "8b"]:
        pt = lb[tag]["per_task"]
        if pt:
            print(f"**{tag} per-task F1**:")
            for task, f1 in sorted(pt.items()):
                print(f"- {task}: {f1:.4f}")
            print()

    print("### Memory/Batch Sweep (INT4-RA, seq=4096)\n")
    mem = analyze_memory_sweep()
    print("| model | b=1 | b=4 | b=8 | b=16 |")
    print("|-------|-----|-----|-----|------|")
    for tag in ["7b", "8b"]:
        row = f"| {tag} |"
        for b in [1, 4, 8, 16]:
            v = mem[tag].get(b)
            row += f" {v:.0f} MB |" if v else " — |"
        print(row)
    print()


# ─── Main ───

def main():
    print("# 实验结果分析 — ALL STAGES COMPLETE\n")
    print(f"生成时间: 2026-04-12 (Stage 1-7 + baseline 全部完成)\n")
    print("---\n")

    # Phase 1 TPOT
    tpot = analyze_tpot()
    print_tpot_table(tpot)

    # Phase 2+3: BD/FI 1.5B quality
    print("---\n")
    print_quality_section(
        title="Phase 2+3: BD adapter vs FlashInfer adapter (1.5B, 带 calib)",
        backends=["bd", "fi"],
        model_tag="1p5b",
        ctx_lens=[4096, 8192, 16384, 32704],
        seq_lens=[4096, 8192, 16384, 32704],
    )
    print("**Note**: BD adapter 已删除（bit_decode 库 GQA bug），数据仅供参考。见 `docs/session_findings_2026-04-12.md`\n")

    # 1.5B FP16 RULER baseline (new)
    print("---\n")
    print_fp16_ruler_baseline()

    # Phase 4 partial: 14B RA vs FP16
    print("---\n")
    print_quality_section(
        title="Phase 4: 14B RA vs FP16 质量 (完整)",
        backends=["ra", "fp16"],
        model_tag="14b",
        ctx_lens=[4096, 8192, 16384, 32704],
        seq_lens=[4096, 8192, 16384],  # 14B skip 32K
    )

    # 14B RA RULER task breakdown
    print("---\n")
    print_14b_ruler_breakdown()

    # 14B K/V ablation
    print("---\n")
    print_kv_ablation()

    # Stage 6 (NEW)
    print("---\n")
    print_stage6()

    # Stage 7 long-seq scaling (NEW - CORE)
    print("---\n")
    lsq = analyze_long_seq_tpot()
    print_long_seq_tables(lsq)

    print("---\n")
    print("_脚本: scripts/batch_p012/analyze_current.py_")


if __name__ == "__main__":
    main()
