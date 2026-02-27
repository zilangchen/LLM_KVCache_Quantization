#!/bin/bash
# Phase 5v2 接力调度脚本
# 在远端执行，负责启动指定模型和 seed 的质量评测
# 用法:
#   bash scripts/dispatch_phase5v2.sh 1p5b 1236        # 启动 1.5B s1236
#   bash scripts/dispatch_phase5v2.sh 7b 1237           # 启动 7B s1237
#   bash scripts/dispatch_phase5v2.sh 8b 1238           # 启动 8B s1238
#   bash scripts/dispatch_phase5v2.sh 7b fused_fix      # 启动 7B int4_fused 重跑
#   bash scripts/dispatch_phase5v2.sh quarantine_7b_s1236  # 隔离 7B s1236 int4_fused

set -euo pipefail
cd /root/LLM_KVCache_Quantization

MODEL="${1:?Usage: dispatch_phase5v2.sh <model> <seed|fused_fix>}"
SEED="${2:?Usage: dispatch_phase5v2.sh <model> <seed|fused_fix>}"

OUT_DIR="results/phase5v2/runs"
LOGS_DIR="results/phase5v2/logs"

# --- Config files ---
declare -A CONFIG_FILES=(
  ["1p5b"]="configs/exp_matrix.yaml"
  ["7b"]="configs/snapshots/exp_matrix_qwen25_7b_v1.yaml"
  ["8b"]="configs/snapshots/exp_matrix_llama31_8b_v1.yaml"
)

# --- Run names for full seed (all quality configs) ---
RUN_NAMES_1P5B="fp16_kv_torch,fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,int8_baseline_torch,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int4_baseline_curve_4k,int4_baseline_curve_8k,int4_baseline_curve_16k,int4_baseline_long,int4_fused_curve_4k,int4_fused_curve_8k,int4_fused_curve_16k,int4_fused_long,int8_ours_kl_temp_fused,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int8_ours_kl_no_temp_fused,int8_ours_percentile_temp_fused,fp16_kv_long,int8_ours_long_fused,int8_ours_long_static_v3_no_temp_adaptive_fused,int8_ours_long_static_v2_temp_fused,int8_ours_long_static_v2_no_temp_fused,int8_ours_long_static_v2_no_temp_adaptive_fused,int8_ours_long_static_v2_no_temp_adaptive_k_only_fused,int8_ours_long_no_static_no_temp_fused,int8_baseline_long_torch,int4_ours_curve_4k,int4_ours_curve_8k,int4_ours_curve_16k,int4_ours_long,kivi_style_int8_curve_4k,kivi_style_int8_curve_8k,kivi_style_int8_curve_16k,kivi_style_int4_curve_4k,kivi_style_int4_curve_8k,kivi_style_int4_curve_16k,kivi_style_int8_long,kivi_style_int4_long"

RUN_NAMES_7B8B="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int4_baseline_curve_4k,int4_baseline_curve_8k,int4_baseline_curve_16k,int4_fused_curve_4k,int4_fused_curve_8k,int4_fused_curve_16k,int4_ours_curve_4k,int4_ours_curve_8k,int4_ours_curve_16k,kivi_style_int8_curve_4k,kivi_style_int8_curve_8k,kivi_style_int8_curve_16k,kivi_style_int4_curve_4k,kivi_style_int4_curve_8k,kivi_style_int4_curve_16k,fp16_kv_long,int8_baseline_long,int8_ours_long,int4_baseline_long,int4_fused_long,int4_ours_long,kivi_style_int8_long,kivi_style_int4_long"

# --- int4_fused only (for rerun) ---
FUSED_NAMES="int4_fused_curve_4k,int4_fused_curve_8k,int4_fused_curve_16k,int4_fused_long"

# --- Quarantine helper ---
quarantine_int4_fused() {
    local model_tag="$1"
    local seed="$2"
    mkdir -p results/phase5v2/quarantine
    local count=0
    for d in $(ls -d results/phase5v2/runs/int4_fused_*_s${seed}_*${model_tag}* 2>/dev/null); do
        # Skip fused_fix dirs
        if echo "$d" | grep -q "fused_fix"; then continue; fi
        mv "$d" results/phase5v2/quarantine/
        echo "QUARANTINED: $(basename $d)"
        count=$((count + 1))
    done
    echo "Quarantined $count dirs for ${model_tag} s${seed}"
}

# --- Dispatch ---
case "$MODEL" in
    quarantine_7b_s1236)
        quarantine_int4_fused "7b" "1236"
        exit 0
        ;;
    quarantine_8b_s1236)
        quarantine_int4_fused "8b" "1236"
        exit 0
        ;;
    quarantine_*)
        # Generic: quarantine_<model>_s<seed>
        q_model="${MODEL#quarantine_}"
        quarantine_int4_fused "$q_model" "$SEED"
        exit 0
        ;;
esac

CONFIG="${CONFIG_FILES[$MODEL]:?Unknown model: $MODEL}"

if [ "$SEED" = "fused_fix" ]; then
    # int4_fused 重跑模式
    case "$MODEL" in
        1p5b)
            SEEDS="1234,1235"
            TAG="phase5v2_1p5b_fused_fix"
            ;;
        7b)
            SEEDS="1234,1235,1236"
            TAG="phase5v2_7b_fused_fix"
            ;;
        8b)
            SEEDS="1234,1235,1236"
            TAG="phase5v2_8b_fused_fix"
            ;;
    esac
    echo "=== ${MODEL} int4_fused RERUN (seeds: ${SEEDS}) === $(date)"
    python scripts/run_experiments.py \
        --config "$CONFIG" \
        --seeds "$SEEDS" \
        --tasks eval_ppl,eval_needle,eval_longbench,eval_ruler \
        --run_tag "$TAG" \
        --run_names "$FUSED_NAMES" \
        --out_dir "$OUT_DIR" \
        --logs_dir "$LOGS_DIR" \
        --failure_policy continue_all
else
    # 正常 seed 模式
    TAG="phase5v2_${MODEL}_s${SEED}"
    if [ "$MODEL" = "1p5b" ]; then
        RUN_NAMES="$RUN_NAMES_1P5B"
    else
        RUN_NAMES="$RUN_NAMES_7B8B"
    fi
    echo "=== ${MODEL} Quality Seed ${SEED} === $(date)"
    python scripts/run_experiments.py \
        --config "$CONFIG" \
        --seeds "$SEED" \
        --tasks eval_ppl,eval_needle,eval_longbench,eval_ruler \
        --run_tag "$TAG" \
        --run_names "$RUN_NAMES" \
        --out_dir "$OUT_DIR" \
        --logs_dir "$LOGS_DIR" \
        --skip_completed_success \
        --failure_policy continue_all
fi

echo "=== DONE: ${MODEL} ${SEED} === $(date)"
