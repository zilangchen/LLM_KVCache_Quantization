# Closed Comments — Resolved reviewer issues

> Log of reviewer issues that have been successfully addressed (either by direct revision in Phase 4 or by experiment closure in Phase 0).

---

## How to read this file

Each entry follows:
```
### CC-NNN [SEVERITY] [TYPE] <short title>
- Raised in: Round N, Phase X (e.g., Round 1, Phase 3 expert_reviews)
- Raised by: <reviewer role or Codex>
- Closed in: Round M, Phase Y (e.g., Round 2, Phase 4a)
- Closure commit: <hash>
- Resolution: ...
```

---

## Closed Issues Log

### CC-001 [MAJOR] [CONTENT] inv_tau 从"废弃组件"重定位为"GQA 尺度依赖的结构性发现"
- Raised in: Round 1 (external T3), by user + 内部核查阶段
- Closed in: Round 1, Phase 4 (T3 external batch)
- Closure commit: `2f65927` refactor(thesis): reposition inv_tau as diagnostic framework byproduct (ch3+ch4)
- Resolution: ch3 section 标题 / figure caption / paragraph 标题 / "首次"降调 / KIVI 对比表 cell / intuitive argument 标注全部同步；由 "abandoned optional enhancement" 改为 "diagnostic framework byproduct"。

### CC-002 [MAJOR] [CONTENT] Contribution 5（C5）新增：inv_tau × GQA diagnostic byproduct
- Raised in: Round 1 (external T4), by user
- Closed in: Round 1, Phase 4 (T4 external batch)
- Closure commit: `dac154f` feat(thesis): add Contribution 5 (inv_tau x GQA diagnostic byproduct)
- Resolution: ch1 Intro 新增 C5 贡献段 + ch4 discussion 发现五 + E16 验证表行同步升级。采纳评审 A 的"意外发现"措辞以避免贡献膨胀。

### CC-003 [MAJOR] [LANGUAGE] Abstract 双语插入 GQA 尺度依赖段
- Raised in: Round 1 (external T5), by user
- Closed in: Round 1, Phase 4 (T5 external batch)
- Closure commit: `847eb11` docs(thesis): abstract bilingual update with inv_tau x GQA finding
- Resolution: abstract_en.tex + abstract_zh.tex 插入 GQA 尺度依赖段；keywords 扩展。

### CC-004 [MAJOR] [CONTENT] Ch5 发现段从 3 升级为 4（新增发现四）
- Raised in: Round 1 (external T6), by user
- Closed in: Round 1, Phase 4 (T6 external batch)
- Closure commit: `a5a53f6` refactor(thesis): upgrade ch5 findings from 3 to 4 (add diagnostic byproduct)
- Resolution: ch5 Findings 从 3 条升级为 4 条，新增 Finding 4 = diagnostic byproduct；方法论启示从"双重功能"升级为"三重功能"。

### CC-005 [MAJOR] [DATA] 数据同步 + FP8 统一 + cs=1 limitations + 8B INT8 v1 校准异常披露
- Raised in: Round 1 (external T7 + 评审 A 反馈), by user + 评审 A
- Closed in: Round 1, Phase 4 (T7 external batch)
- Closure commit: `a81a8bc` fix(thesis): data sync + FP8 unification + cs=1 limitations + 8B INT8 disclosure
- Resolution: n=10 seeds 具体 PPL 数据、KIVI residual 核查、FP8 ch2/ch5 统一、ch2 措辞降调、cs=1 敏感性披露、8B INT8 v1 校准异常主动披露。

### CC-006 [MINOR] [LANGUAGE] 清理 ch3 + ch5 残留"可选增强"wording
- Raised in: Round 1 (external T8 QC), by internal grep
- Closed in: Round 1, Phase 4 (T8 external batch)
- Closure commit: `f216143` fix(thesis): clean up residual "可选增强" wording in ch3 + ch5 clarification
- Resolution: grep 清零"可选增强"、"四项贡献"、"双重功能"、"optional enhancement"。

### CC-007 [MINOR] [CONTENT] T7 follow-up — BA percentile 桥接句 + int4_fused 脚注
- Raised in: Round 1 (external T7 follow-up), by user review
- Closed in: Round 1, Phase 4 (T7 follow-up external batch)
- Closure commit: `b01eee4` docs(thesis): T7 follow-up — BA percentile clarification + int4_fused footnote
- Resolution: BA percentile 桥接句（提醒读者仍是 KL 目标下的搜索参数化）+ int4_fused 反直觉脚注。
