#!/usr/bin/env python3
"""
D2: Memory Profiling Script
Detailed memory analysis (sampling & peak) for objective.md compliance.
"""

import argparse
import csv
import sys
import torch
import gc
import time
import threading
from datetime import datetime
from pathlib import Path
import subprocess

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.engine.generate_loop import generate
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
    parser = argparse.ArgumentParser(description="D2: Memory Profiling")
    parser.add_argument("--seq_len", type=int, default=1024)
    parser.add_argument("--gen_len", type=int, default=128)
    parser.add_argument(
        "--kv_mode",
        type=str,
        default="fp16",
        choices=["fp16", "int8_baseline", "int8_fused", "int8_ours", "int4_baseline"],
    )
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
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
    parser.add_argument("--save_csv", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out_dir", type=str, default="results/runs")

    args = parser.parse_args()

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

    normalize_kv_params(args)
    set_seed(seed=args.seed, deterministic=True)

    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, 
        torch_dtype=torch.float16, 
        device_map="auto", 
        trust_remote_code=True
    )

    txt = "Hello " * args.seq_len
    tokens = tokenizer.encode(txt, add_special_tokens=False)[:args.seq_len]
    prompt_str = tokenizer.decode(tokens)

    # Warmup
    generate(
        model,
        tokenizer,
        prompt="Hi",
        max_new_tokens=2,
        kv_mode=args.kv_mode,
        group_size=args.group_size,
        clip_percentile=args.clip_percentile,
        calib_file=args.calib_file,
        use_attn_temperature=args.use_attn_temperature,
        seed=args.seed,
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
        out = generate(
            model=model, 
            tokenizer=tokenizer, 
            prompt=prompt_str, 
            max_new_tokens=args.gen_len, 
            kv_mode=args.kv_mode,
            group_size=args.group_size,
            clip_percentile=args.clip_percentile,
            calib_file=args.calib_file,
            use_attn_temperature=args.use_attn_temperature,
            seed=args.seed,
        )
    finally:
        monitor.stop()

    torch_peak = torch.cuda.max_memory_allocated() / 1024 / 1024
    nvml_peak = monitor.peak_mem
    print(f"Torch Peak: {torch_peak:.2f} MB")
    print(f"NVML Peak: {nvml_peak:.2f} MB")

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
            "kv_mode": args.kv_mode,
            "quant_bits": 4 if "int4" in args.kv_mode else (8 if "int8" in args.kv_mode else 16),
            "clip_percentile": args.clip_percentile,
            "group_size": args.group_size,
            "dtype": str(model.dtype),
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "seq_len": out.prompt_len,
            "gen_len": out.gen_len,
            "batch": 1,
            "ttft_ms": round(out.ttft_ms, 2),
            "tpot_ms": round(out.tpot_ms, 2),
            "tok_per_s": round(out.tok_per_s, 2),
            "gpu_mem_peak_mb": round(nvml_peak if nvml_peak > 0 else torch_peak, 2), # Prefer NVML if avail
            "timestamp": timestamp,
            "git_commit": git_commit
        }

        run_snapshot_dir = out_dir / row["run_id"]
        snapshot = build_config_snapshot(
            script_name=Path(__file__).name,
            args=args,
        )
        write_config_snapshot(str(run_snapshot_dir), snapshot)
        
        fields = [
            "run_id", "model_id", "kv_mode", "quant_bits", "clip_percentile", "group_size", 
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "tok_per_s", "gpu_mem_peak_mb", "timestamp", "git_commit"
        ]
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
        print(f"Saved to {path}")

if __name__ == "__main__":
    main()
