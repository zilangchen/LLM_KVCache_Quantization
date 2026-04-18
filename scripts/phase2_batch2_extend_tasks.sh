#!/bin/bash
# =============================================================================
# 验证版 第二批: 扩任务到 dureader / vcsum / trec / lcc（8 runs/task）
# =============================================================================
# B:  {Uniform INT4, BAKV k=1, Heuristic k=1, Random-k k=1 s=42} × 1 task × n=50 = 4 runs
# B+: Random-k k=1 × {123, 2024, 3407, 8888} × 1 task = 4 runs
# 总: 8 runs/task × 4 tasks = 32 runs
# 3 GPU 分配（非均匀）: GPU0=dureader+lcc(16), GPU1=vcsum(8), GPU2=trec(8), wall-clock ~48 min
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_batch2_extend_tasks.sh dureader  (主)
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_batch2_extend_tasks.sh vcsum
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_batch2_extend_tasks.sh trec
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_batch2_extend_tasks.sh lcc      (串在 dureader 后)
# =============================================================================
set -euo pipefail

TASK="${1:-}"
if [ -z "$TASK" ]; then
    echo "ERROR: 必须指定任务名（dureader / vcsum / trec / lcc）"
    exit 2
fi

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_batch2_extend_tasks"
POLICY_DIR="artifacts/allocator/sweep"
mkdir -p "$OUT_DIR"

run_eval() {
    local RUN_NAME="$1"
    local POLICY="$2"
    local MODE_LOG="$OUT_DIR/${RUN_NAME}.log"

    if [ ! -f "$POLICY" ]; then
        # 2026-04-18 修复 Bug B: 关键 baseline 缺失必须 fail-fast，不能静默 SKIP
        # 历史教训: batch2 uniform_int4_k4v4.json 缺失，整批安静跳过 4 runs，
        # 聚合时才发现 batch2 主表缺 Uniform INT4 对照线
        # 关键 baseline 用 whitelist 定义；非关键 policy 仍允许 SKIP（向后兼容）
        local policy_basename=$(basename "$POLICY" .json)
        case "$policy_basename" in
            uniform_int4_k4v4|uniform_int8_k8v8)
                echo "[$RUN_NAME] FATAL: 关键 baseline policy 缺失: $POLICY" >&2
                echo "  → 运行 \`bash scripts/phase2_gen_sweep_policies.sh\` 生成缺失 policy 后重跑" >&2
                exit 3
                ;;
            *)
                echo "[$RUN_NAME] SKIP: policy not found $POLICY (non-critical, 允许跳过)"
                return
                ;;
        esac
    fi

    echo "--- [$RUN_NAME] 启动 @ $(date +%H:%M:%S) ---"
    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY" \
        --longbench_source jsonl \
        --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" \
        --longbench_max_samples $N_SAMPLES \
        --seed $SEED \
        --out_dir "$OUT_DIR" \
        --run_name "$RUN_NAME" \
        > "$MODE_LOG" 2>&1; then
        echo "[$RUN_NAME] DONE @ $(date +%H:%M:%S)"
        eng_cnt=$(grep -c "ENG-045" "$MODE_LOG" 2>/dev/null || true)
        echo "  ENG-045 warnings: ${eng_cnt:-0}"
    else
        echo "[$RUN_NAME] FAILED, see $MODE_LOG"
    fi
}

echo "=============================================="
echo "验证版 第二批 扩任务 task=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

# B: 4 configs × 1 task × n=50
for PNAME in uniform_int4_k4v4 bakv_k1 heuristic_k1 random3_k1_seed42; do
    RN="phase2v_b2_1p5b_int4mixedkv_${PNAME}_${TASK}_n${N_SAMPLES}"
    run_eval "$RN" "$POLICY_DIR/${PNAME}.json"
done

# B+: Random-k k=1 × 4 new seeds × 1 task
for S in 123 2024 3407 8888; do
    RN="phase2v_b2_1p5b_int4mixedkv_random3_k1_seed${S}_${TASK}_n${N_SAMPLES}"
    run_eval "$RN" "$POLICY_DIR/random3_k1_seed${S}.json"
done

echo ""
echo "=============================================="
echo "第二批 task $TASK 完成: $(date)"
ls -la "$OUT_DIR/" | grep "$TASK" | head -15
echo "=============================================="
