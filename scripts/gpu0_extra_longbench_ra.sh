#!/bin/bash
# GPU-0 叠加任务: LongBench INT4-RoleAlign 验证 (与 T3 共享 GPU)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization

echo "===== LongBench INT4-RA verify (GPU-0 shared) ====="
echo "Started: $(date)"

python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --longbench_source synthetic --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/longbench_ra_v3_verify

echo "===== Done ====="
echo "Finished: $(date)"
