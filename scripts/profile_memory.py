#!/usr/bin/env python3
"""
D2: Memory Profiling Script
Detailed memory analysis (sampling & peak) for objective.md compliance.
"""

import argparse
import csv
import json
import sys
import torch
import gc
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
import subprocess

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.engine.generate_loop import generate_from_ids
from src.utils.hf import resolve_pretrained_path
from src.utils.repro import (
    build_config_snapshot,
    get_hardware_info,
    set_seed,
    write_config_snapshot,
)
from transformers import AutoModelForCausalLM, AutoTokenizer
from scripts.config_utils import load_config, normalize_kv_params, resolve_run_config

try:
    import pynvml
except ImportError:
    pynvml = None

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

class MemoryMonitor(threading.Thread):
    def __init__(self, device_id=0, interval=0.1):
        super().__init__()
        self.device_id = device_id
        self.interval = interval
        self.stop_signal = False
        self.peak_mem = 0
        self.history = []
        if pynvml:
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
        else:
            self.handle = None

    def run(self):
        if not self.handle:
            return
        while not self.stop_signal:
            info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            used_mb = info.used / 1024 / 1024
            self.peak_mem = max(self.peak_mem, used_mb)
            self.history.append(used_mb)
            time.sleep(self.interval)

    def stop(self):
        self.stop_signal = True
        self.join()

def main():
    global _LAST_ARGS
    parser = argparse.ArgumentParser(description="D2: Memory Profiling")
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
            "kivi_style",
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
    parser.add_argument("--batch", type=int, default=1)
    # Schema args
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
        "--quant_bits",
        type=int,
        default=None,
        help="Override quant_bits for CSV output (needed for kivi_style which can be 4 or 8).",
    )
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

    txt = "Hello " * args.seq_len
    tokens = tokenizer.encode(txt, add_special_tokens=False)[:args.seq_len]
    prompt_str = tokenizer.decode(tokens)

    # Warmup
    warmup_ids = tokenizer("Hi", return_tensors="pt")["input_ids"].to(model.device)
    warmup_ids = warmup_ids.repeat(int(args.batch), 1)
    warmup_mask = torch.ones_like(warmup_ids, dtype=torch.long, device=model.device)
    generate_from_ids(
        model=model,
        tokenizer=tokenizer,
        input_ids=warmup_ids,
        attention_mask=warmup_mask,
        max_new_tokens=2,
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
        quant_bits=getattr(args, 'quant_bits', None),
    )

    hardware = get_hardware_info()

    print("Profiling Memory...")
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    
    # Start Monitor
    monitor = MemoryMonitor()
    monitor.start()

    try:
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
            quant_bits=getattr(args, 'quant_bits', None),
        )
    finally:
        monitor.stop()

    torch_peak = torch.cuda.max_memory_allocated() / 1024 / 1024
    nvml_peak = monitor.peak_mem
    kv_cache_mem_mb = float(getattr(out, "kv_cache_mem_mb", 0.0))
    kv_cache_seq_len = int(getattr(out, "kv_cache_seq_len", 0))
    print(f"Torch Peak: {torch_peak:.2f} MB")
    print(f"NVML Peak: {nvml_peak:.2f} MB")
    print(f"KV Cache (resident): {kv_cache_mem_mb:.2f} MB")
    print(f"KV Cache (seq_len): {kv_cache_seq_len}")

    if args.save_csv:
        timestamp = datetime.now().isoformat()
        git_commit = get_git_commit()
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"profile_memory_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        
        row = {
            "run_id": f"mem_{timestamp}",
            "model_id": args.model_id,
            "run_name": args.run_name,
            "kv_mode": args.kv_mode,
            "quant_bits": getattr(args, 'quant_bits', None) or (4 if "int4" in args.kv_mode else (8 if "int8" in args.kv_mode else 16)),
            "clip_percentile": args.clip_percentile,
            "group_size": args.group_size,
            "dtype": str(model.dtype),
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "seq_len": out.prompt_len,
            "gen_len": out.gen_len,
            "batch": int(args.batch),
            "ttft_ms": round(out.ttft_ms, 2),
            "tpot_ms": round(out.tpot_ms, 2),
            "tok_per_s": round(out.tok_per_s, 2),
            "tok_per_s_per_seq": round(out.tok_per_s_per_seq, 2),
            "gpu_mem_peak_mb": round(nvml_peak if nvml_peak > 0 else torch_peak, 2), # Prefer NVML if avail
            "torch_peak_mb": round(torch_peak, 2),
            "nvml_peak_mb": round(nvml_peak, 2),
            "kv_cache_mem_mb": round(kv_cache_mem_mb, 2),
            "kv_cache_seq_len": int(kv_cache_seq_len),
            "timestamp": timestamp,
            "git_commit": git_commit,
            "seed": int(args.seed),
            "replica_id": int(args.replica_id),
        }

        run_snapshot_dir = out_dir / row["run_id"]
        snapshot = build_config_snapshot(
            script_name=Path(__file__).name,
            args=args,
        )
        write_config_snapshot(str(run_snapshot_dir), snapshot)
        
        fields = [
            "run_id", "model_id", "run_name", "kv_mode", "quant_bits", "clip_percentile", "group_size",
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "tok_per_s", "tok_per_s_per_seq", "gpu_mem_peak_mb", "torch_peak_mb", "nvml_peak_mb", "kv_cache_mem_mb",
            "kv_cache_seq_len", "timestamp", "git_commit", "seed", "replica_id"
        ]
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
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
                message="CUDA out of memory during profile_memory execution.",
                exception=exc,
            )
        sys.exit(EXIT_OOM)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="exception",
                message="Unhandled exception during profile_memory execution.",
                exception=exc,
            )
        sys.exit(EXIT_EXCEPTION)
