#!/bin/bash
# ================================================================
# Step 10: 7B KL vs MSE 校准对比 (完整 6 步)
# ================================================================
# 输出: backend_comparison/runs/{ppl,needle}_{kl,mse}_7b_* + ppl_fp16_7b_s1234
# 原始: scripts/batch_p012/stage_c1_kl_vs_mse.sh
# GPU: ~1.5h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

RD="results/final/final_data/backend_comparison/runs"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"
MSE_CALIB="artifacts/kv_calib_mse_7b_int4_rolealign_v1.json"
KL_CALIB="artifacts/kv_calib_rolealign_7b_v3.json"

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag"; return 0
  fi
  echo "═══ RUN: $tag ═══"
  "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -10
  echo "  DONE: $tag"
}

# Step 1: MSE calibration (如果产物不存在)
if [ ! -f "$MSE_CALIB" ]; then
  echo "═══ Step 1: MSE calibration ═══"
  python3 scripts/calibrate_behavior.py \
    --model_id "$MODEL_7B" --loss_function mse \
    --quant_bits 4 --role_aware_axes --int4_search \
    --seed 1234 --samples 128 --seq_len 2048 \
    --calib_out "$MSE_CALIB" 2>&1 | tail -20
fi

# Step 2: MSE PPL (3 seeds)
MSE_COMMON="--model_id $MODEL_7B --kv_mode int4_ours_asym --calib_file $MSE_CALIB"
for SEED in 1234 1235 1236; do
  run_or_skip "ppl_mse_7b_s${SEED}" \
    python3 scripts/eval_ppl.py $MSE_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Step 3: MSE Needle (4K, 3 seeds)
for SEED in 1234 1235 1236; do
  run_or_skip "needle_mse_7b_c4096_s${SEED}" \
    python3 scripts/eval_needle.py $MSE_COMMON --context_len 4096 --num_depths 10 --seed "$SEED"
done

# Step 4: KL PPL (3 seeds)
KL_COMMON="--model_id $MODEL_7B --kv_mode int4_ours_asym --calib_file $KL_CALIB"
for SEED in 1234 1235 1236; do
  run_or_skip "ppl_kl_7b_s${SEED}" \
    python3 scripts/eval_ppl.py $KL_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Step 5: KL Needle (4K, 3 seeds)
for SEED in 1234 1235 1236; do
  run_or_skip "needle_kl_7b_c4096_s${SEED}" \
    python3 scripts/eval_needle.py $KL_COMMON --context_len 4096 --num_depths 10 --seed "$SEED"
done

# Step 6: FP16 PPL baseline
run_or_skip "ppl_fp16_7b_s1234" \
  python3 scripts/eval_ppl.py --model_id "$MODEL_7B" --kv_mode fp16 \
    --max_samples 32 --chunk_size 128 --seed 1234
