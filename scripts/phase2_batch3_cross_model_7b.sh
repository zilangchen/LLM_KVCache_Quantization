#!/bin/bash
# =============================================================================
# 验证版第三批 C1: Qwen 7B × 编号 8 完整矩阵（14 policies × 1 task × n=50）
# =============================================================================
# 每 GPU 按 task 拆分，循环 14 policies = 12 sweep (4k × 3 allocator) + 2 uniform
# run_name 前缀 phase2c1_7b_int4mixedkv_...
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_batch3_cross_model_7b.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_batch3_cross_model_7b.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_batch3_cross_model_7b.sh gov_report
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
OUT_DIR="results/phase2_batch3_cross_model_7b"
POLICY_DIR="artifacts/allocator/sweep_7b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "uniform_int4_k4v4"
    "uniform_int8_k8v8"
    "bakv_k1" "heuristic_k1" "random3_k1_seed42"
    "bakv_k3" "heuristic_k3" "random3_k3_seed42"
    "bakv_k5" "heuristic_k5" "random3_k5_seed42"
    "bakv_k7" "heuristic_k7" "random3_k7_seed42"
)

echo "=============================================="
echo "验证版 第三批 C1 (Qwen 7B) task=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

for POLICY in "${POLICIES[@]}"; do
    RUN_NAME="phase2c1_7b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
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
echo "第三批 C1 task $TASK 完成: $(date)"
ls -la "$OUT_DIR/" | grep "$TASK" | head -15
echo "=============================================="
