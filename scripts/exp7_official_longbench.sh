#!/bin/bash
# Exp-7: Official LongBench evaluation (3 tasks, FP16 + INT8-ours)
# Uses local JSONL files (data.zip already unzipped)
# Usage: bash scripts/exp7_official_longbench.sh [GPU_ID]
set -euo pipefail
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
CALIB_INT8="artifacts/kv_calib_kl_selected_v3_quick.json"
LB_DATA="data/longbench_official/data"
RD="results/emnlp_defense_v1"

# Fail-fast checks
if [ ! -d "$LB_DATA" ]; then
  echo "FATAL: LongBench data dir not found: $LB_DATA" >&2
  echo "Run: unzip data.zip -d data/longbench_official/" >&2
  exit 1
fi
for task in narrativeqa hotpotqa gov_report; do
  if [ ! -f "$LB_DATA/${task}.jsonl" ]; then
    echo "FATAL: Missing $LB_DATA/${task}.jsonl" >&2
    exit 1
  fi
done

mkdir -p "$RD/runs" "$RD/logs"

echo "=== Exp-7: Official LongBench (JSONL source) ==="
echo "GPU: $GPU_ID | Tasks: narrativeqa,hotpotqa,gov_report"
echo "Start: $(date)"

# FP16 baseline
echo ">>> FP16 LongBench"
python3 scripts/eval_longbench.py \
  --model_id "$MODEL_ID" \
  --kv_mode fp16 --seed 1234 \
  --longbench_source jsonl \
  --longbench_dataset_path "$LB_DATA" \
  --longbench_tasks narrativeqa,hotpotqa,gov_report \
  --longbench_max_samples 50 \
  --save_csv --out_dir "$RD/runs/longbench_official_fp16_1p5b" \
  2>&1 | tee "$RD/logs/exp7_fp16.log"
echo ">>> FP16 done: $(date)"

# INT8-ours
echo ">>> INT8-ours LongBench"
if [ ! -f "$CALIB_INT8" ]; then
  echo "FATAL: INT8 calib not found: $CALIB_INT8" >&2
  exit 1
fi
python3 scripts/eval_longbench.py \
  --model_id "$MODEL_ID" \
  --kv_mode int8_ours \
  --calib_file "$CALIB_INT8" \
  --seed 1234 \
  --longbench_source jsonl \
  --longbench_dataset_path "$LB_DATA" \
  --longbench_tasks narrativeqa,hotpotqa,gov_report \
  --longbench_max_samples 50 \
  --save_csv --out_dir "$RD/runs/longbench_official_int8_1p5b" \
  2>&1 | tee "$RD/logs/exp7_int8.log"
echo ">>> INT8-ours done: $(date)"

echo ""
echo "=== Exp-7 ALL DONE: $(date) ==="
