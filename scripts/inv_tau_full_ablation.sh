#!/bin/bash
# inv_tau 全量消融：3 模型 × tau on/off × PPL + Needle
# 单卡串行跑
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=0
RD="results/emnlp_defense_v1/runs"

MODELS=("Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-7B-Instruct" "/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct")
SHORTS=("1p5b" "7b" "8b")
RA_CALIBS=("artifacts/kv_calib_rolealign_1p5b_v3.json" "artifacts/kv_calib_rolealign_7b_v3.json" "artifacts/kv_calib_rolealign_8b_v3.json")

echo "===== inv_tau Full Ablation (3 models, single GPU) ====="
echo "Started: $(date)"

for i in 0 1 2; do
  MODEL="${MODELS[$i]}"
  SHORT="${SHORTS[$i]}"
  CALIB="${RA_CALIBS[$i]}"

  echo ""
  echo "===== Model: $SHORT ====="

  # Skip 1p5b if already done
  if [ "$SHORT" = "1p5b" ]; then
    echo "--- 1p5b already done in previous run, skipping PPL ---"
    # But run extra seeds for Needle
    for SEED in 1235 1236; do
      echo "--- RA WITH-tau Needle seed=$SEED ---"
      python3 scripts/eval_needle.py \
        --model_id "$MODEL" --kv_mode int4_ours_asym_ba --quant_bits 4 \
        --calib_file "$CALIB" \
        --use_attn_temperature \
        --seq_len 4096 --seed $SEED \
        --save_csv --out_dir "$RD/tau_full_ra_withtau_needle_${SHORT}_s${SEED}"

      echo "--- RA no-tau Needle seed=$SEED ---"
      python3 scripts/eval_needle.py \
        --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
        --calib_file "$CALIB" \
        --no_use_attn_temperature \
        --seq_len 4096 --seed $SEED \
        --save_csv --out_dir "$RD/tau_full_ra_notau_needle_${SHORT}_s${SEED}"
    done
    # Also run RULER for 1p5b with tau
    echo "--- RA WITH-tau RULER 4K ---"
    python3 scripts/eval_ruler.py \
      --model_id "$MODEL" --kv_mode int4_ours_asym_ba --quant_bits 4 \
      --calib_file "$CALIB" \
      --use_attn_temperature \
      --seq_len 4096 --seed 1234 \
      --save_csv --out_dir "$RD/tau_full_ra_withtau_ruler_${SHORT}"
    continue
  fi

  # 7B and 8B: full PPL + Needle for both tau on/off
  echo "--- RA no-tau PPL ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" \
    --no_use_attn_temperature \
    --chunk_size 128 --seed 1234 \
    --save_csv --out_dir "$RD/tau_full_ra_notau_ppl_${SHORT}"

  echo "--- RA WITH-tau PPL ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym_ba --quant_bits 4 \
    --calib_file "$CALIB" \
    --use_attn_temperature \
    --chunk_size 128 --seed 1234 \
    --save_csv --out_dir "$RD/tau_full_ra_withtau_ppl_${SHORT}"

  echo "--- RA no-tau Needle ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB" \
    --no_use_attn_temperature \
    --seq_len 4096 --seed 1234 \
    --save_csv --out_dir "$RD/tau_full_ra_notau_needle_${SHORT}"

  echo "--- RA WITH-tau Needle ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" --kv_mode int4_ours_asym_ba --quant_bits 4 \
    --calib_file "$CALIB" \
    --use_attn_temperature \
    --seq_len 4096 --seed 1234 \
    --save_csv --out_dir "$RD/tau_full_ra_withtau_needle_${SHORT}"
done

echo ""
echo "===== inv_tau Full Ablation Complete ====="
echo "Finished: $(date)"
