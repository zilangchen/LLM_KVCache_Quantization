#!/bin/bash
# =============================================================================
# L2 Phase C wrapper: loop 3 core tasks for one model_key
# =============================================================================
# 专为 Phase C tmux 启动设计, 避免 SSH 三层 quoting 嵌套:
#   tmux new -d -s l2c_<model> "CUDA_VISIBLE_DEVICES=N bash scripts/phase2_l2c_one.sh <model> | tee /tmp/l2c_<model>.log"
#
# 内部按顺序跑:
#   narrativeqa -> hotpotqa -> gov_report
# 每个 task 由 phase2_l2_prompt_adaptive.sh 内部跑 3 variants:
#   global_fixed_k / global_auto_k / prompt_adaptive
# 即单个 session 共 9 quality runs.
#
# 不使用 set -e 以便某 task 失败不阻断后续 task (Phase C 是 exploratory gate,
# 允许 partial signal).
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
        echo "ERROR: unsupported MODEL_KEY=$MODEL_KEY (runner supports {1p5b,7b,8b})" >&2
        exit 2
        ;;
esac

cd /root/LLM_KVCache_Quantization 2>/dev/null || true

echo "=== L2 Phase C session MODEL=$MODEL_KEY start=$(date '+%H:%M:%S') ==="

for t in narrativeqa hotpotqa gov_report; do
    echo ">>> [$MODEL_KEY] task=$t start=$(date '+%H:%M:%S')"
    bash scripts/phase2_l2_prompt_adaptive.sh "$MODEL_KEY" "$t"
    rc=$?
    echo ">>> [$MODEL_KEY] task=$t exit=$rc end=$(date '+%H:%M:%S')"
done

echo "=== L2 Phase C session MODEL=$MODEL_KEY end=$(date '+%H:%M:%S') ==="
