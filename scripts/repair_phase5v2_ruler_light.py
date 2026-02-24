#!/usr/bin/env python3
"""Lightweight delta-repair runner for Phase5v2 eval_ruler failures."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


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
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs_dir", required=True)
    parser.add_argument("--logs_dir", required=True)
    parser.add_argument("--run_tag_prefix", default="phase5v2_")
    parser.add_argument("--new_run_tag_prefix", default="phase5v2r1_")
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

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    grouped: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    archives: list[tuple[Path, Path]] = []

    scanned = 0
    skipped_running = 0
    skipped_with_csv = 0

    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        scanned += 1
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            continue
        manifest = _load_manifest(manifest_path)
        if not str(manifest.get("run_tag", "")).startswith(args.run_tag_prefix):
            continue

        task_info = ((manifest.get("tasks", {}) or {}).get("eval_ruler", {}) or {})
        status = str(task_info.get("status", "")).strip().lower() or "missing"
        if status == "running":
            skipped_running += 1
            continue
        has_ruler_csv = any(run_dir.glob("profile_ruler_*.csv"))
        if has_ruler_csv and status in {"success", "skipped", "missing"}:
            skipped_with_csv += 1
            continue
        if status not in {"failed", "missing"}:
            continue

        model_key = _model_key(str(manifest.get("model_id", "")))
        run_name = str(manifest.get("run_name", "")).strip()
        if not model_key or not run_name:
            continue

        seed = int(manifest.get("seed", 0))
        grouped[model_key][seed].add(run_name)

        src_log = logs_dir / run_dir.name / "eval_ruler.log"
        if src_log.exists():
            dst_log = logs_dir / "logs_legacy_failures" / run_dir.name / f"eval_ruler.{now}.log"
            archives.append((src_log, dst_log))

    commands: list[list[str]] = []
    for model_key in sorted(grouped):
        for seed in sorted(grouped[model_key]):
            commands.append(
                [
                    args.python_bin,
                    "scripts/run_experiments.py",
                    "--config",
                    CONFIG_BY_MODEL[model_key],
                    "--tasks",
                    "eval_ruler",
                    "--seeds",
                    str(seed),
                    "--run_names",
                    ",".join(sorted(grouped[model_key][seed])),
                    "--run_tag",
                    f"{args.new_run_tag_prefix}{model_key}_s{seed}",
                    "--skip_completed_success",
                    "--failure_policy",
                    "continue_all",
                ]
            )

    shell_path = runs_dir.parent / "repair_commands.sh"
    shell_path.write_text(
        "\n".join(" ".join(shlex.quote(x) for x in cmd) for cmd in commands) + ("\n" if commands else ""),
        encoding="utf-8",
    )

    target_count = sum(len(names) for seeds in grouped.values() for names in seeds.values())
    print(f"scanned run dirs: {scanned}")
    print(f"skipped running: {skipped_running}")
    print(f"skipped with existing profile_ruler csv: {skipped_with_csv}")
    print(f"repair targets: {target_count} run_names")
    print(f"commands: {len(commands)}")
    print(f"written: {shell_path}")
    for cmd in commands:
        print("CMD:", " ".join(shlex.quote(x) for x in cmd))

    if args.execute and not args.dry_run:
        for src, dst in archives:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        for cmd in commands:
            subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
