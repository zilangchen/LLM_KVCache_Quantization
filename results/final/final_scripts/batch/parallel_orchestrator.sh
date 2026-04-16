#!/bin/bash
# Parallel orchestrator: Stage 3/4/5 并行跑（共享 GPU），然后串行 Stage 6 → Stage 7
#
# 前置条件：
#   1. master_orchestrator (91736) 已 kill (避免它自动启动 Stage 4 串行)
#   2. post_master_long_seq (93385) 已 kill (避免它因 master 死而提前启动 Stage 7)
#   3. Stage 3 的 bash/python 进程已 orphan 但继续跑
#
# GPU 预算（H20 96 GB）:
#   - Stage 3: ~5 GB (1.5B BD adapter)
#   - Stage 4: ~5 GB (1.5B FI adapter)
#   - Stage 5: ~35 GB (14B full)
#   - Total: ~45 GB (51 GB buffer)
#
# 预期时间:
#   - Stage 3+4+5 并行: ~14h (受 Stage 5 limit)
#   - Stage 6 serial:    ~5h
#   - Stage 7 serial:    ~2h
#   - Total: ~21h (vs 34h serial, save 13h)

set -uo pipefail
cd /root/LLM_KVCache_Quantization

LOGDIR="results/emnlp_p012_batch"
mkdir -p "$LOGDIR"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "═══════════════════════════════════════════"
echo "[$(timestamp)] parallel_orchestrator started"
echo "═══════════════════════════════════════════"

# --- Step 1: 启动 Stage 4 后台 (FI quality 1.5B) ---
echo ""
echo "[$(timestamp)] Launching Stage 4 (FI quality 1.5B) in background..."
bash scripts/batch_p012/stage4_phase3_fi_quality.sh > "$LOGDIR/stage4.log" 2>&1 &
STAGE4_PID=$!
echo "[$(timestamp)] Stage 4 PID=$STAGE4_PID"

# --- Step 2: 启动 Stage 5 后台 (14B 全套) ---
sleep 5  # 错开启动，避免同时 load 竞争
echo ""
echo "[$(timestamp)] Launching Stage 5 (14B full) in background..."
bash scripts/batch_p012/stage5_phase4_14b_full.sh > "$LOGDIR/stage5.log" 2>&1 &
STAGE5_PID=$!
echo "[$(timestamp)] Stage 5 PID=$STAGE5_PID"

# --- Step 3: Wait for Stage 3 (orphan bash + python from old master) ---
echo ""
echo "[$(timestamp)] Waiting for Stage 3 (orphan bash from killed master)..."
echo "  polling every 5 min for stage3_phase2_bd_quality or eval_ppl/ruler/needle/longbench_bd..."
WAIT3_COUNT=0
while pgrep -f "stage3_phase2_bd_quality" > /dev/null; do
  WAIT3_COUNT=$((WAIT3_COUNT + 1))
  if [ $((WAIT3_COUNT % 12)) -eq 0 ]; then
    echo "[$(timestamp)] Stage 3 still running ($((WAIT3_COUNT * 5))m elapsed)"
  fi
  sleep 300
done
echo "[$(timestamp)] Stage 3 completed"

# --- Step 4: Wait for Stage 4 + Stage 5 ---
echo ""
echo "[$(timestamp)] Waiting for Stage 4 (PID=$STAGE4_PID)..."
wait "$STAGE4_PID" 2>/dev/null
STAGE4_RC=$?
echo "[$(timestamp)] Stage 4 done (rc=$STAGE4_RC)"

echo ""
echo "[$(timestamp)] Waiting for Stage 5 (PID=$STAGE5_PID)..."
wait "$STAGE5_PID" 2>/dev/null
STAGE5_RC=$?
echo "[$(timestamp)] Stage 5 done (rc=$STAGE5_RC)"

# --- Step 5: Serial Stage 6 (memory sweep needs exclusive) ---
echo ""
echo "═══════════════════════════════════════════"
echo "[$(timestamp)] Parallel phase complete, starting Stage 6 (serial)"
echo "═══════════════════════════════════════════"
sleep 30  # grace for GPU release
bash scripts/batch_p012/stage6_phase5_misc.sh > "$LOGDIR/stage6.log" 2>&1
echo "[$(timestamp)] Stage 6 done"

# --- Step 6: Serial Stage 7 (长序列 TPOT, exclusive) ---
echo ""
echo "═══════════════════════════════════════════"
echo "[$(timestamp)] Starting Stage 7 (long-seq TPOT, exclusive)"
echo "═══════════════════════════════════════════"
sleep 30

# 二次确认 GPU 空闲
while nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do
  echo "  GPU still busy, waiting 30s more..."
  sleep 30
done

bash scripts/batch_p012/stage7_long_seq.sh > "$LOGDIR/stage7_long_seq.log" 2>&1
echo "[$(timestamp)] Stage 7 done"

echo ""
echo "═══════════════════════════════════════════"
echo "[$(timestamp)] ALL PARALLEL STAGES COMPLETE"
echo "═══════════════════════════════════════════"
