#!/usr/bin/env python3
"""
Phase 1 编号 3: 官方 LongBench 结果聚合 → 第一张官方主表

读取 results/phase1_official/ 下的 profile_longbench_*.csv 和
longbench_task_summary_*.csv，按 (model, task, kv_mode) 联表合并，
输出统一 schema CSV + Markdown 主表。

用法:
  python3 scripts/aggregate_phase1.py \
    --runs_dir results/phase1_official/ \
    --out_csv results/phase1_summary.csv \
    --out_md docs/phase1_main_table.md
"""
import argparse
import csv
import re
from pathlib import Path
from collections import defaultdict

# Phase 1 统一 schema（对应 plan 要求）
UNIFIED_FIELDS = [
    "model", "task", "kv_mode", "n_samples",
    "score", "metric_name",
    "f1_mean", "exact_match_rate", "contains_match_rate",
    "latency_ttft_ms", "latency_tpot_ms",
    "gpu_peak_mem_mb", "seq_len", "gen_len",
    "timestamp", "git_commit", "run_name",
]


def parse_csv(path: Path) -> list:
    """读取 CSV，返回 list[dict]。"""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def find_pairs(runs_dir: Path) -> dict:
    """
    找出每个 run 的 profile + task_summary CSV 对。
    关键字段: timestamp + kv_mode（文件名已含）
    返回 {run_key: {"profile": path, "task_summary": path}}
    """
    pairs = defaultdict(dict)
    for p in sorted(runs_dir.rglob("*.csv")):
        name = p.name
        # 匹配: profile_longbench_{mode}_{timestamp}.csv
        m_prof = re.match(r"profile_longbench_(.+?)_([0-9T:\-\.]+)\.csv$", name)
        m_task = re.match(r"longbench_task_summary_(.+?)_([0-9T:\-\.]+)\.csv$", name)
        if m_prof:
            key = (m_prof.group(1), m_prof.group(2))
            pairs[key]["profile"] = p
        elif m_task:
            key = (m_task.group(1), m_task.group(2))
            pairs[key]["task_summary"] = p
    return pairs


def unify_row(task_row: dict, profile_row: dict) -> dict:
    """把两个 CSV 行合并为统一 schema。"""
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
    }


def build_main_table(rows: list) -> str:
    """生成 task × kv_mode 主表 Markdown。"""
    # 按 task 组织
    by_task = defaultdict(dict)  # by_task[task][mode] = row
    for r in rows:
        by_task[r["task"]][r["kv_mode"]] = r

    # kv_mode 固定顺序（fp16 基线放第一列）
    mode_order = ["fp16", "int8_ours", "kivi_style", "int4_ours_asym"]

    # 找 fp16 基线用于退化率计算
    lines = []
    lines.append("# Phase 1 官方 LongBench 主表（Qwen2.5-1.5B-Instruct）\n")
    lines.append("| task | metric | " + " | ".join(mode_order) + " |")
    lines.append("|---|---|" + "|".join(["---"] * len(mode_order)) + "|")

    for task in sorted(by_task.keys()):
        mode_rows = by_task[task]
        # 取任一存在的 row 看 metric_name
        any_r = next(iter(mode_rows.values()))
        metric = any_r.get("metric_name", "?")

        # score 行
        scores = []
        fp16_score = None
        for m in mode_order:
            if m in mode_rows:
                s = mode_rows[m].get("score", "")
                try:
                    sf = float(s)
                    if m == "fp16":
                        fp16_score = sf
                    scores.append(f"{sf:.2f}")
                except (ValueError, TypeError):
                    scores.append("—")
            else:
                scores.append("—")
        lines.append(f"| {task} | {metric} | " + " | ".join(scores) + " |")

        # 退化率行（相对 fp16）
        if fp16_score is not None and fp16_score != 0:
            deltas = []
            for i, m in enumerate(mode_order):
                if m == "fp16":
                    deltas.append("(基线)")
                elif m in mode_rows:
                    try:
                        sf = float(mode_rows[m].get("score", ""))
                        delta_pct = (sf - fp16_score) / fp16_score * 100
                        sign = "+" if delta_pct >= 0 else ""
                        deltas.append(f"{sign}{delta_pct:.1f}%")
                    except (ValueError, TypeError):
                        deltas.append("—")
                else:
                    deltas.append("—")
            lines.append(f"| ↳ Δ vs fp16 |  | " + " | ".join(deltas) + " |")

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_dir", required=True, type=Path)
    ap.add_argument("--out_csv", required=True, type=Path)
    ap.add_argument("--out_md", required=True, type=Path)
    args = ap.parse_args()

    pairs = find_pairs(args.runs_dir)
    print(f"Found {len(pairs)} run pairs")

    unified_rows = []
    for key, files in pairs.items():
        if "profile" not in files or "task_summary" not in files:
            print(f"WARN: incomplete pair {key}: {files.keys()}")
            continue
        profile_rows = parse_csv(files["profile"])
        task_rows = parse_csv(files["task_summary"])
        if not profile_rows or not task_rows:
            continue
        # profile 每个 run 1 行；task_summary 每个 task 1 行（这里 1 个任务 1 行）
        prof = profile_rows[0]
        for tr in task_rows:
            unified_rows.append(unify_row(tr, prof))

    # 写 CSV
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=UNIFIED_FIELDS)
        w.writeheader()
        w.writerows(unified_rows)
    print(f"Wrote {len(unified_rows)} unified rows to {args.out_csv}")

    # 写 Markdown 主表
    md = build_main_table(unified_rows)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote main table to {args.out_md}")
    print()
    print(md)


if __name__ == "__main__":
    main()
