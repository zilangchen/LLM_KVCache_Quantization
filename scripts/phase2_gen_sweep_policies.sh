#!/bin/bash
# =============================================================================
# Phase 2 编号 7 M2 W2+W3: 生成 15 policy JSON
# =============================================================================
# 产出 (12 sweep + 3 ablation)：
#   artifacts/allocator/sweep/
#     bakv_k{1,3,5,7}.json       # top_k with --sensitivity_agg max
#     heuristic_k{1,3,5,7}.json  # 位置启发式等距
#     random3_k{1,3,5,7}_seed42.json  # random_k 负对照（统一 seed=42）
#   artifacts/allocator/ablation_sens/
#     bakv_max_k3.json           # 复制 ../bakv_top3.json (等价 agg=max k=3)
#     bakv_mean_k3.json          # 新，--sensitivity_agg mean
#     random_k3_seed42.json      # 复制 ../random3_seed42.json
#
# Codex 修订：ablation 中 random 走独立 random_k policy，不进 --sensitivity_agg
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

CALIB="artifacts/kv_calib_kl_selected_v2.json"
SWEEP_DIR="artifacts/allocator/sweep"
ABLATION_DIR="artifacts/allocator/ablation_sens"
BASE_DIR="artifacts/allocator"  # 编号 6 的 bakv_top3.json + random3_seed42.json 在这

mkdir -p "$SWEEP_DIR" "$ABLATION_DIR"

if [ ! -f "$CALIB" ]; then
    echo "ERROR: calib file missing: $CALIB"
    exit 2
fi

echo "=============================================="
echo "Phase 2 编号 7 M2: 生成 15 policy JSON"
echo "时间: $(date)"
echo "=============================================="

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"

# ----- Budget Sweep 12 policies -----
for K in 1 3 5 7; do
    $ALLOCATOR --policy top_k --k $K --sensitivity_agg max \
        --out "$SWEEP_DIR/bakv_k${K}.json"
    $ALLOCATOR --policy heuristic --k $K \
        --out "$SWEEP_DIR/heuristic_k${K}.json"
    $ALLOCATOR --policy random_k --k $K --seed 42 \
        --out "$SWEEP_DIR/random3_k${K}_seed42.json"
done

# ----- Uniform baselines (2026-04-18 修复 Bug A: batch2 runner 需要这两个) -----
# 历史原因: 编号 6 的 phase2_gen_policies.sh 把这些放在 artifacts/allocator/ 根目录;
# 编号 7/8 的 sweep-based runner 查 artifacts/allocator/sweep/ 时踩空导致 batch2
# uniform_int4 SKIP 4 个 task. 现在统一在 sweep/ 目录下也生成一份副本避免漏。
$ALLOCATOR --policy uniform --uniform_bits 4 4 \
    --out "$SWEEP_DIR/uniform_int4_k4v4.json"
$ALLOCATOR --policy uniform --uniform_bits 8 8 \
    --out "$SWEEP_DIR/uniform_int8_k8v8.json"

# ----- Ablation 1 sensitivity_agg 3 policies -----
# bakv_max_k3: 复用编号 6 的 bakv_top3.json（等价 --sensitivity_agg max --k 3）
if [ -f "$BASE_DIR/bakv_top3.json" ]; then
    cp "$BASE_DIR/bakv_top3.json" "$ABLATION_DIR/bakv_max_k3.json"
    echo "Copied $BASE_DIR/bakv_top3.json → $ABLATION_DIR/bakv_max_k3.json"
else
    $ALLOCATOR --policy top_k --k 3 --sensitivity_agg max \
        --out "$ABLATION_DIR/bakv_max_k3.json"
fi

# bakv_mean_k3: 新生成（--sensitivity_agg mean）
$ALLOCATOR --policy top_k --k 3 --sensitivity_agg mean \
    --out "$ABLATION_DIR/bakv_mean_k3.json"

# random_k3_seed42: 复用编号 6 的 random3_seed42.json（独立 random_k policy）
if [ -f "$BASE_DIR/random3_seed42.json" ]; then
    cp "$BASE_DIR/random3_seed42.json" "$ABLATION_DIR/random_k3_seed42.json"
    echo "Copied $BASE_DIR/random3_seed42.json → $ABLATION_DIR/random_k3_seed42.json"
else
    $ALLOCATOR --policy random_k --k 3 --seed 42 \
        --out "$ABLATION_DIR/random_k3_seed42.json"
fi

echo ""
echo "=== Sweep policies ==="
ls -la "$SWEEP_DIR/"
echo ""
echo "=== Ablation policies ==="
ls -la "$ABLATION_DIR/"

echo ""
echo "=== Summary (avg_bits + protected_layers) ==="
python3 - <<'PY'
import json, glob, os
for d in ["artifacts/allocator/sweep", "artifacts/allocator/ablation_sens"]:
    for f in sorted(glob.glob(f"{d}/*.json")):
        data = json.load(open(f))
        name = os.path.basename(f).replace(".json", "")
        print(f"  {name:40s} avg_bits={data.get('avg_bits'):.3f} "
              f"protected={data.get('protected_layers', '(uniform)')} "
              f"agg={data.get('sensitivity_agg', '-')}")
PY
