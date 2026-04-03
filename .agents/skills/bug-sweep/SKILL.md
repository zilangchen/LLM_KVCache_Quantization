---
name: bug-sweep
description: >
  Bug 修复闭环流水线。读取 review_tracker.md，按严重性分组，启动并行 Agent 按文件分区修复，
  每批后自动触发 Codex 审查，FAIL 回去重修，PASS 标记 tracker + 下一批。循环不停直到清零。
  触发: "修 bug"、"清 tracker"、"bug sweep"、"/bug-sweep"、或有 open HIGH/CRITICAL。
---

# Bug 修复闭环流水线

## Phase 1: 评估
1. `python3 scripts/review_tool.py stats`
2. 按文件前缀分组（EVL→eval, ENG→engine, KVC→cache, QNT→quant, etc.）
3. 估算批次数 = ceil(issues / 6)

## Phase 2: 并行修复（≤6 Agent/批）
1. 按文件分区启动 Agent（两个 Agent 不改同一文件）
2. Agent prompt: issue 描述 + 文件路径 + `py_compile` 验证
3. 完成即标记 tracker `[x]`，不等全部回来
4. 同时手动修不冲突的文件

## Phase 3: Codex 审查（每批后自动）
1. 启动 `codex:codex-rescue` 审查该批 `git diff`
2. **FAIL** → 修正 → 回 Phase 2
3. **PASS** → 下一批

## Phase 4: 循环
1. 批量标记 tracker
2. 更新统计头
3. 还有目标 issues → 回 Phase 2
4. 全部清零 → `py_compile` + commit

## 硬性规则
- Codex 审查**必须触发**，不可跳过
- 永远保持 N 个 Agent 后台运行
- Tracker 标记不拖延
- 批次之间不停转，不等用户确认
- 禁止 `git checkout` 有未暂存修改的文件

## tracker 批量标记
```python
python3 -c "
issues = ['XXX-001', 'XXX-002']
with open('review_tracker.md', 'r') as f:
    c = f.read()
n = 0
for i in issues:
    old = f'- [ ] **{i}**'
    if old in c:
        c = c.replace(old, f'- [x] **{i}**', 1)
        n += 1
with open('review_tracker.md', 'w') as f:
    f.write(c)
print(f'Marked {n}')
"
```
