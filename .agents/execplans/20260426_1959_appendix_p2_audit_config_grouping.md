# ExecPlan: Appendix P2 Audit and Configuration Grouping

## 1. Task Alignment

- Goal: Reorganize Appendix A.1--A.6 into three clearer functional groups: audit protocol, configuration glossary, and calibration audit.
- Non-goals:
  - Do not modify figures, generated plot scripts, or unrelated dirty files.
  - Do not change experiment numbers or expand thesis claims.
  - Do not remove audit fields required for reproducibility.
- Background: Current A.1--A.6 all serve reproducibility, environment, protocol, configuration, and calibration audit needs, but they are split into six peer-level sections.

## 2. Constraints

- Environment constraints: Local LaTeX validation uses `xelatex`; no remote experiment execution is needed.
- Repository constraints: Use `apply_patch` for manual edits; do not stage unrelated dirty files.
- Reproducibility constraints: Preserve all existing compatibility labels for former sections and tables.
- Risk constraints: A.1--A.4 are audit materials and must not be substantially reduced.

## 3. Deliverables

- Files to modify:
  - `thesis/chapters/appendix.tex`
  - `iteration.md` after validation
- Files to add:
  - `.agents/execplans/20260426_1959_appendix_p2_audit_config_grouping.md`
- Expected outputs/artifacts:
  - A.1--A.6 reduced from six sections to three functionally grouped sections.
  - All old labels resolve after compilation.

## 4. Acceptance Criteria

- Functional checks:
  - Former A.1--A.3 become one audit section.
  - Former A.5 remains an independent configuration glossary.
  - Former A.4 and A.6 become one calibration audit section.
- Regression checks:
  - Existing labels for A.1--A.6 and their tables remain present.
  - No unexpected edits to figures, scripts, or unrelated draft files.
- Reproducibility checks:
  - PPL protocol, environment, deterministic settings, script coverage, calibration schema, and search-space fields remain available.
- Documentation checks:
  - Appendix wording clearly distinguishes audit material from thesis main claims.

## 5. Execution Steps

1. Rewrite the A.1--A.6 structure in `appendix.tex` with compatibility anchors.
2. Run targeted label scans and LaTeX smoke validation.
3. Launch read-only Sub-agent review for audit completeness, cross-chapter consistency, LaTeX references, and appendix structure.
4. Fix any confirmed issues, rerun validation, then update `iteration.md`.
5. Commit only the P2 semantic file set.

## 6. Verification Commands

- `git diff --check -- thesis/chapters/appendix.tex iteration.md .agents/execplans/20260426_1959_appendix_p2_audit_config_grouping.md`
- `rg -n 'sec:app-fp16-protocol|sec:app-ppl-baseline-matrix|sec:app-env|sec:app-reproduce|sec:app-calib-schema|sec:app-kv-modes|sec:app-calib-search-space|tab:app-ppl-baseline-matrix|tab:app-env|tab:ch3-kv-modes|tab:app-search-space' thesis`
- `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|LaTeX Error|Citation.*undefined' thesis/main.log`
- `pdfinfo thesis/main.pdf | rg Pages`

## 7. Risk Register

- Risk: Audit fields are accidentally removed.
  - Impact: Reproducibility support weakens.
  - Mitigation: Preserve all protocol, environment, script, schema, and search-space content.
- Risk: Compatibility labels point to stale anchors.
  - Impact: Appendix references become misleading.
  - Mitigation: Place `\phantomsection` anchors before former section paragraphs and compile twice.
- Risk: A.5 loses its glossary role.
  - Impact: Readers lose mapping from thesis names to implementation identifiers.
  - Mitigation: Keep A.5 as a standalone section.
- Risk: `inv_tau` wording drifts back into a main-path component.
  - Impact: Conflicts with Ch3/Ch4.
  - Mitigation: Keep it explicitly diagnostic/history-only.
- Risk: Unrelated dirty files are mixed into the commit.
  - Impact: Review scope becomes unclear.
  - Mitigation: Stage explicit paths only and check `git status --short`.

## 8. Open Questions

- Question: Should A.1--A.6 content be moved into the main text?
  - Option A: Keep in Appendix as audit/configuration support.
  - Option B: Move selected material into Ch3/Ch4.
  - Decision: Option A was approved for P2.
