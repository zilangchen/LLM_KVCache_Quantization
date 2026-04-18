#!/usr/bin/env bash
# auto_archive.sh — SessionStart / compact-prep maintenance hook.
# Normalizes iteration.md to the latest-30-entry window and archives older
# entries. review_tracker.md is still size-gated. Exit 0 always.

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

# Always normalize iteration.md to latest 30 entries when possible.
ITERATION="$PROJECT_ROOT/iteration.md"
ITER_OUT=$(python3 "$PROJECT_ROOT/scripts/iteration_tool.py" trim-timeline --keep 30 2>&1 || true)
if [[ -n "$ITER_OUT" && "$ITER_OUT" != *"Nothing to trim."* ]]; then
    echo "$ITER_OUT"
    ARCHIVED_SOMETHING=1
fi

# Check review_tracker.md (>100KB = needs archive)
TRACKER="$PROJECT_ROOT/review_tracker.md"
SIZE=$(file_size "$TRACKER")
if [[ "$SIZE" -gt 102400 ]]; then
    if python3 "$PROJECT_ROOT/scripts/review_tool.py" -h 2>&1 | grep -q "archive-fixed"; then
        echo "⚠ review_tracker.md is $(( SIZE / 1024 ))KB (>100KB), auto-archiving fixed issues..."
        python3 "$PROJECT_ROOT/scripts/review_tool.py" archive-fixed 2>&1 || true
        ARCHIVED_SOMETHING=1
    fi
fi

if [[ "$ARCHIVED_SOMETHING" -eq 1 ]]; then
    echo "Auto-archive complete. Archived content in development_history/"
fi

exit 0
