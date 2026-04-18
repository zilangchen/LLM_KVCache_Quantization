#!/bin/bash
# =============================================================================
# Phase 2.6 A-scheme rerun orchestrator
# =============================================================================
# 默认顺序：
#   wave2 -> mistral_smoke -> wave1 -> wave3 -> wave4 -> wave5 -> wave7a -> wave7b -> wave6
#
# 特性：
#   - 上游 gate fail 即整链停止
#   - 支持 --from/--to 断点恢复
#   - 默认 3 GPU: 0,1,2
#   - 每阶段可触发 iteration append 与 sync hook
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

FROM_STAGE="wave2"
TO_STAGE="wave6"
GPU_CSV="${PHASE2_GPUS:-0,1,2}"
IFS=',' read -r -a GPU_IDS <<<"$GPU_CSV"

STAGES=(wave2 mistral_smoke wave1 wave3 wave4 wave5 wave7a wave7b wave6)
CORE_TASKS=(narrativeqa hotpotqa gov_report)
EXT_TASKS=(dureader vcsum trec lcc)
RUN_ROOT="artifacts/$(date +%F)/phase2_a_scheme_rerun"
mkdir -p "$RUN_ROOT"

usage() {
    cat <<EOF
Usage: bash scripts/phase2_a_scheme_rerun.sh [--from STAGE] [--to STAGE] [--gpus 0,1,2]

Stages:
  wave2
  mistral_smoke
  wave1
  wave3
  wave4
  wave5
  wave7a
  wave7b
  wave6
EOF
}

while (($# > 0)); do
    case "$1" in
        --from) FROM_STAGE="$2"; shift 2 ;;
        --to) TO_STAGE="$2"; shift 2 ;;
        --gpus) GPU_CSV="$2"; IFS=',' read -r -a GPU_IDS <<<"$GPU_CSV"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
    esac
done

stage_index() {
    local needle="$1"
    local i
    for i in "${!STAGES[@]}"; do
        if [ "${STAGES[$i]}" = "$needle" ]; then
            echo "$i"
            return 0
        fi
    done
    return 1
}

FROM_IDX="$(stage_index "$FROM_STAGE")" || { echo "Invalid --from stage: $FROM_STAGE" >&2; exit 2; }
TO_IDX="$(stage_index "$TO_STAGE")" || { echo "Invalid --to stage: $TO_STAGE" >&2; exit 2; }
if [ "$FROM_IDX" -gt "$TO_IDX" ]; then
    echo "--from must not be after --to" >&2
    exit 2
fi

stage_enabled() {
    local stage="$1"
    local idx
    idx="$(stage_index "$stage")" || return 1
    [ "$idx" -ge "$FROM_IDX" ] && [ "$idx" -le "$TO_IDX" ]
}

assert_clean_stage_dir() {
    local out_dir="$1"
    if [ "${PHASE2_ALLOW_DIRTY_OUTDIR:-0}" = "1" ]; then
        return 0
    fi
    if [ -d "$out_dir" ]; then
        shopt -s nullglob
        local existing=( "$out_dir"/longbench_task_summary_*.csv "$out_dir"/phase2*.log "$out_dir"/profile_longbench_*.csv )
        shopt -u nullglob
        if ((${#existing[@]} > 0)); then
            echo "FATAL: output dir already contains result/log artifacts: $out_dir" >&2
            echo "Set PHASE2_ALLOW_DIRTY_OUTDIR=1 only if you intentionally resume in-place." >&2
            exit 2
        fi
    fi
}

run_logged_stage() {
    local stage="$1"
    shift
    local log_path="$RUN_ROOT/${stage}.log"
    echo "=== [${stage}] START @ $(phase2_now) ===" | tee "$log_path"
    if "$@" 2>&1 | tee -a "$log_path"; then
        echo "=== [${stage}] PASS @ $(phase2_now) ===" | tee -a "$log_path"
    else
        echo "=== [${stage}] FAIL @ $(phase2_now) ===" | tee -a "$log_path"
        return 3
    fi
}

run_parallel_tasks() {
    local stage="$1"
    local script="$2"
    local out_dir="$3"
    shift 3
    local tasks=( "$@" )
    local task_idx=0
    local batch=1
    local -a wait_specs
    local gpu task log_path

    assert_clean_stage_dir "$out_dir"
    mkdir -p "$RUN_ROOT/${stage}"

    while [ "$task_idx" -lt "${#tasks[@]}" ]; do
        wait_specs=()
        for gpu in "${GPU_IDS[@]}"; do
            [ "$task_idx" -ge "${#tasks[@]}" ] && break
            task="${tasks[$task_idx]}"
            log_path="$RUN_ROOT/${stage}/${task}.log"
            echo "[${stage}] launch gpu=${gpu} task=${task} @ $(phase2_now)"
            CUDA_VISIBLE_DEVICES="$gpu" bash "$script" "$task" >"$log_path" 2>&1 &
            wait_specs+=( "$!:gpu${gpu}/${task}" )
            task_idx=$((task_idx + 1))
        done
        phase2_wait_pids "${stage}-batch${batch}" "${wait_specs[@]}"
        batch=$((batch + 1))
    done
}

run_parallel_tasks_with_best_k() {
    local stage="$1"
    local script="$2"
    local out_dir="$3"
    local best_k="$4"
    shift 4
    local tasks=( "$@" )
    local task_idx=0
    local batch=1
    local -a wait_specs
    local gpu task log_path

    assert_clean_stage_dir "$out_dir"
    mkdir -p "$RUN_ROOT/${stage}"

    while [ "$task_idx" -lt "${#tasks[@]}" ]; do
        wait_specs=()
        for gpu in "${GPU_IDS[@]}"; do
            [ "$task_idx" -ge "${#tasks[@]}" ] && break
            task="${tasks[$task_idx]}"
            log_path="$RUN_ROOT/${stage}/${task}.log"
            echo "[${stage}] launch gpu=${gpu} task=${task} best_k=${best_k} @ $(phase2_now)"
            CUDA_VISIBLE_DEVICES="$gpu" bash "$script" "$task" "$best_k" >"$log_path" 2>&1 &
            wait_specs+=( "$!:gpu${gpu}/${task}" )
            task_idx=$((task_idx + 1))
        done
        phase2_wait_pids "${stage}-batch${batch}" "${wait_specs[@]}"
        batch=$((batch + 1))
    done
}

resolve_wave1_best_k() {
    if [ -n "${PHASE2_8B_BEST_K:-}" ]; then
        echo "$PHASE2_8B_BEST_K"
        return 0
    fi
    phase2_pick_best_k_from_wave1 "results/phase2_c2b_llama8b_extended"
}

run_stage_and_record() {
    local stage="$1"
    local goal="$2"
    local out_dir="$3"
    shift 3
    run_logged_stage "$stage" "$@"
    phase2_append_iteration_stage \
        "Phase 2.6 ${stage} 自动执行完成" \
        "$goal" \
        "$stage" \
        "stage=${stage}, out_dir=${out_dir}" \
        "PASS (see $RUN_ROOT/${stage}.log)" \
        "继续按 A 方案顺序推进，若需同步可使用 PHASE2_SYNC_HOOK"
    phase2_run_sync_hook "$stage" "$out_dir"
}

echo "=== Phase 2.6 A-scheme rerun orchestrator @ $(phase2_now) ==="
echo "FROM=$FROM_STAGE TO=$TO_STAGE GPUS=${GPU_IDS[*]}"

if stage_enabled wave2; then
    assert_clean_stage_dir "results/phase2_trec_vcsum_sanity"
    run_stage_and_record \
        "wave2" \
        "Wave 2 sanity（fp16 + int8_ours × trec/vcsum）" \
        "results/phase2_trec_vcsum_sanity" \
        bash scripts/phase2_trec_vcsum_sanity.sh
fi

if stage_enabled mistral_smoke; then
    assert_clean_stage_dir "results/phase2_c4_mistral7b/smoke"
    run_stage_and_record \
        "mistral_smoke_calib" \
        "Mistral-7B INT8 calibration（smoke prerequisite）" \
        "artifacts/kv_calib_kl_mistral7b_int8.json" \
        bash scripts/phase2_calibrate_mistral7b.sh
    run_stage_and_record \
        "mistral_smoke" \
        "Mistral smoke（fp16 + int8_ours × 3 tasks）" \
        "results/phase2_c4_mistral7b/smoke" \
        bash scripts/phase2_c4_mistral7b_smoke.sh
fi

if stage_enabled wave1; then
    run_stage_and_record \
        "wave1_policy_gen" \
        "Wave 1 8B extended policy generation" \
        "artifacts/allocator/sweep_8b" \
        bash scripts/phase2_gen_sweep_policies_8b_extended.sh
    run_parallel_tasks "wave1" "scripts/phase2_c2b_llama8b_extended.sh" "results/phase2_c2b_llama8b_extended" "${CORE_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave1 自动执行完成" \
        "Wave 1 8B extended 3-task rerun" \
        "wave1 parallel tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_c2b_llama8b_extended" \
        "PASS (all task runners returned 0)" \
        "可用于后续 8B best-k 自动选择"
    phase2_run_sync_hook "wave1" "results/phase2_c2b_llama8b_extended"
fi

if stage_enabled wave3; then
    run_stage_and_record \
        "wave3_policy_gen" \
        "Wave 3 7B random multi-seed policy generation" \
        "artifacts/allocator/sweep_7b" \
        bash scripts/phase2_gen_random_seeds_7b.sh
    run_parallel_tasks "wave3" "scripts/phase2_7b_random_hardening.sh" "results/phase2_7b_random_hardening" "${CORE_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave3 自动执行完成" \
        "Wave 3 7B random hardening rerun" \
        "wave3 parallel tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_7b_random_hardening" \
        "PASS (all task runners returned 0)" \
        "后续可继续 Wave 4"
    phase2_run_sync_hook "wave3" "results/phase2_7b_random_hardening"
fi

if stage_enabled wave4; then
    run_stage_and_record \
        "wave4_calib" \
        "Wave 4 Qwen-14B INT8 calibration" \
        "artifacts/kv_calib_kl_qwen25_14b_int8.json" \
        bash scripts/phase2_calibrate_14b.sh
    run_stage_and_record \
        "wave4_policy_gen" \
        "Wave 4 14B policy generation" \
        "artifacts/allocator/sweep_14b" \
        bash scripts/phase2_gen_sweep_policies_14b.sh
    run_parallel_tasks "wave4" "scripts/phase2_c3_qwen14b.sh" "results/phase2_c3_qwen14b" "${CORE_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave4 自动执行完成" \
        "Wave 4 Qwen-14B rerun" \
        "wave4 parallel tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_c3_qwen14b" \
        "PASS (all task runners returned 0)" \
        "后续可继续 Wave 5 full"
    phase2_run_sync_hook "wave4" "results/phase2_c3_qwen14b"
fi

if stage_enabled wave5; then
    assert_clean_stage_dir "results/phase2_c4_mistral7b"
    run_stage_and_record \
        "wave5_policy_gen" \
        "Wave 5 Mistral policy generation" \
        "artifacts/allocator/sweep_mistral7b" \
        bash scripts/phase2_gen_sweep_policies_mistral7b.sh
    run_parallel_tasks "wave5" "scripts/phase2_c4_mistral7b_full.sh" "results/phase2_c4_mistral7b" "${CORE_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave5 自动执行完成" \
        "Wave 5 Mistral full rerun" \
        "wave5 parallel tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_c4_mistral7b" \
        "PASS (all task runners returned 0)" \
        "后续可继续 Wave 7a"
    phase2_run_sync_hook "wave5" "results/phase2_c4_mistral7b"
fi

if stage_enabled wave7a; then
    run_parallel_tasks "wave7a" "scripts/phase2_batch4_extend_tasks_7b.sh" "results/phase2_batch4_extend_tasks_7b" "${EXT_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave7a 自动执行完成" \
        "Wave 7a 7B extend tasks rerun" \
        "wave7a batched tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_batch4_extend_tasks_7b" \
        "PASS (all task runners returned 0)" \
        "后续可继续 Wave 7b"
    phase2_run_sync_hook "wave7a" "results/phase2_batch4_extend_tasks_7b"
fi

if stage_enabled wave7b; then
    BEST_K="$(resolve_wave1_best_k)"
    echo "[wave7b] resolved BEST_K=${BEST_K}"
    run_parallel_tasks_with_best_k "wave7b" "scripts/phase2_batch5_extend_tasks_8b.sh" "results/phase2_batch5_extend_tasks_8b" "$BEST_K" "${EXT_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave7b 自动执行完成" \
        "Wave 7b 8B extend tasks rerun (best_k=${BEST_K})" \
        "wave7b batched tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_batch5_extend_tasks_8b" \
        "PASS (all task runners returned 0)" \
        "后续可继续 Wave 6"
    phase2_run_sync_hook "wave7b" "results/phase2_batch5_extend_tasks_8b"
fi

if stage_enabled wave6; then
    run_stage_and_record \
        "wave6_calib" \
        "Wave 6 Qwen-3B INT8 calibration" \
        "artifacts/kv_calib_kl_qwen25_3b_int8.json" \
        bash scripts/phase2_calibrate_3b.sh
    run_stage_and_record \
        "wave6_policy_gen" \
        "Wave 6 3B policy generation" \
        "artifacts/allocator/sweep_3b" \
        bash scripts/phase2_gen_sweep_policies_3b.sh
    run_parallel_tasks "wave6" "scripts/phase2_c5_qwen3b.sh" "results/phase2_c5_qwen3b" "${CORE_TASKS[@]}"
    phase2_append_iteration_stage \
        "Phase 2.6 wave6 自动执行完成" \
        "Wave 6 Qwen-3B rerun" \
        "wave6 parallel tasks on GPUs ${GPU_IDS[*]}" \
        "out_dir=results/phase2_c5_qwen3b" \
        "PASS (all task runners returned 0)" \
        "A-scheme rerun chain completed"
    phase2_run_sync_hook "wave6" "results/phase2_c5_qwen3b"
fi

echo "=== Phase 2.6 A-scheme rerun completed @ $(phase2_now) ==="
