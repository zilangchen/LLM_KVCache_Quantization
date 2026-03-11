#!/usr/bin/env bash
# INT4 Rescue — Tier 2 Wave 1: Float32 Scale Chain Validation
# ENG-066: Re-run INT4 baseline + rescued configs with float32 scale fix.
# Expected GPU time: ~6-10h total (1.5B ~1h, 7B ~3h, 8B ~3h)
set -euo pipefail

PROJ="/root/LLM_KVCache_Quantization"
cd "$PROJ"
export PYTHONPATH="$PROJ"

OUT="results/int4_t2_float32_v1"
mkdir -p "$OUT/runs" "$OUT/logs" "$OUT/tables"

echo "=========================================="
echo "INT4 Tier 2 Wave 1 — Float32 Scale Chain"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# -------------------------------------------------------------------
# Step 1: Qwen2.5-1.5B (eval_ppl + eval_needle)
# Config: T0-C (adaptive=false, temp=false)
# -------------------------------------------------------------------
echo ""
echo "[Step 1/3] Qwen2.5-1.5B — baseline + rescue (noadapt_notemp)"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_ppl,eval_needle \
  --run_names "int4_baseline_long,int4_rescue_noadapt_notemp_long" \
  --seeds "1234,1235,1236" \
  --run_tag "t2_float32_1p5b" \
  --out_dir "$OUT/runs" \
  --logs_dir "$OUT/logs" \
  --failure_policy continue_all \
  2>&1 | tee "$OUT/logs/step1_1p5b.log"

echo "[Step 1/3] Qwen2.5-1.5B DONE: $(date '+%Y-%m-%d %H:%M:%S')"

# -------------------------------------------------------------------
# Step 2: Qwen2.5-7B (eval_ppl only)
# Config: T0-B (adaptive=true, temp=false)
# -------------------------------------------------------------------
echo ""
echo "[Step 2/3] Qwen2.5-7B — baseline + rescue (adaptive_notemp)"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

python scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_qwen25_7b_int4_rescue_v1.yaml \
  --tasks eval_ppl \
  --run_names "int4_baseline_long,int4_rescue_adaptive_notemp_long" \
  --seeds "1234,1235,1236" \
  --run_tag "t2_float32_7b" \
  --out_dir "$OUT/runs" \
  --logs_dir "$OUT/logs" \
  --failure_policy continue_all \
  2>&1 | tee "$OUT/logs/step2_7b.log"

echo "[Step 2/3] Qwen2.5-7B DONE: $(date '+%Y-%m-%d %H:%M:%S')"

# -------------------------------------------------------------------
# Step 3: LLaMA-3.1-8B (eval_ppl + eval_needle)
# Config: T0-B (adaptive=true, temp=false)
# -------------------------------------------------------------------
echo ""
echo "[Step 3/3] LLaMA-3.1-8B — baseline + rescue (adaptive_notemp)"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

python scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_llama31_8b_int4_rescue_v1.yaml \
  --tasks eval_ppl,eval_needle \
  --run_names "int4_baseline_long,int4_rescue_adaptive_notemp_long" \
  --seeds "1234,1235,1236" \
  --run_tag "t2_float32_8b" \
  --out_dir "$OUT/runs" \
  --logs_dir "$OUT/logs" \
  --failure_policy continue_all \
  2>&1 | tee "$OUT/logs/step3_8b.log"

echo "[Step 3/3] LLaMA-3.1-8B DONE: $(date '+%Y-%m-%d %H:%M:%S')"

# -------------------------------------------------------------------
# Step 4: Aggregate results
# -------------------------------------------------------------------
echo ""
echo "[Step 4/4] Aggregating results..."

python scripts/aggregate_results.py \
  --runs_dir "$OUT/runs" \
  --tables_dir "$OUT/tables" \
  2>&1 | tee "$OUT/logs/step4_aggregate.log"

echo ""
echo "=========================================="
echo "INT4 Tier 2 Wave 1 COMPLETE"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Results: $OUT/"
echo "=========================================="
