#!/usr/bin/env bash
# check_archive_needed.sh — PostToolUse hook: warn when iteration.md or review_tracker.md is too big.
# Called after Edit on these files. Non-blocking (exit 0 always).

FILE=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('file_path',''))" 2>/dev/null || echo '')

case "$FILE" in
  */iteration.md|*/review_tracker.md)
    SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE" 2>/dev/null || echo 0)
    if [ "$SIZE" -gt 102400 ]; then
      BASENAME=$(basename "$FILE")
      echo "⚠ $BASENAME is $((SIZE/1024))KB (>100KB). Run: bash scripts/auto_archive.sh"
    fi
    ;;
esac

exit 0
