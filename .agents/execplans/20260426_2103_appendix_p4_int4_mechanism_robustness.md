# ExecPlan: Appendix P4 INT4 Mechanism and Robustness Grouping

## 1. Task Alignment

- Goal: group the INT4 mechanism and robustness appendix materials so that scale sensitivity, sequence-length noise intuition, and chunk-size robustness read as one mechanism/boundary supplement rather than three peer sections.
- Non-goals:
  - Do not change experiment numbers.
  - Do not change Chapter 4 claims, figures, or figure-generation files.
  - Do not compress or remove the SQNR / extreme-value derivation.
  - Do not touch Prompt-Adaptive appendix material in this milestone.
- Background:
  - Current Appendix contains separate sections for INT4 scale sensitivity, SQNR sequence-length analysis, and chunk-size robustness.
  - The SQNR derivation is the theoretical backbone for Chapter 4's INT4 cliff discussion and must remain intact.
  - K/V ablation and inv_tau / KL-MSE provenance are explicitly referenced from the main text and should remain independent landing points.

## 2. Constraints

- Environment constraints:
  - Work in `/Users/chenzilang/Desktop/LLM_KVCache_Quantization`.
  - Current worktree contains unrelated Chapter 4 figure changes; this plan must not stage or commit those files.
- Repository constraints:
  - Use `apply_patch` for manual edits.
  - Preserve labels: `sec:app-eng066`, `sec:app-sqnr-derivation`, `sec:app-chunksize`, `sec:app-kv-ablation-full`, `sec:app-invtau-diagnostic`, `subsec:app-7b-kl-mse`.
  - Do not use `git add .`.
- Reproducibility constraints:
  - Keep all table values and equations unchanged unless a later review finds a typo.
  - Keep all appendix labels resolvable after LaTeX compilation.
- Risk constraints:
  - Do not weaken the SQNR derivation.
  - Do not move K/V ablation provenance or inv_tau provenance into a less visible location.

## 3. Deliverables

- Files to modify:
  - `thesis/chapters/appendix.tex`
  - `iteration.md` after validation
- Files to add:
  - `.agents/execplans/20260426_2103_appendix_p4_int4_mechanism_robustness.md`
- Expected outputs/artifacts:
  - One grouped INT4 mechanism / robustness appendix section.
  - Existing K/V ablation and inv_tau sections still present as independent sections.
  - Clean LaTeX compile and clean appendix label scan.

## 4. Acceptance Criteria

- Functional checks:
  - Appendix no longer presents scale sensitivity, SQNR derivation, and chunk-size robustness as three peer sections.
  - `sec:app-sqnr-derivation` still lands on the SQNR derivation block.
  - `sec:app-eng066` and `sec:app-chunksize` remain valid anchors.
- Regression checks:
  - No Chapter 3 or Chapter 4 reference becomes undefined.
  - `sec:app-kv-ablation-full`, `sec:app-invtau-diagnostic`, and `subsec:app-7b-kl-mse` remain unchanged as independent landing points.
- Reproducibility checks:
  - No experiment values, seeds, PPL values, or table contents are changed.
  - No internal runtime paths or temporary provenance strings are introduced.
- Documentation checks:
  - `iteration.md` records the P4 action and validation after implementation.

## 5. Execution Steps

1. Convert the current INT4 scale sensitivity section into a grouped INT4 mechanism / robustness section.
2. Keep the scale sensitivity table as the first paragraph-level block with `sec:app-eng066`.
3. Move the SQNR derivation under the same section as a protected paragraph-level block with `sec:app-sqnr-derivation`.
4. Move the chunk-size robustness table under the same section as a paragraph-level block with `sec:app-chunksize`.
5. Leave the K/V ablation and inv_tau / KL-MSE sections independent.
6. Run label scans, LaTeX compile, and multi-agent review.
7. Apply any review-driven corrections that stay inside this P4 scope.
8. Record and commit this functional unit without staging unrelated Chapter 4 figure work.

## 6. Verification Commands

- `git diff --check -- thesis/chapters/appendix.tex .agents/execplans/20260426_2103_appendix_p4_int4_mechanism_robustness.md`
  - Expected result: no whitespace errors.
- `awk '/^\\section/ {if(sec) print NR-start-1" lines  "sec; sec=$0; start=NR} END {print NR-start" lines  "sec}' thesis/chapters/appendix.tex`
  - Expected result: INT4 mechanism materials are grouped into one section.
- `rg -n 'sec:app-eng066|sec:app-sqnr-derivation|sec:app-chunksize|sec:app-kv-ablation-full|sec:app-invtau-diagnostic|subsec:app-7b-kl-mse' thesis/chapters`
  - Expected result: all required labels exist and references remain clear.
- `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && xelatex -interaction=nonstopmode -halt-on-error main.tex && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - Expected result: compile succeeds.
- `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Overfull|invalid character' thesis/main.log`
  - Expected result: no matches.

## 7. Risk Register

- Risk: the SQNR derivation is accidentally shortened.
  - Impact: Chapter 4 loses its mechanism backbone.
  - Mitigation: preserve equations and the `n^*` argument verbatim unless a local wording bridge is needed.
- Risk: labels become paragraph anchors whose `\ref` output is less specific.
  - Impact: references may resolve to the parent section.
  - Mitigation: retain labels and check all current references; if any main-text phrase requires a section-level target, adjust wording only.
- Risk: K/V ablation explicit reference loses its landing point.
  - Impact: Chapter 4 table note becomes unclear.
  - Mitigation: leave `sec:app-kv-ablation-full` as an independent section.
- Risk: inv_tau diagnostic provenance is merged too aggressively.
  - Impact: Ch3/Ch4 source-of-truth boundary becomes weaker.
  - Mitigation: leave `sec:app-invtau-diagnostic` and `subsec:app-7b-kl-mse` independent.
- Risk: unrelated Chapter 4 figure work enters the commit.
  - Impact: review scope becomes ambiguous.
  - Mitigation: use explicit staging and inspect `git diff --cached --name-only`.

## 8. Open Questions

- Approved choice: use Scheme A, grouping A.7 + A.9 + A.10 while keeping A.8 and A.11 independent.
