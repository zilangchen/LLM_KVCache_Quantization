#!/bin/bash
# Phase 5v2 吞吐评测调度脚本
# 从冻结副本执行 profile_latency + profile_memory，输出到主工作树 results/
#
# 用法:
#   bash scripts/dispatch_phase5v2_throughput.sh <FREEZE_DIR> <model> <seed_group> [stress]
#
#   FREEZE_DIR:  冻结副本路径 (含 .git, 由上游创建)
#   model:       1p5b | 7b | 8b
#   seed_group:  A (1234-1238) | B (1239-1241) | all (1234-1241)
#   stress:      可选，仅跑 b24/b32 stress 配置 (仅 1.5B)
#
# 示例:
#   bash scripts/dispatch_phase5v2_throughput.sh /root/LLM_freeze_20260308 1p5b A
#   bash scripts/dispatch_phase5v2_throughput.sh /root/LLM_freeze_20260308 7b B
#   bash scripts/dispatch_phase5v2_throughput.sh /root/LLM_freeze_20260308 1p5b all stress

set -euo pipefail

# ── Arguments ──────────────────────────────────────────────────────────
FREEZE="${1:?Usage: dispatch_phase5v2_throughput.sh <FREEZE_DIR> <model> <seed_group> [stress]}"
MODEL="${2:?Usage: dispatch_phase5v2_throughput.sh <FREEZE_DIR> <model> <seed_group> [stress]}"
SEED_GROUP="${3:?Usage: dispatch_phase5v2_throughput.sh <FREEZE_DIR> <model> <seed_group> [stress]}"
STRESS="${4:-}"

PYTHON="${PYTHON:-/root/miniconda3/bin/python}"
SRC="/root/LLM_KVCache_Quantization"
OUT_DIR="$SRC/results/phase5v2/runs"
LOGS_DIR="$SRC/results/phase5v2/logs"

# ── Config files ───────────────────────────────────────────────────────
declare -A CONFIG_FILES=(
    ["1p5b"]="configs/exp_matrix.yaml"
    ["7b"]="configs/snapshots/exp_matrix_qwen25_7b_v1.yaml"
    ["8b"]="configs/snapshots/exp_matrix_llama31_8b_v1.yaml"
)

CONFIG="${CONFIG_FILES[$MODEL]:?Unknown model: $MODEL. Expected: 1p5b|7b|8b}"

# ── Seed groups ────────────────────────────────────────────────────────
case "$SEED_GROUP" in
    A)   SEEDS="1234,1235,1236,1237,1238" ;;
    B)   SEEDS="1239,1240,1241" ;;
    all) SEEDS="1234,1235,1236,1237,1238,1239,1240,1241" ;;
    *)   echo "ERROR: Unknown seed_group '$SEED_GROUP'. Expected: A|B|all"; exit 1 ;;
esac

# ── Run names ──────────────────────────────────────────────────────────
# Required: 8 methods × 5 batch sizes (b1,b2,b4,b8,b16) = 40 configs
THROUGHPUT_REQUIRED="fp16_throughput_8k_b1,fp16_throughput_8k_b2,fp16_throughput_8k_b4,fp16_throughput_8k_b8,fp16_throughput_8k_b16,int8_baseline_throughput_8k_b1,int8_baseline_throughput_8k_b2,int8_baseline_throughput_8k_b4,int8_baseline_throughput_8k_b8,int8_baseline_throughput_8k_b16,int8_ours_throughput_8k_b1,int8_ours_throughput_8k_b2,int8_ours_throughput_8k_b4,int8_ours_throughput_8k_b8,int8_ours_throughput_8k_b16,int4_baseline_throughput_8k_b1,int4_baseline_throughput_8k_b2,int4_baseline_throughput_8k_b4,int4_baseline_throughput_8k_b8,int4_baseline_throughput_8k_b16,int4_fused_throughput_8k_b1,int4_fused_throughput_8k_b2,int4_fused_throughput_8k_b4,int4_fused_throughput_8k_b8,int4_fused_throughput_8k_b16,int4_ours_throughput_8k_b1,int4_ours_throughput_8k_b2,int4_ours_throughput_8k_b4,int4_ours_throughput_8k_b8,int4_ours_throughput_8k_b16,kivi_style_int8_throughput_8k_b1,kivi_style_int8_throughput_8k_b2,kivi_style_int8_throughput_8k_b4,kivi_style_int8_throughput_8k_b8,kivi_style_int8_throughput_8k_b16,kivi_style_int4_throughput_8k_b1,kivi_style_int4_throughput_8k_b2,kivi_style_int4_throughput_8k_b4,kivi_style_int4_throughput_8k_b8,kivi_style_int4_throughput_8k_b16"

# Stress: b24+b32, 4 methods, 1.5B only
THROUGHPUT_STRESS="int8_baseline_throughput_8k_b24,int8_baseline_throughput_8k_b32,int8_ours_throughput_8k_b24,int8_ours_throughput_8k_b32,int4_fused_throughput_8k_b24,int4_fused_throughput_8k_b32,int4_ours_throughput_8k_b24,int4_ours_throughput_8k_b32"

# ── Determine run_names and failure_policy ─────────────────────────────
if [ -n "$STRESS" ]; then
    if [ "$MODEL" != "1p5b" ]; then
        echo "ERROR: Stress mode only supported for 1p5b, got '$MODEL'"
        exit 1
    fi
    RUN_NAMES="$THROUGHPUT_STRESS"
    FAILURE_POLICY="continue_on_oom"
    TAG="phase5v2_tp_${MODEL}_stress"
    echo "=== STRESS MODE: ${MODEL} b24/b32, seeds=${SEEDS} ==="
else
    RUN_NAMES="$THROUGHPUT_REQUIRED"
    FAILURE_POLICY="abort"
    TAG="phase5v2_tp_${MODEL}"
    echo "=== REQUIRED MODE: ${MODEL} b1-b16, seeds=${SEEDS} ==="
fi

# ── Validate frozen copy ──────────────────────────────────────────────
if [ ! -d "$FREEZE" ]; then
    echo "FATAL: Frozen copy not found: $FREEZE"
    exit 1
fi

if [ ! -d "$FREEZE/.git" ]; then
    echo "FATAL: Frozen copy has no .git directory: $FREEZE"
    echo "  Run: cd $FREEZE && git init && git add -A && git commit -m 'frozen snapshot'"
    exit 1
fi

# Compute code fingerprint for integrity checks
CODE_FP=$(cd "$FREEZE" && find scripts/ src/ configs/ -name '*.py' -o -name '*.yaml' \
    | sort | xargs md5sum | md5sum | cut -d' ' -f1)
echo "Frozen copy fingerprint: $CODE_FP"

# Verify git commit is valid (not 'unknown')
FREEZE_COMMIT=$(cd "$FREEZE" && git rev-parse HEAD)
if [ "$FREEZE_COMMIT" = "unknown" ] || [ -z "$FREEZE_COMMIT" ]; then
    echo "FATAL: Frozen copy git commit is unknown/empty"
    exit 1
fi
echo "Frozen copy commit: $FREEZE_COMMIT"

# ── Ensure output dirs exist ──────────────────────────────────────────
mkdir -p "$OUT_DIR" "$LOGS_DIR"

# ── Execute from frozen copy ──────────────────────────────────────────
echo ""
echo "=== START: ${MODEL} ${SEED_GROUP} $(date) ==="
echo "  Config:  $CONFIG"
echo "  Seeds:   $SEEDS"
echo "  Tag:     $TAG"
echo "  Policy:  $FAILURE_POLICY"
echo "  Freeze:  $FREEZE"
echo ""

cd "$FREEZE"

$PYTHON scripts/run_experiments.py \
    --config "$CONFIG" \
    --tasks profile_latency,profile_memory \
    --run_names "$RUN_NAMES" \
    --seeds "$SEEDS" \
    --run_tag "$TAG" \
    --out_dir "$OUT_DIR" \
    --logs_dir "$LOGS_DIR" \
    --latency_warmup 2 \
    --latency_runs 3 \
    --append \
    --skip_completed_success \
    --subprocess_timeout 7200 \
    --failure_policy "$FAILURE_POLICY"

RUN_EXIT=$?

# ── Post-run fingerprint check ────────────────────────────────────────
STEP_FP=$(cd "$FREEZE" && find scripts/ src/ configs/ -name '*.py' -o -name '*.yaml' \
    | sort | xargs md5sum | md5sum | cut -d' ' -f1)

if [ "$STEP_FP" != "$CODE_FP" ]; then
    echo "FATAL: Frozen copy was modified during execution!"
    echo "  Before: $CODE_FP"
    echo "  After:  $STEP_FP"
    exit 1
fi
echo "Fingerprint OK: frozen copy unchanged"

# ── Summary ───────────────────────────────────────────────────────────
cd "$SRC"

# Count completed throughput runs
TOTAL_DIRS=$(ls -d "$OUT_DIR"/*throughput* 2>/dev/null | wc -l)
echo ""
echo "=== DONE: ${MODEL} ${SEED_GROUP} $(date) ==="
echo "  Exit code: $RUN_EXIT"
echo "  Total throughput run dirs: $TOTAL_DIRS"

exit $RUN_EXIT
