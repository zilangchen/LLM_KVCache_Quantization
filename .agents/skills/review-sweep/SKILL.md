---
description: 全项目代码审查扫描 — 并行 D1-D7 Agent 按波次覆盖全模块，自动去重+修正 tracker+commit。支持 full/incremental/verify 三模式。
---

# Review Sweep — 全项目代码审查扫描

> 将 R27-R29 三轮手动审查的最佳实践编码为可重复执行的标准流程。
> 单次执行、完成退出，区别于 review-coord 的持续守护模式。

---

## 触发方式

```
/review-sweep              # 全量扫描（默认）
/review-sweep incremental  # 仅扫描最近 N commits 的变更文件
/review-sweep verify       # 修复验证模式：验证最近修复 + 搜索回归
```

---

## Phase 0: Pre-flight（必须，不可跳过）

### 0.1 工作目录检查

```bash
git status -s
```

- **干净** → 继续
- **有未提交变更** → 提示用户选择：
  - 分批 commit（推荐）→ 按语义分组（归档/src/scripts/tests/docs），每批 `--no-verify` commit
  - 直接审查当前状态 → 在报告中标注"含未提交变更"

### 0.2 Tracker 基线读取

```bash
head -5 review_tracker.md                    # 当前统计
grep -c '^- \[ \]' review_tracker.md         # 实际 open 数
grep '^- \[ \].*\[HIGH\]\|^- \[ \].*\[CRIT\]' review_tracker.md  # CRIT+HIGH 列表
```

生成 **已知 issues 去重列表**（传给每个 Agent 避免重复报告）：
- 提取所有 open issue 的 ID（如 EVL-145, KVC-085 等）
- 按文件分组，每个 Agent 只收到其审查范围内的已知 issues

### 0.3 确定轮次编号

```bash
grep -oP 'R\d+' review_tracker.md | sort -t'R' -k1 -n | tail -1
```

取最大轮次 +1 作为本轮编号（如 R29 → R30）。

### 0.4 模式判断

| 模式 | 触发条件 | 审查范围 | Agent 数量 |
|------|---------|---------|-----------|
| **全量** | 默认 / `full` | 10 模块全覆盖 | 5-8 agents |
| **增量** | `incremental` | 最近 commits 变更文件 | 3-5 agents |
| **验证** | `verify` | 最近修复的文件 + 全量二次确认 | 5 agents |

---

## Phase 1: Agent 调度矩阵

### 1.1 模块-维度矩阵

10 个代码模块 × 7 个审查维度（D1-D7），但不是 70 个 Agent。
按亲和性分组为 **3 波**，每波 spawn 的 Agent 覆盖最相关的维度：

| 波次 | 目标模块 | 文件 glob | 核心维度 | 辅助维度 |
|------|---------|----------|---------|---------|
| **W1** | 评测 + 引擎 | `scripts/eval_*.py` + `src/engine/*.py` | D1(数值), D2(静默) | D4(契约), D5(边界) |
| **W2** | 缓存 + 量化 + 内核 | `src/cache/*.py` + `src/quant/*.py` + `src/kernels/*.py` | D1(数值), D5(边界) | — |
| **W3** | 工具 + 测试 + 配置 | `scripts/{run,profile,calibrate,aggregate,check}*.py` + `tests/*.py` + `configs/*.yaml` | D2(静默), D6(测试) | D3(安全), D7(质量) |

### 1.2 实际 Agent 分配（全量模式）

在 **一条消息** 中并行 spawn 全部 Agent（最大化并行度）：

```
Agent 1: review-numerical  → W1 文件（eval + engine）
Agent 2: review-silent     → W1 文件（eval + engine）+ W3 工具
Agent 3: review-numerical  → W2 文件（cache + quant + kernels）
Agent 4: review-boundary   → W1+W2 全部核心文件
Agent 5: review-contract   → W1 文件 + run_experiments + config_utils
Agent 6: review-test       → tests/ 全部 + 被测源码对照
Agent 7: review-quality    → 最近修改的文件（git diff --stat）
Agent 8: review-security   → 全项目安全扫描（可选，每 3 轮执行一次）
```

**增量模式** 缩减为 3-4 agents，仅覆盖变更文件的相关维度。
**验证模式** 每个 Agent prompt 额外包含"请验证以下修复"段落。

### 1.3 Agent Prompt 模板

每个 Agent 的 prompt **必须包含**以下 5 个段落：

```markdown
## R{N} 全量审查 — {维度名称}（{目标模块}）

### 背景
{上一轮发现摘要 + 修复状态 + 本轮目标}

### 审查文件
{具体文件路径列表}

### 审查清单
{该维度的标准清单 — 从 .claude/agents/review-{dimension}.md 读取}

### 已知 issues（避免重复）
{从 Phase 0.2 生成的去重列表，仅含该 Agent 审查范围内的 issues}

### 输出格式
**[ID-placeholder]** `[severity]` 一句话描述 (file:line_range)
详细说明...
— confidence: XX%

severity = CRITICAL / HIGH / MED / LOW
confidence >= 80% 才报告
```

### 1.4 模型选择

```
默认: model="sonnet"
```

> **硬性规则**：除非用户明确要求 Opus，否则一律使用 Sonnet。
> 原因：Opus 并行 agent 容易触发速率限制（R29 实测 5 个 Opus agent 全部返回空）。
> Sonnet 在 R27 中已验证能发现 CRIT 级问题（KVC-085）。

### 1.5 spawn 参数

```python
Agent(
    subagent_type="review-{dimension}",
    model="sonnet",
    run_in_background=True,
    name="r{N}-d{X}-{target}",      # 如 r30-d1-eval
    prompt="..."                      # Phase 1.3 模板
)
```

---

## Phase 2: 结果汇聚（全部 Agent 返回后）

### 2.1 收集发现

逐个读取返回结果，提取新发现。记录：
- Agent 名称 + 维度
- 发现数量 × 严重性分布
- 修复验证结果（verify 模式）

### 2.2 去重

**跨 Agent 去重**（同一 bug 可能被多个维度发现）：
- 同一文件 + 同一行号范围 → 保留更详细的描述，合并来源标注
- 同根因不同文件 → 保留全部但交叉引用（如 ENG-112 和 ENG-113 都是 CWD 路径问题）

**与 tracker 去重**：
- 新发现的描述与已有 open issue 语义重叠 → 不新建，在已有 issue 追加"R{N} 再次确认"

### 2.3 严重性排序

```
CRITICAL > HIGH > MED > LOW
```

每个严重性内按文件路径字母序排列。

---

## Phase 3: Tracker 更新

### 3.1 写入新发现

每条新 issue 追加到 `review_tracker.md` 对应模块区块末尾。格式：

```markdown
- [ ] **{PREFIX}-{NUM}** `[{SEV}]` {一句话描述} ({file}:{line_range}): {详细说明} — R{N} {维度}, confidence: {XX}%
```

ID 前缀规则：
| 模块 | 前缀 |
|------|------|
| eval_*.py | EVL |
| generate_loop/patch_model | ENG |
| src/cache/ | KVC |
| src/quant/ | QNT |
| src/kernels/ | KRN |
| calibrate_behavior | CAL |
| profile_* | PRF |
| run_experiments | RUN |
| config_utils | CFG |
| tests/ | TST |
| 安全 | SEC |
| 质量 | QUA |
| 跨模块 | XMD |
| LaTeX/导出 | LTX |

### 3.2 修正 Header（关键步骤）

并发 Agent 写入会导致 header 计数不准。**必须**在所有 Agent 写入完成后重新计算：

```bash
# 实际计数
total_open=$(grep -c '^- \[ \]' review_tracker.md)
total_fixed=$(grep -c '^- \[x\]' review_tracker.md)
crit=$(grep -c '^- \[ \].*\[CRIT\]' review_tracker.md)
high=$(grep -c '^- \[ \].*\[HIGH\]' review_tracker.md)
med=$(grep -c '^- \[ \].*\[MED\]' review_tracker.md)
low=$(grep -c '^- \[ \].*\[LOW\]' review_tracker.md)
```

用 Edit 工具替换 header 为准确计数。格式：

```
> {total} issues | {fixed} fixed/documented + {fp} false_positive | {open} open ({crit} CRIT, {high} HIGH, {med} MED, {low} LOW)
> Phase Gate: **{BLOCKED|UNBLOCKED}** ({reason})
> Last updated: {date} (R{N}: {summary})
```

Phase Gate 规则：
- 有 CRIT open → **BLOCKED**
- 0 CRIT → **UNBLOCKED**

### 3.3 Phase Blockers 区块同步

如有新 CRIT issue，追加到 `## Phase Blockers (CRITICAL open)` 区块。
如 CRIT 已修复，将其从 Phase Blockers 中标记为 `[x]`。

---

## Phase 4: 记录与提交

### 4.1 获取真实时间

```bash
date '+%Y-%m-%d %H:%M'
```

### 4.2 追加 iteration.md Timeline

```markdown
### {时间} | R{N} 全量审查 — {agent数}-{model}-Agent 并行扫描完成
- Goal: {目标描述}
- Mode: {全量|增量|验证}扫描，{仅记录|边找边修}，{model} 模型
- **R{N} 新发现**: {total} issues ({crit} CRIT, {high} HIGH, {med} MED, {low} LOW)
  - {CRIT/HIGH 逐条列出}
  - {MED/LOW 概述}
- **修复验证**: {验证结果列表}（verify 模式时）
- **收敛趋势**: R{N-2}({x}) → R{N-1}({y}) → R{N}({z})
- Tracker: {total} issues, {open} open
- Phase Gate: {BLOCKED|UNBLOCKED}
- Next: {建议下一步}
```

### 4.3 Commit

```bash
git add review_tracker.md iteration.md
git commit --no-verify -m "docs: R{N} {mode} review — {new_count} new issues ({severity_summary})"
```

---

## Phase 5: 输出报告

最终输出格式（给用户看）：

```markdown
## R{N} 审查完成报告

| 指标 | 值 |
|------|-----|
| 扫描文件 | ~{count} 个 |
| Agent 数量 | {count} 个并行 |
| 新发现 | {total} issues |
| 严重性 | {crit} CRIT / {high} HIGH / {med} MED / {low} LOW |
| Phase Gate | {status} |

### CRIT + HIGH 问题清单
{逐条列出}

### 收敛趋势
R{N-2}({x}) → R{N-1}({y}) → R{N}({z})
{趋势判断：收敛/发散/波动}

### Tracker 状态
{统计摘要}
```

---

## 硬性规则

1. **不修改源代码**：审查 = 只读 + 写 tracker。要修复请用 `/bug-sweep`
2. **不跳过去重**：Phase 2.2 去重步骤不可省略，否则 tracker 膨胀
3. **必须修正 header**：Phase 3.2 是强制步骤，并发写入必然导致计数偏差
4. **真实时间戳**：iteration.md 条目必须用 `date` 命令获取，不可编造
5. **默认 Sonnet**：除非用户明确说 Opus，否则一律 Sonnet
6. **置信度门槛 80%**：低于门槛的发现不记录，宁缺勿滥
7. **Phase 0 不可跳过**：工作目录必须干净或已确认，tracker 基线必须读取

---

## 与其他 Skill 的协作

| 场景 | 调用链 |
|------|--------|
| 审查后修复 | `/review-sweep` → 用户确认 → `/bug-sweep`（读取新 open issues） |
| 修复后验证 | `/bug-sweep` → `/review-sweep verify` |
| 持续监控 | review-coord agent（守护模式）≠ review-sweep（单次模式） |
| 远程验证前 | `/review-sweep` → 确认 Phase Gate UNBLOCKED → rsync + pytest |

---

## 收敛判断标准

连续审查轮次的新发现趋势用于判断代码库稳定性：

| 趋势 | 判断 | 建议 |
|------|------|------|
| 3 轮递减（如 30→20→7） | **收敛** | 可停止审查，进入实验/发布阶段 |
| 持平（如 15→14→13） | **缓慢收敛** | 再跑 1-2 轮，关注是否有新类型问题 |
| 反弹（如 10→5→12） | **发散** | 检查是否有大量新代码引入，考虑增加审查维度 |
| 连续 2 轮 < 5 且 0 CRIT/HIGH | **稳定** | 代码库审查完成，记录到 iteration.md |
