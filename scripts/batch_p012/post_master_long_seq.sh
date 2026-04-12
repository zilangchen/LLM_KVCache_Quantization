#!/bin/bash
# Post-master wrapper: 等 master orchestrator 完成后跑 Stage 7 长序列实验。
#
# 目的：不干扰当前正在跑的 master (PID $MASTER_PID)，等 Stage 1-6 全部完成后
# 自动接管并启动 Stage 7。
#
# 启动方式:
#   nohup bash scripts/batch_p012/post_master_long_seq.sh [MASTER_PID] \
#         > results/emnlp_p012_batch/post_master.log 2>&1 &
#
# 参数: MASTER_PID - master orchestrator 的 PID，默认从 master.log 里读

set -uo pipefail
cd /root/LLM_KVCache_Quantization

LOGDIR="results/emnlp_p012_batch"
mkdir -p "$LOGDIR"

# 第一个参数是 master PID，默认 91736（当前 master orchestrator 的 PID）
MASTER_PID="${1:-91736}"

echo "═══════════════════════════════════════════"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] post_master_long_seq started"
echo "Waiting for master orchestrator PID=$MASTER_PID to finish..."
echo "Check interval: 5 min"
echo "═══════════════════════════════════════════"

WAIT_COUNT=0
while kill -0 "$MASTER_PID" 2>/dev/null; do
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [ $((WAIT_COUNT % 12)) -eq 0 ]; then
    # 每 60 分钟打印一次心跳
    echo "[$(date '+%H:%M:%S')] still waiting (~$((WAIT_COUNT * 5))m elapsed)"
  fi
  sleep 300
done

echo ""
echo "═══════════════════════════════════════════"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] master completed"
echo "Grace period: 30s (let GPU fully release)..."
echo "═══════════════════════════════════════════"
sleep 30

# 二次确认 GPU 空闲
while nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do
  echo "  GPU still busy, waiting another 30s..."
  sleep 30
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] GPU is free, starting Stage 7"
echo ""

bash scripts/batch_p012/stage7_long_seq.sh > "$LOGDIR/stage7_long_seq.log" 2>&1
RC=$?

echo ""
echo "═══════════════════════════════════════════"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 7 exited (rc=$RC)"
echo "═══════════════════════════════════════════"
