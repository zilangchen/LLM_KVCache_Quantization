#!/bin/bash
# ================================================================
# Step 7: 长序列 TPOT scaling — 产出 backend_comparison/longseq_* 数据
# ================================================================
# 输出: results/final/final_data/backend_comparison/runs/
# 原始脚本: scripts/batch_p012/stage7_rerun.sh
# GPU 时间: ~4-6h (需独占 GPU)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

OUT="results/final/final_data/backend_comparison/runs"

for MODEL in "Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-7B-Instruct" \
             "Qwen/Qwen2.5-14B-Instruct"; do
    for BACKEND in "fp16" "kivi" "torchref" "triton_ra"; do
        for SEQ in 4096 8192 16384 32704; do
            python3 scripts/profile_latency.py \
                --model_id "$MODEL" \
                --kv_mode int4_ours_asym \
                --decode_impl "$BACKEND" \
                --seq_len $SEQ --gen_len 64 --batch_size 1 \
                --warmup 5 --runs 10 --seed 1234 \
                --out_dir "$OUT"
        done
    done
done
