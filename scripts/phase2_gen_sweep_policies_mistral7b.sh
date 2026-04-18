#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 5.2: Mistral-7B policy 生成（smoke 通过后）
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

CALIB="artifacts/kv_calib_kl_mistral7b_int8.json"
OUT_DIR="artifacts/allocator/sweep_mistral7b"
mkdir -p "$OUT_DIR"

if [ ! -f "$CALIB" ]; then
    echo "FATAL: Mistral-7B calib missing: $CALIB" >&2
    echo "  → 先跑 bash scripts/phase2_calibrate_mistral7b.sh（内部使用 --calib_out）" >&2
    exit 2
fi

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

for K in 1 3 5 7; do
    $ALLOCATOR --policy top_k --k $K --sensitivity_agg max --out "$OUT_DIR/bakv_k${K}.json"
    $ALLOCATOR --policy heuristic --k $K --out "$OUT_DIR/heuristic_k${K}.json"
done

for K in 1 5; do
    $ALLOCATOR --policy random_k --k $K --seed 42 --out "$OUT_DIR/random3_k${K}_seed42.json"
done

$ALLOCATOR --policy uniform --uniform_bits 4 4 --out "$OUT_DIR/uniform_int4_k4v4.json"
$ALLOCATOR --policy uniform --uniform_bits 8 8 --out "$OUT_DIR/uniform_int8_k8v8.json"

for COV in 0.7 0.8 0.9; do
    TAG=$(python3 -c "print(int(round(float('$COV') * 100)))")
    $ALLOCATOR --policy auto_k_coverage --coverage "$COV" \
        --coverage_targets 0.7 0.8 0.9 --sensitivity_agg max \
        --out "$OUT_DIR/bakv_auto_cov${TAG}_max.json"
done

echo ""
echo "=== Mistral-7B protected_layers overview ==="
python3 - <<'PYEOF'
import json
d = "artifacts/allocator/sweep_mistral7b"
for k in [1, 3, 5, 7]:
    data = json.load(open(f"{d}/bakv_k{k}.json"))
    print(f"  Mistral-7B bakv_k{k}: protected={data.get('protected_layers')} avg_bits={data.get('avg_bits'):.3f}")
for cov in [70, 80, 90]:
    data = json.load(open(f"{d}/bakv_auto_cov{cov}_max.json"))
    print(f"  Mistral-7B auto_cov{cov}: protected={data.get('protected_layers')} avg_bits={data.get('avg_bits'):.3f} selected_k={data.get('selected_k')}")
PYEOF
