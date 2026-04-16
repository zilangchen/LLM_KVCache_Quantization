#!/bin/bash
# GPU-2: FP16 + INT8 cs=8 PPL baselines
set -euo pipefail
export CUDA_VISIBLE_DEVICES=2
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== FP16 cs=8 PPL ====="
echo "Started: $(date)"
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode fp16 --chunk_size 8 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_fp16_cs8_1p5b

echo "===== INT8-ours cs=8 PPL ====="
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int8_ours \
  --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
  --chunk_size 8 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_int8_cs8_1p5b

echo "===== Done ====="
echo "Finished: $(date)"
