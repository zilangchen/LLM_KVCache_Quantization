#!/bin/bash
# Phase 2.6 Wave 6: Qwen-3B k-scan runner
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

TASK="${1:-}"
[ -z "$TASK" ] && { echo "ERROR: 必须指定 task" >&2; exit 2; }

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-3B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c5_qwen3b"
POLICY_DIR="artifacts/allocator/sweep_3b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "uniform_int4_k4v4" "uniform_int8_k8v8"
    "bakv_k1" "heuristic_k1" "random3_k1_seed42"
    "bakv_k3" "heuristic_k3"
    "bakv_k5" "heuristic_k5" "random3_k5_seed42"
    "bakv_k7" "heuristic_k7"
)

echo "=== Wave 6 (Qwen-3B) task=$TASK @ $(date) ==="

for POLICY in "${POLICIES[@]}"; do
    RN="phase2c5_3b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
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
echo "=== Wave 6 task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows "Wave 6 task $TASK" "$OUT_DIR" "phase2c5_3b_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" "longbench_task_summary_*.csv" 12 "$TASK" "int4_mixed_kv"
