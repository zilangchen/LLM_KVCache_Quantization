#!/bin/bash
# Isolation experiment: KL vs MSE calibration objectives
# 目的：回应 Q10 "方法论创新不清晰 / KL 增益未隔离"
# 固定：kernel (torch_ref), adaptive=off, inv_tau=off
# 变量：校准目标 ∈ {KL, MSE}
# 评测：PPL + Needle 8K + RULER 4K
# 模型：Qwen2.5-1.5B（单模型控制成本）
# 成本估算：~6 GPU-hour

set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=0

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
RD="results/emnlp_defense_v1/runs"
SEED=1234
TS=$(date +%Y%m%d_%H%M%S)

echo "===== Isolation KL vs MSE Experiment ====="
echo "Started: $(date)"

# ===== Step 1: 生成 KL 校准产物 =====
KL_CALIB="artifacts/kv_calib_kl_isolation_1p5b_v1.json"
if [ ! -f "$KL_CALIB" ]; then
  echo "--- Generating KL calibration (isolation) ---"
  python3 scripts/calibrate_behavior.py \
    --model_id "$MODEL" \
    --loss_function kl \
    --quant_bits 8 \
    --samples 128 \
    --seq_len 512 \
    --seed $SEED \
    --search \
    --search_objective mean_kl \
    --calib_out "$KL_CALIB"
else
  echo "--- KL calibration exists: $KL_CALIB ---"
fi

# ===== Step 2: 生成 MSE 校准产物 =====
MSE_CALIB="artifacts/kv_calib_mse_isolation_1p5b_v1.json"
if [ ! -f "$MSE_CALIB" ]; then
  echo "--- Generating MSE calibration (isolation) ---"
  python3 scripts/calibrate_behavior.py \
    --model_id "$MODEL" \
    --loss_function mse \
    --quant_bits 8 \
    --samples 128 \
    --seq_len 512 \
    --seed $SEED \
    --search \
    --search_objective mean_mse \
    --calib_out "$MSE_CALIB"
else
  echo "--- MSE calibration exists: $MSE_CALIB ---"
fi

# ===== Step 3: 对每个校准产物跑 PPL + Needle + RULER =====
for OBJ in kl mse; do
  CALIB_FILE="artifacts/kv_calib_${OBJ}_isolation_1p5b_v1.json"

  if [ ! -f "$CALIB_FILE" ]; then
    echo "WARNING: $CALIB_FILE missing, skipping $OBJ evaluation"
    continue
  fi

  echo "--- [${OBJ}] PPL on 1.5B ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" \
    --kv_mode int8_ours --quant_bits 8 \
    --calib_file "$CALIB_FILE" \
    --no_use_attn_temperature \
    --chunk_size 128 --seed $SEED \
    --save_csv --out_dir "$RD/isolation_${OBJ}_ppl_1p5b"

  echo "--- [${OBJ}] Needle 8K on 1.5B ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" \
    --kv_mode int8_ours --quant_bits 8 \
    --calib_file "$CALIB_FILE" \
    --no_use_attn_temperature \
    --context_len 8192 --seed $SEED \
    --save_csv --out_dir "$RD/isolation_${OBJ}_needle_8k_1p5b"

  echo "--- [${OBJ}] RULER 4K on 1.5B ---"
  python3 scripts/eval_ruler.py \
    --model_id "$MODEL" \
    --kv_mode int8_ours --quant_bits 8 \
    --calib_file "$CALIB_FILE" \
    --no_use_attn_temperature \
    --seq_len 4096 --seed $SEED \
    --save_csv --out_dir "$RD/isolation_${OBJ}_ruler_1p5b"
done

echo "===== Isolation Experiment Complete ====="
echo "Finished: $(date)"
echo ""
echo "Quick summary:"
for OBJ in kl mse; do
  echo "--- [${OBJ}] results ---"
  find "$RD/isolation_${OBJ}_"* -name "profile_*.csv" 2>/dev/null | while read csv; do
    echo "  $csv"
  done
done
