#!/bin/bash
# =============================================================================
# L2 v1: K/V asymmetric allocator minimal runner
# =============================================================================
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_l2_kv_asymmetric.sh 7b narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_l2_kv_asymmetric.sh 8b hotpotqa
#
# 说明:
# - 保持 int4_mixed_kv 执行路径不变
# - 默认比较四组 policy:
#   uniform_int4_k4v4 / bakv_k3 / bakv_auto_cov80_max / kv_asym_avgbits5p0
# - 若缺失 policy，则在 L2 policy 目录中按当前 model 的 calibration 自动生成
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

MODEL_KEY="${1:-}"
TASK="${2:-}"

if [ -z "$MODEL_KEY" ] || [ -z "$TASK" ]; then
    echo "Usage: bash scripts/phase2_l2_kv_asymmetric.sh {1p5b|7b|8b} {narrativeqa|hotpotqa|gov_report}" >&2
    exit 2
fi

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
TARGET_AVG_BITS="${L2_KV_ASYM_TARGET_AVG_BITS:-5.0}"
K_BIAS="${L2_KV_ASYM_K_BIAS:-1.15}"
V_BIAS="${L2_KV_ASYM_V_BIAS:-1.0}"

case "$MODEL_KEY" in
    1p5b)
        MODEL="Qwen/Qwen2.5-1.5B-Instruct"
        CALIB="artifacts/kv_calib_kl_selected_v2.json"
        MODEL_TAG="1p5b"
        ;;
    7b)
        MODEL="Qwen/Qwen2.5-7B-Instruct"
        CALIB="artifacts/kv_calib_kl_qwen25_7b_int8.json"
        MODEL_TAG="7b"
        ;;
    8b)
        MODEL="meta-llama/Llama-3.1-8B-Instruct"
        CALIB="artifacts/kv_calib_kl_llama31_8b_int8.json"
        MODEL_TAG="8b"
        ;;
    *)
        echo "ERROR: unsupported MODEL_KEY=$MODEL_KEY" >&2
        exit 2
        ;;
esac

POLICY_DIR="artifacts/allocator/l2_kv_asymmetric/${MODEL_TAG}"
OUT_DIR="results/l2_kv_asymmetric/${MODEL_TAG}/${TASK}"
mkdir -p "$POLICY_DIR" "$OUT_DIR"

UNIFORM_JSON="$POLICY_DIR/uniform_int4_k4v4.json"
LAYERWISE_JSON="$POLICY_DIR/bakv_k3.json"
AUTOK_JSON="$POLICY_DIR/bakv_auto_cov80_max.json"
KV_ASYM_JSON="$POLICY_DIR/kv_asym_avgbits5p0.json"

ALLOCATOR="python3 scripts/adaptive/behavior_aligned_allocator.py --calib $CALIB"
KV_EXPORTER="python3 scripts/adaptive/export_kv_asymmetric_policy.py --calib_file $CALIB --budget_mode avg_bits --budget_value $TARGET_AVG_BITS --k_bias $K_BIAS --v_bias $V_BIAS --out $KV_ASYM_JSON"

phase2_require_file "$CALIB" "calibration"

if [ ! -f "$UNIFORM_JSON" ]; then
    $ALLOCATOR --policy uniform --uniform_bits 4 4 --out "$UNIFORM_JSON"
fi
if [ ! -f "$LAYERWISE_JSON" ]; then
    $ALLOCATOR --policy top_k --k 3 --sensitivity_agg max --out "$LAYERWISE_JSON"
fi
if [ ! -f "$AUTOK_JSON" ]; then
    $ALLOCATOR --policy auto_k_coverage --coverage 0.8 --coverage_targets 0.7 0.8 0.9 \
        --sensitivity_agg max --out "$AUTOK_JSON"
fi
if [ ! -f "$KV_ASYM_JSON" ]; then
    bash -lc "$KV_EXPORTER"
fi

declare -a POLICIES=(
    "uniform_int4_k4v4:$UNIFORM_JSON"
    "bakv_k3:$LAYERWISE_JSON"
    "bakv_auto_cov80_max:$AUTOK_JSON"
    "kv_asym_avgbits5p0:$KV_ASYM_JSON"
)

echo "=== L2 K/V asymmetric task=$TASK model=$MODEL_TAG @ $(date) ==="

for ENTRY in "${POLICIES[@]}"; do
    POLICY_NAME="${ENTRY%%:*}"
    POLICY_JSON="${ENTRY#*:}"
    RN="l2kvasym_${MODEL_TAG}_int4mixedkv_${POLICY_NAME}_${TASK}_n${N_SAMPLES}"
    LOG="$OUT_DIR/${RN}.log"
    phase2_require_file "$POLICY_JSON" "policy"

    echo "--- [$RN] @ $(date +%H:%M:%S) ---"
    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --longbench_source jsonl \
        --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" \
        --longbench_max_samples "$N_SAMPLES" \
        --seed "$SEED" \
        --out_dir "$OUT_DIR" \
        --run_name "$RN" \
        > "$LOG" 2>&1; then
        echo "[$RN] DONE @ $(date +%H:%M:%S)"
    else
        phase2_fail_from_log "$RN" "$LOG"
    fi
done

echo "=== L2 K/V asymmetric task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows \
    "L2 K/V asymmetric ${MODEL_TAG} task $TASK" \
    "$OUT_DIR" \
    "l2kvasym_${MODEL_TAG}_int4mixedkv_*_${TASK}_n${N_SAMPLES}.log" \
    "longbench_task_summary_*.csv" \
    4 \
    "$TASK" \
    "int4_mixed_kv"
