#!/bin/bash
# =============================================================================
# Phase 1 kivi_style 补跑（ENG-045-v2 补丁后验证用）
# =============================================================================
# 只重跑 kivi_style 1 模式 × 1 任务，用独立输出目录 phase1_official_v2
# 以便和修前数据（phase1_official/）逐点对比。
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase1_rerun_kivi.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase1_rerun_kivi.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase1_rerun_kivi.sh gov_report
# =============================================================================
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定任务名（narrativeqa / hotpotqa / gov_report）"
    exit 2
fi

# 激活 conda base 环境（tmux detached 下默认是 non-login shell，不会自动加载 .bashrc）
if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization
mkdir -p results/phase1_official_v2

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase1_official_v2"
mkdir -p "$OUT_DIR"

MODE="kivi_style"
RUN_NAME="phase1_1p5b_${MODE}_${TASK}_n${N_SAMPLES}_v2"
MODE_LOG="$OUT_DIR/${RUN_NAME}.log"

echo "=============================================="
echo "Phase 1 ENG-045-v2 rerun: $TASK / $MODE"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "Git commit: $(git rev-parse --short HEAD)"
echo "generate_loop.py MD5: $(md5sum src/engine/generate_loop.py | cut -d' ' -f1)"
echo "=============================================="

if python3 scripts/eval_longbench.py \
    --model_id "$MODEL" \
    --kv_mode "$MODE" \
    --longbench_source jsonl \
    --longbench_dataset_path "$JSONL_DIR" \
    --longbench_tasks "$TASK" \
    --longbench_max_samples $N_SAMPLES \
    --seed $SEED \
    --out_dir "$OUT_DIR" \
    --run_name "$RUN_NAME" \
    > "$MODE_LOG" 2>&1; then
    echo "[$TASK/$MODE/v2] DONE @ $(date +%H:%M:%S)"
    echo "--- ENG-045 warning counts (修后应为 0 或极少) ---"
    grep -c "ENG-045" "$MODE_LOG" || echo "0 (no ENG-045 matches)"
else
    echo "[$TASK/$MODE/v2] FAILED, see $MODE_LOG"
    exit 1
fi

echo "--- 产出 CSV ---"
ls -la "$OUT_DIR/" | grep "$TASK" | head -5
