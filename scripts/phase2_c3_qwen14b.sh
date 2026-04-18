#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 4: Qwen-14B minimal k-scan runner
# =============================================================================
# 15 configs × 1 task × n=50（含 auto-k range）
# 用法: CUDA_VISIBLE_DEVICES=X bash scripts/phase2_c3_qwen14b.sh {narrativeqa|hotpotqa|gov_report}
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定 task" >&2
    exit 2
fi

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

# offline mode（兜底 hf-mirror 不稳）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

# 14B 在 modelscope_cache，直接用本地路径（2026-04-18 14:55 用户修正）
MODEL="/root/autodl-tmp/modelscope_cache/qwen/Qwen2.5-14B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c3_qwen14b"
POLICY_DIR="artifacts/allocator/sweep_14b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "uniform_int4_k4v4" "uniform_int8_k8v8"
    "bakv_k1" "heuristic_k1" "random3_k1_seed42"
    "bakv_k3" "heuristic_k3"
    "bakv_k5" "heuristic_k5" "random3_k5_seed42"
    "bakv_k7" "heuristic_k7"
    "bakv_auto_cov70_max" "bakv_auto_cov80_max" "bakv_auto_cov90_max"
)

echo "=== Wave 4 (Qwen-14B) task=$TASK @ $(date) ==="

for POLICY in "${POLICIES[@]}"; do
    RN="phase2c3_14b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
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

echo "=== Wave 4 task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows "Wave 4 task $TASK" "$OUT_DIR" "phase2c3_14b_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" "longbench_task_summary_*.csv" 15 "$TASK" "int4_mixed_kv"
