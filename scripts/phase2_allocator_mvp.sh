#!/bin/bash
# =============================================================================
# Phase 2 编号 6 M3: Layer-wise Allocator MVP 主实验
# =============================================================================
# 1.5B × 1 task × 5 allocator policies × n=50
# kv_mode 固定 int4_mixed_kv；5 policies 来自 artifacts/allocator/*.json
# run_name 含 policy 名，聚合时按 (task, kv_mode, policy_name) 区分
#
# 用法（3 GPU 并行按 task 拆分）:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_allocator_mvp.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_allocator_mvp.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_allocator_mvp.sh gov_report
#
# 预估：单任务 5 policies × ~2-3 min/policy = 10-15 min/GPU；3 GPU 并行 ≈ 15-20 min 总
# =============================================================================
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定任务名（narrativeqa / hotpotqa / gov_report）"
    exit 2
fi

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_allocator_mvp"
POLICY_DIR="artifacts/allocator"
mkdir -p "$OUT_DIR"
FAILED=0

# 5 policies 固定顺序（run_name 含 policy 名 → 聚合时区分实验组）
POLICIES=(
    "uniform_int4_k4v4"
    "uniform_int8_k8v8"
    "bakv_top3"
    "heuristic_top3"
    "random3_seed42"
)

echo "=============================================="
echo "Phase 2 编号 6 M3: allocator MVP 任务=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "Git commit: $(git rev-parse --short HEAD)"
echo "=============================================="

for POLICY in "${POLICIES[@]}"; do
    RUN_NAME="phase2_1p5b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
    MODE_LOG="$OUT_DIR/${RUN_NAME}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"

    if [ ! -f "$POLICY_JSON" ]; then
        echo "[$TASK/$POLICY] ERROR: policy JSON not found: $POLICY_JSON"
        FAILED=1
        continue
    fi

    echo ""
    echo "--- [$TASK/$POLICY] 启动 @ $(date +%H:%M:%S) ---"

    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --longbench_source jsonl \
        --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" \
        --longbench_max_samples $N_SAMPLES \
        --seed $SEED \
        --out_dir "$OUT_DIR" \
        --run_name "$RUN_NAME" \
        > "$MODE_LOG" 2>&1; then
        echo "[$TASK/$POLICY] DONE @ $(date +%H:%M:%S)"
        # Fix: grep -c returns 1 when no matches under pipefail+set -e; use || true
        eng_cnt=$(grep -c "ENG-045" "$MODE_LOG" 2>/dev/null || true)
        echo "  ENG-045 warnings: ${eng_cnt:-0}"
    else
        echo "[$TASK/$POLICY] FAILED, see $MODE_LOG"
        FAILED=1
    fi
done

echo ""
echo "=============================================="
echo "Phase 2 编号 6 M3 task $TASK 完成: $(date)"
find "$OUT_DIR" -maxdepth 1 -type f -name "*${TASK}*" | sort | head -10
echo "=============================================="

if [ "$FAILED" -ne 0 ]; then
    exit 3
fi
