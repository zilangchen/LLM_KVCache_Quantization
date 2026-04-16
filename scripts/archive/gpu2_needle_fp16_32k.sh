#!/bin/bash
# GPU-2: Needle FP16 32K 验证 (v3 产物对照组)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== Needle FP16 32K verify ====="
echo "Started: $(date)"

python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode fp16 \
  --seq_len 32704 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/needle_fp16_32k_verify

echo "===== Needle FP16 Done ====="

# Chain: PPL FP16 baseline for v3 comparison
echo "===== PPL FP16 baseline ====="
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode fp16 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_fp16_baseline_1p5b

echo "===== All GPU-2 tasks Done ====="
echo "Finished: $(date)"
