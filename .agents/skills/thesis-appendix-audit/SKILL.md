---
name: thesis-appendix-audit
description: Use when auditing, restructuring, merging, downgrading, deleting, or cross-reference-checking thesis appendix content, especially when appendix material may overlap with正文, historical results, figures, or source-of-truth chapter narratives.
---

# Thesis Appendix Audit

Use this skill for thesis appendix review and cleanup tasks, including:

- 审查 appendix 是否过重、重复、冲突或历史遗留
- 判断某个 appendix 是否应保留、合并、降级、删除或移回正文
- 同步正文对 appendix 的显式 `\ref{}` 与自然语言引用
- 处理 appendix 图表表格化、文字化或机制归并

## Core Principles

1. **Read before deciding.** First understand the current正文主线、chapter source-of-truth, and appendix structure.
2. **Classify before editing.** Every appendix item must have a role: audit, configuration, mechanism, provenance, historical, or exploratory.
3. **Discuss uncertainty.** If deletion, downgrading, merging, or正文引用 changes are not obvious, list uncertainties and get approval.
4. **One group at a time.** Avoid giant appendix diffs; complete one coherent group, verify, then continue.
5. **Do not leak internal engineering names.** Paper-facing text must not expose temporary paths, backend process names, pins, or provenance details unless explicitly approved as reproducibility material.
6. **Use positive, bounded academic phrasing.** Exploratory or boundary results should be framed as scope, evidence, or future-work seeds, not as negative verdicts.

## Required Workflow

### Phase 0: Read-only Audit

Before editing:

1. List all appendix sections and labels.
2. Search正文 and appendix for:
   - `sec:app-`
   - `fig:app-`
   - `tab:app-`
   - natural-language appendix numbering such as `附录 A.` / `Appendix A.`
3. For each item, identify:
   - corresponding正文 section
   - whether正文 already absorbs the material
   - whether the appendix conflicts with current wording
   - whether it is audit, configuration, mechanism, provenance, historical, or exploratory material

### Phase 1: Audit Matrix

Use this matrix before proposing edits:

| Appendix item | Current topic | Role |正文引用 |正文 location | Duplicate? | Conflict? | Retention value | Recommended action |
|---|---|---|---|---|---|---|---|---|

Allowed actions:

- `保留`
- `保留但降级`
- `移回正文`
- `改写后保留`
- `合并到其他附录`
- `删除`

### Phase 2: ExecPlan Gate

Before any file edits, produce an ExecPlan with:

- problem statement
- alignment with `objective.md` and chapter story
- goals and non-goals
- file-level worklist
- acceptance criteria
- verification commands
- risks and rollback
- explicit questions for uncertain items

Wait for user approval.

### Phase 3: Execute in Small Units

For each approved unit:

1. Modify only the approved appendix group and required正文 references.
2. Keep audit materials such as protocols, environments, reproduction entries, and schemas unless the user explicitly approves removal.
3. Keep mechanism anchors such as theoretical derivations, diagnostic figures, and explanatory tables if正文 depends on them.
4. Downgrade historical or exploratory material without turning it into a main contribution.
5. Preserve stable labels when possible; if a section is downgraded to a paragraph, use `\phantomsection` before its label when the label may still be referenced.

## High-risk Guardrails

- Do not remove audit material merely because正文 does not cite it.
- Do not downgrade mechanism material in a way that weakens正文 explanation.
- Do not turn Prompt-Adaptive, learned allocation, or other exploratory results into Ch4 main results.
- Do not write official LongBench sanity checks as broad generalization claims.
- Do not use old natural-language appendix numbers after reordering sections.
- Do not mix appendix cleanup commits with figure-redrawing or unrelated chapter edits.

## Verification Checklist

Run targeted checks after each unit:

```bash
rg -n 'sec:app-|fig:app-|tab:app-' thesis/chapters
rg -n '附录 A\.|附录 B\.|Appendix A\.|Appendix B\.' thesis/chapters
rg -n 'Phase [0-9]|Gate [A-Z]|final-ready|Level-5|frozen story|clean-provenance|pin=|ddada19|results/' thesis/chapters/appendix.tex
git diff --check -- thesis/chapters/appendix.tex thesis/chapters/ch*.tex
cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex
```

For completed appendix units, prefer full compile:

```bash
cd thesis
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
rg -i 'undefined|multiply defined|LaTeX Error|! ' main.log | head -20
pdfinfo main.pdf | rg Pages
```

## Review Angles

For substantial appendix edits, use independent review passes:

- **Structure and references:** labels, numbering, float order,正文 cross-references.
- **Narrative consistency:** no claim expansion, no conflict with chapter scope.
- **Appendix function:** every retained item serves audit, mechanism, provenance, boundary, or future-work support.
- **Academic expression:** positive, bounded, no internal engineering leakage.

## Reporting Format

When reporting appendix audit results, use:

1. 当前附录总体判断
2. 附录审核矩阵摘要
3. 高风险冲突
4. 下一步执行建议
