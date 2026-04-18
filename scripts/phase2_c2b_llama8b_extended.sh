#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 1: LLaMA-3.1-8B extended k-scan runner
# =============================================================================
# 每 GPU 跑 1 task × 10 configs = 10 runs
# 3 GPU × 3 tasks = 30 runs 总
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_c2b_llama8b_extended.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_c2b_llama8b_extended.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_c2b_llama8b_extended.sh gov_report
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

# LLaMA-8B: 强制 offline mode（hf-mirror 代理不稳）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="meta-llama/Llama-3.1-8B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c2b_llama8b_extended"
POLICY_DIR="artifacts/allocator/sweep_8b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "bakv_k9"
    "bakv_k11"
    "heuristic_k9"
    "heuristic_k11"
    "bakv_mean_k3"
    "bakv_mean_k5"
    "bakv_mean_k7"
    "bakv_auto_cov70_max"
    "bakv_auto_cov80_max"
    "bakv_auto_cov90_max"
)

echo "=== Wave 1 (8B extended) task=$TASK @ $(date) ==="

for POLICY in "${POLICIES[@]}"; do
    RN="phase2c2b_8b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
    LOG="$OUT_DIR/${RN}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"

    phase2_require_file "$POLICY_JSON" "policy"

    echo "--- [$RN] 启动 @ $(date +%H:%M:%S) ---"
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

echo ""
echo "=== Wave 1 task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows "Wave 1 task $TASK" "$OUT_DIR" "phase2c2b_8b_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" "longbench_task_summary_*.csv" 10 "$TASK" "int4_mixed_kv"
