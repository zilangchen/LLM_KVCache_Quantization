#!/bin/bash
# GPU-0 链式任务: KIVI Needle 32K → KIVI Needle 多上下文
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

# KIVI Needle 32K (之前因 NameError 失败)
echo "===== KIVI Needle 32K ====="
echo "Started: $(date)"
python3 scripts/eval_needle.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --seq_len 32704 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/needle_kivi_32k_postfix

# KIVI Needle 8K/16K
for CTX in 8192 16384; do
  echo "===== KIVI Needle ctx=$CTX ====="
  python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode kivi_style --quant_bits 4 \
    --seq_len $CTX --seed 1234 \
    --save_csv --out_dir results/emnlp_defense_v1/runs/needle_kivi_ctx${CTX}_1p5b
done

# KIVI RULER 4K (对比 RA RULER)
echo "===== KIVI RULER 4K ====="
python3 scripts/eval_ruler.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style --quant_bits 4 \
  --seq_len 4096 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ruler_kivi_4k_1p5b

echo "===== All GPU-0 tasks Done ====="
echo "Finished: $(date)"
