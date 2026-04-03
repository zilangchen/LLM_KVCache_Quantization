#!/bin/bash
# Attack Surface 6: K/V ablation PPL experiment
# Tests whether Key or Value quantization dominates PPL degradation
# Usage: bash scripts/exp_kv_ablation_ppl.sh [GPU_ID]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
RD="results/emnlp_defense_v1"
mkdir -p "$RD/runs" "$RD/logs"

echo "=== K/V Ablation PPL (Attack Surface 6) ==="
echo "GPU: $GPU_ID | Start: $(date)"

# K@INT4 + V@FP16 (K-only degradation)
echo ">>> K@INT4 + V@FP16"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_mixed_kv --k_bits 4 --v_bits 16 \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/runs/ppl_ablation_k4_v16_1p5b" \
  2>&1 | tee "$RD/logs/ablation_k4_v16.log"
echo ">>> K@INT4+V@FP16 done: $(date)"

# K@FP16 + V@INT4 (V-only degradation)
echo ">>> K@FP16 + V@INT4"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_mixed_kv --k_bits 16 --v_bits 4 \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/runs/ppl_ablation_k16_v4_1p5b" \
  2>&1 | tee "$RD/logs/ablation_k16_v4.log"
echo ">>> K@FP16+V@INT4 done: $(date)"

# K@INT8 + V@FP16 (INT8 K-only)
echo ">>> K@INT8 + V@FP16"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_mixed_kv --k_bits 8 --v_bits 16 \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/runs/ppl_ablation_k8_v16_1p5b" \
  2>&1 | tee "$RD/logs/ablation_k8_v16.log"
echo ">>> K@INT8+V@FP16 done: $(date)"

# K@FP16 + V@INT8 (INT8 V-only)
echo ">>> K@FP16 + V@INT8"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_mixed_kv --k_bits 16 --v_bits 8 \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/runs/ppl_ablation_k16_v8_1p5b" \
  2>&1 | tee "$RD/logs/ablation_k16_v8.log"
echo ">>> K@FP16+V@INT8 done: $(date)"

echo ""
echo "=== K/V Ablation PPL ALL DONE: $(date) ==="
