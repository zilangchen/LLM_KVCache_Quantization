#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Closure Pack — Post-processing (run AFTER all GPU experiments complete)
# Steps: rsync results → aggregate → paper tables → 8B heatmap
# Run locally on dev machine
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

SSH_HOST="region-42.seetacloud.com"
SSH_PORT="31867"
SSH_USER="root"
REMOTE_DIR="/root/LLM_KVCache_Quantization"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

log() { echo "[POST $(date '+%H:%M:%S')] $*"; }

log "=== Closure Pack Post-processing Starting ==="

# ─── Step 1: Rsync results from remote ────────────────────────────────
log "Step 1: Syncing results from remote..."

# A1/A2 MixedKV LongBench/RULER results
rsync -avz --progress \
  -e "ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
  "$SSH_USER@$SSH_HOST:$REMOTE_DIR/results/emnlp_postfix_v2/runs/" \
  "$LOCAL_DIR/results/emnlp_postfix_v2/runs/"
log "  MixedKV results synced"

# A3 C6 RULER fix results
rsync -avz --progress \
  -e "ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
  "$SSH_USER@$SSH_HOST:$REMOTE_DIR/results/emnlp_c6_fix/" \
  "$LOCAL_DIR/results/emnlp_c6_fix/"
log "  C6 fix results synced"

# A4 8B attention KL data
rsync -avz --progress \
  -e "ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
  "$SSH_USER@$SSH_HOST:$REMOTE_DIR/results/attention_kl/" \
  "$LOCAL_DIR/results/attention_kl/"
log "  Attention KL data synced"

# ─── Step 2: Re-aggregate emnlp_postfix_v2 ───────────────────────────
log "Step 2: Re-aggregating emnlp_postfix_v2..."

# This needs to run on the remote (where pandas/numpy are available)
# OR locally if dependencies are installed
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "bash -lc '
cd $REMOTE_DIR
/root/miniconda3/bin/python3 scripts/aggregate_results.py \
  --runs_dir results/emnlp_postfix_v2/runs \
  --tables_dir results/emnlp_postfix_v2/tables \
  --plots_dir results/emnlp_postfix_v2/plots
'"
log "  Remote aggregation complete"

# Sync aggregated tables back
rsync -avz --progress \
  -e "ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
  "$SSH_USER@$SSH_HOST:$REMOTE_DIR/results/emnlp_postfix_v2/tables/" \
  "$LOCAL_DIR/results/emnlp_postfix_v2/tables/"
log "  Aggregated tables synced"

# ─── Step 3: Aggregate C6 fix results ────────────────────────────────
log "Step 3: Aggregating C6 fix results..."
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "bash -lc '
cd $REMOTE_DIR
/root/miniconda3/bin/python3 scripts/aggregate_results.py \
  --runs_dir results/emnlp_c6_fix/runs \
  --tables_dir results/emnlp_c6_fix/tables \
  --plots_dir results/emnlp_c6_fix/plots
'"

rsync -avz --progress \
  -e "ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
  "$SSH_USER@$SSH_HOST:$REMOTE_DIR/results/emnlp_c6_fix/tables/" \
  "$LOCAL_DIR/results/emnlp_c6_fix/tables/"
log "  C6 aggregation complete"

# ─── Step 4: Generate final paper tables ──────────────────────────────
log "Step 4: Building paper tables..."
python3 scripts/build_paper_tables.py \
  --mainline_dir results/emnlp_final_raw/tables \
  --mixedkv_dir results/emnlp_postfix_v2/tables \
  --out_dir results/paper_tables \
  --tables all -v
log "  Paper tables generated"

# ─── Step 5: Generate 8B heatmap (if data available) ─────────────────
log "Step 5: Generating 8B heatmap..."
if [ -f "results/attention_kl/attention_kl_int4_mixed_kv_llama_3.1_8b_instruct.json" ] || \
   [ -f "results/attention_kl/attention_kl_int4_mixed_kv_Llama-3.1-8B-Instruct.json" ]; then
    python3 scripts/plot_attention_kl_heatmap.py \
      --input results/attention_kl/attention_kl_int4_mixed_kv_*.json \
      --out_dir results/plots/attention_kl/
    log "  All heatmaps generated (including 8B)"
else
    log "  WARNING: 8B attention KL JSON not found. Generating 1.5B+7B only."
    python3 scripts/plot_attention_kl_heatmap.py \
      --input results/attention_kl/attention_kl_int4_mixed_kv_qwen*.json \
      --out_dir results/plots/attention_kl/
fi

# ─── Step 6: Verify completeness ─────────────────────────────────────
log "Step 6: Verification..."
echo "=== Paper tables ==="
ls results/paper_tables/*.tex 2>/dev/null | wc -l
echo " LaTeX tables generated"

echo "=== MixedKV LongBench CSVs ==="
find results/emnlp_postfix_v2/runs/*closure* -name "profile_longbench*.csv" 2>/dev/null | wc -l
echo " LongBench CSVs"

echo "=== MixedKV RULER CSVs ==="
find results/emnlp_postfix_v2/runs/*closure* -name "profile_ruler*.csv" 2>/dev/null | wc -l
echo " RULER CSVs"

echo "=== C6 Fix RULER CSVs ==="
find results/emnlp_c6_fix/runs/ -name "profile_ruler*.csv" 2>/dev/null | wc -l
echo " C6 RULER CSVs"

echo "=== Heatmap PDFs ==="
ls results/plots/attention_kl/*.pdf 2>/dev/null | wc -l
echo " heatmap PDFs"

log "=== Closure Pack Post-processing COMPLETE ==="
