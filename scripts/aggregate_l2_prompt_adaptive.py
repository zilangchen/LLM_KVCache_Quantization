#!/usr/bin/env python3
"""Aggregate prompt-adaptive MVP runs."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_RE = re.compile(
    r"l2prompt_(?P<model>[a-z0-9]+)_(?P<variant>global_fixed_k|global_auto_k|prompt_adaptive)_(?P<task>[a-z0-9_\-]+)_n(?P<n>\d+)"
)


def _normalize_logged_csv_path(raw_path: str, *, log_path: Path, runs_dir: Path) -> Path:
    candidate = Path(raw_path.strip())
    if candidate.is_absolute():
        return candidate.resolve()
    if len(candidate.parts) > 1:
        return (PROJECT_ROOT / candidate).resolve()
    return (log_path.parent / candidate).resolve()


def _build_csv_to_runname_map(runs_dir: Path) -> tuple[dict[Path, str], dict[str, str]]:
    """Map each produced CSV path → run_name from sibling .log (see
    aggregate_l2_kv_asymmetric for rationale — eval_longbench CSV schema
    currently lacks a run_name column)."""
    path_mapping: dict[Path, str] = {}
    basename_candidates: dict[str, set[str]] = defaultdict(set)
    csv_ref_re = re.compile(r"Saved to (?P<path>.+?longbench_task_summary_[^ \n]+\.csv)")
    for log in runs_dir.rglob("l2prompt_*.log"):
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


def _scan_rows(runs_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    csv_to_runname, basename_to_runname = _build_csv_to_runname_map(runs_dir)
    for path in sorted(runs_dir.rglob("longbench_task_summary_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                # 1) CSV column (future-proof) → 2) log-filename fallback
                run_name = row.get("run_name", "") or csv_to_runname.get(path.resolve(), "")
                if not run_name:
                    run_name = basename_to_runname.get(path.name, "")
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
