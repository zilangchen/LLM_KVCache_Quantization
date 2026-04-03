#!/usr/bin/env bash
set -euo pipefail

# Week5 pipeline:
# 1) Extend long-context benchmarks with LongBench + RULER.
# 2) Enforce high-coverage PPL token budget (>=1M tokens per setting by default).
# 3) Aggregate/report with strict data-quality gates.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/bin/python}"
CONFIG_PATH="${CONFIG_PATH:-configs/snapshots/exp_matrix_week5_external_validity_v1.yaml}"
MODEL_REVISION="${MODEL_REVISION:-989aa7980e4cf806f80c7fef2b1adb7bc71aa306}"

RUN_TAG="${RUN_TAG:-week5_external_validity_v1}"
BASE_DIR="${BASE_DIR:-${PROJECT_ROOT}/results/week5_external_validity_v1}"
SEEDS="${SEEDS:-1234,1235,1236,1237,1238}"

PPL_TARGET_TOKENS="${PPL_TARGET_TOKENS:-1000000}"
PPL_MAX_LENGTH="${PPL_MAX_LENGTH:-1024}"
PPL_STRIDE="${PPL_STRIDE:-512}"
PPL_CHUNK_SIZE="${PPL_CHUNK_SIZE:-128}"

LONGBENCH_SOURCE="${LONGBENCH_SOURCE:-hf}"  # hf | synthetic | jsonl
LONGBENCH_TASKS="${LONGBENCH_TASKS:-narrativeqa,dureader,hotpotqa,gov_report,vcsum,trec,lcc}"
LONGBENCH_MAX_SAMPLES="${LONGBENCH_MAX_SAMPLES:-32}"   # per task
LONGBENCH_MAX_NEW_TOKENS="${LONGBENCH_MAX_NEW_TOKENS:-64}"

RULER_NUM_CASES="${RULER_NUM_CASES:-24}"
RULER_NUM_KV_PAIRS="${RULER_NUM_KV_PAIRS:-256}"
RULER_DEPTH_RATIOS="${RULER_DEPTH_RATIOS:-0.1,0.3,0.5,0.7,0.9}"
RULER_MAX_NEW_TOKENS="${RULER_MAX_NEW_TOKENS:-32}"
RULER_TASKS="${RULER_TASKS:-s_niah,mk_niah,vt,cwe}"
RULER_MK_NUM_KEYS="${RULER_MK_NUM_KEYS:-4}"
RULER_VT_NUM_CHAINS="${RULER_VT_NUM_CHAINS:-1}"
RULER_VT_NUM_HOPS="${RULER_VT_NUM_HOPS:-4}"
RULER_CWE_FREQ="${RULER_CWE_FREQ:-30}"
RULER_CWE_NUM_WORDS="${RULER_CWE_NUM_WORDS:-10}"

export HF_HOME="${HF_HOME:-/root/autodl-tmp/hf_cache}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/root/autodl-tmp/hf_cache/hub}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-/root/autodl-tmp/hf_cache/datasets}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/root/autodl-tmp/triton_cache}"

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "[ERROR] Missing config snapshot: ${CONFIG_PATH}"
  exit 2
fi

mkdir -p "${BASE_DIR}"/{runs,logs,tables,plots,latex_tables,reports,gates,env}
echo "[INFO] RUN_TAG=${RUN_TAG}"
echo "[INFO] BASE_DIR=${BASE_DIR}"
echo "[INFO] CONFIG_PATH=${CONFIG_PATH}"

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

echo "[INFO] Collect environment snapshot..."
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
run_cmd "${PYTHON_BIN}" -m pytest -q tests/test_run_experiments_resilience.py tests/test_check_run_completeness.py tests/test_aggregate_results_stats.py \
  > "${BASE_DIR}/gates/gate2_resilience_and_stats.log" 2>&1

EXT_RUNS="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,fp16_kv_long,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_baseline_long_torch,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int8_ours_long_static_v3_no_temp_adaptive_fused"
PPL_RUNS="fp16_kv_curve_4k,int8_baseline_curve_4k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused"
NEEDLE_RUNS="fp16_kv_curve_8k,fp16_kv_curve_16k,fp16_kv_long,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_baseline_long_torch,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int8_ours_long_static_v3_no_temp_adaptive_fused"

echo "[INFO] PPL high-token run..."
run_exp \
  "eval_ppl" \
  "${PPL_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_week5_ppl.json" \
  --seeds "${SEEDS}" \
  --ppl_mode kv_cache \
  --ppl_max_length "${PPL_MAX_LENGTH}" \
  --ppl_stride "${PPL_STRIDE}" \
  --ppl_chunk_size "${PPL_CHUNK_SIZE}" \
  --ppl_target_tokens "${PPL_TARGET_TOKENS}" \
  --ppl_max_samples 1

echo "[INFO] Needle long-context anchor..."
run_exp \
  "eval_needle" \
  "${NEEDLE_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_week5_needle.json" \
  --seeds "${SEEDS}" \
  --needle_num_depths 20 \
  --needle_depth_batch 2 \
  --needle_max_new_tokens 64 \
  --needle_report_exact_match

echo "[INFO] LongBench external-validity run..."
run_exp \
  "eval_longbench" \
  "${EXT_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_week5_longbench.json" \
  --seeds "${SEEDS}" \
  --longbench_source "${LONGBENCH_SOURCE}" \
  --longbench_tasks "${LONGBENCH_TASKS}" \
  --longbench_max_samples "${LONGBENCH_MAX_SAMPLES}" \
  --longbench_max_new_tokens "${LONGBENCH_MAX_NEW_TOKENS}" \
  --longbench_allow_synthetic_fallback

echo "[INFO] RULER external-validity run..."
run_exp \
  "eval_ruler" \
  "${EXT_RUNS}" \
  "abort" \
  "${BASE_DIR}/reports/run_experiments_week5_ruler.json" \
  --seeds "${SEEDS}" \
  --ruler_num_cases "${RULER_NUM_CASES}" \
  --ruler_num_kv_pairs "${RULER_NUM_KV_PAIRS}" \
  --ruler_depth_ratios "${RULER_DEPTH_RATIOS}" \
  --ruler_max_new_tokens "${RULER_MAX_NEW_TOKENS}" \
  --ruler_tasks "${RULER_TASKS}" \
  --ruler_mk_num_keys "${RULER_MK_NUM_KEYS}" \
  --ruler_vt_num_chains "${RULER_VT_NUM_CHAINS}" \
  --ruler_vt_num_hops "${RULER_VT_NUM_HOPS}" \
  --ruler_cwe_freq "${RULER_CWE_FREQ}" \
  --ruler_cwe_num_words "${RULER_CWE_NUM_WORDS}"

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

echo "[DONE] Week5 external-validity pipeline complete."
echo "[DONE] BASE_DIR=${BASE_DIR}"
