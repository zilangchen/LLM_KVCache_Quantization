#!/bin/bash
# GPU-2 链式任务: PPL RA v3 多 seed + Needle RA 多 ctx
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

# PPL RA v3 seed 1235, 1236 (seed 1234 已完成)
for SEED in 1235 1236; do
  echo "===== PPL INT4-RA v3 seed=$SEED ====="
  python3 scripts/eval_ppl.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_ra_v3_1p5b_s${SEED}
done

# Needle RA v3 多上下文 (4K, 8K, 16K — 32K 已完成)
for CTX in 4096 8192 16384; do
  echo "===== Needle INT4-RA v3 ctx=$CTX ====="
  python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
    --seq_len $CTX --seed 1234 \
    --save_csv --out_dir results/emnlp_defense_v1/runs/needle_ra_v3_ctx${CTX}_1p5b
done

echo "===== All GPU-2 chain Done ====="
echo "Finished: $(date)"
