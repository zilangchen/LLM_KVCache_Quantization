#!/bin/bash
# Phase 1: INT4-RoleAlign v2 — close evidence gaps
# Wave 1: TPOT + KV Memory profiling (3 models)
# Wave 2: RULER + PPL full eval (3 models × 5 seeds for PPL, 3 seeds for RULER)
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

RESULTS_DIR="results/emnlp_rolealign_v2"
mkdir -p "$RESULTS_DIR/runs" "$RESULTS_DIR/tables" "$RESULTS_DIR/logs"

MODELS=(
  "Qwen/Qwen2.5-1.5B-Instruct|artifacts/kv_calib_rolealign_1p5b.json|1p5b"
  "Qwen/Qwen2.5-7B-Instruct|artifacts/kv_calib_rolealign_7b.json|7b"
  "meta-llama/Llama-3.1-8B-Instruct|artifacts/kv_calib_rolealign_8b.json|8b"
)

echo "=========================================="
echo "Phase 1: INT4-RoleAlign v2 Experiments"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ============================================================
# Wave 1: Profiling (#1 TPOT + #2 KV Memory)
# ============================================================
for entry in "${MODELS[@]}"; do
  IFS='|' read -r MODEL_ID CALIB TAG <<< "$entry"
  echo ""
  echo "=========== ${TAG} Profiling ==========="

  # #1: TPOT latency profiling
  for SEQ_LEN in 512 1024 2048 4096 8192; do
    echo ">>> ${TAG} TPOT profiling seq_len=${SEQ_LEN}"
    python3 scripts/profile_latency.py \
      --model_id "$MODEL_ID" \
      --kv_mode int4_ours_asym \
      --quant_bits 4 \
      --calib_file "$CALIB" \
      --seq_len "$SEQ_LEN" \
      --gen_len 128 \
      --batch 1 \
      --warmup 3 \
      --runs 8 \
      --save_csv \
      --out_dir "$RESULTS_DIR/runs/latency_ours_asym_${TAG}_s${SEQ_LEN}" \
      2>&1 | tee -a "$RESULTS_DIR/logs/latency_ours_asym_${TAG}.log"
  done

  # #2: KV memory profiling
  for SEQ_LEN in 512 1024 2048 4096 8192; do
    echo ">>> ${TAG} KV memory profiling seq_len=${SEQ_LEN}"
    python3 scripts/profile_memory.py \
      --model_id "$MODEL_ID" \
      --kv_mode int4_ours_asym \
      --quant_bits 4 \
      --calib_file "$CALIB" \
      --seq_len "$SEQ_LEN" \
      --gen_len 128 \
      --batch 1 \
      --save_csv \
      --out_dir "$RESULTS_DIR/runs/memory_ours_asym_${TAG}_s${SEQ_LEN}" \
      2>&1 | tee -a "$RESULTS_DIR/logs/memory_ours_asym_${TAG}.log"
  done
done

echo ""
echo "=========================================="
echo "Wave 1 (Profiling) Done: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ============================================================
# Wave 2: Evaluation (#3 RULER + #4 PPL)
# ============================================================
for entry in "${MODELS[@]}"; do
  IFS='|' read -r MODEL_ID CALIB TAG <<< "$entry"
  echo ""
  echo "=========== ${TAG} Evaluation ==========="

  # #3: RULER (3 seeds × context lengths)
  for SEED in 1234 1235 1236; do
    for CTX in 4096 8192 16384 32704; do
      echo ">>> ${TAG} RULER seed=${SEED} ctx=${CTX}"
      python3 scripts/eval_ruler.py \
        --model_id "$MODEL_ID" \
        --kv_mode int4_ours_asym \
        --quant_bits 4 \
        --calib_file "$CALIB" \
        --context_len "$CTX" \
        --seed "$SEED" \
        --save_csv \
        --out_dir "$RESULTS_DIR/runs/ruler_ours_asym_${TAG}_ctx${CTX}_s${SEED}" \
        2>&1 | tee -a "$RESULTS_DIR/logs/ruler_ours_asym_${TAG}.log"
    done
  done

  # #4: PPL full eval (5 seeds, no max_samples = full wikitext ~1M tokens)
  for SEED in 1234 1235 1236 1237 1238; do
    echo ">>> ${TAG} PPL full eval seed=${SEED}"
    python3 scripts/eval_ppl.py \
      --model_id "$MODEL_ID" \
      --kv_mode int4_ours_asym \
      --quant_bits 4 \
      --calib_file "$CALIB" \
      --seed "$SEED" \
      --save_csv \
      --out_dir "$RESULTS_DIR/runs/ppl_ours_asym_${TAG}_s${SEED}" \
      2>&1 | tee -a "$RESULTS_DIR/logs/ppl_ours_asym_${TAG}.log"
  done

  # Also run FP16 baseline PPL (1 seed, for P1 cross-table validation)
  echo ">>> ${TAG} FP16 PPL baseline seed=1234"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL_ID" \
    --kv_mode fp16 \
    --seed 1234 \
    --save_csv \
    --out_dir "$RESULTS_DIR/runs/ppl_fp16_${TAG}_s1234" \
    2>&1 | tee -a "$RESULTS_DIR/logs/ppl_fp16_${TAG}.log"
done

echo ""
echo "=========================================="
echo "Phase 1 ALL DONE: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
