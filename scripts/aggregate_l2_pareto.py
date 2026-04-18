#!/usr/bin/env python3
"""Aggregate L2 Pareto raw outputs into one table and a Pareto front."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


QUALITY_TASKS = ("narrativeqa", "hotpotqa", "gov_report", "dureader", "lcc")


def _read_manifest(manifest_path: Path) -> dict:
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _scan_quality(policy_dir: Path) -> dict[str, float]:
    scores: dict[str, float] = {}
    for path in sorted(policy_dir.glob("longbench_task_summary_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                task = row.get("task_name", "")
                if task not in QUALITY_TASKS:
                    continue
                try:
                    scores[task] = float(row["official_metric_value"])
                except (KeyError, TypeError, ValueError):
                    continue
    return scores


def _scan_first_value(policy_dir: Path, prefix: str, column: str) -> float | None:
    for path in sorted(policy_dir.glob(f"{prefix}_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            continue
        try:
            return float(rows[0][column])
        except (KeyError, TypeError, ValueError):
            continue
    return None


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def build_table(raw_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for manifest_path in sorted(raw_dir.rglob("manifest.json")):
        policy_dir = manifest_path.parent
        manifest = _read_manifest(manifest_path)
        quality_scores = _scan_quality(policy_dir)
        primary_quality = _mean([quality_scores[t] for t in ("narrativeqa", "hotpotqa", "gov_report") if t in quality_scores])
        extend_quality = _mean([quality_scores[t] for t in ("dureader", "lcc") if t in quality_scores])
        ttft = _scan_first_value(policy_dir, "profile_latency", "ttft_ms")
        tpot = _scan_first_value(policy_dir, "profile_latency", "tpot_ms")
        peak_mem = _scan_first_value(policy_dir, "profile_memory", "gpu_mem_peak_mb")
        ppl = _scan_first_value(policy_dir, "profile_ppl", "perplexity")
        needle = _scan_first_value(policy_dir, "profile_needle", "needle_pass_rate")
        rows.append(
            {
                "model_key": str(manifest["model_key"]),
                "model_id": str(manifest["model_id"]),
                "policy_id": str(manifest["policy_id"]),
                "policy_json": str(manifest["policy_json"]),
                "avg_bits": "" if manifest.get("avg_bits") is None else f"{float(manifest['avg_bits']):.4f}",
                "quality_core": "" if primary_quality is None else f"{primary_quality:.4f}",
                "quality_extend": "" if extend_quality is None else f"{extend_quality:.4f}",
                "ttft_ms": "" if ttft is None else f"{ttft:.4f}",
                "tpot_ms": "" if tpot is None else f"{tpot:.4f}",
                "peak_mem_mb": "" if peak_mem is None else f"{peak_mem:.4f}",
                "ppl": "" if ppl is None else f"{ppl:.4f}",
                "needle_pass_rate": "" if needle is None else f"{needle:.4f}",
            }
        )
    rows.sort(key=lambda row: (row["model_key"], row["policy_id"]))
    return rows


def _dominates(a: dict[str, str], b: dict[str, str]) -> bool:
    if a["model_key"] != b["model_key"]:
        return False
    if not a["quality_core"] or not b["quality_core"]:
        return False
    if not a["tpot_ms"] or not b["tpot_ms"]:
        return False

    qa = float(a["quality_core"])
    qb = float(b["quality_core"])
    ca = float(a["tpot_ms"])
    cb = float(b["tpot_ms"])
    better_or_equal = qa >= qb and ca <= cb
    strictly_better = qa > qb or ca < cb
    return better_or_equal and strictly_better


def build_front(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    front: list[dict[str, str]] = []
    for row in rows:
        dominated = False
        for other in rows:
            if other is row:
                continue
            if _dominates(other, row):
                dominated = True
                break
        if not dominated:
            front.append(row)
    front.sort(key=lambda row: (row["model_key"], -(float(row["quality_core"]) if row["quality_core"] else -math.inf)))
    return front


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate L2 Pareto raw profiles.", allow_abbrev=False)
    parser.add_argument("--raw_dir", required=True)
    parser.add_argument("--out_table", required=True)
    parser.add_argument("--out_front", required=True)
    parser.add_argument("--out_plot_csv", required=True)
    args = parser.parse_args()

    rows = build_table(Path(args.raw_dir))
    if not rows:
        raise SystemExit(f"No Pareto manifests found under {args.raw_dir}")
    front = build_front(rows)

    fieldnames = [
        "model_key",
        "model_id",
        "policy_id",
        "policy_json",
        "avg_bits",
        "quality_core",
        "quality_extend",
        "ttft_ms",
        "tpot_ms",
        "peak_mem_mb",
        "ppl",
        "needle_pass_rate",
    ]
    for out_path_str, table in ((args.out_table, rows), (args.out_front, front), (args.out_plot_csv, rows)):
        out_path = Path(out_path_str)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(table)

    print(f"Saved Pareto table: {args.out_table}")
    print(f"Saved Pareto front: {args.out_front}")
    print(f"Saved plot CSV:     {args.out_plot_csv}")


if __name__ == "__main__":
    main()
