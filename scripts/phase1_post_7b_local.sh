#!/bin/bash
# =============================================================================
# Phase 1 编号 4-5 完成后本地一键流水线
# =============================================================================
# 在本地执行：SSH 触发远端 gate → scp 所有结果 → 本地汇总
# 前置：7B tmux 已全部完成（3 GPU × 4 modes × 3 tasks = 12 CSV）
#
# 用法:
#   bash scripts/phase1_post_7b_local.sh
# =============================================================================
set -euo pipefail

SSH_PORT=23129
SSH_HOST="region-42.seetacloud.com"
REMOTE="/root/LLM_KVCache_Quantization"
LOCAL="/Users/chenzilang/Desktop/LLM_KVCache_Quantization"
SSHPASS_FILE="${HOME}/.ssh/autodl_pw"
SSH_PASS="${AUTODL_PW:-YLt4oozwKWNg}"

cd "$LOCAL"

echo "=============================================="
echo "Phase 1 编号 4-5 post pipeline"
echo "时间: $(date)"
echo "=============================================="

# 1. 确认远端 7B tmux 全部结束
echo ""
echo "=== Step 1: 确认远端 7B tmux 全部结束 ==="
TMUX_COUNT=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -p $SSH_PORT root@$SSH_HOST "tmux ls 2>&1 | grep -c phase1_7b || echo 0")
if [ "$TMUX_COUNT" != "0" ]; then
    echo "ERROR: 还有 $TMUX_COUNT 个 phase1_7b tmux 在跑，等待它们完成再跑此脚本"
    exit 2
fi
echo "远端无 phase1_7b tmux，可以继续"

# 2. 远端跑 gate pipeline（含 aggregate 7B + gate_check with 1.5B + 7B）
echo ""
echo "=== Step 2: 远端跑 phase1_gate5_run.sh ==="
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -p $SSH_PORT root@$SSH_HOST "bash -lc 'cd $REMOTE && bash scripts/phase1_gate5_run.sh 2>&1'" | tee /tmp/phase1_gate5_run_output.log

GATE_EXIT=${PIPESTATUS[0]}
echo "远端 gate run exit code: $GATE_EXIT"

# 3. scp 7B 结果到本地
echo ""
echo "=== Step 3: scp 7B summary + main table + decision log 到本地 ==="
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no -P $SSH_PORT \
    root@$SSH_HOST:$REMOTE/results/phase1_summary_7b.csv \
    results/phase1_summary_7b.csv
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no -P $SSH_PORT \
    root@$SSH_HOST:$REMOTE/docs/phase1_main_table_7b.md \
    docs/phase1_main_table_7b.md
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no -P $SSH_PORT \
    root@$SSH_HOST:$REMOTE/results/phase1_gate5_decision.log \
    results/phase1_gate5_decision.log 2>/dev/null || echo "no decision log (gate may have failed)"

echo ""
echo "=== Step 4: 本地汇总 ==="
echo ""
echo "--- 7B 主表 ---"
cat docs/phase1_main_table_7b.md 2>/dev/null | head -30
echo ""
echo "--- Gate 决策 ---"
cat results/phase1_gate5_decision.log 2>/dev/null | tail -20
echo ""
echo "=============================================="
echo "GATE final exit: $GATE_EXIT"
echo "  0 = PASS → 允许进编号 6 (Allocator MVP)"
echo "  1 = FAIL → 跳编号 11 收口 v6-diagnostic"
echo "=============================================="

exit $GATE_EXIT
