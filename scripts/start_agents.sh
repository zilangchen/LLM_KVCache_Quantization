#!/bin/bash
# Supervisor + Review-Coord 双窗格分屏
# Developer 已改为 Codex MCP 工具调用，不再作为独立 Agent 启动
# 用法: claudes 或 bash scripts/start_agents.sh

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="agents"

# Preflight checks
command -v claude >/dev/null 2>&1 || { echo "错误: claude 命令未找到"; exit 1; }
[[ -f "$PROJECT_DIR/review_tracker.md" ]] || { echo "错误: review_tracker.md 不存在"; exit 1; }
[[ -f "$PROJECT_DIR/iteration.md" ]] || { echo "错误: iteration.md 不存在"; exit 1; }

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. Attaching..."
    tmux attach -t "$SESSION"
    exit 0
fi

# ============================================================
# 创建 tmux 布局 + 启动
# Agent 定义见 .claude/agents/{supervisor,review-coord}.md
# Developer (Codex) 由 Supervisor 通过 MCP 工具 mcp__codex__codex 调用
# ============================================================

tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR"
tmux split-window -h -t "$SESSION:0.0" -c "$PROJECT_DIR" -p 50
sleep 0.5

tmux send-keys -t "$SESSION:0.0" "claude --dangerously-skip-permissions --agent supervisor" Enter
sleep 1
tmux send-keys -t "$SESSION:0.1" "claude --dangerously-skip-permissions --agent review-coord" Enter
sleep 5

tmux send-keys -t "$SESSION:0.0" "我是主管 Agent。按启动流程开始：获取真实时间 → 读 iteration.md + objective.md → 评估状态 → 制定迭代计划 → 开始执行。" Enter
tmux send-keys -t "$SESSION:0.1" "持续审查模式启动。按启动流程开始：获取时间 → 读 review_tracker.md → 进入持续监控循环。" Enter

# Pane titles for easy identification
tmux select-pane -t "$SESSION:0.0" -T "supervisor"
tmux select-pane -t "$SESSION:0.1" -T "review-coord"
tmux set -t "$SESSION" pane-border-format "#{pane_title}"
tmux set -t "$SESSION" pane-border-status top

tmux select-pane -t "$SESSION:0.0"
tmux attach -t "$SESSION"
