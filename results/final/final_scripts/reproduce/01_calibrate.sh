#!/bin/bash
# ================================================================
# Step 1: 离线校准 — 产出论文主线所需校准产物 (JSON)
# ================================================================
# 输出:
#   - artifacts/kv_calib_kl_selected_v3_quick.json (INT8 1.5B)
#   - artifacts/kv_calib_kl_int4_selected.json    (INT4 对称 1.5B)
#   - artifacts/kv_calib_rolealign_1p5b.json      (RoleAlign 1.5B)
#   - artifacts/kv_calib_rolealign_7b.json        (RoleAlign 7B, 见 L56)
#   - artifacts/kv_calib_rolealign_8b.json        (RoleAlign 8B, 见 L57)
# 冻结已有（不由本脚本生成；见 artifacts/）:
#   - kv_calib_rolealign_14b_v3.json (14B 冻结产物，历史命名含 _v3)
# 依赖: 模型权重 (HuggingFace), WikiText-2 校准数据 (test split, n=16~32)
# GPU 时间: ~1h per model；主线最小集 (1.5B) 默认启用，7B/8B 需取消注释
# TR-0011 披露: 7B/8B v3_quick 校准在 05/07/08 中被引用；若未执行 L56/57 则
#   05 的 torchref/triton_ra/fi 分支（7B/8B 上）和 07/08 会因 calib 缺失而 fail-fast。
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

# --- 7B RoleAlign 校准（默认注释；05/07 需要此产物） ---
# python3 "$CALIB_SCRIPT" \
#     --model_id Qwen/Qwen2.5-7B-Instruct \
#     --role_aware_axes --loss_function kl --quant_bits 4 \
#     --samples 16 --seq_len 512 --seed 1234 \
#     --inv_tau_candidates "0.5,0.7,0.85,1.0,1.2,1.5,2.0" \
#     --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
#     --v_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
#     --calib_out "$ARTIFACTS_DIR/kv_calib_rolealign_7b.json"

# --- 8B RoleAlign 校准（默认注释；05/08 需要此产物） ---
# python3 "$CALIB_SCRIPT" \
#     --model_id meta-llama/Llama-3.1-8B-Instruct \
#     --role_aware_axes --loss_function kl --quant_bits 4 \
#     --samples 16 --seq_len 512 --seed 1234 \
#     --inv_tau_candidates "0.5,0.7,0.85,1.0,1.2,1.5,2.0" \
#     --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
#     --v_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
#     --calib_out "$ARTIFACTS_DIR/kv_calib_rolealign_7b.json"

# --- 14B 校准 (冻结产物 artifacts/kv_calib_rolealign_14b_v3.json 已存在，无需重新生成) ---
# 若需重新生成（GPU 3-4h），参照 7B/8B 上面格式，替换 model_id 与 calib_out 后执行。
