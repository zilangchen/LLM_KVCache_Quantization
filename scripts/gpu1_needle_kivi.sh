#!/bin/bash
# GPU-1: Needle KIVI INT4 32K (与 Exp-10 共享 GPU)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=1
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== Needle KIVI INT4 32K ====="
echo "Started: $(date)"

python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --seq_len 32704 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/needle_kivi_int4_32k_1p5b

echo "===== Done ====="
echo "Finished: $(date)"
