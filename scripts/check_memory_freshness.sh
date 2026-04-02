#!/usr/bin/env bash
# check_memory_freshness.sh — SessionStart hook 脚本
# 检测 MEMORY.md 是否与仓库实际状态脱节，输出警告注入会话上下文。
# 设计原则：轻量 (<0.5s)、只读、误报可接受（宁可多提醒一次）。

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
MEMORY_DIR="$HOME/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory"
MEMORY_FILE="$MEMORY_DIR/MEMORY.md"

# 如果不在本项目目录，跳过
if [[ ! "$PROJECT_ROOT" == */LLM_KVCache_Quantization ]]; then
    exit 0
fi

# 如果 MEMORY.md 不存在，跳过
if [[ ! -f "$MEMORY_FILE" ]]; then
    exit 0
fi

WARNINGS=""

# ── Check 1: src/cache/ 中是否有未被 MEMORY.md 记录的 .py 文件 ──
for f in "$PROJECT_ROOT"/src/cache/*.py; do
    fname=$(basename "$f")
    [[ "$fname" == "__init__.py" ]] && continue
    if ! grep -q "$fname" "$MEMORY_FILE" 2>/dev/null; then
        WARNINGS="${WARNINGS}⚠ src/cache/$fname 未在 MEMORY.md 文件导航中记录\n"
    fi
done

# ── Check 2: MEMORY.md 引用的缓存文件是否仍然存在 ──
for ref_file in $(grep -oE 'src/cache/[a-z_]+\.py' "$MEMORY_FILE" 2>/dev/null | sort -u); do
    if [[ ! -f "$PROJECT_ROOT/$ref_file" ]]; then
        WARNINGS="${WARNINGS}⚠ MEMORY.md 引用了不存在的文件: $ref_file\n"
    fi
done

# ── Check 3: kv_modes 是否缺少代码中实际路由的模式 ──
# 从 generate_loop.py 提取路由的 kv_mode 值
if [[ -f "$PROJECT_ROOT/src/engine/generate_loop.py" ]]; then
    for mode in $(grep -oE "kv_mode\s*==\s*['\"][a-z0-9_]+['\"]" "$PROJECT_ROOT/src/engine/generate_loop.py" 2>/dev/null \
                  | grep -oE "['\"][a-z0-9_]+['\"]" | tr -d "'" | tr -d '"' | sort -u); do
        if ! grep -q "$mode" "$MEMORY_FILE" 2>/dev/null; then
            WARNINGS="${WARNINGS}⚠ kv_mode '$mode' 在代码中路由但未在 MEMORY.md 记录\n"
        fi
    done
fi

# ── Check 4: MEMORY.md 最后修改距今是否超过 7 天 ──
if [[ "$(uname)" == "Darwin" ]]; then
    mem_mtime=$(stat -f %m "$MEMORY_FILE" 2>/dev/null || echo 0)
else
    mem_mtime=$(stat -c %Y "$MEMORY_FILE" 2>/dev/null || echo 0)
fi
now=$(date +%s)
age_days=$(( (now - mem_mtime) / 86400 ))
if [[ $age_days -ge 7 ]]; then
    WARNINGS="${WARNINGS}⚠ MEMORY.md 已 ${age_days} 天未更新，可能需要刷新\n"
fi

# ── 输出结果 ──
if [[ -n "$WARNINGS" ]]; then
    echo "Memory freshness check:"
    echo -e "$WARNINGS"
    echo "建议在本 session 中确认 MEMORY.md 是否需要更新。"
fi

exit 0
