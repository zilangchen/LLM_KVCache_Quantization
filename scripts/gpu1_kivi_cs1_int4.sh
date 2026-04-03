#!/bin/bash
# GPU-1: KIVI INT4 cs=1 PPL (修正: 显式 --quant_bits 4)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=1
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== KIVI INT4 cs=1 PPL ====="
echo "Started: $(date)"

python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --chunk_size 1 --max_samples 100 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_kivi_int4_cs1_1p5b

echo "===== Done ====="
echo "Finished: $(date)"
