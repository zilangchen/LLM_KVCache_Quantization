#!/bin/bash
# GPU-2: RULER INT4-RoleAlign v3 多上下文 (8K/16K/32K — 4K 已完成)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

for CTX in 8192 16384 32704; do
  echo "===== RULER INT4-RA v3 ctx=$CTX ====="
  echo "Started: $(date)"
  python3 scripts/eval_ruler.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
    --seq_len $CTX --seed 1234 \
    --save_csv --out_dir results/emnlp_defense_v1/runs/ruler_ra_v3_ctx${CTX}_1p5b
done

echo "===== All GPU-2 RULER Done ====="
echo "Finished: $(date)"
