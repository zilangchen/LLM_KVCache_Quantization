#!/bin/bash
# GPU-2: 诊断 INT4-RA cs=1 PPL 崩溃
# 用 max_samples=64 复现 v2 条件
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== INT4-RA cs=1 max_samples=64 (复现 v2 条件) ====="
echo "Started: $(date)"

python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --chunk_size 1 --max_samples 64 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_ra_cs1_ms64_1p5b

echo "===== INT4-RA cs=8 (中间值) ====="
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --chunk_size 8 --max_samples 64 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_ra_cs8_ms64_1p5b

echo "===== Done ====="
echo "Finished: $(date)"
