#!/bin/bash
# GPU-0: Needle FP16 多上下文 (4K/8K/16K, 32K 已完成)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

for CTX in 4096 8192 16384; do
  echo "===== Needle FP16 ctx=$CTX ====="
  python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode fp16 \
    --seq_len $CTX --seed 1234 \
    --save_csv --out_dir results/emnlp_defense_v1/runs/needle_fp16_ctx${CTX}_1p5b
done

echo "===== Needle FP16 chain Done ====="
echo "Finished: $(date)"
