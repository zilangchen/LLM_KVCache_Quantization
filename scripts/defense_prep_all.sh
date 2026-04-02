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
# T2 → T3 切换：更新 phase1 脚本的 CALIB 路径
# ============================================================
echo "========== 更新 CALIB 路径 =========="

# 备份原脚本
cp scripts/phase1_1p5b.sh scripts/phase1_1p5b.sh.bak
cp scripts/phase1_7b.sh scripts/phase1_7b.sh.bak
cp scripts/phase1_8b.sh scripts/phase1_8b.sh.bak

# 替换 CALIB 路径
sed -i 's|artifacts/kv_calib_rolealign_1p5b.json|artifacts/kv_calib_rolealign_1p5b_v2.json|' scripts/phase1_1p5b.sh
sed -i 's|artifacts/kv_calib_rolealign_7b.json|artifacts/kv_calib_rolealign_7b_v2.json|' scripts/phase1_7b.sh
sed -i 's|artifacts/kv_calib_rolealign_8b.json|artifacts/kv_calib_rolealign_8b_v2.json|' scripts/phase1_8b.sh

# 替换结果目录
sed -i 's|results/emnlp_rolealign_v2|results/emnlp_rolealign_v3|' scripts/phase1_1p5b.sh
sed -i 's|results/emnlp_rolealign_v2|results/emnlp_rolealign_v3|' scripts/phase1_7b.sh
sed -i 's|results/emnlp_rolealign_v2|results/emnlp_rolealign_v3|' scripts/phase1_8b.sh

echo "CALIB 路径已更新为 v2，结果目录已更新为 v3"

# ============================================================
# T3: 完整重跑（RULER + PPL + Profiling）
# 预计: ~27 小时
# ============================================================
echo ""
echo "========== T3: 完整重跑 =========="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"

# --- 1.5B (~5 小时) ---
echo ">>> T3: 1.5B 全量实验"
bash scripts/phase1_1p5b.sh 2>&1 | tee logs/t3_1p5b.log
echo ">>> 1.5B 完成: $(date '+%Y-%m-%d %H:%M:%S')"

# --- 7B (~9.5 小时) ---
echo ">>> T3: 7B 全量实验"
bash scripts/phase1_7b.sh 2>&1 | tee logs/t3_7b.log
echo ">>> 7B 完成: $(date '+%Y-%m-%d %H:%M:%S')"

# --- 8B (~12.5 小时) ---
echo ">>> T3: 8B 全量实验"
bash scripts/phase1_8b.sh 2>&1 | tee logs/t3_8b.log
echo ">>> 8B 完成: $(date '+%Y-%m-%d %H:%M:%S')"

# ============================================================
# 恢复原脚本（保留 v1 版本可追溯）
# ============================================================
mv scripts/phase1_1p5b.sh.bak scripts/phase1_1p5b.sh
mv scripts/phase1_7b.sh.bak scripts/phase1_7b.sh
mv scripts/phase1_8b.sh.bak scripts/phase1_8b.sh

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
