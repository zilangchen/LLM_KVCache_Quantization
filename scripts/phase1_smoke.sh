#!/bin/bash
# =============================================================================
# Phase 1 编号 1: LongBench 官方入口冒烟验证
# =============================================================================
# 目的: 在 Qwen2.5-1.5B + fp16 + narrativeqa + max_samples=10 上验证:
#   1. HuggingFace 官方 LongBench 数据加载链路
#   2. eval_longbench.py 的 CSV 输出 schema
#   3. GPU 基本可用性
# 预期耗时: 3-5 分钟（模型已缓存）或 10-15 分钟（首次下载）
# 对应执行表: 13 步编号 1 第 3 步
# =============================================================================
set -euo pipefail

cd /root/LLM_KVCache_Quantization

# 启用学术加速（HuggingFace 下载）
source /etc/network_turbo 2>/dev/null || true

# 固定使用 GPU 0
export CUDA_VISIBLE_DEVICES=0

# 输出目录
OUT_DIR="results/phase1_smoke"
mkdir -p "$OUT_DIR"

echo "=============================================="
echo "Phase 1 编号 1 冒烟开始: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,memory.free --format=csv,noheader | head -1)"
echo "=============================================="

# LongBench 数据源（改用本地 jsonl，绕过 datasets 4.5.0 + 代理问题）
LONGBENCH_JSONL_DIR="/root/autodl-tmp/longbench_data/data"

# 冒烟核心命令
python3 scripts/eval_longbench.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode fp16 \
    --longbench_source jsonl \
    --longbench_dataset_path "$LONGBENCH_JSONL_DIR" \
    --longbench_tasks narrativeqa \
    --longbench_max_samples 10 \
    --seed 1234 \
    --out_dir "$OUT_DIR" \
    --run_name smoke_1p5b_fp16_narrativeqa_n10 \
    2>&1 | tee "$OUT_DIR/smoke_console.log"

EXIT_CODE=${PIPESTATUS[0]}
echo "=============================================="
echo "冒烟退出码: $EXIT_CODE"
echo "完成时间: $(date)"
echo "=============================================="
ls -la "$OUT_DIR/" || true

exit $EXIT_CODE
