#!/bin/bash
# 64K context ablation on LLaMA-3.1-8B (最大 H_kv=8)
# 目的：验证 INT4-RA 在 64K 上仍能维持 Needle 100%
# 成本：2-3 GPU-hour
# 显存预估：
#   - 8B BF16 weights: ~16 GB
#   - KV @ 64K FP16: 64K × 32 layers × 8 heads × 128 × 2 × 2B = 8.4 GB
#   - INT4-RA: ~2.1 GB
#   - 总占用（FP16）: ~25 GB / (INT4-RA): ~18 GB
#   - H20 98GB 足够

set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

export CUDA_VISIBLE_DEVICES=0

MODEL="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
CALIB_RA="artifacts/kv_calib_rolealign_8b_v3.json"
RD="results/emnlp_defense_v1/runs"
SEED=1234

echo "===== 64K Context Ablation on 8B ====="
echo "Started: $(date)"

# 预检：显存状态
echo "--- GPU memory check ---"
nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader

# 预检：模型和校准产物存在
if [ ! -d "$MODEL" ]; then
  echo "ERROR: Model not found: $MODEL"
  exit 1
fi
if [ ! -f "$CALIB_RA" ]; then
  echo "ERROR: RoleAlign 8B calibration not found: $CALIB_RA"
  exit 1
fi

# ===== Step 1: FP16 Needle 64K =====
echo "--- [FP16] Needle 64K ---"
python3 scripts/eval_needle.py \
  --model_id "$MODEL" \
  --kv_mode fp16 \
  --context_len 65536 --seed $SEED \
  --save_csv --out_dir "$RD/needle_fp16_64k_8b"

# ===== Step 2: INT4-RA Needle 64K =====
echo "--- [INT4-RA] Needle 64K ---"
python3 scripts/eval_needle.py \
  --model_id "$MODEL" \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB_RA" \
  --no_use_attn_temperature \
  --context_len 65536 --seed $SEED \
  --save_csv --out_dir "$RD/needle_ra_64k_8b"

echo "===== 64K Context Ablation Complete ====="
echo "Finished: $(date)"

# Quick summary
for MODE in fp16 ra; do
  DIR="$RD/needle_${MODE}_64k_8b"
  if [ -d "$DIR" ]; then
    echo "[${MODE}] CSV:"
    find "$DIR" -name "profile_needle_*.csv" 2>/dev/null | head -1
  fi
done
