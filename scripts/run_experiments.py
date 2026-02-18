#!/usr/bin/env python3
"""
Run experiment matrix defined in configs/exp_matrix.yaml.
"""

from __future__ import annotations

import argparse
import os
import re
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
    use_static_scales = run_entry.get(
        "use_static_scales", quant_defaults.get("use_static_scales", True)
    )
    adaptive_static_scales = run_entry.get(
        "adaptive_static_scales", quant_defaults.get("adaptive_static_scales", False)
    )
    adaptive_static_margin = run_entry.get(
        "adaptive_static_margin", quant_defaults.get("adaptive_static_margin", 1.0)
    )
    adaptive_static_k = run_entry.get(
        "adaptive_static_k", quant_defaults.get("adaptive_static_k", True)
    )
    adaptive_static_v = run_entry.get(
        "adaptive_static_v", quant_defaults.get("adaptive_static_v", True)
    )
    calib_strategy = run_entry.get("calib_strategy", quant_defaults.get("calib_strategy"))
    return {
        "calib_file": calib_file,
        "use_attn_temperature": use_attn_temperature,
        "use_static_scales": use_static_scales,
        "adaptive_static_scales": adaptive_static_scales,
        "adaptive_static_margin": adaptive_static_margin,
        "adaptive_static_k": adaptive_static_k,
        "adaptive_static_v": adaptive_static_v,
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
    parser.add_argument(
        "--run_tag",
        type=str,
        default=None,
        help=(
            "Override the timestamp suffix used to build per-run directories: "
            "run_id = <run_name>_<run_tag>. Use the same --run_tag across multiple "
            "invocations to append different tasks into the same run_id directory."
        ),
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Append mode for an existing run_id directory: keep the existing "
            "config_snapshot.yaml (if present) and append to task logs instead of overwriting."
        ),
    )
    parser.add_argument("--out_dir", type=str, default="results/runs")
    parser.add_argument("--logs_dir", type=str, default="logs/run_experiments")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help=(
            "Comma-separated seed list. When provided, each selected run_name is executed once per seed "
            "and the seed is appended to the run_id as '<run_name>_s<seed>_<run_tag>'. "
            "When omitted, uses runtime.seed from the config."
        ),
    )
    parser.add_argument("--ppl_max_length", type=int, default=1024)
    parser.add_argument("--ppl_stride", type=int, default=512)
    parser.add_argument(
        "--ppl_chunk_size",
        type=int,
        default=128,
        help=(
            "Pass through to eval_ppl.py --chunk_size for ppl_mode=kv_cache. Larger chunks reduce "
            "Python overhead and increase GPU utilization."
        ),
    )
    parser.add_argument(
        "--ppl_mode",
        type=str,
        default="kv_cache",
        choices=["hf", "kv_cache"],
        help="Pass through to eval_ppl.py --ppl_mode.",
    )
    parser.add_argument(
        "--ppl_max_samples",
        type=int,
        default=32,
        help=(
            "Pass through to eval_ppl.py --max_samples to limit total evaluated tokens. "
            "NOTE: kv_cache PPL can still be slow on large settings; reduce this if you hit time limits."
        ),
    )
    parser.add_argument("--needle_context_len", type=int, default=None)
    parser.add_argument(
        "--needle_num_depths",
        type=int,
        default=None,
        help="Pass through to eval_needle.py --num_depths to reduce evaluation cost.",
    )
    parser.add_argument(
        "--needle_max_new_tokens",
        type=int,
        default=64,
        help="Pass through to eval_needle.py --needle_max_new_tokens.",
    )
    parser.add_argument(
        "--needle_depth_batch",
        type=int,
        default=1,
        help="Pass through to eval_needle.py --depth_batch to batch multiple depths per forward.",
    )
    parser.add_argument(
        "--needle_report_exact_match",
        action="store_true",
        default=False,
        help="Pass through to eval_needle.py --report_exact_match (appendix metric only).",
    )
    parser.add_argument(
        "--latency_runs",
        type=int,
        default=None,
        help="Pass through to profile_latency.py --runs (useful for long-context runs).",
    )
    parser.add_argument(
        "--latency_warmup",
        type=int,
        default=None,
        help="Pass through to profile_latency.py --warmup (useful for long-context runs).",
    )
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
        try:
            from src.utils.repro import build_config_snapshot, write_config_snapshot
        except ModuleNotFoundError as exc:
            if getattr(exc, "name", None) == "torch":
                print("Error: torch is not installed in this environment.")
                print("Run this on the GPU server (see AGENTS.md and .agent/skills/remote-server/SKILL.md),")
                print("or rerun with --dry_run to preview commands.")
                return 2
            raise

    project = config.get("project", {})
    runtime = config.get("runtime", {})
    quant_defaults = runtime.get("quant_defaults", {})
    kernel_defaults = runtime.get("kernel_defaults", {})

    model_id = project.get("model_id", "Qwen/Qwen2.5-1.5B-Instruct")
    model_revision = project.get("model_revision")
    default_seed = runtime.get("seed", 1234)
    seed_list = [int(default_seed)]
    if args.seeds:
        raw = [x.strip() for x in args.seeds.split(",") if x.strip()]
        if not raw:
            print("Error: --seeds must contain at least one integer.")
            return 2
        try:
            seed_list = [int(x) for x in raw]
        except ValueError:
            print(f"Error: invalid --seeds value: {args.seeds!r}. Expected comma-separated integers.")
            return 2

    max_position_embeddings = None
    if not args.dry_run:
        try:
            from transformers import AutoConfig

            model_cfg = AutoConfig.from_pretrained(
                model_id,
                revision=model_revision,
                trust_remote_code=True,
            )
            max_position_embeddings = getattr(model_cfg, "max_position_embeddings", None)
        except ModuleNotFoundError as exc:
            if getattr(exc, "name", None) in {"transformers", "torch"}:
                print(
                    "Error: transformers/torch is not installed in this environment. "
                    "Run on the GPU server or use --dry_run."
                )
                return 2
            raise
        except Exception as exc:
            print(f"Error: failed to load model config for length gate check: {exc}")
            return 2

    task_list = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if args.run_names:
        run_name_filter = {
            name.strip() for name in args.run_names.split(",") if name.strip()
        }
    else:
        run_name_filter = None

    matrix = config.get("matrix", [])
    run_tag = args.run_tag.strip() if args.run_tag else datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.run_tag:
        if not run_tag:
            print("Error: --run_tag must be a non-empty string.")
            return 2
        if not re.fullmatch(r"[A-Za-z0-9._-]+", run_tag):
            print(
                "Error: --run_tag contains unsupported characters. "
                "Allowed: letters, digits, '.', '_', '-'."
            )
            return 2

    for run_entry in matrix:
        run_name = run_entry.get("run_name")
        if not run_name:
            continue
        if run_name_filter and run_name not in run_name_filter:
            continue

        kv_mode = run_entry.get("kv_mode", "fp16")
        if kv_mode not in [
            "fp16",
            "int8_baseline",
            "int8_fused",
            "int8_ours",
            "int4_baseline",
            "int4_fused",
            "int4_ours",
            "int4_ours_mixed",
        ]:
            print(f"Skip unsupported kv_mode={kv_mode} for {run_name}")
            continue

        seq_len = run_entry.get("seq_len", 1024)
        gen_len = run_entry.get("gen_len", 128)
        batch = int(run_entry.get("batch", 1) or 1)
        if max_position_embeddings is not None and seq_len + gen_len > int(max_position_embeddings):
            suggested_seq_len = max(int(max_position_embeddings) - int(gen_len), 1)
            print(
                "Error: run exceeds model max_position_embeddings. "
                f"run_name={run_name} seq_len={seq_len} gen_len={gen_len} "
                f"max_position_embeddings={max_position_embeddings}."
            )
            print(
                "Suggested fix: set "
                f"seq_len <= {suggested_seq_len} (or reduce gen_len)."
            )
            return 2

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

        if not args.dry_run and kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed"]:
            needs_calib = (
                calib_params.get("calib_strategy") == "kl_attn"
                or calib_params.get("use_attn_temperature") is True
            )
            if needs_calib and (calib_file_path is None or not calib_file_path.exists()):
                print(
                    f"Error: kv_mode={kv_mode} requires calibration file but it was not found: {calib_file_path}."
                )
                print(
                    "Run scripts/calibrate_behavior.py to generate it, or switch calib_strategy to 'percentile' and "
                    "disable use_attn_temperature."
                )
                return 2

        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir

        logs_dir = Path(args.logs_dir)
        if not logs_dir.is_absolute():
            logs_dir = project_root / logs_dir

        multi_seed = args.seeds is not None and len(seed_list) > 0
        for replica_id, seed in enumerate(seed_list):
            run_id = f"{run_name}_s{seed}_{run_tag}" if multi_seed else f"{run_name}_{run_tag}"
            run_dir = out_dir / run_id
            if not args.dry_run:
                run_dir.mkdir(parents=True, exist_ok=True)

            if build_config_snapshot and write_config_snapshot:
                snapshot = build_config_snapshot(
                    script_name=Path(__file__).name,
                    args=args,
                    extra={"run_entry": run_entry, "model_id": model_id, "seed": int(seed)},
                )
                if args.append and (run_dir / "config_snapshot.yaml").exists():
                    pass
                else:
                    write_config_snapshot(str(run_dir), snapshot)

            for task in task_list:
                script = TASK_TO_SCRIPT.get(task)
                if not script:
                    print(f"Unknown task: {task}")
                    continue

                cmd = [
                    sys.executable,
                    "-u",
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
                if model_revision:
                    cmd.extend(["--model_revision", str(model_revision)])
                if kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed"] and calib_file_path:
                    cmd.extend(["--calib_file", str(calib_file_path)])
                if calib_params.get("calib_strategy"):
                    cmd.extend(["--calib_strategy", str(calib_params["calib_strategy"])])
                if calib_params.get("use_attn_temperature") is False:
                    cmd.append("--no_use_attn_temperature")
                if calib_params.get("use_static_scales") is False:
                    cmd.append("--no_use_static_scales")
                if calib_params.get("adaptive_static_scales") is True:
                    cmd.append("--adaptive_static_scales")
                adaptive_static_margin = calib_params.get("adaptive_static_margin")
                if (
                    adaptive_static_margin is not None
                    and float(adaptive_static_margin) != 1.0
                ):
                    cmd.extend(["--adaptive_static_margin", str(adaptive_static_margin)])
                if calib_params.get("adaptive_static_k") is False:
                    cmd.append("--no_adaptive_static_k")
                if calib_params.get("adaptive_static_v") is False:
                    cmd.append("--no_adaptive_static_v")
                if decode_attn_impl:
                    cmd.extend(["--decode_attn_impl", str(decode_attn_impl)])

                if task == "eval_ppl":
                    max_length = min(seq_len, args.ppl_max_length)
                    cmd.extend(["--ppl_mode", str(args.ppl_mode)])
                    cmd.extend(["--max_length", str(max_length)])
                    cmd.extend(["--stride", str(args.ppl_stride)])
                    if args.ppl_max_samples is not None:
                        cmd.extend(["--max_samples", str(args.ppl_max_samples)])
                    if args.ppl_chunk_size is not None:
                        cmd.extend(["--chunk_size", str(args.ppl_chunk_size)])
                    cmd.extend(["--replica_id", str(replica_id)])

                if task == "eval_needle":
                    cmd.extend(["--needle_max_new_tokens", str(args.needle_max_new_tokens)])
                    if args.needle_context_len:
                        cmd.extend(["--context_len", str(args.needle_context_len)])
                    if args.needle_num_depths is not None:
                        cmd.extend(["--num_depths", str(args.needle_num_depths)])
                    if args.needle_depth_batch is not None:
                        cmd.extend(["--depth_batch", str(args.needle_depth_batch)])
                    if args.needle_report_exact_match:
                        cmd.append("--report_exact_match")

                if task == "profile_latency":
                    cmd.extend(["--batch", str(batch)])
                    if args.latency_runs is not None:
                        cmd.extend(["--runs", str(args.latency_runs)])
                    if args.latency_warmup is not None:
                        cmd.extend(["--warmup", str(args.latency_warmup)])

                if task == "profile_memory":
                    cmd.extend(["--batch", str(batch)])

                log_path = logs_dir / run_id / f"{task}.log"

                if args.dry_run:
                    print("DRY RUN:", " ".join(cmd))
                    continue

                label = f"{run_name} (seed={seed})" if multi_seed else run_name
                print(f"Running {task} for {label}")
                try:
                    if args.append:
                        # Append logs for long-running/resumed runs.
                        log_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(log_path, "a") as f:
                            result = subprocess.run(
                                cmd, stdout=f, stderr=subprocess.STDOUT, text=True
                            )
                        if result.returncode != 0:
                            raise RuntimeError(f"Task failed: {' '.join(cmd)}")
                    else:
                        run_task(cmd, log_path)
                except RuntimeError as exc:
                    print(str(exc))
                    return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
