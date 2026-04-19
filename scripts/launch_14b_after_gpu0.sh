#!/bin/bash
# One-shot chain launcher: waits for svk_main_gpu0 (1p5b + 3b) to exit,
# then starts 14B main on GPU 0 using the ModelScope local weights via
# SVK_MODEL_PATH_14B env override (committed as 8a87d89).
#
# Usage:
#   SSH_PASSWORD=... bash scripts/launch_14b_after_gpu0.sh
#   or: Bash(run_in_background=true, command="bash scripts/launch_14b_after_gpu0.sh")
#
# Exits 0 once the 14B tmux session is confirmed started.
# Exits non-zero if SSH fails or the session cannot be created.

set -u

: "${SSH_PASSWORD:?SSH_PASSWORD env required}"
SSH_HOST=${SSH_HOST:-region-42.seetacloud.com}
SSH_PORT=${SSH_PORT:-23129}
SSH_USER=${SSH_USER:-root}
SSH_CMD="sshpass -p '${SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}"

WORKTREE=/root/autodl-tmp/LLM_KVCache_Quantization_systemvkivi_36bf21c
MODEL_LOCAL=/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct
TARGET_SESSION=svk_main_gpu0_14b
WATCH_SESSION=svk_main_gpu0
INTERVAL=${INTERVAL:-300}

echo "[$(date +%H:%M:%S)] chain launcher: waiting for ${WATCH_SESSION} to end, then starting ${TARGET_SESSION}"

while true; do
    alive=$(eval "$SSH_CMD" "\"tmux has-session -t ${WATCH_SESSION} 2>/dev/null && echo 1 || echo 0\"" 2>/dev/null || echo 0)
    if [ "$alive" != "1" ]; then
        echo "[$(date +%H:%M:%S)] ${WATCH_SESSION} ended — launching 14B on GPU 0"
        break
    fi
    echo "[$(date +%H:%M:%S)] ${WATCH_SESSION} still alive, sleeping ${INTERVAL}s"
    sleep "$INTERVAL"
done

# Launch 14B main on GPU 0 with ModelScope local path override
LAUNCH_CMD="cd ${WORKTREE} && export CUDA_VISIBLE_DEVICES=0 && export HF_HOME=/root/autodl-tmp/hf_cache && export HF_HUB_OFFLINE=1 && export SVK_MODEL_PATH_14B=${MODEL_LOCAL} && source /etc/network_turbo 2>/dev/null; python3 scripts/run_system_vs_kivi.py --phase main --models 14b --longbench_dataset_path /root/autodl-tmp/longbench_data/data > logs/main_gpu0_14b.log 2>&1; echo EXIT_14b=\\\$? >> logs/main_gpu0_14b.log"

eval "$SSH_CMD" "\"tmux new-session -d -s ${TARGET_SESSION} '${LAUNCH_CMD}'\"" || {
    echo "[$(date +%H:%M:%S)] ERROR: failed to create tmux session ${TARGET_SESSION}"
    exit 1
}

sleep 5
echo "[$(date +%H:%M:%S)] confirming session created:"
eval "$SSH_CMD" "\"tmux ls | grep ${TARGET_SESSION}\"" || {
    echo "[$(date +%H:%M:%S)] ERROR: ${TARGET_SESSION} not found after launch"
    exit 1
}

echo "[$(date +%H:%M:%S)] 14B session launched successfully; chain launcher exiting"
exit 0
