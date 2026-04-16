#!/bin/bash
# GPU-0: Exp-4 KIVI residual_length=128 验证
# 对比 KIVI 无 residual (已有 PPL=10.4294) vs 有 residual 的 PPL
# 注意: residual_length 通过 generate_loop.py 的 generate() 函数传递，
# 但 eval_ppl.py 不走 generate()，走 eval_window_kv_cache()。
# eval_ppl.py 的 build_kv_cache() 直接构造 KIVIStyleKVCache，
# 不接受 residual_length 参数。
# 因此 Exp-4 需要通过 eval_needle.py (走 generate_from_ids) 验证。
# generate_from_ids 的 residual_length 目前硬编码为 0。
# → Exp-4 需要先修改 generate_from_ids 支持 residual_length 参数。
#
# 暂时跑 KIVI PPL cs=128 作为 baseline 对照（已有 10.4294）。
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

echo "===== KIVI PPL cs=128 baseline re-verify ====="
echo "Started: $(date)"

python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --chunk_size 128 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_kivi_cs128_reverify

echo "===== KIVI PPL cs=8 ====="
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --chunk_size 8 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_kivi_cs8_1p5b

echo "===== INT4-RA PPL cs=8 ====="
python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --chunk_size 8 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_ra_cs8_1p5b

echo "===== All Done ====="
echo "Finished: $(date)"
