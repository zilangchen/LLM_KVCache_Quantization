#!/bin/bash
# C1 补实验: 7B KL vs MSE calibration 对比
#
# 目的: 补 C1 (行为对齐) 的泛化性证据 — 之前 KL vs MSE 只有 1.5B
#
# Step 1: 跑 7B MSE 校准 (calibrate_behavior.py --loss_function mse)
# Step 2: 用 MSE calib 跑 7B PPL (3 seeds) + Needle (4K 3 seeds)
# Step 3: 对比 7B KL (rolealign_v3) PPL + Needle (已有数据)
#
# 预计耗时: ~1.5h (calibration 30min + PPL 30min + Needle 30min)

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"
MSE_CALIB="artifacts/kv_calib_mse_7b_int4_rolealign_v1.json"
KL_CALIB="artifacts/kv_calib_rolealign_7b_v3.json"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag (exists)"
    return 0
  fi
  echo ""; echo "═══ RUN: $tag ═══"
  timestamp
  "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -20
  echo "  DONE: $tag"
}

echo "═══════════════════════════════════════════"
echo "C1 补实验: 7B KL vs MSE calibration"
echo "Started: $(timestamp)"
echo "═══════════════════════════════════════════"

# ─── Step 1: 7B MSE calibration ───
echo ""
echo "═══ Step 1: MSE calibration for 7B ═══"

if [ -f "$MSE_CALIB" ]; then
  echo "  SKIP: $MSE_CALIB already exists"
else
  echo "  Running calibrate_behavior.py with MSE loss..."
  timestamp
  python3 scripts/calibrate_behavior.py \
    --model_id "$MODEL_7B" \
    --loss_function mse \
    --quant_bits 4 \
    --role_aware_axes \
    --int4_search \
    --seed 1234 \
    --samples 128 \
    --seq_len 2048 \
    --calib_out "$MSE_CALIB" \
    2>&1 | tail -30
  echo "  Calibration done: $(timestamp)"

  if [ ! -f "$MSE_CALIB" ]; then
    echo "  FAILED: MSE calib not generated!"
    exit 1
  fi
  echo "  Generated: $MSE_CALIB"
fi

# ─── Step 2: 7B MSE PPL (3 seeds) ───
echo ""
echo "═══ Step 2: 7B MSE PPL (3 seeds) ═══"
MSE_COMMON="--model_id $MODEL_7B --kv_mode int4_ours_asym --calib_file $MSE_CALIB"

for SEED in 1234 1235 1236; do
  run_or_skip "ppl_mse_7b_s${SEED}" \
    python3 scripts/eval_ppl.py $MSE_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# ─── Step 3: 7B MSE Needle (4K, 3 seeds) ───
echo ""
echo "═══ Step 3: 7B MSE Needle (4K, 3 seeds) ═══"
for SEED in 1234 1235 1236; do
  run_or_skip "needle_mse_7b_c4096_s${SEED}" \
    python3 scripts/eval_needle.py $MSE_COMMON --context_len 4096 --num_depths 10 --seed "$SEED"
done

# ─── Step 4: 7B KL PPL (3 seeds) — 补 KL 对照 ───
echo ""
echo "═══ Step 4: 7B KL PPL (3 seeds, 对照) ═══"
KL_COMMON="--model_id $MODEL_7B --kv_mode int4_ours_asym --calib_file $KL_CALIB"

for SEED in 1234 1235 1236; do
  run_or_skip "ppl_kl_7b_s${SEED}" \
    python3 scripts/eval_ppl.py $KL_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# ─── Step 5: 7B KL Needle (4K, 3 seeds) — 补 KL 对照 ───
echo ""
echo "═══ Step 5: 7B KL Needle (4K, 3 seeds, 对照) ═══"
for SEED in 1234 1235 1236; do
  run_or_skip "needle_kl_7b_c4096_s${SEED}" \
    python3 scripts/eval_needle.py $KL_COMMON --context_len 4096 --num_depths 10 --seed "$SEED"
done

# ─── Step 6: 7B FP16 PPL baseline (1 seed, 快速对照) ───
echo ""
echo "═══ Step 6: 7B FP16 PPL baseline ═══"
run_or_skip "ppl_fp16_7b_s1234" \
  python3 scripts/eval_ppl.py --model_id "$MODEL_7B" --kv_mode fp16 \
    --max_samples 32 --chunk_size 128 --seed 1234

echo ""
echo "═══════════════════════════════════════════"
echo "C1 补实验 complete: $(timestamp)"
echo "═══════════════════════════════════════════"
echo ""
echo "对比数据:"
echo "  MSE PPL: results/emnlp_p012_batch/runs/ppl_mse_7b_s*/"
echo "  KL PPL:  results/emnlp_p012_batch/runs/ppl_kl_7b_s*/"
echo "  FP16 PPL: results/emnlp_p012_batch/runs/ppl_fp16_7b_s1234/"
echo "  MSE Needle: results/emnlp_p012_batch/runs/needle_mse_7b_*/"
echo "  KL Needle:  results/emnlp_p012_batch/runs/needle_kl_7b_*/"
