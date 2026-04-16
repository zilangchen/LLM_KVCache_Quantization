#!/bin/bash
# ================================================================
# Step 9: FP16 RULER baseline — 证明 1.5B RULER 低分是模型上限
# ================================================================
# 输出: backend_comparison/runs/ruler_fp16_{1p5b,14b}_*
# 内容: 1.5B + 14B FP16 RULER baseline (4 tasks × 4 seq × 3 seeds)
# 原始脚本: scripts/batch_p012/stage_baseline_fp16_ruler.sh
# GPU 时间: ~3h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

for MODEL_TAG in "1p5b:Qwen/Qwen2.5-1.5B-Instruct" \
                 "14b:Qwen/Qwen2.5-14B-Instruct"; do
    TAG="${MODEL_TAG%%:*}"
    MODEL="${MODEL_TAG#*:}"
    for SEQ in 4096 8192 16384 32704; do
        python3 scripts/eval_ruler.py \
            --model_id "$MODEL" \
            --kv_mode fp16 \
            --seq_len $SEQ \
            --seeds 1234,1235,1236
    done
done
