#!/bin/bash
# 优雅关闭所有 Agent tmux 会话
# 用法: bash scripts/stop_agents.sh

SESSION="agents"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    for pane in 0.0 0.1 0.2; do
        tmux send-keys -t "$SESSION:$pane" "/exit" Enter
    done
    echo "已向所有 Agent 发送退出指令。等待 10 秒后强制关闭..."
    sleep 10
    tmux kill-session -t "$SESSION" 2>/dev/null
    echo "Session '$SESSION' 已关闭。"
else
    echo "Session '$SESSION' 不存在。"
fi
