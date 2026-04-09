#!/bin/bash
# Qwen2.5-14B 扩展实验：验证 Claim 5 (inv_tau × GQA) 在更大模型上
# 前提：14B 模型已通过 download_qwen14b.sh 下载
# 成本：校准 5h + 评测 15h = 20 GPU-hour
# H_kv: Qwen2.5-14B 有 8 KV heads (与 LLaMA-3.1-8B 相同)
#        所以 14B 是 "same H_kv, larger scale" 的验证

set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=0

MODEL_DIR="/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct"
CALIB_OUT="artifacts/kv_calib_rolealign_14b_v3.json"
RD="results/emnlp_defense_v1/runs"
SEED=1234

echo "===== Qwen2.5-14B Extended Experiment ====="
echo "Started: $(date)"

# 预检
if [ ! -d "$MODEL_DIR" ]; then
  echo "ERROR: 14B model not downloaded yet: $MODEL_DIR"
  echo "Run scripts/download_qwen14b.sh first"
  exit 1
fi

echo "--- GPU status ---"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

# ===== Step 1: 生成 RoleAlign 校准产物 =====
if [ ! -f "$CALIB_OUT" ]; then
  echo "--- Step 1: Generating RoleAlign calibration for 14B ---"
  python3 scripts/calibrate_behavior.py \
    --model_id "$MODEL_DIR" \
    --role_aware_axes \
    --quant_bits 4 \
    --samples 128 \
    --seq_len 512 \
    --seed $SEED \
    --search \
    --calib_out "$CALIB_OUT"
else
  echo "--- Calibration exists: $CALIB_OUT ---"
fi

# ===== Step 2: FP16 PPL baseline =====
echo "--- Step 2: FP16 PPL on 14B ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_DIR" \
  --kv_mode fp16 \
  --chunk_size 128 --seed $SEED \
  --save_csv --out_dir "$RD/ppl_fp16_14b_s${SEED}"

# ===== Step 3: INT4-RA PPL (no tau) =====
echo "--- Step 3: INT4-RA PPL no-tau on 14B ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_DIR" \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB_OUT" \
  --no_use_attn_temperature \
  --chunk_size 128 --seed $SEED \
  --save_csv --out_dir "$RD/ppl_ra_notau_14b_s${SEED}"

# ===== Step 4: INT4-RA PPL (with tau) - 验证 Claim 5 =====
echo "--- Step 4: INT4-RA PPL with-tau on 14B (Claim 5 validation) ---"
python3 scripts/eval_ppl.py \
  --model_id "$MODEL_DIR" \
  --kv_mode int4_ours_asym_ba --quant_bits 4 \
  --calib_file "$CALIB_OUT" \
  --use_attn_temperature \
  --chunk_size 128 --seed $SEED \
  --save_csv --out_dir "$RD/ppl_ra_withtau_14b_s${SEED}"

# ===== Step 5: Needle 4K/8K/16K =====
for CTX in 4096 8192 16384; do
  echo "--- Needle ctx=${CTX} on 14B FP16 ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL_DIR" \
    --kv_mode fp16 \
    --context_len $CTX --seed $SEED \
    --save_csv --out_dir "$RD/needle_fp16_ctx${CTX}_14b"

  echo "--- Needle ctx=${CTX} on 14B INT4-RA ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL_DIR" \
    --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file "$CALIB_OUT" \
    --no_use_attn_temperature \
    --context_len $CTX --seed $SEED \
    --save_csv --out_dir "$RD/needle_ra_ctx${CTX}_14b"
done

echo "===== 14B Experiment Complete ====="
echo "Finished: $(date)"

# Summary
echo ""
echo "=== 14B Results Summary ==="
for DIR in "$RD/ppl_fp16_14b_s${SEED}" "$RD/ppl_ra_notau_14b_s${SEED}" "$RD/ppl_ra_withtau_14b_s${SEED}"; do
  if [ -d "$DIR" ]; then
    CSV=$(find "$DIR" -name "profile_ppl_*.csv" | head -1)
    if [ -n "$CSV" ]; then
      echo "$DIR:"
      head -2 "$CSV" | tail -1 | cut -d, -f20
    fi
  fi
done
