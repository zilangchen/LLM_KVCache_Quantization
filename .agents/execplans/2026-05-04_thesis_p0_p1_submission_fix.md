# ExecPlan: Thesis P0/P1 Submission Fix

## 1. Task Alignment

- Goal: 修复 P4 复核后真实成立的投稿阻塞项：Ch1/Ch5 RQ 闭环不一致、Ch3 方法章零引用、Abstract 的 Mistral `15.69` 数字在 Ch4 缺显式出处，以及两个局部表注自足性问题。
- Non-goals:
  - 不处理已撤销的误判：Ch3 dangling refs、Mistral scope、INT8 summary scope、Ch4 discourse marker 计数、`inv_tau` 口径、Qwen2.5-7B 跳过剖面、官方 LongBench 50 样本泛化说明。
  - 不改变论文主张强度，不新增实验结果，不把 AutoK 写成跨模型普适最优。
  - 不修改 `objective.md`、`CLAUDE.md` 或实验流程。
- Background:
  - Codex 只读核验与 Claude 二次 grep 已收敛：最终真问题为 3 个 P0、2 个 P1、1 个可选 P2。
  - `objective.md` 当前将 RQ4 定义为 Automatic Budget Proposal，Ch1 已引入 RQ4，但 Ch5 仍按三个问题收束。

## 2. Objective Alignment

- RQ4 / Automatic Budget Proposal: Ch5 必须显式回应画像驱动 AutoK 是否能减少手工 fixed-`k` sweep 的不稳定性。
- Success Criteria 1 / 4 / 5: 修复后论文主张应继续保持 regime-based interpretation，不回到 universal policy 叙事。
- Boundary: 所有新增表述必须绑定现有 Ch4 证据与已验证读数；不能引入未在正文或复现材料中可追踪的新数字。
- Documentation layering: 本计划是单任务执行计划，保存在 `.agents/execplans/`；`iteration.md` 只在执行完成后追加事实记录。

## 3. Constraints

- Environment constraints:
  - 本地论文编译使用 `cd thesis && bibtex main && xelatex -interaction=nonstopmode main.tex`，引用改动后至少运行 BibTeX + 多轮 XeLaTeX。
  - 不运行 GPU 实验；本轮只改论文源。
- Repository constraints:
  - 当前分支为 `codex/aigc-risk-revision-20260501`。
  - 禁止 `git add .`；提交时精确 staging。
  - 纯 `thesis/` 和 `.agents/execplans/` 文档修改可豁免代码双重审查，但仍需要独立 verification agent 复核论文一致性。
- Reproducibility constraints:
  - 数字 `15.69` 必须可由 Ch4 或明确表注追溯到 Mistral extend-task 读数，不靠摘要孤立承载。
  - TPOT/Needle 表注只能写已验证的 seed / denominator / scope；未查到来源时不发明 `<2ms`、`10 runs` 等新口径。
- Risk constraints:
  - P0 修复必须小步完成，避免在 Ch5 新增段落时改变全文贡献排序。
  - Ch3 citation 只补必要来源，不把方法章改回 survey 风格。

## 4. Deliverables

- Files to modify:
  - `thesis/chapters/ch5_conclusion.tex`
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - Optional: `thesis/chapters/abstract_zh.tex`, `thesis/chapters/abstract_en.tex` only if P2 polish is explicitly included after P0/P1.
- Files to add:
  - None beyond this ExecPlan.
- Expected outputs/artifacts:
  - One P0 fix commit.
  - One P1 table-note fix commit, or combined only if diff remains very small and review is clean.
  - `iteration.md` append-only record after verified commits.

## 5. Acceptance Criteria

- P0-1 RQ closure:
  - Ch5 opening and conclusion-answer section refer to four questions, not three.
  - Ch5 contains a fourth RQ answer paragraph that explicitly addresses AutoK / profile-aware budget proposal.
  - The RQ4 paragraph is bounded: AutoK is a useful model-level proposer in certain regimes, not a universal winner.
- P0-2 Ch3 citations:
  - `thesis/chapters/ch3_method.tex` contains at least the necessary method citations for KIVI, Triton, online softmax / FlashAttention, and GQA.
  - Added citation keys already exist in `thesis/references.bib` and compile with no undefined citations.
- P0-4 numeric traceability:
  - `15.69` appears in Ch4 near the Mistral extend profile or table note.
  - Abstract `14.76 / 15.69` has direct Ch4 support.
- P1-4 TPOT table note:
  - `tab:ch4-tpot-4k` table note states the verified repeat/seed and scope information needed for standalone reading.
  - It does not claim CI or noise thresholds unless directly supported.
- P1-5 Needle note:
  - Needle percentage tables or their immediate notes state denominator/seed/task-pair semantics sufficiently for a reader to interpret `100%`, `98%`, and `100/100%`.
- Regression:
  - No undefined references or citations in `thesis/main.log`.
  - Existing resolved Ch3 figure/table labels remain untouched.

## 6. Execution Steps

1. P0-1: Edit Ch5 RQ closure.
   - Change “三个问题” to “四个问题” where appropriate.
   - Add a fourth paragraph in `conclusion-answers` answering RQ4.
   - Grep Ch1/Ch5 for RQ count consistency.
2. P0-2: Add necessary Ch3 citations.
   - Add `\cite{liu2024kivi}` at KIVI-style comparison context.
   - Add `\cite{tillet2019triton}` at Triton fusion kernel context.
   - Add `\cite{dao2022flashattention}` at online softmax context.
   - Add `\cite{ainslie2023gqa}` at GQA head mapping context.
   - Add SmoothQuant/GPTQ only if the INT8 calibration paragraph needs a concise PTQ anchor without expanding survey prose.
3. P0-4: Add Ch4 explicit Mistral extend mean.
   - Prefer table note or immediate §4.4.2 prose so the abstract number is traceable in main text.
   - Keep distinction between `core mean = 14.76` and `extend mean = 15.69`.
4. Verify P0.
   - Run grep checks and LaTeX compile.
   - Spawn one verification agent to review only P0-1/P0-2/P0-4.
   - Fix any PASS-blocking issue before continuing.
5. P1-4/P1-5: Add table-note self-containment.
   - Update TPOT 4K note with verified seed/repeat and scope.
   - Update Needle-related notes with verified denominator/seed/task-pair semantics.
6. Verify P1.
   - Run targeted grep and LaTeX compile.
   - Spawn one verification agent for P1 table-note consistency.
7. Optional P2:
   - Only after P0/P1 pass, lightly polish Chinese abstract English terms if desired.

## 7. Verification Commands

- Command: `rg -n "三个问题|四个问题|RQ4|AutoK|预算建议" thesis/chapters/ch1_introduction.tex thesis/chapters/ch5_conclusion.tex`
  - Expected result: Ch1 and Ch5 both align on four questions; Ch5 has an RQ4/AutoK answer anchor.
- Command: `rg -n -F "\\cite" thesis/chapters/ch3_method.tex`
  - Expected result: Ch3 has necessary citation commands.
- Command: `rg -n "15\\.69|15\\.6946|extend mean|5-task extend|Mistral-7B" thesis/chapters/abstract_zh.tex thesis/chapters/abstract_en.tex thesis/chapters/ch4_experiments.tex`
  - Expected result: `15.69` appears in both abstract and Ch4 evidence context.
- Command: `rg -n "tab:ch4-tpot-4k|8 .*seed|seeds|Needle|100/100|98\\\\%" thesis/chapters/ch4_experiments.tex thesis/chapters/appendix.tex thesis/tables`
  - Expected result: TPOT and Needle notes are locally interpretable and consistent with global protocol.
- Command: `cd thesis && bibtex main && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - Expected result: compilation completes.
- Command: `rg -n "LaTeX Warning: Citation|LaTeX Warning: Reference|undefined|There were undefined" thesis/main.log thesis/main.out`
  - Expected result: no matches.
- Command: `git diff --stat`
  - Expected result: diff limited to the planned thesis files plus this ExecPlan and later `iteration.md`.

## 8. Risk Register

- Risk: Ch5 RQ4 paragraph duplicates Ch4 summary.
  - Probability: Medium.
  - Impact: Ch5 becomes repetitive and weakens conclusion flow.
  - Mitigation: Write RQ4 as a short answer to the research question, not a new result recap.
  - Rollback: Revert only the new paragraph and re-add a shorter sentence-level RQ4 closure.
- Risk: Ch3 citations make the method chapter look like related work.
  - Probability: Low.
  - Impact: Method section loses authorial focus.
  - Mitigation: Add citations inline at origin points; avoid adding survey sentences.
  - Rollback: Keep citations but remove any extra expository prose.
- Risk: `15.69` is computed from two extend tasks while Ch4 table labels the row as 5-task mean.
  - Probability: Medium.
  - Impact: Reader may confuse core mean, extend mean, and 5-task mean.
  - Mitigation: Explicitly name `core mean`, `extend-task mean`, and `5-task mean` separately.
  - Rollback: Move the explanation from prose into table note for tighter scoping.
- Risk: TPOT note introduces unverified noise or CI claim.
  - Probability: Medium.
  - Impact: New unsupported statistical statement.
  - Mitigation: Only write verified seed/repeat and “no CI reported in this table” style scope if needed.
  - Rollback: Remove numeric noise statement and rely on global protocol line.
- Risk: Needle denominator is not recoverable from active thesis source alone.
  - Probability: Medium.
  - Impact: Table note could remain underspecified.
  - Mitigation: Inspect source tables/results before writing; if unavailable, state verified seed/task-pair semantics without inventing `n`.
  - Rollback: Keep note conservative and point to appendix heatmap/protocol if it already contains the denominator.
- Risk: LaTeX compile updates generated artifacts.
  - Probability: High.
  - Impact: Working tree may contain ignored `.aux/.log/.bbl` changes or tracked generated files.
  - Mitigation: Check `git status --short`; stage only source files intentionally.
  - Rollback: Do not stage generated artifacts unless already tracked and necessary.

## 9. Open Questions

- Question: 是否把 P2 中文摘要术语 polish 纳入本轮？
  - Option A (recommended): 暂不纳入。先清 P0/P1，避免把非阻塞审美修改混入投稿阻塞修复。
  - Option B: P0/P1 通过后追加一个很小的 P2 polish commit。
- Question: P0/P1 是否拆成两个 commits？
  - Option A (recommended): 拆成 P0 commit + P1 commit，便于审查和回滚。
  - Option B: 若最终 diff 很小，合并为一个 `docs:` commit。

## 10. Milestones

- M8-A / P0 Closure:
  - Fix P0-1, P0-2, P0-4.
  - Verify via grep + LaTeX + verification agent.
  - Commit if clean.
- M8-B / P1 Table Notes:
  - Fix P1-4, P1-5.
  - Verify via grep + LaTeX + verification agent.
  - Commit if clean.
- M8-C / Optional P2:
  - Only if approved after M8-A/B.
  - Light abstract terminology polish.
