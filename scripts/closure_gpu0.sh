#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Closure Pack — GPU 0 Task Chain
# Tasks: A1(1.5B/8B LongBench) → A3(C6 INT8 RULER) → A2(1.5B/8B RULER)
# FIX: model-specific run_tags to avoid run_id collisions
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

export CUDA_VISIBLE_DEVICES=0
export HF_HOME=/root/autodl-tmp/hf_cache
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

PYTHON=/root/miniconda3/bin/python3
PROJ=/root/LLM_KVCache_Quantization
cd "$PROJ"

SEEDS="1234,1235,1236,1237,1238"
POST_OUT="results/emnlp_postfix_v2/runs"
C6_OUT="results/emnlp_c6_fix/runs"

log() { echo "[GPU0 $(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== Closure Pack GPU 0 Starting ==="
log "Tasks: A1(1.5B LB) → A1(8B LB) → A3(C6 RULER) → A2(1.5B RULER) → A2(8B RULER)"

# ─── A1: 1.5B MixedKV LongBench (5 seeds) ────────────────────────────
log "A1: 1.5B MixedKV LongBench starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_1p5b_v1.yaml \
  --tasks eval_longbench \
  --run_names mixed_kv_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_1p5b \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --longbench_source synthetic \
  --longbench_max_samples 32 \
  --longbench_max_new_tokens 64
log "A1: 1.5B MixedKV LongBench DONE ✓"

# ─── A1: 8B (LLaMA-3.1-8B) MixedKV LongBench (5 seeds) ─────────────
log "A1: 8B MixedKV LongBench starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_8b_v1.yaml \
  --tasks eval_longbench \
  --run_names mixed_kv_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_8b \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --longbench_source synthetic \
  --longbench_max_samples 32 \
  --longbench_max_new_tokens 64
log "A1: 8B MixedKV LongBench DONE ✓"

# ─── A3: C6 INT8 RULER fix (1.5B, 3 methods, 5 seeds) ───────────────
# Re-run RULER with CWE-fixed eval_ruler.py to verify C6 claim
# NOTE: C6 is 1.5B-only, run_tag=c6fix_1p5b is unique (no collision)
log "A3: C6 INT8 RULER verification starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_ruler \
  --run_names fp16_kv_long,int8_ours_long_no_static_no_temp_fused,int8_baseline_long_torch \
  --seeds $SEEDS \
  --out_dir "$C6_OUT" \
  --run_tag c6fix_1p5b \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --ruler_num_cases 64
log "A3: C6 INT8 RULER verification DONE ✓"

# ─── A2: 1.5B MixedKV RULER (5 seeds) ────────────────────────────────
log "A2: 1.5B MixedKV RULER starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_1p5b_v1.yaml \
  --tasks eval_ruler \
  --run_names mixed_kv_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_1p5b \
  --append \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --ruler_num_cases 64
log "A2: 1.5B MixedKV RULER DONE ✓"

# ─── A2: 8B MixedKV RULER (5 seeds) ──────────────────────────────────
log "A2: 8B MixedKV RULER starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_8b_v1.yaml \
  --tasks eval_ruler \
  --run_names mixed_kv_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_8b \
  --append \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --ruler_num_cases 64
log "A2: 8B MixedKV RULER DONE ✓"

log "=== GPU 0 Closure Pack COMPLETE ==="
echo "Finished at $(date '+%Y-%m-%d %H:%M:%S')"
