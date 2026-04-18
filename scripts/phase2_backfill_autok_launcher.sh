#!/bin/bash
# =============================================================================
# Phase 2.6 Backfill Launcher: Wave 1 / Wave 4 auto-k gap filling
# =============================================================================
# 默认只打印命令，不直接启动。
#
# 远端推荐用法：
#   bash scripts/phase2_backfill_autok_launcher.sh --wave wave1
#   bash scripts/phase2_backfill_autok_launcher.sh --wave wave1 --run-now
#   bash scripts/phase2_backfill_autok_launcher.sh --wave wave4 --run-now
#
# 说明：
# - `--wave all` 仅用于打印 wave1 + wave4 的完整承接命令
# - 为避免 6 lanes 抢 3 张 GPU，`--run-now` 不允许与 `--wave all` 同时使用
# =============================================================================
set -euo pipefail

WAVE="all"
RUN_NOW=0
SESSION_PREFIX="autok_backfill"
SKIP_POLICY_GEN=0

usage() {
    cat <<'EOF'
Usage:
  bash scripts/phase2_backfill_autok_launcher.sh [--wave wave1|wave4|all] [--run-now] [--skip-policy-gen] [--session-prefix PREFIX]

Options:
  --wave            选择启动范围，默认 all（仅打印）
  --run-now         实际启动 tmux sessions；默认只打印命令
  --skip-policy-gen 跳过 policy generation
  --session-prefix  自定义 tmux session 前缀（默认 autok_backfill）
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --wave)
            WAVE="${2:-}"
            shift 2
            ;;
        --run-now)
            RUN_NOW=1
            shift
            ;;
        --skip-policy-gen)
            SKIP_POLICY_GEN=1
            shift
            ;;
        --session-prefix)
            SESSION_PREFIX="${2:-}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: 未知参数 $1" >&2
            usage
            exit 2
            ;;
    esac
done

case "$WAVE" in
    wave1|wave4|all) ;;
    *)
        echo "ERROR: --wave 必须是 wave1 / wave4 / all" >&2
        exit 2
        ;;
esac

if [ "$RUN_NOW" -eq 1 ] && [ "$WAVE" = "all" ]; then
    echo "ERROR: --run-now 不能与 --wave all 一起使用；请先启动 wave1，再启动 wave4" >&2
    exit 2
fi

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

TASKS=(narrativeqa hotpotqa gov_report)
GPUS=(0 1 2)

wave_policy_gen() {
    local wave="$1"
    case "$wave" in
        wave1) echo "bash scripts/phase2_gen_sweep_policies_8b_extended.sh" ;;
        wave4) echo "bash scripts/phase2_gen_sweep_policies_14b.sh" ;;
    esac
}

wave_runner() {
    local wave="$1"
    case "$wave" in
        wave1) echo "scripts/phase2_backfill_wave1_autok.sh" ;;
        wave4) echo "scripts/phase2_backfill_wave4_autok.sh" ;;
    esac
}

print_wave_plan() {
    local wave="$1"
    local runner
    runner="$(wave_runner "$wave")"

    echo ""
    echo "=== ${wave} backfill plan ==="
    if [ "$SKIP_POLICY_GEN" -eq 0 ]; then
        echo "$(wave_policy_gen "$wave")"
    fi
    for idx in "${!TASKS[@]}"; do
        local task="${TASKS[$idx]}"
        local gpu="${GPUS[$idx]}"
        local session="${SESSION_PREFIX}_${wave}_${task}"
        echo "tmux new-session -d -s ${session} 'cd /root/LLM_KVCache_Quantization && CUDA_VISIBLE_DEVICES=${gpu} bash ${runner} ${task}'"
    done
}

launch_wave() {
    local wave="$1"
    local runner
    runner="$(wave_runner "$wave")"

    if [ "$SKIP_POLICY_GEN" -eq 0 ]; then
        echo "=== 生成 ${wave} 缺失 policy @ $(date) ==="
        bash -lc "$(wave_policy_gen "$wave")"
    fi

    echo "=== 启动 ${wave} backfill tmux lanes @ $(date) ==="
    for idx in "${!TASKS[@]}"; do
        local task="${TASKS[$idx]}"
        local gpu="${GPUS[$idx]}"
        local session="${SESSION_PREFIX}_${wave}_${task}"
        local cmd="cd /root/LLM_KVCache_Quantization && CUDA_VISIBLE_DEVICES=${gpu} bash ${runner} ${task}"

        if tmux has-session -t "$session" 2>/dev/null; then
            echo "ERROR: tmux session 已存在: $session" >&2
            exit 2
        fi

        echo "  launch ${session} (GPU ${gpu}, task=${task})"
        tmux new-session -d -s "$session" "$cmd"
    done
}

echo "=== Phase 2.6 auto-k backfill launcher @ $(date) ==="
echo "wave=$WAVE run_now=$RUN_NOW skip_policy_gen=$SKIP_POLICY_GEN session_prefix=$SESSION_PREFIX"

if [ "$RUN_NOW" -eq 0 ]; then
    echo "默认模式：只打印命令，不实际启动。"
    case "$WAVE" in
        all)
            print_wave_plan "wave1"
            print_wave_plan "wave4"
            ;;
        *)
            print_wave_plan "$WAVE"
            ;;
    esac
    exit 0
fi

launch_wave "$WAVE"
echo ""
echo "=== 已启动 ${WAVE} backfill ==="
echo "建议下一步："
echo "  tmux ls"
echo "  tmux capture-pane -pt ${SESSION_PREFIX}_${WAVE}_narrativeqa | tail -n 20"
