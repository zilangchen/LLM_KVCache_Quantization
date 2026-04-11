#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# P0+P1+P2 全量实验批次 — 单卡串行
# ═══════════════════════════════════════════════════════════════
# 用法: bash scripts/batch_p012/run_all.sh [PHASE]
#   PHASE=1  只跑 TPOT
#   PHASE=2  只跑 BD adapter 质量
#   PHASE=3  只跑 FlashInfer 质量
#   PHASE=4  只跑 14B 补跑
#   PHASE=5  只跑 7B/8B 杂项
#   不传参   跑全部
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

PHASE="${1:-all}"
RD="results/emnlp_p012_batch/runs"
mkdir -p "$RD"

# ─── Model configs ───
MODEL_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"
MODEL_8B="meta-llama/Llama-3.1-8B-Instruct"
MODEL_14B="Qwen/Qwen2.5-14B-Instruct"

CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"
CALIB_14B="artifacts/kv_calib_rolealign_14b_v3.json"

# ─── Helper ───
run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag (results exist)"
    return 0
  fi
  echo "  RUN: $tag"
  "$@" --save_csv --out_dir "$outdir" || echo "  FAILED: $tag"
}

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

# ═══════════════════════════════════════════════════════════════
# Phase 1: TPOT 统一重测（~2h, 独占 GPU）
# ═══════════════════════════════════════════════════════════════
if [ "$PHASE" = "all" ] || [ "$PHASE" = "1" ]; then
echo ""; echo "═══ Phase 1: TPOT 4 models × 7 backends ═══"; echo "Started: $(timestamp)"

TPOT_COMMON="--seq_len 4096 --gen_len 128 --runs 8 --warmup 3 --seed 1234"

for MODEL_TAG in 1p5b 7b 8b 14b; do
  case "$MODEL_TAG" in
    1p5b) MODEL="$MODEL_1P5B"; CALIB="$CALIB_1P5B" ;;
    7b)   MODEL="$MODEL_7B";   CALIB="$CALIB_7B" ;;
    8b)   MODEL="$MODEL_8B";   CALIB="$CALIB_8B" ;;
    14b)  MODEL="$MODEL_14B";  CALIB="$CALIB_14B" ;;
  esac

  echo ""; echo "--- TPOT: $MODEL_TAG ---"

  # FP16
  run_or_skip "tpot_fp16_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode fp16 $TPOT_COMMON

  # INT4-RA Triton (current main = cache-opt)
  run_or_skip "tpot_triton_ra_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl triton_int4_asym $TPOT_COMMON

  # INT4-RA BitDecoding adapter
  run_or_skip "tpot_bd_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl bitdecoding $TPOT_COMMON

  # INT4-RA FlashInfer
  run_or_skip "tpot_fi_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl flashinfer $TPOT_COMMON

  # INT4-RA torch_ref
  run_or_skip "tpot_torchref_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode int4_ours_asym \
      --calib_file "$CALIB" --decode_attn_impl torch_ref $TPOT_COMMON

  # KIVI baseline INT4
  run_or_skip "tpot_kivi_${MODEL_TAG}" \
    python3 scripts/profile_latency.py --model_id "$MODEL" --kv_mode kivi_style \
      --quant_bits 4 $TPOT_COMMON
done

# BD standalone (1.5B only)
echo ""; echo "--- TPOT: BD standalone (1.5B) ---"
run_or_skip "tpot_bd_standalone_1p5b" \
  python3 scripts/tpot_bitdecoding_e2e.py --model_id "$MODEL_1P5B" \
    --seq_len 4096 --gen_len 128 --runs 8 --warmup 3

echo "Phase 1 done: $(timestamp)"
fi

# ═══════════════════════════════════════════════════════════════
# Phase 2: BD adapter 质量全套 — 1.5B（~5.5h）
# ═══════════════════════════════════════════════════════════════
if [ "$PHASE" = "all" ] || [ "$PHASE" = "2" ]; then
echo ""; echo "═══ Phase 2: BD adapter quality (1.5B) ═══"; echo "Started: $(timestamp)"

BD_COMMON="--model_id $MODEL_1P5B --kv_mode int4_ours_asym --calib_file $CALIB_1P5B --decode_attn_impl bitdecoding"

# PPL (10 seeds)
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_bd_1p5b_s${SEED}" \
    python3 scripts/eval_ppl.py $BD_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Needle (3 seeds × 4 context_lens)
for CL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "needle_bd_1p5b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py $BD_COMMON --context_len "$CL" --num_depths 10 --seed "$SEED"
  done
done

# RULER (3 seeds × 4 seq_lens)
for SL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_bd_1p5b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py $BD_COMMON --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# LongBench synthetic (5 seeds)
for SEED in 1234 1235 1236 1237 1238; do
  run_or_skip "longbench_bd_1p5b_s${SEED}" \
    python3 scripts/eval_longbench.py $BD_COMMON --seq_len 32704 --seed "$SEED"
done

echo "Phase 2 done: $(timestamp)"
fi

# ═══════════════════════════════════════════════════════════════
# Phase 3: FlashInfer 质量全套 — 1.5B（~5.5h）
# ═══════════════════════════════════════════════════════════════
if [ "$PHASE" = "all" ] || [ "$PHASE" = "3" ]; then
echo ""; echo "═══ Phase 3: FlashInfer quality (1.5B) ═══"; echo "Started: $(timestamp)"

FI_COMMON="--model_id $MODEL_1P5B --kv_mode int4_ours_asym --calib_file $CALIB_1P5B --decode_attn_impl flashinfer"

# PPL (10 seeds)
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_fi_1p5b_s${SEED}" \
    python3 scripts/eval_ppl.py $FI_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Needle (3 seeds × 4 context_lens)
for CL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "needle_fi_1p5b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py $FI_COMMON --context_len "$CL" --num_depths 10 --seed "$SEED"
  done
done

# RULER (3 seeds × 4 seq_lens)
for SL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_fi_1p5b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py $FI_COMMON --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# LongBench synthetic (5 seeds)
for SEED in 1234 1235 1236 1237 1238; do
  run_or_skip "longbench_fi_1p5b_s${SEED}" \
    python3 scripts/eval_longbench.py $FI_COMMON --seq_len 32704 --seed "$SEED"
done

echo "Phase 3 done: $(timestamp)"
fi

# ═══════════════════════════════════════════════════════════════
# Phase 4: 14B 全量补跑（~16h）
# ═══════════════════════════════════════════════════════════════
if [ "$PHASE" = "all" ] || [ "$PHASE" = "4" ]; then
echo ""; echo "═══ Phase 4: 14B full suite ═══"; echo "Started: $(timestamp)"

RA14_COMMON="--model_id $MODEL_14B --kv_mode int4_ours_asym --calib_file $CALIB_14B"

# PPL (10 seeds)
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_ra_14b_s${SEED}" \
    python3 scripts/eval_ppl.py $RA14_COMMON --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Also FP16 PPL for baseline
for SEED in 1234 1235 1236 1237 1238 1239 1240 1241 1242 1243; do
  run_or_skip "ppl_fp16_14b_s${SEED}" \
    python3 scripts/eval_ppl.py --model_id "$MODEL_14B" --kv_mode fp16 --max_samples 32 --chunk_size 128 --seed "$SEED"
done

# Needle (3 seeds × 4 context_lens)
for CL in 4096 8192 16384 32704; do
  for SEED in 1234 1235 1236; do
    run_or_skip "needle_ra_14b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py $RA14_COMMON --context_len "$CL" --num_depths 10 --seed "$SEED"
    # FP16 baseline
    run_or_skip "needle_fp16_14b_c${CL}_s${SEED}" \
      python3 scripts/eval_needle.py --model_id "$MODEL_14B" --kv_mode fp16 --context_len "$CL" --num_depths 10 --seed "$SEED"
  done
done

# RULER (3 seeds × 3 seq_lens — 14B max context 32K, skip 32704)
for SL in 4096 8192 16384; do
  for SEED in 1234 1235 1236; do
    run_or_skip "ruler_ra_14b_sl${SL}_s${SEED}" \
      python3 scripts/eval_ruler.py $RA14_COMMON --seq_len "$SL" --ruler_context_len "$SL" --seed "$SEED"
  done
done

# LongBench synthetic (5 seeds)
for SEED in 1234 1235 1236 1237 1238; do
  run_or_skip "longbench_ra_14b_s${SEED}" \
    python3 scripts/eval_longbench.py $RA14_COMMON --seq_len 32704 --seed "$SEED"
done

# K/V ablation PPL — 4 configs × 3 seeds
# K4V16 = K@INT4, V@FP16 (K isolated)
# K16V4 = K@FP16, V@INT4 (V isolated)
# K8V4  = K@INT8, V@INT4 (mixed, published)
# K4V8  = K@INT4, V@INT8 (mixed, opposite)
echo ""; echo "--- 14B K/V ablation ---"
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

echo "Phase 4 done: $(timestamp)"
fi

# ═══════════════════════════════════════════════════════════════
# Phase 5: 7B/8B 小缺口（~5h）
# ═══════════════════════════════════════════════════════════════
if [ "$PHASE" = "all" ] || [ "$PHASE" = "5" ]; then
echo ""; echo "═══ Phase 5: 7B/8B misc ═══"; echo "Started: $(timestamp)"

# 7B LongBench official (source=hf)
run_or_skip "longbench_official_7b_s1234" \
  python3 scripts/eval_longbench.py --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
    --calib_file "$CALIB_7B" --seq_len 32704 --seed 1234 \
    --longbench_source hf --longbench_max_samples 32

# 8B LongBench official (source=hf)
run_or_skip "longbench_official_8b_s1234" \
  python3 scripts/eval_longbench.py --model_id "$MODEL_8B" --kv_mode int4_ours_asym \
    --calib_file "$CALIB_8B" --seq_len 32704 --seed 1234 \
    --longbench_source hf --longbench_max_samples 32

# 7B Memory/Batch sweep
for BATCH in 1 4 8 16; do
  run_or_skip "memory_7b_b${BATCH}" \
    python3 scripts/profile_memory.py --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
      --calib_file "$CALIB_7B" --batch "$BATCH" --seq_len 4096
done

# 8B Memory/Batch sweep
for BATCH in 1 4 8 16; do
  run_or_skip "memory_8b_b${BATCH}" \
    python3 scripts/profile_memory.py --model_id "$MODEL_8B" --kv_mode int4_ours_asym \
      --calib_file "$CALIB_8B" --batch "$BATCH" --seq_len 4096
done

echo "Phase 5 done: $(timestamp)"
fi

echo ""; echo "═══ ALL PHASES COMPLETE ═══"; echo "Finished: $(timestamp)"
echo "Results in: $RD"
echo "Total directories: $(ls -d $RD/*/ 2>/dev/null | wc -l)"
