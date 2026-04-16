#!/bin/bash
# ================================================================
# Step 3: K/V 消融实验 — 产出 kv_ablation/ 数据
# ================================================================
# 输出: results/final/final_data/kv_ablation/
# 内容: K-only/V-only/K4V8/MixedKV 消融 (PPL, RULER, LongBench)
# 原始脚本: scripts/archive/expansion_gpu0.sh, expansion_gpu1.sh
# GPU 时间: ~8-10h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0

CFG="configs/exp_matrix.yaml"
RESULTS_TAG="kv_ablation"

# --- K/V 消融 RULER (1.5B, 7B, 8B, Mistral) ---
for MODEL in "1.5B" "7B" "8B" "Mistral"; do
    python3 scripts/run_experiments.py \
        --config "$CFG" \
        --tasks eval_ruler \
        --seeds 1234,1235,1236 \
        --kv_modes "int4_mixed_kv,int8_baseline" \
        --results_tag "$RESULTS_TAG"
done

# --- K/V 消融 PPL (直接调用 eval_ppl.py) ---
# K@INT4+V@FP16, K@FP16+V@INT4, K@INT8+V@INT4, K@INT4+V@INT8
for CONFIG in "K4V16" "K16V4" "K8V4" "K4V8"; do
    python3 scripts/eval_ppl.py \
        --model_id Qwen/Qwen2.5-1.5B-Instruct \
        --kv_mode "int4_mixed_kv" \
        --kv_config "$CONFIG" \
        --seeds 1234,1235,1236
done

# --- B10 校准灵敏度消融 ---
python3 scripts/run_experiments.py \
    --config "$CFG" \
    --tasks eval_ppl \
    --calib_batch_sizes 1,2,4,8,16,32,64,128,256 \
    --results_tag "$RESULTS_TAG"
