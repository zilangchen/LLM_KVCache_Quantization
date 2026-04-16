#!/bin/bash
# E-3: n=10 seeds — 补跑 seed 1239-1243 (当前已有 1234-1238)
# 3 卡并行 3 模型，质量评测可共享 GPU
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

GPU="${1:-0}"
export CUDA_VISIBLE_DEVICES=$GPU

RD="results/emnlp_defense_v1/runs"

# 模型配置
MODELS_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
MODELS_7B="Qwen/Qwen2.5-7B-Instruct"
MODELS_8B="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"

CALIB_1P5B="artifacts/kv_calib_kl_selected_v3_quick.json"
CALIB_7B="artifacts/kv_calib_kl_qwen25_7b_int8.json"
CALIB_8B="artifacts/kv_calib_kl_llama31_8b_int8.json"

RA_CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
RA_CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
RA_CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"

# GPU-0: 1.5B, GPU-1: 7B, GPU-2: 8B
case $GPU in
  0) MODEL=$MODELS_1P5B; SHORT="1p5b"; CALIB=$CALIB_1P5B; RA_CALIB=$RA_CALIB_1P5B ;;
  1) MODEL=$MODELS_7B;   SHORT="7b";   CALIB=$CALIB_7B;   RA_CALIB=$RA_CALIB_7B ;;
  2) MODEL=$MODELS_8B;   SHORT="8b";   CALIB=$CALIB_8B;   RA_CALIB=$RA_CALIB_8B ;;
  *) echo "GPU must be 0/1/2"; exit 1 ;;
esac

echo "===== E-3: n=10 seeds ($SHORT, GPU-$GPU) ====="
echo "Started: $(date)"

for SEED in 1239 1240 1241 1242 1243; do
  echo "--- INT8-ours PPL seed=$SEED ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode int8_ours \
    --calib_file "$CALIB" \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir "$RD/ppl_int8_n10_${SHORT}_s${SEED}"

  echo "--- INT8-ours Needle seed=$SEED ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" --kv_mode int8_ours \
    --calib_file "$CALIB" \
    --seq_len 4096 --seed $SEED \
    --save_csv --out_dir "$RD/needle_int8_n10_${SHORT}_s${SEED}"

  echo "--- INT4-RA PPL seed=$SEED ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$RA_CALIB" \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir "$RD/ppl_ra_n10_${SHORT}_s${SEED}"

  echo "--- INT4-RA Needle seed=$SEED ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$RA_CALIB" \
    --seq_len 4096 --seed $SEED \
    --save_csv --out_dir "$RD/needle_ra_n10_${SHORT}_s${SEED}"

  echo "--- FP16 PPL seed=$SEED ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode fp16 \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir "$RD/ppl_fp16_n10_${SHORT}_s${SEED}"
done

echo "===== E-3 ($SHORT) Complete ====="
echo "Finished: $(date)"
