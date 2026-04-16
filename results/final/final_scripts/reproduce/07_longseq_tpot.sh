#!/bin/bash
# ================================================================
# Step 7: 长序列 TPOT scaling — 产出 backend_comparison/longseq_* 数据
# ================================================================
# 输出: backend_comparison/runs/longseq_{fp16,kivi,torchref,triton_ra}_{1p5b,7b,14b}_*
# 内容: 3 模型 × 4 后端 × 4 序列长度 (4K, 8K, 16K, 32K)
# 原始脚本: scripts/batch_p012/stage7_rerun.sh
# GPU 时间: ~4-6h (需独占 GPU)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

for MODEL_TAG in "1p5b:Qwen/Qwen2.5-1.5B-Instruct" \
                 "7b:Qwen/Qwen2.5-7B-Instruct" \
                 "14b:Qwen/Qwen2.5-14B-Instruct"; do
    TAG="${MODEL_TAG%%:*}"
    MODEL="${MODEL_TAG#*:}"
    for BACKEND in "fp16" "kivi" "torchref" "triton_ra"; do
        for SEQ in 4096 8192 16384 32704; do
            python3 scripts/profile_latency.py \
                --model_id "$MODEL" \
                --kv_mode int4_ours_asym \
                --decode_impl "$BACKEND" \
                --seq_len $SEQ --gen_len 64 --batch_size 1 \
                --warmup 5 --runs 10 --seed 1234
        done
    done
done
