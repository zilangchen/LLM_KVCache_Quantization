#!/usr/bin/env python3
"""
Phase 1 编号 5 闸门判据自动化检查。

输入 Phase 1 聚合 CSV（aggregate_phase1.py 产出），
按 5 条判据自动打分，输出 PASS/FAIL + 下一步建议。

用法:
  python3 scripts/phase1_gate5_check.py \
    --summary results/phase1_summary.csv \
    --summary_7b results/phase1_summary_7b.csv  # 可选

判据（任意 2 条满足即 "站得住"）：
  1. 至少 1 个量化模式相对 fp16 退化 < 20%
  2. 7B 趋势与 1.5B 基本一致（若有 7B 数据）
  3. 至少 1 个 regime 稳定
  4. quality-memory 存在可讲的 tradeoff
  5. 无关键模式灾难性失效（Codex 修正 4）
     - 定义: 任一量化模式在官方主 metric 上退化 > 50% 即 "灾难性"
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


DEGRADATION_THRESHOLD = 20.0  # 判据 1: <20% 退化
CATASTROPHIC_THRESHOLD = 50.0  # 判据 5: >50% 退化 = 灾难性
MEMORY_COMPRESSION_MIN = 30.0  # 判据 4: 至少 30% 显存节省才算"可讲"


def parse_summary(path: Path) -> dict:
    """解析 aggregate_phase1.py 输出的统一 schema CSV。

    返回: {(task, kv_mode): row_dict}
    """
    if not path.exists():
        return {}
    rows = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            key = (r["task"], r["kv_mode"])
            rows[key] = r
    return rows


def compute_degradation(rows: dict, model_hint: str = "1.5B") -> dict:
    """按 task 计算每个量化 mode 相对 fp16 的退化率（%）。

    返回: {task: {mode: deg_pct}}
    """
    by_task = defaultdict(dict)
    for (task, mode), r in rows.items():
        by_task[task][mode] = r

    deg_map = defaultdict(dict)
    for task, mode_rows in by_task.items():
        if "fp16" not in mode_rows:
            continue
        try:
            fp16 = float(mode_rows["fp16"]["score"])
        except (ValueError, TypeError, KeyError):
            continue
        if fp16 == 0:
            continue
        for mode, r in mode_rows.items():
            if mode == "fp16":
                continue
            try:
                s = float(r["score"])
                deg_pct = (fp16 - s) / fp16 * 100  # 正值 = 变差
                deg_map[task][mode] = deg_pct
            except (ValueError, TypeError):
                continue
    return deg_map


def check_criterion_1(deg_map: dict) -> tuple:
    """判据 1: 至少 1 个量化模式相对 fp16 退化 < 20%"""
    passing_combos = []
    for task, modes in deg_map.items():
        for mode, d in modes.items():
            if d < DEGRADATION_THRESHOLD:
                passing_combos.append(f"{task}/{mode}={d:.1f}%")
    ok = len(passing_combos) > 0
    msg = f"{len(passing_combos)} combinations with degradation <{DEGRADATION_THRESHOLD}%"
    if passing_combos:
        msg += "\n      示例: " + ", ".join(passing_combos[:5])
    return ok, msg


def check_criterion_5(deg_map: dict) -> tuple:
    """判据 5: 无关键模式出现灾难性失效（>50% 退化）"""
    catastrophic = []
    for task, modes in deg_map.items():
        for mode, d in modes.items():
            if d > CATASTROPHIC_THRESHOLD:
                catastrophic.append(f"{task}/{mode}={d:.1f}%")
    ok = len(catastrophic) == 0
    msg = (f"No catastrophic failures" if ok
           else f"CATASTROPHIC: {', '.join(catastrophic[:5])}")
    return ok, msg


def check_criterion_4(rows_1p5b: dict) -> tuple:
    """判据 4: quality-memory tradeoff（至少 1 个量化模式给出 ≥30% 显存节省且非灾难退化）"""
    # 按 task 收集 (mode, score, peak_mem)
    tradeoff_candidates = []
    by_mode = defaultdict(list)
    for (task, mode), r in rows_1p5b.items():
        try:
            mem = float(r.get("gpu_peak_mem_mb", 0))
            score = float(r.get("score", 0))
            by_mode[mode].append((task, score, mem))
        except (ValueError, TypeError):
            continue

    # 以 fp16 作基准，计算 memory 节省 + score 相对保留
    if "fp16" not in by_mode:
        return False, "no fp16 baseline"
    fp16_mems = {task: mem for task, _, mem in by_mode["fp16"]}
    fp16_scores = {task: s for task, s, _ in by_mode["fp16"]}

    for mode in [m for m in by_mode if m != "fp16"]:
        for task, score, mem in by_mode[mode]:
            fp16_mem = fp16_mems.get(task)
            fp16_score = fp16_scores.get(task)
            if not fp16_mem or not fp16_score:
                continue
            mem_saving_pct = (fp16_mem - mem) / fp16_mem * 100
            score_retain_pct = score / fp16_score * 100
            if (mem_saving_pct >= MEMORY_COMPRESSION_MIN
                    and score_retain_pct >= (100 - DEGRADATION_THRESHOLD)):
                tradeoff_candidates.append(
                    f"{task}/{mode}: mem -{mem_saving_pct:.0f}%, quality {score_retain_pct:.1f}%"
                )

    ok = len(tradeoff_candidates) > 0
    msg = (f"{len(tradeoff_candidates)} tradeoff points found"
           if ok else "no combinations meet memory ≥30% + quality ≥80%")
    if tradeoff_candidates:
        msg += "\n      " + "\n      ".join(tradeoff_candidates[:3])
    return ok, msg


def check_criterion_2(deg_1p5b: dict, deg_7b: dict) -> tuple:
    """判据 2: 7B 趋势与 1.5B 基本一致（相同 mode 的退化方向一致）"""
    if not deg_7b:
        return None, "7B data not available (编号 4 未完成，skip)"
    # 按 mode 聚合两模型的平均退化
    mode_avg_1p5b = defaultdict(list)
    mode_avg_7b = defaultdict(list)
    for task, modes in deg_1p5b.items():
        for mode, d in modes.items():
            mode_avg_1p5b[mode].append(d)
    for task, modes in deg_7b.items():
        for mode, d in modes.items():
            mode_avg_7b[mode].append(d)
    # 对每个 mode 比较 1.5B vs 7B 退化的方向/相对量级
    consistent = 0
    total = 0
    msgs = []
    for mode in set(mode_avg_1p5b) & set(mode_avg_7b):
        d_1p5b = sum(mode_avg_1p5b[mode]) / len(mode_avg_1p5b[mode])
        d_7b = sum(mode_avg_7b[mode]) / len(mode_avg_7b[mode])
        total += 1
        # 方向一致（两者同正或同负或都接近 0）
        same_sign = (d_1p5b * d_7b > 0) or (abs(d_1p5b) < 2 and abs(d_7b) < 2)
        if same_sign:
            consistent += 1
        msgs.append(f"{mode}: 1.5B={d_1p5b:+.1f}%, 7B={d_7b:+.1f}%")
    ok = consistent >= max(1, total - 1)  # 允许 1 个 mode 反例
    msg = f"{consistent}/{total} modes consistent\n      " + "\n      ".join(msgs)
    return ok, msg


def check_criterion_3() -> tuple:
    """判据 3: 至少 1 个 regime 稳定——只要至少有一组 (task, mode) 成功跑出有效 score，即算稳定"""
    # 此判据由 summary.csv 的可解析行数代理
    return None, "regime stability: implicit PASS if summary CSV has ≥1 row"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True, type=Path,
                    help="1.5B 的 Phase 1 aggregate 输出（aggregate_phase1.py 产出）")
    ap.add_argument("--summary_7b", type=Path, default=None,
                    help="7B 的同格式 summary（若编号 4 完成则提供）")
    args = ap.parse_args()

    rows_1p5b = parse_summary(args.summary)
    rows_7b = parse_summary(args.summary_7b) if args.summary_7b else {}

    if not rows_1p5b:
        print(f"FATAL: empty or missing summary {args.summary}")
        sys.exit(2)

    deg_1p5b = compute_degradation(rows_1p5b, "1.5B")
    deg_7b = compute_degradation(rows_7b, "7B") if rows_7b else {}

    # 判据评估
    results = []
    results.append(("判据 1 (at least 1 mode <20% degradation)", *check_criterion_1(deg_1p5b)))
    results.append(("判据 5 (no catastrophic failure, >50%)", *check_criterion_5(deg_1p5b)))
    results.append(("判据 4 (quality-memory tradeoff exists)", *check_criterion_4(rows_1p5b)))
    results.append(("判据 2 (7B trend consistent with 1.5B)", *check_criterion_2(deg_1p5b, deg_7b)))
    results.append(("判据 3 (regime stability)", *check_criterion_3()))

    print("=" * 70)
    print("Phase 1 编号 5 闸门判据检查")
    print("=" * 70)
    passed = 0
    available = 0
    for name, ok, msg in results:
        if ok is None:
            icon = "⏸"
        elif ok:
            icon = "✅"
            passed += 1
            available += 1
        else:
            icon = "❌"
            available += 1
        print(f"{icon} {name}")
        print(f"      {msg}")
    print("=" * 70)
    print(f"PASSED: {passed} / {available} 可判定判据")
    print()

    # 决策：任意 2 条满足即通过
    GATE_THRESHOLD = 2
    if passed >= GATE_THRESHOLD:
        print(f"🟢 GATE PASS: {passed} ≥ {GATE_THRESHOLD}")
        print("   → 进入编号 6（Layer-wise Allocator MVP）")
        print("   → 可开始扩展 MixedKVCache.per_layer_bits")
        sys.exit(0)
    else:
        print(f"🔴 GATE FAIL: {passed} < {GATE_THRESHOLD}")
        print("   → 跳编号 11，收口成 'v6-diagnostic' 实证论文")
        print("   → 不得开始 allocator 工作")
        sys.exit(1)


if __name__ == "__main__":
    main()
