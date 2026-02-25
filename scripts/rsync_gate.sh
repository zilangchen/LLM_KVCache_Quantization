#!/bin/bash
# rsync 前置门禁：确保推送稳定代码到远程
set -e

BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "ERROR: rsync 只允许从 main 分支推送（当前: $BRANCH）" && exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: git status 不干净，请先 commit 或 stash" && exit 1
fi

if [ "$1" != "--skip-tests" ]; then
    echo "Running quick test gate..."
    pytest tests/ -v --timeout=60 -q
fi

echo "Gate PASSED. Safe to rsync."
