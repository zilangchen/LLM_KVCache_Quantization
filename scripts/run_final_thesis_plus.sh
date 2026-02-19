#!/usr/bin/env bash
set -euo pipefail

# Final thesis-plus pipeline:
# - gates
# - profile latency/memory
# - eval needle / ppl
# - throughput batch expansion
# - aggregate + latex export

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/bin/python}"
MODEL_REVISION="${MODEL_REVISION:-989aa7980e4cf806f80c7fef2b1adb7bc71aa306}"
RUN_TAG="${RUN_TAG:-final_thesis_plus_$(date +%Y%m%d_%H%M%S)}"
BASE_DIR="${BASE_DIR:-${PROJECT_ROOT}/results/${RUN_TAG}}"
SEEDS="${SEEDS:-1234,1235,1236}"

INT8_CALIB="${INT8_CALIB:-artifacts/kv_calib_kl_selected_v3_quick.json}"
INT4_CALIB="${INT4_CALIB:-artifacts/kv_calib_kl_int4_selected.json}"

export HF_HOME="${HF_HOME:-/root/autodl-tmp/hf_cache}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/root/autodl-tmp/hf_cache/hub}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-/root/autodl-tmp/hf_cache/datasets}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/root/autodl-tmp/triton_cache}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

mkdir -p "${BASE_DIR}"/{runs,logs,tables,plots,latex_tables,gates,env}
echo "[INFO] RUN_TAG=${RUN_TAG}"
echo "[INFO] BASE_DIR=${BASE_DIR}"

run_cmd() {
  echo "[CMD] $*"
  "$@"
}

echo "[INFO] Collect environment..."
run_cmd "${PYTHON_BIN}" scripts/collect_env.py
cp -f env/versions.txt "${BASE_DIR}/env/versions.txt"
cp -f env/requirements_freeze.txt "${BASE_DIR}/env/requirements_freeze.txt"
git rev-parse HEAD > "${BASE_DIR}/env/git_commit_full.txt"
git status --porcelain > "${BASE_DIR}/env/git_status_porcelain.txt"
git diff > "${BASE_DIR}/env/uncommitted_changes.patch" || true

echo "[INFO] Gates..."
run_cmd "${PYTHON_BIN}" scripts/smoke_test.py --save_output --model_revision "${MODEL_REVISION}" \
  > "${BASE_DIR}/gates/gate0_smoke_test.log" 2>&1
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run \
  > "${BASE_DIR}/gates/gate1_dry_run.log" 2>&1
run_cmd "${PYTHON_BIN}" -m unittest tests/test_triton_kernel.py \
  > "${BASE_DIR}/gates/gate2_triton_unittest.log" 2>&1
KV_FUSED_DEBUG=1 run_cmd "${PYTHON_BIN}" scripts/verify_fused_decode.py \
  --model_revision "${MODEL_REVISION}" \
  --kv_mode int8_fused \
  > "${BASE_DIR}/gates/gate3_verify_int8_fused.log" 2>&1
KV_FUSED_DEBUG=1 run_cmd "${PYTHON_BIN}" scripts/verify_fused_decode.py \
  --model_revision "${MODEL_REVISION}" \
  --kv_mode int8_ours \
  --calib_file "${INT8_CALIB}" \
  --no_use_attn_temperature \
  --adaptive_static_scales \
  > "${BASE_DIR}/gates/gate3_verify_int8_ours.log" 2>&1

if [[ -f "${INT4_CALIB}" ]]; then
  KV_FUSED_DEBUG=1 run_cmd "${PYTHON_BIN}" scripts/verify_fused_decode.py \
    --model_revision "${MODEL_REVISION}" \
    --kv_mode int4_fused \
    > "${BASE_DIR}/gates/gate3_verify_int4_fused.log" 2>&1
  KV_FUSED_DEBUG=1 run_cmd "${PYTHON_BIN}" scripts/verify_fused_decode.py \
    --model_revision "${MODEL_REVISION}" \
    --kv_mode int4_ours \
    --calib_file "${INT4_CALIB}" \
    > "${BASE_DIR}/gates/gate3_verify_int4_ours.log" 2>&1
fi

CORE_RUNS="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,fp16_kv_long,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_baseline_long_torch,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int8_ours_long_static_v3_no_temp_adaptive_fused,int4_fused_curve_4k,int4_fused_curve_8k,int4_fused_curve_16k,int4_fused_long,int4_ours_curve_4k,int4_ours_curve_8k,int4_ours_curve_16k,int4_ours_long"
SHORT_NEEDLE_RUNS="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int4_fused_curve_4k,int4_fused_curve_8k,int4_fused_curve_16k,int4_ours_curve_4k,int4_ours_curve_8k,int4_ours_curve_16k"
LONG_NEEDLE_RUNS="fp16_kv_long,int8_baseline_long_torch,int8_ours_long_static_v3_no_temp_adaptive_fused,int4_fused_long,int4_ours_long"
PPL_RUNS="fp16_kv_curve_4k,int8_baseline_curve_4k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int4_fused_curve_4k,int4_ours_curve_4k"
THROUGHPUT_RUNS="fp16_throughput_8k_b1,fp16_throughput_8k_b2,fp16_throughput_8k_b4,fp16_throughput_8k_b8,fp16_throughput_8k_b16,fp16_throughput_8k_b24,fp16_throughput_8k_b32,int8_baseline_throughput_8k_b1,int8_baseline_throughput_8k_b2,int8_baseline_throughput_8k_b4,int8_baseline_throughput_8k_b8,int8_baseline_throughput_8k_b16,int8_baseline_throughput_8k_b24,int8_baseline_throughput_8k_b32,int8_ours_throughput_8k_b1,int8_ours_throughput_8k_b2,int8_ours_throughput_8k_b4,int8_ours_throughput_8k_b8,int8_ours_throughput_8k_b16,int8_ours_throughput_8k_b24,int8_ours_throughput_8k_b32,int4_fused_throughput_8k_b1,int4_fused_throughput_8k_b2,int4_fused_throughput_8k_b4,int4_fused_throughput_8k_b8,int4_fused_throughput_8k_b16,int4_fused_throughput_8k_b24,int4_fused_throughput_8k_b32,int4_ours_throughput_8k_b1,int4_ours_throughput_8k_b2,int4_ours_throughput_8k_b4,int4_ours_throughput_8k_b8,int4_ours_throughput_8k_b16,int4_ours_throughput_8k_b24,int4_ours_throughput_8k_b32"

echo "[INFO] Core latency/memory..."
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks profile_latency,profile_memory \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names "${CORE_RUNS}" \
  --latency_warmup 2 \
  --latency_runs 3 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"

echo "[INFO] Needle short-context..."
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_needle \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names "${SHORT_NEEDLE_RUNS}" \
  --seeds "${SEEDS}" \
  --needle_num_depths 20 \
  --needle_depth_batch 2 \
  --needle_max_new_tokens 64 \
  --needle_report_exact_match \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"

echo "[INFO] Needle long-context..."
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_needle \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names "${LONG_NEEDLE_RUNS}" \
  --seeds "${SEEDS}" \
  --needle_num_depths 20 \
  --needle_depth_batch 1 \
  --needle_max_new_tokens 64 \
  --needle_report_exact_match \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"

echo "[INFO] PPL (kv_cache + chunk)..."
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_ppl \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names "${PPL_RUNS}" \
  --seeds "${SEEDS}" \
  --ppl_mode kv_cache \
  --ppl_max_length 1024 \
  --ppl_stride 512 \
  --ppl_chunk_size 128 \
  --ppl_max_samples 64 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"

echo "[INFO] Throughput batch expansion..."
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks profile_latency,profile_memory \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names "${THROUGHPUT_RUNS}" \
  --latency_warmup 2 \
  --latency_runs 3 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"

echo "[INFO] Aggregate and export latex..."
run_cmd "${PYTHON_BIN}" scripts/aggregate_results.py \
  --runs_dir "${BASE_DIR}/runs" \
  --tables_dir "${BASE_DIR}/tables" \
  --plots_dir "${BASE_DIR}/plots"
run_cmd "${PYTHON_BIN}" scripts/export_tables_latex.py \
  --tables_dir "${BASE_DIR}/tables" \
  --out_dir "${BASE_DIR}/latex_tables"

echo "[DONE] final thesis plus complete"
echo "[DONE] BASE_DIR=${BASE_DIR}"
