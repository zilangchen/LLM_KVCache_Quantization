#!/usr/bin/env python3
"""
D1: Latency Profiling Script
Standardized TTFT/TPOT profiling for objective.md compliance.
"""

import argparse
import csv
import json
import sys
import torch
import gc
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.engine.generate_loop import generate_from_ids
from src.utils.hf import resolve_pretrained_path
from src.utils.timing import reset_gpu_memory_stats
from src.utils.repro import (
    build_config_snapshot,
    get_hardware_info,
    set_seed,
    write_config_snapshot,
)
from scripts.config_utils import load_config, normalize_kv_params, resolve_run_config
from transformers import AutoModelForCausalLM, AutoTokenizer
import subprocess

EXIT_OOM = 73
EXIT_EXCEPTION = 74
_LAST_ARGS: argparse.Namespace | None = None


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root,
        )
        return result.stdout.strip()[:8]
    except Exception:
        return "unknown"


def _resolve_out_dir(out_dir_arg: str) -> Path:
    out_dir = Path(out_dir_arg)
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_task_failure(
    *,
    args: argparse.Namespace,
    failure_type: str,
    message: str,
    exception: Exception | None = None,
) -> None:
    out_dir = _resolve_out_dir(args.out_dir)
    payload = {
        "script": Path(__file__).name,
        "timestamp": datetime.now().isoformat(),
        "failure_type": str(failure_type),
        "message": str(message),
        "kv_mode": str(getattr(args, "kv_mode", "")),
        "run_name": str(getattr(args, "run_name", "")),
        "seed": int(getattr(args, "seed", 0)),
        "replica_id": int(getattr(args, "replica_id", 0)),
        "seq_len": int(getattr(args, "seq_len", 0)),
        "gen_len": int(getattr(args, "gen_len", 0)),
        "batch": int(getattr(args, "batch", 1)),
    }
    if exception is not None:
        payload["exception_type"] = type(exception).__name__
        payload["exception_repr"] = repr(exception)
        payload["traceback"] = traceback.format_exc()
    path = out_dir / f"task_failure_{Path(__file__).stem}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

def main():
    global _LAST_ARGS
    parser = argparse.ArgumentParser(description="D1: Latency Profiling")
    parser.add_argument("--seq_len", type=int, default=1024)
    parser.add_argument("--gen_len", type=int, default=128)
    parser.add_argument(
        "--kv_mode",
        type=str,
        default="fp16",
        choices=[
            "fp16",
            "int8_baseline",
            "int8_fused",
            "int8_ours",
            "int4_baseline",
            "int4_fused",
            "int4_ours",
            "int4_ours_mixed",
        ],
    )
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument(
        "--model_revision",
        type=str,
        default=None,
        help="Optional model revision (commit hash/tag) for strict reproducibility.",
    )
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--batch", type=int, default=1)
    # Quant args (needed for schema, even if not used in fp16)
    parser.add_argument("--group_size", type=int, default=128)
    parser.add_argument("--clip_percentile", type=float, default=99.9)
    parser.add_argument("--group_size_k", type=int, default=None)
    parser.add_argument("--group_size_v", type=int, default=None)
    parser.add_argument("--clip_percentile_k", type=float, default=None)
    parser.add_argument("--clip_percentile_v", type=float, default=None)
    parser.add_argument("--calib_strategy", type=str, default=None)
    parser.add_argument("--decode_attn_impl", type=str, default=None)
    parser.add_argument("--calib_file", type=str, default=None)
    parser.add_argument(
        "--use_attn_temperature",
        dest="use_attn_temperature",
        action="store_true",
        default=True,
        help="Apply per-head temperature if available (int8_ours).",
    )
    parser.add_argument(
        "--no_use_attn_temperature",
        dest="use_attn_temperature",
        action="store_false",
        help="Disable per-head temperature even if calib provides it.",
    )
    parser.add_argument(
        "--use_static_scales",
        dest="use_static_scales",
        action="store_true",
        default=True,
        help="Use static K/V scales from calibration if available (int8_ours).",
    )
    parser.add_argument(
        "--no_use_static_scales",
        dest="use_static_scales",
        action="store_false",
        help="Ignore static K/V scales from calibration (int8_ours).",
    )
    parser.add_argument(
        "--adaptive_static_scales",
        dest="adaptive_static_scales",
        action="store_true",
        default=False,
        help="Adaptively raise static scales with runtime observed scales (int8_ours).",
    )
    parser.add_argument(
        "--no_adaptive_static_scales",
        dest="adaptive_static_scales",
        action="store_false",
        help="Disable adaptive static-scale safeguard.",
    )
    parser.add_argument(
        "--adaptive_static_margin",
        type=float,
        default=1.0,
        help="Safety margin multiplier for static scales before adaptive max.",
    )
    parser.add_argument(
        "--adaptive_static_k",
        dest="adaptive_static_k",
        action="store_true",
        default=True,
        help="Apply adaptive static-scale safeguard on K.",
    )
    parser.add_argument(
        "--no_adaptive_static_k",
        dest="adaptive_static_k",
        action="store_false",
        help="Disable adaptive static-scale safeguard on K.",
    )
    parser.add_argument(
        "--adaptive_static_v",
        dest="adaptive_static_v",
        action="store_true",
        default=True,
        help="Apply adaptive static-scale safeguard on V.",
    )
    parser.add_argument(
        "--no_adaptive_static_v",
        dest="adaptive_static_v",
        action="store_false",
        help="Disable adaptive static-scale safeguard on V.",
    )
    # Optional dump
    parser.add_argument("--save_csv", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument(
        "--replica_id",
        type=int,
        default=0,
        help="Replica id for repeated runs (set by run_experiments multi-seed loop).",
    )
    parser.add_argument("--out_dir", type=str, default="results/runs")

    args = parser.parse_args()
    _LAST_ARGS = args

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

    normalize_kv_params(args)
    set_seed(seed=args.seed, deterministic=True)

    print(f"Loading {args.model_id}...")
    model_path = resolve_pretrained_path(args.model_id, revision=args.model_revision)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, revision=args.model_revision, trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path, 
        torch_dtype=torch.float16, 
        device_map="auto", 
        revision=args.model_revision,
        trust_remote_code=True
    )

    # Fake prompt
    prompt_tokens = args.seq_len
    # Create dummy tokens (just Repeat 0)
    # Using real text is better for correctness but for strict latency dummy is okay too. 
    # Let's use the helper from profile_baseline or just simple repetition.
    # We will use "Hello " * N
    txt = "Hello " * (args.seq_len)
    tokens = tokenizer.encode(txt, add_special_tokens=False)[:args.seq_len]
    prompt_str = tokenizer.decode(tokens)

    print(f"Warmup ({args.warmup} runs)...")
    warmup_ids = tokenizer("Hello", return_tensors="pt")["input_ids"].to(model.device)
    warmup_ids = warmup_ids.repeat(int(args.batch), 1)
    warmup_mask = torch.ones_like(warmup_ids, dtype=torch.long, device=model.device)
    for _ in range(args.warmup):
        generate_from_ids(
            model=model,
            tokenizer=tokenizer,
            input_ids=warmup_ids,
            attention_mask=warmup_mask,
            max_new_tokens=8,
            kv_mode=args.kv_mode,
            group_size=args.group_size,
            clip_percentile=args.clip_percentile,
            calib_file=args.calib_file,
            use_attn_temperature=args.use_attn_temperature,
            use_static_scales=args.use_static_scales,
            adaptive_static_scales=args.adaptive_static_scales,
            adaptive_static_margin=args.adaptive_static_margin,
            adaptive_static_k=args.adaptive_static_k,
            adaptive_static_v=args.adaptive_static_v,
            decode_attn_impl=args.decode_attn_impl or "triton_fused",
            seed=args.seed,
            stop_on_eos=False,
        )

    print(f"Profiling ({args.runs} runs)...")
    results = []
    timestamp = datetime.now().isoformat()
    git_commit = get_git_commit()
    hardware = get_hardware_info()

    for i in range(args.runs):
        gc.collect()
        torch.cuda.empty_cache()
        reset_gpu_memory_stats()

        input_ids = torch.tensor(tokens, dtype=torch.long, device=model.device).unsqueeze(0)
        input_ids = input_ids.repeat(int(args.batch), 1)
        attention_mask = torch.ones_like(input_ids, dtype=torch.long, device=model.device)
        out = generate_from_ids(
            model=model,
            tokenizer=tokenizer,
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=args.gen_len,
            kv_mode=args.kv_mode,
            group_size=args.group_size,
            clip_percentile=args.clip_percentile,
            calib_file=args.calib_file,
            use_attn_temperature=args.use_attn_temperature,
            use_static_scales=args.use_static_scales,
            adaptive_static_scales=args.adaptive_static_scales,
            adaptive_static_margin=args.adaptive_static_margin,
            adaptive_static_k=args.adaptive_static_k,
            adaptive_static_v=args.adaptive_static_v,
            decode_attn_impl=args.decode_attn_impl or "triton_fused",
            seed=args.seed,
            stop_on_eos=False,
        )

        if "int4" in args.kv_mode:
            quant_bits = 4
        elif "int8" in args.kv_mode:
            quant_bits = 8
        else:
            quant_bits = 16

        prefill_tok_per_s = 0.0
        if out.ttft_ms > 0:
            prefill_tok_per_s = (int(args.batch) * int(out.prompt_len) / out.ttft_ms) * 1000.0

        row = {
            "run_id": f"lat_{timestamp}_{i}",
            "model_id": args.model_id,
            "run_name": args.run_name,
            "kv_mode": args.kv_mode,
            "quant_bits": quant_bits,
            "clip_percentile": args.clip_percentile,
            "group_size": args.group_size,
            "dtype": str(model.dtype),
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "seq_len": out.prompt_len,
            "gen_len": out.gen_len,
            "batch": int(args.batch),
            "ttft_ms": round(out.ttft_ms, 2),
            "tpot_ms": round(out.tpot_ms, 2),
            "prefill_tok_per_s": round(prefill_tok_per_s, 2),
            "tok_per_s": round(out.tok_per_s, 2),
            "tok_per_s_per_seq": round(out.tok_per_s_per_seq, 2),
            "gpu_mem_peak_mb": round(out.gpu_mem_peak_mb, 2),
            "kv_cache_mem_mb": round(getattr(out, "kv_cache_mem_mb", 0.0), 2),
            "kv_cache_seq_len": int(getattr(out, "kv_cache_seq_len", 0)),
            "timestamp": timestamp,
            "git_commit": git_commit,
            "seed": int(args.seed),
            "replica_id": int(args.replica_id),
        }
        results.append(row)
        print(
            f"Run {i}: TTFT={row['ttft_ms']}ms, TPOT={row['tpot_ms']}ms, "
            f"PrefillTPS={row['prefill_tok_per_s']}, "
            f"TPS(total)={row['tok_per_s']}, TPS/seq={row['tok_per_s_per_seq']}"
        )

        run_dir = Path(args.out_dir)
        if not run_dir.is_absolute():
            run_dir = project_root / run_dir
        run_snapshot_dir = run_dir / row["run_id"]
        snapshot = build_config_snapshot(
            script_name=Path(__file__).name,
            args=args,
        )
        write_config_snapshot(str(run_snapshot_dir), snapshot)

    if args.save_csv and results:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"profile_latency_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        
        # Schema from objective.md
        fields = [
            "run_id", "model_id", "run_name", "kv_mode", "quant_bits", "clip_percentile", "group_size",
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "prefill_tok_per_s", "tok_per_s", "tok_per_s_per_seq", "gpu_mem_peak_mb", "kv_cache_mem_mb", "kv_cache_seq_len",
            "timestamp", "git_commit", "seed", "replica_id"
        ]
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(results)
        print(f"Saved to {path}")

if __name__ == "__main__":
    try:
        main()
    except torch.cuda.OutOfMemoryError as exc:
        print("OOM")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="oom",
                message="CUDA out of memory during profile_latency execution.",
                exception=exc,
            )
        sys.exit(EXIT_OOM)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="exception",
                message="Unhandled exception during profile_latency execution.",
                exception=exc,
            )
        sys.exit(EXIT_EXCEPTION)
