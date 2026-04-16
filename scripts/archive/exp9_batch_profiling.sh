#!/bin/bash
# Exp-9: Batch>1 INT4-RA + FP16 profiling (独占 GPU-0)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

RD="results/emnlp_defense_v1/runs"

echo "===== Exp-9: Batch>1 Profiling ====="
echo "Started: $(date)"

for BATCH in 1 4 8 16; do
  echo "--- FP16 batch=$BATCH ---"
  python3 scripts/profile_latency.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode fp16 \
    --seq_len 8192 --gen_len 128 --batch $BATCH \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/batch_fp16_b${BATCH}_1p5b"

  echo "--- INT4-RA batch=$BATCH ---"
  python3 scripts/profile_latency.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
    --seq_len 8192 --gen_len 128 --batch $BATCH \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/batch_ra_b${BATCH}_1p5b"

  echo "--- INT8-ours batch=$BATCH ---"
  python3 scripts/profile_latency.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int8_ours \
    --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
    --seq_len 8192 --gen_len 128 --batch $BATCH \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/batch_int8_b${BATCH}_1p5b"
done

echo "===== Exp-9 Complete ====="
echo "Finished: $(date)"
