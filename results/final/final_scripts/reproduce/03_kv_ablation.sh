#!/bin/bash
# ================================================================
# Step 3: K/V 消融 + B10 校准灵敏度 — 产出 kv_ablation/ 数据
# ================================================================
# 输出: results/final/final_data/kv_ablation/runs/
# 原始: scripts/archive/expansion_gpu0.sh + expansion_gpu1.sh
# 配置: configs/snapshots/exp_matrix_b10_sens_*.yaml
#        configs/snapshots/exp_matrix_mixed_kv_*.yaml
# GPU: ~8-10h
# ================================================================
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

OUT="results/final/final_data/kv_ablation/runs"

# ─────────── Part A: B10 校准灵敏度 (1.5B + 7B) ───────────
echo "═══ Part A: B10 sensitivity ═══"

# 1.5B B10
for SAMPLES in 16 64 256; do
  python3 scripts/run_experiments.py \
    --config "configs/snapshots/exp_matrix_b10_sens_1p5b_s${SAMPLES}.yaml" \
    --tasks eval_ppl --seeds 1234 \
    --out_dir "$OUT" --run_tag exp_b10_1p5b
  python3 scripts/run_experiments.py \
    --config "configs/snapshots/exp_matrix_b10_sens_1p5b_s${SAMPLES}.yaml" \
    --tasks eval_needle --seeds 1234,1235,1236 \
    --out_dir "$OUT" --run_tag exp_b10_1p5b --append
  python3 scripts/run_experiments.py \
    --config "configs/snapshots/exp_matrix_b10_sens_1p5b_s${SAMPLES}.yaml" \
    --tasks eval_longbench --seeds 1234,1235,1236 \
    --out_dir "$OUT" --run_tag exp_b10_1p5b --append \
    --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64
done

# 7B B10
for SAMPLES in 16 64 256; do
  python3 scripts/run_experiments.py \
    --config "configs/snapshots/exp_matrix_b10_sens_7b_s${SAMPLES}.yaml" \
    --tasks eval_ppl --seeds 1234 \
    --out_dir "$OUT" --run_tag exp_b10_7b
  python3 scripts/run_experiments.py \
    --config "configs/snapshots/exp_matrix_b10_sens_7b_s${SAMPLES}.yaml" \
    --tasks eval_needle --seeds 1234,1235,1236 \
    --out_dir "$OUT" --run_tag exp_b10_7b --append
  python3 scripts/run_experiments.py \
    --config "configs/snapshots/exp_matrix_b10_sens_7b_s${SAMPLES}.yaml" \
    --tasks eval_longbench --seeds 1234,1235,1236 \
    --out_dir "$OUT" --run_tag exp_b10_7b --append \
    --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64
done

# ─────────── Part B: K/V 消融 LongBench + RULER (1.5B/7B/8B) ───────────
echo "═══ Part B: K/V ablation LongBench + RULER ═══"

KV_RUNS="k_only_int8_long,v_only_int4_long,k_int4_v_int8_long"

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_1p5b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_longbench --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_1p5b \
  --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_1p5b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_ruler --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_1p5b --append --ruler_num_cases 64

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_7b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_longbench --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_7b \
  --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_7b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_ruler --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_7b --append --ruler_num_cases 64

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_8b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_longbench --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_8b \
  --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_8b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_ruler --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_8b --append --ruler_num_cases 64

# ─────────── Part C: K/V 消融 LongBench (Mistral) ───────────
echo "═══ Part C: K/V ablation LongBench (Mistral) ═══"

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_mistral7b_v1.yaml \
  --run_names "$KV_RUNS" --tasks eval_longbench --seeds 1234,1235,1236 \
  --out_dir "$OUT" --run_tag exp_mistral \
  --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

# ─────────── Part D: 跨模型 baselines (7B + 8B) ───────────
echo "═══ Part D: Cross-model baselines ═══"

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_qwen25_7b_v1.yaml \
  --run_names fp16_kv_long,int8_baseline_long,int8_ours_long \
  --tasks eval_ruler --seeds 1234 \
  --out_dir "$OUT" --run_tag c6san_7b --ruler_num_cases 64

python3 scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_llama31_8b_v1.yaml \
  --run_names fp16_kv_long,int8_baseline_long,int8_ours_long \
  --tasks eval_ruler --seeds 1234 \
  --out_dir "$OUT" --run_tag c6san_8b --ruler_num_cases 64
