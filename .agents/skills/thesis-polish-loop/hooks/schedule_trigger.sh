#!/bin/bash
# schedule_trigger.sh — Entry point called by the schedule skill
#
# This script is invoked every 90 minutes by a cron/launchd job created
# via `/schedule create "thesis-polish" "*/90 * * * *" "/thesis-polish-loop"`.
#
# Responsibilities:
# 1. Check if a previous round is still in progress (state/last_checkpoint.json)
# 2. If busy → skip this trigger, log and exit
# 3. If idle → launch a new Claude Code session in the worktree
# 4. Capture logs to a rotating file
#
# The Claude Code session itself is the one that executes /thesis-polish-loop
# and runs Phase 0 → Phase 5 inside its own context.

set -euo pipefail

WORKTREE="/Users/chenzilang/Desktop/LLM_KVCache_Quantization.polish"
SKILL_DIR="${WORKTREE}/.agents/skills/thesis-polish-loop"
STATE_DIR="${SKILL_DIR}/state"
LOG_DIR="${SKILL_DIR}/reports/schedule_logs"

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="${LOG_DIR}/trigger_${TIMESTAMP}.log"

echo "[$(date)] Schedule trigger fired" > "${LOG_FILE}"

# 1. Check if worktree exists
if [ ! -d "${WORKTREE}" ]; then
  echo "ERROR: Worktree not found at ${WORKTREE}" >> "${LOG_FILE}"
  exit 1
fi

cd "${WORKTREE}"

# 2. Check if a previous round is still in progress
CHECKPOINT_FILE="${STATE_DIR}/last_checkpoint.json"
if [ -f "${CHECKPOINT_FILE}" ]; then
  STATUS=$(python3 -c "import json; print(json.load(open('${CHECKPOINT_FILE}')).get('status','unknown'))" 2>/dev/null || echo "unknown")
  if [ "${STATUS}" = "in_progress" ]; then
    echo "[$(date)] Previous round still in progress, skipping this trigger" >> "${LOG_FILE}"
    exit 0
  fi
fi

# 3. Check wall-time limit
COUNTER_FILE="${STATE_DIR}/round_counter.json"
if [ -f "${COUNTER_FILE}" ]; then
  FIRST_STARTED=$(python3 -c "import json; print(json.load(open('${COUNTER_FILE}')).get('first_started',''))" 2>/dev/null || echo "")
  if [ -n "${FIRST_STARTED}" ]; then
    SECONDS_ELAPSED=$(python3 -c "
from datetime import datetime
fs = datetime.fromisoformat('${FIRST_STARTED}')
print(int((datetime.now() - fs).total_seconds()))
" 2>/dev/null || echo "0")
    if [ "${SECONDS_ELAPSED}" -gt 86400 ]; then
      echo "[$(date)] 24h wall-time limit reached, stopping schedule" >> "${LOG_FILE}"
      exit 0
    fi
  fi
fi

# 4. Launch a new Claude Code session to run one round of the skill
# NOTE: The exact command depends on the Claude Code CLI version
# For non-interactive headless mode, use `claude-code --cmd "/thesis-polish-loop"`
# If not available, user needs to manually trigger from an interactive session

echo "[$(date)] Launching Claude Code session for new round..." >> "${LOG_FILE}"

# Try headless mode (if supported by installed CLI)
if command -v claude-code &> /dev/null; then
  claude-code --cwd "${WORKTREE}" \
              --non-interactive \
              --cmd "/thesis-polish-loop" \
              >> "${LOG_FILE}" 2>&1 || {
    echo "[$(date)] Headless invocation failed, falling back to notification" >> "${LOG_FILE}"
    # Fallback: post a desktop notification asking the user to run manually
    osascript -e "display notification \"thesis-polish-loop ready to run next round\" with title \"Schedule Trigger\""
  }
else
  echo "[$(date)] claude-code CLI not found, posting notification" >> "${LOG_FILE}"
  osascript -e "display notification \"Run /thesis-polish-loop in your Claude Code session\" with title \"Schedule Trigger\""
fi

echo "[$(date)] Schedule trigger completed" >> "${LOG_FILE}"
exit 0
