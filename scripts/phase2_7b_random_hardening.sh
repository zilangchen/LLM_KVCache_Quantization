#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 3: 7B random hardening runner
# =============================================================================
# 每 GPU 跑 1 task × 8 configs = 8 runs
# 3 GPU × 3 tasks = 24 runs 总，wall-clock ~40 min
#
# 用法:
#   CUDA_VISIBLE_DEVICES=X bash scripts/phase2_7b_random_hardening.sh {narrativeqa|hotpotqa|gov_report}
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定 task" >&2
    exit 2
fi

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
OUT_DIR="results/phase2_7b_random_hardening"
POLICY_DIR="artifacts/allocator/sweep_7b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "random3_k1_seed123" "random3_k1_seed2024" "random3_k1_seed3407" "random3_k1_seed8888"
    "random3_k5_seed123" "random3_k5_seed2024" "random3_k5_seed3407" "random3_k5_seed8888"
)

echo "=== Wave 3 (7B random hardening) task=$TASK @ $(date) ==="

for POLICY in "${POLICIES[@]}"; do
    RN="phase27b_random_7b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
    LOG="$OUT_DIR/${RN}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"

    phase2_require_file "$POLICY_JSON" "policy"

    echo "--- [$RN] @ $(date +%H:%M:%S) ---"
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
        --run_name "$RN" \
        > "$LOG" 2>&1; then
        echo "[$RN] DONE @ $(date +%H:%M:%S)"
        eng_cnt=$(grep -c "ENG-045" "$LOG" 2>/dev/null || true)
        echo "  ENG-045: ${eng_cnt:-0}"
    else
        phase2_fail_from_log "$RN" "$LOG"
    fi
done

echo "=== Wave 3 task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows "Wave 3 task $TASK" "$OUT_DIR" "phase27b_random_7b_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" "longbench_task_summary_*.csv" 8 "$TASK" "int4_mixed_kv"
