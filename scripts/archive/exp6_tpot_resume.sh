#!/bin/bash
# Exp-6 TPOT resume: 从 INT8 7B 继续（1.5B 全部完成）
# 使用正确的 per-model INT8 校准文件
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

RD="results/emnlp_defense_v1/runs"

echo "===== Exp-6 TPOT Resume (7B + 8B) ====="
echo "Started: $(date)"

# === 7B (GPU-1) ===
MODEL="Qwen/Qwen2.5-7B-Instruct"
SHORT="7b"
GPU=1

echo "===== INT8-ours 7B (correct calib) ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode int8_ours \
  --calib_file "artifacts/kv_calib_kl_qwen25_7b_int8.json" \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_int8_ours_7b_v2"

echo "===== INT4-RA 7B ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "artifacts/kv_calib_rolealign_7b_v3.json" \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_ra_7b"

echo "===== KIVI 7B ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode kivi_style --quant_bits 4 \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_kivi_7b"

# === 8B (GPU-2) — 串行接着跑 ===
MODEL="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
SHORT="8b"
GPU=2

echo "===== FP16 8B ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode fp16 \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_fp16_8b"

echo "===== INT8-ours 8B ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode int8_ours \
  --calib_file "artifacts/kv_calib_kl_llama31_8b_int8.json" \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_int8_ours_8b"

echo "===== INT4-RA 8B ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "artifacts/kv_calib_rolealign_8b_v3.json" \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_ra_8b"

echo "===== KIVI 8B ====="
CUDA_VISIBLE_DEVICES=$GPU python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode kivi_style --quant_bits 4 \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_kivi_8b"

echo "===== Exp-6 TPOT Resume Complete ====="
echo "Finished: $(date)"
