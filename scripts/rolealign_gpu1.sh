#!/bin/bash
# GPU 1: M3.5 Feasibility Probe — kivi_style INT4 + int4_kivi_aligned (v5.2)
# Purpose: Zero-code-change probe to check if asymmetric direction has signal
set -euo pipefail
export CUDA_VISIBLE_DEVICES=1
cd /root/LLM_KVCache_Quantization

# Enable network for HF model download
source /etc/network_turbo 2>/dev/null || true

echo "=========================================="
echo "GPU 1 | v5.2 M3.5 Feasibility Probe"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

RESULTS_DIR="results/emnlp_rolealign_v1"
mkdir -p "$RESULTS_DIR/runs" "$RESULTS_DIR/logs"

# ============================================================
# Probe 1: kivi_style INT4 — Needle (4 context lengths)
# ============================================================
echo ""
echo ">>> Probe 1: kivi_style INT4 Needle (1.5B, seed=1234)"
echo ">>> Start: $(date '+%H:%M:%S')"

for CTX in 4096 8192 16384 32704; do
  echo "--- Needle: kivi_style INT4 ctx=${CTX} ---"
  python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode kivi_style \
    --quant_bits 4 \
    --context_len "$CTX" \
    --num_depths 20 \
    --seed 1234 \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/kivi_style_int4_1p5b_needle_s1234" \
    2>&1 | tee -a "$RESULTS_DIR/logs/needle_kivi_int4_1p5b_s1234.log"
done

# ============================================================
# Probe 2: kivi_style INT4 — LongBench
# ============================================================
echo ""
echo ">>> Probe 2: kivi_style INT4 LongBench (1.5B, seed=1234)"
echo ">>> Start: $(date '+%H:%M:%S')"

python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style \
  --quant_bits 4 \
  --seed 1234 \
  --gen_len 64 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/kivi_style_int4_1p5b_longbench_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/longbench_kivi_int4_1p5b_s1234.log"

# ============================================================
# Probe 3: int4_kivi_aligned (KIVI + inv_tau) — Needle
# ============================================================
echo ""
echo ">>> Probe 3: int4_kivi_aligned Needle (1.5B, seed=1234)"
echo ">>> Start: $(date '+%H:%M:%S')"

for CTX in 4096 8192 16384 32704; do
  echo "--- Needle: int4_kivi_aligned ctx=${CTX} ---"
  python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_kivi_aligned \
    --quant_bits 4 \
    --calib_file artifacts/kv_calib_kl_kivi_aligned_v3.json \
    --use_attn_temperature \
    --context_len "$CTX" \
    --num_depths 20 \
    --seed 1234 \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/int4_kivi_aligned_1p5b_needle_s1234" \
    2>&1 | tee -a "$RESULTS_DIR/logs/needle_kivi_aligned_1p5b_s1234.log"
done

# ============================================================
# Probe 4: int4_kivi_aligned — LongBench
# ============================================================
echo ""
echo ">>> Probe 4: int4_kivi_aligned LongBench (1.5B, seed=1234)"
echo ">>> Start: $(date '+%H:%M:%S')"

python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_kivi_aligned \
  --quant_bits 4 \
  --calib_file artifacts/kv_calib_kl_kivi_aligned_v3.json \
  --use_attn_temperature \
  --seed 1234 \
  --gen_len 64 \
  --save_csv \
  --out_dir "$RESULTS_DIR/runs/int4_kivi_aligned_1p5b_longbench_s1234" \
  2>&1 | tee "$RESULTS_DIR/logs/longbench_kivi_aligned_1p5b_s1234.log"

echo ""
echo "=========================================="
echo "GPU 1 | All probes DONE"
echo "End: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
