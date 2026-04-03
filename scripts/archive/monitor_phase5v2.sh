#!/bin/bash
# Phase 5v2 循环监测脚本
# 每 30 分钟执行一次完整监测 SOP
# 用法: bash scripts/monitor_phase5v2.sh

set -euo pipefail

# SSH config (from docs/autodl_server.md)
SSH_HOST="region-42.seetacloud.com"
SSH_PORT="31867"
SSH_USER="root"
SSH_PASS="YLt4oozwKWNg"
REMOTE_DIR="/root/LLM_KVCache_Quantization"
RESULTS_DIR="$REMOTE_DIR/results/phase5v2/runs"

INTERVAL=1800  # 30 minutes in seconds
ROUND=1
PREV_TOTAL=0

# SSH via stdin to avoid quoting hell
ssh_script() {
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=60 -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "bash -l" <<'REMOTE_EOF'
$1
REMOTE_EOF
}

run_monitor() {
    # Single SSH call that does everything
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=60 -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" bash -l <<REMOTE_SCRIPT
echo "--- Infrastructure ---"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "GPU_QUERY_FAILED"
echo "DISK:"
df -h /root --output=size,used,avail,pcent 2>/dev/null | tail -1

echo ""
echo "--- tmux Sessions ---"
tmux ls 2>&1 || echo "NO_TMUX"

echo ""
echo "--- Run Counts ---"
cd $RESULTS_DIR 2>/dev/null || { echo "RESULTS_DIR_NOT_FOUND"; exit 1; }
total=\$(ls -d */ 2>/dev/null | wc -l)
echo "Total: \$total"
for model in 1p5b 7b 8b; do
    model_total=0
    for s in 1234 1235 1236 1237 1238; do
        count=\$(ls -d *\${model}*s\${s}* 2>/dev/null | wc -l)
        if [ "\$count" -gt 0 ]; then
            echo "  \${model} s\${s}: \${count}"
            model_total=\$((model_total + count))
        fi
    done
    echo "  \${model} subtotal: \${model_total}"
done

echo ""
echo "--- Error Check ---"
failures=\$(find . -name "task_failure_*.json" 2>/dev/null | wc -l)
echo "Failure JSONs: \$failures"
recent_errors=\$(find . -name "*.log" -mmin -60 2>/dev/null | xargs grep -l "Error\|Exception\|Traceback" 2>/dev/null | wc -l)
echo "Recent error logs (1h): \$recent_errors"
if [ "\$recent_errors" -gt 0 ]; then
    echo "ERROR FILES:"
    find . -name "*.log" -mmin -60 2>/dev/null | xargs grep -l "Error\|Exception\|Traceback" 2>/dev/null | head -5
fi

echo ""
echo "--- int4_fused Pollution Tracking ---"
polluted=\$(ls -d *int4_fused*phase5v2_{1p5b_s,7b_s,8b_s}* 2>/dev/null | wc -l)
fixed=\$(ls -d *int4_fused*fused_fix* 2>/dev/null | wc -l)
quarantined=0
if [ -d ../quarantine ]; then
    quarantined=\$(ls -d ../quarantine/*int4_fused* 2>/dev/null | wc -l)
fi
echo "Polluted (old run_tag): \$polluted"
echo "Fixed (fused_fix tag): \$fixed"
echo "Quarantined: \$quarantined"

echo ""
echo "--- tmux Latest ---"
for session in q_1p5b q_7b q_8b retry_s1234; do
    echo "[\$session]:"
    tmux capture-pane -t \$session -p -S -3 2>/dev/null | tail -3 || echo "  (dead/closed)"
done

echo ""
echo "--- Disk Usage Pct ---"
df /root --output=pcent 2>/dev/null | tail -1 | tr -d ' %'
REMOTE_SCRIPT
}

ONCE_MODE=false
if [ "${1:-}" = "--once" ]; then
    ONCE_MODE=true
fi

# Main monitoring loop
echo "=============================================="
echo "Phase 5v2 Monitoring — Started $(date '+%Y-%m-%d %H:%M:%S')"
if $ONCE_MODE; then
    echo "Mode: one-shot"
else
    echo "Interval: ${INTERVAL}s (30 min)"
fi
echo "Target: 535+ runs (1.5B×215 + 7B×160 + 8B×160 + fused_fix)"
echo "=============================================="

while true; do
    echo ""
    echo "====== Round $ROUND — $(date '+%Y-%m-%d %H:%M:%S') ======"

    if output=$(run_monitor 2>&1); then
        echo "$output"

        # Parse disk usage from last line
        disk_pct=$(echo "$output" | tail -1 | tr -d ' %' 2>/dev/null || echo "0")
        if [ "${disk_pct:-0}" -gt 80 ] 2>/dev/null; then
            echo ""
            echo "*** DISK ALERT: ${disk_pct}% used! ***"
        fi

        # Parse total from output
        current_total=$(echo "$output" | grep "^Total:" | awk '{print $2}' || echo "0")
        if [ "$PREV_TOTAL" -gt 0 ] 2>/dev/null && [ "${current_total:-0}" -gt 0 ] 2>/dev/null; then
            delta=$((current_total - PREV_TOTAL))
            echo ""
            echo "Delta since last round: +${delta} runs"
        fi
        PREV_TOTAL=${current_total:-$PREV_TOTAL}
    else
        echo "*** MONITOR FAILED — SSH connection error ***"
        echo "Output: $output"
    fi

    echo "====== End Round $ROUND ======"
    echo ""

    if $ONCE_MODE; then
        echo "One-shot mode complete."
        exit 0
    fi

    ROUND=$((ROUND + 1))

    next_time=$(date -v+${INTERVAL}S '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -d "+${INTERVAL} seconds" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "in 30 min")
    echo "Next check at $next_time"
    echo "Sleeping ${INTERVAL}s..."
    sleep $INTERVAL
done
