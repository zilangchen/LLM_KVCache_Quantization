#!/bin/bash
# ================================================================
# Step 6: 14B 全套评测 — 产出 backend_comparison 中的 14B 数据
# ================================================================
# 输出: results/final/final_data/backend_comparison/runs/
# 原始脚本: scripts/batch_p012/stage5_phase4_14b_full.sh
# GPU 时间: ~6-8h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

MODEL="Qwen/Qwen2.5-14B-Instruct"
OUT="results/final/final_data/backend_comparison/runs"

# --- PPL ---
for SEED in 1234 1235 1236; do
    python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode int4_ours_asym \
        --seed $SEED --out_dir "$OUT"
done

# --- Needle (4K-32K) ---
for CTX in 4096 8192 16384 32704; do
    for SEED in 1234 1235 1236; do
        python3 scripts/eval_needle.py --model_id "$MODEL" --kv_mode int4_ours_asym \
            --context_length $CTX --seed $SEED --out_dir "$OUT"
    done
done

# --- RULER (4K-16K) ---
for CTX in 4096 8192 16384; do
    for SEED in 1234 1235 1236; do
        python3 scripts/eval_ruler.py --model_id "$MODEL" --kv_mode int4_ours_asym \
            --ruler_context_len $CTX --seed $SEED --out_dir "$OUT"
    done
done

# --- K/V 消融 PPL ---
for KV_CFG in "K16V4" "K4V16" "K8V4" "K4V8"; do
    for SEED in 1234 1235 1236; do
        python3 scripts/eval_ppl.py --model_id "$MODEL" \
            --kv_mode int4_mixed_kv \
            --seed $SEED --out_dir "$OUT"
    done
done
