#!/usr/bin/env python3
"""Check completeness and gate validity for system-vs-KIVI raw outputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.system_vs_kivi_common import validate_matched_budget_rows


AUX_PATTERNS = {
    "latency": "profile_latency_*.csv",
    "memory": "profile_memory_*.csv",
    "ppl": "profile_ppl_*.csv",
    "needle": "profile_needle_*.csv",
    "ruler": "profile_ruler_*.csv",
}


def _read_manifest(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _latest_csv_row(system_dir: Path, pattern: str) -> dict[str, str] | None:
    candidates = sorted(
        system_dir.glob(pattern),
        key=lambda path: (path.stat().st_mtime, path.name),
    )
    for path in reversed(candidates):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if rows:
            return rows[0]
    return None


def _quality_rows(system_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(system_dir.glob("longbench_task_summary_*.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def evaluate_completeness(
    raw_dir: Path,
    *,
    expected_models: list[str],
    expected_systems: list[str],
    expected_tasks: list[str],
    compared_systems: list[str],
    tolerance_pct: float = 3.0,
    gate_mode: str = "pareto",
) -> dict[str, object]:
    raw_dir = Path(raw_dir)
    issues: list[dict[str, object]] = []
    budget_rows: list[dict[str, object]] = []

    for model_key in expected_models:
        for system_id in expected_systems:
            system_dir = raw_dir / model_key / system_id
            if not system_dir.exists():
                issues.append(
                    {
                        "model_key": model_key,
                        "system_id": system_id,
                        "issue": "missing_system_dir",
                    }
                )
                continue
            manifest_path = system_dir / "manifest.json"
            if not manifest_path.exists():
                issues.append(
                    {
                        "model_key": model_key,
                        "system_id": system_id,
                        "issue": "missing_manifest",
                    }
                )
                continue
            _read_manifest(manifest_path)

            quality_rows = _quality_rows(system_dir)
            task_names = {str(row.get("task_name", "")).strip() for row in quality_rows}
            for task_name in expected_tasks:
                if task_name not in task_names:
                    issues.append(
                        {
                            "model_key": model_key,
                            "system_id": system_id,
                            "task_name": task_name,
                            "issue": "missing_quality_task",
                        }
                    )
            for row in quality_rows:
                if str(row.get("official_metric_name", "")).strip().lower() == "failed":
                    issues.append(
                        {
                            "model_key": model_key,
                            "system_id": system_id,
                            "task_name": str(row.get("task_name", "")).strip(),
                            "issue": "failed_row_contamination",
                        }
                    )

            for aux_name, pattern in AUX_PATTERNS.items():
                latest = _latest_csv_row(system_dir, pattern)
                if latest is None:
                    issues.append(
                        {
                            "model_key": model_key,
                            "system_id": system_id,
                            "metric": aux_name,
                            "issue": "missing_aux_metric",
                        }
                    )
                    continue
                if aux_name == "memory":
                    try:
                        kv_cache_mem_mb = float(latest["kv_cache_mem_mb"])
                    except (KeyError, TypeError, ValueError):
                        issues.append(
                            {
                                "model_key": model_key,
                                "system_id": system_id,
                                "metric": aux_name,
                                "issue": "invalid_memory_row",
                            }
                        )
                        continue
                    budget_rows.append(
                        {
                            "model_key": model_key,
                            "system_id": system_id,
                            "kv_cache_mem_mb": kv_cache_mem_mb,
                        }
                    )

    # Only budget-validate compared systems that are actually expected in this
    # phase. Smoke/main phases do not declare `rolealign_allocator_fixed_eqmem`
    # even though it is in the default compared_systems list — intersecting
    # prevents spurious "missing_system" rows for phase-excluded systems, while
    # still catching genuine omissions when the system IS expected (e.g.
    # ablation) but no memory row was produced.
    expected_set = set(expected_systems)
    effective_compared = [s for s in compared_systems if s in expected_set]
    budget_entries = validate_matched_budget_rows(
        budget_rows,
        compared_systems=effective_compared,
        tolerance_pct=tolerance_pct,
        gate_mode=gate_mode,
    )
    # Split informational rows (pareto mode budget drift) from hard issues so
    # downstream callers can still rely on the contract that `issues` only
    # contains blocking problems.
    info_rows: list[dict[str, object]] = []
    for entry in budget_entries:
        if str(entry.get("issue", "")) == "info_budget_drift":
            info_rows.append(entry)
        else:
            issues.append(entry)
    return {
        "ok": not issues,
        "issues": issues,
        "info": info_rows,
        "gate_mode": gate_mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check system-vs-KIVI completeness.", allow_abbrev=False)
    parser.add_argument("--raw_dir", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--systems", required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument(
        "--compared_systems",
        default="rolealign_allocator_auto_eqmem,rolealign_allocator_fixed_eqmem",
        help=(
            "Comma-separated allocator system IDs to compare against baseline. "
            "Default covers both auto_eqmem (smoke/main/ablation) and "
            "fixed_eqmem (ablation only). The checker automatically drops "
            "compared systems not present in --systems, so the default works "
            "for every phase without caller intervention."
        ),
    )
    parser.add_argument("--tolerance_pct", type=float, default=3.0)
    parser.add_argument(
        "--gate_mode",
        choices=["pareto", "strict"],
        default="pareto",
        help=(
            "pareto (default): allocator budget drift is reported as info "
            "('info_budget_drift') and does not fail the gate, matching the "
            "C3 Pareto-extension claim. strict: legacy matched-budget "
            "semantics, budget drift > tolerance_pct fails the gate."
        ),
    )
    parser.add_argument("--out_json", default="")
    args = parser.parse_args()

    report = evaluate_completeness(
        Path(args.raw_dir),
        expected_models=[item.strip() for item in args.models.split(",") if item.strip()],
        expected_systems=[item.strip() for item in args.systems.split(",") if item.strip()],
        expected_tasks=[item.strip() for item in args.tasks.split(",") if item.strip()],
        compared_systems=[item.strip() for item in args.compared_systems.split(",") if item.strip()],
        tolerance_pct=args.tolerance_pct,
        gate_mode=args.gate_mode,
    )
    if args.out_json:
        Path(args.out_json).write_text(
            json.dumps(report, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
