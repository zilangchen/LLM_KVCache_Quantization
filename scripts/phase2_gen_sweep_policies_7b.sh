#!/bin/bash
# =============================================================================
# 编号 8 (C1) Qwen 7B Budget Sweep policy 生成
# =============================================================================
# 用 7B calib (artifacts/kv_calib_kl_qwen25_7b_int8.json) 生成 17 policy JSON：
#   sweep_7b/bakv_k{1,3,5,7}.json       (top_k with max sensitivity, 7B 敏感度)
#   sweep_7b/heuristic_k{1,3,5,7}.json  (等距层，layer 数与 1.5B 相同=28)
#   sweep_7b/random3_k{1,3,5,7}_seed42.json
#   sweep_7b/bakv_auto_cov{70,80,90}_max.json
#   sweep_7b/uniform_int4_k4v4.json
#   sweep_7b/uniform_int8_k8v8.json
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
    echo "ERROR: 7B calib file missing: $CALIB"
    exit 2
fi

echo "=============================================="
echo "编号 8 (C1) 7B policy 生成"
echo "时间: $(date) / CALIB: $CALIB"
echo "=============================================="

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

for K in 1 3 5 7; do
    $ALLOCATOR --policy top_k --k $K --sensitivity_agg max \
        --out "$OUT_DIR/bakv_k${K}.json"
    $ALLOCATOR --policy heuristic --k $K \
        --out "$OUT_DIR/heuristic_k${K}.json"
    $ALLOCATOR --policy random_k --k $K --seed 42 \
        --out "$OUT_DIR/random3_k${K}_seed42.json"
done

$ALLOCATOR --policy uniform --uniform_bits 4 4 \
    --out "$OUT_DIR/uniform_int4_k4v4.json"
$ALLOCATOR --policy uniform --uniform_bits 8 8 \
    --out "$OUT_DIR/uniform_int8_k8v8.json"

for COV in 0.7 0.8 0.9; do
    TAG=$(python3 -c "print(int(round(float('$COV') * 100)))")
    $ALLOCATOR --policy auto_k_coverage --coverage "$COV" \
        --coverage_targets 0.7 0.8 0.9 --sensitivity_agg max \
        --out "$OUT_DIR/bakv_auto_cov${TAG}_max.json"
done

echo ""
echo "=== 17 policies (7B) 生成完成 ==="
ls -la "$OUT_DIR/"

echo ""
echo "=== 7B sensitivity top-3（对比 1.5B 的 [0,1,15]）==="
python3 -c "
import json
d = json.load(open('$OUT_DIR/bakv_k3.json'))
print(f'  7B BAKV k=3 protected: {d.get(\"protected_layers\")} (avg_bits={d.get(\"avg_bits\")})')"
python3 -c "
import json
for cov in [70, 80, 90]:
    d = json.load(open(f'$OUT_DIR/bakv_auto_cov{cov}_max.json'))
    print(f'  7B auto_cov{cov}: protected={d.get(\"protected_layers\")} selected_k={d.get(\"selected_k\")} candidate_ks={d.get(\"candidate_ks\")}')"
