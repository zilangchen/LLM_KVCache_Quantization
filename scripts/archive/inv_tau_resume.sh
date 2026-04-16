#!/bin/bash
# inv_tau 恢复脚本：从 7B with-tau PPL 开始（7B no-tau PPL 已完成）
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=0
RD="results/emnlp_defense_v1/runs"

MODELS_7B="Qwen/Qwen2.5-7B-Instruct"
MODELS_8B="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"

echo "===== inv_tau Resume (7B with-tau + 7B Needle + 8B full) ====="
echo "Started: $(date)"

# === 7B: resume from with-tau PPL ===
echo "--- 7B RA WITH-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODELS_7B" --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$CALIB_7B" \
  --use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_withtau_ppl_7b"

echo "--- 7B RA no-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODELS_7B" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB_7B" \
  --no_use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_notau_needle_7b"

echo "--- 7B RA WITH-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODELS_7B" --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$CALIB_7B" \
  --use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_withtau_needle_7b"

# === 8B: full ===
echo "--- 8B RA no-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODELS_8B" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB_8B" \
  --no_use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_notau_ppl_8b"

echo "--- 8B RA WITH-tau PPL ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODELS_8B" --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$CALIB_8B" \
  --use_attn_temperature \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_withtau_ppl_8b"

echo "--- 8B RA no-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODELS_8B" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB_8B" \
  --no_use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_notau_needle_8b"

echo "--- 8B RA WITH-tau Needle ---"
python3 scripts/eval_needle.py \
  --model_id "$MODELS_8B" --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$CALIB_8B" \
  --use_attn_temperature \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir "$RD/tau_full_ra_withtau_needle_8b"

echo "===== inv_tau Resume Complete ====="
echo "Finished: $(date)"
