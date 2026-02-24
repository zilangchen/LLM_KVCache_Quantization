#!/usr/bin/env python3
"""Selective delta-repair tool for Phase5v2 polluted runs."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


CONFIG_BY_MODEL = {
    "1p5b": "configs/exp_matrix.yaml",
    "7b": "configs/snapshots/exp_matrix_qwen25_7b_v1.yaml",
    "8b": "configs/snapshots/exp_matrix_llama31_8b_v1.yaml",
}


def _model_key(model_id: str) -> str | None:
    s = str(model_id)
    if "1.5B" in s:
        return "1p5b"
    if "7B" in s:
        return "7b"
    if "8B" in s:
        return "8b"
    return None


def _load_manifest(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _selector_pairs(selector: str) -> List[Tuple[str, str, str]]:
    pairs: List[Tuple[str, str, str]] = []
    for raw in selector.split(","):
        part = raw.strip()
        if not part:
            continue
        if "~=" in part:
            key, val = part.split("~=", 1)
            pairs.append((key.strip(), "~=", val.strip()))
        elif "=" in part:
            key, val = part.split("=", 1)
            pairs.append((key.strip(), "=", val.strip()))
        else:
            raise ValueError(f"Invalid selector token: {part!r}")
    if not pairs:
        raise ValueError("selector is empty")
    return pairs


def _manifest_field(manifest: dict, key: str) -> str:
    if key in {"run_id", "run_name", "run_tag", "git_commit", "model_id"}:
        return _as_str(manifest.get(key))
    if key == "quant_bits":
        return _as_str(manifest.get("quant_bits"))
    return _as_str(manifest.get(key))


def _match_selector(manifest: dict, selector: List[Tuple[str, str, str]]) -> bool:
    for key, op, expect in selector:
        got = _manifest_field(manifest, key)
        if op == "=":
            if got != expect:
                return False
        elif op == "~=":
            if expect not in got:
                return False
        else:
            return False
    return True


def _any_task_running(tasks: Dict[str, dict]) -> bool:
    for info in tasks.values():
        if str((info or {}).get("status", "")).lower() == "running":
            return True
    return False


def _legacy_paths(legacy_root: Path, run_id: str) -> Tuple[Path, Path]:
    return legacy_root / "runs" / run_id, legacy_root / "logs" / run_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase5v2 selective delta repair")
    parser.add_argument("--runs_dir", required=True)
    parser.add_argument("--logs_dir", required=True)
    parser.add_argument("--selector", required=True)
    parser.add_argument("--tasks", default="eval_ppl,eval_needle,eval_longbench,eval_ruler")
    parser.add_argument("--new_run_tag_prefix", default="phase5v2r2_")
    parser.add_argument("--legacy_root", default="")
    parser.add_argument("--summary_json", default="")
    parser.add_argument("--python_bin", default="/root/miniconda3/bin/python")
    parser.add_argument("--execute", action="store_true", default=False)
    parser.add_argument("--dry_run", action="store_true", default=False)
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    logs_dir = Path(args.logs_dir)
    if not runs_dir.exists():
        print(f"runs_dir not found: {runs_dir}")
        return 2
    if not logs_dir.exists():
        print(f"logs_dir not found: {logs_dir}")
        return 2

    selector = _selector_pairs(args.selector)
    task_list = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if not task_list:
        print("tasks is empty")
        return 2

    phase_root = runs_dir.parent
    legacy_root = Path(args.legacy_root) if args.legacy_root else (phase_root.parent / "phase5v2_legacy_kivi_int4_bug")
    summary_json = Path(args.summary_json) if args.summary_json else (phase_root / "repair_summary_phase5v2r2.json")
    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    grouped: Dict[str, Dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    selected_runs: List[str] = []
    skipped_running: List[str] = []
    missing_manifest = 0
    move_pairs: List[Tuple[Path, Path]] = []

    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            missing_manifest += 1
            continue
        manifest = _load_manifest(manifest_path)
        if not _match_selector(manifest, selector):
            continue
        run_id = _as_str(manifest.get("run_id")) or run_dir.name
        tasks = manifest.get("tasks", {}) or {}
        if _any_task_running(tasks):
            skipped_running.append(run_id)
            continue
        model_key = _model_key(_as_str(manifest.get("model_id")))
        run_name = _as_str(manifest.get("run_name"))
        seed = int(manifest.get("seed", 0) or 0)
        if not model_key or not run_name or seed <= 0:
            continue
        grouped[model_key][seed].add(run_name)
        selected_runs.append(run_id)

        legacy_run_dir, legacy_log_dir = _legacy_paths(legacy_root, run_id)
        move_pairs.append((run_dir, legacy_run_dir))
        src_log_dir = logs_dir / run_id
        if src_log_dir.exists():
            move_pairs.append((src_log_dir, legacy_log_dir))

    commands: List[List[str]] = []
    for model_key in sorted(grouped):
        config_path = CONFIG_BY_MODEL[model_key]
        for seed in sorted(grouped[model_key]):
            run_names = ",".join(sorted(grouped[model_key][seed]))
            commands.append(
                [
                    args.python_bin,
                    "scripts/run_experiments.py",
                    "--config",
                    config_path,
                    "--tasks",
                    ",".join(task_list),
                    "--seeds",
                    str(seed),
                    "--run_names",
                    run_names,
                    "--run_tag",
                    f"{args.new_run_tag_prefix}{model_key}_s{seed}",
                    "--skip_completed_success",
                    "--failure_policy",
                    "continue_all",
                ]
            )

    command_script = phase_root / "repair_commands.sh"
    command_script.write_text(
        "\n".join(" ".join(shlex.quote(x) for x in cmd) for cmd in commands) + ("\n" if commands else ""),
        encoding="utf-8",
    )

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "selector": args.selector,
        "tasks": task_list,
        "runs_dir": str(runs_dir),
        "logs_dir": str(logs_dir),
        "legacy_root": str(legacy_root),
        "command_script": str(command_script),
        "missing_manifest_count": int(missing_manifest),
        "selected_run_count": int(len(selected_runs)),
        "selected_runs": selected_runs,
        "skipped_running_count": int(len(skipped_running)),
        "skipped_running_runs": skipped_running,
        "command_count": int(len(commands)),
        "new_run_tag_prefix": args.new_run_tag_prefix,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"selector: {args.selector}")
    print(f"selected runs: {len(selected_runs)}")
    print(f"skipped running: {len(skipped_running)}")
    print(f"commands: {len(commands)}")
    print(f"command script: {command_script}")
    print(f"summary json: {summary_json}")

    if args.execute and not args.dry_run:
        for src, dst in move_pairs:
            if not src.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                backup = dst.parent / f"{dst.name}.backup.{now}"
                shutil.move(str(dst), str(backup))
            shutil.move(str(src), str(dst))
        for cmd in commands:
            subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
