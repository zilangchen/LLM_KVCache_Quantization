#!/usr/bin/env bash
# INT4 Rescue Plan — Tier 1: Calibration Strategy Comparison
# Purpose: Generate 3 calibration files (MSE, Percentile, KL re-gen) for 1.5B,
#          then run experiments comparing them.
# Expected GPU time: ~3h calibration + ~30min experiments
set -euo pipefail

PROJ="/root/LLM_KVCache_Quantization"
cd "$PROJ"

# Enable academic network proxy for HuggingFace access on AutoDL
source /etc/network_turbo 2>/dev/null || true

LOG_DIR="results/int4_rescue/logs"
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "INT4 Rescue Tier 1 — Calibration Comparison"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ============================================================
# Phase 1: Generate 3 calibration files
# ============================================================

echo ""
echo ">>> [Phase 1/2] Generating calibration files..."
echo ""

# --- 1a. MSE calibration ---
echo ">>> [1a/3] MSE calibration..."
python scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --quant_bits 4 \
  --int4_search \
  --loss_function mse \
  --search \
  --search_group_sizes "16" \
  --search_clip_percentiles "99.0,99.5,99.9,100.0" \
  --search_outlier_ratios "0,0.0025,0.005,0.01" \
  --search_objective robust \
  --group_size_k 16 \
  --group_size_v 16 \
  --seed 1234 \
  --calib_out artifacts/kv_calib_mse_int4_v4_g16.json \
  2>&1 | tee "$LOG_DIR/tier1_calib_mse.log"

echo ">>> [1a] MSE calibration DONE: $(date '+%H:%M:%S')"
echo ""

# --- 1b. Percentile calibration (no --search, pure statistics) ---
echo ">>> [1b/3] Percentile calibration..."
python scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --quant_bits 4 \
  --loss_function mse \
  --group_size_k 16 \
  --group_size_v 16 \
  --clip_percentile_k 99.5 \
  --clip_percentile_v 99.5 \
  --seed 1234 \
  --calib_out artifacts/kv_calib_pctl_int4_v4_g16.json \
  2>&1 | tee "$LOG_DIR/tier1_calib_pctl.log"

echo ">>> [1b] Percentile calibration DONE: $(date '+%H:%M:%S')"
echo ""

# --- 1c. KL re-gen with robust search ---
echo ">>> [1c/3] KL re-gen calibration..."
python scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --quant_bits 4 \
  --int4_search \
  --loss_function kl \
  --search \
  --search_group_sizes "16" \
  --search_clip_percentiles "99.0,99.5,99.9,100.0" \
  --search_outlier_ratios "0,0.0025,0.005,0.01" \
  --search_objective robust \
  --inv_tau_candidates "0.5,0.7,0.85,1.0,1.2,1.5,2.0" \
  --group_size_k 16 \
  --group_size_v 16 \
  --seed 1234 \
  --calib_out artifacts/kv_calib_kl_int4_v4_g16.json \
  2>&1 | tee "$LOG_DIR/tier1_calib_kl.log"

echo ">>> [1c] KL re-gen calibration DONE: $(date '+%H:%M:%S')"
echo ""

# Verify all calibration files exist
echo ">>> Verifying calibration files..."
for f in artifacts/kv_calib_mse_int4_v4_g16.json \
         artifacts/kv_calib_pctl_int4_v4_g16.json \
         artifacts/kv_calib_kl_int4_v4_g16.json; do
  if [ -f "$f" ]; then
    echo "  OK: $f ($(wc -c < "$f") bytes)"
  else
    echo "  MISSING: $f — aborting experiments"
    exit 1
  fi
done
echo ""

# ============================================================
# Phase 2: Run comparison experiments (1.5B, PPL + Needle)
# ============================================================

echo ">>> [Phase 2/2] Running Tier 1 experiments..."
echo ""

# Also include T0-C (noadapt_notemp) as the baseline for comparison
# T0-C used the existing calib file (kv_calib_kl_int4_selected.json)
# Tier 1 entries use the newly generated calib files
python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_ppl,eval_needle \
  --run_names "int4_rescue_kl_v4_long,int4_rescue_mse_v4_long,int4_rescue_pctl_v4_long" \
  --seeds "1234" \
  --run_tag "t1_calib_compare" \
  --out_dir results/int4_rescue/runs \
  --logs_dir results/int4_rescue/logs \
  --failure_policy continue_all \
  --subprocess_timeout 3600 \
  2>&1 | tee "$LOG_DIR/tier1_experiments.log"

echo ""
echo "=========================================="
echo "Tier 1 Complete: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Quick results summary
echo ""
echo ">>> Quick PPL results summary:"
for d in results/int4_rescue/runs/int4_rescue_*_v4_long_s1234_t1_calib_compare; do
  if [ -d "$d" ]; then
    run=$(basename "$d")
    ppl_file="$d/eval_ppl_results.csv"
    if [ -f "$ppl_file" ]; then
      echo "  $run:"
      # Extract 32K PPL value
      grep "32704\|32768" "$ppl_file" | head -3
    fi
  fi
done

echo ""
echo ">>> Tier 0 reference (T0-C noadapt_notemp): PPL=22.04"
echo ">>> int4_baseline reference: PPL=19.54"
echo ""
echo "All results in: results/int4_rescue/runs/"
echo "Logs in: $LOG_DIR/"
