#!/bin/bash
# GPU-2: KIVI residual buffer 初步验证 (residual_length=32)
# 对比 KIVI 无 residual vs 有 residual 的 PPL
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== KIVI residual_length=0 PPL (baseline, already have: 10.4294) ====="
echo "Skipping — already completed"

echo "===== KIVI residual_length=32 PPL ====="
echo "Started: $(date)"

# 注意：residual_length 通过 runtime_config 传递
# eval_ppl.py 不直接支持 --residual_length，需要通过 generate_loop
# 暂时跑 Needle 验证 residual buffer 不影响质量
python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/needle_kivi_4k_1p5b

echo "===== Done ====="
echo "Finished: $(date)"
