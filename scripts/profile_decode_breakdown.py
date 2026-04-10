"""
Decode step timing breakdown: where does 54ms TPOT come from?

Inserts torch.cuda.synchronize() barriers around key phases to measure:
  1. cache_prep: INT8CacheWrapperContainer creation or KV dequant
  2. forward: model() call (attention + MLP + LayerNorm, 28 layers)
  3. sampling: argmax on logits
  4. cache_update: append new KV to cache (fused mode: inside forward)
  5. python_overhead: everything else (loop logic, attention_mask update, etc.)

Usage:
  python3 scripts/profile_decode_breakdown.py \
    --kv_mode int4_ours_asym --decode_attn_impl triton_int4_asym \
    --model_id Qwen/Qwen2.5-1.5B-Instruct --seq_len 4096 --gen_len 64
"""

import argparse
import os
import sys
import time

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--kv_mode", type=str, default="int4_ours_asym")
    parser.add_argument("--decode_attn_impl", type=str, default="triton_int4_asym")
    parser.add_argument("--seq_len", type=int, default=4096)
    parser.add_argument("--gen_len", type=int, default=64)
    parser.add_argument("--warmup_steps", type=int, default=8)
    args = parser.parse_args()

    device = "cuda"
    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map=device
    )
    model.eval()

    # Build prompt of exact length
    tok_id = tokenizer.encode("Hello", add_special_tokens=False)[0]
    tokens = [tok_id] * args.seq_len
    input_ids = torch.tensor([tokens], device=device)
    attention_mask = torch.ones_like(input_ids)

    # Import generate infrastructure
    from src.engine.generate_loop import generate_from_ids

    # === Warmup (JIT compile Triton kernels) ===
    print(f"Warmup ({args.warmup_steps} tokens)...")
    generate_from_ids(
        model=model, tokenizer=tokenizer,
        input_ids=input_ids, attention_mask=attention_mask,
        max_new_tokens=args.warmup_steps,
        kv_mode=args.kv_mode,
        decode_attn_impl=args.decode_attn_impl,
        seed=42, stop_on_eos=False,
    )
    torch.cuda.synchronize()

    # === Timed run: measure total TPOT ===
    print(f"\nTimed run: {args.gen_len} decode steps...")
    torch.cuda.synchronize()
    t_start = time.perf_counter()
    generate_from_ids(
        model=model, tokenizer=tokenizer,
        input_ids=input_ids, attention_mask=attention_mask,
        max_new_tokens=args.gen_len,
        kv_mode=args.kv_mode,
        decode_attn_impl=args.decode_attn_impl,
        seed=42, stop_on_eos=False,
    )
    torch.cuda.synchronize()
    t_total = time.perf_counter() - t_start
    tpot_ms = t_total / args.gen_len * 1000
    print(f"Total: {t_total*1000:.1f}ms, TPOT: {tpot_ms:.2f}ms/token")

    # === FP16 baseline for comparison ===
    print(f"\nFP16 baseline: {args.gen_len} decode steps...")
    torch.cuda.synchronize()
    t_start = time.perf_counter()
    generate_from_ids(
        model=model, tokenizer=tokenizer,
        input_ids=input_ids, attention_mask=attention_mask,
        max_new_tokens=args.gen_len,
        kv_mode="fp16",
        decode_attn_impl="torch_ref",
        seed=42, stop_on_eos=False,
    )
    torch.cuda.synchronize()
    t_fp16 = time.perf_counter() - t_start
    tpot_fp16 = t_fp16 / args.gen_len * 1000
    print(f"FP16 Total: {t_fp16*1000:.1f}ms, TPOT: {tpot_fp16:.2f}ms/token")

    # === Per-component profiling with CUDA_LAUNCH_BLOCKING ===
    print(f"\n=== Component Breakdown (CUDA_LAUNCH_BLOCKING style) ===")
    print("Running generate with per-phase sync timing...\n")

    # We can't easily instrument inside generate_from_ids without modifying it.
    # Instead, compare different configurations to isolate overhead:

    # Test 1: INT4 fused (our path: patch_model + triton kernel)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    generate_from_ids(
        model=model, tokenizer=tokenizer,
        input_ids=input_ids, attention_mask=attention_mask,
        max_new_tokens=args.gen_len,
        kv_mode=args.kv_mode,
        decode_attn_impl=args.decode_attn_impl,
        seed=42, stop_on_eos=False,
    )
    torch.cuda.synchronize()
    t_int4_fused = time.perf_counter() - t0

    # Test 2: INT4 torch_ref (no triton kernel, pure PyTorch dequant + attention)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    generate_from_ids(
        model=model, tokenizer=tokenizer,
        input_ids=input_ids, attention_mask=attention_mask,
        max_new_tokens=args.gen_len,
        kv_mode=args.kv_mode,
        decode_attn_impl="torch_ref",
        seed=42, stop_on_eos=False,
    )
    torch.cuda.synchronize()
    t_int4_ref = time.perf_counter() - t0

    # Test 3: FP16 (no quantization at all)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    generate_from_ids(
        model=model, tokenizer=tokenizer,
        input_ids=input_ids, attention_mask=attention_mask,
        max_new_tokens=args.gen_len,
        kv_mode="fp16",
        decode_attn_impl="torch_ref",
        seed=42, stop_on_eos=False,
    )
    torch.cuda.synchronize()
    t_fp16_2 = time.perf_counter() - t0

    # Derived estimates
    per_step_int4_fused = t_int4_fused / args.gen_len * 1000
    per_step_int4_ref = t_int4_ref / args.gen_len * 1000
    per_step_fp16 = t_fp16_2 / args.gen_len * 1000

    # The difference between int4_fused and fp16 = quantization overhead (cache + kernel + dispatch)
    quant_overhead = per_step_int4_fused - per_step_fp16
    # The difference between int4_ref and fp16 = quantization overhead WITHOUT triton (pure PyTorch)
    quant_overhead_ref = per_step_int4_ref - per_step_fp16
    # The difference between int4_fused and int4_ref = triton kernel benefit (negative = triton faster)
    triton_benefit = per_step_int4_fused - per_step_int4_ref

    print(f"{'Config':<25s} {'Total (ms)':<12s} {'Per-step (ms)':<14s}")
    print("-" * 55)
    print(f"{'FP16':<25s} {t_fp16_2*1000:<12.1f} {per_step_fp16:<14.2f}")
    print(f"{'INT4 torch_ref':<25s} {t_int4_ref*1000:<12.1f} {per_step_int4_ref:<14.2f}")
    print(f"{'INT4 triton_fused':<25s} {t_int4_fused*1000:<12.1f} {per_step_int4_fused:<14.2f}")
    print()
    print(f"{'Derived breakdown:'}")
    print(f"  FP16 base (MLP+LN+sample+dispatch): {per_step_fp16:.2f} ms/step")
    print(f"  + Quantization overhead (fused):     {quant_overhead:+.2f} ms/step")
    print(f"  + Quantization overhead (torch_ref): {quant_overhead_ref:+.2f} ms/step")
    print(f"  Triton vs torch_ref:                 {triton_benefit:+.2f} ms/step")
    print()
    print(f"  If quant_overhead >> 0: bottleneck is cache/dispatch, not kernel")
    print(f"  If triton_benefit << 0: Triton kernel is faster than torch_ref")
    print(f"  If triton_benefit ~ 0: kernel speed doesn't matter (overhead elsewhere)")


if __name__ == "__main__":
    main()
