#!/bin/bash
# =============================================================================
# Phase 2.6 Wave 2: TREC/VCSUM floor sanity check (A scheme rerun, 2026-04-18)
# =============================================================================
# 判断 trec/vcsum 的 0.0 是 1.5B+INT4 floor 还是评测/配置问题
# 用 fp16 (无量化) + int8_ours (中等精度) 对比
#
# 4 runs total: 2 kv_mode × 2 tasks（用户批准口径）
# 用法: bash scripts/phase2_trec_vcsum_sanity.sh
#   (单 GPU 即可，不需要参数；~5 min)
#
# A scheme fix (2026-04-18):
#   - int8_ours 显式传 --calib_file 指向 1.5B INT8 正确 calib（B1c 已禁 default fallback）
#   - HF_HUB_OFFLINE=1 + HF_HOME 避免 hf-mirror 代理不稳
#   - 末尾强制校验 0 Traceback / 0 failed metric / 0 head-mismatch ValueError
#     不通过则 exit 3，不放行后续 wave
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_trec_vcsum_sanity"
CALIB_1P5B_INT8="artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json"
mkdir -p "$OUT_DIR"

# Pre-flight: require 1.5B INT8 calib (B1c禁 default fallback 后必须显式提供)
if [ ! -f "$CALIB_1P5B_INT8" ]; then
    echo "FATAL: 1.5B INT8 calib missing: $CALIB_1P5B_INT8" >&2
    exit 2
fi

echo "=== Wave 2: TREC/VCSUM floor sanity @ $(date) ==="
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "CALIB_1P5B_INT8: $CALIB_1P5B_INT8 ($(stat -c%s "$CALIB_1P5B_INT8") bytes)"

for KV_MODE in fp16 int8_ours; do
    CALIB_ARG=()
    if [ "$KV_MODE" = "int8_ours" ]; then
        CALIB_ARG=(--calib_file "$CALIB_1P5B_INT8")
    fi
    for TASK in trec vcsum; do
        RN="phase2sanity_1p5b_${KV_MODE}_${TASK}_n${N_SAMPLES}"
        LOG="$OUT_DIR/${RN}.log"

        echo "--- [$RN] @ $(date +%H:%M:%S) ---"
        if python3 scripts/eval_longbench.py \
            --model_id "$MODEL" \
            --kv_mode "$KV_MODE" \
            "${CALIB_ARG[@]}" \
            --longbench_source jsonl \
            --longbench_dataset_path "$JSONL_DIR" \
            --longbench_tasks "$TASK" \
            --longbench_max_samples $N_SAMPLES \
            --seed $SEED \
            --out_dir "$OUT_DIR" \
            --run_name "$RN" \
            > "$LOG" 2>&1; then
            echo "[$RN] DONE @ $(date +%H:%M:%S)"
            # Fix 2026-04-18: grep pattern must accept underscore in kv_mode
            # (e.g., int8_ours). Old `[^_]+` excluded underscore → pipefail
            # triggered set -e abort → subsequent runs skipped.
            # `|| true` belt-and-suspenders for any future non-matching case.
            CSV=$(grep -oE 'longbench_task_summary_[A-Za-z0-9_]+_[0-9T:.\-]+\.csv' "$LOG" 2>/dev/null | head -1 || true)
            [ -n "$CSV" ] && echo "  metric_row: $(tail -1 "$OUT_DIR/$CSV" 2>/dev/null | cut -d, -f10,11)"
        else
            echo "[$RN] FAILED, see $LOG" >&2
            tail -20 "$LOG" >&2
        fi
    done
done

echo "=== Wave 2 完成（运行阶段）@ $(date) ==="

# ============================================================================
# 最终校验 — 使用 phase2_gate_lib.sh（pipefail-safe，避免 grep|wc 陷阱）
# ============================================================================
source "$(dirname "$0")/phase2_gate_lib.sh"
phase2_gate_outputs "Wave 2" "$OUT_DIR" 'phase2sanity_*.log' 'longbench_task_summary_*.csv' 4 || exit 3
echo "[Wave 2] ready for Mistral smoke approval"
