#!/bin/bash
# ================================================================
# Step 2: INT8 主线实验 — 产出 int8_mainline/ 数据
# ================================================================
# 输出: results/final/final_data/int8_mainline/
# 内容: PPL, Needle, RULER, LongBench, TPOT (1.5B 全量 + 7B/8B 跨模型)
# 配置: configs/exp_matrix.yaml
# GPU 时间: ~12-15h (全量矩阵)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

RESULTS_TAG="int8_mainline"

# --- 1.5B 全量矩阵 ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix.yaml \
    --tasks eval_ppl,eval_needle,eval_ruler,eval_longbench \
    --seeds 1234,1235,1236,1237,1238 \
    --results_tag "$RESULTS_TAG"

# --- TPOT profiling (需独占 GPU) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix.yaml \
    --tasks profile_latency,profile_memory \
    --seeds 1234,1235,1236 \
    --results_tag "$RESULTS_TAG"

# --- 7B/8B 跨模型泛化 ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix.yaml \
    --tasks eval_ppl,eval_needle,eval_longbench \
    --seeds 1234,1235,1236 \
    --model_filter "7B,8B" \
    --results_tag "$RESULTS_TAG"
