#!/bin/bash
# Baseline: 1.5B + 14B FP16 RULER (补 FI/RA vs FP16 对比的缺口)
#
# 用法:
#   MODEL=1p5b bash stage_baseline_fp16_ruler.sh  # 只跑 1.5B (可与 Stage 5 并行)
#   MODEL=14b  bash stage_baseline_fp16_ruler.sh  # 只跑 14B (需独占 GPU)
#
# 默认 MODEL=1p5b。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
MODEL_TAG="${MODEL:-1p5b}"

case "$MODEL_TAG" in
  1p5b)
    MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
    SEQ_LENS=(4096 8192 16384 32704)
    ;;
  14b)
    MODEL_ID="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"
    SEQ_LENS=(4096 8192 16384)  # skip 32K for 14B (memory)
    ;;
  *)
    echo "Unknown MODEL_TAG: $MODEL_TAG"
    exit 1
    ;;
esac

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag (exists)"
    return 0
  fi
  echo ""; echo "═══ RUN: $tag ═══"
  date '+%Y-%m-%d %H:%M:%S'
  "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -20
  echo "  DONE: $tag"
}

echo "═══ Baseline FP16 RULER: ${MODEL_TAG} ═══"
echo "Model: $MODEL_ID"
echo "Seq lens: ${SEQ_LENS[*]}"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

for SL in "${SEQ_LENS[@]}"; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_fp16_${MODEL_TAG}_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py \
        --model_id "$MODEL_ID" --kv_mode fp16 \
        --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

echo ""
echo "═══ Baseline FP16 RULER ${MODEL_TAG} complete ═══"
date '+%Y-%m-%d %H:%M:%S'
