#!/usr/bin/env bash
set -euo pipefail

# Week-4 journal-grade final rerun pipeline.
# Scope: fp16 / int8_baseline / int8_ours mainline only.
# Output package target: results/final_journal_v1/

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/bin/python}"
CONFIG_PATH="${CONFIG_PATH:-configs/snapshots/exp_matrix_week4_final_journal_v1.yaml}"
MODEL_REVISION="${MODEL_REVISION:-989aa7980e4cf806f80c7fef2b1adb7bc71aa306}"

RUN_TAG="${RUN_TAG:-final_journal_v1}"
BASE_DIR="${BASE_DIR:-${PROJECT_ROOT}/results/final_journal_v1}"
MAIN_SEEDS="${MAIN_SEEDS:-1234,1235,1236,1237,1238}"
THROUGHPUT_SEEDS="${THROUGHPUT_SEEDS:-1234,1235,1236,1237,1238,1239,1240,1241}"
MAX_REPAIR_ITER="${MAX_REPAIR_ITER:-8}"
ALLOW_RESUME="${ALLOW_RESUME:-0}"

INT8_CALIB="${INT8_CALIB:-artifacts/kv_calib_kl_selected_v3_quick.json}"

export HF_HOME="${HF_HOME:-/root/autodl-tmp/hf_cache}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/root/autodl-tmp/hf_cache/hub}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-/root/autodl-tmp/hf_cache/datasets}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/root/autodl-tmp/triton_cache}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "[ERROR] Missing config snapshot: ${CONFIG_PATH}"
  exit 2
fi

if [[ -d "${BASE_DIR}" ]]; then
  existing_count="$(find "${BASE_DIR}" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${existing_count}" != "0" && "${ALLOW_RESUME}" != "1" ]]; then
    echo "[ERROR] BASE_DIR is non-empty: ${BASE_DIR}"
    echo "[ERROR] Refusing to mix runs. Re-run with ALLOW_RESUME=1 if you intend resume mode."
    exit 2
  fi
fi

mkdir -p "${BASE_DIR}"/{runs,logs,tables,plots,latex_tables,reports,gates,env}
echo "[INFO] RUN_TAG=${RUN_TAG}"
echo "[INFO] BASE_DIR=${BASE_DIR}"
echo "[INFO] CONFIG_PATH=${CONFIG_PATH}"
echo "[INFO] MAIN_SEEDS=${MAIN_SEEDS}"
echo "[INFO] THROUGHPUT_SEEDS=${THROUGHPUT_SEEDS}"

run_cmd() {
  echo "[CMD] $*"
  "$@"
}

run_exp() {
  # usage:
  # run_exp <tasks> <run_names> <failure_policy> <summary_json> [extra args...]
  local tasks="$1"
  local run_names="$2"
  local failure_policy="$3"
  local summary_json="$4"
  shift 4
  run_cmd "${PYTHON_BIN}" scripts/run_experiments.py \
    --config "${CONFIG_PATH}" \
    --tasks "${tasks}" \
    --run_tag "${RUN_TAG}" \
    --append \
    --run_names "${run_names}" \
    --failure_policy "${failure_policy}" \
    --max_retries 1 \
    --retry_backoff_sec 2 \
    --skip_completed_success \
    --summary_json "${summary_json}" \
    --out_dir "${BASE_DIR}/runs" \
    --logs_dir "${BASE_DIR}/logs" \
    "$@"
}

check_throughput_completeness() {
  local check_json="${BASE_DIR}/reports/completion_report.json"
  local output
  local status
  set +e
  output="$("${PYTHON_BIN}" scripts/check_run_completeness.py \
    --runs_dir "${BASE_DIR}/runs" \
    --logs_dir "${BASE_DIR}/logs" \
    --run_tag "${RUN_TAG}" \
    --tasks "profile_latency,profile_memory" \
    --seeds "${THROUGHPUT_SEEDS}" \
    --required_run_names "${THROUGHPUT_REQUIRED_RUNS}" \
    --stress_run_names "${THROUGHPUT_STRESS_RUNS}" \
    --out_json "${check_json}" 2>&1)"
  status=$?
  set -e
  echo "${output}"
  THROUGHPUT_CHECK_STATUS="${status}"
  THROUGHPUT_MISSING_REQUIRED="$(echo "${output}" | sed -n 's/^MISSING_REQUIRED=//p' | tail -n 1)"
  THROUGHPUT_MISSING_STRESS="$(echo "${output}" | sed -n 's/^MISSING_STRESS=//p' | tail -n 1)"
  THROUGHPUT_UNEXPECTED_FAILURES="$(echo "${output}" | sed -n 's/^UNEXPECTED_FAILURES=//p' | tail -n 1)"
}

echo "[INFO] Collect environment and freeze snapshot..."
run_cmd "${PYTHON_BIN}" scripts/collect_env.py
cp -f env/versions.txt "${BASE_DIR}/env/versions.txt"
cp -f env/requirements_freeze.txt "${BASE_DIR}/env/requirements_freeze.txt"
cp -f "${CONFIG_PATH}" "${BASE_DIR}/env/exp_matrix_snapshot.yaml"
sha256sum "${BASE_DIR}/env/exp_matrix_snapshot.yaml" > "${BASE_DIR}/env/exp_matrix_snapshot.sha256"
git rev-parse HEAD > "${BASE_DIR}/env/git_commit_full.txt"
git status --porcelain > "${BASE_DIR}/env/git_status_porcelain.txt"
git diff > "${BASE_DIR}/env/uncommitted_changes.patch" || true

echo "[INFO] Gates..."
run_cmd "${PYTHON_BIN}" scripts/smoke_test.py --save_output --model_revision "${MODEL_REVISION}" \
  > "${BASE_DIR}/gates/gate0_smoke_test.log" 2>&1
run_cmd "${PYTHON_BIN}" scripts/run_experiments.py --config "${CONFIG_PATH}" --dry_run \
  > "${BASE_DIR}/gates/gate1_dry_run.log" 2>&1
run_cmd "${PYTHON_BIN}" -m unittest tests/test_triton_kernel.py \
  > "${BASE_DIR}/gates/gate2_triton_unittest.log" 2>&1
run_cmd "${PYTHON_BIN}" -m pytest -q tests/test_run_experiments_resilience.py tests/test_check_run_completeness.py \
  > "${BASE_DIR}/gates/gate2_runner_resilience.log" 2>&1
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

CORE_RUNS="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,fp16_kv_long,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_baseline_long_torch,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int8_ours_long_static_v3_no_temp_adaptive_fused"
SHORT_NEEDLE_RUNS="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused"
LONG_NEEDLE_RUNS="fp16_kv_long,int8_baseline_long_torch,int8_ours_long_static_v3_no_temp_adaptive_fused"
PPL_RUNS="fp16_kv_curve_4k,int8_baseline_curve_4k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused"
THROUGHPUT_REQUIRED_RUNS="fp16_throughput_8k_b1,fp16_throughput_8k_b2,fp16_throughput_8k_b4,fp16_throughput_8k_b8,fp16_throughput_8k_b16,fp16_throughput_8k_b24,int8_baseline_throughput_8k_b1,int8_baseline_throughput_8k_b2,int8_baseline_throughput_8k_b4,int8_baseline_throughput_8k_b8,int8_baseline_throughput_8k_b16,int8_baseline_throughput_8k_b24,int8_ours_throughput_8k_b1,int8_ours_throughput_8k_b2,int8_ours_throughput_8k_b4,int8_ours_throughput_8k_b8,int8_ours_throughput_8k_b16,int8_ours_throughput_8k_b24"
THROUGHPUT_STRESS_RUNS="fp16_throughput_8k_b32,int8_baseline_throughput_8k_b32,int8_ours_throughput_8k_b32"

echo "[INFO] Core latency/memory..."
run_exp \
  "profile_latency,profile_memory" \
  "${CORE_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_core.json" \
  --seeds "${MAIN_SEEDS}" \
  --latency_warmup 2 \
  --latency_runs 5

echo "[INFO] Needle short-context..."
run_exp \
  "eval_needle" \
  "${SHORT_NEEDLE_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_needle_short.json" \
  --seeds "${MAIN_SEEDS}" \
  --needle_num_depths 20 \
  --needle_depth_batch 2 \
  --needle_max_new_tokens 64 \
  --needle_report_exact_match

echo "[INFO] Needle long-context..."
run_exp \
  "eval_needle" \
  "${LONG_NEEDLE_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_needle_long.json" \
  --seeds "${MAIN_SEEDS}" \
  --needle_num_depths 20 \
  --needle_depth_batch 1 \
  --needle_max_new_tokens 64 \
  --needle_report_exact_match

echo "[INFO] PPL (kv_cache + chunk)..."
run_exp \
  "eval_ppl" \
  "${PPL_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_ppl.json" \
  --seeds "${MAIN_SEEDS}" \
  --ppl_mode kv_cache \
  --ppl_max_length 1024 \
  --ppl_stride 512 \
  --ppl_chunk_size 128 \
  --ppl_max_samples 64

echo "[INFO] Throughput required matrix..."
run_exp \
  "profile_latency,profile_memory" \
  "${THROUGHPUT_REQUIRED_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_throughput_required.json" \
  --seeds "${THROUGHPUT_SEEDS}" \
  --latency_warmup 2 \
  --latency_runs 5

echo "[INFO] Throughput stress matrix (continue on OOM)..."
run_exp \
  "profile_latency,profile_memory" \
  "${THROUGHPUT_STRESS_RUNS}" \
  "continue_on_oom" \
  "${BASE_DIR}/reports/run_experiments_throughput_stress.json" \
  --seeds "${THROUGHPUT_SEEDS}" \
  --latency_warmup 2 \
  --latency_runs 5

echo "[INFO] Throughput repair loop..."
for ((iter=1; iter<=MAX_REPAIR_ITER; iter++)); do
  echo "[INFO] Throughput completeness check iter=${iter}/${MAX_REPAIR_ITER}"
  check_throughput_completeness

  if [[ "${THROUGHPUT_UNEXPECTED_FAILURES}" != "" && "${THROUGHPUT_UNEXPECTED_FAILURES}" != "0" ]]; then
    echo "[ERROR] Unexpected throughput failures detected (non-OOM)."
    exit 2
  fi

  if [[ -z "${THROUGHPUT_MISSING_REQUIRED}" && -z "${THROUGHPUT_MISSING_STRESS}" ]]; then
    echo "[INFO] Throughput completeness achieved."
    break
  fi

  if [[ -n "${THROUGHPUT_MISSING_REQUIRED}" ]]; then
    echo "[INFO] Re-running missing required throughput runs: ${THROUGHPUT_MISSING_REQUIRED}"
    run_exp \
      "profile_latency,profile_memory" \
      "${THROUGHPUT_MISSING_REQUIRED}" \
      "abort" \
      "${BASE_DIR}/reports/run_experiments_throughput_required_repair_iter${iter}.json" \
      --seeds "${THROUGHPUT_SEEDS}" \
      --latency_warmup 2 \
      --latency_runs 5
  fi

  if [[ -n "${THROUGHPUT_MISSING_STRESS}" ]]; then
    echo "[INFO] Re-running missing stress throughput runs: ${THROUGHPUT_MISSING_STRESS}"
    run_exp \
      "profile_latency,profile_memory" \
      "${THROUGHPUT_MISSING_STRESS}" \
      "continue_on_oom" \
      "${BASE_DIR}/reports/run_experiments_throughput_stress_repair_iter${iter}.json" \
      --seeds "${THROUGHPUT_SEEDS}" \
      --latency_warmup 2 \
      --latency_runs 5
  fi

  if [[ "${iter}" -eq "${MAX_REPAIR_ITER}" ]]; then
    echo "[ERROR] Exhausted throughput repair iterations (MAX_REPAIR_ITER=${MAX_REPAIR_ITER})."
    exit 2
  fi
done

echo "[INFO] Aggregate and export..."
run_cmd "${PYTHON_BIN}" scripts/aggregate_results.py \
  --runs_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs" \
  --tables_dir "${BASE_DIR}/tables" \
  --plots_dir "${BASE_DIR}/plots" \
  --significance_min_pairs 5 \
  --significance_alpha 0.05 \
  --significance_ci_level 0.95 \
  --significance_bootstrap 10000 \
  --significance_permutations 20000 \
  --strict
run_cmd "${PYTHON_BIN}" scripts/export_tables_latex.py \
  --tables_dir "${BASE_DIR}/tables" \
  --out_dir "${BASE_DIR}/latex_tables"
run_cmd "${PYTHON_BIN}" scripts/generate_thesis_report.py \
  --tables_dir "${BASE_DIR}/tables" \
  --out_dir "${BASE_DIR}/reports" \
  --target_seq_len 32704 \
  --alpha 0.05 \
  --strict

echo "[INFO] Final completeness check (post-aggregation)..."
check_throughput_completeness

echo "[DONE] final journal v1 complete"
echo "[DONE] BASE_DIR=${BASE_DIR}"
