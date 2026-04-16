#!/bin/bash
# Exp-2: INT8 calibration comparison — v5_fixed (with RoPE) vs v3_quick (without RoPE)
# Tests whether correcting the calibration artifact changes INT8 quality
# Usage: bash scripts/exp2_int8_calib_compare.sh [GPU_ID]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
CALIB_NEW="artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json"
RD="results/emnlp_defense_v1"

# Fail-fast
if [ ! -f "$CALIB_NEW" ]; then
  echo "FATAL: v5_fixed calibration not found: $CALIB_NEW" >&2
  exit 1
fi

mkdir -p "$RD/runs" "$RD/logs"

echo "=== Exp-2: INT8 v5_fixed vs v3_quick (1.5B, 3 seeds) ==="
echo "GPU: $GPU_ID | CALIB: $CALIB_NEW"
echo "Start: $(date)"

for SEED in 1234 1235 1236; do
  echo ">>> PPL seed=$SEED"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL_ID" --kv_mode int8_ours \
    --calib_file "$CALIB_NEW" \
    --chunk_size 128 --seed "$SEED" \
    --save_csv --out_dir "$RD/runs/ppl_int8_v5_1p5b_s${SEED}" \
    2>&1 | tee -a "$RD/logs/exp2_int8_v5_ppl.log"

  echo ">>> Needle seed=$SEED"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL_ID" --kv_mode int8_ours \
    --calib_file "$CALIB_NEW" \
    --seq_len 32704 --seed "$SEED" \
    --save_csv --out_dir "$RD/runs/needle_int8_v5_1p5b_s${SEED}" \
    2>&1 | tee -a "$RD/logs/exp2_int8_v5_needle.log"
done

echo ">>> Exp-2 ALL DONE: $(date)"
