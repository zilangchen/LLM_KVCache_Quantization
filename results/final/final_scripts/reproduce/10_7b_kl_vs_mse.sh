#!/bin/bash
# ================================================================
# Step 10: 7B KL vs MSE 校准对比 — C1 规模依赖证据
# ================================================================
# 输出: backend_comparison/runs/{ppl,needle}_{kl,mse,fp16}_7b_*
# 内容: 7B 上 KL 和 MSE 校准在 INT4 下趋同的验证
# 原始脚本: scripts/batch_p012/stage_c1_kl_vs_mse.sh
# GPU 时间: ~1h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

MODEL="Qwen/Qwen2.5-7B-Instruct"

# --- KL 校准 PPL ---
python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode int4_ours_asym \
    --calib_file artifacts/kv_calib_rolealign_7b_v3.json \
    --seeds 1234,1235,1236

# --- MSE 校准 PPL ---
python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode int4_ours_asym \
    --calib_file artifacts/kv_calib_mse_7b_int4_rolealign_v1.json \
    --seeds 1234,1235,1236

# --- FP16 baseline ---
python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode fp16 \
    --seeds 1234,1235,1236
