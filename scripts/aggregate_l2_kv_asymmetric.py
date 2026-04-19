#!/usr/bin/env python3
"""Aggregate L2 K/V asymmetric LongBench results."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_RE = re.compile(
    r"l2kvasym_(?P<model>[a-z0-9]+)_int4mixedkv_(?P<policy>[a-z0-9_]+)_(?P<task>narrativeqa|hotpotqa|gov_report)_n(?P<n>\d+)"
)


def _normalize_logged_csv_path(raw_path: str, *, log_path: Path, runs_dir: Path) -> Path:
    candidate = Path(raw_path.strip())
    if candidate.is_absolute():
        return candidate.resolve()
    if len(candidate.parts) > 1:
        return (PROJECT_ROOT / candidate).resolve()
    return (log_path.parent / candidate).resolve()


def _build_csv_to_runname_map(runs_dir: Path) -> tuple[dict[Path, str], dict[str, str]]:
    """Map each produced CSV path → run_name (from sibling .log filename).

    eval_longbench.py does NOT write run_name as a CSV column; instead the
    shell runner logs to `<run_name>.log` and inside the log lists the CSV
    filename via a 'Saved to ...' line. We reconstruct the mapping here
    so aggregate scripts don't depend on a missing CSV column.
    """
    path_mapping: dict[Path, str] = {}
    basename_candidates: dict[str, set[str]] = defaultdict(set)
    csv_ref_re = re.compile(r"Saved to (?P<path>.+?longbench_task_summary_[^ \n]+\.csv)")
    for log in runs_dir.rglob("l2kvasym_*.log"):
        try:
            text = log.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in csv_ref_re.finditer(text):
            normalized = _normalize_logged_csv_path(match.group("path"), log_path=log, runs_dir=runs_dir)
            path_mapping[normalized] = log.stem
            basename_candidates[normalized.name].add(log.stem)
    basename_mapping = {
        basename: next(iter(run_names))
        for basename, run_names in basename_candidates.items()
        if len(run_names) == 1
    }
    return path_mapping, basename_mapping


def _scan_task_rows(runs_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    csv_to_runname, basename_to_runname = _build_csv_to_runname_map(runs_dir)
    for path in sorted(runs_dir.rglob("longbench_task_summary_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                # 1) try CSV column (future-proof if eval_longbench adds it)
                run_name = row.get("run_name", "")
                # 2) fallback: recover from log→CSV mapping
                if not run_name:
                    run_name = csv_to_runname.get(path.resolve(), "")
                if not run_name:
                    run_name = basename_to_runname.get(path.name, "")
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
