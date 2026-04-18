#!/bin/bash
# =============================================================================
# Phase 1 编号 5 闸门一键流水线
# =============================================================================
# 前置：编号 2-4 已完成（1.5B 4 modes + 7B 4 modes 的 CSV 齐全）
# 流程：
#   1. aggregate 7B 结果（results/phase1_official_7b → results/phase1_summary_7b.csv）
#   2. aggregate merged（已做）
#   3. 跑 gate check 含 --summary_7b 参数（判据 2 7B 一致性启用）
#   4. 产出最终 gate 决策
#
# 用法（远端执行）:
#   cd /root/LLM_KVCache_Quantization
#   bash scripts/phase1_gate5_run.sh
# =============================================================================
set -euo pipefail

# conda activate for tmux detached shells
if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate base
fi

cd /root/LLM_KVCache_Quantization

RUNS_7B="results/phase1_official_7b"
SUMMARY_1P5B="results/phase1_summary_merged.csv"
SUMMARY_7B="results/phase1_summary_7b.csv"
MAIN_TABLE_7B="docs/phase1_main_table_7b.md"

echo "=============================================="
echo "Phase 1 编号 5 闸门流水线"
echo "时间: $(date)"
echo "=============================================="

if [ ! -d "$RUNS_7B" ]; then
    echo "ERROR: 7B runs dir not found: $RUNS_7B（编号 4 未完成？）"
    exit 2
fi

if [ ! -f "$SUMMARY_1P5B" ]; then
    echo "ERROR: 1.5B merged summary not found: $SUMMARY_1P5B"
    exit 2
fi

echo ""
echo "=== Step 1: aggregate 7B results ==="
python3 scripts/aggregate_phase1.py \
    --runs_dir "$RUNS_7B" \
    --out_csv "$SUMMARY_7B" \
    --out_md "$MAIN_TABLE_7B" 2>&1 | tail -20

echo ""
echo "=== Step 2: phase1_gate5_check.py（含 7B 判据 2）==="
python3 scripts/phase1_gate5_check.py \
    --summary "$SUMMARY_1P5B" \
    --summary_7b "$SUMMARY_7B" 2>&1 | tee results/phase1_gate5_decision.log

GATE_EXIT=${PIPESTATUS[0]}

echo ""
echo "=============================================="
echo "Gate 判定 exit code: $GATE_EXIT"
echo "0 = PASS (可进编号 6), 1 = FAIL (跳编号 11 收口)"
echo "决策记录: results/phase1_gate5_decision.log"
echo "=============================================="

exit $GATE_EXIT
