# 2026-05-07 Thesis Layout, RQ Wording, and Font Polish ExecPlan

## 1. Task Alignment

- Goal:
  - Explain and remove the blank physical page 8 introduced between the table of contents and Chapter 1.
  - Replace paper-facing `RQ1` / `RQ2` / `RQ3` / `RQ4` wording with Chinese `研究问题 1` / `研究问题 2` / `研究问题 3` / `研究问题 4`.
  - Rewrite the opening of Chapter 2 so it reads like thesis prose rather than an internal technical note.
  - Enforce the school-facing font intent: Chinese text in Songti, English text in Times New Roman.
- Non-goals:
  - Do not change experimental numbers, tables, figures, formulas, references, labels, or citation keys.
  - Do not rewrite chapter arguments beyond the specific wording issues above.
  - Do not push to origin.
- Background:
  - The current PDF has 99 pages. Physical page 8 is a blank roman-numbered page `vi`.
  - Root cause: `ctexbook`/`book` uses `\cleardoublepage` inside `\mainmatter` under `twoside`, so after the table of contents ends on roman page `v`, LaTeX inserts a blank even page before Chapter 1.
  - Current font file already sets CJK main font to `Songti SC` and English main font to Times New Roman, but headings still explicitly use `\heiti`, CJK sans/mono still map to Heiti/Kaiti, and English mono maps to Courier New. This does not match the user's requested full-document font policy.

## 2. Constraints

- Environment constraints:
  - Work on local `main` at `/Users/chenzilang/Desktop/LLM_KVCache_Quantization`.
  - Current `main` is ahead of `origin/main` after the fast-forward merge; do not push.
- Repository constraints:
  - Use precise edits only; do not use `git add .`.
  - Keep prior stash `stash@{0}: pre-aigc-merge-main-dirty-20260507` intact.
  - Update `iteration.md` with real timestamp after implementation.
- Reproducibility constraints:
  - Rebuild `thesis/main.pdf` with three XeLaTeX passes.
  - Check final `main.log` / `main.out` for undefined refs/cits and rerun warnings.
- Risk constraints:
  - Fonts must compile on the current macOS environment and keep fallback for non-macOS environments.
  - Removing the blank page must not disturb chapter numbering, page numbering, TOC entries, or references.

## 3. Deliverables

- Files to modify:
  - `thesis/main.tex`
  - `thesis/setup/fonts.tex`
  - `thesis/setup/format.tex`
  - `thesis/setup/toc.tex`
  - `thesis/setup/commands.tex`
  - `thesis/chapters/ch1_introduction.tex`
  - `thesis/chapters/ch2_related_work.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
  - `iteration.md`
- Files to add:
  - None beyond this ExecPlan.
- Expected outputs/artifacts:
  - Updated `thesis/main.pdf`, expected to drop the inserted blank page and likely become 98 pages.
  - A small audit commit after validation.
  - Note: external PDF figures may still embed their own fonts; if `pdffonts` reports non-Songti/non-Times families only from included figure PDFs, handle that in a separate figure-font pass rather than mixing regenerated binaries into this text/layout patch.

## 4. Acceptance Criteria

- Functional checks:
  - Physical PDF page 8 is no longer a blank roman-numbered page between TOC and Chapter 1.
  - Chapter 1 visible research-question labels use Chinese wording (`研究问题 1` etc.) rather than `RQ1` etc.
  - Visible Ch4/Ch5 cross-references to research questions use Chinese wording and do not expose `RQ` abbreviations in prose.
  - Chapter 2 opening reads as thesis prose, not an internal note about "只保留技术记号".
  - Chinese font family resolves to Songti-style fonts; English font family resolves to Times New Roman.
- Regression checks:
  - No changes to numeric results.
  - No changes to table/figure data or labels.
  - No undefined references/citations.
- Reproducibility checks:
  - `xelatex` three passes finish successfully.
  - `pdfinfo thesis/main.pdf` reports the new page count.
- Documentation checks:
  - `iteration.md` records changed files, commands, validation, and commit hash.

## 5. Execution Steps

1. Fix blank page:
   - In `thesis/main.tex`, temporarily map `\cleardoublepage` to `\clearpage` only around `\mainmatter`, so `twoside` remains enabled but the TOC-to-Chapter-1 blank page is not inserted.
2. Replace visible `RQ` prose:
   - In `ch1_introduction.tex`, replace labels and structure prose with `研究问题 1` ... `研究问题 4`.
   - In `ch4_experiments.tex` and `ch5_conclusion.tex`, replace `Ch1 RQ2`, `RQ1`, etc. with Chinese phrases such as `第一章研究问题 2` and `研究问题 4`.
   - Keep internal LaTeX labels unchanged.
3. Rewrite Chapter 2 opening:
   - Replace "本章只保留后文会反复调用的技术记号与文献位置" with a thesis-style overview that explains the chapter's role in establishing technical background and literature boundaries.
   - Lightly adjust the first section opening if it still reads like an internal note.
4. Enforce fonts:
   - Add `fontset=none` to the document class if needed to prevent `ctex` from loading the macOS default fontset before project fonts.
   - In `fonts.tex`, map CJK main/sans/mono and `zhsong/zhhei/zhkai` to Songti-compatible fonts; use fake bold/italic where needed.
   - Map English main/sans/mono to Times New Roman.
   - In `format.tex`, replace explicit `\heiti` heading formats with `\songti\bfseries` or inherited Songti bold.
   - In `toc.tex` and `commands.tex`, replace visible title/cover/TOC `\heiti` usage with Songti bold.
5. Validate:
   - Run targeted `rg` checks for remaining paper-facing `RQ[0-9]`.
   - Run three XeLaTeX passes.
   - Scan logs and inspect page count/page 8 text.
6. Record and commit:
   - Append `iteration.md` entry with actual timestamp.
   - Stage exact files and commit.

## 6. Verification Commands

- Command:
  - `rg -n "RQ[0-9]|RQ1--RQ4|Ch1 RQ|本章只保留|技术记号" thesis/chapters thesis/main.tex thesis/setup -g '*.tex'`
- Expected result:
  - No paper-facing `RQ` abbreviation remains except in comments or explicitly approved internal labels; no Chapter 2 opening internal phrasing remains.
- Command:
  - `cd thesis && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
- Expected result:
  - Successful build; final PDF generated.
- Command:
  - `rg -n "LaTeX Warning: (Citation|Reference)|undefined|There were undefined|Rerun to get cross-references right|Citation .* undefined|Reference .* undefined|Label\\(s\\) may have changed" thesis/main.log thesis/main.out || true`
- Expected result:
  - No output.
- Command:
  - `pdfinfo thesis/main.pdf | rg "Pages"`
- Expected result:
  - Page count reflects removal of the blank inserted page, likely 98.
- Command:
  - `pdftotext -f 8 -l 8 thesis/main.pdf - | sed -n '1,80p'`
- Expected result:
  - Page 8 contains Chapter 1 content, not only roman page number `vi`.

## 7. Risk Register

- Risk: Removing the blank page may conflict with a strict printed double-sided convention.
  - Impact: Printed binding may not force chapters to odd pages.
  - Mitigation: Keep `twoside`; only suppress the `\mainmatter` blank page because the document already uses `openany` and the user explicitly flagged this page as unwanted.
- Risk: `fontset=none` may expose missing CJK family definitions.
  - Impact: Compile failure or missing `\songti` / `\heiti` behavior.
  - Mitigation: Verify with XeLaTeX; if needed, define CJK families explicitly in `fonts.tex`.
- Risk: Mapping `\texttt{}` English to Times New Roman reduces code-like visual distinction.
  - Impact: Technical identifiers may look less monospaced.
  - Mitigation: This follows the user's "英文用 Times New Roman" requirement; preserve `\texttt{}` semantics while changing the font.
- Risk: Replacing `RQ` globally could alter internal labels or citation keys by accident.
  - Impact: Broken references or source churn.
  - Mitigation: Only edit paper-facing prose; keep `\label{...}` unchanged.
- Risk: Chapter 2 opening rewrite could weaken its technical role.
  - Impact: Less precise chapter framing.
  - Mitigation: Preserve all technical anchors (`decoder-only Transformer`, `GQA/MQA`, `KV Cache`, `H_{kv}`, bit-width) while improving prose tone.
- Risk: Generated PDF/log files may appear dirty if they are tracked.
  - Impact: Commit could accidentally include generated artifacts.
  - Mitigation: Check `git status --short` and stage exact files only.

## 8. Open Questions (Need Re-confirmation)

- Question: Should the physical blank page between TOC and Chapter 1 be removed even though double-sided book classes often insert it?
  - Option A: Remove it now. Recommended because the user explicitly flagged it and the thesis already uses `openany`.
  - Option B: Keep it for printed double-sided binding convention.
- Question: Should all visible `RQ` abbreviations across chapters be converted, or only Chapter 1.4?
  - Option A: Convert all paper-facing visible `RQ` abbreviations across Ch1/Ch4/Ch5. Recommended for consistency.
  - Option B: Convert only Ch1.4 and leave Ch4/Ch5 as-is.
