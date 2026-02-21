#!/usr/bin/env python3
"""
Profile FP16 baseline generation performance.

.. deprecated::
    This is a legacy script from Milestone B. For new evaluations,
    use ``scripts/profile_latency.py`` or ``scripts/run_experiments.py``.

This script tests the custom generation loop (NOT model.generate()) and
outputs structured performance metrics including TTFT, TPOT, throughput,
and GPU memory usage.

Usage:
    python scripts/profile_baseline.py
    python scripts/profile_baseline.py --seq_len 2048 --gen_len 256
    python scripts/profile_baseline.py --prompt "Your custom prompt"

Output:
    CSV file at results/runs/profile_baseline_<timestamp>.csv
"""

import argparse
import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from scripts.config_utils import load_config, resolve_run_config

def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root,
        )
        return result.stdout.strip()[:8]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def generate_prompt(target_tokens: int, tokenizer) -> str:
    """
    Generate a prompt with approximately target_tokens length.

    Uses a repeating pattern to reach the desired token count.
    """
    base_text = (
        "The quick brown fox jumps over the lazy dog. "
        "In a world of artificial intelligence, language models "
        "have become increasingly powerful and capable. "
    )
    # Estimate tokens per character (roughly 4 chars per token for English)
    chars_per_token = 4
    target_chars = target_tokens * chars_per_token

    # Repeat base text to reach target length
    repeated = base_text * (target_chars // len(base_text) + 1)
    candidate = repeated[:target_chars]

    # Tokenize and adjust
    tokens = tokenizer.encode(candidate, add_special_tokens=False)
    while len(tokens) > target_tokens:
        candidate = candidate[:-10]
        tokens = tokenizer.encode(candidate, add_special_tokens=False)

    return candidate


def main():
    """Main profiling function."""
    parser = argparse.ArgumentParser(
        description="Profile FP16 baseline generation performance"
    )
    parser.add_argument(
        "--seq_len",
        type=int,
        default=1024,
        help="Target prompt length in tokens (default: 1024)",
    )
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
        help="KV cache mode (default: fp16)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configs/exp_matrix.yaml",
    )
    parser.add_argument(
        "--run_name",
        type=str,
        default=None,
        help="Run name to resolve from exp_matrix.yaml",
    )
    parser.add_argument(
        "--clip_percentile",
        type=float,
        default=99.9,
        help="Percentile for INT8 clipping (default: 99.9)",
    )
    parser.add_argument(
        "--calib_file",
        type=str,
        default=None,
        help="Calibration JSON for int8_ours (default: artifacts/kv_calib_kl.json)",
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
        "--group_size",
        type=int,
        default=128,
        help="Group size for INT8 quantization (default: 128)",
    )
    parser.add_argument(
        "--gen_len",
        type=int,
        default=128,
        help="Number of tokens to generate (default: 128)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Custom prompt (overrides --seq_len)",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="HuggingFace model ID",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Number of warmup runs to eliminate JIT compilation effects (default: 3)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of profiling runs (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed (default: 1234)",
    )
    parser.add_argument(
        "--no_save",
        action="store_true",
        help="Don't save CSV output",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="results/runs",
        help="Output directory for CSV (default: results/runs)",
    )
    args = parser.parse_args()

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

    print("=" * 60)
    print("PROFILE BASELINE: Generation Loop")
    print(f"KV Mode: {args.kv_mode}")
    print("=" * 60)

    # Step 1: Import dependencies
    print("\n[1/5] Importing dependencies...")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"  ✓ torch {torch.__version__}")
        print(f"  ✓ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("  Please run: pip install -r requirements.txt")
        sys.exit(1)

    # Import our custom modules
    try:
        from src.engine.generate_loop import generate, GenerationOutput
        from src.utils.timing import reset_gpu_memory_stats
        from src.utils.hf import resolve_pretrained_path
        from src.utils.repro import (
            build_config_snapshot,
            get_hardware_info,
            set_seed,
            write_config_snapshot,
        )

        print("  ✓ Custom generation loop imported")
    except ImportError as e:
        print(f"  ✗ Failed to import project modules: {e}")
        print("  Make sure you're running from the project root.")
        sys.exit(1)

    # Check CUDA
    if not torch.cuda.is_available():
        print("\n⚠️  WARNING: CUDA is not available!")
        print("  This script requires a GPU to run.")
        sys.exit(0)

    # Set seeds for reproducibility
    set_seed(seed=args.seed, deterministic=True)

    # Step 2: Load model and tokenizer
    print(f"\n[2/5] Loading model: {args.model_id}...")
    try:
        model_path = resolve_pretrained_path(args.model_id)
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
        )
        print("  ✓ Tokenizer loaded")

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        print("  ✓ Model loaded")
        print(f"  ✓ Model dtype: {model.dtype}")
    except Exception as e:
        print(f"  ✗ Model loading failed: {e}")
        sys.exit(1)

    # Step 3: Prepare prompt
    print("\n[3/5] Preparing prompt...")
    if args.prompt:
        prompt = args.prompt
        prompt_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))
        print(f"  Using custom prompt ({prompt_tokens} tokens)")
    else:
        prompt = generate_prompt(args.seq_len, tokenizer)
        prompt_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))
        print(f"  Generated prompt with ~{prompt_tokens} tokens")

    print(f"  Prompt preview: {prompt[:80]}...")

    # Step 4: Warmup
    if args.warmup > 0:
        print(f"\n[4/5] Warmup ({args.warmup} runs)...")
        for i in range(args.warmup):
            _ = generate(
                model=model,
                tokenizer=tokenizer,
                prompt="Hello",
                max_new_tokens=8,
                kv_mode=args.kv_mode,
                group_size=args.group_size,
                clip_percentile=args.clip_percentile,
                calib_file=args.calib_file,
                use_attn_temperature=args.use_attn_temperature,
                seed=args.seed,
            )
            print(f"  Warmup {i+1}/{args.warmup} complete")

    # Step 5: Profile runs
    print(f"\n[5/5] Profiling ({args.runs} runs)...")
    results = []
    git_commit = get_git_commit()
    timestamp = datetime.now().isoformat()
    hardware = get_hardware_info()

    for run_idx in range(args.runs):
        print(f"\n  Run {run_idx + 1}/{args.runs}...")
        
        # Aggressive memory cleanup before run
        import gc
        gc.collect()
        torch.cuda.empty_cache()
        reset_gpu_memory_stats()

        try:
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                max_new_tokens=args.gen_len,
                kv_mode=args.kv_mode,
                group_size=args.group_size,
                clip_percentile=args.clip_percentile,
                calib_file=args.calib_file,
                use_attn_temperature=args.use_attn_temperature,
                seed=args.seed,
            )

            result = {
                "run_id": f"profile_{args.kv_mode}_{timestamp}_{run_idx}",
                "model_id": args.model_id,
                "kv_mode": args.kv_mode,
                "quant_bits": 4 if "int4" in args.kv_mode else (8 if "int8" in args.kv_mode else 16),
                "clip_percentile": args.clip_percentile,
                "group_size": args.group_size,
                "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
                "seq_len": output.prompt_len,
                "gen_len": output.gen_len,
                "ttft_ms": round(output.ttft_ms, 2),
                "tpot_ms": round(output.tpot_ms, 2),
                "tok_per_s": round(output.tok_per_s, 2),
                "gpu_mem_peak_mb": round(output.gpu_mem_peak_mb, 2),
                "timestamp": timestamp,
                "git_commit": git_commit,
            }
            results.append(result)

            run_dir = Path(args.out_dir)
            if not run_dir.is_absolute():
                run_dir = project_root / run_dir
            run_snapshot_dir = run_dir / result["run_id"]
            snapshot = build_config_snapshot(
                script_name=Path(__file__).name,
                args=args,
            )
            write_config_snapshot(str(run_snapshot_dir), snapshot)

            print(f"    TTFT: {output.ttft_ms:.2f} ms")
            print(f"    TPOT: {output.tpot_ms:.2f} ms")
            print(f"    Throughput: {output.tok_per_s:.2f} tok/s")
            print(f"    Peak Memory: {output.gpu_mem_peak_mb:.2f} MB")
            print(f"    Generated: {output.gen_len} tokens")

        except torch.cuda.OutOfMemoryError as e:
            print("    ✗ Out of GPU memory!")
            print(f"    Error: {e}")
            print(f"    Current settings: seq_len={args.seq_len}, gen_len={args.gen_len}")
            print("    Suggestions:")
            print(f"      - Reduce --seq_len (try --seq_len {args.seq_len // 2})")
            print(f"      - Reduce --gen_len (try --gen_len {args.gen_len // 2})")
            print("      - Run: torch.cuda.empty_cache() before retrying")
            sys.exit(1)
        except Exception as e:
            print(f"    ✗ Generation failed: {e}")
            sys.exit(1)

    # Output results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    if len(results) > 1:
        avg_ttft = sum(r["ttft_ms"] for r in results) / len(results)
        avg_tpot = sum(r["tpot_ms"] for r in results) / len(results)
        avg_tps = sum(r["tok_per_s"] for r in results) / len(results)
        print(f"Average TTFT: {avg_ttft:.2f} ms")
        print(f"Average TPOT: {avg_tpot:.2f} ms")
        print(f"Average Throughput: {avg_tps:.2f} tok/s")
    else:
        r = results[0]
        print(f"TTFT: {r['ttft_ms']:.2f} ms")
        print(f"TPOT: {r['tpot_ms']:.2f} ms")
        print(f"Throughput: {r['tok_per_s']:.2f} tok/s")
        print(f"Peak Memory: {r['gpu_mem_peak_mb']:.2f} MB")

    # Save CSV
    if not args.no_save:
        runs_dir = Path(args.out_dir)
        if not runs_dir.is_absolute():
            runs_dir = project_root / runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)

        csv_filename = f"profile_{args.kv_mode}_{timestamp.replace(':', '-')}.csv"
        csv_path = runs_dir / csv_filename

        fieldnames = [
            "run_id", "model_id", "kv_mode", "quant_bits", "clip_percentile",
            "group_size", "hardware", "seq_len", "gen_len", "ttft_ms", "tpot_ms",
            "tok_per_s", "gpu_mem_peak_mb", "timestamp", "git_commit"
        ]

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✓ Results saved to {csv_path}")

    print("\n✓ PROFILE COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
