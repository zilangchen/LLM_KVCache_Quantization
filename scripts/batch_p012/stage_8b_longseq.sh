#!/bin/bash
# 8B 长序列 TPOT — 验证 Hkv vs 模型规模的因果分离
#
# 目的: 8B Llama (Hkv=8) 与 14B Qwen (Hkv=8) 在同 Hkv 下的 crossover 是否一致？
# 如果一致 → Hkv 主导；如果不一致 → 模型规模也有贡献。
#
# Phase 1 短序列 (4K) 已暗示一致: 8B Δ=-0.39, 14B Δ=-0.40
# 本实验验证长序列 (8K/16K/32K) 是否也一致。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
MODEL_8B="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"

TPOT_COMMON="--gen_len 64 --runs 10 --warmup 5 --seed 1234"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

run_one() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag"
    return 0
  fi
  echo ""; echo "═══ RUN: $tag ═══"
  timestamp
  "$@" --save_csv --out_dir "$outdir" 2>&1 \
    | grep -E "^Run|tpot_ms|ttft_ms|ERROR|OOM|Traceback" || true
  if ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  DONE: $tag"
  else
    echo "  FAILED: $tag"
  fi
}

echo "═══════════════════════════════════════════"
echo "8B Long-seq TPOT (Hkv=8 控制组)"
echo "Purpose: Hkv vs model-size causal separation"
echo "Started: $(timestamp)"
echo "═══════════════════════════════════════════"

for SEQ in 4096 8192 16384 32704; do
  echo ""; echo "─── 8b × seq=$SEQ ───"

  run_one "longseq_fp16_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL_8B" --kv_mode fp16 \
      --seq_len "$SEQ" $TPOT_COMMON

  run_one "longseq_kivi_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL_8B" --kv_mode kivi_style \
      --quant_bits 4 --seq_len "$SEQ" $TPOT_COMMON

  run_one "longseq_torchref_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL_8B" --kv_mode int4_ours_asym \
      --calib_file "$CALIB_8B" --decode_attn_impl torch_ref \
      --seq_len "$SEQ" $TPOT_COMMON

  run_one "longseq_triton_ra_8b_s${SEQ}" \
    python3 scripts/profile_latency.py --model_id "$MODEL_8B" --kv_mode int4_ours_asym \
      --calib_file "$CALIB_8B" --decode_attn_impl triton_int4_asym \
      --seq_len "$SEQ" $TPOT_COMMON
done

echo ""; echo "═══════════════════════════════════════════"
echo "8B Long-seq complete: $(timestamp)"
echo "═══════════════════════════════════════════"
