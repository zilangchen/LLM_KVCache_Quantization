# Phase 2: Paper Review（逐章论文审查）

> 按章节轮转细读论文，对照 Phase 1 的"优秀叙事模板"给出改进清单。

---

## 输入
- `reports/round_N/literature_summary.md` — 本轮文献调研结果
- `config.yaml` → `phase2_paper_review.chapter_rotation`
- `thesis/chapters/*.tex` — 当前论文状态
- `state/known_issues.md` — 历史待办

## 输出
- `reports/round_N/paper_review.md`

---

## 执行步骤

### Step 2.1: 确定本轮审查范围

根据当前轮次 N，从 `config.yaml` 的 `chapter_rotation` 获取本轮目标章节：

| Round mod 4 | Targets |
|-------------|---------|
| 1, 5, 9, ... | abstract_en.tex, abstract_zh.tex, ch1_introduction.tex |
| 2, 6, 10, ... | ch2_related_work.tex, ch3_method.tex |
| 3, 7, 11, ... | ch4_experiments.tex |
| 0, 4, 8, ... | ch5_conclusion.tex, appendix.tex |

### Step 2.2: 逐段阅读与结构化笔记

对每个目标 .tex 文件：

1. **完整 Read** 该文件（分段如果 > 1000 行）
2. 每段产出一条 review note：
   ```
   File: thesis/chapters/chX.tex
   Paragraph: [L123-L145]
   Summary: 这段讲了 XXX
   Issues:
     - [ ] 叙事：该段先提结论再给证据，与 Phase 1 中 NeurIPS 2024 paper 的"证据→结论"模式相反，读起来有点突兀
     - [ ] 语言：第 127 行 "显著" "明显" 密集出现，疑似 AI 痕迹
     - [ ] 数据：第 135 行引用的 "47.14 ms" 与 ch4:265 一致 ✓
     - [ ] 逻辑：第 140 行的 "因此" 前后因果不成立
   Improvement suggestions:
     - 调整为 "我们观察到 X；这说明 Y"的顺序
     - "显著"→"明确"，"明显"→删掉
     - "因此"改为"一个合理的推测是"
   ```

### Step 2.3: 对照 Phase 1 的叙事模板

对本轮目标章节做"叙事体检"：

1. 引言类（abstract/intro）：
   - 是否用了"反直觉现象"切入（参考文献 70% 模式）
   - 贡献列表是否清晰分层
   - 是否有"承上启下"的段落衔接

2. 相关工作类（ch2）：
   - 是否按维度对比而非时间轴
   - 是否有清晰的"本文差异"声明
   - 参考文献数量是否足够（SCUT ≥10，EMNLP 一般 20-50）

3. 方法类（ch3）：
   - 是否先动机后公式
   - 公式与直觉是否配平衡
   - 图表放置的节奏是否合理

4. 实验类（ch4）：
   - 是否 claim-driven 组织
   - 消融顺序是否从关键到辅助
   - 数据一致性（跨表/跨段）

5. 结论类（ch5）：
   - Findings 是否 RQ-aligned
   - Limitations 是否正向框架（"scope of our claims"）
   - Future work 是否具体而非空泛

### Step 2.4: AI 痕迹检测

参考 `memory/feedback_ai_trace_removal.md` 的原则：

- **不要**机械替换词汇（"显著"→"明显"这种是另一种 AI 模板）
- **要**逐段问："这听起来像一个人类研究者写的吗？"
- 不像的原因可能是：
  - 句式太均匀（每句都 20-30 字）
  - 连接词太机械（"此外"、"然而"、"因此" 密集）
  - 解释太冗余（同一个观点换三种说法重复）
  - 语气太正式（用书面语代替自然表达）

把可疑段落标记在 review note 里，留给 Phase 4c 的 2-agent 交叉审核处理。

### Step 2.5: 一致性检查

对跨章节的数据进行交叉比对：

```bash
# TPOT 数字一致性
grep -n "47\.14\|44\.84\|58\.97\|61\.00" thesis/chapters/*.tex

# Claim 数量一致性（4 还是 5）
grep -n "四项贡献\|五项贡献\|四个 claim\|五个 claim" thesis/chapters/*.tex

# inv_tau 数据一致性
grep -n "10\.58\|10\.41\|7\.58\|8\.03\|6\.92\|7\.16" thesis/chapters/*.tex
```

任何不一致都记到 review note。

### Step 2.6: 输出 paper_review.md

```markdown
# Paper Review — Round N

Generated: YYYY-MM-DD HH:MM
Target chapters: abstract_en.tex, abstract_zh.tex, ch1_introduction.tex

---

## Executive Summary

- 总审查段落数: 45
- 发现 issue 数: 18
  - CRITICAL: 2（叙事逻辑错误 / 数据不一致）
  - MAJOR: 5（改进叙事/消除 AI 痕迹）
  - MINOR: 8（用词/句式）
  - NIT: 3
- 本轮 gap vs 优秀叙事模板：
  - [ ] Ch1 引言未用"反直觉现象"切入
  - [ ] Abstract 段落节奏偏平

---

## 分文件清单

### abstract_en.tex

**Issue AB-1** [MAJOR] [LANGUAGE]
- Location: L47-L54
- Current: "Beyond this primary design, the diagnostic framework also surfaces..."
- Issue: 句式与前面 INT4-RoleAlign 段一模一样（"我们的框架 Y X"），机械感强
- Suggestion: 改写为第一人称口吻 "What we did not expect was that..."

**Issue AB-2** [MINOR] [CONTENT]
- Location: L26-L30
- ...

### ch1_introduction.tex

**Issue C1-1** [CRITICAL] [NARRATIVE]
- Location: L76-L89
- Issue: RQ1-RQ3 的提出顺序与后续 Claim 1-5 的展开顺序不对齐（RQ2 → C3, RQ3 → C4）
- Suggestion: 调整 RQ 的表述顺序，或在贡献段加明确的 "C1 回答 RQ1, C2+C3 共同回答 RQ2, C4 回答 RQ3" 映射

---

## 跨章节一致性

| 数据/概念 | 位置 | 一致性 |
|----------|------|--------|
| TPOT 1.5B INT8 | ch4:265(47.14), ch4:1375(44.84) | ⚠️ 不同 seq_len |
| Claim 数量 | ch1:五项, ch5:四个发现+发现四 | ✅ 一致 |
| ...

---

## AI 痕迹热点段落（移交 Phase 4c）

1. `ch1:L143-149` — 贡献一段落
2. `ch3:L369-372` — inv_tau 开场几句
3. `abstract_en:L17-24` — attention-KL 双重角色描述

---

## 本轮重点改进建议（Top 10，交给 Phase 4）

1. ...
2. ...
```

---

## 重要约束

1. **每段都必须有 review note**（即使是"looks good"）
2. **不要提出修改建议，只提出问题和方向**（实际修改在 Phase 4）
3. **保持批判性**：即使上轮审查过的段落，本轮也要重新看
4. **关注叙事 > 关注拼写**：拼写错误可以批量修，叙事问题是 skill 的核心价值
5. **时间盒**：不超过 60 分钟

---

## 与其他 phase 的交接

- **输入←Phase 1**：引用 literature_summary.md 的叙事模板
- **输入←Phase 0**：known_issues.md 中可能有需要在本次审查中验证的项
- **输出→Phase 3**：reviewer sub-agent 会基于这份 paper_review.md 做深度批评
- **输出→Phase 4**：revision 阶段的主要输入
