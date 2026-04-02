#!/bin/bash
# Phase 1 Stream A: Qwen2.5-1.5B — all experiments
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_ID="Qwen/Qwen2.5-1.5B-Instruct"
CALIB="artifacts/kv_calib_rolealign_1p5b.json"
TAG="1p5b"
RD="results/emnlp_rolealign_v2"
mkdir -p "$RD/runs" "$RD/tables" "$RD/logs"

echo "[${TAG}] Start: $(date '+%Y-%m-%d %H:%M:%S')"

# --- Profiling ---
for SL in 512 1024 2048 4096 8192; do
  echo ">>> ${TAG} TPOT seq=${SL}"
  python3 scripts/profile_latency.py \
    --model_id "$MODEL_ID" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" --seq_len "$SL" --gen_len 128 \
    --batch 1 --warmup 3 --runs 8 --save_csv \
    --out_dir "$RD/runs/latency_ours_asym_${TAG}_s${SL}" \
    2>&1 | tee -a "$RD/logs/latency_${TAG}.log"

  echo ">>> ${TAG} Memory seq=${SL}"
  python3 scripts/profile_memory.py \
    --model_id "$MODEL_ID" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" --seq_len "$SL" --gen_len 128 \
    --batch 1 --save_csv \
    --out_dir "$RD/runs/memory_ours_asym_${TAG}_s${SL}" \
    2>&1 | tee -a "$RD/logs/memory_${TAG}.log"
done

# --- RULER ---
for SEED in 1234 1235 1236; do
  for CTX in 4096 8192 16384 32704; do
    echo ">>> ${TAG} RULER seed=${SEED} ctx=${CTX}"
    python3 scripts/eval_ruler.py \
      --model_id "$MODEL_ID" --kv_mode int4_ours_asym --quant_bits 4 \
      --calib_file "$CALIB" --ruler_context_len "$CTX" --seed "$SEED" \
      --save_csv --out_dir "$RD/runs/ruler_ours_asym_${TAG}_ctx${CTX}_s${SEED}" \
      2>&1 | tee -a "$RD/logs/ruler_${TAG}.log"
  done
done

# --- PPL (5 seeds, full wikitext) ---
for SEED in 1234 1235 1236 1237 1238; do
  echo ">>> ${TAG} PPL seed=${SEED}"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL_ID" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" --seed "$SEED" --save_csv \
    --out_dir "$RD/runs/ppl_ours_asym_${TAG}_s${SEED}" \
    2>&1 | tee -a "$RD/logs/ppl_${TAG}.log"
done

# --- FP16 baseline PPL ---
echo ">>> ${TAG} FP16 PPL baseline"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_ID" --kv_mode fp16 --seed 1234 --save_csv \
  --out_dir "$RD/runs/ppl_fp16_${TAG}_s1234" \
  2>&1 | tee -a "$RD/logs/ppl_fp16_${TAG}.log"

echo "[${TAG}] ALL DONE: $(date '+%Y-%m-%d %H:%M:%S')"
