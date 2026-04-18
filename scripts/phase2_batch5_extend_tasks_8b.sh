#!/bin/bash
# Phase 2.6 Wave 7: 8B extend tasks (4 new tasks × 9 configs)
# 第 2 个参数是 8B best_k (from Wave 1 结果)
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

TASK="${1:-}"
BEST_K="${2:-}"
[ -z "$TASK" ] && { echo "ERROR: arg1 task (dureader/vcsum/trec/lcc)" >&2; exit 2; }
[ -z "$BEST_K" ] && { echo "ERROR: arg2 best_k (e.g. 7 or 9)" >&2; exit 2; }

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="meta-llama/Llama-3.1-8B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_batch5_extend_tasks_8b"
POLICY_DIR="artifacts/allocator/sweep_8b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "uniform_int4_k4v4"
    "uniform_int8_k8v8"
    "bakv_k1"
    "bakv_mean_k1"
    "bakv_k${BEST_K}"
    "heuristic_k1"
    "heuristic_k${BEST_K}"
    "random3_k1_seed42"
    "random3_k${BEST_K}_seed42"
)

echo "=== Wave 7 (8B extend tasks) task=$TASK best_k=$BEST_K @ $(date) ==="

# 如果 sweep_8b 里缺 bakv_mean_k1，先生成
if [ ! -f "$POLICY_DIR/bakv_mean_k1.json" ]; then
    echo "生成缺失 bakv_mean_k1"
    CALIB_8B="artifacts/kv_calib_kl_llama31_8b_int8.json"
    phase2_require_file "$CALIB_8B" "8B calib"
    python3 scripts/adaptive/behavior_aligned_allocator.py \
        --calib "$CALIB_8B" --policy top_k --k 1 --sensitivity_agg mean \
        --out "$POLICY_DIR/bakv_mean_k1.json"
fi

# 如果 sweep_8b 里缺 random3_k${BEST_K}_seed42，先生成
if [ ! -f "$POLICY_DIR/random3_k${BEST_K}_seed42.json" ]; then
    echo "生成缺失 random3_k${BEST_K}_seed42"
    CALIB_8B="artifacts/kv_calib_kl_llama31_8b_int8.json"
    phase2_require_file "$CALIB_8B" "8B calib"
    python3 scripts/adaptive/behavior_aligned_allocator.py \
        --calib "$CALIB_8B" --policy random_k --k $BEST_K --seed 42 \
        --out "$POLICY_DIR/random3_k${BEST_K}_seed42.json"
fi

for POLICY in "${POLICIES[@]}"; do
    RN="phase2b5_8b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
    LOG="$OUT_DIR/${RN}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"

    phase2_require_file "$POLICY_JSON" "policy"

    echo "--- [$RN] @ $(date +%H:%M:%S) ---"
    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --longbench_source jsonl --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" --longbench_max_samples $N_SAMPLES \
        --seed $SEED --out_dir "$OUT_DIR" --run_name "$RN" \
        > "$LOG" 2>&1; then
        echo "[$RN] DONE @ $(date +%H:%M:%S)"
    else
        phase2_fail_from_log "$RN" "$LOG"
    fi
done
echo "=== Wave 7 task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows "Wave 7b task $TASK" "$OUT_DIR" "phase2b5_8b_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" "longbench_task_summary_*.csv" 9 "$TASK" "int4_mixed_kv"
