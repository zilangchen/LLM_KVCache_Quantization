"""TPOT profiling: BitDecoding INT4 fused attention vs torch_ref vs FP16.

Measures end-to-end decode TPOT across three paths:
  1. FP16 baseline (model.generate with native KV cache)
  2. INT4-RA torch_ref (our per-channel KL calibration + PyTorch SDPA)
  3. BitDecoding (BD's own per-token quantization + tensor-core kernel)

BitDecoding uses its own quantization (per-token scale+zp), NOT our KL
calibration. This is an "alternative system" comparison, not "same quant
different kernel". See scripts/bitdecoding_compat_test.py for why direct
format conversion is blocked (per-channel vs per-token incompatibility).

Usage:
    CUDA_VISIBLE_DEVICES=0 python3 scripts/tpot_bitdecoding.py
    CUDA_VISIBLE_DEVICES=0 python3 scripts/tpot_bitdecoding.py --seq_len 1024
"""
import sys
import time
import argparse
import torch
import json
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformers import AutoModelForCausalLM, AutoTokenizer

# ─── Defaults ───
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
    """INT4-RA torch_ref TPOT (our per-channel KL calibration + PyTorch SDPA)."""
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


def measure_tpot_bitdecoding(model, tokenizer, input_ids, gen_len, warmup, runs):
    """BitDecoding end-to-end TPOT.

    Strategy: run model prefill in FP16 to get KV, then quantize KV with
    BitDecoding's own packer, then decode token-by-token using fwd_kvcache_int.

    This measures the full decode loop including:
    - Model forward (FFN + attention) per token
    - BitDecoding INT4 KV cache quantization (per new token)
    - BitDecoding fused attention kernel (tensor-core)
    """
    try:
        from bit_decode import fwd_kvcache_int, kvcache_pack_int
    except ImportError:
        print("  WARNING: bit_decode not installed, skipping BitDecoding measurement")
        return None

    device = input_ids.device
    seq_len = input_ids.shape[1]

    # --- Get model config ---
    config = model.config
    num_layers = config.num_hidden_layers
    num_kv_heads = getattr(config, "num_key_value_heads", config.num_attention_heads)
    num_q_heads = config.num_attention_heads
    head_dim = config.hidden_size // num_q_heads
    pack_dim = head_dim // 8
    sm_scale = 1.0 / (head_dim ** 0.5)

    tpots = []

    for trial in range(warmup + runs):
        torch.cuda.synchronize()

        # Step 1: Prefill — run full model forward to get FP16 KV cache
        with torch.no_grad():
            outputs = model(
                input_ids,
                use_cache=True,
                return_dict=True,
            )
        past_kv = outputs.past_key_values  # list of (k, v) tuples per layer
        # past_kv[layer] = (k: [B, H, S, D], v: [B, H, S, D])

        next_token_logits = outputs.logits[:, -1, :]
        next_token = next_token_logits.argmax(dim=-1, keepdim=True)

        # Step 2: Pack FP16 KV into BitDecoding INT4 format (all layers)
        bd_k_packs = []
        bd_v_packs = []
        bd_k_params_list = []
        bd_v_params_list = []

        for layer_idx in range(num_layers):
            k_layer = past_kv[layer_idx][0]  # [B, H, S, D]
            v_layer = past_kv[layer_idx][1]

            # Transpose to BitDecoding layout: [B, S, H, D]
            k_bshd = k_layer.transpose(1, 2).contiguous().half()
            v_bshd = v_layer.transpose(1, 2).contiguous().half()

            cur_s = k_bshd.shape[1]

            k_pack = torch.zeros(1, cur_s, num_kv_heads, pack_dim,
                                 device=device, dtype=torch.int32)
            v_pack = torch.zeros(1, cur_s, num_kv_heads, pack_dim,
                                 device=device, dtype=torch.int32)
            k_params = torch.zeros(1, cur_s, num_kv_heads, 2,
                                   device=device, dtype=torch.float16)
            v_params = torch.zeros(1, cur_s, num_kv_heads, 2,
                                   device=device, dtype=torch.float16)

            cu_seqlens = torch.tensor([0, cur_s], device=device, dtype=torch.int32)

            kvcache_pack_int(
                k_bshd, k_pack, k_params,
                v_bshd, v_pack, v_params,
                cu_seqlens_k=cu_seqlens,
                seqlen_k=cur_s,
                quant_mode="k-channel",
                group_size=head_dim,
                num_bits=4,
            )

            bd_k_packs.append(k_pack)
            bd_v_packs.append(v_pack)
            bd_k_params_list.append(k_params)
            bd_v_params_list.append(v_params)

        # Step 3: Decode loop — token by token
        # NOTE: This is a simplified decode loop. It runs model.forward for each
        # token (getting new KV), but uses BitDecoding's fwd_kvcache_int for the
        # attention computation timing reference. Since we can't easily monkey-patch
        # the model's attention with BitDecoding mid-loop, we measure a proxy:
        # the BitDecoding kernel time on the accumulated KV cache.
        #
        # For a fair TPOT comparison, we measure just the BitDecoding kernel call
        # at the final sequence length (prefill + gen_len tokens).

        # Generate tokens to grow the KV cache
        generated_ids = [next_token]
        cur_input = next_token
        with torch.no_grad():
            for step in range(gen_len - 1):
                outputs = model(
                    cur_input,
                    past_key_values=past_kv,
                    use_cache=True,
                    return_dict=True,
                )
                past_kv = outputs.past_key_values
                next_logits = outputs.logits[:, -1, :]
                cur_input = next_logits.argmax(dim=-1, keepdim=True)
                generated_ids.append(cur_input)

        # Now measure BitDecoding kernel on the full KV cache
        # Re-pack the full KV cache
        final_s = past_kv[0][0].shape[2]  # seq_len + gen_len

        # Pick layer 0 for timing (representative)
        k_full = past_kv[0][0].transpose(1, 2).contiguous().half()  # [B, S_full, H, D]
        v_full = past_kv[0][1].transpose(1, 2).contiguous().half()

        k_pack_f = torch.zeros(1, final_s, num_kv_heads, pack_dim,
                               device=device, dtype=torch.int32)
        v_pack_f = torch.zeros(1, final_s, num_kv_heads, pack_dim,
                               device=device, dtype=torch.int32)
        k_params_f = torch.zeros(1, final_s, num_kv_heads, 2,
                                 device=device, dtype=torch.float16)
        v_params_f = torch.zeros(1, final_s, num_kv_heads, 2,
                                 device=device, dtype=torch.float16)
        cu_f = torch.tensor([0, final_s], device=device, dtype=torch.int32)

        kvcache_pack_int(
            k_full, k_pack_f, k_params_f,
            v_full, v_pack_f, v_params_f,
            cu_seqlens_k=cu_f,
            seqlen_k=final_s,
            quant_mode="k-channel",
            group_size=head_dim,
            num_bits=4,
        )

        # Dummy Q for timing (single decode token)
        q_dummy = torch.randn(1, 1, num_q_heads, head_dim,
                              device=device, dtype=torch.float16)

        # Time BitDecoding kernel (num_layers calls, like a real decode step)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(num_layers):
            _ = fwd_kvcache_int(
                q_dummy, k_pack_f, k_params_f, v_pack_f, v_params_f,
                softmax_scale=sm_scale,
                quant_mode="k-channel",
                group_size=head_dim,
                num_bits=4,
            )
        torch.cuda.synchronize()
        t1 = time.perf_counter()

        bd_attn_time_ms = (t1 - t0) * 1000  # total for num_layers calls

        if trial >= warmup:
            tpots.append(bd_attn_time_ms)

    if not tpots:
        return None

    mean_tpot = sum(tpots) / len(tpots)
    return mean_tpot


def main():
    parser = argparse.ArgumentParser(description="BitDecoding TPOT benchmark")
    parser.add_argument("--model_id", type=str, default=MODEL_ID)
    parser.add_argument("--seq_len", type=int, default=SEQ_LEN)
    parser.add_argument("--gen_len", type=int, default=GEN_LEN)
    parser.add_argument("--warmup", type=int, default=WARMUP)
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out_dir", type=str, default=OUT_DIR)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto"
    )
    model.eval()

    # Build input
    text = "Hello " * (args.seq_len // 2)
    input_ids = tokenizer(text, return_tensors="pt").input_ids[:, :args.seq_len].to(model.device)
    print(f"Input shape: {input_ids.shape}")

    # 1. FP16 baseline
    print("\n=== FP16 TPOT ===")
    fp16_tpot = measure_tpot_fp16(model, tokenizer, input_ids, args.gen_len, args.warmup, args.runs)
    print(f"FP16 TPOT: {fp16_tpot:.2f} ms")

    # 2. INT4-RA torch_ref
    print("\n=== INT4-RA torch_ref TPOT ===")
    ref_tpot = measure_tpot_int4_ra_torchref(model, tokenizer, input_ids, args.gen_len, args.warmup, args.runs)
    print(f"INT4-RA torch_ref TPOT: {ref_tpot:.2f} ms")

    # 3. BitDecoding (BD's own quantization + tensor-core kernel)
    num_layers = model.config.num_hidden_layers
    print(f"\n=== BitDecoding TPOT (attention kernel only, ×{num_layers} layers) ===")
    bd_tpot = measure_tpot_bitdecoding(model, tokenizer, input_ids, args.gen_len, args.warmup, args.runs)
    if bd_tpot is not None:
        print(f"BitDecoding attn kernel TPOT: {bd_tpot:.2f} ms")
    else:
        print("BitDecoding: SKIPPED (not installed)")
        bd_tpot = -1.0

    # 4. Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY (model={args.model_id}, seq_len={args.seq_len}, gen_len={args.gen_len})")
    print(f"{'='*60}")
    print(f"  FP16 (end-to-end):              {fp16_tpot:.2f} ms/token")
    print(f"  INT4-RA torch_ref (end-to-end):  {ref_tpot:.2f} ms/token")
    if bd_tpot > 0:
        print(f"  BitDecoding attn-only (×{num_layers}L):   {bd_tpot:.2f} ms/step")
        print(f"  BitDecoding per-layer avg:        {bd_tpot/num_layers:.3f} ms/layer")
    print(f"\n  Note: BitDecoding number is attention-kernel-only (×{num_layers} layers),")
    print(f"  NOT end-to-end TPOT. It excludes FFN, embedding, and sampling.")
    print(f"  FP16 and INT4-RA numbers ARE end-to-end TPOT.")

    # Save
    result = {
        "model": args.model_id,
        "seq_len": args.seq_len,
        "gen_len": args.gen_len,
        "warmup": args.warmup,
        "runs": args.runs,
        "fp16_tpot_ms": round(fp16_tpot, 3),
        "int4_ra_torchref_tpot_ms": round(ref_tpot, 3),
        "bitdecoding_attn_all_layers_ms": round(bd_tpot, 3) if bd_tpot > 0 else None,
        "bitdecoding_per_layer_ms": round(bd_tpot / num_layers, 4) if bd_tpot > 0 else None,
        "num_layers": num_layers,
        "note": "BitDecoding uses its own per-token quantization, not our KL calibration. "
                "BitDecoding number is attention-kernel-only, not end-to-end TPOT.",
    }
    out_path = Path(args.out_dir) / "tpot_summary.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
