#!/bin/bash
# GPU 0: 7B Role-Aware calibration + full evaluation (v5.2)
# Phase 1: Calibrate role_aware_axes for 7B (~40 min)
# Phase 2: ours_asym 7B eval (Needle 32K + LongBench + PPL, 3 seeds)
# Phase 3: kivi_style INT4 7B PPL (reference)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "=========================================="
echo "GPU 0 | v5.2 7B RoleAlign Pipeline"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

RESULTS_DIR="results/emnlp_rolealign_v1"
CALIB_OUT="artifacts/kv_calib_rolealign_7b.json"
MODEL_ID="Qwen/Qwen2.5-7B-Instruct"
mkdir -p "$RESULTS_DIR/runs" "$RESULTS_DIR/logs"

# ============================================================
# Phase 1: Role-Aware Calibration for 7B
# ============================================================
echo ">>> Phase 1: Role-Aware Calibration (7B)"
echo ">>> Start: $(date '+%H:%M:%S')"

python3 scripts/calibrate_behavior.py \
  --model_id "$MODEL_ID" \
  --role_aware_axes \
  --quant_bits 4 \
  --samples 16 \
  --seq_len 512 \
  --seed 1234 \
  --loss_function kl \
  --calib_out "$CALIB_OUT" \
  --out_dir "$RESULTS_DIR/calibration_7b" \
  --inv_tau_candidates "0.5,0.7,0.85,1.0,1.2,1.5,2.0" \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --v_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  2>&1 | tee "$RESULTS_DIR/logs/calibrate_rolealign_7b.log"

echo ">>> Phase 1 done: $(date '+%H:%M:%S')"
ls -la "$CALIB_OUT"

# ============================================================
# Phase 2: ours_asym 7B (3 seeds × Needle 32K + LongBench + PPL)
# ============================================================
for SEED in 1234 1235 1236; do
  echo ""
  echo ">>> 7B ours_asym seed=${SEED} — Needle 32K"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL_ID" \
    --kv_mode int4_ours_asym \
    --quant_bits 4 \
    --calib_file "$CALIB_OUT" \
    --context_len 32704 \
    --num_depths 20 \
    --seed $SEED \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/int4_ours_asym_7b_needle_s${SEED}" \
    2>&1 | tee -a "$RESULTS_DIR/logs/needle_ours_asym_7b_s${SEED}.log"

  echo ">>> 7B ours_asym seed=${SEED} — LongBench"
  python3 scripts/eval_longbench.py \
    --model_id "$MODEL_ID" \
    --kv_mode int4_ours_asym \
    --quant_bits 4 \
    --calib_file "$CALIB_OUT" \
    --seed $SEED \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/int4_ours_asym_7b_longbench_s${SEED}" \
    2>&1 | tee "$RESULTS_DIR/logs/longbench_ours_asym_7b_s${SEED}.log"
done

# PPL (single seed)
echo ">>> 7B ours_asym PPL (seed=1234)"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_ours_asym \
  --quant_bits 4 \
  --calib_file "$CALIB_OUT" \
  --seed 1234 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/int4_ours_asym_7b_ppl_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/ppl_ours_asym_7b_s1234.log"

# ============================================================
# Phase 3: kivi_style INT4 7B PPL (reference)
# ============================================================
echo ">>> 7B kivi_style PPL (seed=1234)"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode kivi_style \
  --quant_bits 4 \
  --seed 1234 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/kivi_style_7b_ppl_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/ppl_kivi_7b_s1234.log"

# FP16 PPL reference
echo ">>> 7B fp16 PPL (seed=1234)"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode fp16 \
  --seed 1234 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/fp16_7b_ppl_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/ppl_fp16_7b_s1234.log"

echo ""
echo "=========================================="
echo "GPU 0 | 7B Pipeline DONE: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
