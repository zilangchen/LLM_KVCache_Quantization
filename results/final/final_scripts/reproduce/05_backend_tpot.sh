#!/bin/bash
# ================================================================
# Step 5: 后端 TPOT 对比 (Phase 1)
# ================================================================
# 输出: backend_comparison/runs/tpot_{fp16,kivi,torchref,triton_ra,fi}_{1p5b,7b,8b,14b}
# 原始: scripts/batch_p012/stage1_phase1_rerun.sh + phase1_fix_8b_14b.sh
# GPU: ~3-4h (需独占)
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

RD="results/final/final_data/backend_comparison/runs"
TPOT_COMMON="--seq_len 4096 --gen_len 128 --runs 8 --warmup 3 --seed 1234"

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"

run_one() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag"; return 0
  fi
  echo "═══ RUN: $tag ═══"
  python3 scripts/profile_latency.py "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -5
  echo "  DONE: $tag"
}

for MTAG_MODEL_CALIB in \
    "1p5b:Qwen/Qwen2.5-1.5B-Instruct:$CALIB_1P5B" \
    "7b:Qwen/Qwen2.5-7B-Instruct:$CALIB_7B" \
    "8b:meta-llama/Llama-3.1-8B-Instruct:$CALIB_8B" \
    "14b:Qwen/Qwen2.5-14B-Instruct:$CALIB_14B"; do

  MTAG="${MTAG_MODEL_CALIB%%:*}"
  REST="${MTAG_MODEL_CALIB#*:}"
  MODEL="${REST%%:*}"
  CALIB="${REST#*:}"

  # fp16 (kv_mode=fp16, 无需 calib)
  run_one "tpot_fp16_${MTAG}" \
    --model_id "$MODEL" --kv_mode fp16 $TPOT_COMMON

  # kivi (kv_mode=kivi_style)
  run_one "tpot_kivi_${MTAG}" \
    --model_id "$MODEL" --kv_mode kivi_style --quant_bits 4 $TPOT_COMMON

  # torchref (INT4-RA, PyTorch SDPA)
  run_one "tpot_torchref_${MTAG}" \
    --model_id "$MODEL" --kv_mode int4_ours_asym \
    --calib_file "$CALIB" --decode_attn_impl torch_ref $TPOT_COMMON

  # triton_ra (INT4-RA, Triton kernel)
  run_one "tpot_triton_ra_${MTAG}" \
    --model_id "$MODEL" --kv_mode int4_ours_asym \
    --calib_file "$CALIB" --decode_attn_impl triton_int4_asym $TPOT_COMMON

  # flashinfer
  run_one "tpot_fi_${MTAG}" \
    --model_id "$MODEL" --kv_mode int4_ours_asym \
    --calib_file "$CALIB" --decode_attn_impl flashinfer $TPOT_COMMON
done
