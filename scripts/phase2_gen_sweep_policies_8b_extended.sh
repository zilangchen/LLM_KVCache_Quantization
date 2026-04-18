#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 1: 8B extended policy 生成（k=9/11 + mean_{3,5,7} + auto-k range）
# =============================================================================
# 新增到 artifacts/allocator/sweep_8b/：
#   bakv_k9.json, bakv_k11.json           (max agg 右侧扩展)
#   heuristic_k9.json, heuristic_k11.json (等距位置 L=32)
#   bakv_mean_k3.json, bakv_mean_k5.json, bakv_mean_k7.json  (mean agg 扩展)
#   bakv_auto_cov{70,80,90}_max.json      (coverage-based auto-k range proposer)
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

CALIB="artifacts/kv_calib_kl_llama31_8b_int8.json"
OUT_DIR="artifacts/allocator/sweep_8b"
mkdir -p "$OUT_DIR"

if [ ! -f "$CALIB" ]; then
    echo "FATAL: 8B calib file missing: $CALIB" >&2
    exit 2
fi

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

echo "=== Wave 1: 8B extended policy 生成 ==="
date

# max agg 扩展 k=9, 11
for K in 9 11; do
    $ALLOCATOR --policy top_k --k $K --sensitivity_agg max \
        --out "$OUT_DIR/bakv_k${K}.json"
    $ALLOCATOR --policy heuristic --k $K \
        --out "$OUT_DIR/heuristic_k${K}.json"
done

# mean agg 扩展 k=3, 5, 7（k=1 已有）
for K in 3 5 7; do
    $ALLOCATOR --policy top_k --k $K --sensitivity_agg mean \
        --out "$OUT_DIR/bakv_mean_k${K}.json"
done

# auto-k range proposer（70/80/90 coverage；80 作为推荐点）
for COV in 0.7 0.8 0.9; do
    TAG=$(python3 -c "print(int(round(float('$COV') * 100)))")
    $ALLOCATOR --policy auto_k_coverage --coverage "$COV" \
        --coverage_targets 0.7 0.8 0.9 --sensitivity_agg max \
        --out "$OUT_DIR/bakv_auto_cov${TAG}_max.json"
done

echo ""
echo "=== 新增 10 policies protected_layers 对比 ==="
python3 - <<'PYEOF'
import json, os
d = "artifacts/allocator/sweep_8b"
for name in ["bakv_k9", "bakv_k11", "heuristic_k9", "heuristic_k11",
             "bakv_mean_k3", "bakv_mean_k5", "bakv_mean_k7",
             "bakv_auto_cov70_max", "bakv_auto_cov80_max", "bakv_auto_cov90_max"]:
    try:
        data = json.load(open(f"{d}/{name}.json"))
        extra = ""
        if "selected_k" in data:
            extra = f" selected_k={data.get('selected_k')} candidate_ks={data.get('candidate_ks')}"
        print(f"  {name:20s} protected={data.get('protected_layers')} avg_bits={data.get('avg_bits'):.3f}{extra}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")
PYEOF
