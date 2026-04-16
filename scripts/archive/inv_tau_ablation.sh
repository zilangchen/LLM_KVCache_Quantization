#!/bin/bash
# inv_tau 消融：int4_ours_asym (无tau) vs int4_ours_asym_ba (有tau)
# 同时跑 INT8 的 tau on/off 对比
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

GPU="${1:-0}"
export CUDA_VISIBLE_DEVICES=$GPU

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
RA_CALIB="artifacts/kv_calib_rolealign_1p5b_v3.json"
INT8_CALIB="artifacts/kv_calib_kl_selected_v3_quick.json"
RD="results/emnlp_defense_v1/runs"

echo "===== inv_tau Ablation (GPU-$GPU) ====="
echo "Started: $(date)"

# --- INT4-RoleAlign 无 tau (baseline, 已有数据但重跑确认) ---
echo "--- INT4-RA no-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$RA_CALIB" \
  --no_use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_ra_notau_ppl"

echo "--- INT4-RA no-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$RA_CALIB" \
  --no_use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_ra_notau_needle"

# --- INT4-RoleAlign 有 tau (int4_ours_asym_ba) ---
echo "--- INT4-RA with-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$RA_CALIB" \
  --use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_ra_withtau_ppl"

echo "--- INT4-RA with-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$RA_CALIB" \
  --use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_ra_withtau_needle"

# --- INT8-ours 无 tau (mainline, 已有数据) ---
echo "--- INT8 no-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL" --kv_mode int8_ours \
  --calib_file "$INT8_CALIB" \
  --no_use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_int8_notau_ppl"

echo "--- INT8 no-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODEL" --kv_mode int8_ours \
  --calib_file "$INT8_CALIB" \
  --no_use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_int8_notau_needle"

# --- INT8-ours 有 tau ---
echo "--- INT8 with-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL" --kv_mode int8_ours \
  --calib_file "$INT8_CALIB" \
  --use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_int8_withtau_ppl"

echo "--- INT8 with-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODEL" --kv_mode int8_ours \
  --calib_file "$INT8_CALIB" \
  --use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_ablation_int8_withtau_needle"

echo "===== inv_tau Ablation Complete ====="
echo "Finished: $(date)"
