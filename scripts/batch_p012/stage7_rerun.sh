#!/bin/bash
# Stage 7 REWORK: 长序列 TPOT scaling — 修复 warmup 不足 + 32K OOM
#
# 原 Stage 7 (gen=32, runs=5, warmup=2, seq=32768) 问题:
#   1. warmup=2 不足: Triton JIT + autotune 冷启动未吸收, std 高 20-30x
#   2. seq_len=32768 超过 Qwen2.5 max_position_embeddings (32768)
#      error: Total length 32768 + 8 = 32776 exceeds max
#
# 修复:
#   - warmup=5, runs=10 (更稳定)
#   - gen=64 (更长 decode 覆盖 warmup 残余)
#   - seq_len=32704 代替 32768 (保留 64-token safety margin)
#
# 归档原 longseq_* 数据到 archive/,重跑到同名目录让 analyze 脚本直接消费。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
ARCHIVE="$RD/_archive_stage7_v1_20260412"

# Models (14B 用 local modelscope path)
MODEL_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"
MODEL_14B="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"

# Stage 7 v2 params: 更稳定的 TPOT 测量
TPOT_COMMON="--gen_len 64 --runs 10 --warmup 5 --seed 1234"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

# --- Step 1: 归档原 longseq_* 数据 ---
echo "═══ Stage 7 Rerun: archive old longseq_* data ═══"
mkdir -p "$ARCHIVE"
for d in "$RD"/longseq_*; do
  if [ -d "$d" ]; then
    name=$(basename "$d")
    mv "$d" "$ARCHIVE/$name" 2>/dev/null && echo "  archived: $name"
  fi
done

# --- Step 2: Run (seq_len 32704 替代 32768) ---
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
    | grep -E "^Run|tpot_ms|ttft_ms|gpu_mem|OOM|ERROR|CUDA out of memory|Traceback|exceeds" \
    || echo "  (no matching output)"
  if ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  DONE: $tag"
  else
    echo "  FAILED: $tag"
  fi
}

run_model_matrix() {
  local mtag="$1"
  local model="$2"
  local calib="$3"
  local seqs="$4"  # 空格分隔

  echo ""; echo "▄▄▄▄▄▄ MODEL: $mtag ($model) ▄▄▄▄▄▄"
  timestamp

  for SEQ in $seqs; do
    echo ""; echo "─── $mtag × seq=$SEQ ───"

    # fp16
    run_one "longseq_fp16_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode fp16 \
        --seq_len "$SEQ" $TPOT_COMMON

    # kivi (INT4 baseline)
    run_one "longseq_kivi_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode kivi_style \
        --quant_bits 4 --seq_len "$SEQ" $TPOT_COMMON

    # torch_ref (INT4-RA, PyTorch SDPA)
    run_one "longseq_torchref_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode int4_ours_asym \
        --calib_file "$calib" --decode_attn_impl torch_ref \
        --seq_len "$SEQ" $TPOT_COMMON

    # triton_ra (INT4-RA, Triton kernel)
    run_one "longseq_triton_ra_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode int4_ours_asym \
        --calib_file "$calib" --decode_attn_impl triton_int4_asym \
        --seq_len "$SEQ" $TPOT_COMMON
  done
}

echo ""; echo "═══════════════════════════════════════════"
echo "Stage 7 Rerun: Long-seq TPOT scaling (v2)"
echo "Params: gen=64, runs=10, warmup=5, seed=1234"
echo "Seq lens: 4096 8192 16384 32704 (32768 skipped: max_position_embeddings)"
echo "Started: $(timestamp)"
echo "═══════════════════════════════════════════"

# 1.5B / 7B / 14B × 4 seq × 4 backend = 48 tests
# 32704 = 32768 - 64 safety margin, 和 Phase 2/3 一致
run_model_matrix "1p5b" "$MODEL_1P5B" "$CALIB_1P5B" "4096 8192 16384 32704"
run_model_matrix "7b" "$MODEL_7B" "$CALIB_7B" "4096 8192 16384 32704"
run_model_matrix "14b" "$MODEL_14B" "$CALIB_14B" "4096 8192 16384 32704"

echo ""; echo "═══════════════════════════════════════════"
echo "Stage 7 Rerun complete: $(timestamp)"
echo "═══════════════════════════════════════════"
