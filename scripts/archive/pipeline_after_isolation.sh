#!/bin/bash
# Pipeline: isolation 完成后自动启动 64K context，再自动启动 14B（如果模型就绪）
# 这是一个"守护进程"，应在独立 tmux session 里运行
# 目的：避免手动等待 + 分阶段启动，全链路自动化

set -euo pipefail
cd /root/LLM_KVCache_Quantization

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# ===== Phase 1: 等待 isolation 完成 =====
echo "===== Pipeline: Waiting for isolation =====" | tee -a "$LOG_DIR/pipeline.log"
echo "Started: $(date)" | tee -a "$LOG_DIR/pipeline.log"

while tmux has-session -t isolation 2>/dev/null; do
  sleep 60
  echo "[$(date +%H:%M:%S)] isolation still running..." | tee -a "$LOG_DIR/pipeline.log"
done

echo "===== Phase 1: isolation completed at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"

# 验证 isolation 结果
ISOLATION_CSVS=$(find results/emnlp_defense_v1/runs/isolation_* -name "profile_*.csv" 2>/dev/null | wc -l)
echo "Isolation CSVs: $ISOLATION_CSVS (expected 6: 2 obj × 3 evals)" | tee -a "$LOG_DIR/pipeline.log"

# ===== Phase 2: 启动 64K context =====
echo "===== Phase 2: Starting 64K context at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"
bash scripts/ablation_context_64k.sh 2>&1 | tee "$LOG_DIR/ablation_64k_$(date +%Y%m%d_%H%M%S).log" || {
  echo "WARNING: 64K context failed, continuing..." | tee -a "$LOG_DIR/pipeline.log"
}
echo "===== Phase 2: 64K context done at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"

# ===== Phase 3: 等待 14B 下载完成 =====
echo "===== Phase 3: Waiting for 14B download =====" | tee -a "$LOG_DIR/pipeline.log"

while tmux has-session -t dl_14b 2>/dev/null; do
  sleep 60
  echo "[$(date +%H:%M:%S)] 14B download still running..." | tee -a "$LOG_DIR/pipeline.log"
done

echo "===== Phase 3: 14B download completed at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"

# 验证模型已下载
MODEL_DIR="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"
if [ ! -d "$MODEL_DIR" ]; then
  echo "ERROR: 14B model not found at $MODEL_DIR, skipping 14B experiment" | tee -a "$LOG_DIR/pipeline.log"
  echo "===== Pipeline ended at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"
  exit 0
fi

# ===== Phase 4: 启动 14B 实验 =====
echo "===== Phase 4: Starting 14B experiment at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"
bash scripts/ablation_14b_full.sh 2>&1 | tee "$LOG_DIR/ablation_14b_$(date +%Y%m%d_%H%M%S).log" || {
  echo "WARNING: 14B experiment failed" | tee -a "$LOG_DIR/pipeline.log"
}

echo "===== Pipeline complete at $(date) =====" | tee -a "$LOG_DIR/pipeline.log"
