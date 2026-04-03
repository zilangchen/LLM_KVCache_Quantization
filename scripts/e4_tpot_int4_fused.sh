#!/bin/bash
# E-4b: INT4-RA TPOT profiling — torch_ref vs triton_int4_asym
# 对比融合核函数 vs 非融合路径的延迟差异
# 注意：TPOT profiling 需要独占 GPU！
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

GPU="${1:-0}"
export CUDA_VISIBLE_DEVICES=$GPU

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
CALIB="artifacts/kv_calib_rolealign_1p5b_v3.json"
RD="results/emnlp_defense_v1/runs"

echo "===== E-4b: INT4-RA TPOT Fused vs Ref (GPU-$GPU) ====="
echo "Started: $(date)"

# 1. torch_ref baseline (current default)
echo "--- INT4-RA torch_ref TPOT ---"
python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB" \
  --decode_attn_impl torch_ref \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_ra_torch_ref_1p5b"

# 2. triton_int4_asym (new fused kernel)
echo "--- INT4-RA triton_int4_asym TPOT ---"
python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file "$CALIB" \
  --decode_attn_impl triton_int4_asym \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_ra_fused_1p5b"

# 3. FP16 baseline for reference
echo "--- FP16 TPOT ---"
python3 scripts/profile_latency.py \
  --model_id "$MODEL" --kv_mode fp16 \
  --seq_len 4096 --gen_len 128 --batch 1 \
  --warmup 3 --runs 5 --save_csv \
  --out_dir "$RD/tpot_fp16_e4_ref_1p5b"

echo "===== E-4b Complete ====="
echo "Finished: $(date)"
