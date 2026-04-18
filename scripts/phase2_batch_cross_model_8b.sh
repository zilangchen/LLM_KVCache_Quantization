#!/bin/bash
# =============================================================================
# 编号 8 C2: LLaMA-3.1-8B × k-scan（12 policies × 1 task × n=50）
# =============================================================================
# 每 GPU 按 task 拆分，循环 12 policies = 4 BAKV + 4 Heuristic + 2 Random + 2 Uniform
# run_name 前缀 phase2c2_8b_int4mixedkv_...
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_batch_cross_model_8b.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_batch_cross_model_8b.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_batch_cross_model_8b.sh gov_report
#
# 12 runs/GPU × ~5 min = ~60 min wall-clock（8B 比 7B 慢 25%）
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

# LLaMA-8B: 强制 offline mode（hf-mirror 代理不稳定，本地 cache 完整）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="meta-llama/Llama-3.1-8B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c2_llama8b"
POLICY_DIR="artifacts/allocator/sweep_8b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "uniform_int4_k4v4"
    "uniform_int8_k8v8"
    "bakv_k1" "heuristic_k1" "random3_k1_seed42"
    "bakv_k3" "heuristic_k3"
    "bakv_k5" "heuristic_k5" "random3_k5_seed42"
    "bakv_k7" "heuristic_k7"
)

echo "=============================================="
echo "编号 8 C2 (LLaMA-3.1-8B) k-scan task=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

for POLICY in "${POLICIES[@]}"; do
    RUN_NAME="phase2c2_8b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
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
echo "C2 LLaMA-8B task $TASK 完成: $(date)"
ls -la "$OUT_DIR/" | grep "$TASK" | head -15
echo "=============================================="
