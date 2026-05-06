# 2026-05-07 | School Format Compliance Fix ExecPlan

## 1. Task Alignment

- Goal: Align the current thesis LaTeX/PDF with the school engineering/science thesis format requirements before the later PDF/LaTeX to Word conversion stage.
- Background: The school folder `docs/school/工科、理科类撰写规范及相关表格模板` contains the 2025-11 writing specification and format sample. A read-only audit found that the current thesis is close structurally, but still fails several explicit format checks: title-class Chinese fonts are Songti-bold instead of Heiti, the table of contents omits front-matter entries, and the Chinese/English keyword lists exceed the required 3-5 terms.
- Objective alignment:
  - Supports the project goal of producing a submission-ready thesis artifact.
  - Stays within paper-format and presentation cleanup; it does not change experimental data, claims, figures, tables, algorithms, or evidence.

## 2. Constraints

- Environment constraints:
  - Current macOS environment has `textutil`, `pandoc`, Poppler PDF tools, and XeLaTeX.
  - LibreOffice/`soffice` is not currently available, so high-fidelity Word rendering is deferred.
- Repository constraints:
  - Current branch is `main`, ahead of `origin/main`.
  - Current worktree already has unrelated dirty files: `iteration.md` and `development_history/iteration_archive_202605.md`. These must not be overwritten or staged accidentally.
  - Use exact staging only; never `git add .`.
- Reproducibility constraints:
  - Compile with XeLaTeX three times after format edits.
  - Verify page count, undefined references/citations, font list, TOC text, and keyword count.
- Risk constraints:
  - Formatting changes may shift page breaks; this is acceptable only if no blank-page regression or broken references appear.
  - School specification overrides the earlier temporary simplification that mapped all Chinese title fonts to Songti.

## 3. Deliverables

- Files to modify:
  - `thesis/setup/fonts.tex`: restore separate Heiti family for title-class Chinese text while keeping body Chinese Songti and English Times New Roman.
  - `thesis/setup/format.tex`: use Heiti for chapter/section/subsection/paragraph headings.
  - `thesis/setup/toc.tex`: use Heiti for TOC title and chapter-level entries.
  - `thesis/setup/commands.tex`: use Heiti for cover labels/titles, declaration titles, abstract titles, and keyword labels; add front-matter TOC entries if best placed in environments.
  - `thesis/main.tex`: add TOC entry for `目录` if this is cleaner than putting it in setup files.
  - `thesis/chapters/abstract_zh.tex`: reduce Chinese keywords to 3-5 terms.
  - `thesis/chapters/abstract_en.tex`: reduce English keywords to match the Chinese keyword set.
  - `iteration.md`: append a short record only after successful validation, while preserving existing dirty content.
- Files to add:
  - None expected beyond this ExecPlan.
- Expected outputs/artifacts:
  - Updated `thesis/main.pdf`.
  - Clean LaTeX compile log with no undefined references/citations.
  - A concise final compliance summary.

## 4. Acceptance Criteria

- Functional checks:
  - Body Chinese remains Songti; English remains Times New Roman.
  - Title-class Chinese text uses Heiti where the school specification requires it.
  - Chinese and English keywords each have 3-5 terms and correspond semantically.
  - TOC includes `摘要`, `Abstract`, `目录`, body chapters, conclusion, references, appendix, and acknowledgements.
- Regression checks:
  - Page 8 remains nonblank and starts/continues the main body correctly.
  - No newly introduced `RQ1/RQ2/RQ3/RQ4` paper-facing text.
  - No AIGC/Codex/Claude/internal workflow terms leak into paper-facing files.
- Reproducibility checks:
  - XeLaTeX runs three times successfully in `thesis/`.
  - `main.log` has zero undefined reference/citation warnings.
  - `pdffonts thesis/main.pdf` shows body Songti/Times and title-class Heiti usage; any residual nonconforming fonts must be traceable to embedded external figures and reported separately.
- Documentation checks:
  - `iteration.md` records the change, commands, results, risks, and commit hash after commit.

## 5. Execution Steps

1. Inspect current dirty files enough to avoid overwriting unrelated changes.
2. Patch LaTeX font family mapping so `\songti` and `\heiti` map to distinct school-required Chinese fonts.
3. Patch heading/title/label commands to use `\heiti` only where required by the school standard.
4. Patch TOC front-matter entries and keyword lists.
5. Compile with XeLaTeX three times and inspect log, page count, font list, and extracted TOC/front matter.
6. If validation passes, append `iteration.md` record using system time.
7. Stage only the touched thesis/setup/chapter files plus `iteration.md` and this ExecPlan if the user wants the plan committed.
8. Commit with a scoped message.

## 6. Verification Commands

- Command: `cd thesis && xelatex -interaction=nonstopmode main.tex && bibtex main && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - Expected result: exit 0; generated `main.pdf`.
- Command: `rg -n "LaTeX Warning: (Citation|Reference)|There were undefined|Citation .* undefined|Reference .* undefined|Rerun to get" thesis/main.log`
  - Expected result: no output.
- Command: `pdfinfo -box thesis/main.pdf | sed -n '1,40p'`
  - Expected result: A4 page size; page count reported.
- Command: `pdftotext -layout -f 1 -l 12 thesis/main.pdf - | sed -n '1,220p'`
  - Expected result: front matter and TOC include required entries; page 8 not blank.
- Command: `pdffonts thesis/main.pdf | sed -n '1,100p'`
  - Expected result: Songti/Times for body and Heiti for title-class text; residual figure fonts identified if present.
- Command: keyword-count script over `abstract_zh.tex` and `abstract_en.tex`.
  - Expected result: 3-5 keywords in each language.
- Command: `git diff --stat && git status --short --branch`
  - Expected result: only intended files changed/staged; unrelated dirty files handled explicitly.

## 7. Risk Register

- Risk: Restoring Heiti conflicts with the previous "all Chinese Songti" simplification.
  - Impact: User may see apparent inconsistency.
  - Mitigation: Treat school format as the current authoritative target: body Songti, title-class elements Heiti.
- Risk: TOC front-matter entries may require two compile passes to stabilize page numbers.
  - Impact: Incorrect TOC pages if only compiled once.
  - Mitigation: Run XeLaTeX three times after patching.
- Risk: Font availability differs between macOS and later Word environment.
  - Impact: PDF and Word may not render exactly the same.
  - Mitigation: Use common macOS font fallbacks and report any missing font risk before Word conversion.
- Risk: Keyword compression could remove useful technical specificity.
  - Impact: Abstract metadata becomes less descriptive.
  - Mitigation: Keep 5 terms and preserve the core concepts: LLM, KV Cache quantization, behavior-guided calibration, asymmetric quantization, budget allocation.
- Risk: TOC entries for `目录` may create duplicate or misplaced entries.
  - Impact: School-format mismatch.
  - Mitigation: Verify extracted TOC after compile and adjust placement if needed.
- Risk: Existing dirty `iteration.md` archive operation may conflict with appending this task record.
  - Impact: Could mix unrelated archive work into this commit.
  - Mitigation: Inspect and preserve existing dirty state; exact-stage only this task's final delta if possible, otherwise report blocker before commit.

## 8. Open Questions

- Question: Should the plan file itself be committed with the format fix?
  - Option A: Commit it with the fix. This preserves audit provenance. Recommended.
  - Option B: Leave it uncommitted. This keeps thesis-format commit smaller but weakens traceability.

