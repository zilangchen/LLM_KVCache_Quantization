#!/bin/bash
# Phase 1 RESUME: 1.5B — skip completed profiling, start from RULER
# Usage: bash phase1_resume_1p5b.sh [GPU_ID] [CALIB_FILE] [RESULTS_DIR]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
CALIB="${2:-${PHASE1_CALIB:-artifacts/kv_calib_rolealign_1p5b_v3.json}}"
TAG="1p5b"
RD="${3:-${PHASE1_RESULTS_DIR:-results/emnlp_rolealign_v4}}"

# F2 fail-fast: abort if calibration file missing
if [ ! -f "$CALIB" ]; then
  echo "FATAL: Calibration file not found: $CALIB" >&2
  exit 1
fi

mkdir -p "$RD/runs" "$RD/tables" "$RD/logs"

echo "[${TAG}] Resume from RULER: $(date '+%Y-%m-%d %H:%M:%S')"

# --- RULER ---
for SEED in 1234 1235 1236; do
  for CTX in 4096 8192 16384 32704; do
    echo ">>> ${TAG} RULER seed=${SEED} ctx=${CTX}"
    python3 scripts/eval_ruler.py \
      --model_id "$MODEL_ID" --kv_mode int4_ours_asym --quant_bits 4 \
      --calib_file "$CALIB" --seq_len "$CTX" --ruler_context_len "$CTX" --seed "$SEED" \
      --save_csv --out_dir "$RD/runs/ruler_ours_asym_${TAG}_ctx${CTX}_s${SEED}" \
      2>&1 | tee -a "$RD/logs/ruler_${TAG}.log"
  done
done

# --- PPL (5 seeds, full wikitext) ---
for SEED in 1234 1235 1236 1237 1238; do
  echo ">>> ${TAG} PPL seed=${SEED}"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL_ID" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" --seed "$SEED" --save_csv \
    --out_dir "$RD/runs/ppl_ours_asym_${TAG}_s${SEED}" \
    2>&1 | tee -a "$RD/logs/ppl_${TAG}.log"
done

# --- FP16 baseline PPL ---
echo ">>> ${TAG} FP16 PPL baseline"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" --kv_mode fp16 --seed 1234 --save_csv \
  --out_dir "$RD/runs/ppl_fp16_${TAG}_s1234" \
  2>&1 | tee -a "$RD/logs/ppl_fp16_${TAG}.log"

echo "[${TAG}] ALL DONE: $(date '+%Y-%m-%d %H:%M:%S')"
