# ExecPlan: Appendix P3 Deployment and Batch Supplement Grouping

## 1. Task Alignment

- Goal: Merge the deployment-efficiency supplement and batch-capacity supplement into one appendix function group.
- Non-goals:
  - Do not modify Chapter 4 figure files, plotting scripts, or current Chapter 4 dirty text.
  - Do not change experiment values.
  - Do not turn appendix-only system readings into main deployment claims.
- Background: Current Appendix A.6 and A.7 both serve Chapter 4 deployment boundary auditing, but they are split into two peer-level sections.

## 2. Constraints

- Environment constraints: Validation uses local `xelatex`; no experiment rerun is needed.
- Repository constraints: Use `apply_patch`; stage explicit paths only.
- Reproducibility constraints: Preserve labels for figures, table, and former section anchors.
- Risk constraints: Current working tree contains unrelated Chapter 4 figure/session dirty files; do not stage them.

## 3. Deliverables

- Files to modify:
  - `thesis/chapters/appendix.tex`
  - `iteration.md` only after validation, if it can be staged without mixing unrelated dirty hunks
- Files to add:
  - `.agents/execplans/20260426_2048_appendix_p3_deployment_batch_grouping.md`
- Expected outputs/artifacts:
  - Current A.6/A.7 become one section with a compatibility anchor for the former batch section.

## 4. Acceptance Criteria

- Functional checks:
  - `sec:app-efficiency-plots` remains a section label.
  - `sec:app-batch-capacity` remains resolvable after being lowered into a paragraph anchor.
  - `fig:app-tpot-gain`, `fig:app-throughput-dashboard`, `fig:app-memory-dashboard`, and `tab:app-batch` remain present.
- Regression checks:
  - No unrelated Chapter 4 figure or script files are staged.
  - No deployment claim is strengthened beyond Chapter 4's H20/backend/batch/seq_len scope.
- Reproducibility checks:
  - The batch table keeps its capacity boundary role and all existing numbers.

## 5. Execution Steps

1. Rename current A.6 to a combined deployment and batch supplement section.
2. Add a short scope paragraph for model, hardware, backend, and batch/seq_len limits.
3. Lower current A.7 into a paragraph with `\\phantomsection` and keep its label.
4. Run label scans, section scans, and LaTeX validation.
5. Launch read-only Sub-agent review across正文 consistency, system-claim boundary, LaTeX refs, and structure redundancy.
6. Fix confirmed issues and then commit only the P3 file set.

## 6. Verification Commands

- `git diff --check -- thesis/chapters/appendix.tex`
- `awk '/^\\\\section/ {if(sec) print NR-start-1\" lines  \"sec; sec=$0; start=NR} END {print NR-start\" lines  \"sec}' thesis/chapters/appendix.tex`
- `rg -n 'sec:app-efficiency-plots|sec:app-batch-capacity|fig:app-tpot-gain|fig:app-throughput-dashboard|fig:app-memory-dashboard|tab:app-batch' thesis`
- `rg -n '推理效率与扩展性补充图表|批处理扩展：已测批量' thesis/chapters/appendix.tex`
- `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|LaTeX Error|Overfull' thesis/main.log`
- `pdfinfo thesis/main.pdf | rg Pages`

## 7. Risk Register

- Risk: The batch table is misread as a main speed claim.
  - Impact: It could conflict with Chapter 4 deployment boundaries.
  - Mitigation: State that it is a capacity and boundary supplement.
- Risk: Lowering A.7 breaks a reference.
  - Impact: Appendix refs may resolve incorrectly.
  - Mitigation: Keep `\\phantomsection` before `sec:app-batch-capacity` and compile.
- Risk: The combined section becomes too broad.
  - Impact: Reader loses the system boundary.
  - Mitigation: Use explicit paragraph headings for single-sequence figures and batch capacity.
- Risk: Unrelated figure-session dirty files are staged.
  - Impact: Appendix commit becomes hard to review.
  - Mitigation: Stage explicit paths only and inspect cached diff.
- Risk: Existing `iteration.md` dirty content overlaps with P3 record.
  - Impact: P3 commit may include unrelated timeline changes.
  - Mitigation: Report before staging if clean hunk staging is not possible.

## 8. Open Questions

- Question: Should Chapter 4 text get a new explicit pointer to this combined appendix section?
  - Option A: Do not modify Chapter 4 in P3 unless a broken reference exists.
  - Option B: Add one sentence in Chapter 4 deployment discussion.
  - Decision: Option A for P3, because Chapter 4 currently has unrelated dirty changes.
