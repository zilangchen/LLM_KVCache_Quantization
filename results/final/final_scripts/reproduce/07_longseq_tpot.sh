#!/bin/bash
# ================================================================
# Step 7: 长序列 TPOT scaling
# ================================================================
# 输出: backend_comparison/runs/longseq_{fp16,kivi,torchref,triton_ra}_{1p5b,7b,14b}_s{4096..32704}
# 原始: scripts/batch_p012/stage7_rerun.sh
# GPU: ~4-6h (需独占)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

RD="results/final/final_data/backend_comparison/runs"
TPOT_COMMON="--gen_len 64 --runs 10 --warmup 5 --seed 1234"

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"

run_one() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag"; return 0
  fi
  echo "═══ RUN: $tag ═══"
  "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -5
  echo "  DONE: $tag"
}

run_model() {
  local mtag="$1" model="$2" calib="$3"
  for SEQ in 4096 8192 16384 32704; do
    run_one "longseq_fp16_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode fp16 \
        --seq_len "$SEQ" $TPOT_COMMON

    run_one "longseq_kivi_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode kivi_style \
        --quant_bits 4 --seq_len "$SEQ" $TPOT_COMMON

    run_one "longseq_torchref_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode int4_ours_asym \
        --calib_file "$calib" --decode_attn_impl torch_ref \
        --seq_len "$SEQ" $TPOT_COMMON

    run_one "longseq_triton_ra_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode int4_ours_asym \
        --calib_file "$calib" --decode_attn_impl triton_int4_asym \
        --seq_len "$SEQ" $TPOT_COMMON
  done
}

run_model "1p5b" "Qwen/Qwen2.5-1.5B-Instruct" "$CALIB_1P5B"
run_model "7b"   "Qwen/Qwen2.5-7B-Instruct"   "$CALIB_7B"
run_model "14b"  "Qwen/Qwen2.5-14B-Instruct"   "$CALIB_14B"
