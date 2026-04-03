#!/bin/bash
# Exp-4: KIVI residual_length=128 vs 0 对比
# 测试完整 KIVI 残差缓冲区对 PPL/Needle 的影响
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

GPU="${1:-0}"
export CUDA_VISIBLE_DEVICES=$GPU

RD="results/emnlp_defense_v1/runs"
MODEL="Qwen/Qwen2.5-1.5B-Instruct"

echo "===== Exp-4: KIVI Residual Length (GPU-$GPU) ====="
echo "Started: $(date)"

# 注意：需要 generate_loop.py 支持 residual_length 参数传递
# 如果 eval_ppl.py 不支持 --residual_length，需要先修改代码

for RLEN in 0 64 128; do
  echo "--- KIVI INT4 residual=$RLEN PPL ---"
  python3 scripts/eval_ppl.py \
    --model_id "$MODEL" --kv_mode kivi_style --quant_bits 4 \
    --residual_length $RLEN \
    --chunk_size 128 --seed 1234 \
    --save_csv --out_dir "$RD/ppl_kivi_res${RLEN}_1p5b"

  echo "--- KIVI INT4 residual=$RLEN Needle ---"
  python3 scripts/eval_needle.py \
    --model_id "$MODEL" --kv_mode kivi_style --quant_bits 4 \
    --residual_length $RLEN \
    --seq_len 4096 --seed 1234 \
    --save_csv --out_dir "$RD/needle_kivi_res${RLEN}_1p5b"
done

echo "===== Exp-4 Complete ====="
echo "Finished: $(date)"
