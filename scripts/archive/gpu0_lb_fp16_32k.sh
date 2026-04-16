#!/bin/bash
# GPU-0 叠加: LongBench FP16 32K baseline (与 T3 共享)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== LongBench FP16 32K baseline ====="
echo "Started: $(date)"

python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode fp16 --seed 1234 \
  --longbench_source synthetic \
  --save_csv --out_dir results/emnlp_defense_v1/runs/longbench_fp16_32k_1p5b

echo "===== Done ====="
echo "Finished: $(date)"
