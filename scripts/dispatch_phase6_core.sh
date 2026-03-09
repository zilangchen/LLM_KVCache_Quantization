#!/bin/bash
# Phase 6 Core Profiling: profile_latency + profile_memory at 4K/8K/16K/32K
# Fills the gap: Phase 5v2 only had 8K throughput profiling, not multi-context curves.
#
# Usage:
#   bash scripts/dispatch_phase6_core.sh <FREEZE_DIR> <model>
#
#   FREEZE_DIR:  frozen copy path (with .git, created by upstream)
#   model:       1p5b | 7b | 8b
#
# Expected output: 24 configs × 8 seeds = 192 run dirs per model
# Each dir contains profile_latency_*.csv + profile_memory_*.csv
#
# Run names: 6 non-KIVI methods × 3 curve seq_lens + 6 non-KIVI long configs
# KIVI excluded per NOTE-1: no claim requires KIVI latency/memory data.

set -euo pipefail

# ── Arguments ──────────────────────────────────────────────────────────
FREEZE="${1:?Usage: dispatch_phase6_core.sh <FREEZE_DIR> <model>}"
MODEL="${2:?model: 1p5b | 7b | 8b}"

PYTHON="${PYTHON:-/root/miniconda3/bin/python}"
SRC="/root/LLM_KVCache_Quantization"
OUT_DIR="$SRC/results/phase6/runs"
LOGS_DIR="$SRC/results/phase6/logs"
SEEDS="1234,1235,1236,1237,1238,1239,1240,1241"

# ── Config files ───────────────────────────────────────────────────────
declare -A CONFIG_FILES=(
    ["1p5b"]="configs/exp_matrix.yaml"
    ["7b"]="configs/snapshots/exp_matrix_qwen25_7b_v1.yaml"
    ["8b"]="configs/snapshots/exp_matrix_llama31_8b_v1.yaml"
)

CONFIG="${CONFIG_FILES[$MODEL]:?Unknown model: $MODEL. Expected: 1p5b|7b|8b}"

# ── Curve run names (common across all models) ────────────────────────
# 6 non-KIVI methods × 3 seq_lens (4K/8K/16K) = 18 curves
CURVES="fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k"
CURVES="$CURVES,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k"
CURVES="$CURVES,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused"
CURVES="$CURVES,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused"
CURVES="$CURVES,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused"
CURVES="$CURVES,int4_baseline_curve_4k,int4_baseline_curve_8k,int4_baseline_curve_16k"
CURVES="$CURVES,int4_fused_curve_4k,int4_fused_curve_8k,int4_fused_curve_16k"
CURVES="$CURVES,int4_ours_curve_4k,int4_ours_curve_8k,int4_ours_curve_16k"

# ── Long run names (model-specific naming) ────────────────────────────
# 6 non-KIVI methods at 32K = 6 longs
case "$MODEL" in
    1p5b)
        # 1.5B uses distinct naming: int8_baseline_long_torch, int8_ours_long_static_v3_*
        LONGS="fp16_kv_long,int8_baseline_long_torch"
        LONGS="$LONGS,int8_ours_long_static_v3_no_temp_adaptive_fused"
        LONGS="$LONGS,int4_baseline_long,int4_fused_long,int4_ours_long"
        TAG="phase6_core_1p5b"
        ;;
    7b)
        LONGS="fp16_kv_long,int8_baseline_long,int8_ours_long"
        LONGS="$LONGS,int4_baseline_long,int4_fused_long,int4_ours_long"
        TAG="phase6_core_7b"
        ;;
    8b)
        LONGS="fp16_kv_long,int8_baseline_long,int8_ours_long"
        LONGS="$LONGS,int4_baseline_long,int4_fused_long,int4_ours_long"
        TAG="phase6_core_8b"
        ;;
    *)
        echo "ERROR: Unknown model '$MODEL'. Expected: 1p5b|7b|8b"
        exit 1
        ;;
esac

RUN_NAMES="$CURVES,$LONGS"

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

# Compute code fingerprint
CODE_FP=$(cd "$FREEZE" && find scripts/ src/ configs/ -name '*.py' -o -name '*.yaml' \
    | sort | xargs md5sum | md5sum | cut -d' ' -f1)
echo "Frozen copy fingerprint: $CODE_FP"

# Verify git commit
FREEZE_COMMIT=$(cd "$FREEZE" && git rev-parse HEAD)
if [ "$FREEZE_COMMIT" = "unknown" ] || [ -z "$FREEZE_COMMIT" ]; then
    echo "FATAL: Frozen copy git commit is unknown/empty"
    exit 1
fi
echo "Frozen copy commit: $FREEZE_COMMIT"

# ── Ensure output dirs exist ──────────────────────────────────────────
mkdir -p "$OUT_DIR" "$LOGS_DIR"

# Count expected configs
IFS=',' read -ra NAMES <<< "$RUN_NAMES"
NUM_CONFIGS=${#NAMES[@]}
NUM_SEEDS=$(echo "$SEEDS" | tr ',' '\n' | wc -l)
EXPECTED_DIRS=$((NUM_CONFIGS * NUM_SEEDS))

echo ""
echo "=== Phase 6 Core Profiling: $MODEL ==="
echo "  Config:     $CONFIG"
echo "  Seeds:      $SEEDS ($NUM_SEEDS seeds)"
echo "  Configs:    $NUM_CONFIGS (18 curve + 6 long)"
echo "  Expected:   $EXPECTED_DIRS run dirs"
echo "  Tag:        $TAG"
echo "  Freeze:     $FREEZE"
echo "  Output:     $OUT_DIR"
echo "  Start:      $(date)"
echo ""

# ── Execute from frozen copy ──────────────────────────────────────────
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
    --failure_policy continue_on_oom

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

TOTAL_DIRS=$(find "$OUT_DIR" -maxdepth 1 -type d -name "*${TAG}*" | wc -l)
echo ""
echo "=== DONE: $MODEL $(date) ==="
echo "  Exit code:    $RUN_EXIT"
echo "  Expected dirs: $EXPECTED_DIRS"
echo "  Actual dirs:   $TOTAL_DIRS"

if [ "$TOTAL_DIRS" -ne "$EXPECTED_DIRS" ]; then
    echo "  WARNING: dir count mismatch (expected=$EXPECTED_DIRS, actual=$TOTAL_DIRS)"
fi

exit $RUN_EXIT
