# ExecPlan: AIGC-Risk Reduction Thesis Revision

## 1. Problem Statement

The thesis has a 47-fragment AIGC-risk report. The risk is not weak technical content; it is mostly highly smooth academic phrasing, repeated meta-discourse, mirrored Chinese/English abstracts, survey-like related-work paragraphs, and long abstract summaries that do not expose enough authorial decisions, failed alternatives, or evidence anchors.

The expected outcome is a thesis revision that lowers false-positive risk by increasing evidence density, decision traceability, and bounded academic phrasing. This is not a detector-evasion task. The revision must preserve rigor, claims, provenance boundaries, and reproducibility.

This task is needed now because the project has moved from experiment execution to paper writing and freeze. The active execution queue says no new formal experiments remain; the next work is thesis writing, figure/table cleanup, and archival discipline.

## 2. `objective.md` Alignment

- Supports success criteria 1, 2, 3, 4, and 7 in `objective.md`: claims must match evidence, INT8/INT4 boundaries must stay clear, allocation must remain a regime-based interpretation, and provenance discipline must be preserved.
- Does not expand the mainline beyond `objective.md`: no new experiments, no new superiority claim, no upgrade of exploratory branches to final-ready support.
- Uses `docs/thesis_upgrade_live_plan.md` as the live thesis workbench and `docs/mainline_execution_queue.md` as the queue status source. Both indicate the experiment queue is frozen and the remaining workflow is writing/polish.

## 3. Goals And Non-Goals

### Goals

- Create and use branch `codex/aigc-risk-revision-20260501`.
- Isolate the work in a clean worktree so existing untracked files on `main` are not touched.
- Convert the 47-fragment AIGC-risk report into an auditable revision matrix.
- Revise the thesis in small, reviewable milestones.
- Require validation plus multi-agent review before each milestone commit.

### Non-Goals

- Do not push, tag, or open a PR without explicit user approval.
- Do not edit experimental scripts, result files, figure assets, or table data unless a later approved milestone explicitly requires it.
- Do not use random synonym replacement, sentence shuffling, casual phrasing, or detector-evasion tactics.
- Do not change core conclusions or add unsupported claims.
- Do not delete or modify the untracked files currently present in the original `main` worktree.

## 4. Constraints And Assumptions

- Default output and project records are in Chinese unless a file's local style requires English.
- `CLAUDE.md` and `experiment_sop.md` are read-only.
- `iteration.md` is append-only and only records completed facts.
- `review_tracker.md` is the issue tracker; use it only for actual review issues, not as a task plan.
- The user-provided 47-fragment report is the authoritative segment-level input for this task.
- If the report's fragment numbering does not map one-to-one to exact LaTeX paragraphs, record the closest file/section mapping in the matrix before editing.

## 5. Work Items By Milestone

### M0: Branch And Worktree Isolation

- Create worktree `/Users/chenzilang/Desktop/LLM_KVCache_Quantization_aigc_revision`.
- Create branch `codex/aigc-risk-revision-20260501` from current `main`.
- Confirm `git status --short --branch` is clean in the new worktree.

### M1: Baseline Matrix And Execution Records

- Add `docs/aigc_revision_plan_20260501.md`.
- Add `docs/aigc_revision_matrix_20260501.md`.
- Add this ExecPlan under `.agents/execplans/`.
- Record the completed setup in `iteration.md` after validation and review.

### M2: Abstracts

- Edit `thesis/chapters/abstract_zh.tex`.
- Edit `thesis/chapters/abstract_en.tex`.
- Address fragments 1-3.
- Ensure Chinese and English abstracts are not mirrored and both include concrete evidence anchors and limits.

### M3: Chapter 1

- Edit `thesis/chapters/ch1_introduction.tex`.
- Address fragments 4-10.
- Compress generic background and connect the opening directly to decode-stage KV cache pressure and observed INT4 instability.

### M4: Chapter 2

- Edit `thesis/chapters/ch2_related_work.tex`.
- Address fragments 11-19.
- Rewrite survey-like paragraphs into problem/gap/position paragraphs.

### M5: Chapter 3

- Edit `thesis/chapters/ch3_method.tex`.
- Address fragments 20-34.
- Repair extraction-sensitive formula prose, replace long framework summaries with interface/schema/algorithm-centered explanation, and attach mechanism claims to evidence or definitions.

### M6: Chapter 4 And Chapter 5

- Edit `thesis/chapters/ch4_experiments.tex`.
- Edit `thesis/chapters/ch5_conclusion.tex`.
- Address fragments 35-47.
- Split long notes and summaries into evidence-bound minimum claims plus limitations.

### M7: Final Consistency Sweep

- Run terminology, overclaim, internal-name, and LaTeX-reference checks.
- Confirm all 47 matrix rows are resolved.
- Produce final review summary and repository hygiene report.

## 6. Acceptance Criteria

- Every fragment in the 47-row matrix has a final status: `done`, `kept-with-rationale`, or `deferred-with-reason`.
- Every edited claim sentence that uses language like "表明", "说明", "支持", "reveal", "show", or "suggest" has a nearby evidence anchor, table/figure reference, configuration, model/task, or explicit scope limit.
- Before any matrix row can move to `done`, its evidence tier and canonical source must be filled. Any `final-ready` statement must come from the live-plan frozen 5 claims or clean-provenance readout; exploratory material can only be written as preliminary, supporting, or boundary evidence.
- Abstract and 摘要 are no longer sentence-by-sentence mirrors.
- Related work no longer reads as a literature queue; each retained cluster explains the unresolved gap that motivates this thesis.
- No new experiment result, table value, or unsupported conclusion is introduced.
- LaTeX compilation passes.
- Multi-agent review reaches PASS for each milestone before commit.

## 7. Verification Commands

Run the relevant subset for each milestone:

```bash
git status --short --branch
git diff --stat
git diff --check -- <changed-files>
python scripts/review_tool.py phase-gate
cd thesis
latexmk -pdf -halt-on-error -file-line-error main.tex
! rg -n "Undefined control sequence|LaTeX Error|Reference .* undefined|Citation .* undefined|There were undefined references|multiply defined|Rerun to get cross-references right|Label\\(s\\) may have changed" main.log
pdftotext -layout main.pdf /tmp/thesis_main.txt
! rg -n "�|□|\\?\\?|undefined|para:|fig:|tab:" /tmp/thesis_main.txt
make4ht -ux -d /tmp/thesis_html main.tex
! rg -n "�|□|\\?\\?|undefined|para:|fig:|tab:" /tmp/thesis_html
cd ..
rg -n "tmux|rsync|clean_rerun|/root|pin=|AutoDL|backend process|session" thesis/chapters thesis/tables
rg -n "普适最优|全局胜出|赢家|universally|winner|positive case|recovery story" thesis/chapters
```

Expected results:

- Worktree stays on `codex/aigc-risk-revision-20260501`.
- No unexpected dirty files.
- `git diff --check` returns exit code 0.
- `review_tool.py phase-gate` reports no CRITICAL/HIGH blocker.
- `latexmk` exits with code 0 and no undefined references, citations, rerun warnings, duplicate labels, or LaTeX errors.
- PDF/HTML extracted text checks have no untriaged extraction artifacts or raw unresolved labels.
- Overclaim/internal-name scans have no unhandled hits.

## 8. Multi-Agent Review Gate

Each milestone uses a review loop:

1. Local checks: diff, compile, scan, and matrix status update.
2. Parallel reviewer agents:
   - Style/AIGC-risk reviewer.
   - Evidence and claim-boundary reviewer.
   - LaTeX/reference reviewer.
   - Terminology consistency reviewer.
   - For Chapter 3/4 milestones, add technical/provenance reviewer.
3. Consensus gate:
   - PASS from all reviewers permits staging and commit.
   - Any CONCERN/REJECT triggers a patch and another review round.
   - Conflicting reviewer advice is resolved against `objective.md`, current evidence, and user-provided boundaries. If unresolved, stop and ask the user.

## 9. Risk Register

- Risk: existing untracked files in the original `main` worktree leak into commits.
  - Probability: high.
  - Mitigation: use a separate clean worktree; never use `git add .`.
  - Rollback: remove the new worktree/branch only; do not touch original files.
- Risk: revision weakens academic tone.
  - Probability: medium.
  - Mitigation: add evidence and author decision traces rather than casual phrasing.
  - Rollback: revert the milestone commit.
- Risk: revision introduces unsupported claims.
  - Probability: medium.
  - Mitigation: evidence reviewer checks every claim-bearing sentence.
  - Rollback: revert or patch the paragraph before commit.
- Risk: abstract and Abstract become inconsistent after de-mirroring.
  - Probability: medium.
  - Mitigation: add an abstract alignment check in M2 review.
  - Rollback: revert M2.
- Risk: LaTeX references break.
  - Probability: medium.
  - Mitigation: compile after every thesis-source milestone.
  - Rollback: revert the exact milestone commit.
- Risk: the 47 fragments cannot be mapped exactly to source paragraphs.
  - Probability: medium.
  - Mitigation: record approximate mapping and status in the matrix before editing.
  - Rollback: no code rollback needed; update matrix mapping.
- Risk: reviewers disagree on whether a sentence is too generic or too terse.
  - Probability: medium.
  - Mitigation: prefer objective-bound evidence, bounded positive phrasing, and local chapter purpose.
  - Rollback: keep the original sentence with recorded rationale.

## 10. Questions And Defaults

- Branch strategy:
  - Default: isolated worktree on `codex/aigc-risk-revision-20260501`.
  - Alternative: switch the original worktree directly.
  - Decision: use the default because the original `main` worktree has many untracked files.
- Fragment source:
  - Default: use the user-provided 47-fragment report as authoritative input.
  - Alternative: regenerate fragment candidates from the thesis.
  - Decision: use the user report, and only regenerate exact file/line mapping as needed.
- Commit granularity:
  - Default: one commit per milestone after review PASS.
  - Alternative: one large final commit.
  - Decision: use milestone commits for auditability and rollback.
