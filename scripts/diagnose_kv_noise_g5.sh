#!/bin/bash
# G5 Diagnostic: Key vs Value noise contribution to attention output
# Computes attention output perturbation from K-only vs V-only INT4 quantization.
# Does NOT rely on output_attentions (manually computes softmax(QK^T/sqrt(d))).
# Usage: bash scripts/diagnose_kv_noise_g5.sh [GPU_ID]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

echo "=== G5: Key vs Value Noise Contribution ==="
echo "GPU: $GPU_ID | Start: $(date)"

python3 - << 'PYEOF'
import torch
import numpy as np
import json
import sys
import os
sys.path.insert(0, ".")

from transformers import AutoModelForCausalLM, AutoTokenizer
from src.quant.int4_basic import quantize_symmetric_int4, dequantize_symmetric_int4

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
SEQ_LEN = 256  # shorter for speed — noise ratio is length-independent

print(f"Loading {MODEL_ID}...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, torch_dtype=torch.float16, device_map="auto"
)
model.eval()
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

text = "The quick brown fox jumps over the lazy dog. " * 30
input_ids = tokenizer(text, return_tensors="pt", max_length=SEQ_LEN, truncation=True)["input_ids"].cuda()
print(f"Input shape: {input_ids.shape}")

# Forward pass to collect Q, K, V per layer
# We hook into the model to capture Q after projection + RoPE
layer_qkv = {}

def make_hook(layer_idx):
    def hook_fn(module, args, output):
        # output of self_attn is (attn_output, attn_weights, past_kv)
        # We need Q, K, V from the attention computation.
        # Since we can't easily get Q from the output, we'll compute it differently.
        pass
    return hook_fn

# Alternative approach: use the KV cache to get K, V, then compute Q @ K^T manually
print("Running forward pass with cache...")
with torch.no_grad():
    outputs = model(input_ids, use_cache=True)
past_kv = outputs.past_key_values
num_layers = len(past_kv)
print(f"Layers: {num_layers}")

# Get Q by running one more decode step and capturing the query
# The last hidden state can be projected to Q
print("Computing Q for last position...")
last_hidden = outputs.hidden_states if hasattr(outputs, 'hidden_states') and outputs.hidden_states else None

# Simpler approach: just use K and V to measure noise, compute attention manually
# For each layer:
#   1. Get K_fp16, V_fp16 from past_kv
#   2. Quantize K to INT4 → K_q, quantize V to INT4 → V_q
#   3. Use a random Q vector (same for both) to compute attention
#   4. Compare: ||attn(Q, K_q, V) - attn(Q, K, V)|| vs ||attn(Q, K, V_q) - attn(Q, K, V)||

print("\nComputing Key vs Value noise impact per layer...")
k_perturbation_ratios = []
v_perturbation_ratios = []

for layer_idx in range(num_layers):
    K = past_kv[layer_idx][0][0].float()  # [H_kv, S, D]
    V = past_kv[layer_idx][1][0].float()  # [H_kv, S, D]
    H_kv, S, D = K.shape

    # Use a fixed random Q (same for K-noise and V-noise comparison)
    torch.manual_seed(42)
    Q = torch.randn(H_kv, 1, D, device=K.device)  # [H_kv, 1, D] — single query token
    sm_scale = 1.0 / (D ** 0.5)

    # Reference: attn(Q, K_fp16, V_fp16)
    scores_ref = torch.bmm(Q, K.transpose(1, 2)) * sm_scale  # [H_kv, 1, S]
    attn_ref = torch.softmax(scores_ref, dim=-1)  # [H_kv, 1, S]
    output_ref = torch.bmm(attn_ref, V)  # [H_kv, 1, D]

    # K-noise: quantize K only
    K_4d = K.unsqueeze(0)  # [1, H_kv, S, D]
    K_q_list = []
    for h in range(H_kv):
        kh = K_4d[:, h:h+1, :, :].half()
        kq, ks = quantize_symmetric_int4(kh)
        K_q_list.append(dequantize_symmetric_int4(kq, ks).float().squeeze(0))
    K_noisy = torch.cat(K_q_list, dim=0)  # [H_kv, S, D]

    scores_k_noise = torch.bmm(Q, K_noisy.transpose(1, 2)) * sm_scale
    attn_k_noise = torch.softmax(scores_k_noise, dim=-1)
    output_k_noise = torch.bmm(attn_k_noise, V)  # K noisy, V clean

    # V-noise: quantize V only
    V_4d = V.unsqueeze(0)
    V_q_list = []
    for h in range(H_kv):
        vh = V_4d[:, h:h+1, :, :].half()
        vq, vs = quantize_symmetric_int4(vh)
        V_q_list.append(dequantize_symmetric_int4(vq, vs).float().squeeze(0))
    V_noisy = torch.cat(V_q_list, dim=0)

    output_v_noise = torch.bmm(attn_ref, V_noisy)  # K clean, V noisy

    # Compute perturbation norms
    ref_norm = torch.norm(output_ref).item() + 1e-8
    k_perturb = torch.norm(output_k_noise - output_ref).item() / ref_norm
    v_perturb = torch.norm(output_v_noise - output_ref).item() / ref_norm

    k_perturbation_ratios.append(k_perturb)
    v_perturbation_ratios.append(v_perturb)

    if layer_idx % 7 == 0:
        ratio = k_perturb / (v_perturb + 1e-10)
        print(f"  Layer {layer_idx:2d}: K-noise={k_perturb:.6f}, V-noise={v_perturb:.6f}, K/V ratio={ratio:.1f}x")

mean_k = np.mean(k_perturbation_ratios)
mean_v = np.mean(v_perturbation_ratios)
overall_ratio = mean_k / (mean_v + 1e-10)

print(f"\n  Mean K-noise perturbation: {mean_k:.6f}")
print(f"  Mean V-noise perturbation: {mean_v:.6f}")
print(f"  Overall K/V noise ratio: {overall_ratio:.1f}x")
print(f"  >> Key quantization noise dominates by {overall_ratio:.1f}x")

# Save
results = {
    "model_id": MODEL_ID,
    "seq_len": int(input_ids.shape[1]),
    "quant_bits": 4,
    "g5_k_noise_perturbation": {
        "per_layer": [float(r) for r in k_perturbation_ratios],
        "mean": float(mean_k),
    },
    "g5_v_noise_perturbation": {
        "per_layer": [float(r) for r in v_perturbation_ratios],
        "mean": float(mean_v),
    },
    "g5_kv_ratio": float(overall_ratio),
}
out_path = "results/emnlp_defense_v1/kv_noise_g5.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_path}")
print("\n=== G5 Diagnostic DONE ===")
PYEOF

echo ">>> G5 done: $(date)"
