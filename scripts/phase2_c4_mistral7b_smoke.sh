#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 5.1: Mistral-7B smoke check (fp16 + int8_ours × 3 tasks = 6 runs)
# =============================================================================
# 判断 Mistral-7B LongBench 是否 degenerate（历史有此问题）
# 若 smoke 通过（非全 0 / 非全相同 / 非异常 floor），允许 full sweep
# 用法: CUDA_VISIBLE_DEVICES=X bash scripts/phase2_c4_mistral7b_smoke.sh
# A scheme fix (2026-04-18):
#   - int8_ours 显式传 --calib_file 指向 Mistral-7B INT8 正确 calib
#   - 末尾强制校验 0 Traceback / 0 failed metric / 0 head-mismatch ValueError
#   - smoke 判读失败或 gate 失败则 exit 3，不放行 full sweep
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="mistralai/Mistral-7B-Instruct-v0.3"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c4_mistral7b/smoke"
CALIB_MISTRAL_INT8="artifacts/kv_calib_kl_mistral7b_int8.json"
mkdir -p "$OUT_DIR"

# Pre-flight: require explicit Mistral INT8 calib for int8_ours.
if [ ! -f "$CALIB_MISTRAL_INT8" ]; then
    echo "FATAL: Mistral-7B INT8 calib missing: $CALIB_MISTRAL_INT8" >&2
    exit 2
fi

echo "=== Wave 5.1 Mistral-7B smoke @ $(date) ==="
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "CALIB_MISTRAL_INT8: $CALIB_MISTRAL_INT8 ($(stat -c%s "$CALIB_MISTRAL_INT8") bytes)"

for KV_MODE in fp16 int8_ours; do
    CALIB_ARG=()
    if [ "$KV_MODE" = "int8_ours" ]; then
        CALIB_ARG=(--calib_file "$CALIB_MISTRAL_INT8")
    fi
    for TASK in narrativeqa hotpotqa gov_report; do
        RN="phase2c4smoke_mistral7b_${KV_MODE}_${TASK}_n${N_SAMPLES}"
        LOG="$OUT_DIR/${RN}.log"

        echo "--- [$RN] @ $(date +%H:%M:%S) ---"
        if python3 scripts/eval_longbench.py \
            --model_id "$MODEL" --kv_mode "$KV_MODE" \
            "${CALIB_ARG[@]}" \
            --longbench_source jsonl --longbench_dataset_path "$JSONL_DIR" \
            --longbench_tasks "$TASK" --longbench_max_samples $N_SAMPLES \
            --seed $SEED --out_dir "$OUT_DIR" --run_name "$RN" \
            > "$LOG" 2>&1; then
            echo "[$RN] DONE @ $(date +%H:%M:%S)"
        else
            echo "[$RN] FAILED, see $LOG" >&2
            tail -20 "$LOG" >&2
        fi
    done
done

# ============================================================================
# 最终校验 — 使用 phase2_gate_lib.sh（pipefail-safe）
# ============================================================================
source "$(dirname "$0")/phase2_gate_lib.sh"
phase2_gate_outputs "Wave 5.1" "$OUT_DIR" 'phase2c4smoke_*.log' 'longbench_task_summary_*.csv' 6 || exit 3

# 简单判据：看结果是否 degenerate
echo ""
echo "=== smoke 判读 ==="
python3 - <<PYEOF
import csv, glob, os
rows = []
for f in glob.glob("$OUT_DIR/longbench_task_summary_*.csv"):
    for r in csv.DictReader(open(f)):
        rows.append(r)
if not rows:
    print("FAIL: no task_summary CSV produced")
    exit(1)
scores = [float(r.get('official_metric_value', 0) or 0) for r in rows]
print(f"  {len(rows)} rows, scores: {[f'{s:.3f}' for s in scores]}")
unique = set(scores)
if all(s == 0 for s in scores):
    print("DEGENERATE: all scores = 0 → ABORT full sweep")
    raise SystemExit(3)
elif all(abs(s - 1.0) < 0.01 for s in scores):
    print("DEGENERATE: all scores ≈ 1.0 → ABORT full sweep")
    raise SystemExit(3)
elif len(unique) == 1:
    print(f"DEGENERATE: all scores identical ({list(unique)[0]}) → ABORT full sweep")
    raise SystemExit(3)
else:
    print("OK: scores diverse → full sweep allowed")
PYEOF

echo "[Wave 5.1] GATE PASS — ready for Mistral full sweep approval"
echo "=== smoke done @ $(date) ==="
