#!/bin/bash
# =============================================================================
# L2 Phase C (Prompt-adaptive) poll
# =============================================================================
# 阻塞直到 3 个 tmux session 全部结束:
#   l2c_1p5b, l2c_7b, l2c_8b
# 每个 session 串行跑 3 task × 3 variant = 9 quality runs; 总 27 runs.
#
# 用法:
#   bash scripts/phase2_l2c_poll.sh
#
# Pass criteria per (model, task):
#   quality_csvs=3 (one per variant) AND failed_rows=0
# =============================================================================
set -uo pipefail

cd /root/LLM_KVCache_Quantization 2>/dev/null || true

SESSIONS=(l2c_1p5b l2c_7b l2c_8b)
MODELS=(1p5b 7b 8b)
TASKS=(narrativeqa hotpotqa gov_report)
POLL_SECS="${POLL_SECS:-45}"

echo "[l2c poll] sessions=(${SESSIONS[*]}) interval=${POLL_SECS}s start=$(date '+%H:%M:%S')"

any_alive() {
    local s
    for s in "${SESSIONS[@]}"; do
        if tmux has-session -t "$s" 2>/dev/null; then
            return 0
        fi
    done
    return 1
}

while any_alive; do
    sleep "$POLL_SECS"
done

echo "[l2c poll] all sessions ended @ $(date '+%H:%M:%S')"
echo

echo "=== per-model log tails (last 20) ==="
for m in "${MODELS[@]}"; do
    echo "--- $m ---"
    if [ -f "/tmp/l2c_${m}.log" ]; then
        tail -20 "/tmp/l2c_${m}.log"
    else
        echo "(no log)"
    fi
    echo
done

echo "=== per-(model,task) pass criteria ==="
overall_pass=1
total_cells=0
pass_cells=0
for m in "${MODELS[@]}"; do
    for t in "${TASKS[@]}"; do
        total_cells=$((total_cells + 1))
        D="results/l2_prompt_adaptive/$m/$t"
        if [ ! -d "$D" ]; then
            echo "$m/$t: DIR_MISSING"
            overall_pass=0
            continue
        fi
        shopt -s nullglob
        csvs=( "$D"/longbench_task_summary_*.csv )
        shopt -u nullglob
        q="${#csvs[@]}"
        failed=0
        for f in "${csvs[@]}"; do
            c=$(awk -F, 'NR>1 && $10=="failed" {c++} END {print c+0}' "$f" 2>/dev/null)
            failed=$((failed + ${c:-0}))
        done
        pass=1
        [ "$q" -eq 3 ] || pass=0
        [ "$failed" -eq 0 ] || pass=0
        if [ "$pass" -eq 1 ]; then
            verdict=PASS
            pass_cells=$((pass_cells + 1))
        else
            verdict=FAIL
            overall_pass=0
        fi
        printf "%s/%s: variants=%d failed=%d %s\n" "$m" "$t" "$q" "$failed" "$verdict"
    done
done

echo
echo "=== summary ==="
echo "pass_cells=$pass_cells / total_cells=$total_cells"
if [ "$overall_pass" -eq 1 ] && [ "$total_cells" -gt 0 ]; then
    echo "[l2c poll] ALL CELLS PASS"
    exit 0
else
    echo "[l2c poll] NOT ALL CELLS PASS"
    exit 3
fi
