#!/bin/bash
# =============================================================================
# Phase 2 编号 6 M2: 生成 5 组 policy JSON
# =============================================================================
# 用 behavior_aligned_allocator.py 统一生成：
#   1. uniform_int4_k4v4.json    — uniform INT4 baseline（下界参考）
#   2. uniform_int8_k8v8.json    — uniform INT8（上界参考）
#   3. bakv_top3.json            — BAKV Top-3（attention-KL top-3 保 INT8）
#   4. heuristic_top3.json       — 启发式 {0, L//2, L-1} 保 INT8（强对照）
#   5. random3_seed42.json       — Random-3（seed=42 负对照）
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

CALIB="artifacts/kv_calib_kl_selected_v2.json"
OUT_DIR="artifacts/allocator"
mkdir -p "$OUT_DIR"

if [ ! -f "$CALIB" ]; then
    echo "ERROR: calib file not found: $CALIB"
    exit 2
fi

echo "=============================================="
echo "Phase 2 编号 6 M2: policy JSON 生成"
echo "时间: $(date)"
echo "CALIB: $CALIB"
echo "OUT_DIR: $OUT_DIR"
echo "=============================================="

python3 scripts/adaptive/behavior_aligned_allocator.py \
    --calib "$CALIB" \
    --policy uniform --uniform_bits 4 4 \
    --out "$OUT_DIR/uniform_int4_k4v4.json"

python3 scripts/adaptive/behavior_aligned_allocator.py \
    --calib "$CALIB" \
    --policy uniform --uniform_bits 8 8 \
    --out "$OUT_DIR/uniform_int8_k8v8.json"

python3 scripts/adaptive/behavior_aligned_allocator.py \
    --calib "$CALIB" \
    --policy top_k --k 3 \
    --out "$OUT_DIR/bakv_top3.json"

python3 scripts/adaptive/behavior_aligned_allocator.py \
    --calib "$CALIB" \
    --policy heuristic --k 3 \
    --out "$OUT_DIR/heuristic_top3.json"

python3 scripts/adaptive/behavior_aligned_allocator.py \
    --calib "$CALIB" \
    --policy random_k --k 3 --seed 42 \
    --out "$OUT_DIR/random3_seed42.json"

echo ""
echo "=== 5 policies 生成完成 ==="
ls -la "$OUT_DIR/"

echo ""
echo "=== Avg bits + protected_layers 摘要 ==="
for f in "$OUT_DIR"/*.json; do
    name=$(basename "$f" .json)
    summary=$(python3 -c "
import json
d=json.load(open('$f'))
print(f\"avg_bits={d.get('avg_bits')} protected={d.get('protected_layers','(uniform)')}\")
")
    echo "  $name: $summary"
done
