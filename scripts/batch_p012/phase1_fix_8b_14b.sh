#!/bin/bash
# Stage 2: Phase 1 8B/14B 补跑 — 用本地 modelscope path
#
# 8B 和 14B 模型都已经在远端 modelscope cache 里：
#   8B:  /root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct/
#   14B: /root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct/
#
# 之前 phase1_fix 失败因为 unset HF_HUB_OFFLINE 试图重新下载，hf-mirror.com 代理挂了。
# 修复：直接用 local path + 强制 OFFLINE，绕过 HF cache 解析。

set -uo pipefail

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
mkdir -p "$RD"

MODEL_8B="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
MODEL_14B="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"
TPOT_COMMON="--seq_len 4096 --gen_len 128 --runs 8 --warmup 3 --seed 1234"

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag"
    return 0
  fi
  echo "  RUN: $tag"
  "$@" --save_csv --out_dir "$outdir" 2>&1 \
    | grep -E "^Run|tpot_ms|ttft_ms|ERROR|NaN|Traceback" || true
  if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "  DONE: $tag"
  else
    echo "  FAILED: $tag"
  fi
}

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo ""; echo "═══ Stage 2: Phase 1 8B/14B TPOT ═══"; echo "Started: $(timestamp)"

for MODEL_TAG in 8b 14b; do
  case "$MODEL_TAG" in
    8b)  MODEL="$MODEL_8B"; CALIB="$CALIB_8B" ;;
    14b) MODEL="$MODEL_14B"; CALIB="$CALIB_14B" ;;
  esac

  echo ""; echo "--- TPOT: $MODEL_TAG ---"

  run_or_skip "tpot_fp16_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode fp16 $TPOT_COMMON

  run_or_skip "tpot_triton_ra_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl triton_int4_asym $TPOT_COMMON

  run_or_skip "tpot_bd_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl bitdecoding $TPOT_COMMON

  run_or_skip "tpot_fi_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl flashinfer $TPOT_COMMON

  run_or_skip "tpot_torchref_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl torch_ref $TPOT_COMMON

  run_or_skip "tpot_kivi_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode kivi_style \
      --quant_bits 4 $TPOT_COMMON
done

# BD standalone (no --save_csv support, redirect stdout to file)
echo ""; echo "--- TPOT: BD standalone (1.5B) ---"
BD_OUT="$RD/tpot_bd_standalone_1p5b"
mkdir -p "$BD_OUT"
if [ ! -f "$BD_OUT/tpot_e2e_summary.json" ]; then
  echo "  RUN: tpot_bd_standalone_1p5b"
  python3 scripts/tpot_bitdecoding_e2e.py \
    --model_id "Qwen/Qwen2.5-1.5B-Instruct" \
    --seq_len 4096 --gen_len 128 --runs 8 --warmup 3 \
    --out_dir "$BD_OUT" 2>&1 | tee "$BD_OUT/run.log" || echo "  FAILED: BD standalone"
else
  echo "  SKIP: tpot_bd_standalone_1p5b"
fi

echo ""; echo "Done: $(timestamp)"
