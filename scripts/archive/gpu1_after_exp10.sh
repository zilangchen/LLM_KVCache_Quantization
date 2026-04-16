#!/bin/bash
# After Exp-10 completes on GPU-1, run Exp-7 (LongBench) then Exp-11 (K/V ablation PPL)
# Usage: bash scripts/gpu1_after_exp10.sh
set -euo pipefail
cd /root/LLM_KVCache_Quantization

echo "=== Waiting for Exp-10 to finish ==="
while tmux has-session -t exp10 2>/dev/null; do
  echo "exp10 still running... ($(date '+%H:%M:%S'))"
  sleep 60
done
echo ">>> Exp-10 finished: $(date)"

echo ">>> Starting Exp-7: Official LongBench on GPU-1"
bash scripts/exp7_official_longbench.sh 1
echo ">>> Exp-7 done: $(date)"

echo ">>> Starting Exp-11: K/V Ablation PPL on GPU-1"
bash scripts/exp_kv_ablation_ppl.sh 1
echo ">>> Exp-11 done: $(date)"

echo "=== GPU-1 all follow-up done: $(date) ==="
