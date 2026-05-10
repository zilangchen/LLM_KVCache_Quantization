# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## Current Status

- Active objective source: `objective.md`
- Active execution policy: `AGENTS.md`
- Active experiment protocol: `experiment_sop.md`
- Progress log source of truth: `iteration.md`
- Single-task plan source of truth: `task_plan.md` 或 `.agents/execplans/`
- Historical plan archive: `development_history/iteration_approved_plans_archive_20260419.md`

## Update Rules

1. After each completed functional unit, append one new entry under `Timeline` (latest first).
2. Every entry must include goal, changed files, commands run, outputs, and result quality.
3. If blocked, write explicit blocker and next action.
4. Keep entries concise and auditable; avoid vague summaries.
5. `iteration.md` 只保留开发记录，不再保留 `Approved Plans` 或长期任务计划。
6. Timeline 保留最近 **30 条**。超出时将最旧条目归档到 `development_history/iteration_archive_YYYYMM.md`。
7. SessionStart 维护脚本与 compact 预清理入口会在需要时自动执行归档，确保 `iteration.md` 保持 Latest First + 30 条窗口。

## Entry Template

### YYYY-MM-DD HH:MM | Workstream Title
- Goal:
- Scope:
- Changed files:
- Commands:
- Outputs:
- Validation:
- Risks / follow-ups:

## Timeline (Latest First)

### 2026-05-10 16:09 | Chapter 3 手动修订冻结
- Goal: 冻结第三章手动修订后的正文与配套图件，并同步正式 PDF。
- Scope: Chapter 3 writing polish, Figure 3-1 output-error decomposition layout, Figure 3-2 K/V diagnostic diagram layout and wording, rendered thesis PDF.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `thesis/figures/fig1_error_decomposition.tex`
  - `thesis/figures/fig_ch3_kv_diag_needle.tex`
  - `thesis/main.pdf`
  - `iteration.md`
- Commands:
  - `git diff --check`
  - `latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`
  - `git status --short --branch`
- Outputs:
  - 第三章多处 AIGC 高嫌疑段落已按用户偏好改写，保留原有技术含义、公式边界、路径定义和跨章引用。
  - 图 3-1 底部加入输出误差分解公式并调整框体尺寸，图 3-2 保留英文模型名并更新设计启示链。
  - 正式 `thesis/main.pdf` 已由当前 LaTeX 源重新渲染。
- Validation:
  - `git diff --check`: PASS.
  - `latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`: PASS, generated 100-page PDF.
  - Build warnings limited to existing Underfull boxes and a small Chapter 3 overfull hbox.
- Risks / follow-ups:
  - 本次提交只冻结第三章文本、图件和 PDF，不额外处理剩余排版 warning。
  - Intended commit: `docs: freeze chapter 3 polish`

### 2026-05-10 04:16 | Chapter 1/2 与摘要修订冻结
- Goal: 冻结用户完成的 Chapter 1、Chapter 2 和中英文摘要修订，并同步正式 PDF。
- Scope:
  - Chapter 1: 研究内容、技术路线、研究问题与贡献口径的当前修订版。
  - Chapter 2: 量化基础、相关工作与写作风格的当前修订版。
  - Abstracts: 中英文摘要对齐到当前行为对齐框架、敏感度画像和实验结论口径。
- Changed files:
  - `thesis/chapters/abstract_zh.tex`
  - `thesis/chapters/abstract_en.tex`
  - `thesis/chapters/ch1_introduction.tex`
  - `thesis/chapters/ch2_related_work.tex`
  - `thesis/main.pdf`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/abstract_en.tex thesis/chapters/abstract_zh.tex thesis/chapters/ch1_introduction.tex thesis/chapters/ch2_related_work.tex`
  - `latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`
  - `pdfinfo thesis/main.pdf | rg 'Pages|File size'`
- Outputs:
  - 正式 PDF 已重新渲染，输出为 101 页。
- Validation:
  - `git diff --check -- thesis/chapters/abstract_en.tex thesis/chapters/abstract_zh.tex thesis/chapters/ch1_introduction.tex thesis/chapters/ch2_related_work.tex`: PASS.
  - `latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`: PASS.
  - `pdfinfo thesis/main.pdf`: Pages 101, File size 1489598 bytes.
- Risks / follow-ups:
  - 本轮按用户手动定稿提交，未额外改写正文内容。
- Commit: pending at log-write time; intended `docs: polish thesis ch1 ch2 abstracts`

### 2026-05-09 05:37 | Ch4 官方 LongBench 解读措辞收窄
- Goal: 修正第 4 章官方 LongBench 对照段中“显著性退化”的统计含义偏强问题，使正文解读与表注“不构成全面统计检验”的边界一致。
- Scope:
  - 将表~\ref{tab:ch4-longbench-official} 后的“显著性退化”改为“系统性退化”。
  - 保留原有数值、协议边界和评测一致性结论，不改变实验 claim。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/main.pdf`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex iteration.md`
  - `latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`
- Outputs:
  - 官方 LongBench 小样本对照段不再使用容易被读成 formal significance 的“显著性”表述。
  - 表 4-4 的作用仍限定为评测协议一致性检验。
- Validation:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex iteration.md`: PASS.
  - `latexmk -xelatex -halt-on-error -interaction=nonstopmode main.tex`: PASS, generated 102-page PDF.
- Risks / follow-ups:
  - 仅为措辞收窄，无数据、表格或引用变更。
- Commit: pending at log-write time; intended `docs: narrow ch4 longbench degradation wording`

### 2026-05-09 05:30 | Ch4 第十轮 Codex 外审 fixup（表 4-4/4-5 协议一致 + n.s. 范围）
- Goal: 落地用户提交的 Codex 外审三项 finding。两个 P1 都属数据正确性（表 4-4 协议+数字混用、表 4-5 跨协议 PPL 拼接），P2 属表内/表外标注口径偏差，必须先用 CSV 证据定 ground truth 再动笔，避免再生新错误。
- Scope:
  - P1#1: 表 4-4 协议从 "32K" 修正为 "4K + gen_len=64"，INT8 数字 6.64/5.21/9.29 改为 7.13/5.27/9.25（与权威表 \texttt{table\_official\_longbench\_1p5b.tex} 及 \texttt{phase1\_summary.csv} 一致）；重算 $\Delta$ 列，宏平均由 -0.01 改为 +0.16；正文解读段落重写为"三任务方向均为正、绝对幅度落在噪声带"；表注新增 \texttt{phase1\_summary.csv} 来源标记 + 与表 4-3 不可绝对值并列读取的提示。
  - P1#2: 表 4-5 的 PPL 列原本拼接了两个不同协议（FP16=9.31/7.14/6.73 来自 \texttt{emnlp\_rolealign\_v1} hf 模式 seq=301828；sym INT4=19.5/85.5/6.97 来自 phase5v2 \texttt{kv\_cache} 模式 seq=32K）。统一到 phase5v2 主线协议：1.5B 8.93→19.54 / 7B 6.71→85.49 / 8B 6.92→6.97；表注显式声明 phase5v2 协议（WikiText-2, kv\_cache, seq=32K, n≥20 runs）并禁止与表 4-7 hf-mode 协议做跨表绝对值比较。
  - P2: line 687 + 697 的 "4K 处 |ΔT|<2\,ms" 修正为 "所有长度点上 |ΔT|<2\,ms"，与表 4-13 中 7B 8K/16K 实际标注的 n.s. 范围对齐。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`（13 行净变化）
  - `thesis/main.pdf`（102 页 → 102 页，文件大小 1,497,561 → 1,498,988 bytes）
- Commands:
  - 证据定位：grep `85.5` / `9.31` / `7.14` / `6.73` 跨 `results/archive/round*/` 与 `thesis/`，比对 phase5v2 vs emnlp_rolealign_v1 ppl_summary.csv
  - 协议核对：`cat results/phase1_summary.csv | grep 1.5B` 确认 4K + gen_len=64；`cat phase5v2/tables/ppl_summary.csv` 确认 sym INT4 三模型完整数据
  - 编译：`latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/codex_round10_build* main.tex`（两次：第一次主修复，第二次表 4-4 注引用修正）
  - 写回：`cp /tmp/codex_round10_build_v2/main.pdf thesis/main.pdf`
- Outputs:
  - 表 4-4 数字与 \texttt{phase1\_summary.csv} 完全一致；表 4-5 PPL 与 \texttt{phase5v2/tables/ppl_summary.csv} 完全一致；表 4-13 标注口径与正文表述对齐。
  - Codex 外审 P1#2 的"85.5 可能来自 RULER/Needle"怀疑被反证（85.5 确实是 PPL，phase5v2 archive `int4_baseline mean=85.485` 直接对应），但暴露出比 Codex 怀疑更深的 cross-protocol contamination 问题。
  - PDF 102 页，无新增 undefined references 或 citation warnings；line 369 既有 overfull hbox 与本轮无关。
- Validation:
  - `latexmk`: PASS（两次均通过）
  - `git diff --stat`: 13 insertions, 13 deletions (1:1 干净替换)
  - 跨章节核查：appendix 表 \texttt{tab:app-scale-precision}（line 517-520）的 19.65 / 86.56 来自 int4_t2_float32_v1 archive (n=3) 不同实验子集，与本轮 phase5v2 主线 (n≥20) 数字属"同量级一致"已在 appendix 表注内 acknowledge，无需联动改。
- Risks / follow-ups:
  - Round 10 已闭环；后续如需进入 Phase D 终审，建议用户复核表 4-5 协议脚注是否过长（4 行 footnote 是否影响版式）。
  - Codex 外审表明：跨章节 PPL 数字共用时必须锚定 CSV provenance，未来加 Findings 写作时可按"先指 CSV 再写数字"流程。
- Commit: `29c9c69`

### 2026-05-09 05:17 | 摘要 option-3 精修与中英文对齐
- Goal: 在结论化首版（commit 2712f63）基础上，按用户确认的 option 3 进一步精修中文摘要，再把同一思路平移到英文摘要，使两版的证据链表述、AutoK 预算接口提升和框架三段式收尾保持一致。
- Scope:
  - 中文摘要：第二段把"由此连接量化参数选择和层间预算建议"改为显式证据链表述（"组织成一条连续证据链，使同一组行为读数既能解释量化参数选择，也能转化为层间预算建议"）。
  - 中文摘要：第三段把 AutoK 提升为单独子句并补 boundary 声明（"预算分配应被理解为模型族、规模和任务条件共同约束下的候选选择问题，而不是脱离条件的固定规则"）；总结句改写为"以注意力行为保持为核心、以 K/V 角色差异恢复为低比特路径、以 \texttt{AutoK} 和行为敏感度画像为预算接口"的三段式。
  - 英文摘要：对齐三处改动（evidence chain 显式化 / AutoK separated clause + boundary phrase / framework hierarchical triple）；机制句（"the issue is not merely the reduction in bit-width..."）原版已具备 em-dash 等价表达，未改写。
- Changed files:
  - `thesis/chapters/abstract_zh.tex`（4 行）
  - `thesis/chapters/abstract_en.tex`（4 行）
- Commands:
  - `git diff --check -- thesis/chapters/abstract_zh.tex thesis/chapters/abstract_en.tex`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/abstract_optn3_build main.tex`
  - `pdfinfo thesis/main.pdf | rg 'Pages|File size|PDF version'`
- Outputs:
  - 中文摘要在 commit `70c6ab5` 落地。
  - 英文摘要在 commit `ef2a9ef` 落地，与中文版语义对齐。
  - 正式 PDF 维持 102 页，无新增 undefined references 或 citation warnings。
- Validation:
  - `latexmk`: PASS。
  - 仅保留既有 line 369 overfull hbox（与本轮无关）。
- Risks / follow-ups:
  - Round 10（用户自办 Codex 外审）尚未触发；外审反馈后再决定是否进入 Phase D 终审。
  - §4.2 FP16 数据完整性遗留项（表 4-3/4-4 同号但协议不同）已记入 Round 10 待办。
- Commits: `70c6ab5`（zh option 3）, `ef2a9ef`（en align）

### 2026-05-09 04:58 | 摘要结论化改写与中英文对齐
- Goal: 按用户确认的中文摘要版本替换正文，并对照中文逻辑重写英文摘要，使实验结论更结论化、减少跨模型数字堆叠。
- Scope:
  - 替换中文摘要三段正文。
  - 对齐英文摘要的问题引入、方法路径、实验结论和框架总结。
  - 重新编译并写回正式 PDF。
- Changed files:
  - `thesis/chapters/abstract_zh.tex`
  - `thesis/chapters/abstract_en.tex`
  - `thesis/main.pdf`
- Commands:
  - `git diff --check -- thesis/chapters/abstract_zh.tex thesis/chapters/abstract_en.tex`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/abstract_update_build main.tex`
  - `cp /tmp/abstract_update_build/main.pdf thesis/main.pdf`
  - `pdfinfo thesis/main.pdf | rg 'Pages|File size|PDF version'`
- Outputs:
  - 中文摘要采用用户确认的完整版本。
  - 英文摘要按中文摘要重构，保留框架、INT8、INT4-RoleAlign、跨模型预算和系统边界结论。
  - 正式 PDF 更新为 102 页，文件大小 1,497,561 bytes，PDF version 1.5。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS。
  - 日志无 undefined references 或 citation warnings，仅保留既有 line 369 overfull hbox。
- Risks / follow-ups:
  - 摘要变长导致 PDF 从 101 页变为 102 页，需由用户确认是否接受页数变化。
- Commit: current commit (`docs: update thesis abstracts to conclusion-focused version`)

### 2026-05-09 04:44 | 第四章 6-Reviewer 多轮审查（Phase A+B 完成）
- Goal: 按用户要求的"6 视角 Agent 审查 + 多轮迭代打磨"协议，对 ch4_experiments.tex 逐节审查，修复发现的实质问题。
- Scope:
  - Phase A 7 轮：§4.1-§4.7 各跑 6-reviewer 矩阵（R1 技术 + R2 中文 + R3 跨章 + R4 怀疑 + R5 统计 + R6 读者）。
  - Phase B 2 轮：Ch4 整章自审 + Ch4 × Ch1/Ch2/Ch3/Ch5 跨章节比对。
  - Phase C Round 10（用户自办 Codex 外审）暂未触发。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`（5 处实质性修复，7 行净变化）
- Commands:
  - `git tag chapter-4-review-baseline-v1` 锁基线（commit ab66f7f）
  - `latexmk -xelatex -interaction=nonstopmode` 每轮验证
  - `git tag round-{1,3,5}-s4.{1,3,5}-done` 标注落地修复
- Outputs:
  - Round 1 §4.1: 修复 line 98 "scale 时间语义" 类型误用 + line 115 dangling non-inferiority。Commit 088bc91.
  - Round 3 §4.3: 修复表 4-5 "PPL 退化 >15%" 替换为具体 PPL 数值（Qwen-1.5B 9.31→19.5 / 7B 7.14→85.5 / LLaMA-8B 6.73→6.97）。Commit 4f90084.
  - Round 5 §4.5: 修复表 4-13 Panel B 1.5B 4K 标 n.s. 一致性 + 表注新增 gen=64 vs gen=128 协议差异声明。Commit b2f3651.
  - Round 2/4/6/7/8/9: 6-reviewer 全 PASS，无文本修复。
  - 跨章节比对：Ch1 RQ1-4 / Ch2 KIVI per-channel K+per-token V / Ch3 §3.2 K8V4 表述 / Ch5 全部 8 个 numeric claim 与 Ch4 表逐一 verify 通过。
- Validation:
  - 最终 latexmk PASS，101 页 PDF，仅保留既有 line 369 cosmetic overfull (1.55pt)。
  - 全章无新增 warning / undefined references。
- Risks / follow-ups:
  - **P1 deferred for Codex Round 10**: 表 4-3 vs 表 4-4 FP16 数字 (NarrativeQA 7.07/HotpotQA 4.90/GovReport 9.21) 完全一致，但两表 protocol 不同（合成 vs 真实）。phase1_summary.csv 数据是 4K context，与 §4.2 声明的 32K 不符。需作者自行 verify CSV 数据来源。
  - P3 未修：sec:ch4-rqX label 命名与 body RQ 编号 off-by-one（内部一致，建议 Round 8 不动）；§4.4 主表跳过 Qwen2.5-7B 未明示理由；14B AutoK 阈值 90% 不同于其他 80% 未解释；best-k 选法 (3B=1, 8B=11, 14B=7, Mistral=3) 选法 protocol 缺。
- Commit: 088bc91、4f90084、b2f3651（已落地）；本 entry 后续待提交。

### 2026-05-09 03:56 | AIGC 修订后状态冻结
- Goal: 将 AIGC 段落修订、第三章分配器图调整、迭代日志归档窗口和正式 PDF 写回后的当前仓库状态冻结为一个可追溯提交。
- Scope:
  - 冻结当前工作树中已存在的论文文本、图稿草案与归档状态。
  - 不重新处理新的 AIGC 报告，也不改变实验结果或论文主张。
- Changed files:
  - `development_history/iteration_archive_202605.md`
  - `iteration.md`
  - `thesis/figures/fig_ch3_allocator_flow.tex`
  - `.agents/figure_drafts/`
  - `thesis/main.pdf` 已由 `/tmp/aigc_final_build/main.pdf` 写回，但该路径按 `.gitignore` 不纳入 Git。
- Commands:
  - `cp /tmp/aigc_final_build/main.pdf thesis/main.pdf`
  - `pdfinfo thesis/main.pdf | rg 'Pages|File size|PDF version'`
  - `git status --short`
  - `git diff --stat`
- Outputs:
  - 正式 PDF 写回 `thesis/main.pdf`，页数 101，文件大小 1,496,968 bytes，PDF version 1.5。
  - `iteration.md` 维持最近记录窗口，旧记录归档到 `development_history/iteration_archive_202605.md`。
  - 第三章分配器图的当前草案和对应工作产物随本次冻结提交保留。
- Validation:
  - 最终 `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_final_build main.tex` 已通过，生成 101 页 PDF。
  - 日志无 undefined references 或 citation warnings，仅保留既有 line 369 overfull hbox。
- Risks / follow-ups:
  - `.agents/figure_drafts/` 中包含草案 PDF、PNG 与 LaTeX 构建产物，本次作为冻结快照保留；后续若进入正式整理，应单独清理或归档。
- Commit: pending at log-write time.

### 2026-05-09 03:39 | AIGC 段落修订 50: 第五章机制解耦边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 5 的高嫌疑段落，本轮处理模型族覆盖、同格式比较和机制解耦边界。
- Changed files:
  - `thesis/chapters/ch5_conclusion.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch5_conclusion.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 保留 decoder-only GQA、MHA、MQA、滑动窗口注意力、MoE 和长上下文注意力变体覆盖边界。
  - 保留 `\texttt{INT4-RoleAlign}` 与 `\texttt{KIVI-style}` 在 `\texttt{per-channel K + per-token V}` 同格式条件内比较。
  - 将 `family-/scale-/task-dependent` 中文化为“受模型族、规模和任务共同影响的结构读数”。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理第五章系统层和动态决策层边界段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch5 mechanism boundary`

### 2026-05-09 03:36 | AIGC 段落修订 49: 第五章预算比较边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 5 的高嫌疑段落，本轮处理逐层预算分配的同量级预算带与严格预算匹配比较边界。
- Changed files:
  - `thesis/chapters/ch5_conclusion.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch5_conclusion.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 `在比较口径上` 改为直接边界说明。
  - 将 repeated `matched-budget` 改为“预算匹配”，并把 `分配器线` 改为“分配器方向”。
  - 保留第 4.4 节只能支持结构落点、高性能区间和 heuristic 强基线，不支持严格同预算形式化胜负判定的边界。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理第五章机制解耦与模型族覆盖边界段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch5 budget boundary`

### 2026-05-09 03:34 | AIGC 段落修订 48: 第五章评测协议边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 5 的高嫌疑段落，本轮处理研究局限性中官方 LongBench 对照与真实应用分布覆盖边界。
- Changed files:
  - `thesis/chapters/ch5_conclusion.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch5_conclusion.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 `从评测协议上看` 改为直接边界说明。
  - 保留 Qwen2.5-1.5B、NarrativeQA/HotpotQA/GovReport、每任务最多 50 样本、单一随机种子和全部真实应用分布示例。
  - 保持 PPL、Needle、RULER 与任务级指标降低单一度量偏差但仍需更多观察维度的边界。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理第五章比较口径与 matched-budget 边界段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch5 evaluation boundary`

### 2026-05-09 03:31 | AIGC 段落修订 47: 第四章 KL 与 MSE 机制解释
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 KL/MSE 趋同的机制解释和解释性边界。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 `setting`、`attention`、`quantization noise`、`ranking` 改为中文表述。
  - 保留小模型或激进低比特设置中 KL 分布代理更有诊断价值的机制读法。
  - 保留较大模型、较高位宽或更平滑架构中 KL/MSE 参数趋同的解释。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理第 4.6 节效度边界段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 kl mse mechanism`

### 2026-05-09 03:29 | AIGC 段落修订 46: 第四章 KL 与 MSE 趋同读数
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 7B KL/MSE 校准目标趋同的表格解读。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 去掉 `7B 这块证据` 与冒号式关键结论。
  - 保留 $k_{\mathrm{pct}}=100.0$、$v_{\mathrm{pct}}=99.9$、`\texttt{INT4-RoleAlign}` PPL 7.1121 和附录补充对照。
  - 保持“模型规模与鲁棒性可能调节差异，但正文证据主要支持趋同已经出现”的边界。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理 KL/MSE 趋同的机制解释段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 kl mse convergence`

### 2026-05-09 03:26 | AIGC 段落修订 45: 第四章部署 Panel A 读数
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理表 4-13 Panel A 关于 Qwen2.5-14B 融合路径的长度扩展读数和最小部署结论。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 保留 4K、8K、16K、32K 的全部时间差和相对降幅。
  - 将 `Qwen2.5-14B 上` 改为 `Qwen2.5-14B 采用...时`，并把 `memory traffic` 改为“访存流量”。
  - 将结论限定在 Qwen2.5-14B、H20、`\texttt{batch=1}` 与当前后端组合这一适用条件内。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理附录 A.8.2 中 7B KL/MSE 趋同解释相关段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 deployment panel a`

### 2026-05-09 03:22 | AIGC 段落修订 44: 第四章部署边界表注
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理表 4-13 中 Panel A/B、经验交叉边界、8B vs 14B 控制对比和 n.s. 规则的表注。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 去掉表注中的冒号式 `注：`。
  - 保留 Panel A/B 对应小节、性能交叉边界为经验读数、8B vs 14B 控制对比放在第 4.5.3 节正文、4K 处 $|\Delta T|<2$ ms 标记为 n.s. 且不作为交叉点读取。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理表 4-13 Panel A 的 Qwen2.5-14B 融合路径部署读数。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 deployment table note`

### 2026-05-09 03:19 | AIGC 段落修订 43: 第四章 RoleAlign 配对读数解释
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理表 4-8 后 RoleAlign 与 KIVI-style 的配对范围、PPL 差距和 Needle 恢复读法。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将配对范围改为“配对比较只覆盖 1.5B、7B 与 8B”，避免误读成模型之间互配。
  - 保留 $+0.15$、$+0.05$、$+0.00$ 三个 PPL 差距和两类 Needle 任务恢复到 100\%。
  - 将 `per-group` 改为“对称逐组格式”，并保留 `\texttt{per-channel K + per-token V}` 格式标签。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮进入第 4.5.3 节控制对比和表 4-13 部署读数段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 rolealign paired reading`

### 2026-05-09 03:16 | AIGC 段落修订 42: 第四章 RoleAlign 表注边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理表 4-8 关于 Needle 列、固定 seeds 和 Qwen2.5-14B 配对范围的表注。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 去掉表注中的冒号式 `注：`。
  - 保留 Needle-single-retrieval、MK-NIAH-2、100\% 通过率、5 个固定 seeds 和 Qwen2.5-14B 不纳入配对差异判断。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮处理表 4-8 后 RoleAlign 与 KIVI-style 配对读数解释段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 rolealign table note`

### 2026-05-09 03:14 | AIGC 段落修订 41: 第四章 softmax 阶跃机制解释
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理对称 INT4 阶跃崩塌的 softmax 机制解释和 K/V 诊断过渡。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 Key 侧机制改为条件式表述，避免提前写死 Key 先触发。
  - 保留 top-$k$、softmax 概率质量转移、100\% 到 0\% 跳变和 50\%/30\%/10\% 线性衰减对照。
  - 将 LLaMA-3.1-8B 的 98\% Needle 解释限定为与 $H_{kv}=8$ 和较小 $H_q/H_{kv}$ 重复因子相符，并补充模型族、规模和训练数据混杂边界。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮进入检测报告中 RoleAlign/KIVI-style 或后续系统段落的高嫌疑项。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 softmax cliff mechanism`

### 2026-05-09 03:11 | AIGC 段落修订 40: 第四章对称 INT4 阶跃崩塌证据
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理对称 INT4 阶跃崩塌的表格解读与边界结论。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将冒号式证据展开改为表格读数后的直接解释。
  - 保留 Qwen2.5-1.5B/7B 的 Needle 100\% 到 0\% 变化、语言建模退化和 LLaMA-3.1-8B 的 98\% Needle 例外。
  - 将后续问题从口语化参数调整表述改为量化格式与误差传播路径匹配。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮继续处理第 4.3.1 节 softmax 机制解释段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 int4 cliff evidence`

### 2026-05-09 03:07 | AIGC 段落修订 39: 第四章系统效率指标边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 TPOT、KV Cache 占用、峰值显存和第 4.5 节部署结论边界。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 去掉原句中冒号式指标罗列，改为协议性描述。
  - 保留 TPOT、KV Cache 占用和峰值显存三项系统效率读数。
  - 将第 4.5 节部署结论边界改为正式交叉引用，并限定在当前 H20 环境内解释。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check`: PASS。
  - `latexmk`: PASS，生成 101 页 PDF。
  - 日志仅保留既有 line 369 overfull hbox，无 undefined references 或 citation warnings。
- Risks / follow-ups:
  - 下一轮进入检测报告 Segment 40，处理对称 INT4 架构依附性崩塌及 softmax 机制解释段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 system metric boundary`

### 2026-05-09 03:04 | AIGC 段落修订 38: 第四章 RULER 与 Needle 互补关系
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 RULER 宏平均通过率、Needle 单点检索探针和二者互补关系。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 去掉 `失败信号是` 与冒号式 `前者/后者` 结构。
  - 保留 RULER 的宏平均通过率和组合式长上下文任务定位。
  - 保留 Needle 暴露检索功能临界点、RULER 检查多子任务同步退化的互补关系。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 39 的系统效率指标段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 ruler needle contrast`

### 2026-05-09 03:02 | AIGC 段落修订 37: 第四章 LongBench 风格合成任务协议
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 LongBench 风格合成任务、task-core、任务指标和官方榜单边界。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 保留 task-core、单文档问答、多文档问答和摘要三类功能。
  - 保留 F1、Rouge-L 与 Edit Similarity 等指标。
  - 将绝对分数边界写成按本文协议解释，不与社区官方榜单直接对齐。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 38 的 RULER 与 Needle 互补关系段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 longbench style protocol`

### 2026-05-09 02:59 | AIGC 段落修订 36: 第四章 Needle 协议边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 Needle-in-a-Haystack 的上下文长度、深度扫描和精确匹配读数段。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 `失败信号是` 句式改为更自然的指标说明。
  - 保留 4K、8K、16K、32K 四个上下文长度和统一 needle 深度扫描。
  - 将精确匹配通过率收窄为长距离目标片段取回能力的代理读数。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 37 的 LongBench 风格合成任务段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 needle protocol`

### 2026-05-09 02:57 | AIGC 段落修订 35: 第四章 PPL 协议边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理 PPL 指标协议、32K 上下文、chunk size 和 14B 前缀评测边界。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 `likelihood` 改为“语言建模似然”，减少英文式中文。
  - 保留 32K 评测协议、`\texttt{chunk_size}=128` 和每位置历史窗口约束。
  - 将 14B 固定前缀评测边界写成内部对照和同协议比较规则。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 36 的 Needle-in-a-Haystack 段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 ppl protocol`

### 2026-05-09 02:54 | AIGC 段落修订 34: 第四章指标失败模式总览
- Goal: 逐段处理 AIGC 检测报告中 Chapter 4 的高嫌疑段落，本轮处理评测任务、数据与指标小节的指标总览段。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 减少连续 `检查` 句式，将指标组织为失败模式到读数的映射。
  - 明确 Needle 使用精确匹配通过率检查目标片段能否取回。
  - 将官方 LongBench 真实数据对照定位为协议一致性检验与外部真实数据方向核验，保留其不进入主评测矩阵的边界。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 34 后续的 PPL 协议段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch4 metric overview`

### 2026-05-09 02:50 | AIGC 段落修订 33.3: 第三章小结分配与系统承接
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理第三章小结中 BA-$k$、AutoK、系统接口与第四章承接段。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将分配器段从机械清单改为校准产物到层级预算的承接。
  - 修正 AutoK 覆盖阈值方向，明确给定 $\rho$ 后生成最小保护层数候选。
  - 将第四章承接收窄为质量、低比特路径边界、跨模型适用区间和 TPOT 等系统读数。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮进入检测报告 Segment 34 的第四章评测指标段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 summary allocation handoff`

### 2026-05-09 02:46 | AIGC 段落修订 33.2: 第三章小结路径实例链
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理第三章小结中 §3.4、§3.5 与 KIVI-style 对照的路径实例链段。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将长句拆成校准代理、三条路径职责、RoleAlign 产物边界和 KIVI-style 对照边界四层。
  - 将 `per-channel` / `per-token` 改为更自然的中文混排表达。
  - 把 RoleAlign 的效果收窄为缓解低比特失稳，并明确同格式比较只限定 K/V 轴布局与非对称仿射口径。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 33 中第三章小结的第三段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 summary path chain`

### 2026-05-09 02:41 | AIGC 段落修订 33.1: 第三章小结机制入口
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理第三章小结中 §3.1 与 §3.2 的机制回顾段。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将目录式摘要改为从注意力误差进入输出的机制问题切入。
  - 保留 §3.1 代数分解、§3.2 K/V 对照诊断和 Key 侧低比特失稳判断。
  - 补充 Value 侧没有同等强度退化的边界，避免把诊断结论写得过强。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 33 中第三章小结的第二段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 summary mechanism intro`

### 2026-05-09 02:36 | AIGC 段落修订 32: 离线搜索复杂度引入
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理离线候选参数扫描与路径级搜索复杂度说明。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将机械的变量引入改为更自然的复杂度定义句。
  - 保留 `\mathcal O(|\Theta_{\mathrm{path}}| N L H_q n d_k)` 公式和 `H_q` 粒度解释。
  - 补充 K 路径 KL 统计与 V 路径输出扰动代理的边界，避免把三条路径差异写成只来自候选集合规模。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮进入 Segment 33 的第三章小结段落。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 offline complexity intro`

### 2026-05-09 02:31 | AIGC 段落修订 31b: 系统路径三类职责
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理系统落地中 INT8-Canonical、INT4-RoleAlign 质量路径和 INT4 系统边界扩展的职责划分。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 去掉内部实现名，将质量评估主线写为参考解码实现与语义一致性核验。
  - 明确第四章 TPOT 表参考路径 `INT4` 列是参考后端的时间口径。
  - 区分 KIVI-style 格式对照与 Triton 融合后端读数，避免把格式和后端混成同一层。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮进入 Segment 32 的离线搜索复杂度引入段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 system path roles`

### 2026-05-09 02:27 | AIGC 段落修订 30c-31a: GQA 头映射与并行网格
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理 GQA Query/KV 头映射、重复因子公式和 `(B,H_q)` 并行网格说明。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 拆开公式引入句，保留 `H_q`、`H_{kv}`、整除关系和重复因子公式。
  - 将 `(B,H_q) grid` 改为并行网格表述，并保留直接访问 `h_{kv}` 切片、不复制 KV 头的语义。
  - 保留块内访存合并、元数据广播、寄存器占用和反打包开销共同反映到 TPOT 的边界。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮处理 Segment 31 的系统侧三路径分工段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 gqa head mapping`

### 2026-05-09 02:24 | AIGC 段落修订 30b: INT4 nibble packing 与解包路径
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理 INT4 nibble packing、wrapper 反打包、RoleAlign 核内解包和 TPOT 边界。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 INT4 解包说明重构为存储码值、读取反量化、两类执行路径和 TPOT 边界四层。
  - 明确非对称 INT4 的 `[-8,7]` 16 级码本与对称诊断路径 `q_{\max}=7`、`[-7,7]` 网格的区别。
  - 限定对称路径使用 scale、RoleAlign 使用 `$(s,\zeta)$`，避免把非对称参数误写为所有路径共有。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮处理 Segment 30 的 GQA head mapping 段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 int4 unpack paths`

### 2026-05-09 02:18 | AIGC 段落修订 29b-30: 融合核分块循环与 online softmax 递推说明
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理融合核分块循环、online softmax 递推状态和最终归一化说明。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将冒号式 block 循环说明改为连续说明，数学递推公式不变。
  - 将公式说明文字中的 block 统一为“块”，并去掉不必要括号式解释。
  - 保留 FlashAttention online softmax 等价性、非归一化累加器和最终除法时机。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - 下一轮进入 Segment 31 的 INT4 nibble packing 与 in-kernel unpack 说明。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 online softmax recurrence`

### 2026-05-09 02:14 | AIGC 段落修订 29a: 自回归解码瓶颈与 INT8 融合核动机
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理自回归解码访存瓶颈、朴素反量化路径和 INT8 Triton 融合核动机。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将模板化瓶颈说明改写为自然技术叙述，保留自回归解码访问模式和朴素路径的线性开销。
  - 保留 Triton 引用和融合核内反量化、点积、online softmax、输出累加四个组件。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - Segment 29 还包含融合核分块循环开头，下一轮单独处理。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 int8 fusion motivation`

### 2026-05-09 02:11 | AIGC 段落修订 28c: Prefill/Decode 数据流边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理 Prefill/Decode 数据流、注意力后端交接和融合解码核接口边界。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 Prefill/Decode 平行说明改写为自然数据流，保留预填充写入、解码读取和后端交接。
  - 将“避免低比特缓存中间物化”收窄为“避免反量化后的中间张量物化”，避免语义漂移。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - Segment 28 已按三个自然段处理完成，下一轮进入报告 Segment 29。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 prefill decode boundary`
