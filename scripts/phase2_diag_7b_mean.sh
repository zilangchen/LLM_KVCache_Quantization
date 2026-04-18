#!/bin/bash
# =============================================================================
# Phase 2 编号 8 Diagnostic: 7B × BAKV mean aggregation × k={1,5} × 3 tasks
# =============================================================================
# 回答两个正交问题：
#   (1) k=1 BAKV max 失败（-22.7% vs Heur）是否 max aggregation 导致？
#   (2) k=5 BAKV max 甜点位（+3.6% vs Heur, 3/3 wins）是否对 aggregation 稳健？
#
# 用法（3 GPU 按 task 拆分）:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_diag_7b_mean.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_diag_7b_mean.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_diag_7b_mean.sh gov_report
#
# 每 GPU 2 runs × ~90s = ~3 min wall-clock
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

MODEL="Qwen/Qwen2.5-7B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_diag_7b_mean"
POLICY_DIR="artifacts/allocator/sweep_7b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "bakv_mean_k1"
    "bakv_mean_k5"
)

echo "=============================================="
echo "诊断 7B mean aggregation task=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

for POLICY in "${POLICIES[@]}"; do
    RUN_NAME="phase2diag_7b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
    MODE_LOG="$OUT_DIR/${RUN_NAME}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"

    if [ ! -f "$POLICY_JSON" ]; then
        echo "[$TASK/$POLICY] SKIP: policy JSON not found $POLICY_JSON"
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
        eng_cnt=$(grep -c "ENG-045" "$MODE_LOG" 2>/dev/null || true)
        echo "  ENG-045 warnings: ${eng_cnt:-0}"
    else
        echo "[$TASK/$POLICY] FAILED, see $MODE_LOG"
    fi
done

echo ""
echo "=============================================="
echo "诊断 task $TASK 完成: $(date)"
ls -la "$OUT_DIR/" | grep "$TASK" | head -6
echo "=============================================="
