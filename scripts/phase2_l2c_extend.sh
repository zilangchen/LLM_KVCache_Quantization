#!/bin/bash
# =============================================================================
# L2 Phase C extend (generic): <model_key> × {dureader, lcc}
# =============================================================================
# 用法:
#   bash scripts/phase2_l2c_extend.sh {1p5b|7b|8b}
#
# 每次跑 2 task × 3 variants = 6 quality runs (runner 内部 loop 3 variants).
#
# 8b 已有专用 wrapper phase2_l2c_extend_8b.sh 正在跑；此通用版用于并行补
# 1p5b / 7b extend tasks (标记为 off-protocol exploratory).
# =============================================================================
set -uo pipefail

MODEL_KEY="${1:-}"
if [ -z "$MODEL_KEY" ]; then
    echo "Usage: $0 {1p5b|7b|8b}" >&2
    exit 2
fi

case "$MODEL_KEY" in
    1p5b|7b|8b) ;;
    *)
        echo "ERROR: unsupported MODEL_KEY=$MODEL_KEY" >&2
        exit 2
        ;;
esac

cd /root/LLM_KVCache_Quantization 2>/dev/null || true

echo "=== L2 Phase C extend MODEL=$MODEL_KEY start=$(date '+%H:%M:%S') ==="

for t in dureader lcc; do
    echo ">>> [$MODEL_KEY] task=$t start=$(date '+%H:%M:%S')"
    bash scripts/phase2_l2_prompt_adaptive.sh "$MODEL_KEY" "$t"
    rc=$?
    echo ">>> [$MODEL_KEY] task=$t exit=$rc end=$(date '+%H:%M:%S')"
done

echo "=== L2 Phase C extend MODEL=$MODEL_KEY end=$(date '+%H:%M:%S') ==="
