#!/usr/bin/env bash
# Expansion Pack — Post-processing (run locally after rsync)
#
# Steps:
# 1. Aggregate expansion_v1 results
# 2. Generate B10 sensitivity table
# 3. Generate K/V ablation tables
# 4. Generate Mistral heatmap plots
# 5. Rebuild paper_tables (with new data if applicable)
#
# Usage: bash scripts/expansion_postprocess.sh
# Created: 2026-03-19

set -euo pipefail

PYTHON="${PYTHON:-python3}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

EXP_DIR="results/emnlp_expansion_v1"

echo "=== Expansion Postprocess — started $(date '+%Y-%m-%d %H:%M:%S') ==="

# =====================================================================
# 1. Aggregate expansion results
# =====================================================================
echo "--- Aggregating expansion results ---"
if [ -d "$EXP_DIR/runs" ]; then
    $PYTHON scripts/aggregate_results.py \
        --runs_dir "$EXP_DIR/runs" \
        --tables_dir "$EXP_DIR/tables" \
        --plots_dir "$EXP_DIR/plots"
    echo "Aggregation DONE"
else
    echo "WARNING: $EXP_DIR/runs not found, skipping aggregation"
fi

# =====================================================================
# 2. B10 Sensitivity table
# =====================================================================
echo "--- B10 Sensitivity table ---"
$PYTHON scripts/build_b10_sensitivity_table.py \
    --runs_dir "$EXP_DIR/runs" \
    --out_dir "$EXP_DIR/tables"

# =====================================================================
# 3. K/V Ablation tables
# =====================================================================
echo "--- K/V Ablation tables ---"
$PYTHON scripts/build_kv_ablation_table.py \
    --runs_dir "$EXP_DIR/runs" \
    --out_dir "$EXP_DIR/tables"

# =====================================================================
# 4. Mistral heatmap (Phase 5)
# =====================================================================
echo "--- Mistral heatmap plots ---"
HEATMAP_JSON=$(ls results/attention_kl/attention_kl_int4_mixed_kv_*mistral*.json 2>/dev/null | head -1 || true)
if [ -n "$HEATMAP_JSON" ]; then
    $PYTHON scripts/plot_attention_kl_heatmap.py \
        --input "$HEATMAP_JSON" \
        --out_dir results/plots/attention_kl/
    echo "Heatmap DONE"
else
    echo "WARNING: Mistral heatmap JSON not found, skipping"
fi

# =====================================================================
# 5. Rebuild paper tables (with Closure + Expansion data)
# =====================================================================
echo "--- Rebuild paper tables ---"
$PYTHON scripts/build_paper_tables.py --tables all -v

echo "=== Expansion Postprocess COMPLETE $(date '+%Y-%m-%d %H:%M:%S') ==="
