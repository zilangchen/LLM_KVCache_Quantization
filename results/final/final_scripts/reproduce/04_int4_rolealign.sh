#!/bin/bash
# ================================================================
# Step 4: INT4-RoleAlign 实验 — 产出 int4_rolealign/ 数据
# ================================================================
# 输出: results/final/final_data/int4_rolealign/
# 内容: INT4-RoleAlign PPL/Needle/RULER 跨模型 (1.5B, 7B, 8B)
#        + inv_tau 消融 + serial profiling
# 配置: configs/exp_matrix_rolealign.yaml
# GPU 时间: ~10-12h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

RESULTS_TAG="int4_rolealign"

# --- PPL + Needle (3 models × 5 seeds) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix_rolealign.yaml \
    --tasks eval_ppl,eval_needle \
    --seeds 1234,1235,1236,1237,1238 \
    --results_tag "$RESULTS_TAG"

# --- RULER (3 models × 4 context lengths × 3 seeds) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix_rolealign.yaml \
    --tasks eval_ruler \
    --seeds 1234,1235,1236 \
    --seq_lens 4096,8192,16384,32704 \
    --results_tag "$RESULTS_TAG"

# --- Serial TPOT profiling ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix_rolealign.yaml \
    --tasks profile_latency \
    --seeds 1234,1235,1236 \
    --results_tag "$RESULTS_TAG"
