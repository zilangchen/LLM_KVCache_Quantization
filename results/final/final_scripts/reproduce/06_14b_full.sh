#!/bin/bash
# ================================================================
# Step 6: 14B 全套评测
# ================================================================
# 输出: backend_comparison/runs/{ppl,needle,ruler,longbench,ppl_ablation}_*_14b_*
# 原始: scripts/batch_p012/stage5_phase4_14b_full.sh
# GPU: ~6-8h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

RD="results/final/final_data/backend_comparison/runs"
MODEL_14B="Qwen/Qwen2.5-14B-Instruct"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"
RA14="--model_id $MODEL_14B --kv_mode int4_ours_asym --calib_file $CALIB_14B"

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

# --- PPL: RA + FP16, 10 seeds ---
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_ra_14b_s${SEED}" \
    python3 scripts/eval_ppl.py $RA14 --max_samples 32 --chunk_size 128 --seed "$SEED"
  run_or_skip "ppl_fp16_14b_s${SEED}" \
    python3 scripts/eval_ppl.py --model_id "$MODEL_14B" --kv_mode fp16 \
      --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# --- Needle: 3 seeds × 4 ctx × 2 (RA + FP16) ---
for CL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "needle_ra_14b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py $RA14 --context_len "$CL" --num_depths 10 --seed "$SEED"
    run_or_skip "needle_fp16_14b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py --model_id "$MODEL_14B" --kv_mode fp16 \
        --context_len "$CL" --num_depths 10 --seed "$SEED"
  done
done

# --- RULER: 3 seeds × 3 seq (skip 32K) ---
for SL in 4096 8192 16384; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_ra_14b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py $RA14 --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# --- LongBench synthetic: 5 seeds ---
for SEED in 1234 1235 1236 1237 1238; do
  run_or_skip "longbench_ra_14b_s${SEED}" \
    python3 scripts/eval_longbench.py $RA14 --seq_len 32704 --seed "$SEED"
done

# --- K/V ablation PPL: 4 configs × 3 seeds ---
for CFG in "K4V16:4:16" "K16V4:16:4" "K8V4:8:4" "K4V8:4:8"; do
  TAG="${CFG%%:*}"
  REST="${CFG#*:}"
  KB="${REST%%:*}"
  VB="${REST#*:}"
  for SEED in 1234 1235 1236; do
    run_or_skip "ppl_ablation_${TAG}_14b_s${SEED}" \
      python3 scripts/eval_ppl.py --model_id "$MODEL_14B" --kv_mode int4_mixed_kv \
        --k_bits "$KB" --v_bits "$VB" --max_samples 32 --chunk_size 128 --seed "$SEED"
  done
done
