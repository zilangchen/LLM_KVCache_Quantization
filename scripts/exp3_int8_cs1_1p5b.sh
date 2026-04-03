#!/bin/bash
# Exp-3: INT8-ours chunk_size=1 PPL — Qwen2.5-1.5B
# Tests whether INT8 quality holds under full quantization (no FP16 within-chunk KV)
# Usage: bash scripts/exp3_int8_cs1_1p5b.sh [GPU_ID]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
CALIB="artifacts/kv_calib_kl_selected_v3_quick.json"
RD="results/emnlp_defense_v1"

# Fail-fast
if [ ! -f "$CALIB" ]; then
  echo "FATAL: Calibration file not found: $CALIB" >&2
  exit 1
fi

mkdir -p "$RD/runs" "$RD/logs"

echo "=== Exp-3: INT8-ours cs=1 PPL (1.5B, 5 seeds) ==="
echo "GPU: $GPU_ID | CALIB: $CALIB"
echo "Start: $(date)"

for SEED in 1234 1235 1236 1237 1238; do
  echo ">>> seed=$SEED"
  # max_samples=100: ~100K tokens sufficient for PPL estimate.
  # Without this, cs=1 on full WikiText-2 (~1M tokens) takes ~26h/seed.
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL_ID" --kv_mode int8_ours \
    --calib_file "$CALIB" \
    --chunk_size 1 --max_length 1024 --max_samples 100 --seed "$SEED" \
    --save_csv --out_dir "$RD/runs/ppl_int8_cs1_1p5b_s${SEED}" \
    2>&1 | tee -a "$RD/logs/exp3_int8_cs1_1p5b.log"
done

echo ">>> Exp-3 1.5B ALL DONE: $(date)"
