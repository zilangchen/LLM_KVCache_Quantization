# Phase 1: Literature Scan（文献调研）

> 每轮调研约 20 篇顶级 venue 论文，提取叙事模板和优秀实践供 Phase 2/4 借鉴。

---

## 输入
- `venue_catalog.yaml` — 可选 venue 清单
- `state/venues_read.json` — 已读 venue+year 记录
- 当前轮次号 N

## 输出
- `reports/round_N/literature_summary.md`
- 更新后的 `state/venues_read.json`

---

## 执行步骤

### Step 1.1: 选择本轮 venue 组合
1. 读取 `venue_catalog.yaml` 的 `rotation_strategy.round_N`
2. 读取 `state/venues_read.json`，扣除已读组合
3. 若本轮推荐组合全部已读 → 切换到下一个 priority 的组合
4. 确定本轮目标：2-3 个 venue × 6-10 篇/venue = 约 20 篇

### Step 1.2: 为每个 venue 检索相关论文
对选定的每个 venue：
1. 构造查询：venue 官方名称 + `search_keywords.primary` 中的关键词
2. **WebSearch**：`<venue> <keyword> <year>` 
3. **WebFetch**（若 search 返回结果）：arxiv.org / aclanthology.org / openreview.net
4. 提取每篇论文的：
   - 标题
   - 作者
   - venue + year
   - 摘要
   - 核心贡献（bullet points）
   - 与本文研究的相关性（high/medium/low）

### Step 1.3: 叙事模板提取
对每篇论文，提炼以下叙事要素（这是关键——不只是总结论文本身，更是学习"如何写好论文"）：

1. **引言写法**：
   - 如何切入问题（从宏观到具体？用一个反直觉现象？从一个失败案例？）
   - 如何陈述贡献（列表式？递进式？闭环式？）

2. **相关工作组织**：
   - 按方法分类？按时间轴？按挑战维度？
   - 如何清晰划出与本文的差异

3. **方法描述**：
   - 先原则再细节，还是先动机再公式
   - 公式与直觉如何配合
   - 图表放置的节奏

4. **实验叙事**：
   - Claim-driven 还是 benchmark-driven
   - 如何组织消融实验的顺序
   - 如何引导读者看重点

5. **Limitations / Future Work**：
   - 如何诚实披露而不伤害贡献
   - 如何把未完成的工作写得"有吸引力"

### Step 1.4: 输出 literature_summary.md

```markdown
# Literature Summary — Round N

Generated: YYYY-MM-DD HH:MM
Venues covered: [ACL 2024, NeurIPS 2025]
Papers read: 20

---

## Paper 1: "XXX" (ACL 2024)

**Authors**: ...
**Link**: https://arxiv.org/abs/...
**Relevance**: HIGH — 直接相关

### 核心贡献
- ...
- ...

### 叙事要点
- **Introduction**：用 Figure 1 展示问题现象（INT4 失效），直接切入
- **Contributions bullet**：4 条贡献，每条 1-2 行
- **Method 先讲动机再给公式**，然后配图

### 可借鉴的优点
1. 用"诊断→设计"的递进逻辑组织 Section 3（与我们 5-Claim 相似）
2. Figure 2 的"失败案例→我们的方案"对比很直接
3. Limitations 段用"但是/然而"而非"我们无法"，避免负面语气

### 不适用的点
- 他们用 FlashInfer 做效率对比（我们没法复现）
- 他们的 venue target 是 NeurIPS spotlight，风格更激进

---

[Repeat for Paper 2..20]

---

## 跨篇横向总结

### 共同叙事模式
- 70% 论文在引言使用"反直觉现象+诊断"的切入方式
- 60% 论文在 Method 章用"原则→实例→推广"三段式
- 80% 论文在 Experiments 首段明确 research questions → claims → evidence

### 我们可借鉴的 Top 5 改进机会
1. **引言钩子**：参考 Paper 3 的图 1 用一张"灾难性失效→恢复"的对比图
2. **方法描述节奏**：参考 Paper 7 先给 2 段直觉再给 1 个公式
3. **消融组织**：参考 Paper 12 用 "what if we didn't do X" 反问式标题
4. **Limitations**：参考 Paper 18 的 "scope of our claims" 正向框架
5. **Related Work**：参考 Paper 5 的维度化对比表（而非简单的时间轴）

### 需要借鉴的具体句式
- "Our contributions are threefold: (1) ... (2) ... (3) ..."
- "This observation motivates us to ask: ..."
- "Somewhat surprisingly, we find that ..."
- 避免："extensive experiments demonstrate", "significantly outperform"

---

## 状态更新

- `state/venues_read.json` 新增：
  - ACL: [2024] (已加)
  - NeurIPS: [2025] (已加)
```

### Step 1.5: 更新 venues_read.json
```json
{
  "venues": {
    "ACL": {"years": [2024], "rounds_read": [1]},
    "NeurIPS": {"years": [2025], "rounds_read": [1]}
  },
  "total_papers_read": 20,
  "last_updated_round": 1
}
```

---

## 重要约束

1. **venue 多样性**：每轮尽量不与前 1-2 轮重复相同 venue+year 组合
2. **相关性过滤**：单纯的文献综述不计入（只算 relevance≥medium 的论文）
3. **深度 > 广度**：20 篇中至少 5 篇需要做深度叙事分析（不只是摘要）
4. **引用追踪**：如果 Phase 2/4 后续需要引用某篇，必须先在 Phase 1 中阅读过
5. **时间盒**：单 phase 不超过 60 分钟
6. **失败回退**：若 WebSearch/WebFetch 连续失败 → 降级为"仅读已有 related work"，下一轮重试

---

## 与其他 phase 的交接

- **输出→Phase 2**：paper_review.md 需对照 literature_summary.md 的"优秀叙事模板"
- **输出→Phase 4**：revision 阶段可引用新发现的论文（更新 bib 文件）
- **输出→Phase 3**：reviewer 在审查时可对比"文献是怎么做的 vs 我们是怎么做的"
