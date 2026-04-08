# Known Issues — Accumulated across rounds

> Issues identified but not yet resolved. Carry over from round to round.
> Each issue is tagged with originating round and severity.

---

## How to read this file

Each issue follows:
```
### KI-NNN [SEVERITY] [TYPE] <short title>
- Origin: Round N, Phase X
- Location: file:line
- Description: ...
- Why not fixed yet: ...
- Proposed action: ...
```

---

## Active Issues

### KI-001 [HIGH] [CONTENT] 中英文摘要段落不对齐
- **Origin**: Round 0, Phase 0 (SCUT Baseline Audit)
- **Location**:
  - `thesis/chapters/abstract_en.tex` (6 content paragraphs + keywords)
  - `thesis/chapters/abstract_zh.tex` (4 content paragraphs + keywords)
- **Description**: 英文摘要有 6 个内容段（问题/原则/RoleAlign/Evidence 链/GQA 发现/结论），中文摘要只有 4 个内容段（3 个英文段被压缩为 1 个）
- **SCUT Requirement**: "英文摘要与中文摘要的内容应完全一致" (撰写规范 #22)
- **Why not fixed yet**: Baseline audit 阶段只识别问题，不执行修改
- **Proposed action**: Round 1 Phase 4a — 推荐把中文 Para 2 拆分为 3 段（原则、INT8 验证、INT4 诊断），对齐英文结构

### KI-002 [HIGH] [FORMAT] 关键词数量超上限
- **Origin**: Round 0, Phase 0
- **Location**: `abstract_en.tex:66`, `abstract_zh.tex:50`
- **Current count**: 7 个（中英对称）
- **SCUT Requirement**: 3-5 个 (撰写规范 #24)
- **Why not fixed yet**: Baseline audit 不执行修改
- **Proposed action**: Round 1 Phase 4b — 精简为 5 个
  - 保留：大语言模型 / 键值缓存 / 量化 / 行为对齐校准 / 非对称量化
  - 删除：GQA 架构 / 温度校正（本文的内部发现，不应作为通用 keyword）

### KI-003 [MED] [FORMAT] 内部 tracker id 泄漏
- **Origin**: Round 0, Phase 0
- **Locations**:
  - `ch4_experiments.tex:337` ("...EVL-047...")
  - `appendix.tex:382` ("...EVL-047...")
- **Description**: `EVL-047` 是项目 `review_tracker.md` 的内部 issue id，对外部读者无意义且暴露开发痕迹
- **Proposed action**: Round 1 Phase 4a — 删除 "EVL-047" 引用，保留中性技术描述即可

### KI-005 [MED] [FORMAT] 章节命名渲染确认
- **Origin**: Round 0, Phase 0
- **Location**: 所有 `thesis/chapters/ch*.tex`
- **Description**: 源码 `\chapter{绪论}` 依赖 ctexbook 自动编号，需确认是否渲染为 SCUT 要求的"第一章 绪论"而非"第 1 章 绪论"或"Chapter 1"
- **Proposed action**: Round 1 Phase 4b — xelatex 编译后视觉检查 PDF；若非中文数字则添加 `\CTEXsetup[number={\chinese{chapter}}]{chapter}` 到 `setup/format.tex`

### KI-006 [LOW→PASS 候选] [FORMAT] 参考文献 bib 输出格式抽检
- **Origin**: Round 0, Phase 0
- **Location**: `thesis/references.bib` + `gbt7714-numerical` bib style
- **Status**: **大概率已合规**——`gbt7714-numerical` 基于中国国标 GB/T 7714，SCUT 规范即以此为依据
- **Proposed action**: Round 1 Phase 4b — xelatex + bibtex 编译后抽查 3-5 条 `.bbl` 渲染是否符合 SCUT 示例格式

---

## Pending (SKILL 外)

### PL-001 [HIGH] 外文翻译独立附件
- **SCUT 要求**: ≥5 篇外文参考文献 + ≥5000 汉字翻译作为独立附件（不在论文主体中）
- **Status**: 不在 skill 自动化范围，需手动准备
- **Notes**: 建议挑选本文引用的 5 篇核心外文论文（KIVI / KVTuner / BitDecoding / FlashAttention / vLLM 或类似），翻译其 Abstract + 关键段落

---

## Archived Issues (Resolved)

*(empty — moved here when issues are closed in Phase 4a/4b/Phase 0)*
