---
name: thesis-polish-loop
description: >
  24-hour continuous thesis polishing loop targeting EMNLP-submission quality.
  Each round runs 6 phases: housekeeping → literature → paper review → expert
  reviews (Codex + 6 reviewer sub-agents) → revision → experiment triggers.
  State persists across rounds via state/ directory. Triggered externally by
  schedule skill every ~90 minutes. Primary goal: EMNLP-level quality; secondary
  goal: SCUT undergraduate thesis format compliance (handled in Phase 4b).
---

# Thesis Polish Loop Skill

> 论文持续打磨循环：以 EMNLP 投稿质量为主目标，SCUT 毕设格式为次目标。
> 每轮 6 phase 闭环，跨轮次状态机驱动，schedule 外部触发。

---

## 触发方式

### 手动触发（单轮）
```
/thesis-polish-loop          # 执行一轮，然后退出
/thesis-polish-loop --dry    # 只 planning 不实际修改
```

### 定时触发（24h 循环）
```
# Setup 阶段（只做一次）
/schedule create "thesis-polish" "*/90 * * * *" "/thesis-polish-loop"

# 启动后：每 90 分钟新启一个 Claude Code session 运行本 skill 一轮
```

---

## 单轮执行协议（6 Phase + Step 0 Housekeeping）

每一轮**必须**依次执行以下 phase，不得跳过。每个 phase 的详细指令在 `phases/` 目录：

### Step 0: Housekeeping （闭环回填）
→ `phases/phase0_housekeeping.md`

扫描 `state/running_experiments.json`，检查上轮触发的实验是否完成：
- **已完成** → 读 CSV + 执行 closure_action + 更新论文 + commit
- **未完成** → 保持 running 状态等下一轮
- **超时 >3 轮** → 写入 `state/known_issues.md` 作为"待补充实验"

### Phase 1: Literature Scan
→ `phases/phase1_literature.md`

- 读 `state/venues_read.json`，选 10 venue × 2 paper = 20 篇
- 覆盖 ACL/EMNLP/NAACL/NeurIPS/ICML/ICLR/TMLR/TACL/COLM/COLING
- WebSearch + WebFetch 获取摘要/关键段
- 按 venue 分组总结：叙事逻辑 / 核心贡献 / 优点
- 输出 `reports/round_N/literature_summary.md`
- 更新 `state/venues_read.json`

### Phase 2: Paper Review
→ `phases/phase2_paper_review.md`

按 round 编号轮转章节：
- R1, R5, R9, ... : Abstract + ch1
- R2, R6, R10, ...: ch2 + ch3
- R3, R7, R11, ...: ch4
- R4, R8, R12, ...: ch5 + appendix

逐段对照 Phase 1 的"优秀叙事模板"，检查：
- 叙事逻辑是否最优
- 语言是否有 AI 痕迹（参考 `feedback_ai_trace_removal.md` 原则）
- 与其他章节的一致性
- 数据引用是否准确

输出 `reports/round_N/paper_review.md`

### Phase 3: Expert Reviews
→ `phases/phase3_expert_reviews.md`

**串行**：先启动 Codex 审查
```
/codex:review
```

**并行**：启动 6 个 sub-agent reviewers（每个独立审查）：
- quantization_theorist
- systems_efficiency
- nlp_evaluation
- statistical_methods
- academic_writing
- narrative_logic

汇总所有意见到 `reports/round_N/expert_reviews.md`，按严重度排序，标记：
- `[LEVEL]` CRITICAL / MAJOR / MINOR / NIT
- `[TYPE]` CONTENT / DATA / FORMAT / LANGUAGE
- `[NEEDS_EXP]` true / false（若 true 则进入 rerun_queue）

### Phase 4: Revision
→ `phases/phase4_revision.md`

**三阶段子流程**：

- **4a. 内容修改**：针对不需实验的 comment 立即修改论文
- **4b. SCUT 格式校验**：字号/章节命名/图表编号/参考文献格式的校验与修正
- **4c. 交叉审核 + AI 痕迹消除**：每段修改启动 2 个 sub-agent（"人类读者" + "AI 痕迹检测器"），两者都 PASS 才通过

每个 milestone 独立 commit，更新 `state/known_issues.md`，验证 xelatex 编译。

### Phase 5: Experiment Triggers
→ `phases/phase5_experiments.md`

- 扫描 Phase 3 中标记 `[NEEDS_EXP]` 的 comment
- 为每个生成 `rerun_queue.json` 条目（含 motivation / original_target / closure_action）
- 远端 tmux session 启动实验（不等待结果）
- 更新 `state/running_experiments.json`
- 输出 `reports/round_N/experiments_triggered.md`

### Step F: Round 收尾

1. 更新 `state/round_counter.json`
2. 追加 `iteration.md` Timeline 条目
3. Commit: `chore(thesis-polish): Round N summary`
4. 退出，等待 schedule 下次触发

---

## 核心约束与安全边界

1. **Worktree 隔离**：所有论文修改在 `thesis-polish-v1` worktree 中进行，main 分支只接收 skill 更新
2. **每轮时间盒**：单轮不超过 5 小时，超时则中断并记录 checkpoint
3. **Commit 粒度**：每个 milestone 独立 commit，保持可回退
4. **不破坏主分支**：skill 本身不 push 到 remote，用户手动控制
5. **实验闭环**：任何补跑实验必须有明确 motivation 和 closure_action，防止孤儿数据
6. **AI 痕迹检测**：修改后必须通过 2-agent 交叉审核才算完成
7. **格式验证**：每轮 Phase 4b 运行 xelatex 编译 + grep 一致性检查
8. **资源上限**：Phase 1 文献调研单轮不超过 20 篇；Phase 3 reviewer 不超过 6 + Codex；Phase 5 实验不超过队列前 3 个

---

## 状态文件清单

| 文件 | 用途 | 生命周期 |
|------|------|---------|
| `state/round_counter.json` | 当前轮数 + 起止时间 | 永久 |
| `state/venues_read.json` | 已读刊物清单（venue→years） | 永久 |
| `state/rerun_queue.json` | 实验闭环队列 | 永久 |
| `state/running_experiments.json` | 当前 Running 实验 | 跨轮 |
| `state/known_issues.md` | 累积待办清单 | 永久 |
| `state/closed_comments.md` | 已闭环 reviewer 意见 | 永久 |
| `state/ai_trace_audit.md` | AI 痕迹审计记录 | 永久 |
| `state/scut_baseline_audit.md` | SCUT 合规扫描结果 | 永久（Round 0 生成） |
| `state/last_checkpoint.json` | 本轮中断点 | 本轮 |

---

## 退出条件

- **自然退出**：完成 24 轮（约 36 小时）后自动停止
- **质量阈值**：连续 3 轮 0 CRITICAL 0 MAJOR 意见则停止
- **硬停止**：用户手动 `/thesis-polish-loop --stop`
- **故障停止**：同一 phase 连续 3 轮失败
- **时间限制**：超过真实时间 24 小时

---

## 术语速查

- **Round / 轮次**：一次完整的 6-phase 执行
- **Venue**：顶级会议（ACL/EMNLP/NeurIPS 等）
- **Closure Action**：实验完成后对论文的回填动作
- **Baseline Audit**：Round 0 的 SCUT 合规扫描
- **Chapter Rotation**：每轮轮转审查的章节范围
- **AI Trace**：AI 生成文本的机械化模式（参考 `feedback_ai_trace_removal.md`）

---

## 与其他 skills 的协作

- **$codex-review**：Phase 3 的 Codex 审查入口
- **$long-running-task**：Phase 5 的远端实验触发
- **$unit-commit**：每个 milestone 的 commit 规范
- **$repo-hygiene**：commit 后确认工作树干净
- **$defense-review**：Phase 3 的答辩风格 reviewer（可选）

---

## 完整执行协议参考

- Stage 1 基线扫描：见 `phases/phase0_housekeeping.md` 的 "Round 0" 部分
- 每 phase 详细指令：见 `phases/phase*_*.md`
- Reviewer prompt：见 `reviewer_templates/*.md`
- 配置：见 `config.yaml`
- Venue 清单：见 `venue_catalog.yaml`
