#!/bin/bash
# ================================================================
# Step 6: 14B 全套评测 — 产出 backend_comparison/ppl_ra_14b 等数据
# ================================================================
# 输出: backend_comparison/runs/{ppl,needle,ruler}_*_14b*
# 内容: 14B PPL, Needle (4K-32K), RULER (4K-16K), K/V 消融
# 原始脚本: scripts/batch_p012/stage5_phase4_14b_full.sh
# GPU 时间: ~6-8h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1

MODEL="Qwen/Qwen2.5-14B-Instruct"

# --- PPL ---
python3 scripts/eval_ppl.py --model_id "$MODEL" --kv_mode int4_ours_asym \
    --calib_file artifacts/kv_calib_rolealign_14b_v3.json \
    --seeds 1234,1235,1236

# --- Needle (4K-32K) ---
for CTX in 4096 8192 16384 32704; do
    python3 scripts/eval_needle.py --model_id "$MODEL" --kv_mode int4_ours_asym \
        --context_length $CTX --seeds 1234,1235,1236
done

# --- RULER (4K-16K) ---
for CTX in 4096 8192 16384; do
    python3 scripts/eval_ruler.py --model_id "$MODEL" --kv_mode int4_ours_asym \
        --seq_len $CTX --seeds 1234,1235,1236
done

# --- K/V 消融 PPL ---
for CONFIG in "K16V4" "K4V16" "K8V4" "K4V8"; do
    python3 scripts/eval_ppl.py --model_id "$MODEL" \
        --kv_mode int4_mixed_kv --kv_config "$CONFIG" \
        --seeds 1234,1235,1236
done
