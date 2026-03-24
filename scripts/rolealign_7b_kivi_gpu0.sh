#!/bin/bash
# GPU 0 Phase 2: 7B kivi_style INT4 evaluation (runs AFTER 7B ours_asym)
# Needle + LongBench (3 seeds)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "=========================================="
echo "GPU 0 | 7B kivi_style INT4 evaluation"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

RESULTS_DIR="results/emnlp_rolealign_v1"
MODEL_ID="Qwen/Qwen2.5-7B-Instruct"

for SEED in 1234 1235 1236; do
  echo ""
  echo ">>> 7B kivi_style seed=${SEED} — Needle 32K"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL_ID" \
    --kv_mode kivi_style \
    --quant_bits 4 \
    --context_len 32704 \
    --num_depths 20 \
    --seed $SEED \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/kivi_style_int4_7b_needle_s${SEED}" \
    2>&1 | tee -a "$RESULTS_DIR/logs/needle_kivi_int4_7b_s${SEED}.log"

  echo ">>> 7B kivi_style seed=${SEED} — LongBench"
  python3 scripts/eval_longbench.py \
    --model_id "$MODEL_ID" \
    --kv_mode kivi_style \
    --quant_bits 4 \
    --seed $SEED \
    --gen_len 64 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/kivi_style_int4_7b_longbench_s${SEED}" \
    2>&1 | tee "$RESULTS_DIR/logs/longbench_kivi_int4_7b_s${SEED}.log"
done

echo ""
echo "=========================================="
echo "GPU 0 | 7B kivi_style DONE: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
