#!/bin/bash
# GPU-1 chain: Exp-8 → Exp-7 → Exp-10 (after T3 7B completes)
set -euo pipefail
GPU_ID="${1:-1}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

MODEL_1P5B="Qwen/Qwen2.5-1.5B-Instruct"
CALIB_RA="artifacts/kv_calib_rolealign_1p5b_v3.json"
CALIB_INT8="artifacts/kv_calib_kl_selected_v3_quick.json"
DEF_RD="results/emnlp_defense_v1"
mkdir -p "$DEF_RD/runs" "$DEF_RD/logs"

echo "=== GPU-1 Chain Start: $(date) ==="

# --- Exp-8: KV noise diagnostic G2 (~15min) + G5 (~15min) ---
echo ">>> Exp-8a: G2 cross-head correlation"
bash scripts/diagnose_kv_noise.sh "$GPU_ID" 2>&1 | tee "$DEF_RD/logs/exp8_g2.log"
echo ">>> Exp-8a done: $(date)"

echo ">>> Exp-8b: G5 Key vs Value noise"
bash scripts/diagnose_kv_noise_g5.sh "$GPU_ID" 2>&1 | tee "$DEF_RD/logs/exp8_g5.log"
echo ">>> Exp-8b done: $(date)"

# --- Exp-7: Official LongBench (~2h) ---
echo ">>> Exp-7: Official LongBench (FP16 + INT8-ours)"

echo ">>> FP16 LongBench"
python3 scripts/eval_longbench.py \
  --model_id "$MODEL_1P5B" \
  --kv_mode fp16 --seed 1234 \
  --longbench_source hf \
  --longbench_tasks narrativeqa,hotpotqa,gov_report \
  --longbench_max_samples 50 \
  --save_csv --out_dir "$DEF_RD/runs/longbench_official_fp16_1p5b" \
  2>&1 | tee -a "$DEF_RD/logs/exp7_longbench.log"

echo ">>> INT8-ours LongBench"
python3 scripts/eval_longbench.py \
  --model_id "$MODEL_1P5B" \
  --kv_mode int8_ours \
  --calib_file "$CALIB_INT8" \
  --seed 1234 \
  --longbench_source hf \
  --longbench_tasks narrativeqa,hotpotqa,gov_report \
  --longbench_max_samples 50 \
  --save_csv --out_dir "$DEF_RD/runs/longbench_official_int8_1p5b" \
  2>&1 | tee -a "$DEF_RD/logs/exp7_longbench.log"

echo ">>> Exp-7 done: $(date)"

# --- Exp-10: cs=1 RoleAlign vs KIVI (~1h) ---
echo ">>> Exp-10: cs=1 RoleAlign vs KIVI"

echo ">>> INT4-RoleAlign cs=1"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_1P5B" \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB_RA" \
  --chunk_size 1 --max_samples 100 --seed 1234 \
  --save_csv --out_dir "$DEF_RD/runs/ppl_ra_cs1_1p5b" \
  2>&1 | tee -a "$DEF_RD/logs/exp10_cs1.log"

echo ">>> KIVI cs=1"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_1P5B" \
  --kv_mode kivi_style \
  --chunk_size 1 --max_samples 100 --seed 1234 \
  --save_csv --out_dir "$DEF_RD/runs/ppl_kivi_cs1_1p5b" \
  2>&1 | tee -a "$DEF_RD/logs/exp10_cs1.log"

echo ">>> Exp-10 done: $(date)"

echo ""
echo "=========================================="
echo "  GPU-1 Chain ALL DONE: $(date)"
echo "=========================================="
