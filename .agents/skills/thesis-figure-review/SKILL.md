---
name: thesis-figure-review
description: Use when reviewing, redrawing, polishing, or standardizing thesis/paper figures and tables, especially LaTeX/TikZ academic figures that require repeated render-check-improve loops until they reach publication-ready quality.
---

# Thesis Figure Review

Use this skill for论文图表审稿与重绘任务，尤其适用于：

- “审这张图 / 重画这张图 / 精修这张图”
- “让这张图达到可发表水准”
- 需要反复编译、渲染、检查遮挡、字体、箭头、图例、配色的学术图
- 需要在章内职责、正文口径、图面美观之间同时闭环的论文图

## 核心工作流

1. **先明确图的章内职责**
   - 说明这张图表达什么
   - 说明这张图不表达什么
   - 说明它与前后小节如何衔接

2. **只处理一张图**
   - 默认严格单图闭环
   - 用户未通过前，不进入下一张

3. **先做结构判断，再做审美优化**
   - 不先盲目改颜色和圆角
   - 先解决图义、主次关系、阅读顺序

4. **真实编译 + 真实渲染**
   - 不只看 TikZ 源码
   - 必须查看最终 PDF 页面
   - 若预览不是最新页，先修正渲染流程，再继续判断

5. **内部先迭代到“可发表候选版”**
   - 不把半成品直接交给用户
   - 自己先检查遮挡、重叠、字体、配色、图例、箭头、caption

## 强制规范

### 字体

- 英文统一 Times New Roman 风格
- 中文统一宋体系正文风格
- 不滥用 `\texttt{}` 或等宽字体做普通标签

### 文案

- 图内文字必须是论文定稿口吻
- 禁止“旧方案 / 新方案 / 不再 / 改成”这类修稿痕迹
- 术语必须与正文、Draft、Writing 一致

### 视觉

- 低饱和、有质感、克制
- 不发灰、不花、不脏
- 箭头不能压字，图例必须独立清楚
- 数据点标注规则要统一

### 数据

- 同口径优先
- 每条线 / 每个点都要可追溯
- 找不到可靠来源时宁可不画，不得猜值

## 检查清单

交付前至少确认：

- 是否编译通过
- 是否真实渲染
- 是否无文字遮挡或裁切
- 是否无箭头压字或阅读混乱
- 是否字体统一
- 是否达到“愿意直接放入正文”的水平

## 输出格式

每轮汇报默认包含：

1. 变更摘要
2. 渲染预览
3. 如何验证
4. 实际结果
5. iteration / commit / 仓库卫生状态
6. 下一步计划

## 参考

需要完整规则时，读取：

- [thesis_figure_review_and_drawing_sop.md](../../../docs/thesis_figure_review_and_drawing_sop.md)
