#!/bin/bash
# =============================================================================
# 验证版 第一批: 1.5B 稳定性验证 20 runs/task（A1+A2+A3+A4）
# =============================================================================
# A1: Random-k k=1 × 4 new seeds × 1 task = 4 runs（seed=42 已跑，复用）
# A2: Random-k k=3 × 4 new seeds × 1 task = 4 runs
# A3: {BAKV k=1, Heuristic k=1, Random-k k=1 s=42} × n∈{100,200} × 1 task = 6 runs
# A4: {BAKV k=1, Heuristic k=1, Random-k k=1 s=42} × offset∈{50,100} × n=50 × 1 task = 6 runs
# 总: 4+4+6+6 = 20 runs/task；3 GPU 并行 ≈ 60 min
#
# 用法:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_batch1_verify_1p5b.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_batch1_verify_1p5b.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_batch1_verify_1p5b.sh gov_report
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

cd /root/LLM_KVCache_Quantization

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
SEED=1234  # eval seed (greedy, 不变)
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_batch1_verify_1p5b"
POLICY_DIR="artifacts/allocator/sweep"
mkdir -p "$OUT_DIR"

run_eval() {
    local RUN_NAME="$1"
    local POLICY="$2"
    local N="$3"
    local OFFSET="$4"
    local MODE_LOG="$OUT_DIR/${RUN_NAME}.log"

    if [ ! -f "$POLICY" ]; then
        echo "[$RUN_NAME] SKIP: policy not found $POLICY"
        return
    fi

    echo "--- [$RUN_NAME] 启动 @ $(date +%H:%M:%S) ---"
    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY" \
        --longbench_source jsonl \
        --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" \
        --longbench_max_samples "$N" \
        --longbench_sample_offset "$OFFSET" \
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
echo "验证版 第一批 task=$TASK"
echo "时间: $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name,index --format=csv,noheader | head -1)"
echo "=============================================="

# A1: Random-k k=1 × 4 new seeds
for S in 123 2024 3407 8888; do
    RN="phase2v_b1_1p5b_int4mixedkv_random3_k1_seed${S}_${TASK}_n50_off0"
    run_eval "$RN" "$POLICY_DIR/random3_k1_seed${S}.json" 50 0
done

# A2: Random-k k=3 × 4 new seeds
for S in 123 2024 3407 8888; do
    RN="phase2v_b1_1p5b_int4mixedkv_random3_k3_seed${S}_${TASK}_n50_off0"
    run_eval "$RN" "$POLICY_DIR/random3_k3_seed${S}.json" 50 0
done

# A3: 扩 n × 3 configs × n ∈ {100, 200}
for N in 100 200; do
    for PNAME in bakv_k1 heuristic_k1 random3_k1_seed42; do
        RN="phase2v_b1_1p5b_int4mixedkv_${PNAME}_${TASK}_n${N}_off0"
        run_eval "$RN" "$POLICY_DIR/${PNAME}.json" $N 0
    done
done

# A4: Sample offset × 3 configs × offset ∈ {50, 100}
for OFFSET in 50 100; do
    for PNAME in bakv_k1 heuristic_k1 random3_k1_seed42; do
        RN="phase2v_b1_1p5b_int4mixedkv_${PNAME}_${TASK}_n50_off${OFFSET}"
        run_eval "$RN" "$POLICY_DIR/${PNAME}.json" 50 "$OFFSET"
    done
done

echo ""
echo "=============================================="
echo "第一批 task $TASK 完成: $(date)"
ls -la "$OUT_DIR/" | grep "$TASK" | head -25
echo "=============================================="
