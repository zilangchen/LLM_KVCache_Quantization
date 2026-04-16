# 论文终稿审查档案

> **用途**：华南理工大学本科毕业设计（论文）终稿审查的**唯一入口**。
> **计划**：`~/.claude/plans/sparkling-shimmying-yao.md`（Plan v5，已 approved）
> **baseline tag**：`thesis-final-review-baseline`（main @ e379645）
> **snapshot 分支**：`snapshot/pre-thesis-review-2026-04-17`（commit 75635a5）

---

## 审查维度索引

| 维度 | 说明 | 报告路径 | 状态 |
|------|------|---------|------|
| D1 FMT | 格式合规（附件1-3） | [by_dimension/D1_FMT.md](by_dimension/D1_FMT.md) | pending |
| D2 STYLE | AI 痕迹 + 学术文风 + 术语 | [by_dimension/D2_STYLE.md](by_dimension/D2_STYLE.md) | pending |
| D3 DATA | 数据一致性与论证链 | [by_dimension/D3_DATA.md](by_dimension/D3_DATA.md) | pending |
| D4 TECH | 技术严谨性（方法/公式） | [by_dimension/D4_TECH.md](by_dimension/D4_TECH.md) | pending |
| D5 REF | 参考文献合规（GB/T 7714） | [by_dimension/D5_REF.md](by_dimension/D5_REF.md) | pending |
| D6 ATK | 双视角攻击（校方+ARR） | [by_dimension/D6_ATK_panel.md](by_dimension/D6_ATK_panel.md) + [by_dimension/D6_ATK_arr.md](by_dimension/D6_ATK_arr.md) | pending |
| D7 VIS | 图表叙事一致性 | [by_dimension/D7_VIS.md](by_dimension/D7_VIS.md) | pending |

## 核心产出

- [issues.md](issues.md) — 全量 issue 唯一真相源
- [data_ledger.md](data_ledger.md) — D3 数字对账表
- [entry_conflicts.md](entry_conflicts.md) — 新旧数据入口冲突（D3）
- [repro_pack_audit.md](repro_pack_audit.md) — P0.5 复现包审计结论
- [terms_glossary.md](terms_glossary.md) — 术语统一词表
- [changelog.md](changelog.md) — 按 commit 的修改历史
- [final_compliance.md](final_compliance.md) — 交付学校签收表
- [panel_qa.md](panel_qa.md) — 答辩 Q&A 预案

## 合规对照

- [compliance/fuian1_checklist.md](compliance/fuian1_checklist.md) — 附件1 逐条 ✓/✗
- [compliance/fuian2_format_sample.md](compliance/fuian2_format_sample.md) — 附件2 范例要素
- [compliance/gbt7714_ref_check.md](compliance/gbt7714_ref_check.md) — 参考文献
- [compliance/arr2026_checklist.md](compliance/arr2026_checklist.md) — EMNLP ARR

## 阶段进度

- [x] P0 筹备（snapshot 分支 + baseline tag + latexmk + 规范 txt + 目录骨架）
- [ ] P0.5 复现包审计 + Phase 1 疑似 CRITICAL 重核
- [ ] P1 7 维度并行审查
- [ ] P2 汇总去重 + 用户 approve
- [ ] P3 分批修复（P3a CRIT → P3b HIGH → P3c MED → P3d LOW）
- [ ] P4 终审（差量复跑 + bib 全链编译 + 人工抽样）
- [ ] P5 交付（archive/thesis_final_YYYYMMDD/ + tar.gz + checksum）

## Stats（P1 完成后填）

- Total issues: _
- CRITICAL: _ (fixed: _, open: _)
- HIGH: _ (fixed: _, open: _)
- MEDIUM: _
- LOW: _
