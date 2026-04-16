#!/bin/bash
# ================================================================
# Step 2: INT8 主线实验 — 产出 int8_mainline/ 数据
# ================================================================
# 输出: results/final/final_data/int8_mainline/
# 配置: configs/exp_matrix.yaml (定义模型、kv_modes、评测参数)
# GPU 时间: ~12-15h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

OUT="results/final/final_data/int8_mainline"

# --- 全量矩阵 (模型和 kv_modes 由 config 控制) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix.yaml \
    --tasks eval_ppl,eval_needle,eval_ruler,eval_longbench \
    --seeds 1234,1235,1236,1237,1238 \
    --out_dir "$OUT"

# --- TPOT profiling (需独占 GPU) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix.yaml \
    --tasks profile_latency,profile_memory \
    --seeds 1234,1235,1236 \
    --out_dir "$OUT"
