#!/bin/bash
# scripts/sync_merged_runs.sh — Idempotent merge of experiment runs
#
# Merges emnlp_final_raw (Layer A legacy) and emnlp_postfix_v2 (Layer B/C new)
# into emnlp_final_merged/runs/ via symlinks.
#
# Safe to run at any checkpoint — always picks up new run directories.
# Usage: bash scripts/sync_merged_runs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MERGED="$PROJECT_ROOT/results/emnlp_final_merged/runs"

mkdir -p "$MERGED"

count=0

# Layer A: symlink legacy results (fp16, int8_*, kivi_*, int4_baseline, int4_ours, int4_fused, int4_ours_mixed)
if [ -d "$PROJECT_ROOT/results/emnlp_final_raw/runs" ]; then
    for d in "$PROJECT_ROOT/results/emnlp_final_raw/runs"/*/; do
        [ -d "$d" ] || continue
        target="$MERGED/$(basename "$d")"
        ln -sfn "$(cd "$d" && pwd)" "$target"
        count=$((count + 1))
    done
fi

# Layer B/C: symlink new results (MixedKV, KIVI matched reruns, K/V ablations, extensions)
if [ -d "$PROJECT_ROOT/results/emnlp_postfix_v2/runs" ]; then
    for d in "$PROJECT_ROOT/results/emnlp_postfix_v2/runs"/*/; do
        [ -d "$d" ] || continue
        target="$MERGED/$(basename "$d")"
        ln -sfn "$(cd "$d" && pwd)" "$target"
        count=$((count + 1))
    done
fi

echo "Merged: $count run directories into $MERGED"
