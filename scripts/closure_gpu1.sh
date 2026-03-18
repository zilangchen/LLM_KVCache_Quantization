#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Closure Pack — GPU 1 Task Chain
# Tasks: A1(7B LB) → A1(Mistral LB) → A2(7B RULER) → A2(Mistral RULER) → A4(8B attn KL)
# FIX: model-specific run_tags to avoid run_id collisions
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

export CUDA_VISIBLE_DEVICES=1
export HF_HOME=/root/autodl-tmp/hf_cache
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

PYTHON=/root/miniconda3/bin/python3
PROJ=/root/LLM_KVCache_Quantization
cd "$PROJ"

SEEDS="1234,1235,1236,1237,1238"
POST_OUT="results/emnlp_postfix_v2/runs"

log() { echo "[GPU1 $(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== Closure Pack GPU 1 Starting ==="
log "Tasks: A1(7B LB) → A1(Mistral LB) → A2(7B RULER) → A2(Mistral RULER) → A4(8B KL)"

# ─── A1: 7B MixedKV LongBench (5 seeds) ──────────────────────────────
log "A1: 7B MixedKV LongBench starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_7b_v1.yaml \
  --tasks eval_longbench \
  --run_names mixed_kv_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_7b \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --longbench_source synthetic \
  --longbench_max_samples 32 \
  --longbench_max_new_tokens 64
log "A1: 7B MixedKV LongBench DONE ✓"

# ─── A1: Mistral-7B LongBench (3 methods × 5 seeds) ──────────────────
# Mistral needs fp16 + kivi baselines in addition to mixed_kv (no Legacy data)
log "A1: Mistral-7B LongBench starting (3 methods: mixed_kv + fp16 + kivi)..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_mistral7b_v1.yaml \
  --tasks eval_longbench \
  --run_names mixed_kv_long,fp16_matched_long,kivi_int4_matched_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_mistral \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --longbench_source synthetic \
  --longbench_max_samples 32 \
  --longbench_max_new_tokens 64
log "A1: Mistral-7B LongBench DONE ✓"

# ─── A2: 7B MixedKV RULER (5 seeds) ──────────────────────────────────
log "A2: 7B MixedKV RULER starting..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_7b_v1.yaml \
  --tasks eval_ruler \
  --run_names mixed_kv_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_7b \
  --append \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --ruler_num_cases 64
log "A2: 7B MixedKV RULER DONE ✓"

# ─── A2: Mistral-7B RULER (3 methods × 5 seeds) ─────────────────────
log "A2: Mistral-7B RULER starting (3 methods: mixed_kv + fp16 + kivi)..."
$PYTHON scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_mixed_kv_mistral7b_v1.yaml \
  --tasks eval_ruler \
  --run_names mixed_kv_long,fp16_matched_long,kivi_int4_matched_long \
  --seeds $SEEDS \
  --out_dir "$POST_OUT" \
  --run_tag closure_mistral \
  --append \
  --skip_completed_success \
  --subprocess_timeout 7200 \
  --ruler_num_cases 64
log "A2: Mistral-7B RULER DONE ✓"

# ─── A4: 8B Attention KL Collection ──────────────────────────────────
# Missing: LLaMA-3.1-8B-Instruct attention KL data (1.5B + 7B already exist)
log "A4: 8B Attention KL collection starting..."
$PYTHON scripts/collect_attention_kl.py \
  --model_id meta-llama/Llama-3.1-8B-Instruct \
  --kv_mode int4_mixed_kv \
  --k_bits 8 \
  --v_bits 4 \
  --seq_len 4096 \
  --seed 1234 \
  --num_samples 16 \
  --out_dir results/attention_kl
log "A4: 8B Attention KL collection DONE ✓"

log "=== GPU 1 Closure Pack COMPLETE ==="
echo "Finished at $(date '+%Y-%m-%d %H:%M:%S')"
