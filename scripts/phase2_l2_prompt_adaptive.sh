#!/bin/bash
# =============================================================================
# L2 v1: Prompt-adaptive allocation MVP runner
# =============================================================================
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_l2_prompt_adaptive.sh 8b narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_l2_prompt_adaptive.sh 7b dureader
#
# 说明:
# - 只做 task/profile bucket selector
# - 默认比较:
#   global_fixed_k / global_auto_k / prompt_adaptive
# - runner 会自动构建 policy_pool.json 与 selector.json（若不存在）
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

MODEL_KEY="${1:-}"
TASK="${2:-}"
PROFILE_BUCKET="${3:-default}"

if [ -z "$MODEL_KEY" ] || [ -z "$TASK" ]; then
    echo "Usage: bash scripts/phase2_l2_prompt_adaptive.sh {1p5b|7b|8b} {task} [profile_bucket]" >&2
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

case "$MODEL_KEY" in
    1p5b)
        MODEL="Qwen/Qwen2.5-1.5B-Instruct"
        ;;
    7b)
        MODEL="Qwen/Qwen2.5-7B-Instruct"
        ;;
    8b)
        MODEL="meta-llama/Llama-3.1-8B-Instruct"
        ;;
    *)
        echo "ERROR: unsupported MODEL_KEY=$MODEL_KEY" >&2
        exit 2
        ;;
esac

SELECTOR_DIR="artifacts/allocator/l2_prompt_adaptive/${MODEL_KEY}"
OUT_DIR="results/l2_prompt_adaptive/${MODEL_KEY}/${TASK}"
POOL_JSON="${SELECTOR_DIR}/policy_pool.json"
SELECTOR_JSON="${SELECTOR_DIR}/selector.json"
mkdir -p "$SELECTOR_DIR" "$OUT_DIR"

if [ ! -f "$POOL_JSON" ]; then
    python3 scripts/adaptive/build_prompt_policy_pool.py \
        --model_key "$MODEL_KEY" \
        --out "$POOL_JSON"
fi

if [ ! -f "$SELECTOR_JSON" ]; then
    python3 scripts/adaptive/export_prompt_selector.py \
        --policy_pool "$POOL_JSON" \
        --default_policy auto_k \
        --out "$SELECTOR_JSON"
fi

FIXED_JSON="$(python3 - "$POOL_JSON" <<'PY'
import json, sys
pool = json.load(open(sys.argv[1], encoding="utf-8"))
for item in pool["policies"]:
    if item["policy_id"] == "fixed_k":
        print(item["policy_json"])
        break
else:
    raise SystemExit("missing fixed_k in pool")
PY
)"

AUTOK_JSON="$(python3 - "$POOL_JSON" <<'PY'
import json, sys
pool = json.load(open(sys.argv[1], encoding="utf-8"))
for item in pool["policies"]:
    if item["policy_id"] == "auto_k":
        print(item["policy_json"])
        break
else:
    raise SystemExit("missing auto_k in pool")
PY
)"

PROMPT_JSON="$(python3 - "$SELECTOR_JSON" "$TASK" "$PROFILE_BUCKET" <<'PY'
import json, sys
from scripts.adaptive.export_prompt_selector import resolve_policy_entry

selector = json.load(open(sys.argv[1], encoding="utf-8"))
entry = resolve_policy_entry(selector, task_id=sys.argv[2], profile_bucket=sys.argv[3])
print(entry["policy_json"])
PY
)"

python3 - "$OUT_DIR/prompt_selector_resolution.json" "$SELECTOR_JSON" "$TASK" "$PROFILE_BUCKET" "$PROMPT_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "selector_json": sys.argv[2],
    "task_id": sys.argv[3],
    "profile_bucket": sys.argv[4],
    "resolved_policy_json": sys.argv[5],
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
PY

declare -a VARIANTS=(
    "global_fixed_k:$FIXED_JSON"
    "global_auto_k:$AUTOK_JSON"
    "prompt_adaptive:$PROMPT_JSON"
)

echo "=== L2 Prompt-adaptive task=$TASK model=$MODEL_KEY bucket=$PROFILE_BUCKET @ $(date) ==="

for ENTRY in "${VARIANTS[@]}"; do
    VARIANT="${ENTRY%%:*}"
    POLICY_JSON="${ENTRY#*:}"
    phase2_require_file "$POLICY_JSON" "policy"
    RN="l2prompt_${MODEL_KEY}_${VARIANT}_${TASK}_n${N_SAMPLES}"
    LOG="$OUT_DIR/${RN}.log"
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
        echo "[$RN] DONE"
    else
        phase2_fail_from_log "$RN" "$LOG"
    fi
done

echo "=== L2 Prompt-adaptive task $TASK 完成 @ $(date) ==="
phase2_gate_task_rows \
    "L2 Prompt-adaptive ${MODEL_KEY} task $TASK" \
    "$OUT_DIR" \
    "l2prompt_${MODEL_KEY}_*_${TASK}_n${N_SAMPLES}.log" \
    "longbench_task_summary_*.csv" \
    3 \
    "$TASK" \
    "int4_mixed_kv"
