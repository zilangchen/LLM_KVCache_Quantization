#!/usr/bin/env python3
"""
Run experiment matrix defined in configs/exp_matrix.yaml.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from scripts.config_utils import load_config


TASK_TO_SCRIPT = {
    "profile_latency": "scripts/profile_latency.py",
    "profile_memory": "scripts/profile_memory.py",
    "eval_ppl": "scripts/eval_ppl.py",
    "eval_needle": "scripts/eval_needle.py",
}


def resolve_quant_params(run_entry: Dict, quant_defaults: Dict) -> Dict[str, float]:
    clip_percentile_k = run_entry.get(
        "clip_percentile_k",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_k", 99.9)),
    )
    clip_percentile_v = run_entry.get(
        "clip_percentile_v",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_v", 99.9)),
    )
    group_size_k = run_entry.get(
        "group_size_k",
        run_entry.get("group_size", quant_defaults.get("group_size_k", 128)),
    )
    group_size_v = run_entry.get(
        "group_size_v",
        run_entry.get("group_size", quant_defaults.get("group_size_v", 128)),
    )
    return {
        "clip_percentile": clip_percentile_k,
        "group_size": group_size_k,
        "clip_percentile_k": clip_percentile_k,
        "clip_percentile_v": clip_percentile_v,
        "group_size_k": group_size_k,
        "group_size_v": group_size_v,
    }


def resolve_calib_params(run_entry: Dict, quant_defaults: Dict) -> Dict[str, object]:
    calib_file = run_entry.get("calib_file", quant_defaults.get("calib_file"))
    use_attn_temperature = run_entry.get(
        "use_attn_temperature", quant_defaults.get("use_attn_temperature", False)
    )
    calib_strategy = run_entry.get("calib_strategy", quant_defaults.get("calib_strategy"))
    return {
        "calib_file": calib_file,
        "use_attn_temperature": use_attn_temperature,
        "calib_strategy": calib_strategy,
    }


def run_task(cmd: List[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Task failed: {' '.join(cmd)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run experiment matrix")
    parser.add_argument("--config", type=str, default="configs/exp_matrix.yaml")
    parser.add_argument(
        "--tasks",
        type=str,
        default="profile_latency,profile_memory,eval_ppl,eval_needle",
        help="Comma-separated task list",
    )
    parser.add_argument(
        "--run_names",
        type=str,
        default=None,
        help="Comma-separated run_name filter",
    )
    parser.add_argument("--out_dir", type=str, default="results/runs")
    parser.add_argument("--logs_dir", type=str, default="logs/run_experiments")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--ppl_max_length", type=int, default=1024)
    parser.add_argument("--ppl_stride", type=int, default=512)
    parser.add_argument("--needle_context_len", type=int, default=None)
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    deprecated_config = (project_root / "exp_matrix.yaml").resolve()
    if config_path == deprecated_config:
        print(
            "Error: root exp_matrix.yaml is deprecated. "
            "Use configs/exp_matrix.yaml instead."
        )
        return 2

    config = load_config(args.config)
    if args.dry_run:
        build_config_snapshot = None
        write_config_snapshot = None
    else:
        # Keep --dry_run usable on machines without torch installed.
        from src.utils.repro import build_config_snapshot, write_config_snapshot

    project = config.get("project", {})
    runtime = config.get("runtime", {})
    quant_defaults = runtime.get("quant_defaults", {})
    kernel_defaults = runtime.get("kernel_defaults", {})

    model_id = project.get("model_id", "Qwen/Qwen2.5-1.5B-Instruct")
    seed = runtime.get("seed", 1234)

    task_list = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if args.run_names:
        run_name_filter = {
            name.strip() for name in args.run_names.split(",") if name.strip()
        }
    else:
        run_name_filter = None

    matrix = config.get("matrix", [])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for run_entry in matrix:
        run_name = run_entry.get("run_name")
        if not run_name:
            continue
        if run_name_filter and run_name not in run_name_filter:
            continue

        kv_mode = run_entry.get("kv_mode", "fp16")
        if kv_mode not in ["fp16", "int8_baseline", "int8_fused", "int8_ours", "int4_baseline"]:
            print(f"Skip unsupported kv_mode={kv_mode} for {run_name}")
            continue

        seq_len = run_entry.get("seq_len", 1024)
        gen_len = run_entry.get("gen_len", 128)
        quant_params = resolve_quant_params(run_entry, quant_defaults)
        calib_params = resolve_calib_params(run_entry, quant_defaults)
        decode_attn_impl = run_entry.get(
            "decode_attn_impl", kernel_defaults.get("decode_attn_impl")
        )

        calib_file_path = None
        calib_file = calib_params.get("calib_file")
        if calib_file:
            calib_file_path = Path(calib_file)
            if not calib_file_path.is_absolute():
                calib_file_path = project_root / calib_file_path

        if not args.dry_run and kv_mode == "int8_ours":
            needs_calib = (
                calib_params.get("calib_strategy") == "kl_attn"
                or calib_params.get("use_attn_temperature") is True
            )
            if needs_calib and (calib_file_path is None or not calib_file_path.exists()):
                print(
                    f"Error: kv_mode=int8_ours requires calibration file but it was not found: {calib_file_path}."
                )
                print(
                    "Run scripts/calibrate_behavior.py to generate it, or switch calib_strategy to 'percentile' and "
                    "disable use_attn_temperature."
                )
                return 2

        run_id = f"{run_name}_{timestamp}"
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir
        run_dir = out_dir / run_id
        if not args.dry_run:
            run_dir.mkdir(parents=True, exist_ok=True)

        if build_config_snapshot and write_config_snapshot:
            snapshot = build_config_snapshot(
                script_name=Path(__file__).name,
                args=args,
                extra={"run_entry": run_entry, "model_id": model_id},
            )
            write_config_snapshot(str(run_dir), snapshot)

        for task in task_list:
            script = TASK_TO_SCRIPT.get(task)
            if not script:
                print(f"Unknown task: {task}")
                continue

            cmd = [
                sys.executable,
                script,
                "--kv_mode",
                kv_mode,
                "--model_id",
                model_id,
                "--seq_len",
                str(seq_len),
                "--gen_len",
                str(gen_len),
                "--group_size",
                str(quant_params["group_size"]),
                "--clip_percentile",
                str(quant_params["clip_percentile"]),
                "--group_size_k",
                str(quant_params["group_size_k"]),
                "--group_size_v",
                str(quant_params["group_size_v"]),
                "--clip_percentile_k",
                str(quant_params["clip_percentile_k"]),
                "--clip_percentile_v",
                str(quant_params["clip_percentile_v"]),
                "--seed",
                str(seed),
                "--out_dir",
                str(run_dir),
            ]
            if kv_mode == "int8_ours" and calib_file_path:
                cmd.extend(["--calib_file", str(calib_file_path)])
            if calib_params.get("calib_strategy"):
                cmd.extend(["--calib_strategy", str(calib_params["calib_strategy"])])
            if calib_params.get("use_attn_temperature") is False:
                cmd.append("--no_use_attn_temperature")
            if decode_attn_impl:
                cmd.extend(["--decode_attn_impl", str(decode_attn_impl)])

            if task == "eval_ppl":
                max_length = min(seq_len, args.ppl_max_length)
                cmd.extend(["--max_length", str(max_length)])
                cmd.extend(["--stride", str(args.ppl_stride)])

            if task == "eval_needle" and args.needle_context_len:
                cmd.extend(["--context_len", str(args.needle_context_len)])

            logs_dir = Path(args.logs_dir)
            if not logs_dir.is_absolute():
                logs_dir = project_root / logs_dir
            log_path = logs_dir / run_id / f"{task}.log"

            if args.dry_run:
                print("DRY RUN:", " ".join(cmd))
                continue

            print(f"Running {task} for {run_name}")
            try:
                run_task(cmd, log_path)
            except RuntimeError as exc:
                print(str(exc))
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
