#!/bin/bash
# Phase 1 补跑: RULER ctx>4096 (修复 --seq_len 缺失 bug)
# 只跑 ctx=8192/16384/32704, ctx=4096 已有效
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="$1"   # e.g. Qwen/Qwen2.5-1.5B-Instruct
CALIB="$2"       # e.g. artifacts/kv_calib_rolealign_1p5b.json
TAG="$3"         # e.g. 1p5b

RD="results/emnlp_rolealign_v2"
mkdir -p "$RD/runs" "$RD/logs"

echo "[${TAG}] RULER rerun start: $(date '+%Y-%m-%d %H:%M:%S')"

for SEED in 1234 1235 1236; do
  for CTX in 8192 16384 32704; do
    OUTDIR="$RD/runs/ruler_v2fix_${TAG}_ctx${CTX}_s${SEED}"

    # Skip if already completed
    if ls "$OUTDIR"/ruler_details_*.csv >/dev/null 2>&1; then
      echo ">>> ${TAG} RULER seed=${SEED} ctx=${CTX} — SKIP (already exists)"
      continue
    fi

    echo ">>> ${TAG} RULER seed=${SEED} ctx=${CTX} (seq_len=${CTX})"

    python3 scripts/eval_ruler.py \
      --model_id "$MODEL_ID" \
      --kv_mode int4_ours_asym \
      --quant_bits 4 \
      --calib_file "$CALIB" \
      --ruler_context_len "$CTX" \
      --seq_len "$CTX" \
      --gen_len 64 \
      --seed "$SEED" \
      --save_csv \
      --out_dir "$OUTDIR" \
      2>&1 | tee -a "$RD/logs/ruler_v2fix_${TAG}.log"

    # === Inline validation (via standalone script) ===
    DETAILS=$(ls "$OUTDIR"/ruler_details_*.csv 2>/dev/null | head -1)
    if [ -n "$DETAILS" ]; then
      python3 scripts/validate_ruler_results.py 2>&1 | tail -5 | tee -a "$RD/logs/ruler_v2fix_${TAG}.log" || true
    else
      echo "  WARN: no details CSV produced"
    fi
  done
done

echo "[${TAG}] RULER rerun ALL DONE: $(date '+%Y-%m-%d %H:%M:%S')"
