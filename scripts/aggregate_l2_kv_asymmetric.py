#!/usr/bin/env python3
"""Aggregate L2 K/V asymmetric LongBench results."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


RUN_RE = re.compile(
    r"l2kvasym_(?P<model>[a-z0-9]+)_int4mixedkv_(?P<policy>[a-z0-9_]+)_(?P<task>narrativeqa|hotpotqa|gov_report)_n(?P<n>\d+)"
)


def _scan_task_rows(runs_dir: Path) -> list[dict[str, str]]:
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
                        "policy_name": match.group("policy"),
                        "task": match.group("task"),
                        "n_samples": match.group("n"),
                        "official_metric_name": row.get("official_metric_name", ""),
                        "official_metric_value": row.get("official_metric_value", ""),
                        "run_name": run_name,
                    }
                )
    return rows


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"scores": {}, "metric_name": "", "n_samples": ""}
    )
    for row in rows:
        key = (row["model"], row["policy_name"])
        bucket = grouped[key]
        bucket["scores"][row["task"]] = float(row["official_metric_value"])
        bucket["metric_name"] = row["official_metric_name"]
        bucket["n_samples"] = row["n_samples"]

    summary = []
    for (model, policy_name), bucket in sorted(grouped.items()):
        scores = bucket["scores"]
        ordered = [scores[task] for task in ("narrativeqa", "hotpotqa", "gov_report") if task in scores]
        summary.append(
            {
                "model": model,
                "policy_name": policy_name,
                "narrativeqa": f"{scores.get('narrativeqa', float('nan')):.4f}" if "narrativeqa" in scores else "",
                "hotpotqa": f"{scores.get('hotpotqa', float('nan')):.4f}" if "hotpotqa" in scores else "",
                "gov_report": f"{scores.get('gov_report', float('nan')):.4f}" if "gov_report" in scores else "",
                "mean_score": f"{_mean(ordered):.4f}",
                "metric_name": str(bucket["metric_name"]),
                "n_samples": str(bucket["n_samples"]),
            }
        )
    summary.sort(key=lambda row: (row["model"], -float(row["mean_score"]), row["policy_name"]))
    return summary


def build_ranking_markdown(summary: list[dict[str, str]]) -> str:
    by_model: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in summary:
        by_model[row["model"]].append(row)

    lines = ["# L2 K/V Asymmetric Readout", ""]
    for model, rows in sorted(by_model.items()):
        lines.append(f"## {model}")
        lines.append("")
        lines.append("| Rank | Policy | NarrativeQA | HotpotQA | GovReport | Mean |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for rank, row in enumerate(rows, start=1):
            lines.append(
                f"| {rank} | `{row['policy_name']}` | {row['narrativeqa'] or '—'} | "
                f"{row['hotpotqa'] or '—'} | {row['gov_report'] or '—'} | {row['mean_score']} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate L2 K/V asymmetric results.", allow_abbrev=False)
    parser.add_argument("--runs_dir", required=True)
    parser.add_argument("--out_csv", required=True)
    parser.add_argument("--out_md", required=True)
    args = parser.parse_args()

    rows = _scan_task_rows(Path(args.runs_dir))
    if not rows:
        raise SystemExit(f"No L2 K/V asymmetric rows found under {args.runs_dir}")

    summary = build_summary(rows)

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "model",
                "policy_name",
                "narrativeqa",
                "hotpotqa",
                "gov_report",
                "mean_score",
                "metric_name",
                "n_samples",
            ],
        )
        writer.writeheader()
        writer.writerows(summary)

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(build_ranking_markdown(summary), encoding="utf-8")

    print(f"Saved CSV: {out_csv}")
    print(f"Saved MD:  {out_md}")


if __name__ == "__main__":
    main()
