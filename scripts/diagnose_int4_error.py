#!/usr/bin/env python3
"""
Phase 0.2: Per-layer symmetric vs asymmetric INT4 quantization error diagnosis.

For each layer of the target model (default 1.5B):
1. Capture fp16 K and V tensors during a single prefill pass
2. Apply symmetric INT4 (qmax=7, per-group gs=32) quantize+dequantize
3. Apply asymmetric INT4 per-channel-K (KIVI-style) quantize+dequantize
4. Apply asymmetric INT4 per-token-V (KIVI-style) quantize+dequantize
5. Report per-layer MSE and SQNR, K and V separately

Usage (on GPU server):
    python scripts/diagnose_int4_error.py \
        --model_id Qwen/Qwen2.5-1.5B-Instruct \
        --seq_len 512 \
        --out_dir results/emnlp_postfix_v2/report
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import numpy as np

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.quant.int4_basic import quantize_symmetric_int4, dequantize_symmetric_int4
from src.quant.asymmetric_quant import (
    quantize_asymmetric_per_channel,
    dequantize_asymmetric_per_channel,
    quantize_asymmetric_per_token,
    dequantize_asymmetric_per_token,
)

logger = logging.getLogger(__name__)


def compute_mse(original: torch.Tensor, reconstructed: torch.Tensor) -> float:
    """Compute mean squared error."""
    return float(((original.float() - reconstructed.float()) ** 2).mean().item())


def compute_sqnr(original: torch.Tensor, reconstructed: torch.Tensor) -> float:
    """Compute signal-to-quantization-noise ratio in dB."""
    signal_power = float((original.float() ** 2).mean().item())
    noise_power = float(((original.float() - reconstructed.float()) ** 2).mean().item())
    if noise_power < 1e-20:
        return 100.0  # effectively perfect
    return float(10.0 * np.log10(signal_power / noise_power))


def symmetric_int4_roundtrip(tensor: torch.Tensor, group_size: int = 32) -> torch.Tensor:
    """Symmetric INT4 quantize + dequantize (per-group)."""
    q, scale = quantize_symmetric_int4(tensor, percentile=99.9, group_size=group_size)
    return dequantize_symmetric_int4(q, scale, group_size=group_size).to(tensor.dtype)


def asymmetric_int4_per_channel_roundtrip(tensor: torch.Tensor) -> torch.Tensor:
    """Asymmetric INT4 per-channel quantize + dequantize (for K, KIVI-style)."""
    q, scale, zp = quantize_asymmetric_per_channel(tensor, quant_bits=4)
    return dequantize_asymmetric_per_channel(q, scale, zp).to(tensor.dtype)


def asymmetric_int4_per_token_roundtrip(tensor: torch.Tensor) -> torch.Tensor:
    """Asymmetric INT4 per-token quantize + dequantize (for V, KIVI-style)."""
    q, scale, zp = quantize_asymmetric_per_token(tensor, quant_bits=4)
    return dequantize_asymmetric_per_token(q, scale, zp).to(tensor.dtype)


def capture_kv_tensors(
    model,
    tokenizer,
    text: str,
    max_length: int = 512,
) -> List[Tuple[torch.Tensor, torch.Tensor]]:
    """Run a single prefill pass and capture per-layer K and V tensors.

    Returns list of (k, v) tuples, one per layer. Shape: [1, num_kv_heads, seq_len, head_dim].
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    kv_pairs: List[Tuple[torch.Tensor, torch.Tensor]] = []
    hooks = []

    def make_hook(layer_idx):
        def hook_fn(module, args, output):
            # HF Transformers attention outputs: (attn_output, attn_weights, past_key_value)
            # past_key_value is a tuple (key_states, value_states)
            if isinstance(output, tuple) and len(output) >= 3:
                past_kv = output[2]
                if isinstance(past_kv, tuple) and len(past_kv) == 2:
                    k, v = past_kv[0].detach().clone(), past_kv[1].detach().clone()
                    while len(kv_pairs) <= layer_idx:
                        kv_pairs.append(None)
                    kv_pairs[layer_idx] = (k, v)
        return hook_fn

    # Register hooks on attention layers
    for i, layer in enumerate(model.model.layers):
        h = layer.self_attn.register_forward_hook(make_hook(i))
        hooks.append(h)

    with torch.no_grad():
        model(**inputs, use_cache=True)

    for h in hooks:
        h.remove()

    return [p for p in kv_pairs if p is not None]


def run_diagnosis(model, tokenizer, text: str, seq_len: int) -> List[Dict]:
    """Run per-layer diagnosis and return results."""
    print(f"Capturing KV tensors (seq_len={seq_len})...")
    kv_pairs = capture_kv_tensors(model, tokenizer, text, max_length=seq_len)
    num_layers = len(kv_pairs)
    print(f"Captured {num_layers} layers")

    results = []
    for i, (k, v) in enumerate(kv_pairs):
        # Ensure even head_dim for INT4 bit-packing
        head_dim = k.shape[-1]
        if head_dim % 2 != 0:
            logger.warning("Layer %d: odd head_dim=%d, skipping", i, head_dim)
            continue

        row = {"layer": i, "k_shape": list(k.shape), "v_shape": list(v.shape)}

        # --- K analysis ---
        k_sym_recon = symmetric_int4_roundtrip(k)
        k_asym_recon = asymmetric_int4_per_channel_roundtrip(k)

        row["k_sym_mse"] = compute_mse(k, k_sym_recon)
        row["k_sym_sqnr"] = compute_sqnr(k, k_sym_recon)
        row["k_asym_mse"] = compute_mse(k, k_asym_recon)
        row["k_asym_sqnr"] = compute_sqnr(k, k_asym_recon)
        row["k_sqnr_gain"] = row["k_asym_sqnr"] - row["k_sym_sqnr"]

        # --- V analysis ---
        v_sym_recon = symmetric_int4_roundtrip(v)
        v_asym_recon = asymmetric_int4_per_token_roundtrip(v)

        row["v_sym_mse"] = compute_mse(v, v_sym_recon)
        row["v_sym_sqnr"] = compute_sqnr(v, v_sym_recon)
        row["v_asym_mse"] = compute_mse(v, v_asym_recon)
        row["v_asym_sqnr"] = compute_sqnr(v, v_asym_recon)
        row["v_sqnr_gain"] = row["v_asym_sqnr"] - row["v_sym_sqnr"]

        results.append(row)

        # Free tensors
        del k_sym_recon, k_asym_recon, v_sym_recon, v_asym_recon

    return results


def print_results(results: List[Dict]) -> None:
    """Print per-layer results as a formatted table."""
    print("\n" + "=" * 110)
    print(f"{'Layer':>5} | {'K Sym SQNR':>10} {'K Asym SQNR':>12} {'K Gain':>8} | "
          f"{'V Sym SQNR':>10} {'V Asym SQNR':>12} {'V Gain':>8}")
    print("-" * 110)

    k_gains, v_gains = [], []
    for r in results:
        print(f"{r['layer']:5d} | {r['k_sym_sqnr']:10.2f} {r['k_asym_sqnr']:12.2f} "
              f"{r['k_sqnr_gain']:+8.2f} | {r['v_sym_sqnr']:10.2f} {r['v_asym_sqnr']:12.2f} "
              f"{r['v_sqnr_gain']:+8.2f}")
        k_gains.append(r["k_sqnr_gain"])
        v_gains.append(r["v_sqnr_gain"])

    print("-" * 110)
    print(f"{'MEAN':>5} | {'':>10} {'':>12} {np.mean(k_gains):+8.2f} | "
          f"{'':>10} {'':>12} {np.mean(v_gains):+8.2f}")
    print(f"\nAsymmetric SQNR advantage: K={np.mean(k_gains):+.2f} dB, V={np.mean(v_gains):+.2f} dB")

    gate_threshold = 5.0
    k_pass = np.mean(k_gains) >= gate_threshold
    v_pass = np.mean(v_gains) >= gate_threshold
    avg_pass = (np.mean(k_gains) + np.mean(v_gains)) / 2 >= gate_threshold
    print(f"\nPhase 0.2 Gate (≥{gate_threshold} dB avg gain):")
    print(f"  K-path: {np.mean(k_gains):.2f} dB → {'PASS' if k_pass else 'FAIL'}")
    print(f"  V-path: {np.mean(v_gains):.2f} dB → {'PASS' if v_pass else 'FAIL'}")
    print(f"  Average: {(np.mean(k_gains) + np.mean(v_gains))/2:.2f} dB → {'PASS' if avg_pass else 'FAIL'}")


def main():
    parser = argparse.ArgumentParser(description="Phase 0.2: INT4 quantization error diagnosis")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--seq_len", type=int, default=512)
    parser.add_argument("--out_dir", type=str, default="results/emnlp_postfix_v2/report")
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    torch.manual_seed(args.seed)

    print(f"=== Phase 0.2: Per-layer INT4 Quantization Error Diagnosis ===")
    print(f"Model: {args.model_id}, seq_len: {args.seq_len}")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True,
    )
    model.eval()

    # Use a standard calibration text
    calib_text = (
        "The attention mechanism in transformer models computes a weighted sum of value "
        "vectors, where the weights are determined by the compatibility between query and "
        "key vectors. In large language models with long context windows, the key-value "
        "cache stores these intermediate representations to avoid redundant computation "
        "during autoregressive generation. Quantizing the KV cache to lower bit-widths "
        "reduces memory consumption but introduces quantization noise that can degrade "
        "generation quality, particularly at aggressive compression levels like INT4."
    )

    results = run_diagnosis(model, tokenizer, calib_text, args.seq_len)
    print_results(results)

    # Save JSON
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "int4_error_diagnosis.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
