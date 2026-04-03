#!/bin/bash
# PPL 补跑: target_tokens=32768 (匹配主表条件)
# 可以与 RULER 并行跑（PPL 是质量指标，不受并行影响）
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

RD="results/emnlp_rolealign_v2"
mkdir -p "$RD/runs" "$RD/logs"

MODELS=(
  "Qwen/Qwen2.5-1.5B-Instruct|artifacts/kv_calib_rolealign_1p5b.json|1p5b"
  "Qwen/Qwen2.5-7B-Instruct|artifacts/kv_calib_rolealign_7b.json|7b"
  "/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct|artifacts/kv_calib_rolealign_8b.json|8b"
)

echo "=== PPL 32K-token eval: $(date '+%Y-%m-%d %H:%M:%S') ==="

for entry in "${MODELS[@]}"; do
  IFS='|' read -r MODEL_ID CALIB TAG <<< "$entry"

  for KV_MODE in int4_ours_asym fp16; do
    CALIB_ARG=""
    BITS_ARG=""
    if [ "$KV_MODE" = "int4_ours_asym" ]; then
      CALIB_ARG="--calib_file $CALIB"
      BITS_ARG="--quant_bits 4"
    fi

    for SEED in 1234 1235 1236 1237 1238; do
      echo ">>> ${TAG} PPL-32K ${KV_MODE} seed=${SEED}"
      python3 scripts/eval_ppl.py \
        --model_id "$MODEL_ID" \
        --kv_mode "$KV_MODE" \
        $BITS_ARG $CALIB_ARG \
        --target_tokens 32768 \
        --seed "$SEED" \
        --save_csv \
        --out_dir "$RD/runs/ppl_32k_${KV_MODE}_${TAG}_s${SEED}" \
        2>&1 | tee -a "$RD/logs/ppl_32k_${TAG}.log"
    done
  done
done

echo "=== PPL 32K ALL DONE: $(date '+%Y-%m-%d %H:%M:%S') ==="
