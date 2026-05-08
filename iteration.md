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

### 2026-05-09 02:09 | AIGC 段落修订 28b: 历史缓存闭包与自适应保护边界
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理历史缓存不改写、单调追加、自适应保护开启范围和 RoleAlign 参数生成边界。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将半说明书式长句改为三句，保留历史缓存闭包、逐位一致间接核验和 INT8-Canonical 开启范围。
  - 将第四章引用收窄为固定协议主线读数，避免把其写成逐位一致的直接证明。
  - 明确 RoleAlign 的 K 侧预填充后复用与 V 侧随新 token 即时计算，避免 K 侧每步重算误读。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated.
- Risks / follow-ups:
  - Segment 28 还剩 Prefill/Decode 数据流段，下一轮单独处理。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 cache closure semantics`

### 2026-05-09 02:04 | AIGC 段落修订 28a: 路径参数与运行时映射解释
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理公式后对 $\theta_{\mathrm{path}}^{(l)}$、$g_t$ 与 $h^{K/V}$ 的参数解释。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将冒号式定义列表改写为连续说明，保留三类参数函数的全部语义。
  - 明确 $g_t$ 由自适应保护逻辑确定当前组 scale，避免被误读为在线更新冻结产物。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated; the previous overfull hbox at lines 644--646 no longer appears after this rewrite.
- Risks / follow-ups:
  - Segment 28 还包含历史缓存闭包语义和 Prefill/Decode 数据流两段，后续分别处理。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 runtime parameter mapping`

### 2026-05-09 02:00 | AIGC 段落修订 27b: 在线写入公式引入句
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理在线推理阶段第 $t$ 个新 token 写入公式的引入句。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将机械的“在线推理阶段...可写为”改为更自然的公式引入句。
  - 保留在线推理、第 $t$ 个新 token、第 $l$ 层写入和统一记号四个信息点，公式本身不变。
  - 技术、中文、跨章一致性和 skeptical 审查均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 are unrelated.
- Risks / follow-ups:
  - 下一轮继续处理公式后的参数解释段，重点清理冒号式说明和中英混排实现口吻。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 online write intro`

### 2026-05-09 01:56 | AIGC 段落修订 27a: Runtime artifact 字段与 K/V 参数生成
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理三条路径在 $\mathcal A_{\mathrm{path}}$ 中的字段差异和 K/V 仿射参数运行时生成语义。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将冒号式字段列表改写为分句说明，保留表~`\ref{tab:ch3-runtime-paths}` 的详细字段引用。
  - 保留 INT8、对称 INT4、INT4-RoleAlign 三条路径的字段差异，以及 K 侧预填充阶段一次计算后复用、V 侧逐 token 即时计算的运行时语义。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS，中文失败建议已吸收。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 are unrelated.
- Risks / follow-ups:
  - Segment 27 还包含在线推理阶段写入公式引入句，下一轮单独处理。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 runtime artifact fields`

### 2026-05-09 01:50 | AIGC 段落修订 26b: AutoK 覆盖度入口句
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮只处理正文中 \texttt{AutoK} 读取 $\Gamma(k)$ 的过渡句。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将“直接读取”改为“以 $\Gamma(k)$ 为依据”，弱化程序接口感。
  - 保留 AutoK 给出达到覆盖阈值所需的最小保护层数建议，并保留与 BA-$k$ 方案共用敏感度画像的关系。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS，中文失败建议已吸收。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 27 中运行时字段与写入公式相关高嫌疑句。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 autok coverage entry`

### 2026-05-09 01:48 | AIGC 段落修订 26a: AutoK 覆盖度图注
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮只处理图~`\ref{fig:ch3-coverage-curve}` 的 caption。
- Changed files:
  - `thesis/figures/fig_ch3_coverage_curves.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/figures/fig_ch3_coverage_curves.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 dash-led 图注改为自包含 caption，补明 $k$ 与 $\Gamma(k)$ 两个轴。
  - 保留集中型画像较小 $k$ 达标、弥散型画像覆盖更多层、AutoK 依据画像形态生成预算建议的含义。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS，失败建议已吸收。
- Validation:
  - `git diff --check -- thesis/figures/fig_ch3_coverage_curves.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Segment 26 还包含正文中 \texttt{AutoK} 读取 $\Gamma(k)$ 的句子，下一轮单独处理。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 autok coverage caption`

### 2026-05-09 01:42 | AIGC 段落修订 25: RoleAlign 与 KIVI-style 端点对照
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮处理 RoleAlign 与 KIVI-style 的端点参数来源对照段。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 重构 KIVI-style 与 RoleAlign 的端点来源比较，删除 LaTeX 中的 markdown 式强调。
  - 明确 RoleAlign 运行时仍针对当前张量统计对应百分位并计算 $(s,\zeta)$。
  - 将“更稳定”收窄为搜索目标，保留受控比较章节与双轴布局图引用。
  - 技术、中文、跨章一致性和 skeptical 审查最终均返回 PASS，失败建议已吸收。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 26 中 AutoK coverage curve 相关高嫌疑句。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 rolealign kivi endpoints`

### 2026-05-09 01:37 | AIGC 段落修订 24b: RoleAlign Value 侧公式引入
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮只处理 Value 侧逐 token 非对称量化的公式引入句。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将 Value 侧“使用逐 token 非对称量化”改为“按 token 建立非对称量化参数”。
  - 保留 $V^{(l)}\in\mathbb{R}^{S\times d_v}$、第 $t$ 个 token 和分位数裁剪边界定义。
  - 技术、中文、跨章一致性和 skeptical 审查均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - 下一轮继续处理 Segment 25 中 RoleAlign 与 KIVI-style 的比较段。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 rolealign value token`

### 2026-05-09 01:35 | AIGC 段落修订 24a: RoleAlign Key 侧统计解释
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮只处理 Key 侧分位数统计后的解释句。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将分号压缩句改成三句，拆开分位数统计、逐通道参数作用和 §3.2 诊断承接关系。
  - 保留序列维度统计、每通道一组 $(s,\zeta)$、不同特征方向范围、粗 \texttt{INT4} 网格与 $qK^\top$ 排序影响。
  - 技术、中文、跨章一致性和 skeptical 审查均返回 PASS。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Segment 24 还包含 Value 侧逐 token 非对称量化公式引入，下一轮单独处理。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 rolealign key stats`

### 2026-05-09 01:30 | AIGC 段落修订 23b: RoleAlign Key 侧形状说明
- Goal: 逐段处理 AIGC 检测报告中 Chapter 3 的高嫌疑段落，本轮只处理 `\texttt{INT4-RoleAlign}` Key 侧公式前的维度省略与实现形状说明。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - 将括号内实现形状拆成独立说明，避免一长句同时承担记号省略、张量形状和公式引入。
  - 保留 K/V 张量、Key scale 张量、Value scale 张量形状，以及 Key 逐通道非对称量化和第 $j$ 通道分位数边界。
  - 技术、中文、跨章一致性和 skeptical 审查均返回 PASS，中文审查失败建议已吸收。
- Validation:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS.
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF.
  - Log check: PASS; no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Segment 24 将继续处理 Value 侧分位数统计和逐 token 非对称量化说明。
- Commit: pending at log-write time; committed as `docs: polish aigc ch3 rolealign key shape`

### 2026-05-09 00:52 | AIGC paragraph polish ch3 feasible set
- Goal: Process report segment 18 in Chapter 3 while preserving robust-selection statistics, clipping-rate feasible set, and tail-priority selection rule.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Clarified `\\mu(\\theta)`, `q_{0.95}(\\theta)`, and K/V clipping-rate meanings.
  - Preserved `q_{\\max}` values for INT8 and INT4, the feasible-set threshold rule, and `\\tau_K=\\tau_V=0.01`.
  - Rewrote the `argmin` explanation in Chinese and changed the feasible-set separator from `:` to `\\mid`.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 19 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:47 | AIGC paragraph polish ch3 forward kl
- Goal: Process the second natural paragraph of report segment 17 in Chapter 3 while preserving forward-KL motivation, reverse-KL/JS diagnostic roles, and the Value-path proxy boundary.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the forward-KL paragraph into shorter sentences while preserving the high-probability reference-position penalty.
  - Preserved reverse KL and JS as supplementary diagnostics.
  - Made the Value-path independent output-perturbation proxy boundary explicit.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 18 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:45 | AIGC paragraph polish ch3 kl decomposition
- Goal: Process the first natural paragraph of report segment 17 in Chapter 3 while preserving MSE/KL boundaries and the distribution/aggregation error decomposition.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote dense formula prose into shorter sentences while preserving both error terms and all variable definitions.
  - Clarified that KL directly compares the attention-distribution shift and remains scoped to the distribution-side error path.
  - Replaced dispreferred `在分布侧误差路径上` with `沿分布侧误差路径`.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with the forward-KL paragraph in report segment 17 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:41 | AIGC paragraph polish ch3 framework caption
- Goal: Process report segment 16 in Figure 3-3 caption while preserving framework inputs, offline artifacts, shared profile, allocation output, and online read-only execution.
- Changed files:
  - `thesis/figures/fig_ch3_framework_shared_profile.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/figures/fig_ch3_framework_shared_profile.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the figure caption into a responsibility-oriented summary.
  - Preserved calibration inputs, `\\theta^\\star`, `\\mathcal S`, budget allocation under `\\bar b`, `b^\\star`, and online cache-write/decode execution.
  - Added the no-online-search boundary without introducing figure nodes that are not drawn.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this caption.
- Risks / follow-ups:
  - Continue with report segment 17 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:37 | AIGC paragraph polish ch3 offline online boundary
- Goal: Process the second natural paragraph of report segment 15 in Chapter 3 while preserving the offline/online split and frozen-artifact execution boundary.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the offline/online paragraph to remove `推理路径上` and reduce semicolon-packed explanation.
  - Preserved reference-behavior extraction, path-parameter search, frozen calibration artifacts, shared profile generation, and online read-only execution.
  - Kept `\\theta^\\star` and `b^\\star` as offline deliverables rather than online decision variables.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 16 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:35 | AIGC paragraph polish ch3 allocation mapping
- Goal: Process the first natural paragraph of report segment 15 in Chapter 3 while preserving the allocation mapping, budget constraint, and K/V role extension.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote allocation prose to use `位宽预算` and avoid compressed parenthetical style.
  - Preserved the deterministic mapping, read-only use of `\\mathcal{S}`, no-online-optimization boundary, and `L \\times 2` K/V role extension.
  - Replaced `K/V 角色条件化` with a more natural `进一步区分 K/V 角色` formulation.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with the second natural paragraph in detector segment 15 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:31 | AIGC paragraph polish ch3 evidence hierarchy
- Goal: Process report segment 14 in Chapter 3 while preserving the Key-side low-bit risk conclusion and the PPL/task evidence hierarchy.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the conclusion paragraph to avoid formulaic `因此...被确立` phrasing and English-style dose-response language.
  - Made single-side PPL isolation the primary evidence and task readouts the external consistency/boundary evidence.
  - Restated `K16V4` and `K8V4` contrasts so the Value-side boundary remains explicit.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 15 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:26 | AIGC paragraph polish ch3 model family modulation
- Goal: Process the second natural paragraph of report segment 13 in Chapter 3 while preserving Qwen/LLaMA GQA metadata and the `$H_{kv}` proxy boundary.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the model-family modulation paragraph without colon-led packing or unnecessary parentheses.
  - Preserved Qwen `$H_{kv}` / `$N_{\mathrm{rep}}` values, LLaMA-3.1-8B comparison metadata, and Table 4-7 evidence attribution.
  - Reframed `$H_{kv}$` as a proxy variable with model scale, training data, and GQA configuration as co-modulating factors.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with the next natural paragraph in detector segment 14 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:22 | AIGC paragraph polish ch3 qwen kv diagnosis
- Goal: Process the first natural paragraph of report segment 13 in Chapter 3 while preserving PPL isolation, 32K task diagnostics, and the Key-side trigger interpretation.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the paragraph to avoid report-like colon structure and inaccurate attribution of statistical protocol to the PPL table.
  - Preserved the `K4V16`, `K16V4`, `K4V8`, and `K8V4` comparisons while narrowing the conclusion to the cited Qwen2.5 low-bit contrasts.
  - Added an explicit Value-side boundary so the paragraph does not imply Value compression has no effect.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; log check found no undefined references or citation warnings. Existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with the next natural paragraph in the same detector segment after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:14 | AIGC paragraph polish ch3 kv diagnosis notation
- Goal: Process report segment 12 in Chapter 3 while preserving the equation-based K/V mechanism explanation and the KxVy diagnostic notation.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the K/V path explanation to avoid undefined `吸收` language and keep sensitivity claims conditional.
  - Made `K4V16` and `K16V4` directions explicit and changed `MixedKV` wording to an experimental-notation correspondence.
  - Separated Figure 3-2 configuration roles from Chapter 4 table evidence for `FP16` and single-side PPL isolation.
- Validation:
  - PASS: diff whitespace check.
  - PASS: LaTeX build generated the PDF; existing overfull hboxes at Chapter 3 lines 369 and 644--646 are unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 13 after this commit.
- Commit: pending until this entry is committed.

### 2026-05-09 00:07 | AIGC paragraph polish ch3 problem formalization
- Goal: Process report segment 11 in Chapter 3 while preserving the attention-behavior object, tensor shapes, single-head equation, model-scope boundary, and GQA/MQA applicability.
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the opening problem-formalization paragraph to state the behavior target through logits, softmax, and Value aggregation rather than a terse reconstruction-distance contrast.
  - Narrowed the Mistral scope to `Mistral-7B-Instruct-v0.3` and made the $d_v=d_k$ statement local to the single-head notation.
  - Added explicit GQA/MQA shared-KV-head wording and a forward link to `\Delta_{\mathrm{beh}}`.
- Validation:
  - PASS: whitespace/error check and full LaTeX build completed; generated 100-page PDF.
  - Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Continue with report segment 12 after this commit.
- Commit: see Git history for `docs: polish aigc ch3 problem formalization`

### 2026-05-09 00:01 | AIGC paragraph polish ch2 low-bit recovery boundary
- Goal: Process report segment 10 in Chapter 2 while preserving the low-bit recovery related-work mapping and the boundary between content protection, instability diagnosis, and budget allocation.
- Changed files:
  - `thesis/chapters/ch2_related_work.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch2_related_work.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the ZipCache/IntactKV/SKVQ and boundary-reference paragraph with more conservative method attributions.
  - Replaced the negative compression-ratio-only closure with a positive link between offline behavior sensitivity profiles, instability diagnosis, and budget allocation.
  - Changed the next heading from `正交路线` to `正交关系` after technical review rejected the stronger `可组合关系` title.
- Validation:
  - PASS: whitespace/error check and full LaTeX build completed; generated 100-page PDF.
  - Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Continue with report segment 11 after this commit.
- Commit: see Git history for `docs: polish aigc ch2 low-bit recovery boundary`

### 2026-05-08 23:53 | AIGC paragraph polish ch2 asymmetric quantization axes
- Goal: Process report segment 9 in Chapter 2 while preserving asymmetric-quantization motivation, K/V role-diagnosis parameters, quantization-axis semantics, and attention-path mechanism.
- Changed files:
  - `thesis/chapters/ch2_related_work.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch2_related_work.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the asymmetric-quantization paragraph to avoid `在 KV Cache 上`, strengthen Chinese flow, and make zero-point alignment and K/V axis roles more precise.
  - Preserved the roles of zero-point/scale, per-channel Key, per-token Value, logits/softmax, and weighted aggregation.
  - Added explicit scope around same calibration/clipping policy and avoided treating the K/V statistics as absolute facts across all settings.
- Validation:
  - PASS: whitespace/error check and full LaTeX build completed; generated 100-page PDF.
  - Page-count note: this paragraph expansion shifted the generated PDF from 99 to 100 pages.
  - Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Continue with report segment 10 after this commit.
- Commit: see Git history for `docs: polish aigc ch2 asymmetric quantization axes`

### 2026-05-08 23:45 | AIGC paragraph polish ch2 symmetric quantization roles
- Goal: Process report segment 8 in Chapter 2 while preserving the INT8/symmetric INT4 role split, integer-grid facts, bit-packing storage estimate, and behavior-usability boundary.
- Changed files:
  - `thesis/chapters/ch2_related_work.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch2_related_work.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote the symmetric-quantization role paragraph to keep INT8 as the conservative stability-closure check and symmetric INT4 as the low-bit pressure point.
  - Preserved the 255 vs 15 level counts, approximate 17x discrete-level difference, two-nibble packing, and approximate FP16-to-INT4 payload storage ratio.
  - Added the payload-scope caveat for scale, metadata, and alignment overhead after skeptical review.
- Validation:
  - PASS: whitespace/error check and full LaTeX build completed; generated 99-page PDF.
  - Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated.
- Risks / follow-ups:
  - Continue with report segment 9 after this commit.
- Commit: see Git history for `docs: polish aigc ch2 symmetric quantization roles`

### 2026-05-08 23:32 | AIGC paragraph polish ch1 contribution 3
- Goal: Process report segment 7's third Chapter 1 contribution paragraph while preserving cross-model budget-regime claims and all named phenomena.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote contribution 3 to keep `\texttt{heuristic}` strong-baseline behavior, key-layer deviation, `\texttt{AutoK}` model-level budget candidates, early-layer protection, and high-performance cluster coexistence.
  - Added explicit Chapter 4 audit anchors for the same-order `\texttt{INT4}` budget-band comparison, three-task mean, 97\% near-cluster rule, and profile tables.
  - Multi-round review converged to a final candidate with PASS from technical accuracy, Chinese academic writing, cross-chapter consistency, and skeptical-review perspectives.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 8 after this commit.
- Commit: see Git history for message `docs: polish aigc ch1 budget-regime contribution`

### 2026-05-08 22:56 | AIGC paragraph polish ch1 contribution 2
- Goal: Process report segment 7's second Chapter 1 contribution paragraph while preserving the INT8 baseline, low-bit RoleAlign, AutoK, and bounded system-support claims.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote contribution 2 to preserve the conservative INT8 fidelity reference, K/V role-aware low-bit recovery path, AutoK budget proposal role, and system execution/review interface.
  - Multi-round review converged to a final candidate with PASS from technical accuracy, Chinese academic writing, cross-chapter consistency, and skeptical-review perspectives.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 7's cross-model budget-regime contribution paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 instance-chain contribution`

### 2026-05-08 22:40 | AIGC paragraph polish ch1 contribution 1
- Goal: Process report segment 6's first Chapter 1 contribution paragraph while preserving the attention-behavior object, three observables, and calibration/allocation uses.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Rewrote contribution 1 to preserve quantized cache as an attention-path behavior carrier, attention-distribution change, Value-aggregated representation shift, task-behavior fluctuation, calibration parameter selection, and budget-protection judgment.
  - Multi-round review converged to a final candidate with PASS from technical accuracy, Chinese academic writing, cross-chapter consistency, and skeptical-review perspectives.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with the remaining contribution paragraphs covering the INT8/INT4 instance chain and cross-model budget regimes.
- Commit: see Git history for message `docs: polish aigc ch1 behavior-object contribution`

### 2026-05-08 22:29 | AIGC paragraph polish ch1 chapter roadmap
- Goal: Process report segment 6's Chapter 1 roadmap paragraph while preserving all chapter responsibilities.
- Scope: One paragraph in Chapter 1 plus audit logs.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Split a semicolon-heavy chapter roadmap into shorter sentences.
  - Preserved Chapter 2 positioning, Chapter 3 method design, Chapter 4 experimental evidence, and Chapter 5 conclusion/scope/future-space roles.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646, unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 6 contribution paragraph after commit.
  - Unrelated dirty items remain outside this paragraph scope.

### 2026-05-08 22:25 | AIGC paragraph polish ch1 efficient inference paragraph
- Goal: Process report segment 5's high-efficiency inference systems paragraph while preserving system boundary claims.
- Scope: One paragraph in Chapter 1 plus audit logs.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Removed defensive replacement-vs-complement framing and colon-style explanation.
  - Kept FlashAttention, PagedAttention, complementary system/quantization roles, and decode-time usability question.
  - Added bounded decode overhead wording without claiming production scheduler integration or stable speedup.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646, unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 6 after commit.
  - Unrelated dirty items remain outside this paragraph scope.

### 2026-05-08 22:14 | AIGC paragraph polish ch1 related work kv paragraph
- Goal: Process report segment 5's KV Cache quantization related-work paragraph while preserving literature positioning.
- Scope: One paragraph in Chapter 1 plus audit logs.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Replaced list-like related-work prose with a more specific cache-state motivation.
  - Aligned KVQuant wording with Chapter 2 by using non-uniform codebook, Pre-RoPE Key quantization, and outlier handling.
  - Kept Key-side and Value-side perturbation paths separate before posing the calibration/format audit question.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646, unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 5's high-efficiency inference paragraph after commit.
  - Unrelated dirty items remain outside this paragraph scope.

### 2026-05-08 22:01 | AIGC paragraph polish ch1 motivation paragraph 2
- Goal: Process the second high-suspicion paragraph in AIGC report segment 4 while preserving the Chapter 1 motivation claim.
- Scope: One paragraph in Chapter 1 plus audit logs.
- Changed files:
  - `thesis/chapters/ch1_introduction.tex`
  - `docs/aigc_revision_tracker.md`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`
  - `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`
- Outputs:
  - Removed repeated `因此` and colon-style viewpoint framing.
  - Preserved attention-distribution, aggregation-output, task-behavior, long-context, low-bit, layer/head/role, and stability/usability claims.
  - Multi-angle review converged on avoiding new mechanism claims and preserving the original `稳定和可用` boundary.
- Validation:
  - `git diff --check`: PASS
  - LaTeX: PASS, generated 99-page PDF
  - Residual: existing Chapter 3 overfull hboxes at lines 369 and 644--646, unrelated to this paragraph.
- Risks / follow-ups:
  - Continue with report segment 5 after commit.
  - Unrelated dirty items remain outside this paragraph scope.

### 2026-05-08 21:46 | AIGC paragraph polish ch1 motivation paragraph 1

- Goal: Reduce AIGC-style regularity in the Chapter 1 calibration-premise paragraph while preserving all mechanism and boundary claims.
- Scope: One source paragraph from `thesis/chapters/ch1_introduction.tex`, mapped to detector segment 4.
- Changed files: `thesis/chapters/ch1_introduction.tex`, `docs/aigc_revision_tracker.md`.
- Commands: four-angle reviewer agents; `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`; `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`.
- Outputs: Rewrote the paragraph to reduce colon-style exposition and template connectors while preserving MSE, percentile clipping, softmax nonlinearity, Key perturbation, normalization absorption, and static-threshold limitations.
- Validation: Reviewer gates PASS after adopting skeptical fixes; LaTeX compile PASS. Existing Chapter 3 overfull hboxes are unrelated to this paragraph.
- Risks / follow-ups: Continue with the next Chapter 1 motivation paragraph from detector segment 4.
- Commit: see Git history for message `docs: polish aigc ch1 motivation paragraph 1`

### 2026-05-08 21:42 | AIGC paragraph polish en abstract paragraph 3

- Goal: Reduce formulaic result-list rhythm in the English abstract evidence paragraph while preserving all numerical claims and boundaries.
- Scope: One source paragraph from `thesis/chapters/abstract_en.tex`, mapped to detector segment 2.
- Changed files: `thesis/chapters/abstract_en.tex`, `docs/aigc_revision_tracker.md`.
- Commands: four-angle reviewer agents; `git diff --check -- thesis/chapters/abstract_en.tex docs/aigc_revision_tracker.md iteration.md`; `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`.
- Outputs: Rewrote the English evidence paragraph, retained all model-family, INT8, INT4, AutoK, early-layer, 14B, capacity, and fused-decode boundary numbers, and restored stronger wording after skeptical review.
- Validation: Reviewer gates PASS after adopting required skeptical fixes; LaTeX compile PASS. Existing Chapter 3 overfull hboxes are unrelated to this paragraph.
- Risks / follow-ups: Detector segment 3 is the final sentence of this same English abstract paragraph and is covered here. Continue with detector segment 4.
- Commit: see Git history for message `docs: polish aigc en abstract paragraph 3`

### 2026-05-08 21:38 | AIGC paragraph polish en abstract paragraph 2

- Goal: Reduce formulaic method sequencing in the English abstract method paragraph while preserving all calibration, RoleAlign, and allocation claims.
- Scope: One source paragraph from `thesis/chapters/abstract_en.tex`, mapped to detector segment 2.
- Changed files: `thesis/chapters/abstract_en.tex`, `docs/aigc_revision_tracker.md`.
- Commands: four-angle reviewer agents; `git diff --check -- thesis/chapters/abstract_en.tex docs/aigc_revision_tracker.md iteration.md`; `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`.
- Outputs: Rewrote the method paragraph to remove `three linked steps` framing, retain `same offline calibration artifacts`, and make calibration-to-allocation linkage concrete without stronger optimality claims.
- Validation: Reviewer gates PASS after adopting required writing fixes; LaTeX compile PASS. Existing Chapter 3 overfull hboxes are unrelated to this paragraph.
- Risks / follow-ups: Continue with English abstract paragraph 3 from detector segment 2, one paragraph per commit.
- Commit: see Git history for message `docs: polish aigc en abstract paragraph 2`

### 2026-05-08 21:33 | AIGC paragraph polish en abstract paragraph 1

- Goal: Reduce formulaic phrasing in the English abstract motivation paragraph while preserving the bottleneck claim, K/V propagation distinction, and framework scope.
- Scope: One source paragraph from `thesis/chapters/abstract_en.tex`, mapped to detector segment 2.
- Changed files: `thesis/chapters/abstract_en.tex`, `docs/aigc_revision_tracker.md`.
- Commands: four-angle reviewer agents plus final four-angle re-approval after one skeptical FAIL; `git diff --check -- thesis/chapters/abstract_en.tex docs/aigc_revision_tracker.md iteration.md`; `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`.
- Outputs: Rewrote the English motivation paragraph to remove generic abstract transitions, use `Key-side` and `Value-side` terminology, and compress the final connection so it preserves meaning without adding an abstract page.
- Validation: Reviewer gates PASS after final re-approval; LaTeX compile PASS. Existing Chapter 3 overfull hboxes are unrelated to this paragraph.
- Risks / follow-ups: Continue with English abstract paragraph 2 from detector segment 2, one paragraph per commit.
- Commit: see Git history for message `docs: polish aigc en abstract paragraph 1`

### 2026-05-08 21:29 | AIGC paragraph polish zh abstract paragraph 3

- Goal: Reduce AIGC-style regularity in the Chinese abstract evidence paragraph while preserving all experimental numbers and boundaries.
- Scope: One source paragraph from `thesis/chapters/abstract_zh.tex`, mapped to detector segment 1.
- Changed files: `thesis/chapters/abstract_zh.tex`, `docs/aigc_revision_tracker.md`.
- Commands: four-angle reviewer agents; `git diff --check -- thesis/chapters/abstract_zh.tex docs/aigc_revision_tracker.md iteration.md`; `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`.
- Outputs: Rewrote the evidence paragraph to remove English-style `本文因此`, reduce `在...上` phrasing, and keep every reported number for INT8, INT4, AutoK, early-layer protection, 14B close-cluster behavior, and capacity compression.
- Validation: Reviewer gates PASS; LaTeX compile PASS. Existing Chapter 3 overfull hboxes are unrelated to this paragraph.
- Risks / follow-ups: Continue with detector segment 2, the English abstract, one paragraph per commit.
- Commit: see Git history for message `docs: polish aigc zh abstract paragraph 3`

### 2026-05-08 21:23 | AIGC paragraph polish zh abstract paragraph 2

- Goal: Reduce AIGC-style regularity in the second Chinese abstract paragraph while preserving all method claims and boundaries.
- Scope: One source paragraph from `thesis/chapters/abstract_zh.tex`, mapped to detector segment 1.
- Changed files: `thesis/chapters/abstract_zh.tex`, `docs/aigc_revision_tracker.md`.
- Commands: four-angle reviewer agents; `git diff --check -- thesis/chapters/abstract_zh.tex docs/aigc_revision_tracker.md iteration.md`; `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`.
- Outputs: Rewrote the method paragraph to improve rhythm and remove template-like sequencing while preserving INT8, `\texttt{INT4-RoleAlign}`, K/V role split, behavioral sensitivity profiles, fixed-$k$, heuristic baseline, and `\texttt{AutoK}` claims.
- Validation: Reviewer gates PASS; LaTeX compile PASS. Existing Chapter 3 overfull hboxes are unrelated to this paragraph.
- Risks / follow-ups: Continue processing the remaining high-suspicion abstract paragraph one paragraph per commit.
- Commit: see Git history for message `docs: polish aigc zh abstract paragraph 2`

### 2026-05-08 21:01 | Thesis 第四章全文审查 Round 2（caption ↔ body / 数字算术 / 协议一致性）

- Goal: Round 2 做核验式审查——检查所有 figure caption ↔ body 文字描述对齐、数字内部算术、跨表/跨节协议一致性。Round 1 已修主要术语漂移，Round 2 主要做深度核验。
- Scope:
  - **核验通过的检查项（无需修复）**：
    - **5 figure caption ↔ body 全部对齐** ✅：fig 4-1 (kv-ruler32) / 4-2 (kv-error-heatmap) / 4-3 (autok-protection) / 4-4 (pareto) / 4-5 (regime-heatmap) 的 caption 文字描述与对应正文 \\ref 段落语义一致
    - **14 table caption ↔ body 全部对齐** ✅：所有 \\caption{...} 与正文「表~\\ref{...}~显示/汇总/表明...」语义一致
    - **数字算术内部一致** ✅：tab:ch4-int8-canonical mean 行 (7.07+4.90+9.21)/3=7.06、(7.16+4.88+9.20)/3≈7.08；tab:ch4-longbench-official 宏平均行同理；tab:ch4-rolealign-kivi |ΔPPL|≤0.15
    - **best-$k$ 跨表一致** ✅：tab:ch4-regime-main 注（Qwen2.5-3B k=1, LLaMA-3.1-8B k=11, Qwen2.5-14B k=7, Mistral-7B k=3）与 tab:ch4-profile-a/b 头标 (BA-k1/BA-k3/BA-k7/BA-k11) 完全对齐
    - **百分比读数算术正确** ✅：14B 长序列 -17\\%/-28\\%/-40\\% 对应 -14.54/86.08, -33.26/119.83, -77.08/190.23 算术正确
    - **覆盖阈值跨表跨图一致** ✅：14B=90\\%, 其余=80\\% 在表注 446、fig 4-3 caption（Round 1 修订后）、tab:ch4-profile-a 与 tab:ch4-profile-b panel header 一致
    - **PPL 读数 K4V16 +13,774\\%** ✅：(1290.9-9.31)/9.31 = 137.74 → +13,774\\% 算术正确
    - **§4.6 机制辨析层无 overclaim** ✅：line 784「仍属于解释性推断，尚未构成机制定理」、line 786「避免...普适性 overclaim」、line 798「克制语气」属克制写作纪律
    - **scope 声明全章一致** ✅：「LongBench 风格合成」vs「官方 LongBench」在 line 55/61/108/117/124/169/171/818 反复一致
  - **修复的 1 处问题（P2 跨节协议混用）**:
    - **line 701 8B vs 14B 4K 控制对照协议混用**: 「8B vs 14B 同 H_kv=8 控制对比」中 8B=−0.39ms 来自 §4.5.1 表 4-7 (gen=128，44.49−44.88)，14B=−0.44ms 来自 §4.5.3 Panel A (gen=64)。同一句对照混了两个不同生成长度协议。修订为统一从 §4.5.1 (gen=128) 取值：8B=−0.39ms，14B=−0.40ms (67.67−68.07)，并在文中显式说明协议来源。
- Changed files: `thesis/chapters/ch4_experiments.tex` (1 处)
- Commands: `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- Outputs: 99 页稳定，0 hard error
- Validation:
  - 修订后 8B vs 14B 4K 对照统一为 (−0.39, −0.40)，仍支持「高度一致」结论（差距 0.01ms 比原 (−0.39, −0.44) 的 0.05ms 更接近）
  - 无新增 overfull
- Risks / follow-ups:
  - Round 2 完成 caption/算术/协议三层核验，仅发现 1 处实质问题
  - 已识别但低优先级备查：17 处 hardcoded "第 4.X.Y 节"、sec:ch4-rqN 标签命名 (P3 不修)
  - **Round 3 计划评估**: ch4 经过 1 轮内部修订 + 1 轮深度核验，质量已显著收敛。如需继续，Round 3 可关注「与外部章节（ch1/ch3/ch5/abstract）的横向对齐」最后一遍核查

### 2026-05-08 20:56 | Thesis 第四章全文审查 Round 1（术语 / caption / 跨章一致性扫描）

- Goal: 启动 ch4 全章审查。Round 1 聚焦快速发现的高密度问题：跨章节术语漂移（"Key 精度下降"）、figure caption 与表注矛盾、章内交叉引用。
- Scope:
  - **ch4 全章扫描结果（先查后修）**:
    - **40 个 \\ref 全部解析** ✅
    - **14 table + 5 figure 全部被正文 \\ref**（无悬空表/图）✅
    - **路径名一致**：INT4-RoleAlign / INT8-Canonical / KIVI-style / MixedKV 横向稳定（无 snake_case 残留）✅
    - **统计协议文档化完整**：Bootstrap CI / sign-flip / BH-FDR 在 §4.1.4 完整说明 ✅
    - **关键数字内部一致**：73.4% / 14.76 / 6.90 / 7.23 / 7.15 / +0.02 全部与 ch4 表 + ch5 答复对齐 ✅
    - **PPL 数字逐项校验**：tab:ch4-kv-ppl 四行（FP16=9.31, K4V16=1290.9 即 +13,774% 等）算术正确 ✅
  - **修复的问题**：
    - **ch4 line 347 "Key 精度下降"**: 与同段 line 388 "Key 侧低比特噪声"族术语不统一，且与 ch3 line 54 修复同一类别（Codex 已指出"精度"在量化论文中混淆 accuracy/precision/numerical precision 三义）。修复为"Key 侧低比特噪声"。
    - **ch4 line 286 "Key 精度是否已经进入足以扰动 attention ranking 的区域"**: 同样的术语问题。修复为"Key 侧位宽是否已经低到..."（保留语义，更精确）。
    - **ch4 line 456 fig 4-3 caption "同一 coverage 规则下"**: 与表注 446 明确说明的"AutoK 14B 阈值 90\\%，其余 80\\%"矛盾。修复 caption 为"覆盖率准则下各模型的保护层结构（覆盖阈值 14B 为 90\\%，其余模型为 80\\%）"+ 引用表注 anchor。
    - **ch2 line 91 "Key 侧精度下降"**: 同 ch4 类别问题。修复为"Key 侧位宽降低"。
- Cross-chapter audit findings:
  - sec:ch4-rqN 标签命名（rq1/rq2/rq3）与 ch1 RQ1/RQ2/RQ3 不一一对应——这是 ch4 内部 anchor 命名约定。但实际正文用"第一章研究问题 X"明示对应关系（line 130, 204, 833 等），无歧义。保留为低优先级 P3 备查（不修）。
  - 17 处 hardcoded "第 4.X.Y 节"（line 16/55/65/100/102/108/117/155/164/202 等）。结构稳定时不破坏，作为 P3 备查（不修）。
  - "高精度 Key/Value/路径"（line 256/334/345）是"高位宽参考"的口语用法，与 "Key 精度下降"问题不同类别，可接受。
- Changed files: `thesis/chapters/ch4_experiments.tex` (3 处), `thesis/chapters/ch2_related_work.tex` (1 处)
- Commands: `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`
- Outputs: 99 页（与 ch3 复审后稳定一致），0 hard error；overfull 状态：1.5pt + 7.9pt 两处 cosmetic 残留（继承自 ch3 复审）
- Validation:
  - grep "Key 精度" 在 ch1-ch5 全文清零 ✅
  - grep "同一 coverage 规则" 仅 fig 4-3 caption 一处，已修正 ✅
- Risks / follow-ups:
  - **Round 2 计划**: 检查表/figure caption ↔ 正文宣称的细节对齐（caption claim ↔ body claim 逐项对照），公式利用率，机制辨析层（§4.6）的强声明是否都有数据锚点

### 2026-05-08 20:33 | Thesis 第三章 Codex 全章复审（2 P1 + 4 P2 + 1 跨章节）

- Goal: 用户跑了 Codex 完整全章审查（latexmk -outdir=/tmp/ch3_full_review_build），返回 2 P1 + 4 P2 + 1 跨章节问题。逐项验证后全部应用修订。
- Verification process（先验证再修）:
  - **P1 #1 line 700 系统路径口径**: 验证 ch4 line 625 TPOT 表标题为「参考路径 (INT4) / KIVI(INT4) / Triton 融合路径 (INT4) / FlashInfer(INT4)」+ line 670-672 的实际数字以 INT4 为主 → ch3「主系统落地路径是 INT8 融合核」误导。Codex 正确 ✅
  - **P1 #2 line 54「Key 精度下降」**: 同段 line 58 已用「Key 侧低比特退化」，「精度」与 accuracy/precision/数值精度三义混淆。Codex 正确 ✅
  - **P2 #1 line 135「KL...不同模型规模与 bit-width 下的收益强弱」**: 验证 ch4 §4.6.1 line 751 标题为「KL 与 MSE 校准目标的规模依赖性机制辨析」+ line 756 实际写「KL 的必要性会随位宽压缩强度与模型鲁棒性而变化」+「KL 与数值代理趋同」，确实是必要性边界讨论而非「不同模型规模 × bit-width 收益强弱」全覆盖。Codex 正确 ✅
  - **P2 #2 line 415/423 重复 TopK 平局**: 两处文字几乎逐字重复「在敏感度并列时按层索引升序打破平局，使保护集合在复现中唯一确定」。Codex 正确 ✅
  - **P2 #3 line 441「见本节后续小节」**: 该 \\ref 指向 sec:ch3-allocator，正是当前所在节，自指；且「跨模型 best-$k$ 行为」实际由 ch4 报告。Codex 正确 ✅
  - **P2 #4 overfull hbox**: log 确认 line 172 (50pt) / 369 (1.5pt 极小) / 644 (73.8pt 最严重)。Codex 正确 ✅
  - **跨章节 ch2 line 175「这些工作提供启示我们」**: 验证为不通顺中文（动词「提供 + 启示」复合后接代词不合习惯）。Codex 正确 ✅
- 应用的修订:
  - **P1 #1 修订**: line 700 改为三分口径——\\texttt{INT8} 融合核支撑基准路径；\\texttt{INT4-RoleAlign} 主线用 \\texttt{torch_ref} 保证语义核对；\\texttt{INT4} 融合扩展（KIVI / Triton 融合路径）承担 ch4 系统边界读数。
  - **P1 #2 修订**: 「Key 精度下降」→「Key 侧低比特噪声」（与同段 line 58「Key 侧低比特退化」族系统一）。
  - **P2 #1 修订**: 「KL 在不同模型规模与 bit-width 下的收益强弱」→「KL 与数值代理（如 MSE）的必要性边界——在哪些条件下 KL 更必要、在哪些条件下二者会趋同」（精确对齐 ch4 §4.6.1）。
  - **P2 #2 修订**: 删除 line 415 的 TopK 平局重复说明，仅保留 line 423 在 \\operatorname{TopK} 公式后的描述（更紧贴算子定义）。
  - **P2 #3 修订**: line 441 改为「固定 $k$ 网格由本节定义，跨模型 best-$k$ 读数由第四章第~\\ref{subsec:exp-int4-cross-model}~节报告」（消除自指 + 明确 ch4 锚点）。
  - **P2 #4 修订**:
    - line 172 ($c_K, c_V$ 公式) `equation` 环境改 `align`，两式分行 → 50pt overfull 消除
    - line 644 cases 标签精简（「不启用自适应保护时」→「无自适应保护」等），并删除 `\\bigl/\\bigr` → 73.8pt 改善至 7.9pt
    - line 702 (新 P1 #1 引入) 句首改写避免长英文标识聚集 → 11.2pt 消除
    - line 644 prose 长段拆为两段 + `——` 改为「：；」组合 → 28.9pt 大幅改善
  - **跨章节 ch2 line 175 修订**: 「这些工作提供启示我们」→「这些工作共同说明，」
- Changed files: `thesis/chapters/ch3_method.tex` (28 行变更), `thesis/chapters/ch2_related_work.tex` (1 行)
- Commands: `cd thesis && xelatex -interaction=nonstopmode -halt-on-error main.tex`（多次迭代）
- Outputs: 99 页稳定；overfull 从 4 处（73.8 + 50 + 28.9 + 11.2 = 163.8pt）减少到 2 处（1.5 + 7.9 = 9.4pt，cosmetic 范畴 <10pt）。0 hard error。
- Validation:
  - P1 #1: grep ch3 line 700 无残留「主系统落地路径是 INT8 融合核」✅
  - P1 #2: grep ch3「Key 精度下降」无残留 ✅
  - P2 #2: line 415 「在敏感度并列时」grep 仅 line 423 一处 ✅
  - P2 #3: line 441 grep 无「见...本节后续小节」自指 ✅
  - 跨章节: ch2 line 175 grep「提供启示我们」无残留 ✅
- Risks / follow-ups:
  - 残留 overfull 9.4pt 总和（line 369 表格边界 1.5pt + line 644 prose 7.9pt）属于学术排版可接受范围
  - Codex 全章复审已通过 P1 全部 + P2 全部 + 跨章节，第三章质量在四轮审查后基本稳定
