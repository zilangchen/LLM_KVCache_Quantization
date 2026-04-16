#!/bin/bash
# ================================================================
# Step 9: FP16 RULER baseline — 证明 1.5B RULER 低分是模型上限
# ================================================================
# 输出: results/final/final_data/backend_comparison/runs/
# 原始脚本: scripts/batch_p012/stage_baseline_fp16_ruler.sh
# GPU 时间: ~3h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

OUT="results/final/final_data/backend_comparison/runs"

for MODEL in "Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-14B-Instruct"; do
    for SEQ in 4096 8192 16384 32704; do
        for SEED in 1234 1235 1236; do
            python3 scripts/eval_ruler.py \
                --model_id "$MODEL" \
                --kv_mode fp16 \
                --ruler_context_len $SEQ \
                --seed $SEED \
                --out_dir "$OUT"
        done
    done
done
