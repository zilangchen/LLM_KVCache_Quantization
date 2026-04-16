#!/bin/bash
# ================================================================
# Step 9: FP16 RULER baseline
# ================================================================
# 输出: backend_comparison/runs/ruler_fp16_{1p5b,14b}_sl{4096..32704}_s{1234..1236}
# 原始: scripts/batch_p012/stage_baseline_fp16_ruler.sh
# GPU: ~3h
# 注意: 14B 只跑 4096/8192/16384 (32K 因显存限制不测)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

RD="results/final/final_data/backend_comparison/runs"

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

# --- 1.5B: 4 seq_lens ---
for SL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_fp16_1p5b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py \
        --model_id "Qwen/Qwen2.5-1.5B-Instruct" --kv_mode fp16 \
        --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# --- 14B: 3 seq_lens (skip 32K) ---
for SL in 4096 8192 16384; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_fp16_14b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py \
        --model_id "Qwen/Qwen2.5-14B-Instruct" --kv_mode fp16 \
        --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done
