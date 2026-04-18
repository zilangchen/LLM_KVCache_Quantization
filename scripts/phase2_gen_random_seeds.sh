#!/bin/bash
# =============================================================================
# 验证版 Pre-0: 生成 8 个额外 random-k policies（for 第一批 A1/A2 + 第二批 B+）
# =============================================================================
# k ∈ {1, 3} × seed ∈ {123, 2024, 3407, 8888} = 8 new policies
# seed=42 已有（sweep/random3_k{1,3}_seed42.json 来自编号 7 M2）
# 目的：多 Random-k seed 验证 "BAKV > Random" 不是单 seed 偶然
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization
CALIB="artifacts/kv_calib_kl_selected_v2.json"
OUT_DIR="artifacts/allocator/sweep"
mkdir -p "$OUT_DIR"

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

echo "=============================================="
echo "验证版 Pre-0: 8 random-k seeds 生成"
echo "时间: $(date)"
echo "=============================================="

for K in 1 3; do
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
echo "=== 所有 random-k seed policies ==="
ls -la "$OUT_DIR"/random3_k*_seed*.json | head -12
