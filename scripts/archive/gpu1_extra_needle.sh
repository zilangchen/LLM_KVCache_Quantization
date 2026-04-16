#!/bin/bash
# GPU-1 叠加任务: Needle INT4-RoleAlign 验证 (与 Exp-10 PPL 共享 GPU)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=1
cd /root/LLM_KVCache_Quantization

echo "===== Needle INT4-RA 32K verify (GPU-1 shared) ====="
echo "Started: $(date)"

python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --seq_len 32704 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/needle_ra_v3_32k_verify

echo "===== Done ====="
echo "Finished: $(date)"
