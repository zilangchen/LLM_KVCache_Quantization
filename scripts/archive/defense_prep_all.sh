#!/bin/bash
# ============================================================
# 答辩前实验补强：T2 重新校准 + T3 完整重跑
# 在远程 GPU 服务器上运行
# 预计总时间: ~30 小时（T2: 2.5h + T3: 27h）
# ============================================================
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

# Trap to restore .bak files on unexpected exit
cleanup() {
    echo "Restoring backup files..."
    for f in scripts/phase1_*.sh.bak; do
        [ -f "$f" ] && mv "$f" "${f%.bak}" && echo "  Restored ${f%.bak}"
    done
}
trap cleanup EXIT ERR INT TERM

mkdir -p logs

echo "============================================"
echo "  答辩前实验补强 - 开始"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# ============================================================
# T2: 重新校准（使用修复后的 Q 预处理）
# 预计: ~2.5 小时
# ============================================================
echo ""
echo "========== T2: 重新校准 =========="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"

# --- 1.5B (~15-20 min) ---
echo ">>> T2: 校准 1.5B"
python3 scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --role_aware_axes \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --samples 128 --seq_len 512 --seed 1234 \
  --calib_out artifacts/kv_calib_rolealign_1p5b_v2.json \
  2>&1 | tee logs/recalib_1p5b.log
echo ">>> 1.5B 校准完成: $(date '+%Y-%m-%d %H:%M:%S')"

# --- 7B (~40-60 min) ---
echo ">>> T2: 校准 7B"
python3 scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-7B-Instruct \
  --role_aware_axes \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --samples 128 --seq_len 512 --seed 1234 \
  --calib_out artifacts/kv_calib_rolealign_7b_v2.json \
  2>&1 | tee logs/recalib_7b.log
echo ">>> 7B 校准完成: $(date '+%Y-%m-%d %H:%M:%S')"

# --- 8B (~50-70 min) ---
echo ">>> T2: 校准 8B"
python3 scripts/calibrate_behavior.py \
  --model_id /root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct \
  --role_aware_axes \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --samples 128 --seq_len 512 --seed 1234 \
  --calib_out artifacts/kv_calib_rolealign_8b_v2.json \
  2>&1 | tee logs/recalib_8b.log
echo ">>> 8B 校准完成: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "========== T2 完成 =========="
echo "校准产物:"
ls -la artifacts/kv_calib_rolealign_*_v2.json
echo ""

# ============================================================
# T3: 完整重跑（RULER + PPL + Profiling）
# phase1 脚本已参数化（F1 修复），直接传参调用，无需 sed 替换
# 预计: ~12.5 小时（3 卡并行，受限于最慢的 8B）
# ============================================================
echo ""
echo "========== T3: 完整重跑（3 卡并行） =========="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 校准产物路径（T2 生成的 v2 产物）
CALIB_1P5B="artifacts/kv_calib_rolealign_1p5b_v2.json"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v2.json"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v2.json"
T3_RD="results/emnlp_rolealign_v3"

# 3 卡并行：每卡一个模型
# Codex P1 fix: capture the *script* exit code, not tee's.
# Use subshell + exit-code files so `wait` sees the real status.
echo ">>> T3: 启动 3 卡并行（1.5B@GPU0, 7B@GPU1, 8B@GPU2）"

( bash scripts/phase1_1p5b.sh 0 "$CALIB_1P5B" "$T3_RD" 2>&1 | tee logs/t3_1p5b.log; exit "${PIPESTATUS[0]}"; ) &
PID_1P5B=$!
( bash scripts/phase1_7b.sh   1 "$CALIB_7B"   "$T3_RD" 2>&1 | tee logs/t3_7b.log; exit "${PIPESTATUS[0]}"; ) &
PID_7B=$!
( bash scripts/phase1_8b.sh   2 "$CALIB_8B"   "$T3_RD" 2>&1 | tee logs/t3_8b.log; exit "${PIPESTATUS[0]}"; ) &
PID_8B=$!

echo ">>> PIDs: 1.5B=$PID_1P5B, 7B=$PID_7B, 8B=$PID_8B"
T3_FAIL=0
wait $PID_1P5B && echo ">>> 1.5B 完成" || { echo ">>> 1.5B 失败 (exit $?)"; T3_FAIL=1; }
wait $PID_7B   && echo ">>> 7B 完成"   || { echo ">>> 7B 失败 (exit $?)"; T3_FAIL=1; }
wait $PID_8B   && echo ">>> 8B 完成"   || { echo ">>> 8B 失败 (exit $?)"; T3_FAIL=1; }

if [ "$T3_FAIL" -ne 0 ]; then
  echo "FATAL: One or more T3 streams failed. Check logs/ for details." >&2
  exit 1
fi

# Normal completion — disable cleanup trap
trap - EXIT ERR INT TERM

# ============================================================
# 完成汇总
# ============================================================
echo ""
echo "============================================"
echo "  全部实验完成"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""
echo "结果目录: results/emnlp_rolealign_v3/"
echo "校准产物: artifacts/kv_calib_rolealign_*_v2.json"
echo ""
echo "下一步:"
echo "  1. rsync 结果回本地"
echo "  2. python scripts/aggregate_results.py --runs_dir results/emnlp_rolealign_v3/runs ..."
echo "  3. 更新论文表格和图表"
