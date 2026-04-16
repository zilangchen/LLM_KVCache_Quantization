#!/bin/bash
# Master orchestrator: 等 Stage 1 完成后自动串联 Stage 2-6
#
# 启动方式: nohup bash master_orchestrator.sh > master.log 2>&1 &
#
# 流程：
#   1. 等待 GPU 空闲（Stage 1 完成）
#   2. Stage 2 (Phase 1 8B/14B TPOT, ~2h, 独占 GPU)
#   3. Stage 3 (Phase 2 BD quality 1.5B, ~7h)
#   4. Stage 4 (Phase 3 FI quality 1.5B, ~7h)
#   5. Stage 5 (Phase 4 14B full, ~14h)
#   6. Stage 6 (Phase 5 7B/8B misc, ~5h)
#
# 总耗时 ~35h。每个 stage 独立失败不阻塞下一个。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

LOGDIR="results/emnlp_p012_batch"
mkdir -p "$LOGDIR"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

run_stage() {
  local stage_name="$1"
  local script="$2"
  local logfile="$LOGDIR/${stage_name}.log"
  echo ""; echo "═══════════════════════════════════════════"
  echo "[$(timestamp)] Starting: $stage_name"
  echo "  script: $script"
  echo "  log:    $logfile"
  echo "═══════════════════════════════════════════"
  bash "$script" > "$logfile" 2>&1
  local rc=$?
  if [ $rc -eq 0 ]; then
    echo "[$(timestamp)] $stage_name DONE"
  else
    echo "[$(timestamp)] $stage_name FAILED (exit $rc) — continuing to next stage"
  fi
  return 0
}

# --- Step 0: Wait for Stage 1 (GPU 独占的前置条件) ---
echo "═══════════════════════════════════════════"
echo "[$(timestamp)] Master orchestrator started"
echo "Waiting for Stage 1 (GPU) to complete..."
echo "═══════════════════════════════════════════"

WAIT_COUNT=0
while nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [ $((WAIT_COUNT % 10)) -eq 0 ]; then
    echo "[$(timestamp)] Still waiting for GPU (${WAIT_COUNT}0s elapsed)..."
    nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null
  fi
  sleep 10
done
echo "[$(timestamp)] GPU is free, proceeding"

# --- Step 1: Stage 2 (Phase 1 8B/14B) ---
run_stage "stage2" "scripts/batch_p012/phase1_fix_8b_14b.sh"

# --- Step 2: Stage 3 (Phase 2 BD quality) ---
run_stage "stage3" "scripts/batch_p012/stage3_phase2_bd_quality.sh"

# --- Step 3: Stage 4 (Phase 3 FI quality) ---
run_stage "stage4" "scripts/batch_p012/stage4_phase3_fi_quality.sh"

# --- Step 4: Stage 5 (Phase 4 14B full) ---
run_stage "stage5" "scripts/batch_p012/stage5_phase4_14b_full.sh"

# --- Step 5: Stage 6 (Phase 5 7B/8B misc) ---
run_stage "stage6" "scripts/batch_p012/stage6_phase5_misc.sh"

echo ""
echo "═══════════════════════════════════════════"
echo "[$(timestamp)] ALL STAGES COMPLETE"
echo "═══════════════════════════════════════════"
echo ""
echo "Results in: $LOGDIR/runs/"
echo "Logs in:    $LOGDIR/stage{2..6}.log"
