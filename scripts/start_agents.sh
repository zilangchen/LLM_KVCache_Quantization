#!/bin/bash
# 三个独立 Claude Code Agent 分屏，通过 iteration.md 间接沟通
# 用法: claudes 或 bash scripts/start_agents.sh

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="agents"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. Attaching..."
    tmux attach -t "$SESSION"
    exit 0
fi

# ============================================================
# 创建 tmux 布局 + 启动
# Agent 定义见 .claude/agents/{supervisor,developer,review-coord}.md
# ============================================================

tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR"
tmux split-window -h -t "$SESSION:0.0" -c "$PROJECT_DIR" -p 66
tmux split-window -v -t "$SESSION:0.1" -c "$PROJECT_DIR" -p 50
sleep 0.5

tmux send-keys -t "$SESSION:0.0" "claude --dangerously-skip-permissions --agent supervisor" Enter
sleep 1
tmux send-keys -t "$SESSION:0.1" "claude --dangerously-skip-permissions --agent developer" Enter
sleep 1
tmux send-keys -t "$SESSION:0.2" "claude --dangerously-skip-permissions --agent review-coord" Enter
sleep 5

tmux send-keys -t "$SESSION:0.0" "我是主管 Agent。按启动流程开始：获取真实时间 → 读 iteration.md + objective.md → 评估状态 → 制定迭代计划 → 开始执行。" Enter
tmux send-keys -t "$SESSION:0.1" "我是开发 Agent。按启动流程开始：获取真实时间 → 读 review_tracker.md + iteration.md → 按优先级矩阵领取任务 → 开始修复。" Enter
tmux send-keys -t "$SESSION:0.2" "持续审查模式启动。按启动流程开始：获取时间 → 读 review_tracker.md → 进入持续监控循环。" Enter

tmux select-pane -t "$SESSION:0.0"
tmux attach -t "$SESSION"
