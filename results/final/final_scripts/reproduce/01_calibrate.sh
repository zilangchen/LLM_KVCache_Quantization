#!/bin/bash
# ================================================================
# Step 1: 离线校准 — 产出 INT8/INT4 校准产物 (JSON)
# ================================================================
# 输出: artifacts/kv_calib_*.json
# 依赖: 模型权重 (HuggingFace), WikiText-103 校准数据
# GPU 时间: ~1h per model
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

# --- 1.5B INT8 KL 校准 ---
python3 scripts/calibrate_behavior.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --method kl_selected \
    --bit_width 8 \
    --num_samples 128 \
    --output artifacts/kv_calib_kl_1p5b_int8.json

# --- 1.5B INT4 KL 校准 ---
python3 scripts/calibrate_behavior.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --method kl_selected \
    --bit_width 4 \
    --num_samples 128 \
    --output artifacts/kv_calib_kl_1p5b_int4.json

# --- 7B/8B/14B 校准 (同上，替换 model_id) ---
# python3 scripts/calibrate_behavior.py --model_id Qwen/Qwen2.5-7B-Instruct ...
# python3 scripts/calibrate_behavior.py --model_id meta-llama/Llama-3.1-8B-Instruct ...
# python3 scripts/calibrate_behavior.py --model_id Qwen/Qwen2.5-14B-Instruct ...
