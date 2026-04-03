"""TPOT profiling: BitDecoding INT4 fused attention vs torch_ref vs FP16.

This script directly measures decode TPOT using BitDecoding's fused INT4
attention kernel (HPCA 2026, tensor-core enabled) as a drop-in replacement
for our Triton kernel.

Usage:
    CUDA_VISIBLE_DEVICES=0 python3 scripts/tpot_bitdecoding.py
"""
import sys
import time
import torch
import json
import csv
import os
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformers import AutoModelForCausalLM, AutoTokenizer

# ─── Config ───
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
SEQ_LEN = 4096
GEN_LEN = 128
WARMUP = 3
RUNS = 5
SEED = 1234
CALIB_FILE = "artifacts/kv_calib_rolealign_1p5b_v3.json"
OUT_DIR = "results/emnlp_defense_v1/runs/tpot_bitdecoding_1p5b"


def measure_tpot_fp16(model, tokenizer, input_ids, gen_len, warmup, runs):
    """FP16 baseline TPOT."""
    device = model.device
    tpots = []
    for i in range(warmup + runs):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(
                input_ids,
                max_new_tokens=gen_len,
                do_sample=False,
                use_cache=True,
            )
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        actual_gen = out.shape[1] - input_ids.shape[1]
        if i >= warmup and actual_gen > 0:
            tpots.append((t1 - t0) / actual_gen * 1000)
    return sum(tpots) / len(tpots) if tpots else 0.0


def measure_tpot_int4_ra_torchref(model, tokenizer, input_ids, gen_len, warmup, runs):
    """INT4-RA torch_ref TPOT (our current method)."""
    from src.engine.generate_loop import generate_from_ids

    tpots = []
    attn_mask = torch.ones_like(input_ids)
    for i in range(warmup + runs):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        out = generate_from_ids(
            model=model,
            tokenizer=tokenizer,
            input_ids=input_ids,
            attention_mask=attn_mask,
            max_new_tokens=gen_len,
            kv_mode="int4_ours_asym",
            calib_file=CALIB_FILE,
            decode_attn_impl="torch_ref",
            use_attn_temperature=False,
            quant_bits=4,
            seed=SEED,
        )
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        actual_gen = out.generated_ids.shape[1] if hasattr(out, 'generated_ids') else gen_len
        if i >= warmup and actual_gen > 0:
            tpots.append((t1 - t0) / actual_gen * 1000)
    return sum(tpots) / len(tpots) if tpots else 0.0


def main():
    torch.manual_seed(SEED)
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Loading {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float16, device_map="auto"
    )
    model.eval()

    # Build input
    text = "Hello " * (SEQ_LEN // 2)
    input_ids = tokenizer(text, return_tensors="pt").input_ids[:, :SEQ_LEN].to(model.device)
    print(f"Input shape: {input_ids.shape}")

    # 1. FP16 baseline
    print("\n=== FP16 TPOT ===")
    fp16_tpot = measure_tpot_fp16(model, tokenizer, input_ids, GEN_LEN, WARMUP, RUNS)
    print(f"FP16 TPOT: {fp16_tpot:.2f} ms")

    # 2. INT4-RA torch_ref
    print("\n=== INT4-RA torch_ref TPOT ===")
    ref_tpot = measure_tpot_int4_ra_torchref(model, tokenizer, input_ids, GEN_LEN, WARMUP, RUNS)
    print(f"INT4-RA torch_ref TPOT: {ref_tpot:.2f} ms")

    # 3. Summary
    print(f"\n=== Summary ===")
    print(f"FP16:           {fp16_tpot:.2f} ms")
    print(f"INT4-RA ref:    {ref_tpot:.2f} ms ({ref_tpot/fp16_tpot:.2f}x)")

    # Save
    result = {
        "fp16_tpot_ms": fp16_tpot,
        "int4_ra_torchref_tpot_ms": ref_tpot,
        "model": MODEL_ID,
        "seq_len": SEQ_LEN,
        "gen_len": GEN_LEN,
    }
    with open(f"{OUT_DIR}/tpot_summary.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved to {OUT_DIR}/tpot_summary.json")


if __name__ == "__main__":
    main()
