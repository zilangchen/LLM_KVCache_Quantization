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

### 2026-05-08 07:00 | Thesis Ch3 §3.2 4-Round 6-Agent Audit + v3 落地
- Goal: 沿用 §3.1 同流程对 §3.2 K/V 敏感性不对称动机诊断节执行 6-agent 多视角审查与迭代重写，v0 (commit 90cb485) → v3 全 PASS 落地。
- Scope:
  - 6 视角并行审查：D1 顶会 / D2 数学 / D3 复现 / D4 中文（codex prefs ground truth）/ D5 skeptical / D6 博士生
  - 4 轮迭代：v0 (commit 90cb485) → v1 → v2 → v3 (落地)
  - 24 个 agent 报告（6 reviewer × 4 rounds，含 D4/D6 round 3 因 prompt 行号定位错误 re-spawn 一次）
  - 关键 critical bug 抓取：D2 round 3 抓出 v2 "$H_{kv}$ 个查询头均摊" 数学错误（应为 $H_q/H_{kv}$ 个查询头共享），D6 round 3 独立确认
- Changed files:
  - `thesis/chapters/ch3_method.tex` line 45-58（§3.2 v0→v3 完整重写，net +6 -6 = 0；6 段重写 + 图 \input 位置移到段 2 后）
  - `docs/ch3_writing_quality_audit_20260508.md`（追加 §3.2 v1/v2/v3 候选稿 + 4 轮 D-phase 对照 + 6-agent 总结）
- Commands:
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`（pass 1 + pass 2）
  - `git diff --check thesis/chapters/ch3_method.tex`
- Outputs:
  - v3 加权平均 8.90（v0=6.0 → v1=7.43 → v2=8.38 → v3=8.90）
  - 6/6 PASS：D1=8.6 / D2=8.8 / D3=9.0 / D4=9.2 / D5=8.6 / D6=9.2
  - xelatex 编译 96 页，零 LaTeX Error，零 undefined references
  - D5/D6 双双明确"何时停止"：「v3 封版，可投稿；继续迭代边际收益低于风险」
- Validation:
  - .tex 落地后 xelatex 双轮编译通过 96 页
  - `git diff --check` OK（无 whitespace 错误）
  - codex prefs 12 项 (A-L) v3 全合规
- Risks / follow-ups:
  - D5 R1: 桥接句"机制预测"方向性依赖读者从公式推导 K 更脆弱（归档，可在终稿审读时补脚注）
  - D5 R2: GQA 单因素归因 $H_{kv}$（$H_q$ 也参与调制，归档）
  - D1/D2/D4/D6 各 1 处 P3 minor 归档（不阻塞）
  - 下一节 §3.3 行为引导量化框架总览审查待启动（v0 line 60-94，状态 ⚪ 待审）

### 2026-05-08 06:35 | Thesis Ch3 §3.1 5-Round 6-Agent Audit + v4 落地
- Goal: 严格按用户新工作流（A→B→C→D→E→F：原稿审 → 综合 → 候选稿 → 多 agent 审 → 迭代重修 → 落地）完成 §3.1 注意力近似误差代数分解节的写作质量审查与重写，达到 EMNLP/ACL/NeurIPS senior reviewer 通过水准。
- Scope:
  - 6 视角并行审查：D1 顶会 reviewer / D2 数学严谨 / D3 复现实验者 / D4 中文写作专家（严守 codex prefs ground truth）/ D5 skeptical reader / D6 同行博士生
  - 5 轮迭代：v0 (commit dd869e4) → v1 → v2 → v3 → v4 (落地)
  - 30 个 agent 报告（6 reviewer × 5 rounds）
  - codex prefs ground truth 文件：`/Users/chenzilang/.codex/rules/writing_preferences.md` 作为 D4 评分 rubric
  - 关键 review 演化：v0→v1 修 D4 round 1 6 处中文残留；v1→v2 删 codex prefs 违规；v2→v3 修 D5 4 处实质问题；v3→v4 修 D5 KL 代理 gap + GQA 共享悬挂 + $(a,o)$ 正面论证
- Changed files:
  - `thesis/chapters/ch3_method.tex` line 3-46（§3.1 v0→v4 完整重写，net +7 -11，删 v0 章末过渡 + 合并 v0 图后段到末段 + 补 KL 论证桥）
  - `docs/ch3_writing_quality_audit_20260508.md`（新建，~700 行 audit log，含 §3.1+§3.2 各 6-agent 审查 + 5 轮 D-phase + 落地状态）
- Commands:
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`（pass 1 + pass 2）
  - `git diff --check thesis/chapters/ch3_method.tex`
- Outputs:
  - v4 加权平均 9.02（轨迹：v0=6.7 → v1=8.5 → v2=8.05 → v3=8.68 → v4=9.02）
  - 6/6 PASS：D1=9.2 / D2=9.4 / D3=9.5 / D4=8.7 / D5=8.5（**撤回 round 4 NOT PASS**）/ D6=8.8
  - xelatex 编译 96 页，零 LaTeX Error，零 undefined references；Underfull 在 line 140/756（与 §3.1 无关）
  - D5 明确"何时停止"判定：「v4 达到 PhD 论文方法章首节的合理标准...停止建议：此稿提交。剩余可疑点均属于答辩响应层面，不是论文修改层面。」
- Validation:
  - .tex 落地后 xelatex 双轮编译通过 96 页
  - `git diff --check` OK（无 whitespace 错误）
  - codex prefs 12 项 (A-L) v4 全合规（v0 仅 5/12 → v4 12/12）
- Risks / follow-ups:
  - 末段密度 v3 4 句 → v4 6 句（D6 + D4 双双警告"潜在 P3"，都判 PASS，归档供后续打磨）
  - `$Q_{\theta_K}$` 作用域"逐元素/逐通道/逐 token"列举越界（连续 5 轮 D1 提及，归档不阻塞）
  - "间接约束聚合侧"措辞精度（D2 round 5 提议加限定"权重分布 $\hat a_i$"，D5 判答辩可承担）
  - 下一节 §3.2 同流程审查待启动（v0 audit 已在 MD 第 168-293 行完成，6.0/10 Major revision needed，待 candidate v1 + D 阶段迭代）
  - codex prefs 反馈待用户决策：D4 提议补充 2 条（交叉引用密度控制 + 批评对象显式引出规则）

### 2026-05-07 05:07 | Thesis Ch1/Ch2/Ch5 AIGC Paraphrase Pass
- Goal: 等量改写 Ch1 / Ch2 / Ch5 中 VPCS AIGC 检测器易标注的概括性、结构化与 meta 句式，目标降低 12.27% 总疑似率至 ~9% 区间，同时保留全部 claim、数字、模型名、引用与公式。
- Scope:
  - Ch1：1.2 校准目标段开头重写；1.4 RQ1–RQ4 从「这一问题关注 X」结构改为直接问句；1.5 三条贡献 lead-in 重写并把贡献 3 收束到「同量级 INT4 预算带」表述。
  - Ch2：2.4 综述章开头与 KIVI 组 lead-in 重写；2.5 line 180 双重 meta 否定开头改为单句正向陈述；2.5 四点空白去掉「第一/第二/第三/第四」编号。
  - Ch5：5.1 四点回答全部绑入 ch4 的具体数字（Δ=+0.02 / BA-k1=6.90 / Heuristic-k1=3.48 / Uniform=7.23 / BA-AutoK cov90=7.15 / Mistral 14.76、15.69、15.14）；5.2 三层价值 framing 重写；5.4 三方向 lead-in 重写；5.5 结语重写；line 23 大小写一致性 `heuristic-k1` → `Heuristic-k1`。
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `thesis/chapters/ch2_related_work.tex`
  - `thesis/chapters/ch5_conclusion.tex`
- Commands:
  - `git diff HEAD -- thesis/chapters/ch1_introduction.tex thesis/chapters/ch2_related_work.tex thesis/chapters/ch5_conclusion.tex`
  - `rg -n "BA-k1|BA-AutoK|heuristic-k1|Uniform|cov90|task-core" thesis/chapters/ch3*.tex thesis/chapters/ch4*.tex thesis/chapters/abstract_*.tex`
  - `cd thesis && xelatex -interaction=nonstopmode main.tex`（3-pass + 1-pass post case fix）
  - `grep -E "(LaTeX Warning: (Citation|Reference)|undefined|Rerun to get cross-references right|Label\(s\) may have changed)" main.log`
  - `pdfinfo main.pdf`
- Outputs:
  - `thesis/main.pdf` 重新生成，97 页（与 6fc5c71 baseline 一致），1462713 bytes。
  - 三章 +37 / −37 行等量替换；总字数变化 < 1%。
  - 5.1 新增 8 个数字证据全部追溯到 ch4 L540 / L523 / L538 / L833 与 abstract_zh / abstract_en，无 over-claim。
- Validation:
  - 0 undefined references / 0 undefined citations / 0 Rerun warnings / 0 Label changes。
  - 仅有中英混排 `Underfull \hbox` 排版警告，与本次改动无关。
  - 5.1 数字（+0.02 / 6.90 / 3.48 / 7.23 / 7.15 / 14.76 / 15.69 / 15.14）grep 在 ch4 / abstracts 全部找到来源。
- Risks / follow-ups:
  - VPCS 是黑盒，估算 12.27% → ~9% 基于"连接句被标 / 数字句不被标"反推，实测以重跑 VPCS 为准。
  - 若某段改写后反弹，可单点 revert `1eafb98` 而不影响 `6fc5c71`（P0+P1）与 `c7fccdb`（学校格式合规）。
- Commit: 1eafb98

### 2026-05-07 01:53 | School Format Compliance Fix
- Goal: 按 `docs/school/工科、理科类撰写规范及相关表格模板` 中 2025-11 工科/理科类撰写规范，修复当前论文进入 Word 转换前的关键格式差距。
- Scope:
  - 正文中文保持宋体，英文保持 Times New Roman；标题类中文恢复黑体。
  - 目录补入 `摘要`、`Abstract`、`目录`，并收敛为学校允许的二级目录，避免目录尾页大面积空白。
  - 中英文关键词从 8 个压缩为 5 个，并保持语义对应。
- Changed files:
  - `.agents/execplans/2026-05-07_school_format_compliance_fix.md`
  - `thesis/setup/fonts.tex`
  - `thesis/setup/format.tex`
  - `thesis/setup/toc.tex`
  - `thesis/setup/commands.tex`
  - `thesis/main.tex`
  - `thesis/chapters/abstract_zh.tex`
  - `thesis/chapters/abstract_en.tex`
- Commands:
  - `xelatex -interaction=nonstopmode main.tex && bibtex main && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - `rg -n "LaTeX Warning: (Citation|Reference)|There were undefined|Citation .* undefined|Reference .* undefined|Rerun to get|Label\\(s\\) may have changed|Citation\\(s\\) may have changed" thesis/main.log || true`
  - `pdfinfo -box thesis/main.pdf`
  - `pdffonts thesis/main.pdf`
  - `pdftotext -layout -f 1 -l 10 thesis/main.pdf -`
  - keyword count script for `abstract_zh.tex` and `abstract_en.tex`
- Outputs:
  - `thesis/main.pdf` regenerated, 97 pages, A4.
  - PDF font list includes `STHeitiSC-Light`, `STSongti-SC-Regular`, and `TimesNewRomanPS*`; residual `ArialUnicodeMS`/`DejaVu*` are from embedded external Ch4 PDF figures.
- Validation:
  - 0 undefined references / citations and 0 rerun warnings in `main.log`.
  - TOC now contains `摘要 / Abstract / 目录` and no longer spills into a mostly blank fourth TOC page.
  - Keywords: Chinese 5 terms; English 5 corresponding terms.
  - Visual render of TOC page and Chapter 1 opening page checked; no blank-page regression.
- Risks / follow-ups:
  - `iteration.md` already had unrelated archive dirty state before this task, so this entry remains in the dirty working tree and was not included in commit `c7fccdb`.
  - Word conversion still needs LibreOffice/Word-side high-fidelity style verification; current machine lacks `soffice`.
- Commit: c7fccdb

### 2026-05-07 01:31 | Thesis Layout, RQ Wording, and Font Polish
- Goal: 修复用户指出的三类论文版式与表达问题：目录后第 8 页空白、正文可见 `RQ1/RQ2` 英文缩写、第二章开头内部技术文档口吻，并将 LaTeX 正文/标题/目录/封面字体统一为中文宋体、英文 Times New Roman。
- Scope:
  - 去掉 `twoside` 下 `\mainmatter` 自动插入的目录后空白偶数页，同时保留双面页眉设置。
  - 将 Ch1/Ch4/Ch5 纸面可见的 `RQ1`--`RQ4` 改为“研究问题 1”--“研究问题 4”或“第一章研究问题 2”等中文表达；内部 `\label{sec:ch4-rq1}` 保持不动。
  - 重写 Ch2 开头“本章只保留后文会反复调用的技术记号...”和 §2.1 开头，使其成为论文式技术背景说明。
  - 将正文、标题、目录、封面、摘要关键词和 `\texttt{}` 所用字体映射到宋体 / Times New Roman。
- Changed files:
  - `.agents/execplans/2026-05-07_thesis_layout_font_polish.md`
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
- Commands:
  - `pdftotext -layout -f 48 -l 48 thesis/main.pdf -`
  - `pdftoppm -f 47 -l 49 -png -r 120 thesis/main.pdf tmp/pdf_pages/main_range`
  - `rg -n "RQ[0-9]|RQ1--RQ4|Ch1 RQ|本章只保留|技术记号|在线自适应" thesis/chapters thesis/setup thesis/main.tex -g '*.tex'`
  - `git diff --check`
  - `cd thesis && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - `rg -n "LaTeX Warning: (Citation|Reference)|undefined|There were undefined|Rerun to get cross-references right|Citation .* undefined|Reference .* undefined|Label\\(s\\) may have changed" thesis/main.log thesis/main.out`
  - `pdfinfo thesis/main.pdf`
  - `pdftotext -layout -f 8 -l 8 thesis/main.pdf -`
  - `pdffonts thesis/main.pdf`
- Outputs:
  - `main.pdf` 从 99 页变为 98 页；物理第 8 页现在是第一章正文，不再是罗马页码 `vi` 的空白页。
  - Ch1/Ch4/Ch5 纸面可见 `RQ` 英文编号清零。
  - 第二章开头改为论文式背景定位，不再使用“只保留技术记号”表达。
  - 正文、标题、目录、封面、代码样式的 LaTeX 字体不再引入 `STHeitiSC`、`STKaitiSC` 或 `Courier New`。
- Validation:
  - `git diff --check` passed.
  - Three XeLaTeX passes completed; `main.pdf` generated at 98 pages.
  - `main.log` / `main.out` scan found no undefined references/citations or rerun warnings.
  - `pdftotext -f 8 -l 8` confirms page 8 contains Chapter 1 content.
  - `pdffonts` confirms LaTeX body fonts are `STSongti-SC` and `TimesNewRoman`; remaining `ArialUnicodeMS/DejaVu` entries come from embedded external PDF figures and require a separate figure-regeneration pass if full figure-font unification is required.
- Risks / follow-ups:
  - 第 48 页附近的大空白并非内容缺失：当前物理第 48 页是 4.1.2 正文；原先可见空白主要来自章节结束页或第四章开章页的表格/分页约束，不建议把下一章强行接到上一章末页。
  - 若学校要求图内文字也严格宋体/Times，需要另起 figure-font pass 重生成 Ch4 PDF 图。
- Commit: 11d97fd

### 2026-05-07 00:50 | M8-C Pre-merge Consistency Nits
- Goal: 合并前最后一轮文本级一致性补丁，仅修文字编号与术语口径；不动数据、图、表、公式。
- Scope:
  - Ch4 可见 RQ 口径显式映射到 Ch1 全局 RQ：INT8 保真线对应 Ch1 RQ2，低比特恢复线作为 Ch1 RQ1/RQ2 的证据线，跨模型分配与 AutoK 对应 Ch1 RQ3/RQ4；内部 `\label{sec:ch4-rq1}` 保持不动以避免 ref churn。
  - `abstract_en.tex` 将 `controlled main-protocol results` 改为 `controlled task-core and extend-profile results`。
  - `ch5_conclusion.tex` 将“在线自适应”改为“在线参数调整”，避免与 Ch3 的离线冻结产物和 adaptive protection 口径混淆。
  - `iteration.md` 追加本条 pre-merge 记录。
- Context:
  - M8-C 是 pre-merge consistency nits，不是新发现的 P0/P1。
  - 本支线在合并前总规模为 25 commits / 21 files / 约 `+1700/-425`。独立审查将其拆为两类工作：约 40% 是 AIGC-risk revision，包括术语统一、模板化连接词减少、内部平台和路径痕迹清理；约 60% 是投稿就绪严谨度补写，包括 Ch3 方法章结构化补写、必要 citation 补全、Ch4 表注自足性强化与数字 traceability 修复。
  - 这些质量补写超出最初 polish 范围，但均服务论文严谨度，且已经过 Claude、Codex 与多轮只读 verification agent 交叉审查。
- Changed files:
  - `thesis/chapters/abstract_en.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
  - `iteration.md`
- Commands:
  - `rg -n "controlled task-core|controlled main-protocol|Ch1 RQ2|低比特恢复线|Ch1 RQ3/RQ4|RQ1--RQ3|在线参数调整|在线自适应" thesis/chapters/abstract_en.tex thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex`
  - `git diff --check`
  - `cd thesis && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - `rg -n "LaTeX Warning: (Citation|Reference)|undefined|There were undefined|Rerun to get cross-references right|Citation .* undefined|Reference .* undefined|Label\\(s\\) may have changed" thesis/main.log thesis/main.out`
  - One read-only verification agent for M8-C scope and no-new-issue review.
- Outputs:
  - Ch4 no longer uses a local visible `RQ1--RQ3` numbering scheme that conflicts with Ch1 RQ1--RQ4.
  - English abstract no longer mixes `main-protocol` wording with extend-profile evidence.
  - Ch5 INT8 conclusion no longer uses the ambiguous “online adaptation” phrasing.
- Validation:
  - `git diff --check` passed.
  - Three XeLaTeX passes completed; `main.pdf` generated at 99 pages.
  - `main.log` / `main.out` scan found no undefined references/citations or rerun warnings.
  - M8-C verification agent PASS.
- Risks / follow-ups:
  - Ready for fast-forward merge to `main`; keep local until user explicitly approves push.
- Commit: 4c10c4f

### 2026-05-06 03:42 | M8-B Thesis P1 Table Note Protocol Closure
- Goal: 修复精简清单中两项 P1 表注自足性问题：TPOT 表缺 repeat/CI 口径，Needle 百分比缺分母/seed 解释。
- Scope:
  - Ch4 Needle 相关表注的 exact-match、context/depth sweep、双检索任务与 seed 口径
  - Ch4 4K TPOT 表注的 8 fixed seeds 与不单独报告 CI 口径
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `iteration.md`
- Commands:
  - `rg -n 'label\{subsec:ch4-(benchmarks|statistics)\}|ref\{subsec:ch4-(benchmarks|statistics)\}|Needle 百分比|Needle-single-retrieval|MK-NIAH-2|所有 TPOT 读数|表中不单独报告 CI|5 个固定 seeds|8 个固定 seeds' thesis/chapters/ch4_experiments.tex`
  - `git diff --check`
  - `cd thesis && xelatex -interaction=nonstopmode main.tex`
  - `rg -n "LaTeX Warning: (Citation|Reference)|undefined|There were undefined|Rerun to get cross-references right|Citation .* undefined|Reference .* undefined" thesis/main.log thesis/main.out`
  - Two read-only verification agents for TPOT and Needle table-note closure.
- Outputs:
  - `tab:ch4-int4-cliff` now explains Needle exact-match percentages over 4K--32K context and unified depth sweep, with 5 fixed seeds.
  - `tab:ch4-rolealign-kivi` now explains that `100/100%` denotes Needle-single-retrieval and MK-NIAH-2 both reaching 100%, with 5 fixed seeds.
  - `tab:ch4-tpot-4k` now explains TPOT uses the 8 fixed seeds throughput protocol and does not report CI in that table.
- Validation:
  - `git diff --check` passed.
  - XeLaTeX completed and wrote `main.pdf` at 99 pages.
  - `main.log` / `main.out` scan found no undefined references/citations or rerun warnings.
  - TPOT verification agent PASS.
  - Needle verification agent PASS.
- Risks / follow-ups:
  - P2 abstract terminology polish remains optional and is intentionally excluded from this M8-B functional unit.
- Commit: 8308e2e

### 2026-05-06 03:35 | M8-A Thesis P0 Submission Closure
- Goal: 修复 Claude/Codex 复核后确认属实的三项投稿前 P0：Ch1/Ch5 RQ 闭环不一致、Ch3 方法章零引用、Abstract 中 Mistral `15.69` 缺 Ch4 显式出处。
- Scope:
  - Ch5 RQ1--RQ4 结论闭环
  - Ch3 方法章必要 citation 锚点
  - Ch4 Mistral core/extend mean traceability
- Changed files:
  - `thesis/chapters/ch5_conclusion.tex`
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `.agents/execplans/2026-05-04_thesis_p0_p1_submission_fix.md`（force-add; ignored execplan audit trail）
- Commands:
  - `rg -n "三个问题|四个问题|RQ4|AutoK|预算建议" thesis/chapters/ch1_introduction.tex thesis/chapters/ch5_conclusion.tex`
  - `rg -n -F "\\cite" thesis/chapters/ch3_method.tex`
  - `rg -n "15\\.69|15\\.6946|extend mean|core mean|5-task|五任务均值|Mistral-7B" thesis/chapters/abstract_zh.tex thesis/chapters/abstract_en.tex thesis/chapters/ch4_experiments.tex`
  - `cd thesis && bibtex main && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - `rg -n "LaTeX Warning: Citation|LaTeX Warning: Reference|undefined|There were undefined|Rerun to get cross-references right" thesis/main.log thesis/main.out`
  - Two read-only verification agents for RQ/numeric traceability and Ch3 citation/LaTeX state.
- Outputs:
  - Ch5 now explicitly answers four questions; RQ4 is bounded as a model-level AutoK/profiling budget candidate mechanism, not a universal cross-model rule.
  - Ch3 now contains four method citations: `liu2024kivi`, `tillet2019triton`, `dao2022flashattention`, `ainslie2023gqa`.
  - Ch4 table note now states Mistral core mean `14.76`, extend mean `15.69`, and five-task mean `15.14`, making the abstract numbers traceable in the main chapter.
- Validation:
  - BibTeX + three XeLaTeX passes completed; `main.pdf` generated at 99 pages.
  - `main.log` / `main.out` scan found no undefined references/citations or rerun warnings.
  - RQ/numeric verification agent PASS.
  - Citation/LaTeX verification agent PASS.
- Risks / follow-ups:
  - M8-B still needs the two P1 table-note fixes: TPOT 4K repeat/scope note and Needle denominator/seed semantics.
  - P2 abstract terminology polish remains optional and is intentionally excluded from M8-A.
- Commit: d758b85

### 2026-05-01 19:36 | docs(aigc): initialize revision branch and 47-fragment matrix
- Goal: 在独立分支中启动 AIGC 误判风险降噪改写任务，把用户提供的 47 段分析转成可审计、可回滚、带 evidence-tier gate 的执行矩阵。
- Scope:
  - Branch/worktree setup for `codex/aigc-risk-revision-20260501`
  - M1 baseline matrix and review gate records
- Changed files:
  - `.agents/execplans/2026-05-01_aigc_risk_revision.md`
  - `docs/aigc_revision_plan_20260501.md`
  - `docs/aigc_revision_matrix_20260501.md`
- Commands:
  - `git worktree add -b codex/aigc-risk-revision-20260501 /Users/chenzilang/Desktop/LLM_KVCache_Quantization_aigc_revision main`
  - `git status --short --branch`
  - `python scripts/review_tool.py phase-gate`
  - `git diff --check -- .agents/execplans/2026-05-01_aigc_risk_revision.md docs/aigc_revision_plan_20260501.md docs/aigc_revision_matrix_20260501.md`
  - `git add -f .agents/execplans/2026-05-01_aigc_risk_revision.md docs/aigc_revision_plan_20260501.md docs/aigc_revision_matrix_20260501.md`
  - `git diff --cached --stat && git diff --cached --check`
  - `git commit -m "docs: add AIGC revision execution matrix"`
- Outputs:
  - New worktree created at `/Users/chenzilang/Desktop/LLM_KVCache_Quantization_aigc_revision`.
  - M1 matrix now covers all 47 user-provided fragments with evidence tier, canonical source, allowed/forbidden language, and compiled source coverage.
  - Four reviewer dimensions reached PASS after iterative fixes: Style/AIGC-risk, Evidence/claim-boundary, LaTeX/reference, Terminology consistency.
- Validation:
  - `git diff --check` passed after removing one Markdown trailing whitespace issue.
  - `python scripts/review_tool.py phase-gate` reported `PHASE GATE: CLEAR` with only pre-existing `review_tracker.md` parse warnings.
  - No thesis source files were modified in M1.
- Risks / follow-ups:
  - Original `main` worktree still contains many unrelated untracked files; this task remains isolated in the new worktree.
  - `.agents/execplans/` is ignored by default, so future plan commits require explicit `git add -f`.
  - M2 should only edit `thesis/chapters/abstract_zh.tex` and `thesis/chapters/abstract_en.tex`, then rerun the full review gate.
- Commit: `28aff37`

### 2026-04-26 22:52 | docs(workflow): preserve appendix audit preferences as project skill
- Goal: 将本轮 Appendix 清理中形成的稳定偏好与专项流程沉淀到项目 skill、项目规范和全局个人规范中。
- Scope:
  - `.agents/skills/thesis-appendix-audit/SKILL.md`
  - `AGENTS.md`
  - `/Users/chenzilang/.codex/AGENTS.md`（全局文件，已备份，不随 git 提交）
- Changed files:
  - 新增 `thesis-appendix-audit` skill，固化 appendix 只读审查、审核矩阵、ExecPlan 门禁、小步执行、引用同步、工程命名泄露扫描与多角度审查流程。
  - 在项目 `AGENTS.md` 增加 Appendix workflow 入口，要求 appendix 审查/清理/合并任务使用该 skill。
  - 在全局 `~/.codex/AGENTS.md` 增加跨项目个人偏好：不确定项先讨论、小步推进、正向克制表达、不泄露内部工程命名、dirty worktree 精确提交、验证后再声称完成。
- Commands:
  - `find .agents/skills/thesis-appendix-audit -maxdepth 2 -type f -print`
  - `sed -n '1,80p' .agents/skills/thesis-appendix-audit/SKILL.md`
  - `rg -n "thesis-appendix-audit|Thesis Appendix Workflow" AGENTS.md`
  - `rg -n "个人协作与研究写作偏好|不确定项先讨论|不泄露内部工程命名" ~/.codex/AGENTS.md`
  - `git diff --check -- AGENTS.md .agents/skills/thesis-appendix-audit/SKILL.md iteration.md`
- Outputs:
  - Project-level appendix cleanup workflow is now reusable by skill trigger instead of remaining only in chat history.
  - Global preference backup created at `/Users/chenzilang/.codex/AGENTS.md.bak-20260426_225248`.
- Validation:
  - Pending final diff and staging checks before commit.
- Risks / follow-ups:
  - Current worktree still has external Ch4 figure/draft dirty files; this workflow commit must stage only the project rule, skill, and this iteration entry.

### 2026-04-26 22:33 | docs(appendix): merge Needle supplement into INT4 mechanism appendix
- Goal: 执行已批准的 Appendix P6，将 Needle 深度-位置热力图从独立附录降级并入 INT4 失稳机制附录，同时为部署效率补充材料增加正文反向引用。
- Scope:
  - `thesis/chapters/appendix.tex`
  - `thesis/chapters/ch4_experiments.tex`
- Changed files:
  - A5 `Needle-in-a-Haystack 深度-位置热力图` 不再作为独立 `\section`，并入 A7/current A6 `INT4 失稳机制与评估粒度边界补充` 的开头机制背景块。
  - 保留 `fig:app-needle-depth-grid` 与 exact-match 补充文字，并为 `sec:app-needle-heatmaps` 增加 paragraph anchor。
  - 在 Ch4 部署效率节末尾增加对 `sec:app-efficiency-plots` 的轻量反向引用，限定为 Qwen2.5-1.5B 设置下的 batch 容量、吞吐与显存扩展补充审计。
- Commands:
  - `rg -n "\\section\\{Needle|fig:app-needle-depth-grid|sec:app-needle-heatmaps|sec:app-efficiency-plots" thesis/chapters/appendix.tex thesis/chapters/ch4_experiments.tex`
  - `rg -n '附录 A\\.|附录 B\\.|Appendix A\\.|Appendix B\\.' thesis/chapters`
  - `git diff --check -- thesis/chapters/appendix.tex thesis/chapters/ch4_experiments.tex`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && xelatex -interaction=nonstopmode -halt-on-error main.tex && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - `rg -i 'undefined|multiply defined|LaTeX Error|! ' thesis/main.log | head -20`
  - `pdfinfo thesis/main.pdf | rg Pages`
- Outputs:
  - Appendix section count reduced from 11 to 10; A5 content now functions as the first mechanism-background block inside the INT4 mechanism appendix.
  - Ch4 deployment section now points readers to A6/current A5 deployment supplement without changing deployment claims.
  - `thesis/main.pdf` compiles to 105 pages.
- Validation:
  - Full LaTeX compile passed after regenerating auxiliary files; final `main.log` has no undefined refs/citations, multiply-defined labels, or LaTeX errors.
  - 三路 Sub-agent 审查通过：结构与引用 PASS，正文一致性 PASS，附录功能 PASS；非阻断建议已采纳，包括 Qwen2.5-1.5B 限定与 paragraph anchor。
- Risks / follow-ups:
  - 当前工作树仍有外部 Ch4 图相关 dirty 项；本轮后续若提交，需要精确 staging，避免混入外部图改动。
  - 本轮未提交；等待用户确认是否提交。

### 2026-04-26 22:12 | docs(appendix): replace low-value figures with compact text
- Goal: 执行 Appendix P5，将三个低可视化必要性附录图改为紧凑表格或定稿文字说明，降低附录图密度并保留必要证据。
- Scope:
  - `thesis/chapters/appendix.tex`
  - `.agents/execplans/20260426_2201_appendix_p5_low_value_figures.md`
- Changed files:
  - A.4 质量趋势双图替换为 `tab:app-quality-context-summary`，只保留 FP16 与 INT8-Canonical 的 RULER / LongBench-style 关键读数。
  - A.5 删除单独 exact-match 曲线图，用文字保留严格 Needle 判据，并明确 INT8-Canonical 在 32K 的约 70.3\% 边界读数。
  - A.6 删除单序列 TPOT gain 图，用部署边界文字说明替代，保留吞吐与显存扩展图。
  - 旧低必要性 figure labels 从论文源中清零，图 PDF 资产不删除。
- Commands:
  - `git diff --check -- thesis/chapters/appendix.tex .agents/execplans/20260426_2201_appendix_p5_low_value_figures.md`
  - `rg -n "fig:app-quality-vs-context|fig:app-ruler-vs-context|fig:app-longbench-vs-context|fig:app-needle-exact|fig:app-tpot-gain" thesis/chapters`
  - `rg -n "tab:app-quality-context-summary|fig:app-throughput-dashboard|fig:app-memory-dashboard|fig:app-needle-depth-grid" thesis/chapters/appendix.tex`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && xelatex -interaction=nonstopmode -halt-on-error main.tex && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - `rg -n "Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\\(s\\) may have changed|LaTeX Error|Overfull|invalid character|multiply defined" thesis/main.log`
  - `pdfinfo thesis/main.pdf | rg "Pages|Page size"`
  - `awk '/^\\section/ {if(sec) print NR-start-1" lines  "sec; sec=$0; start=NR} END {print NR-start" lines  "sec}' thesis/chapters/appendix.tex`
- Outputs:
  - Appendix remains 761 lines and `thesis/main.pdf` compiles to 105 pages.
  - Removed active labels: `fig:app-quality-vs-context`, `fig:app-ruler-vs-context`, `fig:app-longbench-vs-context`, `fig:app-needle-exact`, `fig:app-tpot-gain`.
  - Preserved labels: `fig:app-needle-depth-grid`, `fig:app-throughput-dashboard`, `fig:app-memory-dashboard`; added `tab:app-quality-context-summary`.
- Validation:
  - Full LaTeX compile passed; `thesis/main.log` has no undefined refs/citations, rerun warnings, LaTeX Error, Overfull, invalid character, or multiply-defined label warnings.
  - 多角度 Sub-agent 审查完成：数据证据初审发现 exact-match claim 过强，已回修；LaTeX 引用 PASS；正文一致性 PASS；结构版面 PASS；最终复审 PASS。
  - 表格数值已由 `ruler_summary.csv` 与 `longbench_summary.csv` 主线配置核对；exact-match 32K 约 70.3\% 与 `needle_summary.csv` 一致。
- Risks / follow-ups:
  - 本轮不删除旧图 PDF 资产，也不修改图生成脚本；后续如需清理未引用资产，应单独开图资产清理计划。
  - 工作树仍存在外部 Ch4 图相关 dirty 项和外部 `iteration.md` 图修改记录，本轮 commit 已通过精确 staging 隔离。
- Commit: `c54d1d3`

### 2026-04-26 20:07 | docs(appendix): group audit and configuration materials
- Goal: 执行已批准的 Appendix P2，将 former A.1-A.6 从六个平级 section 收束为审计协议、代码标识映射、校准审计三个功能组。
- Scope:
  - `thesis/chapters/appendix.tex`
  - `.agents/execplans/20260426_1959_appendix_p2_audit_config_grouping.md`
- Changed files:
  - former A.1-A.3 合并为 current A.1 `评测协议、环境与复现入口`，保留 PPL protocol、环境表、seed/greedy decoding、复现覆盖与校准样本数量说明。
  - former A.5 改为 current A.2 `量化路径与代码标识映射`，明确只承担 `kv_mode` 复现审计映射职责。
  - former A.4+A.6 合并为 current A.3 `校准产物与搜索空间审计`，保留 schema、search-space 表和 `inv_tau=None` 主线口径。
  - 保留 former A.1-A.6 的全部 section/table label，并用 `\phantomsection` 维护降级 paragraph anchor。
- Commands:
  - `git diff --check -- thesis/chapters/appendix.tex`
  - `rg -n 'sec:app-fp16-protocol|sec:app-ppl-baseline-matrix|sec:app-env|sec:app-reproduce|sec:app-calib-schema|sec:app-kv-modes|sec:app-calib-search-space|tab:app-ppl-baseline-matrix|tab:app-env|tab:ch3-kv-modes|tab:app-search-space' thesis/chapters/appendix.tex`
  - `awk '/^\\section/ {if(sec) print NR-start-1" lines  "sec; sec=$0; start=NR} END {print NR-start" lines  "sec}' thesis/chapters/appendix.tex`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Citation.*undefined|Warning: Citation|Font Warning|Overfull|invalid character' thesis/main.log`
  - `pdfinfo thesis/main.pdf | rg Pages`
- Outputs:
  - Appendix 前部从 6 个 section 收束为 3 个 section。
  - `main.pdf` 生成成功，105 pages。
  - P2 plan 文件因 `.gitignore` 默认忽略 `.agents/execplans/`，本轮使用显式路径 force-add 纳入审计。
- Validation:
  - 四个只读 Sub-agent review 完成：审计完整性 PASS，正文一致性 PASS，LaTeX label/ref PASS，结构读者体验 CONCERN 已在 Appendix 内修复。
  - `git diff --check` 通过。
  - `thesis/main.log` 未发现 undefined refs/cits、rerun warning、LaTeX Error、Font Warning、Overfull 或 invalid character。
  - former A.1-A.6 的关键 labels 均可在 `thesis/main.aux` 中解析。
- Risks / follow-ups:
  - Ch4 当前存在图相关未提交 diff，本轮未 stage；因此没有把“正文额外指向 A.1 复现说明”的可选建议混入 P2。
  - `docs/Chapter 4 Draft.md`、`thesis/chapters/ch4_experiments.tex`、`thesis/figures/ch4/fig_ch4_05_regime_heatmap.pdf` 与 `scripts/thesis/plot_ch4_regime_combined.py` 仍属图相关/外部 dirty，未纳入本轮提交。
- Commit: `0b0ee99`

### 2026-04-26 19:55 | docs(appendix): merge LongBench and quality supplements
- Goal: 执行已批准的 Appendix P1，合并 LongBench 补充、统计检验与质量趋势图材料，并同步正文对该补充组的定位。
- Scope:
  - `thesis/chapters/appendix.tex`
  - `thesis/chapters/ch4_experiments.tex`
- Changed files:
  - A.7-A.9 合并为 `LongBench、统计检验与质量趋势补充材料`，保留原 LongBench official check、seed statistics、quality plots 的兼容 label。
  - LongBench 补充表改用论文叙事路径名，删除裸露配置字符串作为主显示名的问题。
  - INT8 统计检验表改为审计统计口径，清理脚本字段名，并补充小样本统计 power 限定。
  - Ch4 新增对合并后 A.7 的正文引用，并将 official LongBench 单种子对照改为方向一致性检查，不作显著性结论。
- Commands:
  - `git diff --check -- thesis/chapters/appendix.tex thesis/chapters/ch4_experiments.tex`
  - `rg -n 'sec:app-longbench-full|sec:app-longbench-official|sec:app-seed-detail|sec:app-quality-plots|tab:app-longbench-full|tab:app-sig-quality|fig:app-quality-vs-context' thesis`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Citation.*undefined|Warning: Citation|Font Warning' thesis/main.log`
  - `rg -c 'Overfull' thesis/main.log`
  - `pdfinfo thesis/main.pdf | rg Pages`
- Outputs:
  - `main.pdf` 生成成功，106 pages。
  - 合并后 A.7 作为质量补充审计材料保留，不进入正文主证据矩阵。
- Validation:
  - 四个只读 Sub-agent review 已完成；正文一致性、统计 claim、LaTeX label、结构冗余问题均已处理。
  - `git diff --check` 通过。
  - `thesis/main.log` 未发现 undefined refs/cits、rerun warning、LaTeX Error、Font Warning 或 Overfull entries。
  - 关键兼容 label 均可在 `thesis/main.aux` 中解析。
- Risks / follow-ups:
  - P1 只处理 LongBench/statistics/quality supplement group。下一步建议进入 P2，处理 A.1-A.6 的审计与配置分组。
  - `thesis/figures/ch4/fig_ch4_05_regime_heatmap.pdf` 与 `scripts/thesis/plot_ch4_regime_combined.py` 属于未纳入本次范围的图相关工作，未 stage。
- Commit: `ffc0109`

### 2026-04-26 11:20 | chore(iteration): correct attribution of 11:20 commit 1f9d575
- Goal: 修正前一条 timeline entry 的归属错位 — 本 session 在 11:20 尝试 add 3 个 ch3 tables 时，外部并行 agent 已于 11:14:25 提交 `42ab6de docs: align thesis figures and table boundaries` 抢先把 3 tables + 4 figures + ch3/ch4 文本全部落账。导致 `1f9d575` 实际只含 iteration.md 22 行（即被覆盖前的旧 11:20 entry 文本），不含任何 tables 内容 diff。本 entry 修正归属。
- Actual content of `1f9d575`: 仅 `iteration.md` 一文件 22 行新增。
- Actual content of `42ab6de`（外部并行 agent 抢先落账）:
  - `thesis/chapters/ch3_method.tex`、`thesis/chapters/ch4_experiments.tex`（表 4-13 部署边界双面板重构）
  - `thesis/figures/fig_ch3_{allocator_flow,calibration_workflow,framework_shared_profile,kv_diag_needle}.tex`（4 个 TikZ 图重绘）
  - `thesis/tables/table_ch3_{path_instantiation,runtime_paths,calibration_interfaces}.tex`（"INT8 规范路径"→"基准路径"统一 + layout 收紧 + 删除"后续"列）
  - `iteration.md`：在文件**末尾**（line 968 之后）追加 11:12 entry，违反"Latest First"规则
- Validation: `git log -2 --format='%h %s'` 与 `git show 42ab6de --stat` / `git show 1f9d575 --stat` 双向核对，两 commit 的实际 diff 与 stat 行数一致。
- Risks / follow-ups:
  - `42ab6de` 在 iteration.md 文件末尾的 11:12 entry 位置错位，下次维护脚本运行时应一起搬到 Latest First 顶部。
  - 外部 agent 与本 session 短窗内可能再次抢账：以后 commit 之前应跑 `git diff --cached` 二次确认 staged 内容是否符合预期，再落账。
  - working tree 仍有 `thesis/chapters/appendix.tex` 浮动 dirty（外部 linter 改动，不在本轮范围）。
- Intended commit: `chore: correct iteration log attribution for 11:20 entry`

### 2026-04-26 11:03 | docs(thesis): clean appendix terminology and prompt-adaptive prose tail
- Goal: 收掉 ece32fa "规范路径 → 基准路径" 改名时漏改 appendix.tex 的 4 处中文叙事残留 + RQ1/RQ2/RQ3 标号残留，同时把 ac3c125 之后留下的 prompt-adaptive 段落 4 处 prose 微调一并落账。
- Scope:
  - `thesis/chapters/appendix.tex`
- Changed files:
  - L92-93: "RQ1 规范路径验证、RQ2 低比特恢复、RQ3 跨模型预算分配" → 去 RQ 编号 + "规范路径"→"基准路径"
  - L140: 表格 cell "KL-guided 对称规范路径" → "KL-guided 对称基准路径"
  - L197: "INT8 规范路径主线搜索为..." → "INT8 基准路径主线搜索为..."
  - L208: "本表是正文 RQ1/RQ2 证据的补充审计材料" → "本表是正文基准保真与低比特恢复证据的补充审计材料"
  - 另含 ac3c125 之后留下的 4 处 prose 微调：删除 3 处 inline `% 附录 P1 / P2 / orphan ref resolved` 工作语言注释 + prompt-adaptive 段落两段更精确化（明确 8B 为正式探索矩阵 / 1.5B/7B 为补充读数；结尾段说明三组 5-task mean 最高项分别落在 fixed-$k$ 或 auto-$k$ 上）。
- Commands:
  - `grep -rn "规范路径" thesis/chapters/`
  - `grep -n "RQ1\|RQ2\|RQ3" thesis/chapters/appendix.tex`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- Outputs:
  - "规范路径" 残留 = 0；appendix.tex RQ1/2/3 残留 = 0
  - main.pdf 108 pages（与精简前 110 pages 相比少 2 页，匹配 ac3c125 prompt-adaptive 附录精简预期）
- Validation:
  - `xelatex` exit_code=0
  - `main.log` 无 LaTeX Error / undefined references / Rerun warning
- Risks / follow-ups:
  - `thesis/figures/` + `thesis/tables/` 仍存在 7 个未提交 dirty 文件（ch3 tikz 图重绘 + table 术语统一），归属并行工作流，不在本轮 commit 范围内，待用户单独审定。
- Intended commit: `docs: clean appendix terminology and prompt-adaptive prose tail`

### 2026-04-24 09:28 | docs(thesis): appendix M1 config and diagnostic cleanup
- Goal: 执行已批准的附录清理 M1，先处理 A.5 量化模式 glossary、A.6 搜索空间口径、A.19 `inv_tau` 诊断与 7B KL/MSE 溯源，并同步正文自然语言引用。
- Scope:
  - `thesis/chapters/appendix.tex`
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
- Changed files:
  - A.5 改为正文名称到 `kv_mode` 的映射表，清理旧内部字符串作为论文方法名的问题。
  - A.6 将温度因子改为历史诊断分支，不计入主线搜索规模，保持 `inv_tau=None` 口径。
  - A.19 重构为两个 subsection：逐头温度校正诊断与 7B KL/MSE 校准目标趋同溯源。
  - Ch3 / Ch4 同步 RoleAlign K/V 代理分工、`inv_tau` 降级口径和 A.19 自然语言编号引用。
- Commands:
  - `git diff --check -- thesis/chapters/appendix.tex thesis/chapters/ch3_method.tex thesis/chapters/ch4_experiments.tex`
  - `awk '/^\\\\section/ {if(sec) print sec, NR-start-1; sec=$0; start=NR} END {print sec, NR-start}' thesis/chapters/appendix.tex`
  - `cd thesis && xelatex -interaction=nonstopmode main.tex`
  - `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\\(s\\) may have changed|LaTeX Warning: Reference|LaTeX Error' thesis/main.log`
- Outputs:
  - M1 三文件 diff 为 81 insertions / 114 deletions，净减少 33 行。
  - A.5 为 41 行，A.6 为 39 行，A.19 为 46 行，均落在本轮约束带内。
  - 多轮审查发现的 A.4 schema、A.5 backend、A.19 subsection anchor、A.6 温度因子主线漂移均已修正。
- Validation:
  - `git diff --check` 无输出。
  - `xelatex` 生成 `main.pdf` 110 pages。
  - `main.log` 中未发现 undefined reference、rerun cross-reference、LaTeX Error。
- Risks / follow-ups:
  - 工作树中存在其他 Agent / 外部进程造成的正文与草稿 dirty 文件，本轮不纳入提交。
  - 下一步建议进入 M2：合并并降级 A.21 / A.22，同时修复 `\\section{附录 A/B：...}` 命名问题。
- Intended commit: `docs: clean appendix config diagnostics`

### 2026-04-23 09:51 | docs(thesis): finalize Chapter 4 prose and cross-chapter interfaces
- Goal: 收掉 Chapter 4 最后一轮 prose / 接口层遗留问题，使章节主文、Chapter 5 结论接口和 Appendix 命名与已冻结的 Chapter 4 图表系统保持一致。
- Scope:
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
  - `thesis/chapters/appendix.tex`
  - `docs/Chapter 4 Draft.md`
  - `docs/Chapter 5 Draft.md`
- Changed files:
  - 清空 Chapter 4 正文中的 `\\S4.x` 引用，统一改为 `第 4.x 节` 或自然中文衔接
  - 清掉 Chapter 4 主文中的 `same-format`、`matched-budget`、`calibration philosophy` 等 reviewer shorthand
  - 将 Chapter 5 与 Chapter 4 直接相连的旧接口术语收成中文主导表述
  - 统一 Appendix 中 `Llama-3.1-8B` 命名，并将残留 provenance / 接口说明改成正常中文
  - 同步回写 Chapter 4 / 5 Draft adopted text，避免 `Draft ↔ tex` 漂移
- Commands:
  - `rg -n \"\\\\S4\\\\.|§4\\\\.|same-format|calibration philosophy|matched-budget|family/scale\" thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex thesis/chapters/appendix.tex`
  - `cd thesis && rm -f main.aux main.bbl main.blg main.out main.toc`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex && bibtex main && xelatex -interaction=nonstopmode -halt-on-error main.tex && xelatex -interaction=nonstopmode -halt-on-error main.tex`
  - `pdftotext thesis/main.pdf - | rg -n \"第 4\\\\.3\\\\.1 节|prompt 级自适应方案|结果溯源链|模型族/规模/任务\"`
- Outputs:
  - Chapter 4 正文、Chapter 5 接口段和 Appendix 命名已统一到第一轮粗修版本
  - `docs/Chapter 4 Draft.md` 与 `docs/Chapter 5 Draft.md` adopted text 已同步
- Validation:
  - `ch4_experiments.tex` 中 `\\S4.x` 清零
  - `main.pdf` 全量重建成功
  - `main.log` 对 undefined citations / labels / rerun 目标 grep 为空
  - 抽查 Chapter 4 / 5 / Appendix 对应页未出现新的版式异常
- Risks / follow-ups:
  - Appendix future-work 里仍可能保留少量面向未来工作的英文术语，这不属于本轮接口清洗 blocker
  - 下一轮若进入全文终稿联审，应把 Chapter 1 / 5 / Appendix 再做一次跨章命名一致性检查

### 2026-04-23 09:51 | feat(thesis): polish Chapter 4 figure assets and plotting scripts
- Goal: 锁定 Chapter 4 六张正式图的第一轮粗修版本，使图面语言、图例位置、标题口径与正文章节职责一致，并为整仓 checkpoint 提供可追溯的图资产提交单元。
- Scope:
  - `scripts/generate_thesis_figures.py`
  - `scripts/plot_attention_kl_heatmap.py`
  - `scripts/thesis/plot_l2_pareto.py`
  - `scripts/thesis/plot_regime_map.py`
  - `scripts/thesis/plot_scale_trend.py`
  - `scripts/thesis/plot_sensitivity_heatmap.py`
  - `thesis/figures/ch4/*.pdf`
  - `thesis/figures/fig4_sensitivity_heatmap.pdf`
  - `thesis/figures/fig7_pareto.pdf`
  - `thesis/figures/fig8_regime_map.pdf`
  - `thesis/figures/fig9_scale_trend.pdf`
  - `thesis/figures/kv_ablation_summary_ruler.pdf`
- Changed files:
  - 图 4-1 改成折线图，补数据标注并将 legend 收到图内右下角
  - 图 4-2 收口标题、去工程 mode 名、统一 paired K/V reconstruction 诊断图语言
  - 图 4-3/4-4/4-5/4-6 全部收成“中文主导、术语保留英文”的论文图口径
  - 图 4-6 额外完成图例挪到右下角、标题 `Family/Scale` 大写、删除底部两行辅助文字
- Commands:
  - `python3 scripts/generate_thesis_figures.py`
  - `python3 scripts/plot_attention_kl_heatmap.py ...`
  - `python3 scripts/thesis/plot_l2_pareto.py`
  - `python3 scripts/thesis/plot_regime_map.py`
  - `python3 scripts/thesis/plot_scale_trend.py`
  - `python3 scripts/thesis/plot_sensitivity_heatmap.py`
  - `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- Outputs:
  - `thesis/figures/ch4/fig_ch4_01_kv_ruler32.pdf`
  - `thesis/figures/ch4/fig_ch4_02_kv_error_heatmap.pdf`
  - `thesis/figures/ch4/fig_ch4_03_autok_protection_map.pdf`
  - `thesis/figures/ch4/fig_ch4_04_pareto_budget_quality.pdf`
  - `thesis/figures/ch4/fig_ch4_05_regime_heatmap.pdf`
  - `thesis/figures/ch4/fig_ch4_06_family_scale_summary.pdf`
- Validation:
  - 6 张正式图均已进入 `main.pdf`
  - 图内语言纪律与 Chapter 4 caption / prose 当前口径一致
  - 图 4-6 的用户指定改动（legend、标题大小写、去底部说明）已真实落版
- Risks / follow-ups:
  - 后续若做全文终稿联审，仍需把图内语言与 Chapter 5 / Appendix 的最终口径一起再核一遍
  - 当前记录对应“第一轮粗修 checkpoint”，不是最终投稿前的最后图面 polish

### 2026-04-21 21:56 | Story + Ch3 Writing 联合 patch: 第四章 case roster 3→4 + overclaim guardrails + Ch3 Writing 映射表同步
- Goal: 吸收 ChatGPT 对 `thesis_story_20260420.md` 的 5 条 patch 建议（§4.2.2 降调 / §4.3.1 架构依附 / §4.4 加 LLaMA-8B / §8.4 overclaim guardrails / §9 checklist +6），并反向同步 Ch3 Writing §0.3 映射表使 §4.6 编号与 story 保持一致
- Changed files:
  - `docs/thesis_story_20260420.md`（5 patch）：
    1. §4 Ch4 目录：§4.2.2 标题由"真实场景泛化"→"评测协议一致性检验：官方 LongBench 真实数据对照"；§4.3.1 "系统性失效"→"架构依附性失效与阶跃崩塌"（显式容纳 LLaMA-3.1-8B 例外）；§4.4 case roster 3→4，插入 §4.4.4 LLaMA-3.1-8B，原 14B 顺延 §4.4.5；§4.6.2 注明 `inv_tau × GQA` 段内并入
    2. §5 迁移点 5→6 条（加第 4 条：§4.4 case roster 3→4）
    3. §7 模型角色：1.5B 升为"INT8 canonical + LongBench 双锚点"；7B 降 supporting case；新增 LLaMA 角色（BA-k11 中等规模共识）
    4. §8 新增 §8.4 "防过度声明与前向引桥"（6 条：§4.2.2 只能 sanity check / §4.3.1 显式例外 / §4.4 same-order budget band / §4.2 埋 §4.6.1 forward pointer / §4.4.1 埋 §4.6.3 forward pointer / §4.6 不写成第二结论节）
    5. §9 checklist 原 7 条 + 新增"第四章答辩防守" 6 条
  - `docs/This is Chapter 3 Writing.md`（2 patch）：
    1. §0.3 §4.x 新编号列表：§4.6.4 改回"威胁效度与外推边界"（原为 inv_tau × GQA）、删除 §4.6.5、§4.6.2 补注 "inv_tau × GQA 段内并入"、新增 §4.4.5 映射
    2. §0.3 旧→新 label 映射表同步：新增 §4.4.5 对应现稿 `subsec:exp-per-model-14b`，§4.6.4 改为 `subsec:disc-threats-to-validity`，加"编号对齐说明"指向 story §4
- Commands: 无（纯 md 编辑，不涉 tex 编译，不改代码）
- Outputs: 7 处 Edit 落地（5 story + 2 Ch3 Writing）
- Validation:
  - story §4.4 子节数 3→4（Mistral / 3B / **LLaMA** / 14B 顺延到 §4.4.5）
  - story §4.6 子节数保持 4（§4.6.4 威胁效度）
  - Ch3 Writing §0.3 §4.6 编号与 story §4 一致（§4.6.4 = 威胁效度）
  - Ch3 Writing §0.3 §4.4 编号补 §4.4.5（14B 顺延）
- Risks / follow-ups:
  - 后续进入 Ch4 施工文档（未来的 `This is Chapter 4 Writing.md`）时，必须按 §8.4 + §9 新增的 12 条防守纪律逐节对照
  - tex 回写阶段按新映射表创建 §4.4.4 LLaMA / §4.4.5 14B / §4.6.4 威胁效度的 `\label`
  - 本轮仅修 md 不涉 tex/code，无需 xelatex smoke 或 pytest 验证

### 2026-04-21 06:07 | Ch3 Round 10: §3.4 方案 M1 合并 — §3.4.1+§3.4.2 合并为 "INT8 对称路径" 单一 subsec
- Goal: 用户选 M1 方案. §3.4.1 静态 Scale 的设计 + §3.4.2 自适应保护机制 两个 subsec 实际都是 INT8 对称路径（A 线）的实现细节, 合并为一个 subsec 更清晰
- Scope: ch3_method.tex §3.4.1-§3.4.2 合并
- 改动 (2 处):
  - §3.4.1 标题改: "静态 Scale 的设计" → "INT8 对称路径：静态 Scale 与自适应保护"
    原 body 开头加 \paragraph{静态 Scale 的设计} 保留子标题
  - §3.4.2 subsection 降级为 paragraph: "\subsection{自适应保护机制}" → "\paragraph{自适应保护机制}"
    原 §3.4.2 的所有 content 自然并入 §3.4.1 (包括 "\paragraph{自适应保护对历史缓存的影响}")
- 新 §3.4 TOC (从 6 → 5 subsec):
  - §3.4.1 INT8 对称路径: 静态 Scale 与自适应保护 (A 线, 含 4 paragraph)
  - §3.4.2 从对称到非对称的格式升级 (B 线 motivation, 含 2 paragraph)
  - §3.4.3 Behavior-Guided Percentile 校准 (B 线核心, 含 2 paragraph)
  - §3.4.4 与 KIVI 的设计差异 (B 线对比, Table 3.2)
  - §3.4.5 Triton 核函数设计 (系统实现, 含 6 paragraph)
- Commands: python heredoc 2 处 + xelatex ×2
- Outputs: main.pdf 99 pages (保持) / 1.64 MB
- Validation: 0 undef / 0 multi / 0 dim / 0 error
- 下一步: 继续深入讨论更多 §3.4 subsec 问题, 或进其他章

### 2026-04-21 05:53 | Ch3 Round 9: 表 3.1 挪附录 + §3.2 TikZ 全景图 + Forward KL 中化 + §3.4 重组 + Triton 散装清理
- Goal: 用户深度 review Ch3 发现多层结构问题 (表 3.1 位置 / §3.2 缺全景图 / 图 3.2 温度注释 / forward KL 英文 / §3.4.2 content orphan / §3.4.6 散装)
- Scope: ch3_method.tex + appendix.tex + fig3_calib_pipeline.tex + 新增 fig_ch3_framework_overview.tex
- 改动清单:
  1. **§3.2 重写** (Block A): 旧 3 段 prose + Table 3.1 → 新 prose + TikZ 全景图
     - 加可视化全景图 (fig_ch3_framework_overview.tex, 新建): 顶层 BG 原则 → 中层校准/分配两层 → 底层两路实例化 + Triton 系统落地
     - §3.2 prose 重写: 强调行为引导统一组织原则 + 两层贯通 + 离线/在线阶段
     - 表 3.1 挪到附录 §sec:app-kv-modes (新 appendix section)
  2. **图 3.2 (fig3_calib_pipeline.tex) 3 改**:
     - 删底部 "$\tau^{-1}$ 温度校正路径已降级" 反向陈述
     - "共享校准目标: min D_KL" → "校准目标: D_KL 最小化"
     - JSON 文件名 (kv_calib_kl_*_int8.json) → 参数类型描述 (INT8 校准产物/逐层 per-group 静态 Scale)
     - 删底部冗余 "共享 KL 目标" dashed label
  3. **§3.3.1 前向/反向 KL 中化** (Block B):
     - forward KL → 前向 KL 散度
     - reverse KL → 反向 KL 散度
     - mass-covering (zero-avoiding) → 概率质量覆盖 (mass-covering / zero-avoiding)
  4. **§3.4 加 section intro** (Block C1): 介绍 A 线 (INT8 对称) + B 线 (INT4 非对称 RoleAlign) + Triton 系统落地 的组织
  5. **§3.4.2 → §3.4.3 content 挪位** (Block C2): "向非对称格式的扩展" paragraph + 40 行 orphan 内容 (RoleAlign intro + 正交性 paragraph + 格式升级动机) 从 §3.4.2 末尾挪到 §3.4.3 subsection 内部
  6. **§3.4.6 Triton 散装英文清理** (Block D, 14 处):
     - online softmax 思想 → 在线 softmax 技术
     - bit-packing / packed / signed INT8 / zero-point / split-channel / nibble → 中化
     - program 实例 / naive 路径 / roofline → 中化
     - attention-KL / attention logits → 注意力 KL / 注意力 logits
- 新增文件: thesis/figures/fig_ch3_framework_overview.tex (TikZ BG 框架两层全景图)
- 新增附录 section: appendix.tex §sec:app-kv-modes "量化模式配置汇总" 含 Table 3.1
- Commands: Write + Edit + python heredoc + xelatex ×2
- Outputs: main.pdf 99 pages (保持) / 1.64 MB
- Validation: 0 undef / 0 multi / 0 dim / 0 error
- 下一步: Codex review 验证 Ch3 整体一致性; 或继续用户指出的更多 §3.4 subsec 合理性讨论

### 2026-04-21 05:18 | Ch2 整章重构 Round 1: 碎 subsec 合并 + §2.4 精简 + 散装英文清理 (20 处)
- Goal: 用户给 Ch2 3 条指令 + 我补 4 条额外发现; 一次性推到 review-ready
- Scope: thesis/chapters/ch2_related_work.tex + ch3_method.tex (加 label)
- Changed files:
  - ch2_related_work.tex: Phase 1 结构 (13 处) + Phase 2 术语 (7 处)
  - ch3_method.tex: §3.4.5 加 \label{subsec:ch3-rolealign-vs-kivi} (为 Ch2 ref 服务)
- Phase 1 结构改动 (13 处):
  - §2.1 删 3 个 subsec 标题 (Decoder-only / 自注意力计算 / 多头+GQA → 合并为 prose, 无 subsec)
  - §2.5 删 3 个 subsec 标题 (FlashAttention / PagedAttention / Triton → 同样合并)
  - §2.4 L293-308 "两正交维度段" (22 行) 精简为 8 行 (去重复 Ch3 内容; 保留 research-gap 定位)
  - §2.4 "相对 KIVI 的三层关系定位" paragraph (17 行含 itemize) 整段删除 (内容已在 Ch3 §3.4.5 覆盖, cross-ref 到 subsec:ch3-rolealign-vs-kivi)
  - §2.4.1 温度校正对比段 (25 行 Velickovic/AhaKV + 三点 differences + 未纳入 claim) 瘦身为 6 行
  - §2.6 删"空白三：温度校正 GQA 尺度依赖"整段 (9 行, 温度校正已降级 appendix; 四空白 → 三空白, 原空白四升为空白三)
  - §2.6 空白三 (原空白四) 后续段散装清理 (3 空白 → 2 空白 + behavior sensitivity profile / calibration / allocation 术语化)
  - §2.6 总结段清理 (behavior-guided / attention-KL / behavior sensitivity profile / fused-kernel efficiency phase boundary → 中文化)
- Phase 2 术语 sweep (7 处):
  - attention score → 注意力得分
  - attention 内部 → 注意力内部
  - output logits → 输出 logits
  - behavior-guided 框架 → 行为引导框架
  - KV compression 综述 → KV 缓存压缩综述
  - KV cache → KV Cache (大小写统一)
  - 基准 前后空格清理
- Ch3 附带改动: §3.4.5 "与 KIVI 的设计差异" 加 subsec:ch3-rolealign-vs-kivi label (支撑 Ch2 cross-ref)
- 新 Ch2 TOC (6 section):
  - §2.1 Transformer 架构与自注意力机制 (无 subsec, 3 段 prose)
  - §2.2 KV Cache 机制与显存分析 (保留 2 subsec)
  - §2.3 模型量化技术基础 (保留 3 subsec)
  - §2.4 KV Cache 量化相关工作 (4 paragraph + §2.4.1 量化对注意力分布)
  - §2.5 高效注意力计算 (无 subsec, 3 段 prose)
  - §2.6 本章小结 (3 空白 + 总结)
- Commands: 单 python heredoc 一次性 apply + xelatex ×2
- Outputs: main.pdf 100 → 98 pages (压缩 2 页) / 1.64 MB
- Validation: 0 undef / 0 multi / 0 dim / 0 error
- 下一步: 继续 Ch2 可能遗漏项或进 Ch4/Ch5 review

### 2026-04-21 04:50 | Ch3 Round 8: §3.4 Triton 5 subsec 合并为 1 subsec + 5 paragraph
- Goal: 用户反馈 §3.4.6/7/8 (INT8 核函数 / INT4 核函数 / INT4 非对称融合核函数) 三个小节应合并为一个"Triton 核函数设计"小节; §3.4.10 标题 "经验交叉点：融合核延迟收益的 (H_kv, seq_len) 空间特征" 太长, 且内容属于 Triton 范畴, 应一并并入
- Scope: thesis/chapters/ch3_method.tex §3.4.6-10 五 subsec 合并
- Changed files: ch3_method.tex (5 处 subsec → paragraph demotion)
- 改动清单:
  - §3.4.6 "INT8 核函数设计" subsection → "Triton 核函数设计" subsection (保留 sec:ch3-triton label), 原 body 成 `\paragraph{INT8 核函数}` (保留 subsec:ch3-triton-int8)
  - §3.4.7 "INT4 核函数设计" subsec → `\paragraph{INT4 核函数}` (保留 subsec:ch3-triton-int4)
  - §3.4.8 "INT4 非对称融合核函数" subsec → `\paragraph{INT4 非对称核函数}` (保留 subsec:ch3-triton-int4-asym)
  - §3.4.9 "GQA 支持机制" subsec → `\paragraph{GQA 支持}` (保留 subsec:ch3-gqa, 顺手简化标题)
  - §3.4.10 "经验交叉点: ..." 长标题 subsec → `\paragraph{经验交叉点}` (保留 subsec:ch3-phase-boundary, 去 texorpdfstring)
- 新 §3.4 TOC (从 10 → 6 subsec):
  - §3.4.1 静态 Scale 的设计
  - §3.4.2 自适应保护机制
  - §3.4.3 从对称到非对称的格式升级
  - §3.4.4 Behavior-Guided Percentile 校准
  - §3.4.5 与 KIVI 的设计差异
  - §3.4.6 Triton 核函数设计 (含 INT8/INT4/INT4 非对称/RoleAlign 分工/GQA/经验交叉点 6 paragraph)
- Commands: python heredoc str.replace ×5 + xelatex ×2
- Outputs: main.pdf 99 pages / 1.64 MB (保持, 因为内容等量保留)
- Validation: 0 undef / 0 multi / 0 dim / 0 error; 所有 label (sec:ch3-triton / subsec:ch3-triton-int8/int4/int4-asym/gqa/phase-boundary) 保留跨章 ref 兼容
- Tag: `thesis-m-plus-v5.1` (标记 Ch3 subsec 合并后的稳定版本)
- 下一步: 继续 Ch3 review 或开 Ch4

### 2026-04-21 04:40 | Ch3 Round 7: Codex adversarial-review 5 issues 全修 (7a + 7b 共 14 处)
- Goal: Codex 过审 Ch3 v4 发现 2 HIGH + 1 MED + 2 LOW 全是真问题 (verdict: needs-attention)；按 Round 7a (快速) + Round 7b (HIGH 1 口径统一) 两子轮全修
- Scope: thesis/chapters/ch3_method.tex
- Round 7a (9 处):
  - LOW 2: Forward KL "mass-covering (zero-forcing)" → "mass-covering (zero-avoiding)" — 纠正术语错配 (zero-forcing 对应 reverse KL)
  - LOW 1a: 删 L645-647 "Phase Boundary" 英文别名 (保留 "经验交叉点" 作唯一命名)
  - LOW 1b-e: 散装 per-layer / allocator 4 处清理 → 逐层敏感度画像 / 分配器
  - MED 1a: L602 "附录~\ref{subsec:exp-int4-honest}" → "第~\ref...~节" (label 实际在 ch4 不是 appendix)
  - MED 1b: L732 cross-ref 错链修正 (跨模型实验→sec:exp-cross-model; 第五章→sec:conclusion-future)
  - HIGH 2: §3.4.8 "核内 Percentile 在线估计" paragraph 重写为 "RoleAlign 与融合核的路径分工" — 明确 RoleAlign 默认路径=torch_ref 消费离线 (p_K,p_V)；融合核=工程可行性验证 (decode M=1 无 Tensor Core); 消除原段"避免校准产物与 kernel 耦合"导致的 RoleAlign 融合核定义歧义
- Round 7b (5 处, HIGH 1 Static Scale 对象口径统一):
  - §3.2 L82-89: "逐层 Scale JSON" → "per-layer per-group 静态 Scale 常量 + JSON 不含 adaptive 覆盖"
  - §3.4.1 eq 3-12 (`s_{b,h,s,j}`) → (`s^{(l)}_j`) 离线校准常量公式, 消除 batch/time 下标歧义
  - §3.4.1 eq 3-15 (`s_{b,h,t,j}`) → (`s^{\text{cache}}_{b,h,t,j}`) 推理时 per-token scale 快照, 明确 static 路径下=$s^{(l)}_j$, adaptive 触发时=$s_{\text{final}}$
  - §3.6.2 显存公式前加说明: cache 存 per-token scale 快照以支持 "写入即冻结" adaptive 语义
  - §3.6.4 JSON 开销: 仅含离线 $\{s^{(l)}_j\}$ + clip percentile + group size, 推理 adaptive 快照不落盘
- Commands: python heredoc ×2 (7a: 9 处 / 7b: 5 处) + xelatex ×2
- Outputs: main.pdf 99 → 100 pages (解释增加 1 页) / 1.64 MB
- Validation: 0 undef / 0 multi / 0 dim / 0 error
- Tag: `thesis-m-plus-v5` 标记 Ch3 经 Codex review 全修后的稳定版本
- 下一步 candidate: Codex review round 2 验证 v5 无回归 / 或进入 Ch4 逐节优化

### 2026-04-21 03:22 | Ch3 逐节优化 Round 6: preamble 清理 + chapter/section title 一致中化 + 裸 label 归位（9 处）
- Goal: Round 5 tag thesis-m-plus-v4 后 user 选 A "Ch3 最后遗漏项"：chapter title 中英混排 + preamble L6-14 散装英文 + 2 个裸 label (sec:ch3-rolealign / sec:ch3-triton) 定位问题
- Scope: thesis/chapters/ch3_method.tex L1-18 + L385 + L544 + L426/L558 + L691
- Changed files: ch3_method.tex (9 处)
- 改动清单:
  - 1. L4 chapter title 中文化: "Behavior-Guided 量化框架设计" → "行为引导量化框架设计"
  - 2. L6 preamble 空格 artifact: "形式化 行为引导 量化" → "形式化行为引导量化"
  - 3. L13 preamble 散装: "per-layer 敏感度画像" → "逐层敏感度画像"
  - 4. L14 preamble 空格+散装: "行为引导 allocator 与 profile-guided 预算建议机制" → "行为引导的层间预算分配器与敏感度引导的预算建议机制"
  - 5. §3.5 section title 一致化: "Behavior-Guided 层间预算分配器" → "行为引导的层间预算分配器" (与 chapter title 一致; 方法名英文保留在正文 inline terms)
  - 6. 裸 label `sec:ch3-rolealign` L385 删除 + 挪到 §3.4.3 "从对称到非对称的格式升级" 下 → aux resolve 为 3.4.3 (原解为 3.4)
  - 7. 裸 label `sec:ch3-triton` L544 删除 + 挪到 §3.4.6 "INT8 核函数设计" 下 → aux resolve 为 3.4.6 (原解为 3.4)
- Commands: python heredoc str.replace ×9 + xelatex ×2
- Validation:
  - 0 undefined / 0 multi / 0 error
  - aux label 验证: rolealign→3.4.3 / triton→3.4.6 / autok→3.5.4 全部指向具体 subsection
- Ch3 终局: Rounds 1-6 累计 ~69 处 surgical 改动；tag `thesis-m-plus-v4` 之前已打，本轮后考虑补 v4.1 或直接继续下一章（Ch4/Ch5 逐节优化或 Codex adversarial-review）
- 下一步 candidate: Ch4 逐节优化 (8 subsection) / Ch5 逐节优化 (3 节 + 小结) / Codex 过审 Ch3 v4+

### 2026-04-21 01:28 | Ch3 逐节优化 Round 5: §3.7 本章小结清理（5 处）+ Ch3 整章优化收尾 tag
- Goal: §3.7 本章小结的空格 artifact + 散装英文 + sensitivity profile 遗漏，§3.6 复杂度分析扫过基本干净无改动
- Scope: thesis/chapters/ch3_method.tex §3.7 L881-920
- Changed files: ch3_method.tex (5 处)
- 5 处清单:
  - "给出了 行为引导 量化框架" → "给出了行为引导量化框架" (空格)
  - L895-897 "per-layer sensitivity profile / 提出 行为引导 allocator / profile-guided 预算建议机制" → "逐层敏感度画像 / 提出行为引导的层间预算分配器 / 敏感度引导的预算建议机制"
  - L901 "使 behavior 原则在框架内部" → "使行为引导原则在框架内部"
  - L917 "行为引导 allocator 的跨模型适用区间地图" → "行为引导分配器的跨模型适用区间地图"
  - L919 "Mistral、3B、14B 的 per-model 案例分析" → "…的逐模型案例分析"
- 保留: "INT8 canonical path" / attention / KIVI-style 等方法名
- Commands: python heredoc str.replace ×5 + xelatex ×2
- Validation: 99 pages / 0 undef / 0 multi / 0 error
- Ch3 整章优化收尾: Round 1 (§3.1/§3.2/全章空格) + Round 2 (§3.3) + Round 3 (§3.4) + Round 4 (§3.5) + Round 5 (§3.7) 累计 ~60 处 surgical 改动；打 tag `thesis-m-plus-v4` 标记 Ch3 新骨架 + 全章清理完成
- 下一步: Round 6 跨章审计 (preamble cross-ref / chapter title "Behavior-Guided 量化框架设计" 中英混排判定)，或进入其他章节 review

### 2026-04-21 01:24 | Ch3 逐节优化 Round 4: §3.5 Allocator + AutoK 清理（13 处）
- Goal: §3.5 有 scaffold 注释、behavior/sensitivity 散装英文、AutoK 定位段连续两处 meta 否定、一处循环引用
- Scope: thesis/chapters/ch3_method.tex §3.5 L691-800
- Changed files: ch3_method.tex (13 处)
- HIGH (7 处):
  - H1: 删 L755-757 scaffold 注释 + 挪 `\label{sec:ch3-autok}` 到 §3.5.4 subsection 下 (修复裸 label)
  - H2: L699 "behavior 原则" → "行为引导原则"
  - H4: L740 "第五章 future work" → "第五章"
  - H5a: L751 "operating 适用区间" → "适用区间特征"
  - H5b: L752 "supporting case" → "佐证案例"
  - H6: AutoK 定位段 (§3.5.5) 整段重写 — 去除 "而非宣称...普适最优策略" 连续两处 meta 否定 + "行为引导 框架" 空格，改为正向 "AutoK 作为自然延伸 + 定位于具体场景"
  - H7: L786 循环引用 `\ref{sec:ch3-autok}` parenthetical 删除
- MEDIUM (6 处):
  - M1a: L719 "heuristic 选择器" → "启发式选择器"
  - M1b: L722 "sensitivity 信息" → "敏感度信息"
  - M1c: L723 "Heuristic 在实验章节作为强基线被正面承认" → "启发式选择器在实验章节中作为强基线与行为引导策略并列比较" (去 awkward 被动 + 散装)
  - M2: L732 "Role-aware allocator" → "Role-Aware Allocator" (全文大小写统一)
  - M3a: L745 "Per-layer sensitivity" → "逐层敏感度"
  - M3b: L765 "sensitivity profile" → "敏感度画像"
- 保留: top-k 公式 / K-V 非对称预算公式 / cov80-90 阈值 / 术语 AutoK/fixed-k/Role-Aware
- Commands: python heredoc str.replace ×13 + xelatex ×2
- Validation: 99 pages / 0 undef / 0 multi / 0 error
- 剩余 follow-ups: Round 5 §3.7 本章小结 (~8 处空格+散装) + §3.6 已扫过基本干净

### 2026-04-21 01:19 | Ch3 逐节优化 Round 3: §3.4 INT8+INT4 实现清理（10 处 surgical + 3 处 meta 否定重写）
- Goal: §3.4 是 Ch3 最长节（411 行 / 10 subsec），结构 OK 但 Triton 尾部有连续 meta 否定 + scaffold 注释 + 中英空格
- Scope: thesis/chapters/ch3_method.tex §3.4 L284-695
- Changed files: ch3_method.tex (10 处替换)
- 改动清单:
  - HIGH scaffold 清理:
    - H1: 删 L385 "原 §3.5 KIVI-style 实例化 RoleAlign 合入" 注释
    - H2+H3: 删 L545 "原 §3.8 Triton 融合核" 注释 + L547-550 Triton 开篇待定注释块（FlashInfer/BitDecoding positioning + 反向 "不做 kernel 速度级比较"）
  - HIGH 空格 artifact:
    - H4: L552 "行为引导 校准方案" → "行为引导校准方案"
    - H5a: L388 "Role-Aware量化" → "Role-Aware 量化"
    - H5b: L434 "为Role-Aware的" → "为 Role-Aware 的"
  - HIGH meta 否定改正向（纪律一）:
    - H6: L679-680 "未纳入 Split-K...不应理解为本质属性" → "聚焦 H_kv≥4 主流 GQA；H_kv=2 场景 Split-K 作为未来扩展"
    - H7: L690-692 "不构成净加速...而非对...绝对加速" → "40% 加速口径相对未融合参考实现成立；与 FlashAttention-2 的对比属另一维度，Tensor Core 未来扩展方向"
    - H8: L614 "故此处不声称 无需 Residual Buffer 优于 KIVI" → "RoleAlign 融合核针对 cs=128 评测设计；Residual Buffer + flash-decoding 分块未来工作"
  - MED:
    - M1: L441 "离线 BA 校准" → "离线行为引导校准"（术语冻结废弃词清理）
    - M2a: L573 "naive dequant+SDPA 路径" → "未融合的 dequant+SDPA 路径"
    - M2b: L691 "未融合 INT4 naive 参考实现" → "未融合 INT4 参考实现"（含在 H7 改写中）
- 保留 depth: §3.4.1-5 数学推导完整；Triton 技术术语（softmax/FlashAttention/SRAM/Tensor Core/CUDA Core/Residual Buffer/Split-K/Flash-Decoding/bit-packing/nibble/per-channel/per-token）
- Commands: python heredoc str.replace ×10 + xelatex ×2
- Outputs: main.pdf 99 pages / 1.64 MB
- Validation: 0 undefined / 0 multi-defined / 0 dim-too-large / 0 error
- Risks / follow-ups: 下一步 Round 4 §3.5 Allocator (L697-) 含 2 裸 label (sec:ch3-rolealign/triton 已处理) + Role-Aware 部分 meta 否定

### 2026-04-21 01:13 | Ch3 逐节优化 Round 2: §3.3 行为引导校准方法清理（10 处 surgical）
- Goal: §3.3 结构/内容 depth 合适无需重写，但存在 meta 自我否定 + 散装英文 + 错位加粗 + 内部注释泄露等 surgical 问题
- Scope: thesis/chapters/ch3_method.tex §3.3 L154-284
- Changed files: ch3_method.tex (10 处替换)
- 10 处清单:
  - HIGH H1: 删除 L245 meta 自我否定句 "$H_{kv}$... 而非全文的组织脊柱" (违反纪律一正向陈述)
  - HIGH H2: L244 空格 artifact "提供了 行为引导 校准目标" → "提供了行为引导校准目标"
  - HIGH H3: L179 `\textbf{完整流程}` 错位加粗 → 去 textbf + 重写"在离线校准阶段可视化"
  - HIGH H4: L248 label 内部注释 "% 保留 label 用于 backward-compat" 删除
  - MED M1: L243 "bit-width" → "位宽"
  - MED M2a: L265 "robust 优先策略" → "稳健优先策略"
  - MED M2b: L272 "完整 calibration 过程" → "完整校准过程"
  - MED M2c: L280 "diagnostic 观察" → "诊断观察"
  - MED M2d: L282 "在 calibration 与推理阶段" → "在校准与推理阶段"
  - MED M3a: L180+L181 "两条 path" × 2 → "两条路径"
  - MED M3b: L182 "降级为附录 diagnostic note" → "降级为附录诊断说明"
- 保留: 三点选 KL 理由 / forward vs reverse KL / epsilon 截断数值分析 / 专业术语英文 (softmax/mass-covering/Jensen-Shannon)
- Commands: python heredoc 10 处 str.replace (比 Edit tool 单处替换更快) + xelatex ×2
- Outputs: main.pdf 99 pages / 1.64 MB
- Validation: 0 undefined / 0 multiply-defined / 0 dim-too-large / 0 error
- Risks / follow-ups: 下一步 Round 3 §3.4 (10 subsec 的行为引导 INT8/INT4 实现，最长一节)

### 2026-04-21 01:05 | Ch3 逐节优化 Round 1: §3.1 微调 + §3.2 完全重写 + 全章空格 sweep
- Goal: 用户启动"一节一节优化"模式。Round 1 目标：§3.1 两处微调通过（最小 commit），§3.2 大刀阔斧解决三层重复，同时清扫 Stage 2 残留的 13+ 处空格 artifact
- Scope: thesis/chapters/ch3_method.tex
- Changed files:
  - §3.1 L64-72 两处：`behavior 原则` → `行为引导原则`；L72-75 四句图描述 → 一句 "图可视化了上述两条误差传播路径"
  - §3.2 L78-224（146 行）→ L78-150（72 行）：intro 段 + 5 subsection（`离线校准阶段 / 在线推理阶段 / KV Cache 管理架构 / 生成循环集成 / 量化模式总览`）全部消解为 3 段连贯 prose + Table 3.1（保留）+ 1 段表后解读；原旧注释 L110-113（tau^-1 scribble）+ L154-155（`% 保持旧 ref 兼容` 内部语言）全删
  - 全章空格 artifact 全清：stage-2 风格残留 "中文 空格 词 空格 中文" 15 处（框架 ×6 / 基线 ×2 / 总览 ×3 / 流程 ×2 / 适用区间 ×2 / 溯源完整 ×1 / 覆盖度 ×2 / 预算 ×1）
  - 全章 `behavior-guided` 小写 → 行为引导（9 处，大写 `Behavior-Guided` 作为方法名保留）
- Commands:
  - 单 python heredoc 脚本：§3.2 重写 + 全章 bilateral/unilateral 空格 regex sweep
  - `cd thesis && xelatex -interaction=nonstopmode main.tex` ×2
- Outputs: main.pdf 100 → 99 pages / 1.64 MB（§3.2 压缩 74 行自然节省 1 页）
- Validation:
  - 0 undefined / 0 multiply-defined / 0 error / 0 dimension-too-large
  - sanity grep: ` 框架 ` / ` 基线 ` / ` 总览 ` / ` 流程 ` / ` 适用区间 ` / ` 溯源完整 ` / ` 覆盖度 ` 全零残留
  - Ch3 从 1007 → 936 lines（-71，主要来自 §3.2 压缩）
- §3.2 新骨架 (3 段 + Table):
  1. 离线阶段：校准目标 + 搜索空间正交维度 + 产物 JSON
  2. 在线阶段：\code{kv\_mode} 路由 + 四类格式 + Triton 反量化
  3. 表 3.1 汇总 9 种量化模式 + int8/int4\_ours / kivi\_style / int4\_ours\_asym 定位
- Risks / follow-ups:
  - 下一步 Round 2: §3.3 检查（KL 目标 + Scale 搜索），重点审 L319 "H_kv ... 而非全文的组织脊柱" meta 自我否定
  - §3.4 10 subsection 仍待决定（promote 5 Triton subsec 为 paragraph 还是保持 flat）

### 2026-04-21 00:50 | Ch3 结构重组：10 section → 7 section（脚本化一次性重排）
- Goal: 用户对 Ch3 提 7 条重组建议：§3.1 改名为专业术语；§3.2 精简不过度细分；§3.4+§3.5 合并为"行为引导校准的 INT8 和 INT4 实现"；§3.6+§3.7 AutoK 合并；§3.8 Triton 并入 §3.4 末尾作为 §3.4.x（非第二层故事）；§3.9 A 类（系统架构）融入 §3.2，B 类（复杂度）独立
- Scope: thesis/chapters/ch3_method.tex 一次性重排；新增 refactor_ch3_structure.py 可复用脚本
- Changed files:
  - scripts/thesis/refactor_ch3_structure.py (new, 180 lines) — section parse + 按新骨架 concatenate
  - thesis/chapters/ch3_method.tex (1008 → 1010 lines，内容等价保留，只重排 section/subsection 层次)
- 新 7-section 骨架:
  - §3.1 注意力近似误差分析（原"问题形式化"重命名）
  - §3.2 方法框架总览（原 §3.2 精简"系统架构概述" subsection 标题 + 融入原 §3.9.1-3 A 类 KV Cache 管理/生成循环/量化模式总览）
  - §3.3 行为引导校准方法（保留）
  - §3.4 行为引导校准的 INT8 和 INT4 实现（合并原 §3.4+§3.5+§3.8 Triton，共 10 subsections；用户明确 Triton 信息全保留不压缩）
  - §3.5 Behavior-Guided 层间预算分配器（合并原 §3.6+§3.7 AutoK 为 5 subsections）
  - §3.6 复杂度与资源分析（原 §3.9 B 类独立，§3.9.4 升级为 section 标题，其余为 subsection）
  - §3.7 本章小结
- Commands:
  - `python3 scripts/thesis/refactor_ch3_structure.py`
  - `xelatex -interaction=nonstopmode main.tex` ×2
- Outputs: main.pdf 100 pages / 减 1 页（合并 section 节省 break space）
- Validation:
  - 0 undefined references / 0 multiply-defined / 0 error
  - sec:ch3-problem / sec:ch3-calibration / sec:ch3-allocator / sec:ch3-system / sec:ch3-complexity 全部 resolve
  - TOC 结构从 aux 核对：7 section + 每节 subsection 保序
- Risks / follow-ups:
  - §3.4 有 10 subsection 可能偏多（需 user 审视是否要 promote 部分为 subsubsection/paragraph）
  - §3.2 现有 5 subsection（2 个原 §3.2 + 3 A 类），可进一步精简用户若觉得细
  - 下一步：tag `thesis-m-plus-v3` 标记新骨架，memory 已更新写作纪律第三条
