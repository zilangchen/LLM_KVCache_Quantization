#!/bin/bash
# Download 7B + 8B models, then launch their experiment streams
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

RD="results/emnlp_rolealign_v2"
mkdir -p "$RD/logs"

echo "=== Downloading 7B + 8B models ==="
echo "Start: $(date '+%H:%M:%S')"
python3 scripts/download_models.py 2>&1 | tee "$RD/logs/download.log"

echo ""
echo "=== Models ready, launching experiments ==="
echo "$(date '+%H:%M:%S')"

export HF_HUB_OFFLINE=1

# Launch 7B
rm -f "$RD/logs/stream_7b.log"
tmux new-session -d -s p1_7b "bash -l scripts/phase1_7b.sh 2>&1 | tee $RD/logs/stream_7b.log"
echo "7B launched"

# Launch 8B
rm -f "$RD/logs/stream_8b.log"
tmux new-session -d -s p1_8b "bash -l scripts/phase1_8b.sh 2>&1 | tee $RD/logs/stream_8b.log"
echo "8B launched"

tmux ls
echo "=== Done: $(date '+%H:%M:%S') ==="
