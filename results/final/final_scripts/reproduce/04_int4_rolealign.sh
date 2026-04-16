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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FINAL_SCRIPTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$FINAL_SCRIPTS_DIR/../../.." && pwd)"
RUN_SCRIPT="$REPO_ROOT/scripts/run_experiments.py"
CONFIG="$FINAL_SCRIPTS_DIR/configs/exp_matrix_rolealign.yaml"
OUT="$REPO_ROOT/results/final/final_data/int4_rolealign/runs"
QUALITY_RUNS="int4_ours_sym_ref,int4_ours_asym_long,int4_ours_asym_ba_long,kivi_style_int4_ref"
PROFILE_RUNS="int4_ours_sym_ref,int4_ours_asym_long,int4_ours_asym_ba_long"

# --- PPL + Needle 论文主线子集 (稳定 run_tag) ---
python3 "$RUN_SCRIPT" \
    --config "$CONFIG" \
    --run_names "$QUALITY_RUNS" \
    --tasks eval_ppl,eval_needle \
    --seeds 1234,1235,1236,1237,1238 \
    --run_tag int4_rolealign_quality \
    --out_dir "$OUT"

# --- RULER (4 context lengths, 每个 context 使用稳定 run_tag) ---
for CTX in 4096 8192 16384 32704; do
    python3 "$RUN_SCRIPT" \
        --config "$CONFIG" \
        --run_names "$QUALITY_RUNS" \
        --tasks eval_ruler \
        --seeds 1234,1235,1236 \
        --run_tag "int4_rolealign_ruler_ctx${CTX}" \
        --ruler_context_len "$CTX" \
        --out_dir "$OUT"
done

# --- Serial TPOT profiling 子集 (稳定 run_tag) ---
python3 "$RUN_SCRIPT" \
    --config "$CONFIG" \
    --run_names "$PROFILE_RUNS" \
    --tasks profile_latency \
    --seeds 1234,1235,1236 \
    --run_tag int4_rolealign_profile \
    --out_dir "$OUT"
