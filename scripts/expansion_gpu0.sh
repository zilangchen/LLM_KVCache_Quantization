#!/usr/bin/env bash
# Expansion Pack — GPU 0 Task Chain
# Wave 1: Phase 1 (B10 calibration + eval for 1.5B)
# Wave 2: Phase 2 (K/V ablation LongBench for 1.5B + 8B)
# Wave 3: Phase 3 (C6 RULER sanity 7B) + Phase 4 (K/V ablation RULER 1.5B + 8B)
#
# Usage: CUDA_VISIBLE_DEVICES=0 bash scripts/expansion_gpu0.sh 2>&1 | tee logs/expansion_gpu0.log
# Created: 2026-03-19

set -euo pipefail

PYTHON="${PYTHON:-python3}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RESULTS_DIR="results/emnlp_expansion_v1/runs"
mkdir -p "$RESULTS_DIR" logs

echo "=== Expansion GPU 0 — started $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# Wave 1: Phase 1 — B10 calibration sensitivity (1.5B)
# =====================================================================
echo "--- Phase 1: B10 calibration 1.5B ---"

# Step 1: Generate 3 calibration artifacts (16, 64, 256 samples)
for SAMPLES in 16 64 256; do
    CALIB_OUT="artifacts/kv_calib_kl_b10_1p5b_s${SAMPLES}.json"
    if [ -f "$CALIB_OUT" ]; then
        echo "SKIP: $CALIB_OUT already exists"
    else
        echo "Calibrating 1.5B with samples=$SAMPLES ..."
        $PYTHON scripts/calibrate_behavior.py \
            --model_id Qwen/Qwen2.5-1.5B-Instruct \
            --model_revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
            --samples "$SAMPLES" --quant_bits 8 --loss_function kl \
            --group_size_k 16 --group_size_v 16 \
            --calib_out "$CALIB_OUT"
        echo "DONE: $CALIB_OUT"
    fi
done

# Step 2: Evaluate each B10 variant
for SAMPLES in 16 64 256; do
    CFG="configs/snapshots/exp_matrix_b10_sens_1p5b_s${SAMPLES}.yaml"
    TAG="exp_b10_1p5b"

    echo "Evaluating 1.5B B10 s=$SAMPLES — PPL (seed 1234) ..."
    $PYTHON scripts/run_experiments.py \
        --config "$CFG" --tasks eval_ppl --seeds 1234 \
        --out_dir "$RESULTS_DIR" --run_tag "$TAG"

    echo "Evaluating 1.5B B10 s=$SAMPLES — Needle (seeds 1234-1236) ..."
    $PYTHON scripts/run_experiments.py \
        --config "$CFG" --tasks eval_needle --seeds 1234,1235,1236 \
        --out_dir "$RESULTS_DIR" --run_tag "$TAG" --append

    echo "Evaluating 1.5B B10 s=$SAMPLES — LongBench (seeds 1234-1236) ..."
    $PYTHON scripts/run_experiments.py \
        --config "$CFG" --tasks eval_longbench --seeds 1234,1235,1236 \
        --out_dir "$RESULTS_DIR" --run_tag "$TAG" --append \
        --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

    echo "DONE: 1.5B B10 s=$SAMPLES"
done

echo "=== Phase 1 (1.5B) COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# Wave 2: Phase 2 — K/V ablation LongBench (1.5B + 8B)
# =====================================================================
echo "--- Phase 2: K/V ablation LongBench 1.5B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_1p5b_v1.yaml \
    --tasks eval_longbench \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_1p5b \
    --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

echo "--- Phase 2: K/V ablation LongBench 8B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_8b_v1.yaml \
    --tasks eval_longbench \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_8b \
    --longbench_source synthetic --longbench_max_samples 32 --longbench_max_new_tokens 64

echo "=== Phase 2 (GPU 0) COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# Wave 3: Phase 3 — C6 RULER sanity (7B) + Phase 4 — K/V ablation RULER
# =====================================================================
echo "--- Phase 3: C6 RULER sanity 7B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_qwen25_7b_v1.yaml \
    --tasks eval_ruler \
    --run_names fp16_kv_long,int8_baseline_long,int8_ours_long \
    --seeds 1234 \
    --out_dir "$RESULTS_DIR" --run_tag c6san_7b \
    --ruler_num_cases 64

echo "--- Phase 4: K/V ablation RULER 1.5B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_1p5b_v1.yaml \
    --tasks eval_ruler \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_1p5b \
    --append --ruler_num_cases 64

echo "--- Phase 4: K/V ablation RULER 8B ---"
$PYTHON scripts/run_experiments.py \
    --config configs/snapshots/exp_matrix_mixed_kv_8b_v1.yaml \
    --tasks eval_ruler \
    --run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long \
    --seeds 1234,1235,1236 \
    --out_dir "$RESULTS_DIR" --run_tag exp_8b \
    --append --ruler_num_cases 64

echo "=== GPU 0 ALL COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="
