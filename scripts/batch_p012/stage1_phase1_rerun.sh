#!/bin/bash
# Stage 1: Phase 1 RA 衍生 backend 1.5B/7B 重测（v_percentile fix 后）
#
# 需要 GPU 完全独占。前置条件：Stage 0 sanity check 通过。
# 重测 8 个 TPOT：triton_ra / bd / fi / torchref × 1.5B / 7B
#
# Archive 旧污染数据到 _archive_pre_fix_20260411，避免 run_or_skip 跳过。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
ARCHIVE="$RD/_archive_pre_fix_20260411"
TPOT_COMMON="--seq_len 4096 --gen_len 128 --runs 8 --warmup 3 --seed 1234"

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"

MODEL_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"

# --- Step 1: Archive 旧污染数据 ---
echo "═══ Stage 1: Archive polluted Phase 1 data ═══"
mkdir -p "$ARCHIVE"
for backend in triton_ra bd fi torchref; do
  for model in 1p5b 7b; do
    src="$RD/tpot_${backend}_${model}"
    if [ -d "$src" ]; then
      mv "$src" "$ARCHIVE/tpot_${backend}_${model}_$(date +%H%M%S)" \
        && echo "  archived: tpot_${backend}_${model}"
    fi
  done
done

# --- Step 2: 跑 8 个 TPOT ---
run_one() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  echo ""; echo "═══ RUN: $tag ═══"
  date '+%Y-%m-%d %H:%M:%S'
  python3 scripts/profile_latency.py "$@" --save_csv --out_dir "$outdir" 2>&1 \
    | grep -E "^Run|tpot_ms|ttft_ms|ERROR|NaN|Traceback"
  if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "  DONE: $tag"
  else
    echo "  FAILED: $tag"
  fi
}

# 1.5B (4 backends)
run_one tpot_triton_ra_1p5b \
  --model_id "$MODEL_1P5B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_1P5B" --decode_attn_impl triton_int4_asym $TPOT_COMMON

run_one tpot_bd_1p5b \
  --model_id "$MODEL_1P5B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_1P5B" --decode_attn_impl bitdecoding $TPOT_COMMON

run_one tpot_fi_1p5b \
  --model_id "$MODEL_1P5B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_1P5B" --decode_attn_impl flashinfer $TPOT_COMMON

run_one tpot_torchref_1p5b \
  --model_id "$MODEL_1P5B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_1P5B" --decode_attn_impl torch_ref $TPOT_COMMON

# 7B (4 backends)
run_one tpot_triton_ra_7b \
  --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_7B" --decode_attn_impl triton_int4_asym $TPOT_COMMON

run_one tpot_bd_7b \
  --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_7B" --decode_attn_impl bitdecoding $TPOT_COMMON

run_one tpot_fi_7b \
  --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_7B" --decode_attn_impl flashinfer $TPOT_COMMON

run_one tpot_torchref_7b \
  --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
  --calib_file "$CALIB_7B" --decode_attn_impl torch_ref $TPOT_COMMON

echo ""; echo "═══ Stage 1 complete ═══"
date '+%Y-%m-%d %H:%M:%S'
