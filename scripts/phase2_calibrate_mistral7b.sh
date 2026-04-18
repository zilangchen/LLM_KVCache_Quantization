#!/bin/bash
# Phase 2.6 Wave 5 Step B: Mistral-7B INT8 behavior calibration
set -euo pipefail
if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache

cd /root/LLM_KVCache_Quantization

MODEL="mistralai/Mistral-7B-Instruct-v0.3"
OUT_CALIB="artifacts/kv_calib_kl_mistral7b_int8.json"

[ -f "$OUT_CALIB" ] && { echo "SKIP: already exists $OUT_CALIB"; exit 0; }

echo "=== Wave 5 Mistral-7B calibration @ $(date) ==="
# B1 fix (2026-04-18, A scheme): use --calib_out (the real CLI flag) instead
# of --out (argparse prefix-match to --out_dir, default fallback overwrite).
rm -rf "$OUT_CALIB" 2>/dev/null
python3 scripts/calibrate_behavior.py --model_id "$MODEL" --calib_out "$OUT_CALIB" 2>&1 | tail -30

[ -f "$OUT_CALIB" ] && echo "SUCCESS: $OUT_CALIB" || { echo "FAILED"; exit 3; }
