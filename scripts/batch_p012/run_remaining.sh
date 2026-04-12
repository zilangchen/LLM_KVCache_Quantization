#!/bin/bash
# 串联：Phase 1 修复 → Phase 2 → Phase 3 → Phase 4 → Phase 5
set -uo pipefail
cd /root/LLM_KVCache_Quantization

LOGDIR="results/emnlp_p012_batch"
mkdir -p "$LOGDIR"

echo "═══ Step 1: Phase 1 fix (8B+14B+BD standalone) ═══"
echo "Started: $(date)"
bash scripts/batch_p012/phase1_fix_8b_14b.sh > "$LOGDIR/phase1_fix.log" 2>&1
echo "Phase 1 fix done: $(date)"

echo ""
echo "═══ Step 2: Phase 2 (BD adapter quality) ═══"
echo "Started: $(date)"
bash scripts/batch_p012/run_all.sh 2 > "$LOGDIR/phase2.log" 2>&1
echo "Phase 2 done: $(date)"

echo ""
echo "═══ Step 3: Phase 3 (FlashInfer quality) ═══"
echo "Started: $(date)"
bash scripts/batch_p012/run_all.sh 3 > "$LOGDIR/phase3.log" 2>&1
echo "Phase 3 done: $(date)"

echo ""
echo "═══ Step 4: Phase 4 (14B full) ═══"
echo "Started: $(date)"
bash scripts/batch_p012/run_all.sh 4 > "$LOGDIR/phase4.log" 2>&1
echo "Phase 4 done: $(date)"

echo ""
echo "═══ Step 5: Phase 5 (7B/8B misc) ═══"
echo "Started: $(date)"
bash scripts/batch_p012/run_all.sh 5 > "$LOGDIR/phase5.log" 2>&1
echo "Phase 5 done: $(date)"

echo ""
echo "═══ ALL DONE ═══"
echo "Finished: $(date)"
