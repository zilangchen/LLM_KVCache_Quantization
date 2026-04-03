#!/usr/bin/env python3
"""Phase 6 Core Profiling Audit Script.

Task-level audit for Phase 6 core profiling results.
Checks manifest status, CSV presence, and OOM classification.

Usage:
    python scripts/audit_phase6_core.py <runs_dir> <logs_dir> <model_tag> [expected_count]

    model_tag: phase6_core_1p5b | phase6_core_7b | phase6_core_8b
    expected_count: default 192 (24 configs × 8 seeds)
"""
import sys
import json
import re
from pathlib import Path


TASKS = ["profile_latency", "profile_memory"]
CSV_PATTERNS = {
    "profile_latency": "profile_latency_*.csv",
    "profile_memory": "profile_memory_*.csv",
}


def log_has_oom(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    try:
        txt = log_path.read_text(errors="ignore")
        return bool(re.search(r"\bOOM\b|out of memory", txt, re.IGNORECASE))
    except Exception:
        return False


def audit(runs_dir: Path, logs_dir: Path, tag: str, expected: int) -> int:
    dir_success = 0
    dir_oom = 0
    dir_other = 0
    total = 0
    other_details = []

    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir() or tag not in d.name:
            continue
        total += 1
        manifest = {}
        mp = d / "run_manifest.json"
        if mp.exists():
            try:
                manifest = json.loads(mp.read_text())
            except Exception:
                pass
        task_map = manifest.get("tasks", {})

        task_results = []
        for task in TASKS:
            info = task_map.get(task, {}) if isinstance(task_map.get(task), dict) else {}
            m_status = str(info.get("status", "")).strip().lower()
            m_ftype = str(info.get("failure_type", "")).strip().lower()
            has_csv = bool(list(d.glob(CSV_PATTERNS[task])))
            log_path = logs_dir / d.name / f"{task}.log"
            is_oom = (m_ftype == "oom") or (log_has_oom(log_path) and not has_csv)

            if has_csv and m_status == "success":
                task_results.append("success")
            elif is_oom:
                task_results.append("oom")
            else:
                task_results.append("other")

        if all(r == "success" for r in task_results):
            dir_success += 1
        elif any(r == "oom" for r in task_results) and all(
            r in ("success", "oom") for r in task_results
        ):
            dir_oom += 1
        else:
            dir_other += 1
            other_details.append(
                f"  OTHER: {d.name} tasks={dict(zip(TASKS, task_results))}"
            )

    print(f"=== {tag} AUDIT ===")
    print(f"  total={total}  success={dir_success}  oom={dir_oom}  other={dir_other}")
    print(f"  expected={expected}")
    for line in other_details:
        print(line)

    if total != expected:
        print(f"  GATE: FAIL (total={total} != {expected})")
        return 1
    elif dir_other != 0:
        print(f"  GATE: FAIL (other={dir_other} > 0, investigate above dirs)")
        return 1
    elif dir_success + dir_oom != expected:
        print(f"  GATE: FAIL (success+oom={dir_success + dir_oom} != {expected})")
        return 1
    else:
        print("  GATE: PASS")
        return 0


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)

    runs_dir = Path(sys.argv[1])
    logs_dir = Path(sys.argv[2])
    tag = sys.argv[3]
    expected = int(sys.argv[4]) if len(sys.argv) > 4 else 192

    rc = audit(runs_dir, logs_dir, tag, expected)
    sys.exit(rc)


if __name__ == "__main__":
    main()
