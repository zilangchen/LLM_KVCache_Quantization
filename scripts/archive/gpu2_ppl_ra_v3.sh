#!/bin/bash
# GPU-2: PPL INT4-RoleAlign v3 (关键数据 — 验证 v3 校准 PPL)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== PPL INT4-RoleAlign v3 (1.5B) ====="
echo "Started: $(date)"

python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_ra_v3_1p5b_s1234

echo "===== PPL INT4-RA v3 Done ====="

# Chain: KIVI-style INT4 PPL for comparison
echo "===== PPL KIVI-style INT4 (1.5B) ====="
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_kivi_int4_1p5b_s1234

echo "===== All GPU-2 tasks Done ====="
echo "Finished: $(date)"
