#!/bin/bash
# Wait for gpu0work session to finish, then launch T3 1.5B on GPU-0
# Usage: bash scripts/launch_t3_1p5b_after_gpu0.sh
set -euo pipefail
cd /root/LLM_KVCache_Quantization

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
T3_RD="results/emnlp_rolealign_v4"

echo "=== Waiting for gpu0work to finish ==="
while tmux has-session -t gpu0work 2>/dev/null; do
  echo "gpu0work still running... ($(date '+%H:%M:%S'))"
  sleep 60
done

echo ">>> gpu0work finished: $(date)"

# Fail-fast
if [ ! -f "$CALIB_1P5B" ]; then
  echo "FATAL: 1.5B v3 calib not found" >&2
  exit 1
fi

echo ">>> Launching T3 1.5B on GPU-0"
tmux new-session -d -s t3_1p5b "bash scripts/phase1_1p5b.sh 0 $CALIB_1P5B $T3_RD 2>&1 | tee logs/t3_1p5b_v4.log"
echo ">>> T3 1.5B launched: $(date)"
