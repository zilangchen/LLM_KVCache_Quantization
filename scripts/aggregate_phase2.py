#!/usr/bin/env python3
"""
Phase 2 编号 6 M4: Allocator MVP 结果聚合

读取 results/phase2_allocator_mvp/ 下的 15 组 CSV（3 tasks × 5 policies），
主键按 (task, kv_mode, policy_name) 区分——5 组 policy 都是 kv_mode=int4_mixed_kv，
必须用 policy_name 维度避免互相覆盖（Codex 修订 3 关键点）。

从 run_name 正则解析 policy_name：
  phase2_1p5b_int4mixedkv_{POLICY}_{TASK}_n50

输出:
  - results/phase2_summary.csv    (15 行 × schema)
  - docs/phase2_main_table.md     (3 task × 5 policy 宽表 + M4 硬 gate 判定)

用法:
  python3 scripts/aggregate_phase2.py \
    --runs_dir results/phase2_allocator_mvp/ \
    --out_csv results/phase2_summary.csv \
    --out_md docs/phase2_main_table.md
"""
import argparse
import csv
import re
from pathlib import Path
from collections import defaultdict

UNIFIED_FIELDS = [
    "model", "task", "kv_mode", "policy_name",
    "n_samples", "score", "metric_name",
    "f1_mean", "exact_match_rate", "contains_match_rate",
    "latency_ttft_ms", "latency_tpot_ms", "gpu_peak_mem_mb",
    "seq_len", "gen_len", "timestamp", "git_commit", "run_name",
]

# 5 policies 顺序（与 phase2_allocator_mvp.sh 一致）
POLICY_ORDER = [
    "uniform_int4_k4v4",
    "uniform_int8_k8v8",
    "bakv_top3",
    "heuristic_top3",
    "random3_seed42",
]

# Short label for main table
POLICY_LABEL = {
    "uniform_int4_k4v4": "Uniform INT4",
    "uniform_int8_k8v8": "Uniform INT8",
    "bakv_top3":         "BAKV Top-3",
    "heuristic_top3":    "Heuristic-3",
    "random3_seed42":    "Random-3 (seed42)",
}

RUN_NAME_RE = re.compile(
    r"phase2_1p5b_int4mixedkv_(?P<policy>[a-z0-9_]+?)_(?P<task>narrativeqa|hotpotqa|gov_report)_n\d+"
)


def parse_csv(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def find_pairs(runs_dir: Path):
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


def policy_from_run_name(run_name: str):
    m = RUN_NAME_RE.match(run_name or "")
    if not m:
        return None, None
    return m.group("policy"), m.group("task")


def unify_row(task_row, profile_row):
    run_name = profile_row.get("run_name", "")
    policy_name, task_from_name = policy_from_run_name(run_name)
    task = task_row.get("task_name", "") or task_from_name or ""
    return {
        "model": profile_row.get("model_id", ""),
        "task": task,
        "kv_mode": task_row.get("kv_mode", ""),
        "policy_name": policy_name or "",
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
        "run_name": run_name,
    }


def build_main_table_and_gate(rows):
    by_task = defaultdict(dict)  # by_task[task][policy_name] = row
    for r in rows:
        if not r["policy_name"]:
            continue
        by_task[r["task"]][r["policy_name"]] = r

    lines = []
    lines.append("# Phase 2 编号 6 M3 主表：Layer-wise Allocator MVP（Qwen2.5-1.5B）")
    lines.append("")
    lines.append("kv_mode 固定 `int4_mixed_kv`；5 policy 按 `(task, policy_name)` 区分。所有非 uniform policy avg_bits=4.429（3 层 INT8 + 25 层 INT4）。")
    lines.append("")
    headers = ["task", "metric"] + [POLICY_LABEL[p] for p in POLICY_ORDER]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Absolute scores row per task
    for task in sorted(by_task.keys()):
        row_list = by_task[task]
        any_r = next(iter(row_list.values()))
        metric = any_r.get("metric_name", "?")
        cells = [task, metric]
        for p in POLICY_ORDER:
            if p in row_list:
                try:
                    s = float(row_list[p]["score"])
                    cells.append(f"{s:.3f}")
                except (ValueError, TypeError):
                    cells.append("—")
            else:
                cells.append("—")
        lines.append("| " + " | ".join(cells) + " |")
        # Δ vs Uniform INT4 (下界参考)
        try:
            ref = float(row_list["uniform_int4_k4v4"]["score"])
            delta_cells = [f"↳ Δ vs UInt4", ""]
            for p in POLICY_ORDER:
                if p == "uniform_int4_k4v4":
                    delta_cells.append("(基线)")
                elif p in row_list:
                    try:
                        s = float(row_list[p]["score"])
                        d = (s - ref) / ref * 100 if ref != 0 else 0.0
                        sign = "+" if d >= 0 else ""
                        delta_cells.append(f"{sign}{d:.1f}%")
                    except (ValueError, TypeError):
                        delta_cells.append("—")
                else:
                    delta_cells.append("—")
            lines.append("| " + " | ".join(delta_cells) + " |")
        except (KeyError, ValueError, TypeError):
            pass

    # M4 硬 gate 判定（Codex 修改版 v2）
    lines.append("")
    lines.append("## M4 硬 Gate 判定（Codex 修改版 v2）")
    lines.append("")
    lines.append("**硬 Gate**：BAKV Top-3 平均分 > Random-3 平均分 **且 ≥2/3 tasks 胜**")
    lines.append("")

    bakv_scores = {}
    random_scores = {}
    heuristic_scores = {}
    for task in sorted(by_task.keys()):
        rt = by_task[task]
        try:
            bakv_scores[task] = float(rt["bakv_top3"]["score"])
        except (KeyError, ValueError, TypeError):
            pass
        try:
            random_scores[task] = float(rt["random3_seed42"]["score"])
        except (KeyError, ValueError, TypeError):
            pass
        try:
            heuristic_scores[task] = float(rt["heuristic_top3"]["score"])
        except (KeyError, ValueError, TypeError):
            pass

    common_tasks = sorted(set(bakv_scores.keys()) & set(random_scores.keys()))
    bakv_wins_random = 0
    for task in common_tasks:
        verdict = "BAKV > Random" if bakv_scores[task] > random_scores[task] else "BAKV ≤ Random"
        if bakv_scores[task] > random_scores[task]:
            bakv_wins_random += 1
        lines.append(f"- **{task}**: BAKV={bakv_scores[task]:.3f} vs Random={random_scores[task]:.3f} → {verdict}")

    total_tasks = len(common_tasks)
    if total_tasks > 0:
        bakv_mean = sum(bakv_scores[t] for t in common_tasks) / total_tasks
        random_mean = sum(random_scores[t] for t in common_tasks) / total_tasks
        mean_verdict = "PASS" if bakv_mean > random_mean else "FAIL"
        win_verdict = "PASS" if bakv_wins_random >= max(1, (2 * total_tasks + 2) // 3) else "FAIL"
        # 2/3 tasks: 3 tasks → 2 wins
        threshold = max(1, (2 * total_tasks + 2) // 3) if total_tasks == 3 else max(1, (total_tasks + 1) // 2)
        win_verdict = "PASS" if bakv_wins_random >= 2 else "FAIL"

        lines.append("")
        lines.append(f"- **平均分**: BAKV={bakv_mean:.3f} vs Random={random_mean:.3f} → **{mean_verdict}**")
        lines.append(f"- **任务胜率**: BAKV 胜 {bakv_wins_random}/{total_tasks} tasks → **{win_verdict}** (需要 ≥2/3)")

        hard_gate_pass = (mean_verdict == "PASS") and (win_verdict == "PASS")
        lines.append("")
        if hard_gate_pass:
            lines.append("### 🟢 M4 硬 Gate PASS → 允许进编号 7（Budget Sweep + 消融）")
        else:
            lines.append("### 🔴 M4 硬 Gate FAIL → 退编号 11 收口 v6-stable（Findings 偏下）")

    # 次 Gate: BAKV > Heuristic
    if heuristic_scores and common_tasks:
        lines.append("")
        lines.append("## 次 Gate 参考（加分项）：BAKV Top-3 > Heuristic Top-3 ?")
        lines.append("")
        bakv_wins_heuristic = 0
        for task in common_tasks:
            if task in heuristic_scores:
                h = heuristic_scores[task]
                b = bakv_scores[task]
                if b > h:
                    bakv_wins_heuristic += 1
                verdict = "BAKV > Heuristic" if b > h else "BAKV ≤ Heuristic"
                lines.append(f"- **{task}**: BAKV={b:.3f} vs Heuristic={h:.3f} → {verdict}")
        lines.append("")
        lines.append(f"- **Heuristic 胜率**: BAKV 胜 {bakv_wins_heuristic}/{len(heuristic_scores)} tasks")
        if bakv_wins_heuristic > len(heuristic_scores) / 2:
            lines.append("- **次 Gate 参考**: attention-KL lens 优于位置启发 — 加强 lens 叙事")
        else:
            lines.append("- **次 Gate 参考**: attention-KL lens 未显著优于位置启发 — 论文需弱化 lens 独占性")

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_dir", required=True, type=Path)
    ap.add_argument("--out_csv", required=True, type=Path)
    ap.add_argument("--out_md", required=True, type=Path)
    args = ap.parse_args()

    pairs = find_pairs(args.runs_dir)
    print(f"Found {len(pairs)} run pairs in {args.runs_dir}")

    raw_rows = []
    for key, files in pairs.items():
        if "profile" not in files or "task_summary" not in files:
            print(f"WARN: incomplete pair {key}: {list(files.keys())}")
            continue
        profile_rows = parse_csv(files["profile"])
        task_rows = parse_csv(files["task_summary"])
        if not profile_rows or not task_rows:
            continue
        prof = profile_rows[0]
        for tr in task_rows:
            raw_rows.append(unify_row(tr, prof))

    # Codex 2026-04-18 巡检修复：去重 (task, policy_name) 保留最新 timestamp
    # 防 M3 重启后目录残留的旧 uniform_int4_k4v4 CSV 污染主表/CSV
    latest_by_key = {}
    dropped = 0
    for row in raw_rows:
        key = (row.get("task", ""), row.get("policy_name", ""))
        ts = row.get("timestamp", "")
        existing = latest_by_key.get(key)
        if existing is None:
            latest_by_key[key] = row
        else:
            # ISO 8601 字典序比较等价于时间排序
            if ts > existing.get("timestamp", ""):
                latest_by_key[key] = row
                dropped += 1
                print(f"  dedup: replaced older (task={key[0]}, policy={key[1]}) "
                      f"@ {existing.get('timestamp','?')} with newer @ {ts}")
            else:
                dropped += 1
                print(f"  dedup: kept newer (task={key[0]}, policy={key[1]}) "
                      f"@ {existing.get('timestamp','?')}, dropped older @ {ts}")
    unified_rows = sorted(
        latest_by_key.values(),
        key=lambda r: (r.get("task", ""), r.get("policy_name", "")),
    )
    if dropped > 0:
        print(f"  dedup summary: dropped {dropped} older rows; final {len(unified_rows)} unique (task, policy_name)")

    # Write CSV
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=UNIFIED_FIELDS)
        w.writeheader()
        w.writerows(unified_rows)
    print(f"Wrote {len(unified_rows)} rows to {args.out_csv}")

    # Write main table
    md = build_main_table_and_gate(unified_rows)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote main table to {args.out_md}")
    print()
    print(md)


if __name__ == "__main__":
    main()
