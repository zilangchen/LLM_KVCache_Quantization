#!/bin/bash
# Shared helpers for Phase 2.6 A-scheme gated reruns.

set -o pipefail

phase2_now() {
    date '+%Y-%m-%d %H:%M'
}

phase2_require_file() {
    local path="$1"
    local label="${2:-file}"
    if [ ! -f "$path" ]; then
        echo "FATAL: missing ${label}: $path" >&2
        return 2
    fi
}

phase2_require_dir() {
    local path="$1"
    local label="${2:-directory}"
    if [ ! -d "$path" ]; then
        echo "FATAL: missing ${label}: $path" >&2
        return 2
    fi
}

phase2_fail_from_log() {
    local run_name="$1"
    local log_path="$2"
    echo "[$run_name] FAILED, see $log_path" >&2
    if [ -f "$log_path" ]; then
        tail -20 "$log_path" >&2 || true
    fi
    return 3
}

phase2_collect_logged_csvs() {
    local out_dir="$1"
    local csv_glob="$2"
    shift 2

    python3 - "$out_dir" "$csv_glob" "$@" <<'PY'
import sys
from pathlib import Path

out_dir = Path(sys.argv[1])
csv_glob = sys.argv[2]
logs = [Path(item) for item in sys.argv[3:]]

available = {path.name: str(path) for path in sorted(out_dir.glob(csv_glob))}
seen = set()
for log_path in logs:
    try:
        text = log_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for line in text.splitlines():
        if "Saved to " not in line:
            continue
        raw_path = line.split("Saved to ", 1)[1].strip()
        csv_name = Path(raw_path).name
        matched = available.get(csv_name)
        if matched and matched not in seen:
            seen.add(matched)
            print(matched)
PY
}

phase2_gate_outputs() {
    local wave_name="$1"
    local out_dir="$2"
    local log_glob="$3"
    local csv_glob="$4"
    local expected_csv="$5"

    local -a logs csvs
    local traceback_cnt=0
    local head_mismatch_cnt=0
    local failed_metric_cnt=0
    local csv_cnt=0

    shopt -s nullglob
    logs=( "$out_dir"/$log_glob )
    shopt -u nullglob
    mapfile -t csvs < <(phase2_collect_logged_csvs "$out_dir" "$csv_glob" "${logs[@]}")

    csv_cnt="${#csvs[@]}"
    # pipefail-safe counters: avoid `grep -l ... | wc -l` (grep exit 1 on 0 match
    # abort script under `set -euo pipefail`). Use shell loop + `grep -q || true`.
    local f
    for f in "${logs[@]}"; do
        grep -q -E 'Traceback|RuntimeError' "$f" 2>/dev/null && traceback_cnt=$((traceback_cnt + 1)) || true
        grep -q 'calibration vs model heads mismatch' "$f" 2>/dev/null && head_mismatch_cnt=$((head_mismatch_cnt + 1)) || true
    done
    if ((${#csvs[@]} > 0)); then
        # awk always exits 0; no pipeline needed.
        failed_metric_cnt=$(awk -F, 'NR>1 && $10=="failed" {c++} END {print c+0}' "${csvs[@]}" 2>/dev/null || echo 0)
    fi

    echo "=== ${wave_name} 最终校验 ==="
    echo "  CSV count:          $csv_cnt (expected $expected_csv)"
    echo "  Traceback/RT error: $traceback_cnt (expected 0)"
    echo "  Head mismatch:      $head_mismatch_cnt (expected 0)"
    echo "  failed metric rows: $failed_metric_cnt (expected 0)"

    if [ "$csv_cnt" -ne "$expected_csv" ] || [ "$traceback_cnt" -ne 0 ] || [ "$head_mismatch_cnt" -ne 0 ] || [ "$failed_metric_cnt" -ne 0 ]; then
        echo "[${wave_name}] GATE FAIL" >&2
        return 3
    fi

    echo "[${wave_name}] GATE PASS"
}

phase2_gate_task_rows() {
    local wave_name="$1"
    local out_dir="$2"
    local log_glob="$3"
    local csv_glob="$4"
    local expected_rows="$5"
    local task_name="$6"
    local kv_mode_filter="${7:-}"

    local -a logs csvs
    local traceback_cnt=0
    local head_mismatch_cnt=0
    local failed_metric_cnt=0
    local row_cnt=0

    shopt -s nullglob
    logs=( "$out_dir"/$log_glob )
    shopt -u nullglob
    mapfile -t csvs < <(phase2_collect_logged_csvs "$out_dir" "$csv_glob" "${logs[@]}")

    # pipefail-safe counters: see phase2_gate_outputs comment.
    local f
    for f in "${logs[@]}"; do
        grep -q -E 'Traceback|RuntimeError' "$f" 2>/dev/null && traceback_cnt=$((traceback_cnt + 1)) || true
        grep -q 'calibration vs model heads mismatch' "$f" 2>/dev/null && head_mismatch_cnt=$((head_mismatch_cnt + 1)) || true
    done
    if ((${#csvs[@]} > 0)); then
        if [ -n "$kv_mode_filter" ]; then
            row_cnt=$(awk -F, -v task="$task_name" -v kv="$kv_mode_filter" 'NR>1 && $2==task && $3==kv {c++} END {print c+0}' "${csvs[@]}" 2>/dev/null)
            failed_metric_cnt=$(awk -F, -v task="$task_name" -v kv="$kv_mode_filter" 'NR>1 && $2==task && $3==kv && $10=="failed" {c++} END {print c+0}' "${csvs[@]}" 2>/dev/null)
        else
            row_cnt=$(awk -F, -v task="$task_name" 'NR>1 && $2==task {c++} END {print c+0}' "${csvs[@]}" 2>/dev/null)
            failed_metric_cnt=$(awk -F, -v task="$task_name" 'NR>1 && $2==task && $10=="failed" {c++} END {print c+0}' "${csvs[@]}" 2>/dev/null)
        fi
    fi

    echo "=== ${wave_name} 最终校验 ==="
    echo "  Task rows:          $row_cnt (expected $expected_rows)"
    echo "  Traceback/RT error: $traceback_cnt (expected 0)"
    echo "  Head mismatch:      $head_mismatch_cnt (expected 0)"
    echo "  failed metric rows: $failed_metric_cnt (expected 0)"

    if [ "$row_cnt" -ne "$expected_rows" ] || [ "$traceback_cnt" -ne 0 ] || [ "$head_mismatch_cnt" -ne 0 ] || [ "$failed_metric_cnt" -ne 0 ]; then
        echo "[${wave_name}] GATE FAIL" >&2
        return 3
    fi

    echo "[${wave_name}] GATE PASS"
}

phase2_append_iteration_stage() {
    local title="$1"
    local goal="$2"
    local commands="$3"
    local outputs="$4"
    local validation="$5"
    local followups="$6"
    local iteration_file="${PHASE2_ITERATION_FILE:-iteration.md}"

    if [ ! -f "$iteration_file" ]; then
        return 0
    fi

    cat >>"$iteration_file" <<EOF
### $(phase2_now) | ${title}
- Goal: ${goal}
- Changed files:
  - automation run (no source edits)
- Commands:
  - ${commands}
- Outputs:
  - ${outputs}
- Validation:
  - ${validation}
- Risks / follow-ups:
  - ${followups}
- Commit: 未提交

EOF
}

phase2_run_sync_hook() {
    local stage="$1"
    local out_dir="${2:-}"
    if [ -n "${PHASE2_SYNC_HOOK:-}" ]; then
        PHASE2_STAGE="$stage" PHASE2_OUT_DIR="$out_dir" bash -lc "$PHASE2_SYNC_HOOK"
    fi
}

phase2_wait_pids() {
    local stage="$1"
    shift
    local spec pid label rc=0
    for spec in "$@"; do
        pid="${spec%%:*}"
        label="${spec#*:}"
        if ! wait "$pid"; then
            echo "[${stage}] subtask failed: ${label}" >&2
            rc=3
        fi
    done
    return "$rc"
}

phase2_pick_best_k_from_wave1() {
    local out_dir="$1"
    python3 - "$out_dir" <<'PY'
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

out_dir = Path(sys.argv[1])
prof_re = re.compile(r"profile_longbench_(.+?)_([0-9T:\-\.]+)\.csv$")
task_re = re.compile(r"longbench_task_summary_(.+?)_([0-9T:\-\.]+)\.csv$")
run_re = re.compile(r"phase2c2b_8b_int4mixedkv_(bakv_k(?P<k>\d+))_(narrativeqa|hotpotqa|gov_report)_n\d+")

pairs = defaultdict(dict)
for p in sorted(out_dir.glob("*.csv")):
    m = prof_re.match(p.name)
    if m:
        pairs[(m.group(1), m.group(2))]["profile"] = p
        continue
    m = task_re.match(p.name)
    if m:
        pairs[(m.group(1), m.group(2))]["task"] = p

scores = defaultdict(list)
for key, files in pairs.items():
    if "profile" not in files or "task" not in files:
        continue
    with files["profile"].open() as fh:
        prof_rows = list(csv.DictReader(fh))
    with files["task"].open() as fh:
        task_rows = list(csv.DictReader(fh))
    if not prof_rows or not task_rows:
        continue
    rn = prof_rows[0].get("run_name", "")
    m = run_re.match(rn)
    if not m:
        continue
    k = int(m.group("k"))
    try:
        score = float(task_rows[0]["official_metric_value"])
    except Exception:
        continue
    scores[k].append(score)

if not scores:
    raise SystemExit("NO_WAVE1_BAKV_RESULTS")

best = max(sorted(scores), key=lambda k: (sum(scores[k]) / len(scores[k]), -k))
print(best)
PY
}
