#!/usr/bin/env bash
# auto_archive.sh — SessionStart hook: auto-archive bloated tracker files.
# Checks iteration.md and review_tracker.md sizes; archives if >100KB.
# Exit 0 always (must not block session startup).

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Guard: only run in the correct project
if [[ ! -f "$PROJECT_ROOT/iteration.md" ]]; then
    exit 0
fi

ARCHIVED_SOMETHING=0

# Cross-platform stat: macOS uses -f%z, Linux uses -c%s
file_size() {
    stat -f%z "$1" 2>/dev/null || stat -c%s "$1" 2>/dev/null || echo 0
}

# Check iteration.md (>100KB = needs trim)
ITERATION="$PROJECT_ROOT/iteration.md"
SIZE=$(file_size "$ITERATION")
if [[ "$SIZE" -gt 102400 ]]; then
    echo "⚠ iteration.md is $(( SIZE / 1024 ))KB (>100KB), auto-trimming timeline..."
    python3 "$PROJECT_ROOT/scripts/iteration_tool.py" trim-timeline --keep 15 2>&1 || true
    ARCHIVED_SOMETHING=1
fi

# Check review_tracker.md (>100KB = needs archive)
TRACKER="$PROJECT_ROOT/review_tracker.md"
SIZE=$(file_size "$TRACKER")
if [[ "$SIZE" -gt 102400 ]]; then
    echo "⚠ review_tracker.md is $(( SIZE / 1024 ))KB (>100KB), auto-archiving fixed issues..."
    python3 "$PROJECT_ROOT/scripts/review_tool.py" archive-fixed 2>&1 || true
    ARCHIVED_SOMETHING=1
fi

if [[ "$ARCHIVED_SOMETHING" -eq 1 ]]; then
    echo "Auto-archive complete. Archived content in development_history/"
fi

exit 0
