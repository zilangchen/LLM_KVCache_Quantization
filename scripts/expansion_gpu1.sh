#!/usr/bin/env bash
# Expansion Pack — GPU 1 Task Chain
# Wave 1: Phase 1 (B10 calibration + eval for 7B) + Phase 5 (Mistral heatmap)
# Wave 2: Phase 2 (K/V ablation LongBench for 7B + Mistral)
# Wave 3: Phase 3 (C6 RULER sanity 8B) + Phase 4 (K/V ablation RULER 7B)
#
# Usage: CUDA_VISIBLE_DEVICES=1 bash scripts/expansion_gpu1.sh 2>&1 | tee logs/expansion_gpu1.log
# Created: 2026-03-19

set -euo pipefail

export HF_HOME=/root/autodl-tmp/hf_cache
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

PYTHON="${PYTHON:-python3}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RESULTS_DIR="results/emnlp_expansion_v1/runs"
mkdir -p "$RESULTS_DIR" logs results/attention_kl

echo "=== Expansion GPU 1 — started $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# Wave 1: Phase 5 — Mistral heatmap (quick, ~30 min)
# =====================================================================
echo "--- Phase 5: Mistral attention KL heatmap ---"
$PYTHON scripts/collect_attention_kl.py \
    --model_id mistralai/Mistral-7B-Instruct-v0.3 \
    --model_revision c170c708c41dac9275d15a8fff4eca08d52bab71 \
    --kv_mode int4_mixed_kv --k_bits 8 --v_bits 4 \
    --seq_len 4096 --seed 1234 --num_samples 16 \
    --out_dir results/attention_kl
echo "Phase 5 DONE $(date '+%Y-%m-%d %H:%M:%S')"

# =====================================================================
# Wave 1: Phase 1 — B10 calibration sensitivity (7B)
# =====================================================================
echo "--- Phase 1: B10 calibration 7B ---"

# Step 1: Generate 3 calibration artifacts (16, 64, 256 samples)
for SAMPLES in 16 64 256; do
    CALIB_OUT="artifacts/kv_calib_kl_b10_7b_s${SAMPLES}.json"
    if [ -f "$CALIB_OUT" ]; then
        echo "SKIP: $CALIB_OUT already exists"
    else
        echo "Calibrating 7B with samples=$SAMPLES ..."
        $PYTHON scripts/calibrate_behavior.py \
            --model_id Qwen/Qwen2.5-7B-Instruct \
            --model_revision a09a35458c702b33eeacc393d103063234e8bc28 \
            --samples "$SAMPLES" --quant_bits 8 --loss_function kl \
            --group_size_k 16 --group_size_v 16 \
            --calib_out "$CALIB_OUT"
        echo "DONE: $CALIB_OUT"
    fi
done

# Step 2: Evaluate each B10 variant
for SAMPLES in 16 64 256; do
    CFG="configs/snapshots/exp_matrix_b10_sens_7b_s${SAMPLES}.yaml"
    TAG="exp_b10_7b"

    echo "Evaluating 7B B10 s=$SAMPLES — PPL (seed 1234) ..."
    $PYTHON scripts/run_experiments.py \
        --config "$CFG" --tasks eval_ppl --seeds 1234 \
        --out_dir "$RESULTS_DIR" --run_tag "$TAG"

    echo "Evaluating 7B B10 s=$SAMPLES — Needle (seeds 1234-1236) ..."
    $PYTHON scripts/run_experiments.py \
        --config "$CFG" --tasks eval_needle --seeds 1234,1235,1236 \
        --out_dir "$RESULTS_DIR" --run_tag "$TAG" --append

    echo "Evaluating 7B B10 s=$SAMPLES — LongBench (seeds 1234-1236) ..."
    $PYTHON scripts/run_experiments.py \
        --config "$CFG" --tasks eval_longbench --seeds 1234,1235,1236 \
        --out_dir "$RESULTS_DIR" --run_tag "$TAG" --append \
        --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

    echo "DONE: 7B B10 s=$SAMPLES"
done

echo "=== Phase 1 (7B) COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# Wave 2: Phase 2 — K/V ablation LongBench (7B + Mistral)
# =====================================================================
echo "--- Phase 2: K/V ablation LongBench 7B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_7b_v1.yaml \
    --tasks eval_longbench \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_7b \
    --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

echo "--- Phase 2: K/V ablation LongBench Mistral ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_mistral7b_v1.yaml \
    --tasks eval_longbench \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_mistral \
    --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

echo "=== Phase 2 (GPU 1) COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# Wave 3: Phase 3 — C6 RULER sanity (8B) + Phase 4 — K/V ablation RULER (7B)
# =====================================================================
echo "--- Phase 3: C6 RULER sanity 8B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_llama31_8b_v1.yaml \
    --tasks eval_ruler \
    --run_names fp16_kv_long,int8_baseline_long,int8_ours_long \
    --seeds 1234 \
    --out_dir "$RESULTS_DIR" --run_tag c6san_8b \
    --ruler_num_cases 64

echo "--- Phase 4: K/V ablation RULER 7B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_7b_v1.yaml \
    --tasks eval_ruler \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_7b \
    --append --ruler_num_cases 64

echo "=== GPU 1 ALL COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="
