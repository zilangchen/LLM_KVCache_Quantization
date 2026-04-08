# Phase 3: Expert Reviews（专家评审）

> Codex + 6 个 sub-agent reviewer 并行审查，汇总为统一意见清单。

---

## 输入
- `reports/round_N/paper_review.md` — Phase 2 的审查笔记
- `reports/round_N/literature_summary.md` — 文献调研结果
- `reviewer_templates/*.md` — 6 个 reviewer 的 prompt 模板
- 当前论文状态（thesis/chapters/*.tex）

## 输出
- `reports/round_N/expert_reviews.md` — 汇总评审意见

---

## 执行步骤

### Step 3.1: Codex 审查（先执行，串行）

调用：
```
/codex:review
```

Prompt 模板：
```
请审查 thesis/chapters/ 下当前修改的章节（本轮重点：<本轮章节列表>）。

上下文：
- 这是一篇面向 EMNLP 2026 投稿的论文
- 主线叙事是 5-Claim + 4-Finding 闭环
- 附带要求：SCUT 本科毕设格式合规（次要目标）

请从以下维度评审：
1. 学术严谨性（数据一致性、引用正确性）
2. 叙事逻辑（Claim-Finding-Evidence 链条）
3. 潜在的 reviewer 攻击面
4. 与现有 SOTA 的区分度

输出格式：
- [SEVERITY] [TYPE] 位置 — 问题描述 — 改进建议
```

Codex 输出保存到 `reports/round_N/codex_review.md`。

### Step 3.2: 并行启动 6 个 Reviewer sub-agents

使用 `Agent` 工具并行启动所有 6 个 reviewer。**必须在同一个 message 中发起所有 Agent 调用以实现真正并行**。

每个 reviewer 的 prompt 模板在 `reviewer_templates/<role>.md`，通用结构：

```
你是一位 EMNLP/ACL 的资深审稿人，专注领域：<该 reviewer 的领域>。

审查目标：
<粘贴当前 thesis/chapters/*.tex 的内容或关键段落>

你的审查标准：
<从该 reviewer 模板的 criteria 段落>

输出要求：
按以下格式，每个 issue 一条：

### Issue [SEVERITY] [TYPE] <short title>
- **File**: thesis/chapters/chX.tex
- **Location**: Line 123-145
- **Observation**: 你观察到了什么
- **Why it matters**: 为什么这是问题
- **Suggestion**: 如何修复
- **Needs experiment?**: yes/no
  - If yes: what experiment and what closure action
- **Priority**: HIGH/MEDIUM/LOW

严重度定义：
- CRITICAL: 审稿人会因此拒稿
- MAJOR: 审稿人会给低分但不一定拒
- MINOR: 可接受但不完美
- NIT: 吹毛求疵
```

6 个 reviewer 角色及其侧重：

| Role | 侧重 |
|------|------|
| quantization_theorist | 量化数学、scale/zero-point 正确性、理论基础 |
| systems_efficiency | Triton kernel、TPOT 测量、显存分析、BitDecoding 对比 |
| nlp_evaluation | Needle/LongBench/RULER 评测设计、数据集选择、metric 定义 |
| statistical_methods | Bootstrap CI、BH-FDR、样本量、置信度计算 |
| academic_writing | 语言风格、AI 痕迹、段落节奏、用词准确 |
| narrative_logic | Claim-Finding-Evidence 链条、跨章节一致性、RQ 回答度 |

### Step 3.3: 汇总意见到 expert_reviews.md

**去重**：多个 reviewer 可能提出相同的 issue，按 file+location+observation hash 去重。

**排序**：按 severity × frequency 排序。被多个 reviewer 同时提出的 issue 优先级提升。

**分类**：
- **需修改不需实验**：流入 Phase 4a 立即处理
- **需要补实验**：流入 Phase 5 进入 rerun_queue
- **需要进一步调研**：流入下一轮 Phase 1

输出模板：

```markdown
# Expert Reviews — Round N

Generated: YYYY-MM-DD HH:MM
Reviewers: Codex + 6 sub-agents

---

## Executive Summary

| Severity | Count | Consensus (≥3 reviewers) |
|----------|-------|--------------------------|
| CRITICAL | 2 | 1 |
| MAJOR | 8 | 3 |
| MINOR | 15 | 5 |
| NIT | 7 | 0 |

**Top 5 Priority Issues (consensus from multiple reviewers)**:

1. **[CRITICAL] [NARRATIVE]** Abstract fails to highlight C5 contribution
   - Raised by: Codex, narrative_logic, academic_writing
   - Suggested fix: ...

2. ...

---

## Detailed Issues by Reviewer

### Codex Review (N issues)
<合并 Codex 的输出>

### quantization_theorist (N issues)
<合并该 reviewer 的输出>

### systems_efficiency (N issues)
...

### nlp_evaluation (N issues)
...

### statistical_methods (N issues)
...

### academic_writing (N issues)
...

### narrative_logic (N issues)
...

---

## Cross-Reviewer Consensus

Issues raised by ≥3 reviewers (highest priority for Phase 4):

1. Issue ID: CONS-001
   - Description: ...
   - Raised by: Codex, academic_writing, narrative_logic
   - Severity: CRITICAL
   - Action: Phase 4a immediate revision

2. ...

---

## Experiment Queue Candidates

Issues requiring empirical data (flowing to Phase 5):

1. EXP-001: Reviewer quantization_theorist 要求补 INT4 symmetric vs asymmetric 对 scale range 的数学上界对比
   - Motivation: 支撑 C3 Key 主导诊断的数学基础
   - Proposed experiment: 计算 K 张量的通道间 variance ratio
   - Closure action: ch3 添加 Lemma + 附录证明

2. ...

---

## Stats

- Total issues: 32
- Issues with consensus (≥3 reviewers): 9
- Issues needing experiments: 2
- Issues resolvable in Phase 4a: 23
```

### Step 3.4: 更新 state

- 新增 experiments 到 `state/rerun_queue.json`
- 新增 issue 到 `state/known_issues.md`

---

## 重要约束

1. **真正并行**：6 个 reviewer 必须在同一个 message 中并行启动，不得串行
2. **独立性**：reviewer 之间不共享信息，模拟真实 blind review
3. **诚实严苛**：reviewer prompt 中要求"假设你是一位严苛的 area chair"
4. **分歧保留**：reviewer 之间的意见分歧也要记录，不强行合并
5. **时间盒**：60 分钟（并行执行所以可达）

---

## 与其他 phase 的交接

- **输入←Phase 2**：paper_review.md 作为 reviewer 的初始输入
- **输出→Phase 4**：consensus issues 作为修改的主输入
- **输出→Phase 5**：experiment queue candidates
- **输出→状态**：rerun_queue.json, known_issues.md
