#!/bin/bash
# GPU-2: RULER INT4-RoleAlign 修复验证 (4K, seed=1234)
set -euo pipefail

export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization

echo "===== RULER INT4-RoleAlign 4K verify ====="
echo "Started: $(date)"

python3 scripts/eval_ruler.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ruler_ra_fix_verify

echo "===== RULER RA Done ====="
echo "Finished: $(date)"
