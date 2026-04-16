#!/bin/bash
# ================================================================
# Step 3: K/V 消融实验 — 产出 kv_ablation/ 数据
# ================================================================
# 输出: results/final/final_data/kv_ablation/
# 原始脚本: scripts/archive/expansion_gpu0.sh, expansion_gpu1.sh
# GPU 时间: ~8-10h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

OUT="results/final/final_data/kv_ablation"

# --- K/V 消融 RULER + LongBench (由 config 中的 ablation entries 控制) ---
python3 scripts/run_experiments.py \
    --config configs/exp_matrix.yaml \
    --tasks eval_ruler,eval_longbench \
    --seeds 1234,1235,1236 \
    --out_dir "$OUT"

# --- K/V 消融 PPL (直接调用，指定 kv_config) ---
for MODEL in "Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-7B-Instruct" \
             "meta-llama/Llama-3.1-8B-Instruct"; do
    for KV_CFG in "K4V16" "K16V4" "K8V4" "K4V8"; do
        for SEED in 1234 1235 1236; do
            python3 scripts/eval_ppl.py \
                --model_id "$MODEL" \
                --kv_mode int4_mixed_kv \
                --seed $SEED \
                --out_dir "$OUT/runs"
        done
    done
done
