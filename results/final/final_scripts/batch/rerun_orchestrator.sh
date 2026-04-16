#!/bin/bash
# Rerun orchestrator: Stage 7 rerun → 14B fp16 RULER baseline (串联)
#
# 两个任务都独占 GPU (TPOT 和 14B large model 质量评测互相挤不起).
#
# 启动:
#   nohup bash scripts/batch_p012/rerun_orchestrator.sh \
#     > results/emnlp_p012_batch/rerun.log 2>&1 &

set -uo pipefail
cd /root/LLM_KVCache_Quantization

LOGDIR="results/emnlp_p012_batch"
mkdir -p "$LOGDIR"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "═══════════════════════════════════════════"
echo "[$(timestamp)] rerun_orchestrator started"
echo "═══════════════════════════════════════════"

# --- Step 1: Stage 7 Rerun (TPOT 独占, ~2-3h with warmup=5 runs=10) ---
echo ""
echo "═══ Step 1: Stage 7 Rerun ═══"
bash scripts/batch_p012/stage7_rerun.sh > "$LOGDIR/stage7_rerun.log" 2>&1
STAGE7_RC=$?
echo "[$(timestamp)] Stage 7 rerun done (rc=$STAGE7_RC)"

# Grace period
sleep 30

# --- Step 2: 14B FP16 RULER baseline (独占, ~12-18h) ---
echo ""
echo "═══ Step 2: 14B FP16 RULER baseline ═══"
MODEL=14b bash scripts/batch_p012/stage_baseline_fp16_ruler.sh > "$LOGDIR/baseline_fp16_ruler_14b.log" 2>&1
BASELINE_RC=$?
echo "[$(timestamp)] 14B FP16 RULER baseline done (rc=$BASELINE_RC)"

echo ""
echo "═══════════════════════════════════════════"
echo "[$(timestamp)] ALL RERUNS COMPLETE"
echo "═══════════════════════════════════════════"
