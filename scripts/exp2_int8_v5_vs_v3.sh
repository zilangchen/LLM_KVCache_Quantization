#!/bin/bash
# Exp-2: INT8 v5_fixed (含RoPE) vs v3_quick (缺RoPE) 校准对比
# 仅 1.5B，3 seeds × PPL + Needle
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

GPU="${1:-0}"
export CUDA_VISIBLE_DEVICES=$GPU

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
RD="results/emnlp_defense_v1/runs"

# 校准文件检查
V5="artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json"
V3="artifacts/kv_calib_kl_selected_v3_quick.json"

if [ ! -f "$V5" ]; then
  echo "FATAL: v5_fixed calibration not found: $V5" >&2
  exit 1
fi
if [ ! -f "$V3" ]; then
  echo "FATAL: v3_quick calibration not found: $V3" >&2
  exit 1
fi

echo "===== Exp-2: INT8 v5 vs v3 (GPU-$GPU) ====="
echo "Started: $(date)"

for SEED in 1234 1235 1236; do
  echo "--- v5_fixed PPL seed=$SEED ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode int8_ours \
    --calib_file "$V5" \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir "$RD/ppl_int8_v5_1p5b_s${SEED}"

  echo "--- v5_fixed Needle seed=$SEED ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" --kv_mode int8_ours \
    --calib_file "$V5" \
    --seq_len 4096 --seed $SEED \
    --save_csv --out_dir "$RD/needle_int8_v5_1p5b_s${SEED}"

  echo "--- v3_quick PPL seed=$SEED (baseline check) ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode int8_ours \
    --calib_file "$V3" \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir "$RD/ppl_int8_v3_reverify_1p5b_s${SEED}"
done

echo "===== Exp-2 Complete ====="
echo "Finished: $(date)"
