#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 3: 7B random multi-seed policy 生成
# =============================================================================
# 新增到 artifacts/allocator/sweep_7b/：
#   random3_k1_seed{123,2024,3407,8888}.json
#   random3_k5_seed{123,2024,3407,8888}.json
# 共 8 个新 policy（k=1 seed=42 和 k=5 seed=42 已存在，不重生成）
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

CALIB="artifacts/kv_calib_kl_qwen25_7b_int8.json"
OUT_DIR="artifacts/allocator/sweep_7b"
mkdir -p "$OUT_DIR"

if [ ! -f "$CALIB" ]; then
    echo "FATAL: 7B calib file missing: $CALIB" >&2
    exit 2
fi

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

echo "=== Wave 3: 7B random multi-seed 生成 ==="

for K in 1 5; do
    for SEED in 123 2024 3407 8888; do
        OUT="$OUT_DIR/random3_k${K}_seed${SEED}.json"
        if [ -f "$OUT" ]; then
            echo "SKIP existing: $OUT"
            continue
        fi
        $ALLOCATOR --policy random_k --k $K --seed $SEED --out "$OUT"
    done
done

echo ""
echo "=== 新增 random policies list ==="
ls -la "$OUT_DIR"/random3_k{1,5}_seed{123,2024,3407,8888}.json 2>&1 | head -10
