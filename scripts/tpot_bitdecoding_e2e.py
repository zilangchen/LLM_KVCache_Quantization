#!/usr/bin/env python3
"""End-to-end TPOT measurement with BitDecoding INT4 attention.

Implements a manual decode loop where every layer's attention is computed
by BitDecoding's fwd_kvcache_int kernel. FFN, projections, norms are
standard PyTorch. This gives a real, measured TPOT comparable to our
FP16 and INT4-RA torch_ref numbers.

NOTE: BitDecoding uses its own per-token quantization, NOT our KL
calibration. This is a system-level comparison.

Usage:
    CUDA_VISIBLE_DEVICES=0 python3 scripts/tpot_bitdecoding_e2e.py
    CUDA_VISIBLE_DEVICES=0 python3 scripts/tpot_bitdecoding_e2e.py --seq_len 1024 --gen_len 32
"""
import sys
import os
import time
import argparse
import json

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bit_decode import fwd_kvcache_int, kvcache_pack_int
except ImportError:
    print("ERROR: bit_decode not installed. Run on GPU server.")
    sys.exit(2)

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.models.qwen2.modeling_qwen2 import apply_rotary_pos_emb

# ─── Defaults ───
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
SEQ_LEN = 4096
GEN_LEN = 64
WARMUP = 2
RUNS = 5
SEED = 1234


class BitDecodingKVCache:
    """Manages packed INT4 KV cache in BitDecoding format for all layers."""

    def __init__(self, num_layers, num_kv_heads, head_dim, device):
        self.num_layers = num_layers
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.pack_dim = head_dim // 8
        self.device = device
        self.seq_len = 0

        # Per-layer packed caches — initialized on first append
        self.k_packs = [None] * num_layers
        self.v_packs = [None] * num_layers
        self.k_params = [None] * num_layers
        self.v_params = [None] * num_layers

    def pack_and_store(self, layer_idx, k_fp16, v_fp16):
        """Pack FP16 K/V into BitDecoding INT4 format and store.

        Args:
            k_fp16: [B, H_kv, S_new, D] float16
            v_fp16: [B, H_kv, S_new, D] float16
        """
        # Transpose to BitDecoding layout: [B, S, H, D]
        k_bshd = k_fp16.transpose(1, 2).contiguous()
        v_bshd = v_fp16.transpose(1, 2).contiguous()

        B, S_new, H, D = k_bshd.shape

        k_pack = torch.zeros(B, S_new, H, self.pack_dim,
                             device=self.device, dtype=torch.int32)
        v_pack = torch.zeros(B, S_new, H, self.pack_dim,
                             device=self.device, dtype=torch.int32)
        k_par = torch.zeros(B, S_new, H, 2,
                            device=self.device, dtype=torch.float16)
        v_par = torch.zeros(B, S_new, H, 2,
                            device=self.device, dtype=torch.float16)

        cu_seqlens = torch.tensor([0, S_new], device=self.device, dtype=torch.int32)

        kvcache_pack_int(
            k_bshd, k_pack, k_par,
            v_bshd, v_pack, v_par,
            cu_seqlens_k=cu_seqlens,
            seqlen_k=S_new,
            quant_mode="k-channel",
            group_size=self.head_dim,
            num_bits=4,
        )

        if self.k_packs[layer_idx] is None:
            # First call (prefill)
            self.k_packs[layer_idx] = k_pack
            self.v_packs[layer_idx] = v_pack
            self.k_params[layer_idx] = k_par
            self.v_params[layer_idx] = v_par
        else:
            # Append (decode) — concatenate along sequence dimension
            self.k_packs[layer_idx] = torch.cat(
                [self.k_packs[layer_idx], k_pack], dim=1)
            self.v_packs[layer_idx] = torch.cat(
                [self.v_packs[layer_idx], v_pack], dim=1)
            self.k_params[layer_idx] = torch.cat(
                [self.k_params[layer_idx], k_par], dim=1)
            self.v_params[layer_idx] = torch.cat(
                [self.v_params[layer_idx], v_par], dim=1)

    def get_cache(self, layer_idx):
        """Return (k_pack, k_params, v_pack, v_params) for a layer."""
        return (self.k_packs[layer_idx], self.k_params[layer_idx],
                self.v_packs[layer_idx], self.v_params[layer_idx])


def manual_decode_step(model, token_ids, position_ids, bd_cache, sm_scale):
    """Run one decode step through all layers with BitDecoding attention.

    Args:
        model: HuggingFace Qwen2 model
        token_ids: [B, 1] current token
        position_ids: [B, 1] position of current token
        bd_cache: BitDecodingKVCache
        sm_scale: softmax scale

    Returns:
        logits: [B, vocab_size]
    """
    layers = model.model.layers
    num_layers = len(layers)
    num_q_heads = model.config.num_attention_heads
    num_kv_heads = model.config.num_key_value_heads
    head_dim = model.config.hidden_size // num_q_heads

    # Embedding
    hidden_states = model.model.embed_tokens(token_ids)  # [B, 1, hidden_size]

    for i, layer in enumerate(layers):
        residual = hidden_states

        # Input LayerNorm
        hidden_states = layer.input_layernorm(hidden_states)

        # Q/K/V projections
        bsz, q_len, _ = hidden_states.shape
        q = layer.self_attn.q_proj(hidden_states)
        k = layer.self_attn.k_proj(hidden_states)
        v = layer.self_attn.v_proj(hidden_states)

        # Reshape: [B, 1, num_heads, head_dim] → [B, num_heads, 1, head_dim]
        q = q.view(bsz, q_len, num_q_heads, head_dim).transpose(1, 2)
        k = k.view(bsz, q_len, num_kv_heads, head_dim).transpose(1, 2)
        v = v.view(bsz, q_len, num_kv_heads, head_dim).transpose(1, 2)

        # RoPE
        cos, sin = layer.self_attn.rotary_emb(v, position_ids)
        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        # Pack new K/V token and append to BitDecoding cache
        bd_cache.pack_and_store(i, k.half(), v.half())

        # Get full packed cache for this layer
        k_pack, k_params, v_pack, v_params = bd_cache.get_cache(i)

        # BitDecoding attention: q needs [B, 1, Hq, D] layout
        q_bd = q.transpose(1, 2).contiguous().half()  # [B, 1, Hq, D]

        attn_out = fwd_kvcache_int(
            q_bd, k_pack, k_params, v_pack, v_params,
            softmax_scale=sm_scale,
            quant_mode="k-channel",
            group_size=head_dim,
            num_bits=4,
        )
        # attn_out: [B, 1, Hq, D] → reshape to [B, 1, hidden_size]
        attn_out = attn_out.reshape(bsz, q_len, num_q_heads * head_dim)

        # O projection
        attn_out = layer.self_attn.o_proj(attn_out)

        # Residual + Post-attention LayerNorm
        hidden_states = residual + attn_out
        residual = hidden_states
        hidden_states = layer.post_attention_layernorm(hidden_states)

        # FFN (MLP)
        hidden_states = layer.mlp(hidden_states)
        hidden_states = residual + hidden_states

    # Final LayerNorm
    hidden_states = model.model.norm(hidden_states)

    # LM Head
    logits = model.lm_head(hidden_states)  # [B, 1, vocab_size]
    return logits[:, -1, :]  # [B, vocab_size]


def prefill_and_pack(model, input_ids, bd_cache):
    """Run prefill with standard model, then pack KV into BitDecoding format.

    Returns:
        next_token: [B, 1] first generated token
        position: int, next position index
    """
    with torch.no_grad():
        outputs = model(input_ids, use_cache=True, return_dict=True)

    past_kv = outputs.past_key_values
    num_layers = len(past_kv)

    for i in range(num_layers):
        k_layer = past_kv[i][0]  # [B, H, S, D]
        v_layer = past_kv[i][1]
        bd_cache.pack_and_store(i, k_layer.half(), v_layer.half())

    next_token = outputs.logits[:, -1, :].argmax(dim=-1, keepdim=True)
    position = input_ids.shape[1]  # next position

    return next_token, position


def measure_tpot_bitdecoding_e2e(model, input_ids, gen_len, warmup, runs):
    """Measure end-to-end TPOT with BitDecoding for attention."""
    config = model.config
    num_layers = config.num_hidden_layers
    num_kv_heads = config.num_key_value_heads
    num_q_heads = config.num_attention_heads
    head_dim = config.hidden_size // num_q_heads
    sm_scale = 1.0 / (head_dim ** 0.5)
    device = next(model.parameters()).device

    tpots = []

    for trial in range(warmup + runs):
        # Fresh cache each trial
        bd_cache = BitDecodingKVCache(
            num_layers=num_layers,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            device=device,
        )

        # Prefill
        with torch.no_grad():
            next_token, position = prefill_and_pack(model, input_ids, bd_cache)

        # Decode loop with timing
        torch.cuda.synchronize()
        t0 = time.perf_counter()

        with torch.no_grad():
            for step in range(gen_len):
                pos_ids = torch.tensor([[position + step]],
                                       device=device, dtype=torch.long)
                logits = manual_decode_step(
                    model, next_token, pos_ids, bd_cache, sm_scale
                )
                next_token = logits.argmax(dim=-1, keepdim=True)

        torch.cuda.synchronize()
        t1 = time.perf_counter()

        tpot = (t1 - t0) / gen_len * 1000  # ms per token

        if trial >= warmup:
            tpots.append(tpot)
            print(f"  Run {trial - warmup + 1}/{runs}: {tpot:.2f} ms/token")

        # Free cache memory
        del bd_cache
        torch.cuda.empty_cache()

    return tpots


def measure_tpot_fp16(model, input_ids, gen_len, warmup, runs):
    """FP16 baseline TPOT for comparison."""
    tpots = []
    for i in range(warmup + runs):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(
                input_ids, max_new_tokens=gen_len,
                do_sample=False, use_cache=True,
            )
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        actual_gen = out.shape[1] - input_ids.shape[1]
        if i >= warmup and actual_gen > 0:
            tpots.append((t1 - t0) / actual_gen * 1000)
    return tpots


def main():
    parser = argparse.ArgumentParser(
        description="BitDecoding end-to-end TPOT benchmark")
    parser.add_argument("--model_id", type=str, default=MODEL_ID)
    parser.add_argument("--seq_len", type=int, default=SEQ_LEN)
    parser.add_argument("--gen_len", type=int, default=GEN_LEN)
    parser.add_argument("--warmup", type=int, default=WARMUP)
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out_dir", type=str,
                        default="results/emnlp_defense_v1/runs/tpot_bitdecoding_e2e_1p5b")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto"
    )
    model.eval()

    config = model.config
    print(f"  Layers={config.num_hidden_layers}, Hq={config.num_attention_heads}, "
          f"Hkv={config.num_key_value_heads}, D={config.hidden_size // config.num_attention_heads}")

    # Build input
    text = "Hello " * (args.seq_len // 2)
    input_ids = tokenizer(text, return_tensors="pt").input_ids[:, :args.seq_len]
    input_ids = input_ids.to(next(model.parameters()).device)
    print(f"Input shape: {input_ids.shape}")

    # 1. FP16 baseline
    print(f"\n=== FP16 TPOT (warmup={args.warmup}, runs={args.runs}) ===")
    fp16_tpots = measure_tpot_fp16(model, input_ids, args.gen_len, args.warmup, args.runs)
    fp16_mean = sum(fp16_tpots) / len(fp16_tpots)
    fp16_std = (sum((t - fp16_mean)**2 for t in fp16_tpots) / len(fp16_tpots)) ** 0.5
    print(f"FP16 TPOT: {fp16_mean:.2f} ± {fp16_std:.2f} ms")

    # 2. BitDecoding end-to-end
    print(f"\n=== BitDecoding E2E TPOT (warmup={args.warmup}, runs={args.runs}) ===")
    bd_tpots = measure_tpot_bitdecoding_e2e(
        model, input_ids, args.gen_len, args.warmup, args.runs)
    bd_mean = sum(bd_tpots) / len(bd_tpots)
    bd_std = (sum((t - bd_mean)**2 for t in bd_tpots) / len(bd_tpots)) ** 0.5
    print(f"BitDecoding E2E TPOT: {bd_mean:.2f} ± {bd_std:.2f} ms")

    # 3. Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY (model={args.model_id}, seq_len={args.seq_len}, gen_len={args.gen_len})")
    print(f"{'='*60}")
    print(f"  FP16 (end-to-end):              {fp16_mean:.2f} ± {fp16_std:.2f} ms/token")
    print(f"  BitDecoding (end-to-end):        {bd_mean:.2f} ± {bd_std:.2f} ms/token")
    print(f"  BD speedup vs FP16:              {fp16_mean/bd_mean:.2f}×")
    print(f"  INT4-RA torch_ref (from prev):   ~86 ms/token (reference)")
    print(f"  INT4-RA Triton v1 (from prev):   ~54 ms/token (reference)")
    print()
    print(f"  NOTE: BitDecoding uses its own per-token quantization.")
    print(f"  INT4-RA uses our per-channel KL calibration.")
    print(f"  This is a system-level comparison, not same-quant kernel swap.")

    # Save
    result = {
        "model": args.model_id,
        "seq_len": args.seq_len,
        "gen_len": args.gen_len,
        "warmup": args.warmup,
        "runs": args.runs,
        "fp16_tpot_ms": round(fp16_mean, 3),
        "fp16_tpot_std_ms": round(fp16_std, 3),
        "bitdecoding_e2e_tpot_ms": round(bd_mean, 3),
        "bitdecoding_e2e_tpot_std_ms": round(bd_std, 3),
        "speedup_vs_fp16": round(fp16_mean / bd_mean, 3),
        "fp16_tpots_raw": [round(t, 3) for t in fp16_tpots],
        "bd_tpots_raw": [round(t, 3) for t in bd_tpots],
        "note": "BitDecoding uses per-token quantization (not our KL calibration). "
                "System-level comparison, not same-quant kernel swap.",
    }
    out_path = os.path.join(args.out_dir, "tpot_e2e_summary.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
