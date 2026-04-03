#!/bin/bash
# gpu_orchestrator_check.sh — 远端 GPU & 任务状态采集
# 单次 SSH 连接收集所有数据，结构化输出供 Claude 解析
#
# 使用: 先从 docs/autodl_server.md 读取连接信息，然后:
#   SSH_HOST=xxx SSH_PORT=xxx bash scripts/gpu_orchestrator_check.sh
#
# 或由 Claude 在 /gpu-orchestrator skill 中自动调用

set -euo pipefail

: "${SSH_HOST:?SSH_HOST not set — read from docs/autodl_server.md}"
: "${SSH_PORT:?SSH_PORT not set — read from docs/autodl_server.md}"
SSH_USER="${SSH_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/root/LLM_KVCache_Quantization}"

SSH_OPTS="-o ConnectTimeout=15 -o ServerAliveInterval=60 -o StrictHostKeyChecking=no"
SSH_CMD="ssh $SSH_OPTS -p $SSH_PORT $SSH_USER@$SSH_HOST"

echo "=== GPU Orchestrator Check — $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

# Single SSH call — all data collection in one connection
$SSH_CMD bash -l <<REMOTE_SCRIPT
echo "<<< GPU_STATUS >>>"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null || echo "GPU_QUERY_FAILED"

echo ""
echo "<<< GPU_PROCESSES >>>"
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory,process_name --format=csv,noheader 2>/dev/null || echo "NO_PROCESSES"

echo ""
echo "<<< TMUX_SESSIONS >>>"
tmux ls 2>/dev/null || echo "NO_TMUX_SESSIONS"

echo ""
echo "<<< TMUX_OUTPUT >>>"
for session in \$(tmux ls -F "#{session_name}" 2>/dev/null); do
    echo "[[\$session]]"
    tmux capture-pane -t \$session -p -S -25 2>/dev/null | tail -25 || echo "(capture failed)"
    echo "[[/\$session]]"
    echo ""
done

echo "<<< DISK >>>"
df -h /root 2>/dev/null | tail -1

echo ""
echo "<<< RESULTS_RECENT >>>"
cd $REMOTE_DIR 2>/dev/null || { echo "REMOTE_DIR_NOT_FOUND"; exit 0; }
echo "Recently modified result dirs (2h):"
find results/ -maxdepth 2 -name "runs" -type d 2>/dev/null | while read d; do
    tag=\$(basename \$(dirname "\$d"))
    count=\$(ls -d "\$d"/*/ 2>/dev/null | wc -l)
    recent=\$(find "\$d" -maxdepth 1 -type d -mmin -120 2>/dev/null | wc -l)
    echo "  \$tag: \$count total, \$((recent > 0 ? recent - 1 : 0)) new (2h)"
done

echo ""
echo "<<< ERROR_CHECK >>>"
failures=\$(find results/ -name "task_failure_*.json" -mmin -120 2>/dev/null | wc -l)
echo "Recent failure JSONs (2h): \$failures"
if [ "\$failures" -gt 0 ]; then
    echo "Files:"
    find results/ -name "task_failure_*.json" -mmin -120 2>/dev/null | head -5
fi
recent_errors=\$(find results/ -name "*.log" -mmin -60 2>/dev/null | xargs grep -l "Error\|Exception\|Traceback" 2>/dev/null | wc -l)
echo "Error logs (1h): \$recent_errors"
if [ "\$recent_errors" -gt 0 ]; then
    echo "Error files:"
    find results/ -name "*.log" -mmin -60 2>/dev/null | xargs grep -l "Error\|Exception\|Traceback" 2>/dev/null | head -5
fi

echo ""
echo "<<< RUNNING_COMMANDS >>>"
ps aux | grep -E "python.*scripts/" | grep -v grep | awk '{print \$2, \$10, \$11, \$12, \$13}' 2>/dev/null || echo "NO_PYTHON_PROCESSES"
REMOTE_SCRIPT

echo ""
echo "=== Check Complete ==="
