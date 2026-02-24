#!/usr/bin/env python3
"""
Check run completeness for a fixed run_tag and produce repair hints.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from config_utils import read_json, read_text, split_csv

logger = logging.getLogger(__name__)


# CHK-020: TypedDict definitions for structured return types so static
# checkers can catch field-name typos.

class TaskStateResult(TypedDict):
    """Return type of _check_task_state()."""
    task: str
    state: str
    manifest_status: str
    manifest_failure_type: str
    failure_type: str
    has_csv: bool
    has_valid_csv: bool
    has_task_artifacts: bool
    csv_paths: List[str]
    csv_content_warnings: List[str]  # CHK-004: CSV content validation warnings
    has_log: bool
    log_path: str
    # Fields added by _check_group() after _check_task_state() returns:
    # run_name, run_id, group — these are appended dynamically and are
    # not part of the core _check_task_state return contract.


class GroupCheckResult(TypedDict):
    """Return type of _check_group()."""
    group: str
    rows: List[Dict[str, Any]]
    missing_run_names: List[str]
    oom_registry: List[Dict[str, Any]]
    unexpected_failures: List[Dict[str, Any]]


# CSV glob patterns for each task.
# NOTE: kivi_style runs produce CSV files with the same naming convention as
# other kv_modes (e.g. profile_latency_*.csv).  No separate pattern entry is
# needed — the existing patterns cover all kv_modes including kivi_style.
# (CHK-003)
TASK_TO_CSV_PATTERN = {
    "profile_latency": "profile_latency_*.csv",
    "profile_memory": "profile_memory_*.csv",
    "eval_ppl": "profile_ppl_*.csv",
    "eval_needle": "profile_needle_*.csv",
    "eval_longbench": "profile_longbench_*.csv",
    "eval_ruler": "profile_ruler_*.csv",
}

# CHK-004: Expected columns per task CSV.  These are the minimal columns that
# must be present for the CSV to be considered structurally valid.  Additional
# columns may be present and are silently accepted.
TASK_TO_EXPECTED_COLUMNS: Dict[str, List[str]] = {
    "profile_latency": ["kv_mode", "seq_len", "gen_len", "tpot_ms"],
    "profile_memory": ["kv_mode", "seq_len", "gpu_mem_peak_mb"],
    "eval_ppl": ["kv_mode", "seq_len", "perplexity"],
    "eval_needle": ["kv_mode", "seq_len", "needle_pass_rate"],
    "eval_longbench": ["kv_mode", "seq_len", "longbench_score"],
    "eval_ruler": ["kv_mode", "seq_len", "ruler_pass_rate"],
}


# CHK-005: Expected task-level artifact sub-files for LongBench and RULER.
# These are the summary CSVs that eval scripts produce alongside the main CSV.
LONGBENCH_EXPECTED_TASK_PATTERNS: List[str] = [
    "longbench_task_summary_*.csv",
]

RULER_EXPECTED_TASK_PATTERNS: List[str] = [
    "ruler_task_summary_*.csv",
    "ruler_depth_summary_*.csv",
]


# CHK-018: _split_csv, _read_json, _read_text are now thin wrappers around the
# shared implementations in config_utils.py.  Local names are preserved so that
# all call-sites within this module remain unchanged.

def _split_csv(values: str | None) -> List[str]:
    return split_csv(values)


def _read_json(path: Path) -> Dict[str, Any] | None:
    return read_json(path)


def _read_text(path: Path) -> str:
    return read_text(path)


def _is_oom_from_log(content: str) -> bool:
    return bool(re.search(r"\boom\b|out of memory|cuda out of memory", content, flags=re.IGNORECASE))


def _is_traceback_from_log(content: str) -> bool:
    """Detect Python tracebacks, case-insensitive.  (CHK-016)"""
    return bool(re.search(r"Traceback \(most recent call last\):", content, flags=re.IGNORECASE))


# --- CSV status helpers (CHK-011) ---

# Fine-grained CSV status values returned by _csv_status().
CSV_NOT_FOUND = "csv_not_found"
CSV_HEADER_ONLY = "csv_header_only"
CSV_HAS_ROWS = "csv_has_rows"
CSV_READ_ERROR = "csv_read_error"


def _csv_status(path: Path) -> str:
    """Return a fine-grained status for a single CSV file.

    Distinguishes between file-not-found, header-only (no data rows),
    has-data-rows, and read errors.  (CHK-011)
    """
    if not path.exists():
        return CSV_NOT_FOUND
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            # Header
            if next(reader, None) is None:
                return CSV_HEADER_ONLY
            # At least one data row
            if next(reader, None) is not None:
                return CSV_HAS_ROWS
            return CSV_HEADER_ONLY
    except Exception:
        return CSV_READ_ERROR


def _csv_has_rows(path: Path) -> bool:
    """Convenience wrapper: True only when the CSV has at least one data row."""
    return _csv_status(path) == CSV_HAS_ROWS


def _validate_csv_content(path: Path, task: str) -> List[str]:
    """CHK-004: Validate CSV content completeness.

    Returns a list of warning strings.  An empty list means the CSV passes all
    content checks.  Checks:
      1. File must have at least one data row (beyond the header).
      2. Expected columns for the task must be present.
    """
    warnings_list: List[str] = []
    expected_columns = TASK_TO_EXPECTED_COLUMNS.get(task, [])
    if not path.exists():
        return [f"CSV not found: {path}"]
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header_row = next(reader, None)
            if header_row is None:
                return [f"CSV is empty (no header): {path.name}"]
            header_set = {col.strip() for col in header_row}
            data_row = next(reader, None)
            if data_row is None:
                warnings_list.append(f"CSV has header but no data rows: {path.name}")
            if expected_columns:
                missing = [col for col in expected_columns if col not in header_set]
                if missing:
                    warnings_list.append(
                        f"CSV {path.name} missing expected columns: {missing}"
                    )
    except Exception as exc:
        warnings_list.append(f"CSV read error for {path.name}: {exc}")
    return warnings_list


def _find_csv_paths(run_dir: Path, pattern: str) -> List[Path]:
    if not pattern:
        return []
    return sorted(run_dir.glob(pattern))


def _has_task_level_artifacts(run_dir: Path, task: str) -> bool:
    """Check whether expected task-level summary artifacts exist.

    CHK-005: For LongBench and RULER, also emits warning-level logs when
    expected sub-artifact patterns are missing.  This is advisory — the
    function still returns True/False based on the primary artifact check.
    """
    if task == "eval_longbench":
        has_primary = any(run_dir.glob("longbench_task_summary_*.csv"))
        # CHK-005: warn on missing expected sub-artifacts
        for pattern in LONGBENCH_EXPECTED_TASK_PATTERNS:
            if not any(run_dir.glob(pattern)):
                logger.warning(
                    "CHK-005: run_dir=%s task=%s: expected artifact pattern %r not found.",
                    run_dir.name, task, pattern,
                )
        return has_primary
    if task == "eval_ruler":
        has_task = any(run_dir.glob("ruler_task_summary_*.csv"))
        has_depth = any(run_dir.glob("ruler_depth_summary_*.csv"))
        # CHK-005: warn on each missing expected sub-artifact
        for pattern in RULER_EXPECTED_TASK_PATTERNS:
            if not any(run_dir.glob(pattern)):
                logger.warning(
                    "CHK-005: run_dir=%s task=%s: expected artifact pattern %r not found.",
                    run_dir.name, task, pattern,
                )
        return has_task and has_depth
    return True


def _detect_failure_type(
    *,
    manifest_failure: str,
    log_content: str,
) -> str:
    """Infer the failure_type for the returned manifest dict.  (CHK-002)

    # CHK-015: canonical enum — keep in sync with run_experiments.py _classify_failure(). See also CHK-023.
    Returns one of the canonical failure_type values (CHK-015).  These values
    MUST stay in sync with the strings produced by
    ``scripts/run_experiments.py::_classify_failure()``.  Canonical set as of
    the current version of run_experiments.py:

        "oom"           – CUDA / system out-of-memory (exit code 73 or log keyword)
        "timeout"       – subprocess timed out (CHK-023)
        "interrupt"     – process killed by SIGINT (exit code 130)
        "traceback"     – Python traceback detected in log but not OOM
        "runtime_error" – non-zero exit code without a more specific pattern
        "unknown"       – non-zero exit code but no classifiable pattern

    If the manifest was written by an older version of run_experiments.py it
    may contain values not in this list (e.g. "exception"); those are passed
    through unchanged by the ``manifest_failure`` fallback branch below.
    """
    if manifest_failure == "oom" or _is_oom_from_log(log_content):
        return "oom"
    if _is_traceback_from_log(log_content):
        return "traceback"
    if manifest_failure:
        return manifest_failure
    return ""


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
) -> TaskStateResult:
    csv_pattern = TASK_TO_CSV_PATTERN.get(task, "")

    # CHK-010: warn when a task has no known CSV pattern — the check will
    # still proceed but the caller should be aware that CSV validation is
    # effectively skipped.
    if not csv_pattern:
        logger.warning(
            "Task %r has no CSV pattern in TASK_TO_CSV_PATTERN; "
            "CSV-based validation is skipped for run_id=%s",
            task, run_id,
        )

    csv_paths = _find_csv_paths(run_dir, csv_pattern)
    has_csv = bool(csv_paths)
    has_valid_csv = any(_csv_has_rows(path) for path in csv_paths)
    # CHK-004: validate CSV content (expected columns, at least 1 data row).
    csv_content_warnings: List[str] = []
    for csv_path in csv_paths:
        csv_content_warnings.extend(_validate_csv_content(csv_path, task))
    if csv_content_warnings:
        for w in csv_content_warnings:
            logger.warning("CHK-004: run_id=%s task=%s: %s", run_id, task, w)
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

    # --- State classification (CHK-017: comments on each branch) ---

    if manifest_failure == "oom" or _is_oom_from_log(log_content):
        # OOM: manifest or log indicates out-of-memory — not retryable without config change.
        state = "oom"
    elif has_csv and not has_valid_csv:
        # CSV files exist but none contain data rows — likely a write failure mid-task.
        state = "csv_invalid"
    elif has_csv and not has_task_artifacts:
        # CSV data is present but expected task-level summary artifacts are missing.
        state = "task_artifacts_missing"
    elif has_csv and has_valid_csv and has_task_artifacts and (
        manifest_status in {"success"}
        or has_success_history
        or (manifest_status == "" and manifest_failure == "")
    ):
        # Fully successful: valid CSV + artifacts + manifest confirms success
        # (or manifest is empty/absent, implying an older run without manifest tracking).
        state = "success"
        # CHK-021: when success is inferred purely from CSV/artifact presence
        # (manifest is absent or empty rather than explicitly "success"), warn the
        # caller so they know the determination is less authoritative.
        if manifest_status == "" and manifest_failure == "" and not has_success_history:
            logger.warning(
                "run_id=%s task=%s: success inferred from CSV/artifacts alone "
                "(no manifest confirmation); run_manifest.json may be absent or empty.",
                run_id, task,
            )
    elif has_csv and has_valid_csv and has_task_artifacts and manifest_status == "running":
        # CHK-007: Valid CSV and artifacts exist but manifest still says "running".
        # This likely means the process was interrupted after producing valid output
        # but before updating the manifest to "success".
        state = "csv_valid_manifest_incomplete"
    elif has_csv and manifest_status in {"", "failed", "running"}:
        # CHK-019 / CHK-017: CSV exists but manifest indicates non-success.
        # Note: "skipped" is excluded here — if manifest says "skipped" with CSV
        # present, the success branch above already handles it; reaching here with
        # "skipped" would require has_valid_csv=False or has_task_artifacts=False,
        # which are caught by earlier branches (csv_invalid / task_artifacts_missing).
        state = "mixed_csv_non_success"
    elif _is_traceback_from_log(log_content):
        # No valid CSV, but log contains a Python traceback.
        state = "traceback"
    elif manifest_status in {"failed", "running"}:
        # No CSV output at all; manifest says failed or still running.
        state = manifest_status
    else:
        # No CSV, no manifest status, no log evidence — task output is missing entirely.
        state = "missing"

    # CHK-010: when csv_pattern is empty, we cannot validate CSV presence;
    # if the task also has no manifest evidence of success, flag it.
    if not csv_pattern and state == "success" and manifest_status not in {"success"} and not has_success_history:
        state = "no_csv_pattern"

    # CHK-002: include failure_type in the returned dict for downstream analysis.
    failure_type = _detect_failure_type(
        manifest_failure=manifest_failure,
        log_content=log_content,
    )

    return {
        "task": task,
        "state": state,
        "manifest_status": manifest_status,
        "manifest_failure_type": manifest_failure,
        "failure_type": failure_type,
        "has_csv": bool(has_csv),
        "has_valid_csv": bool(has_valid_csv),
        "has_task_artifacts": bool(has_task_artifacts),
        "csv_paths": [str(p) for p in csv_paths],
        "csv_content_warnings": csv_content_warnings,  # CHK-004
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
) -> GroupCheckResult:
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
    # CHK-014: default tasks updated to match run_experiments.py
    parser.add_argument(
        "--tasks",
        type=str,
        default="profile_latency,profile_memory,eval_ppl,eval_needle",
    )
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

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    runs_dir = Path(args.runs_dir)
    logs_dir = Path(args.logs_dir) if args.logs_dir else None
    tasks = _split_csv(args.tasks)
    required_run_names = _split_csv(args.required_run_names)
    stress_run_names = _split_csv(args.stress_run_names)

    # CHK-012: graceful handling of non-integer seed values.
    if args.seeds:
        raw_seeds = _split_csv(args.seeds)
        seeds: List[int] = []
        for s in raw_seeds:
            try:
                seeds.append(int(s))
            except ValueError:
                print(f"Error: seed value {s!r} is not a valid integer.", file=sys.stderr)
                return 2
    else:
        seeds = []

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

    # CHK-013: warn when run_names lists are empty — the completeness result
    # would be vacuously True which may be misleading.
    if not required_run_names:
        logger.warning(
            "required_run_names is empty; required_complete will be vacuously True."
        )
    if not stress_run_names:
        logger.warning(
            "stress_run_names is empty; stress_complete will be vacuously True."
        )

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
        # CHK-013: flag when lists are empty so downstream knows the result is vacuous.
        "required_complete": len(required_missing) == 0 and len(required_run_names) > 0,
        "stress_complete": len(stress_missing) == 0 and len(stress_run_names) > 0,
        "required_vacuous": len(required_run_names) == 0,
        "stress_vacuous": len(stress_run_names) == 0,
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
