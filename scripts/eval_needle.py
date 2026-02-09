#!/usr/bin/env python3
"""
D4: Needle In A Haystack (eval_needle.py)
Strategy A: Synthetic UUID Retrieval.
"""

import argparse
import csv
import sys
import torch
import uuid
import numpy as np
from datetime import datetime
from pathlib import Path
import subprocess

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

def generate_haystack(tokenizer, context_len, needle, depth_percent):
    """
    Generates a haystack text with the needle inserted at depth_percent.
    Haystack is "The quick brown fox..." repeated.
    """
    filler = "The quick brown fox jumps over the lazy dog. " * 50
    filler_tokens = tokenizer.encode(filler, add_special_tokens=False)
    
    # Needle phrasing
    needle_text = f" The special secret passkey is {needle}. Remember it. "
    needle_tokens = tokenizer.encode(needle_text, add_special_tokens=False)
    
    # Target total tokens
    target_len = context_len - 100 # leave room for system prompt / response
    
    # Calculate insertion point
    depth_idx = int(target_len * (depth_percent / 100))
    
    # Construct
    # Fill up to depth
    current_tokens = []
    while len(current_tokens) < depth_idx:
        current_tokens.extend(filler_tokens)
    current_tokens = current_tokens[:depth_idx]
    
    # Insert needle
    current_tokens.extend(needle_tokens)
    
    # Fill rest
    while len(current_tokens) < target_len:
        current_tokens.extend(filler_tokens)
    current_tokens = current_tokens[:target_len]
    
    return tokenizer.decode(current_tokens)

def main():
    parser = argparse.ArgumentParser(description="D4: Needle Evaluation")
    parser.add_argument("--context_len", type=int, default=4096)
    parser.add_argument("--num_depths", type=int, default=10) # How many checkpoints (e.g. 0, 10, ... 100)
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

    depths = np.linspace(0, 100, args.num_depths)
    results = []
    timestamp = datetime.now().isoformat()
    git_commit = get_git_commit()
    hardware = get_hardware_info()

    print(f"Running Needle Test (Context: {args.context_len}, Depths: {args.num_depths})...")

    pass_count = 0
    
    for depth in depths:
        needle = str(uuid.uuid4())
        haystack = generate_haystack(tokenizer, args.context_len, needle, depth)
        
        prompt = (
            f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
            f"<|im_start|>user\n{haystack}\n\n"
            f"What is the special passkey mentioned in the text?<|im_end|>\n"
            f"<|im_start|>assistant\nMO" # Prefill slightly to guide
        )
        
        out = generate(
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            max_new_tokens=32, # short gen
            kv_mode=args.kv_mode,
            group_size=args.group_size,
            clip_percentile=args.clip_percentile,
            calib_file=args.calib_file,
            use_attn_temperature=args.use_attn_temperature,
            seed=args.seed,
        )
        
        # Verify
        generated_text = out.text
        passed = needle in generated_text
        if passed: pass_count += 1
        
        print(f"Depth {depth:.1f}%: {'PASS' if passed else 'FAIL'} (Needle: {needle} vs Gen: {generated_text.strip()})")
        
        results.append({
            "depth": depth,
            "passed": int(passed),
            "generated": generated_text
        })

    pass_rate = (pass_count / len(depths)) * 100
    print(f"\nFinal Pass Rate: {pass_rate:.2f}%")

    if args.save_csv:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"profile_needle_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        
        row = {
            "run_id": f"needle_{timestamp}",
            "model_id": args.model_id,
            "kv_mode": args.kv_mode,
            "quant_bits": 4 if "int4" in args.kv_mode else (8 if "int8" in args.kv_mode else 16),
            "clip_percentile": args.clip_percentile,
            "group_size": args.group_size,
            "dtype": str(model.dtype),
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "seq_len": args.context_len,
            "gen_len": 32,
            "batch": 1,
            "ttft_ms": 0,
            "tpot_ms": 0,
            "tok_per_s": 0,
            "gpu_mem_peak_mb": 0,
            "timestamp": timestamp,
            "git_commit": git_commit,
            "needle_pass_rate": pass_rate
        }
        
        fields = [
            "run_id", "model_id", "kv_mode", "quant_bits", "clip_percentile", "group_size", 
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "tok_per_s", "gpu_mem_peak_mb", "timestamp", "git_commit", "needle_pass_rate"
        ]
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
        print(f"Saved to {path}")

        run_snapshot_dir = out_dir / row["run_id"]
        snapshot = build_config_snapshot(
            script_name=Path(__file__).name,
            args=args,
        )
        write_config_snapshot(str(run_snapshot_dir), snapshot)

if __name__ == "__main__":
    main()
