#!/bin/bash
# =============================================================================
# Phase 2.6 Backfill: Wave 4 (14B) auto-k only runner
# =============================================================================
# 仅补跑 Wave 4 缺失的 3 个 auto-k policies：
#   bakv_auto_cov70_max / bakv_auto_cov80_max / bakv_auto_cov90_max
#
# 用法：
#   CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_backfill_wave4_autok.sh narrativeqa
#   CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_backfill_wave4_autok.sh hotpotqa
#   CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_backfill_wave4_autok.sh gov_report
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/phase2_gate_lib.sh"

TASK="${1:-}"
case "$TASK" in
    narrativeqa|hotpotqa|gov_report) ;;
    *)
        echo "ERROR: task 必须是 narrativeqa / hotpotqa / gov_report" >&2
        exit 2
        ;;
esac

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT

cd /root/LLM_KVCache_Quantization

MODEL="/root/autodl-tmp/modelscope_cache/qwen/Qwen2.5-14B-Instruct"
N_SAMPLES=50
SEED=1234
JSONL_DIR="/root/autodl-tmp/longbench_data/data"
OUT_DIR="results/phase2_c3_qwen14b"
POLICY_DIR="artifacts/allocator/sweep_14b"
mkdir -p "$OUT_DIR"

POLICIES=(
    "bakv_auto_cov70_max"
    "bakv_auto_cov80_max"
    "bakv_auto_cov90_max"
)

phase2_backfill_verify_wave4_task() {
    local out_dir="$1"
    local task="$2"
    shift 2
    python3 - "$out_dir" "$task" "$@" <<'PY'
import csv
import sys
from pathlib import Path

out_dir = Path(sys.argv[1])
task = sys.argv[2]
expected = sys.argv[3:]

def collect_logged_csvs(prefix: str):
    selected = []
    seen = set()
    for run_name in expected:
        log_path = out_dir / f"{run_name}.log"
        if not log_path.exists():
            continue
        text = log_path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if "Saved to " not in line:
                continue
            raw_path = line.split("Saved to ", 1)[1].strip()
            name = Path(raw_path).name
            if not name.startswith(prefix):
                continue
            candidate = out_dir / name
            if candidate.exists() and candidate not in seen:
                seen.add(candidate)
                selected.append(candidate)
    return selected


profiles = {}
for path in collect_logged_csvs("profile_longbench_int4_mixed_kv_"):
    with path.open() as fh:
        for row in csv.DictReader(fh):
            run_name = row.get("run_name", "")
            if run_name in expected:
                profiles.setdefault(run_name, set()).add(row.get("run_id", ""))

task_hits = {run_name: 0 for run_name in expected}
for path in collect_logged_csvs("longbench_task_summary_int4_mixed_kv_"):
    with path.open() as fh:
        for row in csv.DictReader(fh):
            if row.get("task_name") != task:
                continue
            run_id = row.get("run_id", "")
            for run_name, run_ids in profiles.items():
                if run_id in run_ids:
                    task_hits[run_name] += 1

missing_profiles = [run_name for run_name in expected if not profiles.get(run_name)]
missing_tasks = [run_name for run_name in expected if task_hits.get(run_name, 0) == 0]

print(f"=== Wave 4 backfill task {task} 精确校验 ===")
print(f"  expected runs:      {len(expected)}")
print(f"  profile rows found: {sum(1 for run_name in expected if profiles.get(run_name))}")
print(f"  task rows found:    {sum(1 for run_name in expected if task_hits.get(run_name, 0) > 0)}")
if missing_profiles:
    print("  missing profiles:   " + ", ".join(missing_profiles))
if missing_tasks:
    print("  missing task rows:  " + ", ".join(missing_tasks))

if missing_profiles or missing_tasks:
    raise SystemExit(3)
PY
}

echo "=== Wave 4 auto-k backfill task=$TASK @ $(date) ==="

RUN_NAMES=()
for POLICY in "${POLICIES[@]}"; do
    RN="phase2c3_14b_int4mixedkv_${POLICY}_${TASK}_n${N_SAMPLES}"
    LOG="$OUT_DIR/${RN}.log"
    POLICY_JSON="$POLICY_DIR/${POLICY}.json"
    RUN_NAMES+=("$RN")

    phase2_require_file "$POLICY_JSON" "policy"

    echo "--- [$RN] @ $(date +%H:%M:%S) ---"
    if python3 scripts/eval_longbench.py \
        --model_id "$MODEL" \
        --kv_mode int4_mixed_kv \
        --policy_json "$POLICY_JSON" \
        --longbench_source jsonl \
        --longbench_dataset_path "$JSONL_DIR" \
        --longbench_tasks "$TASK" \
        --longbench_max_samples $N_SAMPLES \
        --seed $SEED \
        --out_dir "$OUT_DIR" \
        --run_name "$RN" \
        > "$LOG" 2>&1; then
        echo "[$RN] DONE @ $(date +%H:%M:%S)"
    else
        phase2_fail_from_log "$RN" "$LOG"
    fi
done

traceback_cnt=0
head_mismatch_cnt=0
for RUN_NAME in "${RUN_NAMES[@]}"; do
    LOG="$OUT_DIR/${RUN_NAME}.log"
    grep -q -E 'Traceback|RuntimeError' "$LOG" 2>/dev/null && traceback_cnt=$((traceback_cnt + 1)) || true
    grep -q 'calibration vs model heads mismatch' "$LOG" 2>/dev/null && head_mismatch_cnt=$((head_mismatch_cnt + 1)) || true
done

echo "=== Wave 4 auto-k backfill task $TASK 日志校验 ==="
echo "  Traceback/RT error: $traceback_cnt (expected 0)"
echo "  Head mismatch:      $head_mismatch_cnt (expected 0)"
if [ "$traceback_cnt" -ne 0 ] || [ "$head_mismatch_cnt" -ne 0 ]; then
    echo "[Wave 4 auto-k backfill task $TASK] GATE FAIL" >&2
    exit 3
fi

phase2_backfill_verify_wave4_task "$OUT_DIR" "$TASK" "${RUN_NAMES[@]}"
echo "[Wave 4 auto-k backfill task $TASK] GATE PASS"
