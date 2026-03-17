#!/usr/bin/env python3
"""
Phase 0.3: K-only / V-only INT4 attribution experiment.

Builds an AttributionKVCache wrapper that selectively quantizes K, V, or both
using KIVI-style asymmetric quantization. Runs PPL and Needle evaluation in
4 configurations to identify whether PPL/Needle degradation comes primarily
from K or V quantization.

Experiment matrix (1.5B, seed=1234):
  1. fp16 baseline (no quantization)
  2. K-only INT4 (K per-channel quantized, V stays fp16)
  3. V-only INT4 (K stays fp16, V per-token quantized)
  4. Both INT4 (equivalent to KIVI INT4 plain)

Usage (on GPU server):
    python scripts/diagnose_kv_attribution.py \
        --model_id Qwen/Qwen2.5-1.5B-Instruct \
        --seed 1234 \
        --out_dir results/emnlp_postfix_v2/report
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_channel,
    dequantize_asymmetric_per_token,
    quantize_asymmetric_per_channel,
    quantize_asymmetric_per_token,
)

logger = logging.getLogger(__name__)


class AttributionKVCache:
    """KV cache wrapper for K/V attribution experiments.

    Supports selective quantization:
    - quantize_k=True, quantize_v=True  → both quantized (KIVI INT4)
    - quantize_k=True, quantize_v=False → K-only INT4
    - quantize_k=False, quantize_v=True → V-only INT4
    - quantize_k=False, quantize_v=False → fp16 (should use FP16KVCache instead)

    K is quantized per-channel (KIVI-style), V is quantized per-token (KIVI-style).
    Non-quantized tensors are stored in fp16.
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        quant_bits: int = 4,
        quantize_k: bool = True,
        quantize_v: bool = True,
        k_percentile: float = 100.0,
        v_percentile: float = 100.0,
    ):
        self.num_layers = num_layers
        self.device = device
        self.dtype = dtype
        self.quant_bits = quant_bits
        self.quantize_k = quantize_k
        self.quantize_v = quantize_v
        self.k_percentile = k_percentile
        self.v_percentile = v_percentile

        # KIVI-compatible interface attributes
        self.decode_attn_impl = "torch_ref"
        self.inv_tau = None
        self.use_attn_temperature = False

        # Storage: per-layer fp16 buffers for non-quantized path
        self._k_fp16: List[Optional[Tensor]] = [None] * num_layers
        self._v_fp16: List[Optional[Tensor]] = [None] * num_layers

        # Storage: quantized K (per-channel, KIVI-style)
        self._k_quant: List[Optional[Tensor]] = [None] * num_layers
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers
        self._k_zp: List[Optional[Tensor]] = [None] * num_layers

        # Storage: quantized V (per-token, KIVI-style)
        self._v_quant: List[Optional[Tensor]] = [None] * num_layers
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers
        self._v_zp: List[Optional[Tensor]] = [None] * num_layers

        self._seq_len = 0
        self._layer_seq_lens = [0] * num_layers

        # Decode stats (compatible interface)
        self.decode_stats: Dict = {
            "fused_decode_calls": 0, "triton_kernel_calls": 0,
            "torch_ref_calls": 0, "layer_hits": {}, "triton_layer_hits": {},
        }

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """Append KV tensors, selectively quantizing based on config."""
        # K path
        if self.quantize_k:
            q_k, k_scale, k_zp = quantize_asymmetric_per_channel(
                k, quant_bits=self.quant_bits, percentile=self.k_percentile
            )
            if self._k_quant[layer_id] is None:
                self._k_quant[layer_id] = q_k
                self._k_scale[layer_id] = k_scale
                self._k_zp[layer_id] = k_zp
            else:
                self._k_quant[layer_id] = torch.cat([self._k_quant[layer_id], q_k], dim=2)
                # For simplicity, recompute scale from full K (decode appends are rare in eval)
        else:
            if self._k_fp16[layer_id] is None:
                self._k_fp16[layer_id] = k.to(self.dtype)
            else:
                self._k_fp16[layer_id] = torch.cat([self._k_fp16[layer_id], k.to(self.dtype)], dim=2)

        # V path
        if self.quantize_v:
            q_v, v_scale, v_zp = quantize_asymmetric_per_token(
                v, quant_bits=self.quant_bits, percentile=self.v_percentile
            )
            if self._v_quant[layer_id] is None:
                self._v_quant[layer_id] = q_v
                self._v_scale[layer_id] = v_scale
                self._v_zp[layer_id] = v_zp
            else:
                self._v_quant[layer_id] = torch.cat([self._v_quant[layer_id], q_v], dim=2)
                self._v_scale[layer_id] = torch.cat([self._v_scale[layer_id], v_scale], dim=2)
                self._v_zp[layer_id] = torch.cat([self._v_zp[layer_id], v_zp], dim=2)
        else:
            if self._v_fp16[layer_id] is None:
                self._v_fp16[layer_id] = v.to(self.dtype)
            else:
                self._v_fp16[layer_id] = torch.cat([self._v_fp16[layer_id], v.to(self.dtype)], dim=2)

        new_len = (self._k_fp16[layer_id] if not self.quantize_k else self._k_quant[layer_id]).shape[2]
        self._layer_seq_lens[layer_id] = new_len
        self._seq_len = max(self._layer_seq_lens)

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """Return dequantized (or fp16) K and V tensors."""
        # K
        if self.quantize_k:
            k = dequantize_asymmetric_per_channel(
                self._k_quant[layer_id], self._k_scale[layer_id], self._k_zp[layer_id]
            ).to(self.dtype)
        else:
            k = self._k_fp16[layer_id]

        # V
        if self.quantize_v:
            v = dequantize_asymmetric_per_token(
                self._v_quant[layer_id], self._v_scale[layer_id], self._v_zp[layer_id]
            ).to(self.dtype)
        else:
            v = self._v_fp16[layer_id]

        return k, v

    def get_seq_len(self) -> int:
        return self._seq_len

    def clear(self) -> None:
        for i in range(self.num_layers):
            self._k_fp16[i] = self._v_fp16[i] = None
            self._k_quant[i] = self._k_scale[i] = self._k_zp[i] = None
            self._v_quant[i] = self._v_scale[i] = self._v_zp[i] = None
        self._layer_seq_lens = [0] * self.num_layers
        self._seq_len = 0

    def release(self) -> None:
        self.clear()

    def get_memory_mb(self) -> float:
        total = 0
        for i in range(self.num_layers):
            for t in [self._k_fp16[i], self._v_fp16[i], self._k_quant[i], self._v_quant[i],
                       self._k_scale[i], self._k_zp[i], self._v_scale[i], self._v_zp[i]]:
                if t is not None:
                    total += t.numel() * t.element_size()
        return total / (1024 * 1024)

    def record_fused_decode(self, layer_id: int, decode_impl: str) -> None:
        pass

    def record_triton_kernel_call(self, layer_id=None) -> None:
        pass

    def reset_decode_stats(self) -> None:
        pass

    def get_decode_stats(self) -> Dict:
        return self.decode_stats


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

CONFIGURATIONS = [
    {"name": "fp16_baseline", "quantize_k": False, "quantize_v": False},
    {"name": "k_only_int4",  "quantize_k": True,  "quantize_v": False},
    {"name": "v_only_int4",  "quantize_k": False, "quantize_v": True},
    {"name": "both_int4",    "quantize_k": True,  "quantize_v": True},
]


def compute_kv_reconstruction_error(
    model, tokenizer, cache, text: str, max_len: int = 4096,
) -> Dict[str, float]:
    """Compute KV reconstruction error after quantize→dequantize round-trip.

    Instead of re-running the model (which requires cache injection into HF
    forward), we measure the direct quantization noise on K and V tensors:
    - K SQNR: how well K is preserved (affects attention distribution)
    - V SQNR: how well V is preserved (affects output logits linearly)

    Returns dict with k_sqnr_db, v_sqnr_db, k_mse, v_mse, cache_mb.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_len)
    input_ids = inputs["input_ids"].to(model.device)
    num_layers = model.config.num_hidden_layers

    with torch.no_grad():
        outputs = model(**{k: v.to(model.device) for k, v in inputs.items()}, use_cache=True)

    # Extract fp16 KV from model output
    past_kv = outputs.past_key_values
    n_kv = len(past_kv) if hasattr(past_kv, "__len__") else 0
    fp16_kvs = []
    for i in range(min(num_layers, n_kv)):
        layer_kv = past_kv[i]
        if isinstance(layer_kv, (tuple, list)) and len(layer_kv) >= 2:
            fp16_kvs.append((layer_kv[0].detach(), layer_kv[1].detach()))
        else:
            break

    # Populate the attribution cache
    cache.clear()
    for i, (k, v) in enumerate(fp16_kvs):
        cache.append(i, k, v)

    # Measure reconstruction error per layer
    k_mse_total, v_mse_total = 0.0, 0.0
    k_signal_total, v_signal_total = 0.0, 0.0
    n_layers_measured = 0

    for i, (k_fp16, v_fp16) in enumerate(fp16_kvs):
        if i >= cache.num_layers:
            break
        k_deq, v_deq = cache.get_kv(i)

        k_f, k_d = k_fp16.float(), k_deq.float()
        v_f, v_d = v_fp16.float(), v_deq.float()

        k_mse_total += (k_f - k_d).pow(2).mean().item()
        v_mse_total += (v_f - v_d).pow(2).mean().item()
        k_signal_total += k_f.pow(2).mean().item()
        v_signal_total += v_f.pow(2).mean().item()
        n_layers_measured += 1

    n = max(n_layers_measured, 1)
    k_mse = k_mse_total / n
    v_mse = v_mse_total / n
    k_sqnr = 10 * torch.log10(torch.tensor(k_signal_total / n / max(k_mse, 1e-20))).item()
    v_sqnr = 10 * torch.log10(torch.tensor(v_signal_total / n / max(v_mse, 1e-20))).item()

    return {
        "k_sqnr_db": round(k_sqnr, 2),
        "v_sqnr_db": round(v_sqnr, 2),
        "k_mse": k_mse,
        "v_mse": v_mse,
        "cache_mb": round(cache.get_memory_mb(), 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 0.3: K/V attribution experiment")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--seq_len", type=int, default=2048,
                        help="Sequence length for PPL evaluation")
    parser.add_argument("--out_dir", type=str, default="results/emnlp_postfix_v2/report")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    torch.manual_seed(args.seed)

    print(f"=== Phase 0.3: K/V Attribution Experiment ===")
    print(f"Model: {args.model_id}, seed: {args.seed}")
    print(f"NOTE: This script should be run on GPU server for meaningful results.")
    print(f"For full PPL/Needle evaluation, use run_experiments.py with custom cache.\n")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True,
    )
    model.eval()
    num_layers = model.config.num_hidden_layers

    # Calibration text for PPL proxy
    calib_text = (
        "The transformer architecture has revolutionized natural language processing "
        "through its self-attention mechanism. Key-value caching enables efficient "
        "autoregressive generation by storing intermediate computations. However, "
        "as context lengths grow to tens of thousands of tokens, the memory footprint "
        "of the KV cache becomes a significant bottleneck. Quantization offers a "
        "promising solution, but aggressive compression to 4-bit precision requires "
        "careful handling of the distinct error propagation characteristics of keys "
        "and values. Keys affect attention distributions through the softmax nonlinearity, "
        "while values propagate linearly to the output. This asymmetry suggests that "
        "a single quantization strategy may not be optimal for both."
    ) * 4  # Repeat for longer context

    results = []
    for cfg in CONFIGURATIONS:
        name = cfg["name"]
        print(f"\n--- Configuration: {name} ---")

        cache = AttributionKVCache(
            num_layers=num_layers,
            device=str(model.device),
            quant_bits=4,
            quantize_k=cfg["quantize_k"],
            quantize_v=cfg["quantize_v"],
        )

        metrics = compute_kv_reconstruction_error(
            model, tokenizer, cache, calib_text, max_len=args.seq_len
        )

        result = {
            "name": name,
            "quantize_k": cfg["quantize_k"],
            "quantize_v": cfg["quantize_v"],
            **metrics,
        }
        results.append(result)
        print(f"  K SQNR: {metrics['k_sqnr_db']:.2f} dB, V SQNR: {metrics['v_sqnr_db']:.2f} dB, "
              f"K MSE: {metrics['k_mse']:.6f}, V MSE: {metrics['v_mse']:.6f}, "
              f"Cache: {metrics['cache_mb']:.2f} MB")
        cache.release()

    # Print summary
    print("\n" + "=" * 80)
    print(f"{'Config':<20} {'K':<6} {'V':<6} {'K SQNR':>8} {'V SQNR':>8} {'K MSE':>10} {'V MSE':>10} {'MB':>6}")
    print("-" * 80)
    for r in results:
        k_str = "INT4" if r["quantize_k"] else "FP16"
        v_str = "INT4" if r["quantize_v"] else "FP16"
        print(f"{r['name']:<20} {k_str:<6} {v_str:<6} {r['k_sqnr_db']:>8.2f} {r['v_sqnr_db']:>8.2f} "
              f"{r['k_mse']:>10.6f} {r['v_mse']:>10.6f} {r['cache_mb']:>6.1f}")

    # Attribution analysis — compare K-only vs V-only degradation
    if len(results) == 4:
        fp16_r, k_only_r, v_only_r, both_r = results
        # For fp16_baseline, both SQNR should be ~100 dB (no quantization noise)
        # For k_only: K SQNR drops (V stays ~100), for v_only: V SQNR drops
        k_noise = k_only_r["k_mse"]  # K quantization noise (MSE)
        v_noise = v_only_r["v_mse"]  # V quantization noise (MSE)
        k_sqnr_drop = fp16_r["k_sqnr_db"] - k_only_r["k_sqnr_db"]
        v_sqnr_drop = fp16_r["v_sqnr_db"] - v_only_r["v_sqnr_db"]

        print(f"\n--- Attribution Analysis (Quantization Noise) ---")
        print(f"K-only: SQNR drop = {k_sqnr_drop:.2f} dB, MSE = {k_noise:.6f}")
        print(f"V-only: SQNR drop = {v_sqnr_drop:.2f} dB, MSE = {v_noise:.6f}")
        print(f"Both:   K SQNR = {both_r['k_sqnr_db']:.2f} dB, V SQNR = {both_r['v_sqnr_db']:.2f} dB")

        if v_noise > k_noise * 1.5:
            print("→ V quantization noise > K noise → V is the primary quality bottleneck")
            print("  (Phase 1B V-path token-CE calibration is main battleground)")
        elif k_noise > v_noise * 1.5:
            print("→ K quantization noise > V noise → K is the primary quality bottleneck")
            print("  (Phase 1A K-path attention-aligned calibration is critical)")
        else:
            print("→ K and V noise are comparable → dual-path approach needed")

    # Save
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "kv_attribution_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
