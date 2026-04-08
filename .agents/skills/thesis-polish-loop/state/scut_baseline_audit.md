# SCUT Baseline Audit — Round 0

> 本文档由 `thesis-polish-loop` skill 在 Round 0 生成，作为后续所有轮次 Phase 4b 格式校验的参照基线。

**Generated**: 2026-04-08 12:46:22
**Worktree**: `/Users/chenzilang/Desktop/LLM_KVCache_Quantization.polish`
**Branch**: `thesis-polish-v1`
**Thesis HEAD**: `dbfefe9` (tag: `thesis-polish-baseline`)
**SCUT Regulation**: 华南理工大学本科毕业设计（论文）撰写规范（工科、理科类专业）

---

## 概览

**合规状态**：15 项检查中 **9 项完全合规** / **2 项小瑕疵** / **2 项 HIGH 不合规** / **1 项待编译抽检** / **1 项 SKILL 外**

**Round 1 必修**（2 项）：
- KI-001: 中英文摘要段落数不对齐
- KI-002: 关键词数量超上限（7 → 3-5）

**Round 1-2 处理**（1 项）：
- KI-003: 2 处 `EVL-047` 内部 id 泄漏

**编译后抽检**（2 项）：
- KI-005: 章节命名渲染为"第X章 XXX"的样式
- KI-006: `gbt7714-numerical` bib style 输出是否完全符合 GB/T 7714

**SKILL 外**（1 项）：
- PL-001: 外文翻译 ≥5000 字独立附件

---

## 详细检查表（15 项）

| # | 检查项 | SCUT 规范 | 实际状态 | 判定 | 证据 |
|---|--------|----------|---------|------|------|
| 1 | 中文摘要字数 | 400-600 字 | 569 中文字符 | ✅ | `wc` on `abstract_zh.tex` |
| 2 | 中英文摘要对齐 | 内容完全一致 | EN 6 内容段 vs ZH 4 内容段 | ❌ HIGH | 段落切分统计 |
| 3 | 关键词数量 | 3-5 个 | 7 个（EN/ZH 均） | ❌ HIGH | `abstract_en:66`, `abstract_zh:50` |
| 4 | 正文总字数 | ≥15,000 字 | 32,266 中文字符（ch1-5） | ✅ | `wc` + Chinese char filter |
| 5 | 章节命名 | "第一章/二章..." | `\chapter{绪论}` (依赖 ctexbook) | ⚠️ 待编译确认 | grep `\chapter{`, main.tex 有 `chapter` 选项 |
| 6 | 图表按章编号 | 图X-Y / 表X-Y | `setup/format.tex` 已配置短横线按章 | ✅ | `setup/format.tex:45-47` |
| 7 | 参考文献总数 | ≥10 | 62 | ✅ | `grep -c @article/@inproceedings references.bib` |
| 8 | 外文参考文献 | ≥2 | 62（全英） | ✅ | Python Unicode title check |
| 9 | 参考文献格式 | 符合 GB/T 7714 | `\bibliographystyle{gbt7714-numerical}` | ✅ | `setup/packages.tex:50` |
| 10 | 页眉奇偶页 | 偶:华工标题 / 奇:章名 | `\fancyhead[CE/CO]` 正确配置 | ✅ | `setup/header.tex:22-23` |
| 11 | 页码两套 | 前置罗马 + 正文阿拉伯 | `\frontmatter` + `\mainmatter` | ✅ | `main.tex:27,42` |
| 12 | 页面边距 25mm | 上下左右 25mm | `\geometry{top/bottom/left/right=25mm}` | ✅ | `setup/header.tex:8-13` |
| 13 | 字号字体 | 一级小二黑/二级小三黑/三级四号黑/正文小四宋 | `setup/format.tex` 全部符合 | ✅ | `setup/format.tex:17,26,32,38` |
| 14 | 无开发细节泄漏 | 无内部 tracker id | 2 处 `EVL-047`（ch4:337, appendix:382） | ⚠️ MED | `grep EVL- chapters/*` |
| 15 | 外文翻译 ≥5000 字 | 独立附件 | 不在论文主体 | ⏸ SKILL 外 | PL-001 |

---

## 字数分布（按章）

| 章节 | LaTeX words | 中文字符 | 备注 |
|------|------------|----------|------|
| `abstract_en.tex` | 432 | — | 英文摘要 |
| `abstract_zh.tex` | 147 | **569** | 中文摘要，擦边 400-600 |
| `ch1_introduction.tex` | 632 | 2,723 | 绪论 |
| `ch2_related_work.tex` | 1,858 | 6,632 | 相关工作 |
| `ch3_method.tex` | 3,583 | 7,532 | 方法 |
| `ch4_experiments.tex` | 6,246 | **12,149** | 实验（最大） |
| `ch5_conclusion.tex` | 829 | 3,230 | 结论 |
| `appendix.tex` | 3,643 | 4,560 | 附录 |
| `acknowledgements.tex` | 22 | ~50 | 致谢 |
| **正文（ch1-5）合计** | **13,148** | **32,266** | 远超 SCUT 15,000 要求 |

---

## 图表分布（按章）

| 章节 | Figures | Tables | Labels (fig/tab) |
|------|---------|--------|------------------|
| ch1_introduction | 1 | 0 | 1 |
| ch2_related_work | 0 | 1 | 1 |
| ch3_method | 3 | 3 | 6 |
| ch4_experiments | 7 | 15 | 22 |
| ch5_conclusion | 0 | 0 | 0 |
| appendix | 6 | 13 | 21 |
| **总计** | **17** | **32** | **51** |

---

## 参考文献组成

- **总数**: 62 条
  - 42 `@article`
  - 19 `@inproceedings`
  - 1 `@book`
- **语言**: 全部非中文题名（62 全英）
- **Bib style**: `gbt7714-numerical`（基于中国国标 GB/T 7714，SCUT 依据的参考文献规范）
- **Package**: `natbib` with `[sort&compress]`

---

## LaTeX 配置验证摘要

### main.tex
```
\documentclass[a4paper, zihao=-4, twoside, openany, UTF8, chapter]{ctexbook}
```
- `a4paper` ✅
- `zihao=-4` → 默认正文小四号 ✅
- `twoside` → 启用奇偶页区分 ✅
- `chapter` → 章节级编号 ✅
- `\frontmatter` 切换罗马页码 → `\mainmatter` 切换阿拉伯 ✅

### setup/header.tex（奇偶页 + 边距）
```latex
\usepackage{geometry}
\geometry{
  a4paper,
  top=25mm, bottom=25mm, left=25mm, right=25mm,
  headheight=14pt, headsep=10mm, footskip=10mm,
}
\fancypagestyle{mainmatter}{
  \fancyhead[CE]{\zihao{5}\songti 华南理工大学学士学位论文}
  \fancyhead[CO]{\zihao{5}\songti \leftmark}
  \fancyfoot[C]{\zihao{5}\thepage}
  \renewcommand{\headrulewidth}{1.0pt}
}
```
- 页面边距 25mm ✅
- 偶数页页眉 = 华工标题 ✅
- 奇数页页眉 = 章名 (`\leftmark`) ✅
- 页眉下划线 1.0pt ✅（SCUT 要求 1.0 磅）
- 五号宋体字号 ✅

### setup/format.tex（章节标题字号）
- `\zihao{-2}\heiti\bfseries` → 章：小二号黑体加粗居中 ✅
- `\zihao{-3}\heiti` → section：小三号黑体居左 ✅
- `\zihao{4}\heiti` → subsection：四号黑体居左 ✅
- `\zihao{-4}\heiti` → subsubsection：小四号黑体居左 ✅
- 图表 caption：五号宋体 + 按章短横线编号 ✅

### setup/fonts.tex（CJK 字体）
- macOS: Songti SC + Heiti SC + Kaiti SC
- 其他平台: FandolSong + FandolHei + FandolKai
- 英文: Times New Roman ✅

### setup/packages.tex（核心包）
- 数学：amsmath, amssymb, amsthm, bm
- 图表：graphicx, booktabs, multirow, makecell, tabularx, longtable, threeparttable
- 浮动体：float, caption, subcaption
- 颜色代码：xcolor, listings
- 算法：algorithm, algpseudocode
- 超链接：hyperref
- 参考文献：natbib + gbt7714-numerical
- 绘图：tikz

---

## Active Issues（需要 Round 1+ 处理）

### 🔴 HIGH（2 项，Round 1 必修）

#### KI-001 [HIGH] [CONTENT] 中英文摘要段落不对齐
- **Origin**: Round 0, Phase 0
- **Location**:
  - `thesis/chapters/abstract_en.tex` — 6 个内容段 + keywords
  - `thesis/chapters/abstract_zh.tex` — 4 个内容段 + keywords
- **英文段落切分**:
  1. 问题陈述（context window 扩展 / INT4 失效）
  2. 核心提案（attention-KL 双重角色）
  3. INT4-RoleAlign 贡献
  4. The design of INT4-RoleAlign follows a complete evidence chain...
  5. Beyond this primary design (GQA 尺度依赖)
  6. Results demonstrate...
- **中文段落切分**:
  1. 问题陈述
  2. Attention-KL + INT8 验证 + INT4 诊断（3 个英文段压缩为 1 个）
  3. GQA 尺度依赖
  4. INT4-RoleAlign 核心贡献 + 总结
- **根因**: T5 阶段（叙事升级 Abstract 双语）时，英文版把 GQA 段独立成段，中文版融入前一段，导致结构不对称
- **SCUT 要求**: "英文摘要与中文摘要的内容应完全一致"
- **Proposed action**: Round 1 Phase 4a 重新对齐段落结构（两种选择）：
  - A. 把英文的 Para 3-4 合并为 1 段（对齐中文）
  - B. 把中文的 Para 2 拆分为 3 段（对齐英文）
- **推荐**: 选 B，因为中文现在的段落过于庞大，拆分后更好读
- **Priority**: HIGH

#### KI-002 [HIGH] [FORMAT] 关键词数量超上限
- **Origin**: Round 0, Phase 0
- **Location**:
  - `thesis/chapters/abstract_en.tex:66` —
    `\keywordsen{Large Language Model; Key-Value Cache; Quantization; Behavior-Aligned Calibration; Asymmetric Quantization; GQA Architecture; Temperature Correction}`
  - `thesis/chapters/abstract_zh.tex:50` —
    `\keywordszh{大语言模型；键值缓存；量化；行为对齐校准；非对称量化；GQA 架构；温度校正}`
- **Count**: 7 个（中英对称）
- **SCUT 要求**: 3-5 个
- **根因**: T5 阶段扩展 keywords 时按 EMNLP 风格加到 7 个，未注意 SCUT 3-5 上限
- **Proposed action**: Round 1 Phase 4b 精简为 5 个，候选删除（保留 5 个最核心）：
  - 保留：大语言模型 / 键值缓存 / 量化 / 行为对齐校准 / 非对称量化
  - 删除："GQA 架构"和"温度校正"（这两项属于本文的内部发现，不应作为通用关键词）
- **Priority**: HIGH

### 🟡 MED（1 项，Round 1-2 处理）

#### KI-003 [MED] [FORMAT] 内部 tracker id 泄漏
- **Origin**: Round 0, Phase 0
- **Locations**:
  - `thesis/chapters/ch4_experiments.tex:337` — "其中 CWE 的零通过率已确认为评测缺陷（干扰词频 >> 目标词频，EVL-047）"
  - `thesis/chapters/appendix.tex:382` — "上表数据基于修复前的 CWE 实现（干扰词频高于目标词频约 90 倍，EVL-047）"
- **Description**: `EVL-047` 是项目内部 `review_tracker.md` 的 issue id，对外部读者无意义且暴露内部开发痕迹
- **Proposed action**: Round 1 Phase 4a 改为中性描述
  - 建议：删除括号内的 "EVL-047"，保留 "干扰词频 >> 目标词频" 技术描述即可
- **Priority**: MED

### ⚠️ 待编译抽检（2 项）

#### KI-005 [MED] [FORMAT] 章节命名渲染确认
- **Origin**: Round 0, Phase 0
- **Location**: `thesis/chapters/ch*.tex`
- **Description**:
  - 源码使用 `\chapter{绪论}`, `\chapter{相关工作与技术基础}` 等（只有内容，没有前缀）
  - `ctexbook` 应自动渲染为"第一章 绪论"或"第 1 章 绪论"
  - `main.tex` 的 `chapter` 选项决定章节级编号存在，但具体格式（"第一章"vs"第 1 章"vs"Chapter 1"）需要看 PDF
- **SCUT 要求**: "第一章"、"第二章"（中文数字）
- **Proposed action**: Round 1 Phase 4b 编译 PDF 后视觉检查
  - 若渲染为"第 1 章" → 添加 `\CTEXsetup[number={\chinese{chapter}}]{chapter}` 到 `setup/format.tex`
  - 若已是"第一章" → PASS
- **Priority**: MED

#### KI-006 [LOW→PASS 候选] [FORMAT] 参考文献格式抽检
- **Origin**: Round 0, Phase 0
- **Location**: `thesis/references.bib` (62 entries) + `gbt7714-numerical` style
- **Status**: **大概率合规**——`gbt7714-numerical` 正是基于中国国标 GB/T 7714，SCUT 规范即依据此标准
- **Proposed action**: Round 1 Phase 4b 编译后抽查 3-5 条 `.bbl` 渲染：
  - 期刊格式应为：`[序号] 作者. 题名[J]. 刊名, 年, 卷(期): 页码.`
  - 专著格式应为：`[序号] 作者. 书名[M]. 出版地: 出版单位, 年份: 页码.`
  - 作者数 ≤3 全列，≥4 列前 3 + "等"/"et al"
- **Priority**: LOW（大概率 PASS）

---

## Pending Outside Skill

### PL-001 [HIGH] 外文翻译 5000 字独立附件
- **SCUT 要求**: ≥5 篇外文 + ≥5000 汉字翻译作为单独附件
- **Status**: 不在 skill 自动化范围，需手动准备
- **Notes**: 这是一个独立材料（不属于论文主体），最后补充即可。可挑选本文引用的 5 篇核心外文论文（如 KIVI、KVTuner、BitDecoding、FlashAttention、vLLM 等），分别翻译其 abstract + 关键段落。

---

## Round 1 启动建议

**Chapter Rotation**: R1 聚焦 `abstract_en` + `abstract_zh` + `ch1_introduction`

**Phase 4a 优先级**（可立即修复，无需实验）：
1. KI-001 摘要段落对齐（推荐拆分 ZH Para 2 为 3 段）
2. KI-002 关键词精简到 5 个
3. KI-003 EVL-047 改为中性描述

**Phase 4b 需编译验证**:
4. KI-005 编译 PDF 后检查章节命名渲染
5. KI-006 编译后抽检 3-5 条 bib 渲染

**Phase 1 文献调研**（按 rotation）: R1 = ACL + NeurIPS 各取 10 篇

**Phase 2 论文审查**（按 rotation）: R1 = abstract_en + abstract_zh + ch1_introduction

---

## Compliance Score

**当前基线**:
- **Fully Compliant**: 9/15 (60%)
- **Minor Issues**: 2/15 (13%)
- **HIGH Issues**: 2/15 (13%)
- **Pending Verify**: 2/15 (13%)
- **Out of Scope**: 1/15 (7%)

**Round 1 预期提升**: Fully Compliant 9 → 13+（KI-001, KI-002, KI-003 修复 + 2 项编译验证 PASS）

---

## 结论

论文的 SCUT 合规基础**比预期好很多**——15 项中 9 项完全合规，LaTeX 配置层（字号、字体、边距、页眉、参考文献 bib style）**几乎全部符合华南理工大学规范**。

真正需要人工修改的只有 **3 个小问题**：
1. 摘要段落对齐（Round 1 可修）
2. 关键词数量精简（Round 1 可修）
3. EVL-047 内部 id 清理（Round 1 可修）

**以及 2 项需要编译 PDF 后抽检的项目**（KI-005 章节命名、KI-006 bib 输出格式），这些在 Round 1 Phase 4b 会完成。

这意味着 Round 1 之后，SCUT 格式合规工作基本完成，后续轮次（Round 2+）可以专注于 **EMNLP 投稿质量**（叙事打磨、AI 痕迹消除、专家评审响应）作为主目标。
