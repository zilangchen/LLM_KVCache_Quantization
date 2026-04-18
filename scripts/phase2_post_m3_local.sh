#!/bin/bash
# =============================================================================
# Phase 2 编号 6 M4 一键 post 流水线（本地执行）
# =============================================================================
# 前置：M3 (phase2_gpu0/1/2 tmux) 全部完成
# 流程：
#   1. 确认远端无 phase2_gpu tmux
#   2. 远端跑 aggregate_phase2.py（聚合 + 硬/次 gate 判定）
#   3. scp phase2_summary.csv + phase2_main_table.md 到本地
#   4. 打印 gate 决策
# =============================================================================
set -euo pipefail

SSH_PORT=23129
SSH_HOST="region-42.seetacloud.com"
REMOTE="/root/LLM_KVCache_Quantization"
LOCAL="/Users/chenzilang/Desktop/LLM_KVCache_Quantization"
SSH_PASS="${AUTODL_PW:-YLt4oozwKWNg}"

cd "$LOCAL"

echo "=============================================="
echo "Phase 2 编号 6 M4 post pipeline"
echo "时间: $(date)"
echo "=============================================="

# Step 1: 确认 tmux 结束（用 grep -c || true 避免 pipefail 拦截）
echo ""
echo "=== Step 1: 确认远端 phase2_gpu tmux 全部结束 ==="
TMUX_COUNT=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -p $SSH_PORT root@$SSH_HOST "tmux ls 2>/dev/null | grep -c phase2_gpu || true" 2>/dev/null || echo 0)
# Fix grep -c output may contain multiple lines — take first
TMUX_COUNT=$(echo "$TMUX_COUNT" | head -1 | tr -d '[:space:]')
if [ -z "$TMUX_COUNT" ] || [ "$TMUX_COUNT" = "0" ]; then
    echo "远端无 phase2_gpu tmux，可以继续"
else
    echo "WARN: 还有 $TMUX_COUNT 个 phase2_gpu tmux 在跑 — 继续（数据可能不完整）"
fi

# Step 2: 远端跑 aggregate
echo ""
echo "=== Step 2: 远端跑 aggregate_phase2.py ==="
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -p $SSH_PORT root@$SSH_HOST "bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate base && cd $REMOTE && python3 scripts/aggregate_phase2.py --runs_dir results/phase2_allocator_mvp/ --out_csv results/phase2_summary.csv --out_md docs/phase2_main_table.md 2>&1'" | tee /tmp/phase2_agg_output.log

# Step 3: scp 产出回本地
echo ""
echo "=== Step 3: scp phase2 产出到本地 ==="
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no -P $SSH_PORT \
    root@$SSH_HOST:$REMOTE/results/phase2_summary.csv \
    results/phase2_summary.csv
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no -P $SSH_PORT \
    root@$SSH_HOST:$REMOTE/docs/phase2_main_table.md \
    docs/phase2_main_table.md

# Step 4: 汇总决策
echo ""
echo "=============================================="
echo "=== Phase 2 主表 + Gate 决策 ==="
echo "=============================================="
cat docs/phase2_main_table.md

echo ""
echo "=============================================="
echo "本地产出："
ls -la results/phase2_summary.csv docs/phase2_main_table.md 2>/dev/null
echo "=============================================="
