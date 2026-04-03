#!/bin/bash
# Exp-6: TPOT 独占 profiling (3 卡串行, v3 校准)
# 必须 3 卡全空时跑！profiling 结果对 GPU 共享敏感
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

RD="results/emnlp_defense_v1/runs"
MODELS=("Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-7B-Instruct" "/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct")
SHORTS=("1p5b" "7b" "8b")
CALIBS=("artifacts/kv_calib_rolealign_1p5b_v3.json" "artifacts/kv_calib_rolealign_7b_v3.json" "artifacts/kv_calib_rolealign_8b_v3.json")

echo "===== Exp-6 TPOT Exclusive Profiling ====="
echo "Started: $(date)"
echo "WARNING: 3 GPUs must be idle for accurate TPOT!"

for i in 0 1 2; do
  MODEL="${MODELS[$i]}"
  SHORT="${SHORTS[$i]}"
  CALIB="${CALIBS[$i]}"

  echo ""
  echo "===== Model: $SHORT (GPU-$i) ====="

  # FP16 baseline
  echo "--- FP16 TPOT ---"
  CUDA_VISIBLE_DEVICES=$i python3 scripts/profile_latency.py \
    --model_id "$MODEL" --kv_mode fp16 \
    --seq_len 4096 --gen_len 128 --batch 1 \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/tpot_fp16_${SHORT}"

  # INT8-ours (Triton fused)
  echo "--- INT8-ours TPOT ---"
  CUDA_VISIBLE_DEVICES=$i python3 scripts/profile_latency.py \
    --model_id "$MODEL" --kv_mode int8_ours \
    --calib_file "artifacts/kv_calib_kl_selected_v3_quick.json" \
    --seq_len 4096 --gen_len 128 --batch 1 \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/tpot_int8_ours_${SHORT}"

  # INT4-RoleAlign (torch_ref)
  echo "--- INT4-RA TPOT ---"
  CUDA_VISIBLE_DEVICES=$i python3 scripts/profile_latency.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" \
    --seq_len 4096 --gen_len 128 --batch 1 \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/tpot_ra_${SHORT}"

  # KIVI-style INT4 (torch_ref)
  echo "--- KIVI TPOT ---"
  CUDA_VISIBLE_DEVICES=$i python3 scripts/profile_latency.py \
    --model_id "$MODEL" --kv_mode kivi_style --quant_bits 4 \
    --seq_len 4096 --gen_len 128 --batch 1 \
    --warmup 3 --runs 5 --save_csv \
    --out_dir "$RD/tpot_kivi_${SHORT}"
done

echo ""
echo "===== Exp-6 TPOT Complete ====="
echo "Finished: $(date)"
