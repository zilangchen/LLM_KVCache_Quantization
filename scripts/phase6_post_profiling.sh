#!/bin/bash
# Phase 6 Post-Profiling Pipeline: Steps 3-7
# Run AFTER core profiling completes (Step 2).
#
# Steps:
#   3. Merge phase5v2 + phase6 → emnlp_final_raw/
#   4. Copy raw → strictable, run diagnostics
#   5. Authoritative aggregation + LaTeX + claim validation
#   6. Optional strict QA
#   7. Claim summary
#
# Usage:
#   bash scripts/phase6_post_profiling.sh
#
# Prerequisites:
#   - Phase 5v2 results in results/phase5v2/runs (1560 dirs)
#   - Phase 6 results in results/phase6/runs (~576 dirs)

set -uo pipefail

PYTHON="${PYTHON:-/root/miniconda3/bin/python}"
SRC="/root/LLM_KVCache_Quantization"
PHASE5V2_RUNS="$SRC/results/phase5v2/runs"
PHASE6_RUNS="$SRC/results/phase6/runs"
FINAL_RAW="$SRC/results/emnlp_final_raw"
FINAL_STRICT="$SRC/results/emnlp_final_strictable"
TABLES_DIR="$FINAL_RAW/tables"
PLOTS_DIR="$FINAL_RAW/plots"
LATEX_DIR="$FINAL_RAW/latex_tables"
REPORT_DIR="$FINAL_RAW/report"
LOGS_RAW="$FINAL_RAW/logs"
LOG="$SRC/results/phase6_post_profiling.log"

echo "=== Phase 6 Post-Profiling Pipeline: $(date) ===" | tee "$LOG"

# ── Step 3: Merge data ──────────────────────────────────────────────
echo "" | tee -a "$LOG"
echo "=== STEP 3: Merge data to emnlp_final_raw ===" | tee -a "$LOG"

# Archive old if exists
if [ -d "$FINAL_RAW" ]; then
    BACKUP="$SRC/results/emnlp_final_raw_bak_$(date +%Y%m%d_%H%M%S)"
    echo "  Archiving existing emnlp_final_raw → $BACKUP" | tee -a "$LOG"
    mv "$FINAL_RAW" "$BACKUP"
fi

mkdir -p "$FINAL_RAW/runs" "$FINAL_RAW/logs"

echo "  Merging phase5v2..." | tee -a "$LOG"
rsync -a "$PHASE5V2_RUNS/" "$FINAL_RAW/runs/"
# Also merge phase5v2 logs if available
if [ -d "$SRC/results/phase5v2/logs" ]; then
    rsync -a "$SRC/results/phase5v2/logs/" "$FINAL_RAW/logs/"
fi

echo "  Merging phase6..." | tee -a "$LOG"
rsync -a "$PHASE6_RUNS/" "$FINAL_RAW/runs/"
if [ -d "$SRC/results/phase6/logs" ]; then
    rsync -a "$SRC/results/phase6/logs/" "$FINAL_RAW/logs/"
fi

TOTAL_MERGED=$(find "$FINAL_RAW/runs" -maxdepth 1 -type d | wc -l)
TOTAL_MERGED=$((TOTAL_MERGED - 1))
echo "  Total merged dirs: $TOTAL_MERGED" | tee -a "$LOG"

# Sanity check
P5V2_COUNT=$(find "$PHASE5V2_RUNS" -maxdepth 1 -type d | wc -l)
P6_COUNT=$(find "$PHASE6_RUNS" -maxdepth 1 -type d | wc -l)
P5V2_COUNT=$((P5V2_COUNT - 1))
P6_COUNT=$((P6_COUNT - 1))
echo "  Phase5v2: $P5V2_COUNT, Phase6: $P6_COUNT, Expected: ~$((P5V2_COUNT + P6_COUNT))" | tee -a "$LOG"

# Check for long dirs (32K data)
LONG_COUNT=$(find "$FINAL_RAW/runs" -maxdepth 1 -type d -name "*_long_*" -o -name "*_long" | wc -l)
echo "  *_long* dirs: $LONG_COUNT" | tee -a "$LOG"

echo "=== STEP 3 COMPLETE ===" | tee -a "$LOG"

# ── Step 4: Strictable copy ─────────────────────────────────────────
echo "" | tee -a "$LOG"
echo "=== STEP 4: Strictable copy + diagnostics ===" | tee -a "$LOG"

if [ -d "$FINAL_STRICT" ]; then
    BACKUP_S="$SRC/results/emnlp_final_strictable_bak_$(date +%Y%m%d_%H%M%S)"
    mv "$FINAL_STRICT" "$BACKUP_S"
fi

rsync -a "$FINAL_RAW/runs/" "$FINAL_STRICT/runs/"
mkdir -p "$FINAL_STRICT/logs"
if [ -d "$FINAL_RAW/logs" ]; then
    rsync -a "$FINAL_RAW/logs/" "$FINAL_STRICT/logs/"
fi

echo "  Strictable copy created" | tee -a "$LOG"
echo "=== STEP 4 COMPLETE ===" | tee -a "$LOG"

# ── Step 5: Authoritative aggregation ───────────────────────────────
echo "" | tee -a "$LOG"
echo "=== STEP 5: Aggregation + LaTeX + Claims ===" | tee -a "$LOG"

mkdir -p "$TABLES_DIR" "$PLOTS_DIR" "$LATEX_DIR" "$REPORT_DIR"

# 5a: Aggregate
echo "  5a: Running aggregate_results.py..." | tee -a "$LOG"
$PYTHON "$SRC/scripts/aggregate_results.py" \
    --runs_dir "$FINAL_RAW/runs" \
    --tables_dir "$TABLES_DIR" \
    --plots_dir "$PLOTS_DIR" \
    --logs_dir "$FINAL_RAW/logs" 2>&1 | tee -a "$LOG"
AGG_EXIT=$?
echo "  aggregate exit: $AGG_EXIT" | tee -a "$LOG"

# Check critical CSVs
echo "  Checking CSVs..." | tee -a "$LOG"
for csv in latency_summary memory_summary ppl_summary needle_summary throughput_by_batch significance_summary; do
    if [ -f "$TABLES_DIR/${csv}.csv" ]; then
        ROWS=$(wc -l < "$TABLES_DIR/${csv}.csv")
        echo "    $csv: $ROWS rows" | tee -a "$LOG"
    else
        echo "    $csv: MISSING" | tee -a "$LOG"
    fi
done

# Check thesis_main_claims_32k
if [ -f "$TABLES_DIR/thesis_main_claims_32k.csv" ]; then
    ROWS=$(wc -l < "$TABLES_DIR/thesis_main_claims_32k.csv")
    echo "    thesis_main_claims_32k: $ROWS rows" | tee -a "$LOG"
else
    echo "    thesis_main_claims_32k: MISSING" | tee -a "$LOG"
fi

# Verify seq_lens in latency/memory
echo "  Checking latency_summary seq_lens..." | tee -a "$LOG"
$PYTHON -c "
import csv
for name in ['latency_summary', 'memory_summary']:
    path = '$TABLES_DIR/' + name + '.csv'
    try:
        with open(path) as f:
            r = csv.DictReader(f)
            seq_lens = set()
            for row in r:
                if 'seq_len' in row: seq_lens.add(row['seq_len'])
        print('    ' + name + ': seq_lens=' + str(sorted(seq_lens)))
    except Exception as e:
        print('    ' + name + ': ERROR ' + str(e))
" 2>&1 | tee -a "$LOG"

# 5b: LaTeX export
echo "  5b: Running export_tables_latex.py..." | tee -a "$LOG"
$PYTHON "$SRC/scripts/export_tables_latex.py" \
    --tables_dir "$TABLES_DIR" \
    --out_dir "$LATEX_DIR" 2>&1 | tee -a "$LOG"
LATEX_EXIT=$?
echo "  latex exit: $LATEX_EXIT" | tee -a "$LOG"

# Count tex files
TEX_COUNT=$(find "$LATEX_DIR" -name "*.tex" | wc -l)
echo "  LaTeX files: $TEX_COUNT" | tee -a "$LOG"

# 5c: Claim validation report
echo "  5c: Running generate_thesis_report.py..." | tee -a "$LOG"
$PYTHON "$SRC/scripts/generate_thesis_report.py" \
    --tables_dir "$TABLES_DIR" \
    --report_dir "$REPORT_DIR" 2>&1 | tee -a "$LOG"
REPORT_EXIT=$?
echo "  report exit: $REPORT_EXIT" | tee -a "$LOG"

# Check claim_validation.csv
if [ -f "$REPORT_DIR/claim_validation.csv" ]; then
    echo "  claim_validation.csv:" | tee -a "$LOG"
    cat "$REPORT_DIR/claim_validation.csv" | tee -a "$LOG"
else
    echo "  claim_validation.csv: MISSING" | tee -a "$LOG"
fi

echo "=== STEP 5 COMPLETE ===" | tee -a "$LOG"

# ── Step 6: Optional strict QA ──────────────────────────────────────
echo "" | tee -a "$LOG"
echo "=== STEP 6: Strict QA (optional) ===" | tee -a "$LOG"

$PYTHON "$SRC/scripts/aggregate_results.py" \
    --runs_dir "$FINAL_STRICT/runs" \
    --tables_dir "$FINAL_STRICT/tables" \
    --plots_dir "$FINAL_STRICT/plots" \
    --logs_dir "$FINAL_STRICT/logs" \
    --strict 2>&1 | tail -10 | tee -a "$LOG"
STRICT_EXIT=$?
echo "  strict exit: $STRICT_EXIT (0=pass, 2=strict fail, non-blocking)" | tee -a "$LOG"

echo "=== STEP 6 COMPLETE ===" | tee -a "$LOG"

# ── Step 7: Claim summary ───────────────────────────────────────────
echo "" | tee -a "$LOG"
echo "=== STEP 7: Claim Validation Summary ===" | tee -a "$LOG"

if [ -f "$REPORT_DIR/claim_validation.csv" ]; then
    $PYTHON -c "
import csv
with open('$REPORT_DIR/claim_validation.csv') as f:
    r = csv.DictReader(f)
    rows = list(r)
passed = [r for r in rows if r.get('status','').lower() == 'pass']
failed = [r for r in rows if r.get('status','').lower() == 'fail']
errors = [r for r in rows if r.get('status','').lower() == 'error']
print('  Total claims: ' + str(len(rows)))
print('  PASS: ' + str(len(passed)))
print('  FAIL: ' + str(len(failed)))
print('  ERROR: ' + str(len(errors)))
for r in failed:
    print('    FAIL: ' + r.get('claim_id','?') + ' - ' + r.get('description',''))
for r in errors:
    print('    ERROR: ' + r.get('claim_id','?') + ' - ' + r.get('description',''))
" 2>&1 | tee -a "$LOG"
fi

echo "" | tee -a "$LOG"
echo "=== Phase 6 Post-Profiling Pipeline COMPLETE: $(date) ===" | tee -a "$LOG"
echo "  Aggregate exit: $AGG_EXIT" | tee -a "$LOG"
echo "  LaTeX exit: $LATEX_EXIT" | tee -a "$LOG"
echo "  Report exit: $REPORT_EXIT" | tee -a "$LOG"
echo "  Strict exit: $STRICT_EXIT" | tee -a "$LOG"
