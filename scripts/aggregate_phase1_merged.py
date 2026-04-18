#!/usr/bin/env python3
"""
Phase 1 ENG-045-v2 后主表聚合（v1 主目录 + v2 kivi_style 补丁重跑合并）

读取多个 runs_dir，后一个目录的 (kv_mode, task) 覆盖前一个目录的同键。
这样我们可以把 v1 的 fp16/int8_ours/int4_ours_asym 与 v2 的 kivi_style
合并到同一张主表，不破坏任何原始数据。

用法:
  python3 scripts/aggregate_phase1_merged.py \
    --runs_dirs results/phase1_official results/phase1_official_v2 \
    --out_csv results/phase1_summary_merged.csv \
    --out_md docs/phase1_main_table_merged.md
"""
import argparse
import csv
import re
from pathlib import Path
from collections import defaultdict

UNIFIED_FIELDS = [
    "model", "task", "kv_mode", "n_samples",
    "score", "metric_name",
    "f1_mean", "exact_match_rate", "contains_match_rate",
    "latency_ttft_ms", "latency_tpot_ms",
    "gpu_peak_mem_mb", "seq_len", "gen_len",
    "timestamp", "git_commit", "run_name", "source_dir",
]


def parse_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def find_pairs(runs_dir):
    pairs = defaultdict(dict)
    for p in sorted(runs_dir.rglob("*.csv")):
        name = p.name
        m_prof = re.match(r"profile_longbench_(.+?)_([0-9T:\-\.]+)\.csv$", name)
        m_task = re.match(r"longbench_task_summary_(.+?)_([0-9T:\-\.]+)\.csv$", name)
        if m_prof:
            pairs[(m_prof.group(1), m_prof.group(2))]["profile"] = p
        elif m_task:
            pairs[(m_task.group(1), m_task.group(2))]["task_summary"] = p
    return pairs


def unify_row(task_row, profile_row, source_dir):
    return {
        "model": profile_row.get("model_id", ""),
        "task": task_row.get("task_name", ""),
        "kv_mode": task_row.get("kv_mode", ""),
        "n_samples": task_row.get("sample_count", ""),
        "score": task_row.get("official_metric_value", ""),
        "metric_name": task_row.get("official_metric_name", ""),
        "f1_mean": task_row.get("f1_mean", ""),
        "exact_match_rate": task_row.get("exact_match_rate", ""),
        "contains_match_rate": task_row.get("contains_match_rate", ""),
        "latency_ttft_ms": profile_row.get("ttft_ms", ""),
        "latency_tpot_ms": profile_row.get("tpot_ms", ""),
        "gpu_peak_mem_mb": profile_row.get("gpu_mem_peak_mb", ""),
        "seq_len": task_row.get("seq_len", ""),
        "gen_len": task_row.get("gen_len", ""),
        "timestamp": task_row.get("timestamp", ""),
        "git_commit": task_row.get("git_commit", ""),
        "run_name": profile_row.get("run_name", ""),
        "source_dir": source_dir,
    }


def build_main_table(rows):
    by_task = defaultdict(dict)
    for r in rows:
        by_task[r["task"]][r["kv_mode"]] = r

    mode_order = ["fp16", "int8_ours", "kivi_style", "int4_ours_asym"]
    lines = []
    lines.append("# Phase 1 官方 LongBench 主表（Qwen2.5-1.5B, ENG-045-v2 修后合并）")
    lines.append("")
    lines.append("数据源: v1 `results/phase1_official` (fp16/int8_ours/int4_ours_asym) + "
                 "v2 `results/phase1_official_v2` (kivi_style 重跑)")
    lines.append("")
    lines.append("| task | metric | " + " | ".join(mode_order) + " | source (kivi_style) |")
    lines.append("|---|---|" + "|".join(["---"] * (len(mode_order) + 1)) + "|")

    for task in sorted(by_task):
        mode_rows = by_task[task]
        any_r = next(iter(mode_rows.values()))
        metric = any_r.get("metric_name", "?")
        scores = []
        fp16_score = None
        for m in mode_order:
            if m in mode_rows:
                try:
                    sf = float(mode_rows[m]["score"])
                    if m == "fp16":
                        fp16_score = sf
                    scores.append(f"{sf:.2f}")
                except (ValueError, TypeError):
                    scores.append("—")
            else:
                scores.append("—")
        kivi_source = mode_rows.get("kivi_style", {}).get("source_dir", "—").split("/")[-1]
        lines.append(f"| {task} | {metric} | " + " | ".join(scores) + f" | {kivi_source} |")

        if fp16_score is not None and fp16_score != 0:
            deltas = []
            for m in mode_order:
                if m == "fp16":
                    deltas.append("(基线)")
                elif m in mode_rows:
                    try:
                        sf = float(mode_rows[m]["score"])
                        d = (sf - fp16_score) / fp16_score * 100
                        sign = "+" if d >= 0 else ""
                        deltas.append(f"{sign}{d:.1f}%")
                    except (ValueError, TypeError):
                        deltas.append("—")
                else:
                    deltas.append("—")
            lines.append(f"| ↳ Δ vs fp16 |  | " + " | ".join(deltas) + " |  |")

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_dirs", nargs="+", required=True, type=Path,
                    help="按优先级升序列出（后列覆盖前列的同键）")
    ap.add_argument("--out_csv", required=True, type=Path)
    ap.add_argument("--out_md", required=True, type=Path)
    args = ap.parse_args()

    merged = {}  # (kv_mode, task) -> unified row
    for runs_dir in args.runs_dirs:
        if not runs_dir.exists():
            print(f"WARN: {runs_dir} not found, skip")
            continue
        pairs = find_pairs(runs_dir)
        print(f"[{runs_dir}] {len(pairs)} run pairs")
        for key, files in pairs.items():
            if "profile" not in files or "task_summary" not in files:
                continue
            profile_rows = parse_csv(files["profile"])
            task_rows = parse_csv(files["task_summary"])
            if not profile_rows or not task_rows:
                continue
            prof = profile_rows[0]
            for tr in task_rows:
                row = unify_row(tr, prof, str(runs_dir))
                merged_key = (row["kv_mode"], row["task"])
                merged[merged_key] = row  # later runs_dir overrides earlier

    unified_rows = sorted(merged.values(), key=lambda r: (r["task"], r["kv_mode"]))

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=UNIFIED_FIELDS)
        w.writeheader()
        w.writerows(unified_rows)
    print(f"Wrote {len(unified_rows)} unified rows to {args.out_csv}")

    md = build_main_table(unified_rows)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote main table to {args.out_md}")
    print()
    print(md)


if __name__ == "__main__":
    main()
