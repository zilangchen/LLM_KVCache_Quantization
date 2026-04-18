#!/bin/bash
# =============================================================================
# Phase 2 编号 8 C2 诊断补丁: LLaMA-8B × bakv_mean_k1 × 3 tasks = 3 runs
# =============================================================================
# 目的: 判断 8B 的 low-budget (k=1) regime 归类:
#   (A) 像 1.5B (aggregation-insensitive, k=1 仍强) → max_k1 和 mean_k1 都胜 Heuristic
#   (B) 像 7B max 模式 (k=1 失败, mean 救回) → max_k1 输 Heuristic, mean_k1 胜
#   (C) 像 7B 但更极端 → 两者都输
#   这 3 runs 不加进去，C2 只能答 "8B best-k 在哪"，无法答 "8B 如何被 regime 归类"。
#
# 用法（3 GPU 按 task 拆分，可在 C2 主批之后串跑）:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_diag_8b_mean.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_diag_8b_mean.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_diag_8b_mean.sh gov_report
#
# 每 GPU 1 run × ~5 min = ~5 min wall-clock（与 C2 主批串行）
# =============================================================================
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定任务名（narrativeqa / hotpotqa / gov_report）"
    exit 2
fi

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

# LLaMA-8B: 强制 offline mode（hf-mirror 代理不稳定，本地 cache 完整）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="meta-llama/Llama-3.1-8B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c2_llama8b"
POLICY_DIR="artifacts/allocator/sweep_8b"
mkdir -p "$OUT_DIR"

POLICY="bakv_mean_k1"

RUN_NAME="phase2c2_8b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
MODE_LOG="$OUT_DIR/${RUN_NAME}.log"
POLICY_JSON="$POLICY_DIR/${POLICY}.json"

echo "=============================================="
echo "C2 诊断补丁 8B mean_k1 task=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

if [ ! -f "$POLICY_JSON" ]; then
    echo "[$TASK/$POLICY] FATAL: policy JSON not found $POLICY_JSON"
    exit 3
fi

echo "--- [$TASK/$POLICY] 启动 @ $(date +%H:%M:%S) ---"
if python3 scripts/eval_longbench.py \
    --model_id "$MODEL" \
    --kv_mode int4_mixed_kv \
    --policy_json "$POLICY_JSON" \
    --longbench_source jsonl \
    --longbench_dataset_path "$JSONL_DIR" \
    --longbench_tasks "$TASK" \
    --longbench_max_samples $N_SAMPLES \
    --seed $SEED \
    --out_dir "$OUT_DIR" \
    --run_name "$RUN_NAME" \
    > "$MODE_LOG" 2>&1; then
    echo "[$TASK/$POLICY] DONE @ $(date +%H:%M:%S)"
    eng_cnt=$(grep -c "ENG-045" "$MODE_LOG" 2>/dev/null || true)
    echo "  ENG-045 warnings: ${eng_cnt:-0}"
else
    echo "[$TASK/$POLICY] FAILED, see $MODE_LOG"
    exit 4
fi

echo ""
echo "=============================================="
echo "C2 诊断补丁 task $TASK 完成: $(date)"
echo "=============================================="
