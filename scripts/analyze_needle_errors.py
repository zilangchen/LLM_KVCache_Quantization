#!/usr/bin/env python3
"""
Aggregate needle failure modes and optional fused dump diagnostics.

Outputs:
  - results/tables/fused_error_diagnosis.csv
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Tuple


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def classify_needle_error(needle: str, generated: str, passed: int) -> str:
    needle = (needle or "").strip()
    generated = (generated or "").strip()
    if int(passed) == 1 or generated == needle:
        return "exact_match"
    if not generated:
        return "empty_output"
    if needle and needle in generated:
        return "contains_needle_extra_text"
    if generated and generated in needle:
        if len(needle) - len(generated) == 1:
            return "single_char_missing"
        return "truncated_prefix"
    distance = edit_distance(needle, generated)
    if distance == 1:
        return "single_char_edit"
    if distance <= 3:
        return "near_miss_edit_le_3"
    if "lazy dog" in generated.lower():
        return "drift_lazy_dog"
    return "drift_other"


def classify_dump_error(max_abs_diff: float) -> str:
    if max_abs_diff <= 0.05:
        return "fused_match_good"
    if max_abs_diff <= 0.5:
        return "fused_match_warn"
    return "fused_mismatch"


def _iter_csv_rows(paths: Iterable[str]) -> Iterable[Dict[str, str]]:
    for path in paths:
        with open(path, newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row["_source_path"] = path
                yield row


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def collect_rows(needle_glob: str, dump_glob: str) -> list[dict]:
    rows = []
    needle_paths = sorted(glob.glob(needle_glob, recursive=True))
    for row in _iter_csv_rows(needle_paths):
        kv_mode = row.get("kv_mode", "unknown")
        context_len = _safe_int(row.get("context_len"), -1)
        bucket = classify_needle_error(
            needle=row.get("needle", ""),
            generated=row.get("generated_text", ""),
            passed=_safe_int(row.get("passed"), 0),
        )
        rows.append(
            {
                "source": "needle",
                "kv_mode": kv_mode,
                "context_len": context_len,
                "layer": -1,
                "step": -1,
                "error_bucket": bucket,
            }
        )

    dump_paths = sorted(glob.glob(dump_glob, recursive=True))
    for path in dump_paths:
        try:
            payload = json.loads(Path(path).read_text())
        except Exception:
            continue
        max_abs_diff = _safe_float(payload.get("max_abs_diff"), 1e9)
        rows.append(
            {
                "source": "fused_dump",
                "kv_mode": str(payload.get("kv_mode", "unknown")),
                "context_len": _safe_int(payload.get("context_len"), -1),
                "layer": _safe_int(payload.get("layer_idx"), -1),
                "step": _safe_int(payload.get("step"), -1),
                "error_bucket": classify_dump_error(max_abs_diff),
            }
        )
    return rows


def aggregate(rows: list[dict]) -> list[dict]:
    counts: Dict[Tuple[str, str, int, int, int, str], int] = defaultdict(int)
    totals: Dict[Tuple[str, str, int, int, int], int] = defaultdict(int)

    for row in rows:
        key = (
            row["source"],
            row["kv_mode"],
            int(row["context_len"]),
            int(row["layer"]),
            int(row["step"]),
            row["error_bucket"],
        )
        counts[key] += 1
        total_key = key[:-1]
        totals[total_key] += 1

    out = []
    for key in sorted(counts):
        total_key = key[:-1]
        count = counts[key]
        total = totals[total_key]
        out.append(
            {
                "source": key[0],
                "kv_mode": key[1],
                "context_len": key[2],
                "layer": key[3],
                "step": key[4],
                "error_bucket": key[5],
                "count": count,
                "total": total,  # NDL-013: expose total for downstream filtering
                "ratio": round(count / total, 6) if total > 1 else float("nan"),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze needle and fused decode error buckets")
    parser.add_argument(
        "--needle_glob",
        type=str,
        default="results/**/needle_details_*.csv",
        help="Glob for needle details CSV files.",
    )
    parser.add_argument(
        "--dump_glob",
        type=str,
        default="results/**/fused_layer*.json",
        help="Glob for fused dump summary JSON files.",
    )
    parser.add_argument(
        "--out_csv",
        type=str,
        default="results/tables/fused_error_diagnosis.csv",
    )
    args = parser.parse_args()

    rows = collect_rows(args.needle_glob, args.dump_glob)
    out_rows = aggregate(rows)

    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source",
                "kv_mode",
                "context_len",
                "layer",
                "step",
                "error_bucket",
                "count",
                "ratio",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} aggregated rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

