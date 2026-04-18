#!/bin/bash
# =============================================================================
# Phase 2 编号 6 5-policy 快速回归冒烟
# =============================================================================
# 用 n=5 × 1 task × 5 policies 快速验证所有 policy 路由正常。
# 用途：未来修改 MixedKVCache / generate_loop.py 后的回归测试
# 预估：5 × ~1 min = 5 min 单 GPU
#
# 用法（远端执行）:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_smoke_all_policies.sh
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_smoke_all_policies.sh hotpotqa   # 自选任务
# =============================================================================
set -euo pipefail

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

TASK="${1:-narrativeqa}"
MODEL="Qwen/Qwen2.5-1.5B-Instruct"
N_SAMPLES=5
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_smoke_regression"
POLICY_DIR="artifacts/allocator"
mkdir -p "$OUT_DIR"

POLICIES=(
    "uniform_int4_k4v4"
    "uniform_int8_k8v8"
    "bakv_top3"
    "heuristic_top3"
    "random3_seed42"
)

echo "=============================================="
echo "Phase 2 5-policy 回归冒烟 (n=$N_SAMPLES, task=$TASK)"
echo "时间: $(date)"
echo "Git commit: $(git rev-parse --short HEAD)"
echo "generate_loop.py MD5: $(md5sum src/engine/generate_loop.py | cut -d' ' -f1)"
echo "mixed_kv_cache.py MD5: $(md5sum src/cache/mixed_kv_cache.py | cut -d' ' -f1)"
echo "=============================================="

for POLICY in "${POLICIES[@]}"; do
    RUN_NAME="smoke_${POLICY}_${TASK}_n${N_SAMPLES}"
    MODE_LOG="$OUT_DIR/${RUN_NAME}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"

    if [ ! -f "$POLICY_JSON" ]; then
        echo "[$POLICY] SKIP (policy JSON not found: $POLICY_JSON)"
        continue
    fi

    echo ""
    echo "--- [$POLICY] 启动 @ $(date +%H:%M:%S) ---"
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
        echo "[$POLICY] DONE @ $(date +%H:%M:%S)"
        eng_cnt=$(grep -c "ENG-045" "$MODE_LOG" 2>/dev/null || true)
        echo "  ENG-045 warnings: ${eng_cnt:-0}"
    else
        echo "[$POLICY] FAILED, see $MODE_LOG"
    fi
done

echo ""
echo "=============================================="
echo "回归冒烟 scores（按 timestamp 排序）"
echo "=============================================="
python3 - <<'PY'
import csv, glob, os
out_dir = "results/phase2_smoke_regression"
files = sorted(glob.glob(f"{out_dir}/longbench_task_summary_*.csv"))
print(f"{'file':<60} {'kv_mode':<15} {'metric':<10} {'score':<8}")
for f in files:
    try:
        for r in csv.DictReader(open(f, newline="")):
            name = os.path.basename(f).replace("longbench_task_summary_", "")
            print(f"{name:<60} {r.get('kv_mode',''):<15} {r.get('official_metric_name',''):<10} {r.get('official_metric_value','0'):<8}")
    except Exception as e:
        print(f"  ERROR reading {f}: {e}")
PY

echo ""
echo "如所有 policy 都 DONE + score 非零 → 路由链路健康 ✓"
