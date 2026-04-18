#!/bin/bash
# Phase 2.6 Wave 6: Qwen-3B INT8 behavior calibration
# B1 fix (2026-04-18, A scheme): use --calib_out instead of --out
set -euo pipefail
if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-3B-Instruct"
OUT_CALIB="artifacts/kv_calib_kl_qwen25_3b_int8.json"

[ -f "$OUT_CALIB" ] && { echo "SKIP: already exists $OUT_CALIB"; exit 0; }

echo "=== Wave 6 Qwen-3B calibration @ $(date) ==="
rm -rf "$OUT_CALIB" 2>/dev/null
python3 scripts/calibrate_behavior.py --model_id "$MODEL" --calib_out "$OUT_CALIB" 2>&1 | tail -30

[ -f "$OUT_CALIB" ] && echo "SUCCESS: $OUT_CALIB" || { echo "FAILED"; exit 3; }
