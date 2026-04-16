#!/bin/bash
# ================================================================
# Step 5: 后端 TPOT 对比 — 产出 backend_comparison/tpot_* 数据
# ================================================================
# 输出: results/final/final_data/backend_comparison/runs/
# 内容: 4 模型 × 5 后端 Phase 1 TPOT
# 原始脚本: scripts/batch_p012/stage1_phase1_rerun.sh
# GPU 时间: ~3-4h (需独占 GPU)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

OUT="results/final/final_data/backend_comparison/runs"

for MODEL in "Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-7B-Instruct" \
             "meta-llama/Llama-3.1-8B-Instruct" "Qwen/Qwen2.5-14B-Instruct"; do
    for BACKEND in "fp16" "torchref" "kivi" "triton_ra" "flashinfer"; do
        python3 scripts/profile_latency.py \
            --model_id "$MODEL" \
            --kv_mode int4_ours_asym \
            --decode_impl "$BACKEND" \
            --seq_len 4096 --gen_len 128 --batch_size 1 \
            --warmup 3 --runs 8 --seed 1234 \
            --out_dir "$OUT"
    done
done
