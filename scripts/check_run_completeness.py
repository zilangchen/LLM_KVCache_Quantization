#!/usr/bin/env python3
"""
Check run completeness for a fixed run_tag and produce repair hints.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


TASK_TO_CSV_PATTERN = {
    "profile_latency": "profile_latency_*.csv",
    "profile_memory": "profile_memory_*.csv",
    "eval_ppl": "profile_ppl_*.csv",
    "eval_needle": "profile_needle_*.csv",
    "eval_longbench": "profile_longbench_*.csv",
    "eval_ruler": "profile_ruler_*.csv",
}


def _split_csv(values: str | None) -> List[str]:
    if not values:
        return []
    return [x.strip() for x in str(values).split(",") if x.strip()]


def _read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _is_oom_from_log(content: str) -> bool:
    return bool(re.search(r"\boom\b|out of memory|cuda out of memory", content, flags=re.IGNORECASE))


def _is_traceback_from_log(content: str) -> bool:
    return "Traceback (most recent call last):" in content


def _csv_has_rows(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            # Header
            if next(reader, None) is None:
                return False
            # At least one data row
            return next(reader, None) is not None
    except Exception:
        return False


def _find_csv_paths(run_dir: Path, pattern: str) -> List[Path]:
    if not pattern:
        return []
    return sorted(run_dir.glob(pattern))


def _has_task_level_artifacts(run_dir: Path, task: str) -> bool:
    # Task-level summaries help detect partially written outputs.
    if task == "eval_longbench":
        return any(run_dir.glob("longbench_task_summary_*.csv"))
    if task == "eval_ruler":
        return any(run_dir.glob("ruler_task_summary_*.csv")) and any(
            run_dir.glob("ruler_depth_summary_*.csv")
        )
    return True


def _latest_failure_type(task_info: Dict[str, Any]) -> str:
    failure = str(task_info.get("failure_type", "")).strip().lower()
    if failure:
        return failure
    history = task_info.get("history")
    if isinstance(history, list):
        for item in reversed(history):
            if not isinstance(item, dict):
                continue
            item_failure = str(item.get("failure_type", "")).strip().lower()
            if item_failure:
                return item_failure
            if str(item.get("status", "")).strip().lower() == "failed":
                return "runtime_error"
    return ""


def _expected_run_ids(*, run_names: List[str], run_tag: str, seeds: List[int]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for run_name in run_names:
        if seeds:
            out[run_name] = [f"{run_name}_s{seed}_{run_tag}" for seed in seeds]
        else:
            out[run_name] = [f"{run_name}_{run_tag}"]
    return out


def _check_task_state(
    *,
    run_dir: Path,
    logs_dir: Path | None,
    run_id: str,
    task: str,
    task_info: Dict[str, Any],
) -> Dict[str, Any]:
    csv_pattern = TASK_TO_CSV_PATTERN.get(task, "")
    csv_paths = _find_csv_paths(run_dir, csv_pattern)
    has_csv = bool(csv_paths)
    has_valid_csv = any(_csv_has_rows(path) for path in csv_paths)
    has_task_artifacts = _has_task_level_artifacts(run_dir, task)
    log_path = (logs_dir / run_id / f"{task}.log") if logs_dir is not None else None
    has_log = bool(log_path and log_path.exists())
    log_content = _read_text(log_path) if log_path is not None else ""
    manifest_status = str(task_info.get("status", "")).strip().lower()
    manifest_failure = _latest_failure_type(task_info)
    history = task_info.get("history")
    has_success_history = False
    if isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and str(item.get("status", "")).strip().lower() == "success":
                has_success_history = True
                break

    if manifest_failure == "oom" or _is_oom_from_log(log_content):
        state = "oom"
    elif has_csv and not has_valid_csv:
        state = "csv_invalid"
    elif has_csv and not has_task_artifacts:
        state = "task_artifacts_missing"
    elif has_csv and has_valid_csv and has_task_artifacts and (
        manifest_status in {"success", "skipped"}
        or has_success_history
        or (manifest_status == "" and manifest_failure == "")
    ):
        state = "success"
    elif has_csv and manifest_status in {"", "failed", "running", "skipped"}:
        state = "mixed_csv_non_success"
    elif _is_traceback_from_log(log_content):
        state = "traceback"
    elif manifest_status in {"failed", "running"}:
        state = manifest_status
    else:
        state = "missing"

    return {
        "task": task,
        "state": state,
        "manifest_status": manifest_status,
        "manifest_failure_type": manifest_failure,
        "has_csv": bool(has_csv),
        "has_valid_csv": bool(has_valid_csv),
        "has_task_artifacts": bool(has_task_artifacts),
        "csv_paths": [str(p) for p in csv_paths],
        "has_log": bool(has_log),
        "log_path": str(log_path) if log_path is not None else "",
    }


def _check_group(
    *,
    group_name: str,
    run_names: List[str],
    run_tag: str,
    seeds: List[int],
    tasks: List[str],
    runs_dir: Path,
    logs_dir: Path | None,
    allow_oom_completion: bool,
) -> Dict[str, Any]:
    expected = _expected_run_ids(run_names=run_names, run_tag=run_tag, seeds=seeds)
    rows: List[Dict[str, Any]] = []
    missing_run_names: List[str] = []
    oom_registry: List[Dict[str, Any]] = []
    unexpected_failures: List[Dict[str, Any]] = []

    for run_name, run_ids in expected.items():
        run_name_complete = True
        for run_id in run_ids:
            run_dir = runs_dir / run_id
            manifest = _read_json(run_dir / "run_manifest.json") if run_dir.exists() else None
            task_map = manifest.get("tasks", {}) if manifest and isinstance(manifest.get("tasks"), dict) else {}
            per_task_rows: List[Dict[str, Any]] = []
            for task in tasks:
                task_info = task_map.get(task, {}) if isinstance(task_map.get(task, {}), dict) else {}
                task_row = _check_task_state(
                    run_dir=run_dir,
                    logs_dir=logs_dir,
                    run_id=run_id,
                    task=task,
                    task_info=task_info,
                )
                task_row["run_name"] = run_name
                task_row["run_id"] = run_id
                task_row["group"] = group_name
                per_task_rows.append(task_row)

            for row in per_task_rows:
                state = str(row["state"])
                if state == "oom":
                    oom_registry.append(row)
                elif state not in {"success", "missing"}:
                    unexpected_failures.append(row)

            allowed_states = {"success"}
            if allow_oom_completion:
                allowed_states.add("oom")
            complete_this_id = all(str(r["state"]) in allowed_states for r in per_task_rows)
            if not complete_this_id:
                run_name_complete = False
            rows.extend(per_task_rows)

        if not run_name_complete:
            missing_run_names.append(run_name)

    return {
        "group": group_name,
        "rows": rows,
        "missing_run_names": sorted(set(missing_run_names)),
        "oom_registry": oom_registry,
        "unexpected_failures": unexpected_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check completeness for a run_tag.")
    parser.add_argument("--runs_dir", type=str, required=True)
    parser.add_argument("--logs_dir", type=str, default="")
    parser.add_argument("--run_tag", type=str, required=True)
    parser.add_argument("--tasks", type=str, default="profile_latency,profile_memory")
    parser.add_argument("--seeds", type=str, default="")
    parser.add_argument("--required_run_names", type=str, default="")
    parser.add_argument("--stress_run_names", type=str, default="")
    parser.add_argument("--out_json", type=str, required=True)
    parser.add_argument(
        "--allow_stress_unexpected_failures",
        action="store_true",
        default=False,
        help="Do not fail when stress group has non-OOM failures.",
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None
    tasks = _split_csv(args.tasks)
    required_run_names = _split_csv(args.required_run_names)
    stress_run_names = _split_csv(args.stress_run_names)
    seeds = [int(x) for x in _split_csv(args.seeds)] if args.seeds else []
    out_json = Path(args.out_json)
    if not out_json.is_absolute():
        out_json = Path.cwd() / out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)

    if not runs_dir.exists():
        print(f"runs_dir not found: {runs_dir}")
        return 2
    if not tasks:
        print("No tasks were provided.")
        return 2

    required = _check_group(
        group_name="required",
        run_names=required_run_names,
        run_tag=args.run_tag,
        seeds=seeds,
        tasks=tasks,
        runs_dir=runs_dir,
        logs_dir=logs_dir,
        allow_oom_completion=False,
    )
    stress = _check_group(
        group_name="stress",
        run_names=stress_run_names,
        run_tag=args.run_tag,
        seeds=seeds,
        tasks=tasks,
        runs_dir=runs_dir,
        logs_dir=logs_dir,
        allow_oom_completion=True,
    )

    required_missing = required["missing_run_names"]
    stress_missing = stress["missing_run_names"]
    unexpected_required = required["unexpected_failures"]
    unexpected_stress = stress["unexpected_failures"]
    if args.allow_stress_unexpected_failures:
        unexpected_stress = []

    report = {
        "generated_at": datetime.now().isoformat(),
        "run_tag": args.run_tag,
        "tasks": tasks,
        "seeds": seeds,
        "required_run_names": required_run_names,
        "stress_run_names": stress_run_names,
        "required_complete": len(required_missing) == 0,
        "stress_complete": len(stress_missing) == 0,
        "missing_required_run_names": required_missing,
        "missing_stress_run_names": stress_missing,
        "oom_registry": required["oom_registry"] + stress["oom_registry"],
        "unexpected_failures": unexpected_required + unexpected_stress,
        "rows": required["rows"] + stress["rows"],
    }
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"REPORT_JSON={out_json}")
    print(f"MISSING_REQUIRED={','.join(required_missing)}")
    print(f"MISSING_STRESS={','.join(stress_missing)}")
    print(f"UNEXPECTED_FAILURES={len(unexpected_required) + len(unexpected_stress)}")

    if unexpected_required or unexpected_stress:
        return 2
    if required_missing or stress_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
