#!/bin/bash
# Stage 5: Phase 4 14B 全套质量评测
#
# 14B 是论文当前最大缺口。Stage 2 已验证 14B local model path 可以 load。
#
# 模型路径用 local modelscope path 避免 HF download attempt。
# RULER 和 32K Needle 因 14B 显存约束需要小心。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
MODEL_14B="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"
RA14_COMMON="--model_id $MODEL_14B --kv_mode int4_ours_asym --calib_file $CALIB_14B"

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag (results exist)"
    return 0
  fi
  echo ""; echo "═══ RUN: $tag ═══"
  date '+%Y-%m-%d %H:%M:%S'
  "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -20
  echo "  DONE: $tag"
}

echo ""; echo "═══ Stage 5: Phase 4 14B full suite ═══"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

# PPL: RA + FP16, 10 seeds each
echo ""; echo "--- PPL: 10 seeds × 2 (RA + FP16) ---"
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_ra_14b_s${SEED}" \
    python3 scripts/eval_ppl.py $RA14_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_fp16_14b_s${SEED}" \
    python3 scripts/eval_ppl.py --model_id "$MODEL_14B" --kv_mode fp16 \
      --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Needle: 3 seeds × 4 context_lens × 2 (RA + FP16)
echo ""; echo "--- Needle: 3 seeds × 4 context_lens × 2 ---"
for CL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "needle_ra_14b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py $RA14_COMMON --context_len "$CL" --num_depths 10 --seed "$SEED"
    run_or_skip "needle_fp16_14b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py --model_id "$MODEL_14B" --kv_mode fp16 \
        --context_len "$CL" --num_depths 10 --seed "$SEED"
  done
done

# RULER: 3 seeds × 3 seq_lens (skip 32704 — 14B 显存约束)
echo ""; echo "--- RULER: 3 seeds × 3 seq_lens (skip 32K) ---"
for SL in 4096 8192 16384; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_ra_14b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py $RA14_COMMON --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# LongBench synthetic (5 seeds)
echo ""; echo "--- LongBench synthetic: 5 seeds ---"
for SEED in 1234 1235 1236 1237 1238; do
  run_or_skip "longbench_ra_14b_s${SEED}" \
    python3 scripts/eval_longbench.py $RA14_COMMON --seq_len 32704 --seed "$SEED"
done

# K/V ablation PPL (4 cfg × 3 seeds)
echo ""; echo "--- K/V ablation: 4 configs × 3 seeds ---"
for CFG in "K4V16:4:16" "K16V4:16:4" "K8V4:8:4" "K4V8:4:8"; do
  TAG="${CFG%%:*}"
  REST="${CFG#*:}"
  KB="${REST%%:*}"
  VB="${REST#*:}"
  for SEED in 1234 1235 1236; do
    run_or_skip "ppl_ablation_${TAG}_14b_s${SEED}" \
      python3 scripts/eval_ppl.py --model_id "$MODEL_14B" --kv_mode int4_mixed_kv \
        --k_bits "$KB" --v_bits "$VB" \
        --max_samples 32 --chunk_size 128 --seed "$SEED"
  done
done

echo ""; echo "═══ Stage 5 complete ═══"
date '+%Y-%m-%d %H:%M:%S'
