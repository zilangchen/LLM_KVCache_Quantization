#!/bin/bash
# ================================================================
# Step 8: 8B 长序列 TPOT — Hkv=8 控制对比
# ================================================================
# 输出: backend_comparison/runs/longseq_{fp16,kivi,torchref,triton_ra}_8b_s{4096..32704}
# 原始: scripts/batch_p012/stage_8b_longseq.sh
# GPU: ~2h (需独占)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

RD="results/final/final_data/backend_comparison/runs"
MODEL="meta-llama/Llama-3.1-8B-Instruct"
CALIB="artifacts/kv_calib_rolealign_8b_v3.json"
TPOT_COMMON="--gen_len 64 --runs 10 --warmup 5 --seed 1234"

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

for SEQ in 4096 8192 16384 32704; do
  run_one "longseq_fp16_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode fp16 \
      --seq_len "$SEQ" $TPOT_COMMON

  run_one "longseq_kivi_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode kivi_style \
      --quant_bits 4 --seq_len "$SEQ" $TPOT_COMMON

  run_one "longseq_torchref_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl torch_ref \
      --seq_len "$SEQ" $TPOT_COMMON

  run_one "longseq_triton_ra_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl triton_int4_asym \
      --seq_len "$SEQ" $TPOT_COMMON
done
