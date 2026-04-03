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
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runs_dir", required=True)
    p.add_argument("--logs_dir", required=True)
    p.add_argument("--run_tag_prefix", default="phase5v2_")
    p.add_argument("--new_run_tag_prefix", default="phase5v2r1_")
    p.add_argument("--python_bin", default="/root/miniconda3/bin/python")
    p.add_argument("--execute", action="store_true", default=False)
    p.add_argument("--dry_run", action="store_true", default=False)
    args = p.parse_args()
    runs_dir, logs_dir = Path(args.runs_dir), Path(args.logs_dir)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    grouped: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    archives: list[tuple[Path, Path]] = []
    for run_dir in sorted(runs_dir.iterdir()):
        mp = run_dir / "run_manifest.json"
        if not mp.exists():
            continue
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Warning: failed to parse {mp}: {exc}")
            continue
        if not str(m.get("run_tag", "")).startswith(args.run_tag_prefix):
            continue
        status = str(((m.get("tasks", {}) or {}).get("eval_ruler", {}) or {}).get("status", "")).strip().lower() or "missing"
        if status not in {"failed", "missing"}:
            continue
        key, run_name = _model_key(str(m.get("model_id", ""))), str(m.get("run_name", "")).strip()
        if not key or not run_name:
            continue
        seed = int(m.get("seed", 0))
        grouped[key][seed].add(run_name)
        src_log = logs_dir / run_dir.name / "eval_ruler.log"
        if src_log.exists():
            dst_log = (
                logs_dir / "logs_legacy_failures" / run_dir.name / f"eval_ruler.{now}.log"
            )
            archives.append((src_log, dst_log))
    commands: list[list[str]] = []
    for key in sorted(grouped):
        for seed in sorted(grouped[key]):
            commands.append([
                args.python_bin, "scripts/run_experiments.py", "--config", CONFIG_BY_MODEL[key],
                "--tasks", "eval_ruler", "--seeds", str(seed),
                "--run_names", ",".join(sorted(grouped[key][seed])),
                "--run_tag", f"{args.new_run_tag_prefix}{key}_s{seed}",
                "--append", "--skip_completed_success", "--failure_policy", "continue_all",
            ])
    shell_path = runs_dir.parent / "repair_commands.sh"
    # EVL-097: don't silently overwrite existing file
    if shell_path.exists():
        bak = shell_path.with_suffix(".sh.bak")
        shell_path.rename(bak)
        print(f"  Backed up existing {shell_path.name} → {bak.name}")
    shell_path.write_text(
        "\n".join(" ".join(shlex.quote(x) for x in cmd) for cmd in commands) + ("\n" if commands else ""),
        encoding="utf-8",
    )
    target_count = sum(len(names) for seeds in grouped.values() for names in seeds.values())
    print(f"repair targets: {target_count} run_names")
    print(f"commands: {len(commands)}")
    print(f"written: {shell_path}")
    for cmd in commands:
        print("CMD:", " ".join(shlex.quote(x) for x in cmd))
    if args.execute and not args.dry_run:
        project_root = runs_dir.parent
        failed_cmds: list[tuple[list[str], int]] = []
        for cmd in commands:
            result = subprocess.run(cmd, cwd=project_root)
            if result.returncode != 0:
                print(f"Warning: command failed (rc={result.returncode}): {' '.join(cmd)}")
                failed_cmds.append((cmd, result.returncode))
        # Archive old logs only after commands have executed
        for src, dst in archives:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        if failed_cmds:
            print(f"\n{len(failed_cmds)} command(s) failed:")
            for fc, rc in failed_cmds:
                print(f"  rc={rc}: {' '.join(fc)}")
            return 1
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
