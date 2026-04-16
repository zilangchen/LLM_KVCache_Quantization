#!/bin/bash
# ================================================================
# Step 10: 7B KL vs MSE 校准对比 — C1 规模依赖证据
# ================================================================
# 输出: results/final/final_data/backend_comparison/runs/
# 原始脚本: scripts/batch_p012/stage_c1_kl_vs_mse.sh
# GPU 时间: ~1h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

MODEL="Qwen/Qwen2.5-7B-Instruct"
OUT="results/final/final_data/backend_comparison/runs"

# --- KL 校准 PPL ---
for SEED in 1234 1235 1236; do
    python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode int4_ours_asym \
        --calib_file artifacts/kv_calib_rolealign_7b_v3.json \
        --seed $SEED --out_dir "$OUT"
done

# --- MSE 校准 PPL ---
for SEED in 1234 1235 1236; do
    python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode int4_ours_asym \
        --calib_file artifacts/kv_calib_mse_7b_int4_rolealign_v1.json \
        --seed $SEED --out_dir "$OUT"
done

# --- FP16 baseline ---
for SEED in 1234 1235 1236; do
    python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode fp16 \
        --seed $SEED --out_dir "$OUT"
done
