#!/bin/bash
# =============================================================================
# L2 Phase C extend: 8B × {dureader, lcc} (official protocol補齊)
# =============================================================================
# 原始 phase2_l2c_one.sh 内部硬編碼 narrativeqa/hotpotqa/gov_report；
# 本 wrapper 專用於補齊官方 Prompt-adaptive 矩陣 (8B × 5 tasks) 中缺失的
# dureader 與 lcc 兩個 extend task，保留既有 3 core task 不重跑。
# =============================================================================
set -uo pipefail

cd /root/LLM_KVCache_Quantization 2>/dev/null || true

MODEL_KEY="8b"

echo "=== L2 Phase C extend 8B start=$(date '+%H:%M:%S') ==="

for t in dureader lcc; do
    echo ">>> [$MODEL_KEY] task=$t start=$(date '+%H:%M:%S')"
    bash scripts/phase2_l2_prompt_adaptive.sh "$MODEL_KEY" "$t"
    rc=$?
    echo ">>> [$MODEL_KEY] task=$t exit=$rc end=$(date '+%H:%M:%S')"
done

echo "=== L2 Phase C extend 8B end=$(date '+%H:%M:%S') ==="
