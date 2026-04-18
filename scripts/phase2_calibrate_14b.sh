#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 4 Step A: Qwen-14B INT8 behavior calibration
# =============================================================================
# 用 calibrate_behavior.py 生成 14B 的 INT8 KL-divergence behavior calibration
# 用法: CUDA_VISIBLE_DEVICES=X bash scripts/phase2_calibrate_14b.sh
# 单 GPU ~30 min on H20
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

# 14B 在 modelscope_cache，用本地路径
MODEL="/root/autodl-tmp/modelscope_cache/qwen/Qwen2.5-14B-Instruct"
OUT_CALIB="artifacts/kv_calib_kl_qwen25_14b_int8.json"

if [ ! -d "$MODEL" ]; then
    echo "FATAL: 14B model path missing: $MODEL" >&2
    exit 2
fi

if [ -f "$OUT_CALIB" ]; then
    echo "SKIP: 14B calib already exists: $OUT_CALIB"
    exit 0
fi

echo "=== Wave 4 Step A: 14B INT8 calibration @ $(date) ==="
echo "Model: $MODEL"
echo "Output: $OUT_CALIB"

# B1 fix (2026-04-18, A scheme): use --calib_out (the real CLI flag)
# instead of --out (which argparse prefix-matched to --out_dir, causing
# default fallback 'artifacts/kv_calib_kl.json' to be overwritten across
# different model calibrations). Workaround block below is removed.
rm -rf "$OUT_CALIB" 2>/dev/null
python3 scripts/calibrate_behavior.py \
    --model_id "$MODEL" \
    --calib_out "$OUT_CALIB" \
    2>&1 | tail -30

if [ -f "$OUT_CALIB" ]; then
    echo "=== 14B calibration SUCCESS @ $(date) ==="
    ls -la "$OUT_CALIB"
else
    echo "=== 14B calibration FAILED @ $(date) ==="
    exit 3
fi
