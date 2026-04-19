#!/bin/bash
# =============================================================================
# L2 Phase B v4 全量 poll
# =============================================================================
# 阻塞直到 3 个 tmux session 全部结束:
#   l2b_v4_7b, l2b_v4_8b, l2b_v4_mistral7b
# 然后对每 model/policy 目录跑与 smoke poll 完全同构的 pass-criteria 判定,
# 打印每 policy 的 PASS/FAIL + overall verdict.
#
# 用法:
#   bash scripts/phase2_l2b_v4_poll.sh
#   # 非默认 RAW_BASE (极少用):
#   L2_PARETO_RAW_BASE=results/l2_pareto_alt/raw bash scripts/phase2_l2b_v4_poll.sh
#
# Pass criteria per policy:
#   quality_csvs=3, failed_rows=0, marker=0,
#   latency_csv=1, memory_csv=1, ppl_csv=1, needle_csv=1
# =============================================================================
set -uo pipefail

cd /root/LLM_KVCache_Quantization 2>/dev/null || true

RAW_BASE="${L2_PARETO_RAW_BASE:-results/l2_pareto/raw}"
POLL_SECS="${POLL_SECS:-60}"
SESSIONS=(l2b_v4_7b l2b_v4_8b l2b_v4_mistral7b)
MODELS=(7b 8b mistral7b)

echo "[v4 poll] raw_base=$RAW_BASE sessions=(${SESSIONS[*]}) interval=${POLL_SECS}s start=$(date '+%H:%M:%S')"

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

echo "[v4 poll] all sessions ended @ $(date '+%H:%M:%S')"
echo

echo "=== per-model log tails (last 30 lines) ==="
for m in "${MODELS[@]}"; do
    echo "--- $m ---"
    if [ -f "/tmp/l2b_v4_${m}.log" ]; then
        tail -30 "/tmp/l2b_v4_${m}.log"
    else
        echo "(no log: /tmp/l2b_v4_${m}.log)"
    fi
    echo
done

echo "=== per-policy pass criteria ==="
overall_pass=1
total_policies=0
pass_policies=0
for m in "${MODELS[@]}"; do
    MODEL_DIR="$RAW_BASE/$m"
    if [ ! -d "$MODEL_DIR" ]; then
        echo "[$m] OUT_DIR_MISSING ($MODEL_DIR)"
        overall_pass=0
        continue
    fi
    shopt -s nullglob
    pdirs=( "$MODEL_DIR"/*/ )
    shopt -u nullglob
    for pdir in "${pdirs[@]}"; do
        policy=$(basename "$pdir")
        case "$policy" in
            _quarantine*|quarantine_*) continue ;;
        esac
        total_policies=$((total_policies + 1))

        shopt -s nullglob
        qcsvs=( "$pdir"longbench_task_summary_*.csv )
        lat=( "$pdir"profile_latency_*.csv )
        mem=( "$pdir"profile_memory_*.csv )
        ppl=( "$pdir"profile_ppl_*.csv )
        needle=( "$pdir"profile_needle_*.csv )
        shopt -u nullglob

        failed=0
        for f in "${qcsvs[@]}"; do
            c=$(awk -F, 'NR>1 && $10=="failed" {c++} END {print c+0}' "$f" 2>/dev/null)
            failed=$((failed + ${c:-0}))
        done

        marker=0
        [ -f "${pdir}.quality_failed" ] && marker=1

        q="${#qcsvs[@]}"
        l="${#lat[@]}"
        me="${#mem[@]}"
        p="${#ppl[@]}"
        n="${#needle[@]}"

        pass=1
        [ "$q" -eq 3 ] || pass=0
        [ "$failed" -eq 0 ] || pass=0
        [ "$marker" -eq 0 ] || pass=0
        [ "$l" -eq 1 ] || pass=0
        [ "$me" -eq 1 ] || pass=0
        [ "$p" -eq 1 ] || pass=0
        [ "$n" -eq 1 ] || pass=0

        if [ "$pass" -eq 1 ]; then
            verdict=PASS
            pass_policies=$((pass_policies + 1))
        else
            verdict=FAIL
            overall_pass=0
        fi
        printf "%s/%s: q=%d fail=%d marker=%d lat=%d mem=%d ppl=%d needle=%d %s\n" \
            "$m" "$policy" "$q" "$failed" "$marker" "$l" "$me" "$p" "$n" "$verdict"
    done
done

echo
echo "=== summary ==="
echo "pass_policies=$pass_policies / total_policies=$total_policies"
if [ "$overall_pass" -eq 1 ] && [ "$total_policies" -gt 0 ]; then
    echo "[v4 poll] ALL POLICIES PASS"
    exit 0
else
    echo "[v4 poll] NOT ALL POLICIES PASS (see per-policy verdicts above)"
    exit 3
fi
