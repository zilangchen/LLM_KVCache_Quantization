#!/bin/bash
# ================================================================
# Step 1: 离线校准 — 产出论文主线所需校准产物 (JSON)
# ================================================================
# 输出:
#   - artifacts/kv_calib_kl_selected_v3_quick.json
#   - artifacts/kv_calib_kl_int4_selected.json
#   - artifacts/kv_calib_rolealign_1p5b.json
# 依赖: 模型权重 (HuggingFace), WikiText-103 校准数据
# GPU 时间: ~1h per model
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

CALIB_SCRIPT="scripts/calibrate_behavior.py"
ARTIFACTS_DIR="artifacts"

# --- 1.5B INT8 KL 校准（fused 友好主线） ---
python3 "$CALIB_SCRIPT" \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --search \
    --loss_function kl \
    --quant_bits 8 \
    --samples 16 \
    --seq_len 8192 \
    --calib_out "$ARTIFACTS_DIR/kv_calib_kl_selected_v3_quick.json"

# --- 1.5B INT4 KL 校准（对称 INT4 baseline / fused 路径） ---
python3 "$CALIB_SCRIPT" \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --search \
    --loss_function kl \
    --quant_bits 4 \
    --samples 32 \
    --seq_len 8192 \
    --search_group_sizes 8,16,32,64 \
    --search_clip_percentiles 99.0,99.5,99.9,100.0 \
    --search_outlier_ratios 0,0.0025,0.005,0.01 \
    --calib_out "$ARTIFACTS_DIR/kv_calib_kl_int4_selected.json"

# --- 1.5B RoleAlign 校准（per-channel K + per-token V） ---
python3 "$CALIB_SCRIPT" \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --role_aware_axes \
    --loss_function kl \
    --quant_bits 4 \
    --samples 16 \
    --seq_len 512 \
    --seed 1234 \
    --inv_tau_candidates "0.5,0.7,0.85,1.0,1.2,1.5,2.0" \
    --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
    --v_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
    --calib_out "$ARTIFACTS_DIR/kv_calib_rolealign_1p5b.json"

# --- 7B/8B/14B 校准 (同上，替换 model_id / calib_out) ---
# python3 "$CALIB_SCRIPT" --model_id Qwen/Qwen2.5-7B-Instruct --search --loss_function kl --quant_bits 8 --samples 16 --seq_len 8192 --calib_out "$ARTIFACTS_DIR/..."
# python3 "$CALIB_SCRIPT" --model_id meta-llama/Llama-3.1-8B-Instruct --role_aware_axes --loss_function kl --quant_bits 4 --samples 16 --seq_len 512 --calib_out "$ARTIFACTS_DIR/..."
# python3 "$CALIB_SCRIPT" --model_id Qwen/Qwen2.5-14B-Instruct --role_aware_axes --loss_function kl --quant_bits 4 --samples 16 --seq_len 512 --calib_out "$ARTIFACTS_DIR/..."
