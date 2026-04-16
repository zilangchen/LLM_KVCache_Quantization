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

RUN_SCRIPT="scripts/run_experiments.py"
CONFIG="configs/exp_matrix.yaml"
OUT="results/final/final_data/int8_mainline/runs"
QUALITY_RUNS="fp16_kv_long,int8_baseline_long_torch,int8_ours_long_fused,kivi_style_int8_long"
PROFILE_RUNS="fp16_throughput_8k_b1,fp16_throughput_8k_b4,fp16_throughput_8k_b8,fp16_throughput_8k_b16,int8_baseline_throughput_8k_b1,int8_baseline_throughput_8k_b4,int8_baseline_throughput_8k_b8,int8_baseline_throughput_8k_b16,int8_ours_throughput_8k_b1,int8_ours_throughput_8k_b4,int8_ours_throughput_8k_b8,int8_ours_throughput_8k_b16,kivi_style_int8_throughput_8k_b1,kivi_style_int8_throughput_8k_b4,kivi_style_int8_throughput_8k_b8,kivi_style_int8_throughput_8k_b16"

# --- 论文主线质量子集 (稳定 run_tag；不追求与历史冻结目录逐个同名) ---
python3 "$RUN_SCRIPT" \
    --config "$CONFIG" \
    --run_names "$QUALITY_RUNS" \
    --tasks eval_ppl,eval_needle,eval_ruler,eval_longbench \
    --seeds 1234,1235,1236,1237,1238 \
    --run_tag int8_mainline_quality \
    --out_dir "$OUT"

# --- 论文主线 profiling 子集 (稳定 run_tag) ---
python3 "$RUN_SCRIPT" \
    --config "$CONFIG" \
    --run_names "$PROFILE_RUNS" \
    --tasks profile_latency,profile_memory \
    --seeds 1234,1235,1236 \
    --run_tag int8_mainline_profile \
    --out_dir "$OUT"
