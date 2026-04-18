#!/bin/bash
# =============================================================================
# Phase 1 编号 2: 1.5B × 官方 LongBench × 4 modes × 1 个任务
# =============================================================================
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase1_run_task.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase1_run_task.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase1_run_task.sh gov_report
#
# 对应执行表: 编号 2（3 GPU 并行分工按 task 维度拆分）
# 预估耗时（单 GPU 单任务 4 模式）: ~5-8 分钟（jsonl 免下载）
# =============================================================================
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定任务名（narrativeqa / hotpotqa / gov_report）"
    exit 2
fi

cd /root/LLM_KVCache_Quantization

# 固定配置
MODEL="Qwen/Qwen2.5-1.5B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase1_official"
mkdir -p "$OUT_DIR"

# Calibration 文件映射（仅 INT 模式需要）
CALIB_INT8="artifacts/kv_calib_kl_selected_v2.json"
CALIB_INT4_ASYM="artifacts/kv_calib_rolealign_1p5b.json"

# 待跑的 4 模式
MODES=(fp16 int8_ours kivi_style int4_ours_asym)

echo "=============================================="
echo "Phase 1 编号 2 任务开始: $TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "JSONL 源: $JSONL_DIR"
echo "=============================================="

for MODE in "${MODES[@]}"; do
    RUN_NAME="phase1_1p5b_${MODE}_${TASK}_n${N_SAMPLES}"
    MODE_LOG="$OUT_DIR/${RUN_NAME}.log"

    # 根据 mode 选 calib_file
    CALIB_ARG=""
    case "$MODE" in
        fp16)           CALIB_ARG="" ;;
        int8_ours)      CALIB_ARG="--calib_file $CALIB_INT8" ;;
        kivi_style)     CALIB_ARG="" ;;
        int4_ours_asym) CALIB_ARG="--calib_file $CALIB_INT4_ASYM" ;;
    esac

    echo ""
    echo "--- [$TASK/$MODE] 启动 @ $(date +%H:%M:%S) ---"

    # 使用 || true 允许单个 mode 失败不阻断整个脚本
    # 但记录失败状态
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
        echo "[$TASK/$MODE] ✅ DONE @ $(date +%H:%M:%S)"
    else
        echo "[$TASK/$MODE] ❌ FAILED, see $MODE_LOG"
    fi
done

echo "=============================================="
echo "Phase 1 编号 2 任务 $TASK 完成: $(date)"
echo "=============================================="
ls -la "$OUT_DIR/" | grep "$TASK" | head -10
