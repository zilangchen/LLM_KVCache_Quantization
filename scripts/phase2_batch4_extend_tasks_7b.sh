#!/bin/bash
# Phase 2.6 Wave 7: 7B extend tasks (4 new tasks × 8 configs)
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

TASK="${1:-}"
[ -z "$TASK" ] && { echo "ERROR: task 必填（dureader/vcsum/trec/lcc）" >&2; exit 2; }

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-7B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_batch4_extend_tasks_7b"
POLICY_DIR="artifacts/allocator/sweep_7b"
mkdir -p "$OUT_DIR"

# 7B 用 best=k5 max (Phase 2.5 已确认) + k=1 mean (rescue) + 对照
POLICIES=(
    "uniform_int4_k4v4"
    "uniform_int8_k8v8"
    "bakv_mean_k1"
    "bakv_k5"
    "heuristic_k1"
    "heuristic_k5"
    "random3_k1_seed42"
    "random3_k5_seed42"
)

# 注意: 7B sweep_7b 里没有 bakv_mean_k1 —— 需要先生成（若缺）
if [ ! -f "$POLICY_DIR/bakv_mean_k1.json" ]; then
    echo "生成缺失的 7B bakv_mean_k1"
    CALIB_7B="artifacts/kv_calib_kl_qwen25_7b_int8.json"
    phase2_require_file "$CALIB_7B" "7B calib"
    python3 scripts/adaptive/behavior_aligned_allocator.py \
        --calib "$CALIB_7B" --policy top_k --k 1 --sensitivity_agg mean \
        --out "$POLICY_DIR/bakv_mean_k1.json"
fi

echo "=== Wave 7 (7B extend tasks) task=$TASK @ $(date) ==="

for POLICY in "${POLICIES[@]}"; do
    RN="phase2b4_7b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
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
phase2_gate_task_rows "Wave 7a task $TASK" "$OUT_DIR" "phase2b4_7b_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" "longbench_task_summary_*.csv" 8 "$TASK" "int4_mixed_kv"
