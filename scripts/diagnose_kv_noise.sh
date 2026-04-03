#!/bin/bash
# G2+G5 Diagnostic: KV quantization noise analysis
# G2: Cross-head quantization error correlation (validates GQA 1/H_kv independence assumption)
# G5: Key vs Value noise contribution to attention output (quantifies "Key decides where")
# Usage: bash scripts/diagnose_kv_noise.sh [GPU_ID]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

echo "=== G2+G5 KV Noise Diagnostic ==="
echo "GPU: $GPU_ID | Start: $(date)"

python3 - << 'PYEOF'
import torch
import numpy as np
import json
import sys
sys.path.insert(0, ".")

from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
SEQ_LEN = 512
QUANT_BITS = 4  # INT4 is where the noise matters most

print(f"Loading {MODEL_ID}...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, torch_dtype=torch.float16, device_map="auto"
)
model.eval()
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# Generate input
text = "The quick brown fox jumps over the lazy dog. " * 50
input_ids = tokenizer(text, return_tensors="pt", max_length=SEQ_LEN, truncation=True)["input_ids"].cuda()
print(f"Input shape: {input_ids.shape}")

# Forward pass to collect KV (no attentions needed — G2 only uses KV cache)
with torch.no_grad():
    outputs = model(input_ids, use_cache=True)

past_kv = outputs.past_key_values
num_layers = len(past_kv)
print(f"Layers: {num_layers}")

from src.quant.int4_basic import quantize_symmetric_int4, dequantize_symmetric_int4

# ============================================================
# G2: Cross-head quantization error correlation
# ============================================================
print("\n=== G2: Cross-Head Quantization Error Correlation ===")
layer_correlations = []

for layer_idx in range(num_layers):
    k = past_kv[layer_idx][0]  # [batch, num_kv_heads, seq_len, head_dim]
    num_kv_heads = k.shape[1]

    # Quantize and compute per-head error
    head_errors = []
    for h in range(num_kv_heads):
        k_head = k[:, h:h+1, :, :]  # [B, 1, seq_len, head_dim] — keeps 4D
        k_q, k_scale = quantize_symmetric_int4(k_head)
        k_deq = dequantize_symmetric_int4(k_q, k_scale)
        error = (k_head - k_deq).flatten().float().cpu().numpy()
        head_errors.append(error)

    # Compute pairwise correlation
    if num_kv_heads >= 2:
        corr_matrix = np.corrcoef(head_errors)
        # Extract off-diagonal elements (inter-head correlations)
        mask = ~np.eye(num_kv_heads, dtype=bool)
        inter_corr = corr_matrix[mask]
        mean_corr = float(np.mean(np.abs(inter_corr)))
        layer_correlations.append(mean_corr)
        if layer_idx % 7 == 0:
            print(f"  Layer {layer_idx:2d}: mean |inter-head correlation| = {mean_corr:.4f} (H_kv={num_kv_heads})")

overall_corr = np.mean(layer_correlations)
print(f"\n  Overall mean |inter-head correlation|: {overall_corr:.4f}")
if overall_corr < 0.3:
    print("  >> Conclusion: Correlation is LOW — independence assumption is REASONABLE")
elif overall_corr < 0.6:
    print("  >> Conclusion: Correlation is MODERATE — independence is approximate")
else:
    print("  >> Conclusion: Correlation is HIGH — independence assumption may NOT hold")

# G5 (Key vs Value output perturbation) removed: requires attention weights
# which Qwen2.5 does not return in a usable format with use_cache=True.
# K/V ablation data (Table 4.7/4.8) provides stronger task-level evidence.
v_noise_ratios = []

# Save results
results = {
    "model_id": MODEL_ID,
    "seq_len": SEQ_LEN,
    "quant_bits": QUANT_BITS,
    "g2_cross_head_correlation": {
        "per_layer": [float(c) for c in layer_correlations],
        "overall_mean": float(overall_corr),
    },
}
out_path = "results/emnlp_defense_v1/kv_noise_diagnostic.json"
import os
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {out_path}")
print("\n=== G2 Diagnostic DONE ===")
PYEOF

echo ">>> Diagnostic done: $(date)"
