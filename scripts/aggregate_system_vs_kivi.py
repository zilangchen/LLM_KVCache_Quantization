#!/usr/bin/env python3
"""Aggregate system_vs_kivi main-phase quality scores and run G2 Claim Strength judgment.

Reads every ``longbench_task_summary_*.csv`` under
``results/system_vs_kivi/raw/<phase>/<model>/<system>/`` (latest by mtime per cell),
plus auxiliary ``profile_{needle,ruler,ppl,latency,memory}`` summaries for budget
context, and produces:

- ``summary_long.csv``   one row per (model, system, task, metric)
- ``summary_wide.csv``   one row per (model, task) × 3 system columns
- ``g2_judgment.md``     markdown report with cell-level deltas + aggregate L-level

Usage:
    python3 scripts/aggregate_system_vs_kivi.py \
        --raw_dir results/system_vs_kivi/raw/main \
        --models 1p5b,3b,8b,14b,mistral7b \
        --systems kivi_style,rolealign_static,rolealign_allocator_auto_eqmem \
        --tasks narrativeqa,hotpotqa,gov_report,dureader,lcc \
        --out_dir results/system_vs_kivi/aggregate/main
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def _latest_csv(system_dir: Path, pattern: str) -> Path | None:
    candidates = sorted(
        system_dir.glob(pattern),
        key=lambda p: (p.stat().st_mtime, p.name),
    )
    return candidates[-1] if candidates else None


def _read_rows(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def collect_long(raw_dir: Path, models: List[str], systems: List[str]) -> List[dict]:
    """Return flat rows: (model, system, task, metric_name, metric_value).

    Each ``longbench_task_summary_*.csv`` contains exactly one task's row
    (run_system_vs_kivi dispatches one CLI invocation per task). Therefore
    we must collate **all** summaries in the directory, not just the most
    recent — the latter would keep only whichever task ran last.

    If multiple CSVs exist for the same (model, system, task) (e.g. retries),
    the most-recently-modified one wins.
    """
    rows: List[dict] = []
    for model in models:
        for system in systems:
            sys_dir = raw_dir / model / system
            if not sys_dir.is_dir():
                continue
            per_task_latest: Dict[str, Tuple[float, Path, dict]] = {}
            for path in sys_dir.glob("longbench_task_summary_*.csv"):
                mtime = path.stat().st_mtime
                for task_row in _read_rows(path):
                    task_name = task_row.get("task_name", "").strip()
                    if not task_name:
                        continue
                    existing = per_task_latest.get(task_name)
                    if existing is None or mtime > existing[0]:
                        per_task_latest[task_name] = (mtime, path, task_row)
            for task_name, (_, path, task_row) in per_task_latest.items():
                try:
                    value = float(task_row["official_metric_value"])
                except (KeyError, TypeError, ValueError):
                    continue
                rows.append({
                    "model": model,
                    "system": system,
                    "task": task_name,
                    "metric": task_row.get("official_metric_name", "").strip(),
                    "score": value,
                    "kv_mode": task_row.get("kv_mode", "").strip(),
                    "sample_count": int(task_row.get("sample_count", 0) or 0),
                    "source_csv": path.name,
                })
    return rows


def pivot_wide(
    long_rows: List[dict],
    models: List[str],
    systems: List[str],
    tasks: List[str],
) -> Tuple[List[dict], List[str]]:
    """Return wide rows (model, task, <score per system>, delta_vs_kivi) and column order."""
    table: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(dict)
    for r in long_rows:
        table[(r["model"], r["task"])][r["system"]] = r["score"]

    baseline = "kivi_style"
    allocator = "rolealign_allocator_auto_eqmem"
    wide: List[dict] = []
    for model in models:
        for task in tasks:
            cell = table.get((model, task), {})
            row = {"model": model, "task": task}
            for sys_id in systems:
                row[sys_id] = cell.get(sys_id)
            kivi_v = cell.get(baseline)
            alloc_v = cell.get(allocator)
            if kivi_v is not None and alloc_v is not None:
                row["delta_alloc_vs_kivi"] = alloc_v - kivi_v
                row["rel_pct_alloc_vs_kivi"] = (
                    (alloc_v - kivi_v) / kivi_v * 100.0 if kivi_v != 0 else None
                )
            else:
                row["delta_alloc_vs_kivi"] = None
                row["rel_pct_alloc_vs_kivi"] = None
            wide.append(row)
    cols = ["model", "task", *systems, "delta_alloc_vs_kivi", "rel_pct_alloc_vs_kivi"]
    return wide, cols


def judge_g2(
    wide_rows: List[dict],
    *,
    win_threshold: float = 0.5,
    baseline_system: str = "kivi_style",
    allocator_system: str = "rolealign_allocator_auto_eqmem",
) -> dict:
    """Classify each (model, task) cell as win/tie/lose, compute aggregate L-level.

    Thresholds:
      - |delta| <= win_threshold -> tie (absolute; quality metrics here are %-like)
      - delta > threshold -> allocator win
      - delta < -threshold -> allocator lose

    L-level mapping (conservative; user can override by reading the numbers):
      - L1: win rate >= 0.8 AND no (model, task) with lose
      - L2: win rate >= 0.6 AND at most 20% lose
      - L3: win rate >= 0.4 (Pareto advantage only; allocator wins where it counts)
      - L4: otherwise (mechanism only)
    """
    total = wins = ties = loses = 0
    deltas: List[float] = []
    per_cell: List[dict] = []
    for row in wide_rows:
        delta = row.get("delta_alloc_vs_kivi")
        if delta is None:
            continue
        total += 1
        deltas.append(delta)
        if delta > win_threshold:
            label = "win"
            wins += 1
        elif delta < -win_threshold:
            label = "lose"
            loses += 1
        else:
            label = "tie"
            ties += 1
        per_cell.append({
            "model": row["model"],
            "task": row["task"],
            "delta": delta,
            "label": label,
        })

    win_rate = wins / total if total else 0.0
    lose_rate = loses / total if total else 0.0

    # Conservative mapping
    if win_rate >= 0.8 and loses == 0:
        level = "L1_systematic_win"
    elif win_rate >= 0.6 and lose_rate <= 0.2:
        level = "L2_quality_win"
    elif win_rate >= 0.4:
        level = "L3_pareto_advantage"
    else:
        level = "L4_mechanism_only"

    return {
        "total_cells": total,
        "wins": wins,
        "ties": ties,
        "loses": loses,
        "win_rate": win_rate,
        "lose_rate": lose_rate,
        "mean_delta": statistics.mean(deltas) if deltas else 0.0,
        "median_delta": statistics.median(deltas) if deltas else 0.0,
        "min_delta": min(deltas) if deltas else 0.0,
        "max_delta": max(deltas) if deltas else 0.0,
        "level": level,
        "per_cell": per_cell,
        "baseline_system": baseline_system,
        "allocator_system": allocator_system,
        "win_threshold": win_threshold,
    }


def write_long_csv(rows: List[dict], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = ["model", "system", "task", "metric", "score", "kv_mode", "sample_count", "source_csv"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def write_wide_csv(wide_rows: List[dict], cols: List[str], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        writer.writerows(wide_rows)


def write_judgment_md(
    judgment: dict,
    wide_rows: List[dict],
    models: List[str],
    tasks: List[str],
    out_path: Path,
) -> None:
    lines: List[str] = []
    lines.append("# system_vs_kivi Main-Phase G2 Claim Strength Judgment\n")
    lines.append(f"- Baseline system: `{judgment['baseline_system']}`")
    lines.append(f"- Allocator system: `{judgment['allocator_system']}`")
    lines.append(f"- Win threshold (absolute |Δ|): **{judgment['win_threshold']}**\n")
    lines.append("## Aggregate\n")
    lines.append(f"| Metric | Value |\n|---|---|")
    lines.append(f"| Total cells (model × task) | {judgment['total_cells']} |")
    lines.append(f"| Allocator wins | {judgment['wins']} ({judgment['win_rate']*100:.1f}%) |")
    lines.append(f"| Ties | {judgment['ties']} |")
    lines.append(f"| Allocator loses | {judgment['loses']} ({judgment['lose_rate']*100:.1f}%) |")
    lines.append(f"| Mean Δ | {judgment['mean_delta']:+.3f} |")
    lines.append(f"| Median Δ | {judgment['median_delta']:+.3f} |")
    lines.append(f"| Min Δ | {judgment['min_delta']:+.3f} |")
    lines.append(f"| Max Δ | {judgment['max_delta']:+.3f} |")
    lines.append(f"| **G2 Level** | **{judgment['level']}** |\n")

    lines.append("## Per-cell results\n")
    lines.append("| Model | Task | KIVI | RoleAlign static | Allocator auto | Δ (alloc−kivi) | rel % | Label |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in wide_rows:
        def fmt(v):
            if v is None:
                return "—"
            if isinstance(v, float):
                return f"{v:.3f}"
            return str(v)
        cell_label = next(
            (c["label"] for c in judgment["per_cell"]
             if c["model"] == row["model"] and c["task"] == row["task"]),
            "—",
        )
        lines.append(
            f"| {row['model']} | {row['task']} "
            f"| {fmt(row.get('kivi_style'))} "
            f"| {fmt(row.get('rolealign_static'))} "
            f"| {fmt(row.get('rolealign_allocator_auto_eqmem'))} "
            f"| {fmt(row.get('delta_alloc_vs_kivi'))} "
            f"| {fmt(row.get('rel_pct_alloc_vs_kivi'))} "
            f"| {cell_label} |"
        )

    lines.append("\n## Per-model win/lose breakdown\n")
    per_model: Dict[str, Dict[str, int]] = defaultdict(lambda: {"win": 0, "tie": 0, "lose": 0})
    for c in judgment["per_cell"]:
        per_model[c["model"]][c["label"]] += 1
    lines.append("| Model | Wins | Ties | Loses | Win rate |")
    lines.append("|---|---|---|---|---|")
    for model in models:
        stats = per_model.get(model, {"win": 0, "tie": 0, "lose": 0})
        n = sum(stats.values())
        wr = stats["win"] / n if n else 0.0
        lines.append(
            f"| {model} | {stats['win']} | {stats['tie']} | {stats['lose']} "
            f"| {wr*100:.1f}% |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate system_vs_kivi main results + G2 judgment")
    parser.add_argument("--raw_dir", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--systems", required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--win_threshold", type=float, default=0.5)
    args = parser.parse_args()

    models = [x.strip() for x in args.models.split(",") if x.strip()]
    systems = [x.strip() for x in args.systems.split(",") if x.strip()]
    tasks = [x.strip() for x in args.tasks.split(",") if x.strip()]

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    long_rows = collect_long(raw_dir, models, systems)
    wide_rows, cols = pivot_wide(long_rows, models, systems, tasks)
    judgment = judge_g2(wide_rows, win_threshold=args.win_threshold)

    write_long_csv(long_rows, out_dir / "summary_long.csv")
    write_wide_csv(wide_rows, cols, out_dir / "summary_wide.csv")
    write_judgment_md(judgment, wide_rows, models, tasks, out_dir / "g2_judgment.md")
    (out_dir / "g2_judgment.json").write_text(
        json.dumps(judgment, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    print(f"Aggregated {len(long_rows)} long-form rows from {raw_dir}")
    print(f"G2 level: {judgment['level']}  (win_rate={judgment['win_rate']:.1%})")
    print(f"Outputs: {out_dir}/{{summary_long,summary_wide,g2_judgment}}.{{csv,md,json}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
