---
name: defense-review
description: >
  多角度论文审查。读取 thesis/*.tex，并行启动 6 个专家 Agent（系统架构/NLP/统计/工业/写作/顶会审稿人），
  各自输出结构化评审（评级 + 问题分级 + 应答策略），汇总写入 docs/defense_critique_report.md。
  触发: "审查论文"、"答辩准备"、"defense review"、"/defense-review"。
---

# 多角度论文审查

## 执行流程

### 1. 读取论文
- `thesis/chapters/*.tex` 全部章节
- `thesis/chapters/appendix.tex`

### 2. 并行启动 6 个 Agent

| Agent | 角色 | 审查角度 |
|-------|------|---------|
| 1 | 系统架构教授 | 设计合理性、性能评测公平性、工程成熟度、工业差距 |
| 2 | NLP/ML 教授 | 理论基础、实验科学性、SOTA 对比、贡献新颖性 |
| 3 | 顶会审稿人 | Overall Score、Strengths/Weaknesses、Questions、Recommendation |
| 4 | 数学统计教授 | 公式推导、统计检验、符号一致性 |
| 5 | 工业实践者 | 部署可行性、框架集成、延迟/成本 |
| 6 | 写作教授 | 结构、论证逻辑、AI 痕迹、参考文献 |

### 3. 每个 Agent 输出格式
```
评级: X/10 或 A-F
致命问题: (答辩不通过级)
严重问题: (必须回答)
一般问题: (简要回应)
应答策略: (每个问题附建议)
```

### 4. 汇总
- 追加到 `docs/defense_critique_report.md`
- 提取跨审稿人共识的 TOP 3 问题
- 生成答辩 Q&A 应答策略汇总

## Agent Prompt 模板
每个 Agent prompt 必须包含:
1. 角色设定（"你是一位...方向的教授"）
2. 论文文件路径列表
3. 审查角度（5-6 个具体维度）
4. 输出格式要求
5. "用中文输出。要求最严格、最严厉。"
