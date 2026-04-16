#!/bin/bash
# GPU-1 叠加: KIVI Needle 4K 验证 (NameError bug 已修复)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=1
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== KIVI Needle 4K (post-fix) ====="
echo "Started: $(date)"

python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/needle_kivi_4k_postfix

echo "===== Done ====="
echo "Finished: $(date)"
