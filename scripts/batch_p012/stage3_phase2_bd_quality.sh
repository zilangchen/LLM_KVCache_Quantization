#!/bin/bash
# Stage 3: Phase 2 BD adapter 1.5B 质量评测重跑
#
# 前置条件：BD adapter Layout A 已修复（commit b6ee998 + remote scp）。
# Stage 0 sanity check 已验证 BD with calib cosine > 0.95，TPOT ~45ms。
#
# 旧 Phase 2 数据全部废弃（rsync 中途替换 adapter 导致旧/新混合污染）。
# 本脚本先 archive 旧数据，然后跑完整 39 个测试。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
ARCHIVE="$RD/_archive_phase2_polluted_20260411"
mkdir -p "$ARCHIVE"

MODEL_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
BD_COMMON="--model_id $MODEL_1P5B --kv_mode int4_ours_asym --calib_file $CALIB_1P5B --decode_attn_impl bitdecoding"

# --- Step 1: Archive 污染的 Phase 2 数据 ---
echo "═══ Stage 3: Archive Phase 2 polluted data ═══"
for prefix in ppl needle ruler longbench; do
  for d in "$RD/${prefix}_bd_1p5b_"*; do
    if [ -d "$d" ]; then
      mv "$d" "$ARCHIVE/" 2>/dev/null && echo "  archived: $(basename $d)"
    fi
  done
done

# --- Step 2: 重跑 Phase 2 ---
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

echo ""; echo "═══ Phase 2 BD adapter 1.5B quality ═══"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

# PPL (10 seeds)
echo ""; echo "--- PPL: 10 seeds ---"
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_bd_1p5b_s${SEED}" \
    python3 scripts/eval_ppl.py $BD_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Needle (3 seeds × 4 context_lens)
echo ""; echo "--- Needle: 3 seeds × 4 context_lens ---"
for CL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "needle_bd_1p5b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py $BD_COMMON --context_len "$CL" --num_depths 10 --seed "$SEED"
  done
done

# RULER (3 seeds × 4 seq_lens)
echo ""; echo "--- RULER: 3 seeds × 4 seq_lens ---"
for SL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_bd_1p5b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py $BD_COMMON --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# LongBench synthetic (5 seeds)
echo ""; echo "--- LongBench synthetic: 5 seeds ---"
for SEED in 1234 1235 1236 1237 1238; do
  run_or_skip "longbench_bd_1p5b_s${SEED}" \
    python3 scripts/eval_longbench.py $BD_COMMON --seq_len 32704 --seed "$SEED"
done

echo ""; echo "═══ Stage 3 complete ═══"
date '+%Y-%m-%d %H:%M:%S'
