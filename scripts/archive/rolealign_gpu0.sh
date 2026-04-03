#!/bin/bash
# GPU 0: Role-Aware Asymmetric calibration + smoke test (v5.2)
# Phase 1: Calibrate (role_aware_axes) → ~20 min
# Phase 2: M4.2 ours_asym smoke test (Needle + LongBench on 1.5B)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization

# Enable network for HF model download
source /etc/network_turbo 2>/dev/null || true

echo "=========================================="
echo "GPU 0 | v5.2 RoleAlign Pipeline"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

RESULTS_DIR="results/emnlp_rolealign_v1"
CALIB_OUT="artifacts/kv_calib_rolealign_1p5b.json"
mkdir -p "$RESULTS_DIR/runs" "$RESULTS_DIR/tables" "$RESULTS_DIR/logs"

# ============================================================
# Phase 1: Role-Aware Calibration (per-channel K + per-token V axes)
# ============================================================
echo ""
echo ">>> Phase 1: Role-Aware Calibration (1.5B)"
echo ">>> Start: $(date '+%H:%M:%S')"

python3 scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --role_aware_axes \
  --quant_bits 4 \
  --samples 16 \
  --seq_len 512 \
  --seed 1234 \
  --loss_function kl \
  --calib_out "$CALIB_OUT" \
  --out_dir "$RESULTS_DIR/calibration_1p5b" \
  --inv_tau_candidates "0.5,0.7,0.85,1.0,1.2,1.5,2.0" \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --v_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  2>&1 | tee "$RESULTS_DIR/logs/calibrate_rolealign_1p5b.log"

echo ">>> Phase 1 done: $(date '+%H:%M:%S')"
echo ">>> Calibration JSON: $CALIB_OUT"
ls -la "$CALIB_OUT"

# ============================================================
# Phase 2: M4.2 Smoke Test — int4_ours_asym (Needle + LongBench)
# ============================================================
echo ""
echo ">>> Phase 2: M4.2 ours_asym smoke test (1.5B, seed=1234)"
echo ">>> Start: $(date '+%H:%M:%S')"

# 2a. Needle evaluation — int4_ours_asym (4 context lengths × 20 depths each)
for CTX in 4096 8192 16384 32704; do
  echo "--- Needle: int4_ours_asym ctx=${CTX} ---"
  python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_ours_asym \
    --quant_bits 4 \
    --calib_file "$CALIB_OUT" \
    --context_len "$CTX" \
    --num_depths 20 \
    --seed 1234 \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/int4_ours_asym_1p5b_needle_s1234" \
    2>&1 | tee -a "$RESULTS_DIR/logs/needle_ours_asym_1p5b_s1234.log"
done

# 2b. LongBench evaluation — int4_ours_asym
echo "--- LongBench: int4_ours_asym ---"
python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym \
  --quant_bits 4 \
  --calib_file "$CALIB_OUT" \
  --seed 1234 \
  --gen_len 64 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/int4_ours_asym_1p5b_longbench_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/longbench_ours_asym_1p5b_s1234.log"

# 2c. Needle — int4_ours (symmetric reference, for comparison)
echo "--- Needle: int4_ours (sym reference) ctx=32704 ---"
python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours \
  --quant_bits 4 \
  --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
  --use_static_scales \
  --use_attn_temperature \
  --context_len 32704 \
  --num_depths 20 \
  --seed 1234 \
  --gen_len 64 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/int4_ours_sym_1p5b_needle_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/needle_ours_sym_1p5b_s1234.log"

echo ""
echo "=========================================="
echo "GPU 0 | All phases DONE"
echo "End: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
