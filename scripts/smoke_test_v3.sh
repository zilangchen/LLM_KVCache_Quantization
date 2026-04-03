#!/bin/bash
# Smoke test: verify v3 calibration + RULER + PPL on 1.5B
# Run on remote GPU server after rsync.
# Usage: bash scripts/smoke_test_v3.sh
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
CALIB="artifacts/kv_calib_rolealign_1p5b_v3.json"
SMOKE_RD="results/smoke_test_v3"

# Fail-fast: check calib exists
if [ ! -f "$CALIB" ]; then
  echo "FATAL: v3 calibration file not found: $CALIB" >&2
  echo "Run calibrate_behavior.py first to generate it." >&2
  exit 1
fi

mkdir -p "$SMOKE_RD/runs" "$SMOKE_RD/logs"

echo "=== SMOKE TEST: RULER (1.5B, seed=1234, ctx=4096) ==="
echo "Start: $(date)"
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ruler.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB" \
  --seq_len 4096 --ruler_context_len 4096 --seed 1234 \
  --save_csv --out_dir "$SMOKE_RD/runs/ruler_smoke_1p5b" \
  2>&1 | tee "$SMOKE_RD/logs/ruler_smoke.log"
echo ">>> RULER done: $(date)"

echo ""
echo "=== SMOKE TEST: PPL (1.5B, seed=1234, cs=128) ==="
echo "Start: $(date)"
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB" \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$SMOKE_RD/runs/ppl_smoke_1p5b" \
  2>&1 | tee "$SMOKE_RD/logs/ppl_smoke.log"
echo ">>> PPL done: $(date)"

echo ""
echo "=========================================="
echo "  SMOKE TEST ALL PASSED"
echo "  $(date)"
echo "=========================================="
