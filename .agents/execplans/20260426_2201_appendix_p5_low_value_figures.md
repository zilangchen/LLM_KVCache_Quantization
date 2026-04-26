# ExecPlan: Appendix P5 Low-Value Figure Simplification

## 1. Task Alignment

- Goal: replace three low-necessity appendix figures with compact table/text while preserving the evidence function of the appendix.
- Non-goals:
  - Do not delete figure PDF assets.
  - Do not edit figure-generation scripts.
  - Do not change Chapter 4 claims or any Chapter 4 figure work currently dirty in the worktree.
  - Do not introduce legacy method names or internal runtime/provenance details.
- Background:
  - The appendix currently contains three figures whose visual necessity is low: quality-vs-context, Needle exact-match, and single-sequence TPOT gain.
  - The corresponding information can be represented more compactly as a short table or prose because these materials support boundaries rather than primary claims.

## 2. Constraints

- Use `apply_patch` for manual edits.
- Only modify `thesis/chapters/appendix.tex`, this plan file, and `iteration.md` after validation.
- Keep existing unrelated Chapter 4 figure dirty files out of staging.
- Derive the compact quality table from source CSVs, not from PDF visual inspection.
- Keep current formal narrative names, such as `INT8-Canonical`; do not use legacy names such as AutoK.

## 3. Deliverables

- Files to modify:
  - `thesis/chapters/appendix.tex`
  - `iteration.md`
- Files to add:
  - `.agents/execplans/20260426_2201_appendix_p5_low_value_figures.md`
- Expected outputs:
  - `fig:app-quality-vs-context`, `fig:app-ruler-vs-context`, `fig:app-longbench-vs-context`, `fig:app-needle-exact`, and `fig:app-tpot-gain` removed from active appendix text.
  - New `tab:app-quality-context-summary` table.
  - Throughput and memory appendix figures preserved.

## 4. Acceptance Criteria

- Old low-value figure labels no longer appear in `thesis/chapters`.
- New quality context table compiles and has a stable label.
- Needle exact-match and TPOT gain are represented as text, not new standalone figures.
- `fig:app-throughput-dashboard`, `fig:app-memory-dashboard`, and `fig:app-needle-depth-grid` remain valid.
- LaTeX compile succeeds with no undefined references/citations or rerun warning.

## 5. Execution Steps

1. Extract FP16 and INT8-Canonical quality trend values from source CSVs.
2. Replace quality-vs-context figure block with a compact table.
3. Replace Needle exact-match figure with a prose explanation tied to the depth heatmap.
4. Replace TPOT gain figure with a prose deployment-boundary note.
5. Scan for removed labels and compile.
6. Run multi-angle review: evidence adequacy, label/ref integrity, and scope/claim consistency.
7. Record and commit without staging unrelated files.

## 6. Verification Commands

- `rg "fig:app-quality-vs-context|fig:app-ruler-vs-context|fig:app-longbench-vs-context|fig:app-needle-exact|fig:app-tpot-gain" thesis/chapters`
  - Expected: no matches.
- `rg "tab:app-quality-context-summary|fig:app-throughput-dashboard|fig:app-memory-dashboard|fig:app-needle-depth-grid" thesis/chapters/appendix.tex`
  - Expected: all active labels/references present.
- `git diff --check -- thesis/chapters/appendix.tex .agents/execplans/20260426_2201_appendix_p5_low_value_figures.md`
  - Expected: no whitespace errors.
- `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && xelatex -interaction=nonstopmode -halt-on-error main.tex && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - Expected: compile succeeds.
- `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Overfull|invalid character|multiply defined' thesis/main.log`
  - Expected: no matches.

## 7. Risk Register

- Risk: compact table values are not traceable.
  - Impact: appendix loses auditability.
  - Mitigation: derive values from CSVs and record source in the table note.
- Risk: old figure labels remain in active text.
  - Impact: undefined refs or confusing orphan anchors.
  - Mitigation: run explicit label scans.
- Risk: replacing figures makes evidence too thin.
  - Impact: appendix loses support value.
  - Mitigation: keep endpoint/summary table for quality; keep Needle heatmap and throughput/memory figures.
- Risk: TPOT prose overstates deployment findings.
  - Impact: conflict with Chapter 4 deployment boundaries.
  - Mitigation: phrase TPOT as batch=1 boundary note only.
- Risk: unrelated dirty files enter commit.
  - Impact: review scope becomes ambiguous.
  - Mitigation: explicit staging and inspect cached file list.

## 8. Open Questions

- Approved choice: execute the narrowed plan: A-1 table, A-3 prose, A-4 prose; do not delete PDF assets.
