#!/bin/bash
# =============================================================================
# L2 v1: Quality-Cost Pareto runner
# =============================================================================
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_l2_pareto_eval.sh 7b
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_l2_pareto_eval.sh 8b "uniform_int4_k4v4,bakv_k11,bakv_auto_cov80_max"
#
# 默认策略集:
#   7b        -> uniform_int4_k4v4,heuristic_k3,bakv_k3,bakv_auto_cov80_max
#   8b        -> uniform_int4_k4v4,heuristic_k11,bakv_k11,bakv_auto_cov80_max
#   mistral7b -> uniform_int4_k4v4,heuristic_k3,bakv_k3,bakv_auto_cov80_max
#
# 若 role-aware candidate 已存在且设置 INCLUDE_ROLE_AWARE=1，则会追加比较。
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

MODEL_KEY="${1:-}"
POLICY_LIST="${2:-}"

if [ -z "$MODEL_KEY" ]; then
    echo "Usage: bash scripts/phase2_l2_pareto_eval.sh {7b|8b|mistral7b} [policy_csv]" >&2
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

LONG_TASKS_DEFAULT=(narrativeqa hotpotqa gov_report)
EXTRA_TASKS_DEFAULT=()
if [ -n "${L2_PARETO_EXTRA_TASKS:-}" ]; then
    IFS=',' read -r -a EXTRA_TASKS_DEFAULT <<<"${L2_PARETO_EXTRA_TASKS}"
fi

LAT_SEQ_LEN="${L2_PARETO_LAT_SEQ_LEN:-1024}"
LAT_GEN_LEN="${L2_PARETO_LAT_GEN_LEN:-128}"
PPL_MAX_LENGTH="${L2_PARETO_PPL_MAX_LENGTH:-1024}"
PPL_TARGET_TOKENS="${L2_PARETO_PPL_TARGET_TOKENS:-4096}"
NEEDLE_CONTEXT_LEN="${L2_PARETO_NEEDLE_CONTEXT_LEN:-4096}"
NEEDLE_DEPTHS="${L2_PARETO_NEEDLE_DEPTHS:-5}"
NEEDLE_MAX_NEW_TOKENS="${L2_PARETO_NEEDLE_MAX_NEW_TOKENS:-32}"
LONG_N_SAMPLES="${L2_PARETO_LONG_N_SAMPLES:-50}"
SEED="${L2_PARETO_SEED:-1234}"

case "$MODEL_KEY" in
    7b)
        MODEL="Qwen/Qwen2.5-7B-Instruct"
        CALIB="artifacts/kv_calib_kl_qwen25_7b_int8.json"
        POLICY_DIR="artifacts/allocator/sweep_7b"
        DEFAULT_POLICIES="uniform_int4_k4v4,heuristic_k3,bakv_k3,bakv_auto_cov80_max"
        ROLE_AWARE_JSON="artifacts/allocator/l2_kv_asymmetric/7b/kv_asym_avgbits5p0.json"
        ;;
    8b)
        MODEL="meta-llama/Llama-3.1-8B-Instruct"
        CALIB="artifacts/kv_calib_kl_llama31_8b_int8.json"
        POLICY_DIR="artifacts/allocator/sweep_8b"
        DEFAULT_POLICIES="uniform_int4_k4v4,heuristic_k11,bakv_k11,bakv_auto_cov80_max"
        ROLE_AWARE_JSON="artifacts/allocator/l2_kv_asymmetric/8b/kv_asym_avgbits5p0.json"
        ;;
    mistral7b)
        MODEL="mistralai/Mistral-7B-Instruct-v0.3"
        CALIB="artifacts/kv_calib_kl_mistral7b_int8.json"
        POLICY_DIR="artifacts/allocator/sweep_mistral7b"
        DEFAULT_POLICIES="uniform_int4_k4v4,heuristic_k3,bakv_k3,bakv_auto_cov80_max"
        ROLE_AWARE_JSON="artifacts/allocator/l2_kv_asymmetric/mistral7b/kv_asym_avgbits5p0.json"
        ;;
    *)
        echo "ERROR: unsupported MODEL_KEY=$MODEL_KEY" >&2
        exit 2
        ;;
esac

phase2_require_file "$CALIB" "calibration"
phase2_require_dir "$POLICY_DIR" "policy_dir"

if [ -z "$POLICY_LIST" ]; then
    POLICY_LIST="$DEFAULT_POLICIES"
fi
if [ "${INCLUDE_ROLE_AWARE:-0}" = "1" ] && [ -f "$ROLE_AWARE_JSON" ]; then
    POLICY_LIST="${POLICY_LIST},role_aware"
fi

RAW_BASE="results/l2_pareto/raw/${MODEL_KEY}"
mkdir -p "$RAW_BASE"

policy_json_for() {
    local policy_name="$1"
    if [ "$policy_name" = "role_aware" ]; then
        echo "$ROLE_AWARE_JSON"
    else
        echo "$POLICY_DIR/${policy_name}.json"
    fi
}

policy_avg_bits() {
    python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
with path.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("avg_bits", ""))
PY
}

for POLICY in ${POLICY_LIST//,/ }; do
    POLICY_JSON="$(policy_json_for "$POLICY")"
    phase2_require_file "$POLICY_JSON" "policy"

    POLICY_OUT_DIR="${RAW_BASE}/${POLICY}"
    mkdir -p "$POLICY_OUT_DIR"
    POLICY_AVG_BITS="$(policy_avg_bits "$POLICY_JSON")"

    python3 - "$POLICY_OUT_DIR/manifest.json" "$MODEL_KEY" "$MODEL" "$POLICY" "$POLICY_JSON" "$POLICY_AVG_BITS" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
payload = {
    "model_key": sys.argv[2],
    "model_id": sys.argv[3],
    "policy_id": sys.argv[4],
    "policy_json": sys.argv[5],
    "avg_bits": float(sys.argv[6]) if sys.argv[6] else None,
}
out.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
PY

    echo "=== Pareto eval model=$MODEL_KEY policy=$POLICY @ $(date) ==="

    for TASK in "${LONG_TASKS_DEFAULT[@]}"; do
        RN="l2pareto_${MODEL_KEY}_${POLICY}_${TASK}_quality"
        LOG="${POLICY_OUT_DIR}/${RN}.log"
        if python3 scripts/eval_longbench.py \
            --model_id "$MODEL" \
            --kv_mode int4_mixed_kv \
            --policy_json "$POLICY_JSON" \
            --longbench_source jsonl \
            --longbench_dataset_path /root/autodl-tmp/longbench_data/data \
            --longbench_tasks "$TASK" \
            --longbench_max_samples "$LONG_N_SAMPLES" \
            --seed "$SEED" \
            --out_dir "$POLICY_OUT_DIR" \
            --run_name "$RN" \
            > "$LOG" 2>&1; then
            echo "  [quality:$TASK] DONE"
        else
            phase2_fail_from_log "$RN" "$LOG"
        fi
    done

    for TASK in "${EXTRA_TASKS_DEFAULT[@]}"; do
        [ -z "$TASK" ] && continue
        RN="l2pareto_${MODEL_KEY}_${POLICY}_${TASK}_quality"
        LOG="${POLICY_OUT_DIR}/${RN}.log"
        if python3 scripts/eval_longbench.py \
            --model_id "$MODEL" \
            --kv_mode int4_mixed_kv \
            --policy_json "$POLICY_JSON" \
            --longbench_source jsonl \
            --longbench_dataset_path /root/autodl-tmp/longbench_data/data \
            --longbench_tasks "$TASK" \
            --longbench_max_samples "$LONG_N_SAMPLES" \
            --seed "$SEED" \
            --out_dir "$POLICY_OUT_DIR" \
            --run_name "$RN" \
            > "$LOG" 2>&1; then
            echo "  [quality:$TASK] DONE"
        else
            phase2_fail_from_log "$RN" "$LOG"
        fi
    done

    python3 scripts/profile_latency.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --calib_file "$CALIB" \
        --seq_len "$LAT_SEQ_LEN" \
        --gen_len "$LAT_GEN_LEN" \
        --runs 1 \
        --warmup 1 \
        --seed "$SEED" \
        --out_dir "$POLICY_OUT_DIR" \
        --run_name "l2pareto_${MODEL_KEY}_${POLICY}_latency" \
        > "${POLICY_OUT_DIR}/l2pareto_${MODEL_KEY}_${POLICY}_latency.log" 2>&1

    python3 scripts/profile_memory.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --calib_file "$CALIB" \
        --seq_len "$LAT_SEQ_LEN" \
        --gen_len "$LAT_GEN_LEN" \
        --runs 1 \
        --warmup 1 \
        --seed "$SEED" \
        --out_dir "$POLICY_OUT_DIR" \
        --run_name "l2pareto_${MODEL_KEY}_${POLICY}_memory" \
        > "${POLICY_OUT_DIR}/l2pareto_${MODEL_KEY}_${POLICY}_memory.log" 2>&1

    python3 scripts/eval_ppl.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --calib_file "$CALIB" \
        --dataset wikitext2 \
        --max_length "$PPL_MAX_LENGTH" \
        --target_tokens "$PPL_TARGET_TOKENS" \
        --seed "$SEED" \
        --out_dir "$POLICY_OUT_DIR" \
        --run_name "l2pareto_${MODEL_KEY}_${POLICY}_ppl" \
        > "${POLICY_OUT_DIR}/l2pareto_${MODEL_KEY}_${POLICY}_ppl.log" 2>&1

    python3 scripts/eval_needle.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --calib_file "$CALIB" \
        --context_len "$NEEDLE_CONTEXT_LEN" \
        --num_depths "$NEEDLE_DEPTHS" \
        --needle_max_new_tokens "$NEEDLE_MAX_NEW_TOKENS" \
        --seed "$SEED" \
        --out_dir "$POLICY_OUT_DIR" \
        --run_name "l2pareto_${MODEL_KEY}_${POLICY}_needle" \
        > "${POLICY_OUT_DIR}/l2pareto_${MODEL_KEY}_${POLICY}_needle.log" 2>&1
done

echo "=== L2 Pareto raw runs ready under $RAW_BASE @ $(date) ==="
