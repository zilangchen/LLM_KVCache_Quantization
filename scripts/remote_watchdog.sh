#!/bin/bash
# Remote tmux watchdog: polls a remote host until all named tmux sessions are gone.
#
# Why this exists
#   Previously we used ScheduleWakeup(delaySeconds=...) to re-enter Claude Code
#   at guessed intervals to check long-running remote jobs. That wasted Anthropic
#   prompt cache (5-min TTL) and either woke up too early or too late. A local
#   background bash watchdog is strictly better:
#     - zero cache cost while waiting (Claude Code just idles)
#     - exits the exact moment the remote task terminates
#     - wakes Claude Code through the "background bash completed" notification
#
# Usage
#   Required env:
#     SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD    (see docs/autodl_server.md)
#   Positional args:
#     $1 = comma-separated tmux session names (e.g. "svk_smoke_1p5b,svk_smoke_8b")
#     $2 = optional remote log paths (comma-separated); printed on exit
#     $3 = optional poll interval seconds (default: 60)
#
# Launch via:
#   Bash(run_in_background=true, command="bash scripts/remote_watchdog.sh ...")
# Claude Code's runtime notifies the agent automatically when this script exits.

set -u

if [ $# -lt 1 ]; then
    echo "usage: $0 <comma-separated-sessions> [comma-separated-logs] [interval-sec]" >&2
    exit 2
fi

SESSIONS_CSV="$1"
LOGS_CSV="${2:-}"
INTERVAL="${3:-60}"

: "${SSH_HOST:?SSH_HOST env required}"
: "${SSH_PORT:?SSH_PORT env required}"
: "${SSH_USER:?SSH_USER env required}"
: "${SSH_PASSWORD:?SSH_PASSWORD env required}"

SSH_CMD="sshpass -p '${SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}"

# Turn CSV into a regex alternation for grep
SESSION_REGEX=$(echo "$SESSIONS_CSV" | tr ',' '|')

echo "[$(date +%H:%M:%S)] watchdog start: sessions=${SESSIONS_CSV} interval=${INTERVAL}s"

while true; do
    alive=$(eval "$SSH_CMD" "\"tmux ls 2>/dev/null | grep -E '^(${SESSION_REGEX}):' | awk -F: '{print \\\$1}'\"" 2>/dev/null || true)
    if [ -z "$alive" ]; then
        echo "[$(date +%H:%M:%S)] all watched sessions ended; dumping log tails:"
        if [ -n "$LOGS_CSV" ]; then
            IFS=',' read -ra LOGS <<< "$LOGS_CSV"
            for log in "${LOGS[@]}"; do
                echo "--- $log ---"
                eval "$SSH_CMD" "\"tail -6 '${log}' 2>/dev/null\"" || true
            done
        fi
        exit 0
    fi
    n=$(echo "$alive" | wc -l | tr -d ' ')
    echo "[$(date +%H:%M:%S)] $n alive: $(echo "$alive" | tr '\n' ' ')"
    sleep "$INTERVAL"
done
