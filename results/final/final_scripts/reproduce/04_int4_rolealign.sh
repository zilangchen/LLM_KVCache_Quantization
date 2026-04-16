#!/bin/bash
# ================================================================
# Step 4: INT4-RoleAlign 实验 — 产出 int4_rolealign/ 数据
# ================================================================
# 输出: results/final/final_data/int4_rolealign/
# 配置: configs/exp_matrix_rolealign.yaml
# GPU 时间: ~10-12h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

OUT="results/final/final_data/int4_rolealign"

# --- PPL + Needle (模型和 kv_modes 由 rolealign config 控制) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix_rolealign.yaml \
    --tasks eval_ppl,eval_needle \
    --seeds 1234,1235,1236,1237,1238 \
    --out_dir "$OUT"

# --- RULER (4 context lengths) ---
for CTX in 4096 8192 16384 32704; do
    python3 scripts/run_experiments.py \
        --config configs/exp_matrix_rolealign.yaml \
        --tasks eval_ruler \
        --seeds 1234,1235,1236 \
        --ruler_context_len $CTX \
        --out_dir "$OUT"
done

# --- Serial TPOT profiling ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix_rolealign.yaml \
    --tasks profile_latency \
    --seeds 1234,1235,1236 \
    --out_dir "$OUT"
