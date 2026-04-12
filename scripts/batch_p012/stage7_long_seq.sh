#!/bin/bash
# Stage 7: 长序列 TPOT scaling 实验 — triton_ra 换战场
#
# 核心假设：triton_ra 在短序列（4K）上输给 torch_ref 2-3 ms，但架构上长序列必赢：
# 1. torch_ref 每 decode step 都要分配 fp16 KV buffer (O(S) dequant work)
# 2. triton_ra 直接读 int4 KV 做 fused attention (常数内存，无临时 buffer)
# 3. 内存带宽预算：int4 比 fp16 省 4×，加上无临时写入总体省 ~6×
#
# 期望：4K→32K 区间看到 triton_ra 与 torch_ref 的 crossover
#       32K 时 triton_ra 明显快，或 torch_ref 在大模型 OOM (triton_ra 独存)
#
# 矩阵: 3 models × 4 seq_lens × 4 backends = 48 tests
# 14B 32K 可能 OOM — 允许失败不 abort，作为 "triton_ra 独存" 的证据

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
mkdir -p "$RD"

# Models (14B 用 local modelscope path 避免 HF download)
MODEL_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"
MODEL_14B="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"

# Short runs to save time: gen_len=32, warmup=2, runs=5
# TPOT per-token 不受 gen_len 影响，减少总时间
TPOT_COMMON="--gen_len 32 --runs 5 --warmup 2 --seed 1234"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag"
    return 0
  fi
  echo ""; echo "═══ RUN: $tag ═══"
  timestamp
  # 允许单个测试失败（OOM）不阻塞后续
  "$@" --save_csv --out_dir "$outdir" 2>&1 \
    | grep -E "^Run|tpot_ms|ttft_ms|gpu_mem|peak|OOM|ERROR|NaN|CUDA out of memory|Traceback" \
    || echo "  (no matching output)"
  if [ -f "$outdir"/*.csv ] 2>/dev/null; then
    echo "  DONE: $tag"
  else
    echo "  FAILED: $tag (likely OOM)"
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

    # fp16 baseline (cuDNN SDPA)
    run_or_skip "longseq_fp16_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode fp16 \
        --seq_len "$SEQ" $TPOT_COMMON

    # kivi baseline (INT4, runtime absmax, no calib)
    run_or_skip "longseq_kivi_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode kivi_style \
        --quant_bits 4 --seq_len "$SEQ" $TPOT_COMMON

    # torch_ref (INT4-RA + PyTorch SDPA, 每 step 全量反量化)
    run_or_skip "longseq_torchref_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode int4_ours_asym \
        --calib_file "$calib" --decode_attn_impl torch_ref \
        --seq_len "$SEQ" $TPOT_COMMON

    # triton_ra (INT4-RA + Triton fused kernel)
    run_or_skip "longseq_triton_ra_${mtag}_s${SEQ}" \
      python3 scripts/profile_latency.py --model_id "$model" --kv_mode int4_ours_asym \
        --calib_file "$calib" --decode_attn_impl triton_int4_asym \
        --seq_len "$SEQ" $TPOT_COMMON
  done
}

echo "═══════════════════════════════════════════"
echo "Stage 7: Long-seq TPOT scaling"
echo "Started: $(timestamp)"
echo "═══════════════════════════════════════════"

# 1.5B (smallest, fastest)
run_model_matrix "1p5b" "$MODEL_1P5B" "$CALIB_1P5B" "4096 8192 16384 32768"

# 7B
run_model_matrix "7b" "$MODEL_7B" "$CALIB_7B" "4096 8192 16384 32768"

# 14B (largest — 32K 可能 OOM on fp16/torch_ref)
run_model_matrix "14b" "$MODEL_14B" "$CALIB_14B" "4096 8192 16384 32768"

echo ""; echo "═══════════════════════════════════════════"
echo "Stage 7 complete: $(timestamp)"
echo "Results in: $RD/longseq_*"
echo "═══════════════════════════════════════════"
