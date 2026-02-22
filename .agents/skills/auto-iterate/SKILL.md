---
name: auto-iterate
description: >
  Continuously iterate toward project objectives until all success criteria
  are met or a hard blocker is reached. Use when you want autonomous,
  multi-cycle development without manual intervention. Reads objective.md
  for goals, iteration.md for progress, runs code/tests, invokes
  $debug-iterate on failure, $unit-commit on milestone completion,
  and $repo-hygiene after each commit. Stops only when objectives are
  satisfied or after hitting the iteration cap.
---

# Auto-Iterate Skill

> 自动迭代引擎：持续驱动项目向 objective.md 中的目标前进，直到所有验收标准达成或遇到无法自主解决的阻塞。

---

## 触发方式

- 用户手动调用 `/auto-iterate [可选：聚焦方向]`
- 示例：`/auto-iterate 完成 Week5 外部有效性实验` 或 `/auto-iterate`（全目标扫描）

---

## 核心循环（强制遵守）

每轮迭代严格执行以下 6 个阶段，**不得跳过任何阶段**：

### Phase 1: 加载上下文

1. 读取 `objective.md` — 提取所有 **Success Criteria** 条目
2. 读取 `iteration.md` — 了解已完成的里程碑和当前进度
3. 读取 `iteration.md` 顶部的 **待办清单**（如有）
4. 如果用户传入了聚焦方向（`$ARGUMENTS`），只关注相关目标子集

输出一份简要的 **状态评估**：
```
## 迭代 N — 状态评估
- 已达成目标：[列出]
- 未达成目标：[列出，按优先级排序]
- 当前阻塞：[列出，若无则写"无"]
- 本轮计划：[选择优先级最高的 1 个未达成目标]
```

### Phase 2: 规划本轮工作

针对选定的目标，制定 **最小可交付单元**：
- 具体要改哪些文件
- 验证命令是什么
- 预期通过的信号

规模控制：每轮迭代只做 **1 个里程碑**（小步快跑），不要试图一次解决所有问题。

### Phase 3: 执行

- 编码 / 修改配置 / 运行脚本
- 遵守项目编码标准（正确性第一、小步可审查、必要测试）
- 远程 GPU 任务使用 `$long-running-task` 模式（检查点 + 断点续传）

### Phase 4: 验证

运行验证命令，检查结果：
- **通过** → 进入 Phase 5
- **失败** → 立即调用 `$debug-iterate`，修复后重新验证
  - `$debug-iterate` 最多循环 5 次
  - 仍失败 → 记录为阻塞，进入 Phase 6

### Phase 5: 落地

调用 `$unit-commit`：
1. 追加 `iteration.md`（时间、目标、变更、命令、结果、commit hash）
2. 运行验证命令
3. 按语义分组 `git add`（禁止 `git add .`）
4. `git commit` with semantic prefix
5. 调用 `$repo-hygiene`（确保 git status 干净）

### Phase 6: 循环判断

检查退出条件：

| 条件 | 动作 |
|------|------|
| **所有目标达成** | 输出最终总结，正常退出 |
| **达到迭代上限**（默认 8 轮） | 输出进度摘要 + 剩余工作，暂停并汇报 |
| **遇到硬阻塞**（缺权限/数据/外部依赖） | 记录阻塞原因到 iteration.md，给出选项和推荐，暂停提问 |
| **以上均不满足** | 回到 Phase 1，开始下一轮 |

---

## 迭代上限与安全机制（防止死循环、浪费 token）

### 硬性上限

- **默认迭代上限**：**5 轮**（可通过 `/auto-iterate --max N` 覆盖，绝对上限 10）
- **单轮超时**：如果单轮执行超过 15 分钟没有产出，自动暂停并汇报

### 无进展检测（最重要的防护）

每轮结束时自评本轮是否产生了 **实质性进展**（定义：至少产生了 1 个新 commit，或解决了 1 个之前未解决的问题）。

- **连续 2 轮无实质进展** → 立即停止，输出诊断报告，标记 `<!-- auto-iterate-stalled -->`
- **连续失败熔断**：同一个目标连续 2 轮都在 Phase 4 失败（`$debug-iterate` 无法修复）→ 停止，不要继续在同一个坑里打转
- **重复劳动检测**：如果发现自己在做与前一轮相同的修改（改了又改回去）→ 立即停止

### 禁止行为

- **禁止掩盖失败**：不得跳过失败的测试、不得注释掉断言、不得降低验收标准
- **禁止膨胀式修复**：如果一个 bug 修了 3 次还没修好，说明需要换思路或人工介入，不要继续堆补丁

---

## 必须停下来问用户的场景（强制 Escalation）

只有以下 **高风险情况** 才需要暂停迭代等待用户确认，其他情况自行判断推进：

- 需要修改 `objective.md` 的目标/边界/成功标准
- 需要执行破坏性操作（删除数据/重要文件/分支）
- 实验结果表明需要改变研究方向

暂停时的输出格式：
```markdown
## ⏸ 需要用户确认

**类型**：[架构决策 / 目标变更 / 资源风险 / 不确定性]
**问题**：[简述]
**选项**：
- A: [方案] — 理由 / 风险
- B: [方案] — 理由 / 风险
**推荐**：[选项] — 因为 [理由]

请回复选项字母或给出你的决定，我将继续迭代。
```

在 `iteration.md` 中标记：`<!-- auto-iterate-needs-user-input: 简述问题 -->`

---

## 输出格式（每轮必须）

```markdown
---
## 迭代 N/M | <执行 date '+%Y-%m-%d %H:%M' 获取的真实时间>

### 状态评估
- 目标达成：X/Y
- 本轮聚焦：[目标名称]

### 执行摘要
- 变更：[文件列表]
- 验证命令：[具体命令]
- 结果：PASS / FAIL

### 落地状态
- iteration.md：已追加
- commit：`<hash>` — `<message>`
- 仓库卫生：干净

### 下一轮计划
- [下一个目标或"全部达成，退出"]
---
```

---

## 最终总结（所有目标达成时）

```markdown
## Auto-Iterate 完成报告

- 总迭代轮次：N
- 达成目标：[全部列出]
- 关键 commit：[hash 列表]
- 遗留事项：[若有]
- iteration.md 最终条目已写入
```

---

## 与现有技能的协作关系

```
auto-iterate（编排者）
    ├── $debug-iterate  — Phase 4 失败时调用
    ├── $unit-commit    — Phase 5 落地时调用
    ├── $repo-hygiene   — Phase 5 落地后调用
    └── $long-running-task — Phase 3 远程 GPU 任务时调用
```

---

## 约束与红线

- **不修改** `objective.md`（除非目标确实需要更新，且必须先获得用户确认）
- **不修改** `experiment_sop.md` 或 `AGENTS.md`（除非用户明确要求）
- **不执行** 破坏性命令（`rm -rf` / `git reset --hard` / `git push --force`）
- **不 push**（除非用户明确要求）
- **iteration.md 只追加**，不覆盖历史
- 每轮结束后 `git status` 必须干净
