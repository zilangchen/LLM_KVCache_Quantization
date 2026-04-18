#!/bin/bash
# =============================================================================
# 编号 8 (C2) LLaMA-3.1-8B Budget Sweep policy 生成
# =============================================================================
# 用 8B calib (artifacts/kv_calib_kl_llama31_8b_int8.json, num_layers=32) 生成 12 policy JSON：
#   sweep_8b/bakv_k{1,3,5,7}.json       (top_k with max sensitivity, 8B num_layers=32)
#   sweep_8b/heuristic_k{1,3,5,7}.json  (等距层 np.linspace(0, 31, k).round())
#   sweep_8b/random3_k{1,5}_seed42.json (只在 best-k 候选点补，省 GPU)
#   sweep_8b/uniform_int4_k4v4.json
#   sweep_8b/uniform_int8_k8v8.json
# 共 12 policies × 3 tasks = 36 runs
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
    echo "ERROR: 8B calib file missing: $CALIB"
    exit 2
fi

echo "=============================================="
echo "编号 8 (C2) LLaMA-3.1-8B policy 生成"
echo "时间: $(date) / CALIB: $CALIB"
echo "=============================================="

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

# BAKV + Heuristic × k∈{1,3,5,7}
for K in 1 3 5 7; do
    $ALLOCATOR --policy top_k --k $K --sensitivity_agg max \
        --out "$OUT_DIR/bakv_k${K}.json"
    $ALLOCATOR --policy heuristic --k $K \
        --out "$OUT_DIR/heuristic_k${K}.json"
done

# Random 只在 best-k 候选点补（k=1 和 k=5）
for K in 1 5; do
    $ALLOCATOR --policy random_k --k $K --seed 42 \
        --out "$OUT_DIR/random3_k${K}_seed42.json"
done

# Uniform 上下界
$ALLOCATOR --policy uniform --uniform_bits 4 4 \
    --out "$OUT_DIR/uniform_int4_k4v4.json"
$ALLOCATOR --policy uniform --uniform_bits 8 8 \
    --out "$OUT_DIR/uniform_int8_k8v8.json"

echo ""
echo "=== 12 policies (8B) 生成完成 ==="
ls -la "$OUT_DIR/"

echo ""
echo "=== 8B BAKV k=5 protected_layers（对比 7B [?,?,?,?,?] 和 1.5B [0,1,15]）==="
python3 -c "
import json
for k in [1, 3, 5, 7]:
    d = json.load(open(f'$OUT_DIR/bakv_k{k}.json'))
    print(f'  8B BAKV k={k} protected: {d.get(\"protected_layers\")} (avg_bits={d.get(\"avg_bits\"):.3f})')"
