#!/bin/bash
# =============================================================================
# Phase 1 编号 4 路线 α: Qwen2.5-7B × 官方 LongBench × 4 modes × 1 个任务
# =============================================================================
# 仅在编号 5 闸门通过前作为"同格式复核"使用；编号 2 完成后再启动。
# 3 GPU 并行拆分同 phase1_run_task.sh（narrativeqa/hotpotqa/gov_report）
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase1_run_task_7b.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase1_run_task_7b.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase1_run_task_7b.sh gov_report
#
# 预估耗时（7B 单 GPU 单任务 4 模式）: ~15-25 分钟（模型大，略慢于 1.5B）
# =============================================================================
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定任务名（narrativeqa / hotpotqa / gov_report）"
    exit 2
fi

# 激活 conda base 环境（tmux detached 下默认是 non-login shell）
if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

# 固定配置
MODEL="Qwen/Qwen2.5-7B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase1_official_7b"
mkdir -p "$OUT_DIR"

# 7B Calibration 文件
CALIB_INT8="artifacts/kv_calib_kl_qwen25_7b_int8.json"
CALIB_INT4_ASYM="artifacts/kv_calib_rolealign_7b_v3.json"

# 待跑 4 模式
MODES=(fp16 int8_ours kivi_style int4_ours_asym)

echo "=============================================="
echo "Phase 1 编号 4 (α: 7B 复核) 任务: $TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

for MODE in "${MODES[@]}"; do
    RUN_NAME="phase1_7b_${MODE}_${TASK}_n${N_SAMPLES}"
    MODE_LOG="$OUT_DIR/${RUN_NAME}.log"

    CALIB_ARG=""
    case "$MODE" in
        fp16)           CALIB_ARG="" ;;
        int8_ours)      CALIB_ARG="--calib_file $CALIB_INT8" ;;
        kivi_style)     CALIB_ARG="" ;;
        int4_ours_asym) CALIB_ARG="--calib_file $CALIB_INT4_ASYM" ;;
    esac

    echo ""
    echo "--- [7B/$TASK/$MODE] 启动 @ $(date +%H:%M:%S) ---"

    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" \
        --kv_mode "$MODE" \
        $CALIB_ARG \
        --longbench_source jsonl \
        --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" \
        --longbench_max_samples $N_SAMPLES \
        --seed $SEED \
        --out_dir "$OUT_DIR" \
        --run_name "$RUN_NAME" \
        > "$MODE_LOG" 2>&1; then
        echo "[7B/$TASK/$MODE] ✅ DONE @ $(date +%H:%M:%S)"
    else
        echo "[7B/$TASK/$MODE] ❌ FAILED, see $MODE_LOG"
    fi
done

echo "=============================================="
echo "Phase 1 编号 4 (7B) 任务 $TASK 完成: $(date)"
echo "=============================================="
ls -la "$OUT_DIR/" | grep "$TASK" | head -10
