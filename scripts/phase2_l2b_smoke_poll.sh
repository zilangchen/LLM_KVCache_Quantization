#!/bin/bash
# =============================================================================
# L2 Phase B v4 smoke poll
# =============================================================================
# 阻塞直到指定 tmux session 结束，然后 dump 日志尾部 + 产物清单 +
# failed-row 计数 + smoke pass-criteria 校验。
#
# 用法:
#   bash scripts/phase2_l2b_smoke_poll.sh \
#       <session> <log_path> <out_dir>
#
# 例:
#   bash scripts/phase2_l2b_smoke_poll.sh \
#       l2b_smoke_v4 \
#       /tmp/l2b_smoke_v4.log \
#       results/l2_pareto_smoke_v4/7b/uniform_int4_k4v4
#
# Pass criteria (smoke 7b × uniform_int4_k4v4):
#   quality_csvs=3, latency_csv=1, memory_csv=1, ppl_csv=1, needle_csv=1,
#   failed_rows=0, quality_failed_marker=absent, tmux exit=0.
# =============================================================================
set -uo pipefail

SESSION="${1:-l2b_smoke_v4}"
LOG_PATH="${2:-/tmp/l2b_smoke_v4.log}"
OUT_DIR="${3:-results/l2_pareto_smoke_v4/7b/uniform_int4_k4v4}"
POLL_SECS="${POLL_SECS:-45}"

cd /root/LLM_KVCache_Quantization 2>/dev/null || true

echo "[poll] session=$SESSION log=$LOG_PATH out_dir=$OUT_DIR interval=${POLL_SECS}s start=$(date '+%H:%M:%S')"

while tmux has-session -t "$SESSION" 2>/dev/null; do
    sleep "$POLL_SECS"
done

echo "[poll] tmux session ended @ $(date '+%H:%M:%S')"
echo

echo "=== LOG TAIL (last 100 lines) ==="
if [ -f "$LOG_PATH" ]; then
    tail -100 "$LOG_PATH"
else
    echo "(log not found: $LOG_PATH)"
fi
echo

echo "=== OUT_DIR LISTING ==="
ls -la "$OUT_DIR" 2>&1 | tail -60
echo

echo "=== CSV FAILED-ROW COUNT ==="
shopt -s nullglob
csvs=( "$OUT_DIR"/longbench_task_summary_*.csv )
shopt -u nullglob
if [ "${#csvs[@]}" -eq 0 ]; then
    echo "NO_TASK_SUMMARY_CSV"
    failed_rows=0
else
    failed_rows=0
    for f in "${csvs[@]}"; do
        c=$(awk -F, 'NR>1 && $10=="failed" {c++} END {print c+0}' "$f")
        echo "$(basename "$f") failed_rows=$c"
        failed_rows=$((failed_rows + c))
    done
fi
echo

echo "=== QUALITY FAIL MARKER ==="
if [ -f "$OUT_DIR/.quality_failed" ]; then
    echo "MARKER_PRESENT"
    ls -la "$OUT_DIR/.quality_failed"
    marker_present=1
else
    echo "NO_MARKER"
    marker_present=0
fi
echo

echo "=== AUX CSV PRESENCE ==="
shopt -s nullglob
lat=( "$OUT_DIR"/profile_latency_*.csv )
mem=( "$OUT_DIR"/profile_memory_*.csv )
ppl=( "$OUT_DIR"/profile_ppl_*.csv )
needle=( "$OUT_DIR"/profile_needle_*.csv )
shopt -u nullglob
lat_n="${#lat[@]}"
mem_n="${#mem[@]}"
ppl_n="${#ppl[@]}"
needle_n="${#needle[@]}"
echo "latency_csv=$lat_n memory_csv=$mem_n ppl_csv=$ppl_n needle_csv=$needle_n"
echo

echo "=== SMOKE PASS CRITERIA ==="
quality_csvs="${#csvs[@]}"
pass=1
[ "$quality_csvs" -eq 3 ] || pass=0
[ "$failed_rows" -eq 0 ] || pass=0
[ "$marker_present" -eq 0 ] || pass=0
[ "$lat_n" -eq 1 ] || pass=0
[ "$mem_n" -eq 1 ] || pass=0
[ "$ppl_n" -eq 1 ] || pass=0
[ "$needle_n" -eq 1 ] || pass=0
echo "quality_csvs=$quality_csvs (expect 3)"
echo "failed_rows=$failed_rows (expect 0)"
echo "quality_failed_marker=$marker_present (expect 0)"
echo "latency_csv=$lat_n (expect 1)"
echo "memory_csv=$mem_n (expect 1)"
echo "ppl_csv=$ppl_n (expect 1)"
echo "needle_csv=$needle_n (expect 1)"
if [ "$pass" -eq 1 ]; then
    echo "[poll] SMOKE PASS"
    exit 0
else
    echo "[poll] SMOKE FAIL"
    exit 3
fi
