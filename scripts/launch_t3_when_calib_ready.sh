#!/bin/bash
# Auto-launcher: starts T3 full re-run for 7B and 8B once their v3 calibration is ready.
# 1.5B's T3 will be started separately after Exp-3/Exp-2 finish on GPU-0.
# Usage: bash scripts/launch_t3_when_calib_ready.sh
set -euo pipefail
cd /root/LLM_KVCache_Quantization

CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"
T3_RD="results/emnlp_rolealign_v4"

echo "=== T3 auto-launcher: waiting for v3 calibration artifacts ==="
echo "Start: $(date)"

# Poll until 7B artifact appears
while [ ! -f "$CALIB_7B" ]; do
  echo "Waiting for $CALIB_7B... ($(date '+%H:%M:%S'))"
  sleep 30
done
echo ">>> 7B v3 artifact ready. Launching T3 7B on GPU-1."
tmux new-session -d -s t3_7b "bash scripts/phase1_7b.sh 1 $CALIB_7B $T3_RD 2>&1 | tee logs/t3_7b_v4.log"

# Poll until 8B artifact appears
while [ ! -f "$CALIB_8B" ]; do
  echo "Waiting for $CALIB_8B... ($(date '+%H:%M:%S'))"
  sleep 30
done
echo ">>> 8B v3 artifact ready. Launching T3 8B on GPU-2."
tmux new-session -d -s t3_8b "bash scripts/phase1_8b.sh 2 $CALIB_8B $T3_RD 2>&1 | tee logs/t3_8b_v4.log"

echo ""
echo "=== T3 7B + 8B launched. ==="
echo "Monitor: tmux ls"
echo "$(date)"
