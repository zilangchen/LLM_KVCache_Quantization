#!/bin/bash
# 简化 pipeline: 只监控 14B 下载，下载完成后立即启动 14B 实验
# 与 isolation 和 64K context 并行运行（单 GPU 多任务）

set -euo pipefail
cd /root/LLM_KVCache_Quantization

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

echo "===== Pipeline (14B only): Waiting for dl_14b ====="
echo "Started: $(date)"

# 等待 14B 下载完成
while tmux has-session -t dl_14b 2>/dev/null; do
  sleep 60
  echo "[$(date +%H:%M:%S)] 14B download still running..."
done

echo "===== 14B download completed at $(date) ====="

# 验证模型已下载
MODEL_DIR="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"
if [ ! -d "$MODEL_DIR" ]; then
  echo "ERROR: 14B model not found at $MODEL_DIR"
  exit 1
fi

echo "===== Starting 14B experiment at $(date) ====="
# 14B 实验可以与 isolation / 64K context 并行
# (所有都是质量评测，显存充裕)
bash scripts/ablation_14b_full.sh 2>&1 | tee "$LOG_DIR/ablation_14b_$(date +%Y%m%d_%H%M%S).log" || {
  echo "WARNING: 14B experiment failed"
}

echo "===== Pipeline complete at $(date) ====="
