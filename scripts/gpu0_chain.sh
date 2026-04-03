#!/bin/bash
# GPU-0 chain: Exp-3 cs=1 → Exp-2 INT8 compare → T3 1.5B full re-run
# Usage: bash scripts/gpu0_chain.sh
set -euo pipefail
cd /root/LLM_KVCache_Quantization

echo "=== GPU-0 Chain: Exp-3 → Exp-2 → T3 1.5B ==="
echo "Start: $(date)"

# Step 1: Exp-3 INT8 cs=1 PPL
echo ">>> Step 1: Exp-3 INT8 cs=1"
bash scripts/exp3_int8_cs1_1p5b.sh 0
echo ">>> Exp-3 done: $(date)"

# Step 2: Exp-2 INT8 calibration comparison
echo ">>> Step 2: Exp-2 INT8 calib compare"
bash scripts/exp2_int8_calib_compare.sh 0
echo ">>> Exp-2 done: $(date)"

# Step 3: T3 1.5B full re-run with v3 calibration
echo ">>> Step 3: T3 1.5B full re-run"
CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
T3_RD="results/emnlp_rolealign_v4"
if [ ! -f "$CALIB_1P5B" ]; then
  echo "FATAL: 1.5B v3 calib not found: $CALIB_1P5B" >&2
  exit 1
fi
bash scripts/phase1_1p5b.sh 0 "$CALIB_1P5B" "$T3_RD"
echo ">>> T3 1.5B done: $(date)"

echo ""
echo "=========================================="
echo "  GPU-0 Chain ALL DONE"
echo "  $(date)"
echo "=========================================="
