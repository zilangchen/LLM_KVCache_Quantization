#!/bin/bash
# Download Qwen2.5-14B-Instruct via modelscope
# 目的：为任务 2.3 (14B 扩展实验) 准备模型
# 只占网络带宽，不占 GPU 计算，可与 isolation 实验并行

set -euo pipefail
cd /root/LLM_KVCache_Quantization

CACHE_DIR="/root/autodl-tmp/modelscope_cache"
TARGET_DIR="$CACHE_DIR/qwen/Qwen2___5-14B-Instruct"

echo "===== Download Qwen2.5-14B ====="
echo "Started: $(date)"
echo "Target: $TARGET_DIR"

# 检查是否已存在
if [ -d "$TARGET_DIR" ]; then
  echo "Model already exists at $TARGET_DIR"
  du -sh "$TARGET_DIR"
  exit 0
fi

# 启用学术加速
source /etc/network_turbo 2>/dev/null || true

# 使用 modelscope 下载（与现有 8B 模型同一机制）
python3 -c "
from modelscope import snapshot_download
import os

cache_dir = '$CACHE_DIR'
model_id = 'qwen/Qwen2.5-14B-Instruct'

print(f'Downloading {model_id} to {cache_dir}...')
path = snapshot_download(model_id, cache_dir=cache_dir)
print(f'Downloaded to: {path}')

# 显示大小
total = 0
for root, _, files in os.walk(path):
    for f in files:
        total += os.path.getsize(os.path.join(root, f))
print(f'Total size: {total / 1e9:.2f} GB')
"

echo "===== Download Complete ====="
echo "Finished: $(date)"
ls -la "$TARGET_DIR" 2>&1 | head -10
