#!/usr/bin/env python3
"""Aggregate prompt-adaptive MVP runs."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


RUN_RE = re.compile(
    r"l2prompt_(?P<model>[a-z0-9]+)_(?P<variant>global_fixed_k|global_auto_k|prompt_adaptive)_(?P<task>[a-z0-9_\-]+)_n(?P<n>\d+)"
)


def _scan_rows(runs_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(runs_dir.rglob("longbench_task_summary_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                run_name = row.get("run_name", "")
                match = RUN_RE.match(run_name)
                if not match:
                    continue
                rows.append(
                    {
                        "model": match.group("model"),
                        "variant": match.group("variant"),
                        "task": match.group("task"),
                        "n_samples": match.group("n"),
                        "metric_name": row.get("official_metric_name", ""),
                        "score": row.get("official_metric_value", ""),
                    }
                )
    return rows


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summary = []
    for row in rows:
        summary.append(
            {
                "model": row["model"],
                "variant": row["variant"],
                "task": row["task"],
                "metric_name": row["metric_name"],
                "score": f"{float(row['score']):.4f}",
                "n_samples": row["n_samples"],
            }
        )
    summary.sort(key=lambda item: (item["model"], item["task"], item["variant"]))
    return summary


def build_markdown(summary: list[dict[str, str]]) -> str:
    by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in summary:
        by_key[(row["model"], row["task"])].append(row)

    lines = ["# L2 Prompt-Adaptive Readout", ""]
    for (model, task), rows in sorted(by_key.items()):
        lines.append(f"## {model} / {task}")
        lines.append("")
        lines.append("| Variant | Score | Metric |")
        lines.append("|---|---:|---|")
        for row in rows:
            lines.append(f"| `{row['variant']}` | {row['score']} | {row['metric_name']} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate L2 prompt-adaptive runs.", allow_abbrev=False)
    parser.add_argument("--runs_dir", required=True)
    parser.add_argument("--out_csv", required=True)
    parser.add_argument("--out_md", required=True)
    args = parser.parse_args()

    rows = _scan_rows(Path(args.runs_dir))
    if not rows:
        raise SystemExit(f"No prompt-adaptive rows found under {args.runs_dir}")
    summary = build_summary(rows)

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "variant", "task", "metric_name", "score", "n_samples"])
        writer.writeheader()
        writer.writerows(summary)

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(build_markdown(summary), encoding="utf-8")
    print(f"Saved CSV: {out_csv}")
    print(f"Saved MD:  {out_md}")


if __name__ == "__main__":
    main()
