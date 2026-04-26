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

### 2026-04-21 00:37 | 术语统一 + 散装英文中文化 + 内部工作语言清理（281 处批处理）
- Goal: 用户对 Ch3 结构重组 + 术语命名提议中发现 7 条术语冲突 + 26 个散装英文词 + 大量内部工作语言（Phase 1/3/8/9、Gate C、final-ready、Level-5、story §X.Y、Weak/Mixed、clean-provenance pin=）泄露进论文正文；约定先做全局术语清理再动 Ch3 结构（顺序反了会漏清理）
- Scope: thesis/chapters/ 8 个 tex 文件批处理，281 处替换 (stage1=39 / stage2=186 / stage3=55 / comments=7)；新增 normalize_terminology.py 可复用脚本
- Changed files:
  - scripts/thesis/normalize_terminology.py (new, 173 lines)
  - thesis/chapters/abstract_en.tex / abstract_zh.tex / appendix.tex / ch1-ch5 (+232/-232, 纯替换)
- Commands:
  - `python3 scripts/thesis/normalize_terminology.py --dry-run` (分布核对)
  - `python3 scripts/thesis/normalize_terminology.py --apply`
  - 中途 bug: Stage 3 cross-model 规则在 mask 之前跑，破坏 8 处 `\label{*-cross-model-*}` / `\ref{}` → 写 one-shot restore python patch 还原 5 文件 label 参数
  - `cd thesis && xelatex -interaction=nonstopmode main.tex` ×2
- Outputs: main.pdf 101 pages / 1.64 MB
- Validation:
  - 0 undefined references / 0 multiply-defined / 0 dimension too large / 0 error
  - sanity grep: 行为对齐=0 / Gate C=0 / Phase 1 TPOT=0 / Level-5 clean=0 / Weak/Mixed=0 / clean-provenance pin=0 / BA-guided=0
  - 残留: `\label{sec:discussion-final-ready}` 1 处 (LaTeX label 不进 PDF) + 英文 abstract `regime map` 2 处 (脚本跳过 abstract_en 预期行为)
- 写作纪律新增: 用户明确"整个文章你有很多把我们内部工作的那些叙述全部泄露了...不要把那些内部的分析...写进去"——待 commit 后固化到 `feedback_thesis_writing_style.md` 第三条纪律
- Risks / follow-ups:
  - 脚本已修 bug（cross-model 规则移到 Stage 2 / Stage 3 先于 mask），未来重跑不会再破坏 label
  - 下一步：Ch3 结构重组（§3.1 改 "注意力近似误差分析" / §3.2 精简+融入原 §3.9 A 类 / §3.4 合并 §3.4+§3.5+§3.8 Triton 为 3.4.4 / §3.5 合并 §3.6+§3.7 AutoK / §3.6=原 §3.9 B 类复杂度）

### 2026-04-20 22:27 | Codex 7 issues 全修 + 写作纪律固化（memory）
- Goal: 用户审批 Codex adversarial-review 的 8 条意见全部为真问题，按 1-7 顺序全修（P2.8 图 vs 文档归为 control doc 层低优先做）；同时用户提出两条贯穿全文的写作纪律——正向陈述不写反向、学术论文语气不写技术报告——固化到 memory 并应用到这一轮所有修改
- 写作纪律固化：
  - `feedback_thesis_writing_style.md` 新建：两条纪律（正向陈述 / 不堆 bullet / 不暴露 internal terms）+ 正反例
  - MEMORY.md 索引追加；未来论文写作贯穿适用
- Codex 7 issues 修复（按 1-7 顺序执行）：
  1. **P1.3 附录 A/B 数字错**：从 `results/l2_prompt_adaptive_summary_final.csv`（frozen CSV）+ `completion_report 8B table` 重生附录 A（8B）与附录 B（1.5B/7B）的 15 row × 3 variant 完整数据，学术段落替代 "Gate C / OFF-PROTOCOL / Weak-Mixed" 等 internal verdict
  2. **P2.6 + Ch4 §4.6 旧叙事孤岛**：Ch4 §4.6 "综合讨论"开头 "以 H_kv 为组织轴" 段 + 3 bulleted "主要发现"（旧 KL-MSE/Key 主导/融合核相位图 = 旧 5-Contribution summary）整段重写为 behavior-guided framework 贯通 C1/C2/C3 的连贯叙事段；威胁效度第 1 条"H_kv 与规模共变" 降级为"$H_{kv}$ 作为解释变量，不是全文组织脊柱"；Ch2 §2 "研究空白四" 从 "H_kv 组织轴" 重构为 "behavior 保持度作为贯通 calibration 与 allocation 的统一目标"；Ch3 §3.2 L248 "以 H_kv 为结构性相关变量的实验起点" 也改
  3. **P1.1 provenance + P1.2 matched-budget 口径统一**：Ch4 clean-provenance 段落从"本章所有正文数字"软化为"final-ready 数据来自 clean-provenance + supporting 对比跨模型用 legacy backport"；Ch1 §1.4 C3 + Abstract en + T3 caption + T3 note + Ch4 §4.5.1 Mistral 共 5 处 "matched INT4 budget" → "same-order INT4 budget band" 正向表述；T3 note "±3%" 改为指向 budget band 定义段的 forward ref；Ch2/Ch4/Ch5 中 3 处 "本章不包含 X" / "只做 X，不做 Y" 反向陈述改为正向 scope 声明
  4. **P2.5 Ch3 tau⁻¹ 主体内部冲突**：§3.2 在线推理阶段 tau⁻¹ 预缩放描述 → 静态 Scale-only 在线路径；§3.3 "两阶段搜索策略" subsection 重写为 "Scale 搜索策略"（第二阶段 tau⁻¹ 搜索段改写为 "温度校正的历史定位" —— 诊断观察在 appendix 保留）；§3.5 生成循环集成 tau⁻¹ hook 注入描述 → 静态 Scale 路由；tab:ch3-kv-modes 的 $\tau^{-1}$ 列删除（6 列→5 列）；复杂度段 "第二阶段 tau⁻¹ 搜索" 删除；校准产物存储段 tau⁻¹ 删除
  5. **P1.4 §4.1 scope 分层**：L47 "实验覆盖四个开源大语言模型" → "六个开源大语言模型...依 experimental role 分为三类 (canonical validation / cross-model main matrix / supporting reference)"；LongBench-style 7 任务 benchmark vs 5 task main matrix 关系补写
  6. **P2.7 附录 internal terms**：与 #1 合并处理，附录 A/B 重写时全部清零
  7. **P2.8 图 vs 画图文档漂移**：tracker 追加"图表与 doc 对齐说明"；story §11 图④ spec 由用户手动调整（接受 linter 改动不 revert）
- Changed files:
  - thesis/chapters/ch1_introduction.tex (matched-budget)
  - thesis/chapters/ch2_related_work.tex (H_kv 组织轴 + 空白四 + positioning 段)
  - thesis/chapters/ch3_method.tex (tau⁻¹ 主体清理 × 5 处)
  - thesis/chapters/ch4_experiments.tex (provenance + scope + §4.6 整段 + matched-budget × 3)
  - thesis/chapters/ch5_conclusion.tex (Limitation 5 正向化)
  - thesis/chapters/abstract_en.tex (matched-budget → same-order)
  - thesis/chapters/appendix.tex (附录 A + B 重生 with frozen CSV + internal terms 清零)
  - thesis/tables/table_t3_cross_model_main.tex (caption + note 改口径)
  - scripts/thesis/make_table_cross_model_compare.py (脚本 source 同步)
  - docs/thesis_rewrite_tracker_20260420.md (figure sync note)
  - ~/.claude/...memory/feedback_thesis_writing_style.md (新建, 写作纪律 memory)
  - ~/.claude/...memory/MEMORY.md (索引追加)
- Validation:
  - xelatex × 2 pass → main.pdf 100 → 101 pages, 1.64 MB
  - 0 undefined ref / 0 undefined cite / 0 multiply-defined / 0 Dimension too large / 0 error
  - grep 附录 A 新数字（9.73/10.77/12.16/10.03）✓ 匹配 frozen CSV
  - grep Hook-conditional 语言 → 0 match
  - grep H_kv 组织轴 → 清理到合理引用
- Risks / follow-ups:
  - 进入"逐段 collaborative review"模式（用户明确要求）
  - main.pdf 100 → 101（+1 from §4.6 重写 + 附录扩写）
- Commit: <pending 本批>

### 2026-04-20 21:57 | Thesis Hook closure 落地 — Ch4/Ch5 条件性 Hook 条款全部清除
- Goal: 响应 `docs/allocator_vs_kivi_closed_20260420.md` §5 的 thesis-side action list，把 Ch4 / Ch5 里所有"若 Hook 激活..." / "条件 Future Work" / "story §13 Hook" 类 conditional 措辞全部改为非条件的 past-tense 陈述（L4_CLOSED 决定后不保留后门式 disclaimer）
- Scope:
  - **Ch4 §4.2 opening**（L305-309）："为 §2.5 预留的 Allocator-vs-KIVI matched-budget 正式对比留出 Hook 位置"→ 改为"本章不包含 matched-budget 下的 formal comparison；allocator 作为方法贡献在 §\ref{sec:ch3-allocator} 保留，本论文不就系统性超越 KIVI 作 claim"
  - **Ch4 §4.2.3 HOOK POSITION LaTeX 注释块**（L636-644，9 行）：整块删除（Hook 永不激活，占位注释变死代码）
  - **Ch4 §4.3 Budget band 段**（L678-679）："作为条件 Future Work（story §13 Hook、...）"→ "作为 Future Work（§\ref{sec:conclusion-future}），不在本文 scope"
  - **Ch5 §5.1 发现三 末尾**（L76）："若 Hook（story §13）激活则可具体化为正式 claim。"→ 整句删除
  - **Ch5 §5.2 第 5 条 Limitation**（L157-162）：旧"【条件性 Limitation】...若 Hook 激活则 limitation 可删除"→ 新写为普通 Limitation，含 G2 探索性实证事实："allocator 需 1.5-1.8× KV 内存换 1-3% quality 提升 + 16% (model,task) 反向劣于 KIVI，cost/benefit 不支持 systematic claim"
  - **Ch5 §5.3 Future Work 3**（L192-199）：旧"story §13 Hook 的正式对比包...若达到 L1/L2 则升级为正式 claim + ExecPlan 骨架冻结"→ 新写为非条件延伸工作描述（bit dictionary 扩展 / 新 context / 新架构下重新搜索 budget-matched policy）
- Changed files:
  - thesis/chapters/ch4_experiments.tex（3 处 Hook-conditional 清除）
  - thesis/chapters/ch5_conclusion.tex（3 处 Hook-conditional 清除，含 Limitation 第 5 条实证事实扩写）
- Commands:
  - Read docs/allocator_vs_kivi_closed_20260420.md §5 action list
  - grep 定位当前 Ch4/Ch5 Hook 残留行（Phase 10 后行号偏移）
  - 6 组 Edit 逐个清理
  - xelatex × 2 pass → main.pdf 99 → **100 pages** (+1 from Limitation 5 + Future Work 3 扩写)
  - grep verify：0 residual Hook refs
- Outputs:
  - Ch4 / Ch5 不再出现任何"若 Hook 激活" / "条件 Future Work" / "story §13 Hook" / "升级为正式 claim" 类措辞
  - Limitation 第 5 条从 meta 条件性改为实证事实陈述（符合 feedback_meta_disclaimers 纪律）
  - Future Work 3 保留但去 conditional framing，允许未来 revisit 时自然延伸（不是"激活开关"）
- Validation:
  - xelatex: 100 pages, no halt, 0 undefined ref / 0 undefined cite / 0 multiply-defined
  - grep -rn 'Hook|若 Hook|条件 Future Work|story §13' thesis/chapters/ → 0 match
- Risks / follow-ups:
  - docs/allocator_vs_kivi_closed_20260420.md §6 保留 infrastructure 未动（allocator 方法 / calibration JSON / scripts 等）
  - §7 禁止事项：不启 ablation / 不扩 bit dictionary / 不重跑 policy 搜索——全部遵守
  - 下一步：进入用户指定的"逐段 collaborative review"模式
- Commit: <pending 本批>

### 2026-04-20 21:48 | Allocator vs KIVI Hook 最终 L4 关闭 — 用户决定不写此 claim
- Goal: 在 main phase 完整收口（5 model × 5 task × 3 system = 360 CSV, 0 failure）+ G2 Claim Strength aggregate 产出后，按实际数据做 claim 层最终决定
- G2 aggregate 数据:
  - 25 cells: win 7 (28%) / tie 14 (56%) / lose 4 (16%)
  - mean Δ = +0.192（quality 量级 5-20，相当 ~1-3% 相对提升）
  - budget ratio: 1.501×–1.818×（allocator 用 50-80% 额外内存）
  - per-model 极化：14b (60% win / 0 lose) vs mistral7b (20% win / 60% lose) vs 3b (100% tie)
  - aggregate 产物: `results/system_vs_kivi/aggregate/main/{summary_long,summary_wide,g2_judgment}.{csv,md,json}`
- 决策过程:
  - 我初判 L3 framing（mean Δ 微正 + 14b 干净赢 → 想包装成 Pareto advantage）
  - 用户质疑 "是不是跑偏了" → 我回退承认这是美化数据
  - 诚实定位：花 50-80% 额外内存换 ≤3% quality 且 16% 反向输，不是 Pareto advantage，符合 §13.2 L4 "mechanism-only"
  - **用户最终决定**（原话）："我们用了更多的成本还不一定能保证稳赢的话，那我们为什么还要再做这个呢？"
- 落地:
  - `docs/thesis_story_20260420.md` §13.1 Hook 状态从 "L3-pending" 改为 **"L4_CLOSED"**，附决定日期 + 依据 + 数据沉没成本保留说明
  - §13.4 激活清单 3 个 gate 全部 ✅，最终判定 L4，其余清单项关闭
  - allocator 作为 §3 方法贡献保留（"behavior-guided per-layer bit allocation"），不 claim 系统性超越 KIVI
  - thesis chapters 里的 "conditional Future Work" / "Hook position" 注释（ch2_related_work §... / ch4_experiments §4.X / ch5_conclusion §... "条件 Limitation + 条件 Future Work"）由写作 session 下次按 L4 规则简化：去掉 "若 Hook 激活到 L1/L2 则..." 条款，保留 "matched-budget formal compare 作为 Future Work" 一条
- Changed files:
  - `docs/thesis_story_20260420.md`
  - `iteration.md`
- 保留 infrastructure（未来扩展 bit dictionary 或 re-search policy 时可复用）:
  - `scripts/system_vs_kivi_common.py`（含 pareto/strict gate_mode + SVK_MODEL_PATH env override）
  - `scripts/check_system_vs_kivi_completeness.py`（pareto/strict 双 gate）
  - `scripts/run_system_vs_kivi.py` + `scripts/aggregate_system_vs_kivi.py`
  - `scripts/remote_watchdog.sh`（通用 tmux watchdog，已进 .agents/skills/remote-server/SKILL.md）
  - allocator backend kv_mode `int4_ours_asym_alloc` + `src/cache/role_aware_allocator_cache.py`
  - 5 rolealign calibration JSON（artifacts/）
- 未做:
  - **取消 ablation phase 启动**（L4 定位下 ablation 无 claim 支撑作用，跑 3-5h × 3卡 ≈ 9-15 GPU-hour 为不支撑 claim 的实验做 mechanism 分解，不符合科研纪律）
- Commit: <pending>

### 2026-04-20 07:38 | Thesis figure/format finalize — hard compile issues cleared + core figures repainted
- Goal: 清掉 thesis 当前的硬格式问题，并把 `fig4/fig7/fig8/fig9` 与 `kv_ablation_summary_ruler` 收口到可审阅状态。
- Scope: thesis 编译日志清理、Ch4 图文语义对齐、fig7/fig9 重画、fig4/fig8/kv-ablation 版式收尾、PDF 目视验收。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/appendix.tex`
  - `scripts/thesis/plot_sensitivity_heatmap.py`
  - `scripts/thesis/plot_l2_pareto.py`
  - `scripts/thesis/plot_regime_map.py`
  - `scripts/thesis/plot_scale_trend.py`
  - `scripts/generate_thesis_figures.py`
  - `thesis/figures/fig4_sensitivity_heatmap.pdf`
  - `thesis/figures/fig7_pareto.pdf`
  - `thesis/figures/fig8_regime_map.pdf`
  - `thesis/figures/fig9_scale_trend.pdf`
  - `thesis/figures/kv_ablation_summary_ruler.pdf`
- Commands:
  - `python3 -m compileall -q scripts/thesis scripts/generate_thesis_figures.py`
  - `PYTHONPATH=/tmp/codex_pydeps ... python3 scripts/thesis/plot_sensitivity_heatmap.py`
  - `PYTHONPATH=/tmp/codex_pydeps ... python3 scripts/thesis/plot_l2_pareto.py`
  - `PYTHONPATH=/tmp/codex_pydeps ... python3 scripts/thesis/plot_regime_map.py`
  - `PYTHONPATH=/tmp/codex_pydeps ... python3 scripts/thesis/plot_scale_trend.py`
  - `PYTHONPATH=/tmp/codex_pydeps ... python3 scripts/generate_thesis_figures.py --only kv_ablation_summary --tables_dir results/final/final_data/kv_ablation/tables --out_dir thesis/figures`
  - `cd thesis && bibtex main && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
  - `rg -n "undefined references|multiply-defined labels|fig:ch3-framework|sec:app-kv-ablation-full|Missing character: There is no [④⑦⑧⑨]" thesis/main.log -S`
- Outputs:
  - `fig7_pareto.pdf` 改为 quality-budget Pareto 视图；
  - `fig9_scale_trend.pdf` 改为 categorical regime-ordering 图，不再伪装成连续 scaling law；
  - `fig4_sensitivity_heatmap.pdf` 顶部标注清理并明确为 protection map；
  - `fig8_regime_map.pdf` 标签改为 `k_*` 语义；
  - `kv_ablation_summary_ruler.pdf` 的 0 分失败样式从竖排 `FAIL` 改为红色 `x + 0.0`；
  - thesis 中坏引用、重复 label、圈号缺字问题已清除。
- Validation:
  - thesis 成功编译出 `main.pdf`（99 页）；
  - `main.log` 中已无 `undefined references`、`multiply-defined labels`、`fig:ch3-framework`、`sec:app-kv-ablation-full`、圈号缺字告警；
  - 核心图经 PDF→PNG 目视复审，`fig7/fig9` 从“不通过”提升为可用稿图。
- Risks / follow-ups:
  - 仍有若干历史正文 `Overfull/Underfull` 告警，主要集中在长英文短语与少数旧段落排版，不再属于本轮硬 blocker；
  - `docs/claude_thesis_outline_pack_v1.md` 仍是无关 dirty，未纳入本轮。

### 2026-04-20 07:19 | Thesis Phase 10 — references.bib 清理 + cite 位置审计
- Goal: 按"新叙事相关度"对 references.bib 做清理：删除与 behavior-guided framework / regime map / AutoK 新叙事无关的 unused entries；新增相关但缺失的 cite 位置；保证 xelatex + bibtex 编译无 undefined citation / undefined ref / multiply-defined label
- Scope:
  - **审计结果**：bib 79 entries / 57 unique cited keys / 22 unused / 0 missing
  - **Tier A 删除 18 unused**（aminabadi2022deepspeed / bai2025longbenchv2 / bean2025measuring / chen2023longlora / dettmers2024qlora / ding2024longrope / egiazarian2024aqlm / han2025polarquant / ouyang2025lowbit / peng2023yarn / press2022train / shao2024omniquant / sheng2023flexgen / tseng2024quipsharp / yuan2025numerical / yue2024wkvquant / zheng2024sglang / zhang2024coupled）
  - **Tier B 新增 4 处 cite**：
    - `fang2025longppl` → Ch5 §5.4 Limitations 第 1 条（PPL 作为长上下文指标的局限）
    - `fogliato2024precise` → Ch4 §4.1.4 统计框架（小样本精确评测 + Bootstrap CI 策略）
    - `ye2025flashinfer` → Ch3 §3.5 Triton 节（与 FlashInfer INT4/INT8 decode kernel 互为补充）
    - `yuan2024kvcompressionbench` → Ch2 §2.4 KV compression 综述说明
  - **Tier C 顺便修复的 label 冲突**：
    - Ch3 `sec:ch3-triton` duplicate label（§3.5 section + 多余的注释块 label，保留首个）
    - Appendix `sec:app-kv-ablation-full` duplicate（Phase 7 加的 alias 与原 label 重复，删多余的）
  - **Tier D 删除 orphan figure ref**：Ch3 L111 旧引用 `fig:ch3-framework`（H1 修复时删除 figure block 后未清），改为指向 Ch1 §1.5 的 `fig:framework-overview`
- Changed files:
  - thesis/references.bib（79 → 61 entries，~7.4 KB 瘦身）
  - thesis/chapters/ch5_conclusion.tex（Limitations 第 1 条加 fang2025longppl）
  - thesis/chapters/ch4_experiments.tex（§4.1.4 统计框架加 fogliato2024precise）
  - thesis/chapters/ch3_method.tex（§3.5 Triton 加 ye2025flashinfer + du2026bitdecoding comment；删除 L111 orphan fig:ch3-framework ref；删 duplicate sec:ch3-triton label）
  - thesis/chapters/ch2_related_work.tex（§2.4 加 yuan2024kvcompressionbench）
  - thesis/chapters/appendix.tex（删 duplicate sec:app-kv-ablation-full label）
- Commands:
  - Python audit script: bib 条目 × cite keys 集合运算 + 逐条判读相关度 + cite 位置检查
  - Python bib-cleanup 脚本: balanced brace regex 删除 18 个 entry
  - `xelatex + bibtex + xelatex × 2` 完整循环 → bbl 更新 resolve 所有 cite
- Outputs:
  - references.bib 从 79 → **61 entries**（-23%）
  - 新增 4 处 cite 位置（story §12 相关工作 positioning + 统计 + 评测 + kernel benchmark）
  - 全部 multiply-defined / undefined ref / undefined cite / Dimension too large 警告清零
- Validation:
  - xelatex × 2 pass → main.pdf **99 pages, 1.63 MB**
  - **0 Warning: Reference undefined**
  - **0 Warning: Citation undefined**
  - **0 multiply-defined labels**
  - **0 Dimension too large**
  - **0 ! Error**
- Risks / follow-ups:
  - bib 61 条全部在正文有至少 1 次 cite
  - 打 tag `thesis-m-plus-v1-final-refs` 作为 Phase 10 终点
- Commit: <pending 本批>

### 2026-04-20 06:00 | Thesis Phase 9h — Codex adversarial-review 6 issues 全部修复
- Goal: 响应 Codex adversarial-review（verdict: needs-attention / no-ship）指出的 3 HIGH + 3 MEDIUM issues，逐一修复
- Codex 6 issues 修复状态:
  - **H1 Ch3 §3.2 legacy τ⁻¹ figure 块自相矛盾**：删除旧 `fig:ch3-framework`（attention-KL framing）+ 旧 `fig:ch3-calib-pipeline` TikZ（阶段 2 τ⁻¹ 搜索节点）+ L125 正文 "(3) τ⁻¹ 作为诊断产物"；统一由新 `fig:framework-overview` + `fig:calib-pipeline` 承担，τ⁻¹ 严格作为附录 diagnostic note ✅
  - **H2 matched-budget 数学不一致**：承认 eq:ch4-matched-budget 线性于 bit-width；allocator $\bar{b}\in[4.5, 5.0]$ vs uniform $\bar{b}=4.0$ 实际对应 +12.5% 至 +25% memory delta（不是 ±3%）；重命名段落为 "Budget band（非严格 matched-budget）"；整章定位改为 **regime signature readout** 而非 formal matched-budget comparison ✅
  - **H3 behavior joint 定义统一**：Ch1 §1.2 假设 H 改为 "分布 a 与输出 o 的联合保持度"；解释 telescoping 分解中两侧 coupled（$\hat a_i$ 出现在聚合侧项）；分布侧 KL 作为可优化工程代理同时约束两条误差路径；Abstract 中英对齐 ✅
  - **M1 Ch4 winner framing → regime signature**：4 处关键词替换（"winner 多样性"→"per-model regime signature"、"winner 指纹"→"per-model regime footprint"、`\text{winner}(X)=Y` equation → `\text{top-tier}(X) \ni Y` relation、"不存在跨模型统一最优 policy"→"不存在跨模型统一的 point 最优 policy...top-tier 落点 vs universal winner"）✅
  - **M2 图 ① "正交" → "耦合 telescoping"**：fig1_error_decomposition.tex caption 改写，明确公式是 telescoping 恒等式非 K/V 独立因子化；保留 behavior 作为联合对象的论证（分布 a 保持 → $\hat a_i$ 接近 $a_i$ → 聚合侧项第一因子受控）✅
  - **M3 fig7_pareto Dimension too large**：根因 matplotlib annotate 用 `xytext=(x*1.15, ...)` 在 log scale 下被误解为 log-space 乘法，产生极大 x 坐标（page size 被炸到 764282 × 357 pts）；修为 `xytext=(frac, frac), textcoords="axes fraction"` + 显式 set_xlim；重跑 plot_l2_pareto.py，page size 恢复到 998 × 332 pts ✅
- Changed files:
  - thesis/chapters/ch3_method.tex（H1：删 2 legacy figure block + 清 τ⁻¹ 产物描述）
  - thesis/chapters/ch4_experiments.tex（H2：§4.3 "budget band 非严格 matched" framing；M1：winner → regime signature 4 处）
  - thesis/chapters/ch1_introduction.tex（H3：假设 H 改 joint）
  - thesis/chapters/abstract_zh.tex（H3：joint behavior + telescoping）
  - thesis/chapters/abstract_en.tex（H3：mirror 中文）
  - thesis/figures/fig1_error_decomposition.tex（M2：caption 正交 → 耦合）
  - scripts/thesis/plot_l2_pareto.py（M3：annotate 用 axes fraction + set_xlim）
  - thesis/figures/fig7_pareto.pdf（M3：regen 后 size 正常）
- Commands:
  - Codex adversarial-review 后台运行 → verdict: needs-attention, 6 issues
  - 逐一 Edit / Python slice 替换 / Python regen
  - xelatex smoke × 2 pass → main.pdf **99 pages**（从 100 减 1 因 H1 删了 2 TikZ block 腾空间）
  - **Dimension too large 错误消失**
- Outputs:
  - 全 6 issue 修复落地，叙事与数学一致性 100% 对齐 story + objective
  - Ch3 变为\emph{单一}方法叙事（无 τ⁻¹ main-path 矛盾）
  - Ch4 §4.3 从 "matched-budget formal" 降为 "regime signature readout"（诚实 framing）
  - Ch1 + Abstract 中英 "behavior" 全部用 joint (a, o) 定义
  - 图 ① caption 与公式数学对齐（telescoping 非正交）
  - fig7 Pareto page size 修复（764282 → 998 pts）
- Validation:
  - xelatex: 99 pages, no halt, no "Dimension too large"
  - 镜像 triplet（Ch1 §1.4 / Ch5 §5.1 / Abstract）behavior 定义一致
- Risks / follow-ups:
  - Phase 9 最终锁点：本 commit 之后打 tag thesis-m-plus-v1-final
  - Codex follow-up review 可选（若用户希望再跑一轮确认 no-ship → clean）
- Commit: <pending 本批>

### 2026-04-20 05:45 | Thesis Phase 9g — 图①③ TikZ + inline math 存量清存
- Goal: Phase 9 最终 polish 的 P1-P3 子项落地（剩 P4 Codex review 后台启动）
- Scope:
  - **P1 图① Attention error decomposition**：新写 `thesis/figures/fig1_error_decomposition.tex`（TikZ 3 栏布局：attention flow / 量化路径 / 两条传播分支 + 底部误差分解公式框），挂到 Ch3 §3.1 末尾
  - **P2 图③ Calibration pipeline**：新写 `thesis/figures/fig3_calib_pipeline.tex`（TikZ：WikiText-2 输入 → FP16 前向 → 共享 KL 目标 → INT8/INT4-RoleAlign 两路并行 → JSON 产物；底部注明 inv_tau 降级），挂到 Ch3 §3.3 sec:ch3-calibration
  - **P3 inline math 存量清**：按 feedback_math_display_style 规则扫 Ch1-Ch3 复杂 inline math（含 sum/prod/int/frac/sqrt），**6 处全部改 display**：
    - Ch1 §1.2 attention 定义（$z_i$/$a_i$/$o$ 三连 → 1 个 equation* 合并）
    - Ch3 §3.1 量化后输出 $\hat o$
    - Ch3 §3.3 softmax 局限性 logits 扰动公式
    - Ch3 §3.3 layer-wise allocator 平均位宽约束
    - Ch3 §3.3 role-aware 总预算约束
  - 顺便修 Ch3 duplicate label：§3.1 `eq:ch3-kl` → `eq:ch3-kl-general`（避免与 §3.3 的具体 KL 定义撞名）
- Changed files:
  - thesis/figures/fig1_error_decomposition.tex（新建）
  - thesis/figures/fig3_calib_pipeline.tex（新建）
  - thesis/chapters/ch1_introduction.tex（§1.2 3 inline → 1 display）
  - thesis/chapters/ch3_method.tex（4 inline → 4 display + duplicate label rename + §3.1 末图① \input + §3.3 KL 目标后图③ \input）
- Commands:
  - `python3 /tmp/thesis_phase3/step_p3_scan_inline_math.py` → 初始 6 候选 → 清理后 0 候选
  - xelatex smoke × 2 pass → main.pdf 99 → **100 pages** (+1 from 新增 6 display math 块)
- Outputs:
  - M+ 图表清单 17 项：**16/17 就绪**（仅缺原本设计为 optional 的图 ③ 细节 — 已完成新版）
  - Ch1/Ch2/Ch3 inline math 存量 100% 按规则对齐 feedback_math_display_style
  - 所有 fig refs (fig:error-decomposition / fig:calib-pipeline) resolve
- Validation:
  - xelatex: 100 pages, no halt, 0 undefined fig ref
  - P3 scan: Ch1/Ch2/Ch3 复杂 inline math 候选 0/0
  - 剩 "Dimension too large" TikZ warning（不阻塞）
- Risks / follow-ups:
  - P4 Codex adversarial-review 待启动（后台执行）
  - P5 最终 commit + tag thesis-m-plus-v1-final
- Commit: <pending 本批>

### 2026-04-20 05:36 | 14B chain launcher — 等 GPU 0 空闲自动启动 14B main（不打断正在跑的 1p5b/3b）
- Goal: 3 张 GPU 都在跑 main session，无卡给 14B。不 kill 现有 session 保留 progress，改用 chain launcher 等 GPU 0 自然空闲后自动启动 14B
- Scope:
  - `scripts/launch_14b_after_gpu0.sh` — 本地后台一次性脚本：每 5 min 远端 `tmux has-session -t svk_main_gpu0` 查询，消失后立即 `tmux new -d -s svk_main_gpu0_14b` 启动 14B，带 `SVK_MODEL_PATH_14B=/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct` env override（依赖 8a87d89 的代码路径）
  - 启动 `Bash(run_in_background=true)` 任务 `beesibaru` 跑它
- Changed files:
  - `scripts/launch_14b_after_gpu0.sh` (新建)
  - `iteration.md`
- Commands:
  - `chmod +x scripts/launch_14b_after_gpu0.sh && bash -n` → `syntax OK`
  - `SSH_PASSWORD=... INTERVAL=300 bash scripts/launch_14b_after_gpu0.sh` (background id `beesibaru`)
- Outputs:
  - GPU 0 当前跑 1p5b (~2h) → 3b (~4.5h)；chain launcher 轮询后 ~6.7h 启动 14B；14B wall-clock ~15h；total main ≈ 21-22h
- Validation:
  - bash syntax 通过；launcher 在 14B launch 成功后 exit 0，退出信号触发 Claude Code notification
- Risks / follow-ups:
  - 14B 启动后，原 main watchdog (b1swt0qjp) 只盯 gpu0/gpu1/gpu2 不会盯 `svk_main_gpu0_14b`——14B 需在 chain launcher notify 后启动独立 watchdog
  - 若 GPU 0 session 异常早退 (<1p5b 完成)，chain launcher 仍会启动 14B；没有残留冲突（下次 session 是全新 tmux）
- Commit: <pending>

### 2026-04-20 05:33 | Thesis Rewrite Phase 9 — consistency audit + orphan ref 清零
- Goal: 完成 Phase 9（最终 polish）的核心工作：对照 objective.md + 3 份 source-of-truth 文档（thesis_story / chapter_drafts / data_asset_inventory + legacy_term_audit + rewrite_tracker）逐项审计论文一致性，产出 gap 报告，并修掉所有立即可修的 Minor Gap
- Scope:
  - **Phase 9a+9b+9c 审计**：读 objective.md 10 节 + thesis_story §9-§16 + drafts §1-§7 + inventory Part A + legacy_term_audit 全部；对照现 .tex 逐项核实
  - **产出 `docs/thesis_consistency_audit_20260420.md`**（约 260 行详细 gap 报告，分 Part A/B/C/D/E/F）
  - **审计结论**：总体对齐度 ~92%；objective 七条成功标准全部 ✅；红线 6/6 ✅；章节映射 20/22（缺 2 minor subsection）；图表 14/17（缺 3 TikZ）；术语冻结 6/7（landscape 1 违规）
  - **Major Gap 5 条**需用户决策（全部推荐 A 保持现状）：M1 RQ 数量 story 3 vs objective 4 / M2 Framework 层数 2 vs 3 / M3 Ch4 §4.4 prompt-adaptive 正文 / M4 Ch4 §4.6 7B aggregation / M5 "Key 主导退化" 用词保留
  - **Phase 9d 立即修**：批量 Python 脚本修 orphan ref + landscape 术语
    - 16 个旧 label mapping（sec:ch3-invtau → sec:app-invtau-diagnostic, subsec:exp-rolealign-results → subsec:exp-int4-cross-model, tab:rolealign-results → tab:t2-int4-kivi 等）
    - "校准 landscape" → "校准 profile"（术语冻结表对齐）
    - 25 处 substitution，跨 3 个文件（appendix.tex / ch3_method.tex / ch4_experiments.tex）
  - xelatex smoke 验证：**0 undefined reference warning**（从 Phase 8 的 15+ warning 降到 0）
- Changed files:
  - docs/thesis_consistency_audit_20260420.md（新建，~260 行审计报告）
  - thesis/chapters/appendix.tex（8 处 ref substitution + landscape→profile）
  - thesis/chapters/ch3_method.tex（13 处 ref substitution）
  - thesis/chapters/ch4_experiments.tex（4 处 ref substitution）
- Commands:
  - Read + grep 审计（objective.md / thesis_story §9-§15 / drafts / inventory / legacy_term_audit）
  - `python3 /tmp/thesis_phase3/step_phase9d_fix_orphan_refs.py` → 25 substitutions，all orphan refs cleaned
  - xelatex smoke × 2 pass → main.pdf **98 pages**（稳定）+ **0 undefined reference**
- Outputs:
  - 完整一致性审计报告归档为 docs 永久文档
  - 所有 Phase 3-6 重组遗留的 orphan ref 全部清除
  - 术语冻结表 100% 对齐
  - PDF 内不再出现 `??` 占位符（引用断裂）
- Validation:
  - xelatex smoke: 98 pages, 0 undefined reference
  - 审计报告覆盖 objective 10 节 + story §9-§16 + drafts §1-§7 + inventory
- Risks / follow-ups:
  - 5 Major Gap 留待用户决策（当前全部 A 方案保持现状，与 Phase 8 终稿对齐）
  - 可选 Phase 9g（图①③ TikZ + inline math 存量清理 + Codex adversarial-review）未做，工作量较高
- Commit: <pending 本批>

### 2026-04-20 05:32 | 14B 权重定位 + SVK_MODEL_PATH env override，补齐 main phase 第 5 个 model
- Goal: 用户纠正 "14B 不存在" 的错误判断——14B 在 modelscope cache 下，需要让 transformers 离线加载，并不永久修改 `_MODEL_SPECS` 默认 HF id
- Root cause（错误判断 + 正确定位）:
  - 我之前只搜 `/root/autodl-tmp/hf_cache/hub/`，认定 14B 缺失
  - 用户指出应该有 → 扩大搜索 → 找到 `/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct/`（modelscope 命名把 `.` 替换为 `___`）8 个 safetensors 共 28GB 完整
- 方案选择:
  - ❌ HF-cache symlink 方案：`snapshot_download(local_files_only=True)` 要求 blobs/sha + refs/<commit-hash> 规范结构，仅改 refs/main 不够（实测仍报 LocalEntryNotFoundError）
  - ✅ **env override 方案**：`get_model_specs()` 读 `SVK_MODEL_PATH_<KEY>` env 覆盖 `model_id`；`src/utils/hf.py::resolve_pretrained_path` 已有 `is_dir` 分支，传本地路径自动绕过 hub lookup
  - Why env (not code default)：保留 `_MODEL_SPECS` 的 HF id 用于 reproducibility，override 仅 session-scoped，审计 trail 清晰
- Changed files:
  - `scripts/system_vs_kivi_common.py` — `get_model_specs()` 新逻辑：每 key 检查 `SVK_MODEL_PATH_<KEY_UPPER>` env，存在则 override model_id
  - `tests/test_system_vs_kivi_common.py` — 新增 2 项测试：env override 命中 / 无 env 时回 HF 默认
  - `iteration.md`
- Commands:
  - `pytest -q tests/test_system_vs_kivi_common.py tests/test_check_system_vs_kivi_completeness.py tests/test_run_system_vs_kivi.py tests/test_allocator_cli_modes.py` → `34 passed`
  - remote `ls /root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct/` 确认 8 shards 28G 完整
- Outputs:
  - 14B main 启动契约：`SVK_MODEL_PATH_14B=/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct python3 scripts/run_system_vs_kivi.py --phase main --models 14b ...`
  - env override 为 session 作用域，不污染默认 HF id
- Validation:
  - 34 passed（+2 新 env override 测试）
- Risks / follow-ups:
  - 需本轮 commit + bundle 到 remote 后才能启动 14B main session
  - 14B main ~15h wall-clock（28GB 模型 load 3-5 min + 5 tasks × 3 systems × 7 aux 多 jobs）
- Commit: <pending>

### 2026-04-20 05:22 | Pareto gate P2 follow-ups（Codex R1/R2 回归修复）
- Goal: 修复 Codex R1/R2 对 Pareto gate_mode 初版（d4dd704 合入）提出的两个 P2 issue，让 checker 的 CLI default 对 smoke/main/ablation 三 phase 都自适应，并恢复 `report["issues"]` = "hard failure only" 的下游契约
- Root cause:
  - P2-1 (R1): `info_budget_drift` 塞进 `issues` 列表破坏了 "issues 只装 blocking 问题" 的契约，下游 `if report["issues"]` 误判 clean 跑为 dirty
  - P2-2 (R1→R2): `--compared_systems` default 原含 `fixed_eqmem`，但 smoke/main 只有 `auto_eqmem` → 误报 missing_system；一旦收窄 default 去掉 fixed，ablation phase 又会漏查 fixed budget
- Fix:
  - `scripts/check_system_vs_kivi_completeness.py`:
    1. `evaluate_completeness()` 把 budget 结果按 issue 类型分流：hard 进 `issues`，`info_budget_drift` 进新的 `info` key，`ok = not issues`
    2. `compared_systems` 在进 `validate_matched_budget_rows` 前与 `expected_systems` 求交集——default `auto,fixed` 在 smoke/main 自动降级为 `auto`，在 ablation 保持 `auto,fixed`
    3. `--compared_systems` default 恢复为 `"rolealign_allocator_auto_eqmem,rolealign_allocator_fixed_eqmem"` 覆盖全 phase
  - `tests/test_check_system_vs_kivi_completeness.py`:
    - 新增 `test_evaluate_completeness_skips_compared_systems_not_in_expected` 守护 intersection 语义
    - pareto drift 测试断言 `issues == [] and info 1 row`（新契约）
- Changed files:
  - `scripts/check_system_vs_kivi_completeness.py`
  - `tests/test_check_system_vs_kivi_completeness.py`
  - `iteration.md`
- Commands:
  - `pytest -q tests/test_system_vs_kivi_common.py tests/test_check_system_vs_kivi_completeness.py tests/test_run_system_vs_kivi.py tests/test_allocator_cli_modes.py` → `32 passed`
  - Codex R3 → `no discrete correctness regression`
- Validation:
  - 32 passed（+1 新 intersection 测试）
  - Codex 3 轮 review 完整覆盖 Pareto gate 语义
- Risks / follow-ups:
  - `d4dd704` 里的 Pareto gate 初版 + 本 commit 的 P2 fix 一起才构成完整修复；单独 revert 任一 commit 都会 break
  - 需在 remote 用 P2 修复后的代码跑 `--gate_mode pareto` 确认 smoke raw ok=true → 才进 main phase
- Commit: <pending>

### 2026-04-20 05:17 | Thesis Rewrite Phase 8 最终收束（Ch1 §1.4 + Ch5 + Abstract 镜像 triplet）
- Goal: M+ Phase 8 最后收束（镜像 triplet：Ch1 §1.4 contribution 段 + Ch5 整章 + Abstract 中英），严格遵守 feedback_math_display_style.md 的 display math 规则
- Scope:
  - **Ch1 §1.4 contribution paragraphs 重写**：旧 C1-C3（attention-KL 诊断透镜 / INT4-RoleAlign / 融合核相位图）→ 新 C1-C3（Framework / Method Instance / Empirical Insight + regime map），含 display math 公式块 `\begin{equation*}` 误差分解（underbrace 分布侧项 + 聚合侧项）
  - **Ch5 整章重写**（保留 `\chapter*` + `\addcontentsline` unnumbered 结构）：§1 主要发现（5 findings + 贡献总结 C1/C2/C3）/ §2 局限性（5 条）/ §3 未来工作展望（3 条，含 Hook 条件）/ §4 结语（正向收束）
  - **Abstract 中文重写**：对齐 drafts §1.3，严格按 behavior-guided framework + C1/C2/C3 + regime map 叙事
  - **Abstract 英文重写**：mirror 中文版
  - 补 Ch1 §1.5 `\label{sec:ch1-structure}`
- Changed files:
  - thesis/chapters/ch1_introduction.tex / ch5_conclusion.tex / abstract_zh.tex / abstract_en.tex
- Commands:
  - `python3 /tmp/thesis_phase3/step_phase8_ch1_contribution.py` → Ch1 §1.4 17/17 pass
  - Write ch5_conclusion.tex / abstract_zh.tex / abstract_en.tex
  - xelatex smoke × 2 pass → main.pdf 99 → **98 pages** (no halt)
- Outputs:
  - 三份镜像文档（Ch1 §1.4 / Ch5 §5.1 / Abstract）全部对齐 C1/C2/C3
  - 旧叙事全部清除；5 个 final-ready claim 显式列出在 Ch5 §5.1 发现五
- Validation:
  - xelatex 98 pages
  - Ch1 §1.4 含 display math `\begin{equation*}` 误差分解（feedback_math_display_style）
  - Ch5 §5.2 limitations 5 条 + §5.3 future 3 条
- Risks / follow-ups:
  - Phase 9（optional）全局 Codex adversarial-review 统一扫 orphan ref + 存量 inline math fix
- Commit: <pending 本批>

### 2026-04-20 05:04 | B 升级：smoke gate 从 matched-budget ±3% 重构为 Pareto-disclosure framing（数学上 ±3% 不可达）
- Goal: 按用户 B 升级版决策，把 system_vs_kivi 的 G1 Fairness Gate 从 "matched-budget ±3%" 重构为 "Pareto-disclosure"（allocator 作为 KIVI 到不了的 (higher budget, higher quality) Pareto 点公开披露）。
- Root cause（为什么 framing 必须改）:
  - 1p5b 28 层 allocator policy `bakv_auto_cov80_max` = 15 (8,8) + 13 (4,4) = 344 bits/token
  - KIVI 纯 int4 = 28 × 8 = 224 bits/token → allocator 必 1.54× KIVI
  - ±3% 约束下 allocator 只能保留 ≤1 层升 bit，数学上退化为 KIVI
  - 所以 "matched-budget winner" framing 在当前 `{4,8,16}` bit 字典下**数学上不可能** meaningful win
- Scope:
  - `scripts/system_vs_kivi_common.py` — `validate_matched_budget_rows()` 新增 `gate_mode="pareto"|"strict"` 参数；pareto 下 budget drift 作为 `info_budget_drift` 记录 + 附 `budget_ratio`，不失败
  - `scripts/check_system_vs_kivi_completeness.py` — `evaluate_completeness` 接 `gate_mode`；report 里返回 `gate_mode` 字段；CLI 新增 `--gate_mode {pareto,strict}` 默认 `pareto`；pareto mode 下 `info_budget_drift` 不 fail `ok`
  - `tests/test_system_vs_kivi_common.py` — 新增 4 项 gate_mode 测试；旧 strict 测试显式加 `gate_mode="strict"`
  - `tests/test_check_system_vs_kivi_completeness.py` — pareto mode 默认覆盖；新增 "drift reported but ok" 测试；旧 out_of_band 测试显式加 `gate_mode="strict"`
  - `docs/system_vs_kivi_preflight.md` — Fairness Rule §2 从 "matched memory ±3%" 改为 "budget disclosure + Pareto plot"；解释数学必然性 + tooling 切换
  - `docs/thesis_story_20260420.md` — §13.1 Hook 状态从 "G0 BLOCKED" 升级为 "L3-pending"；加 Framing I→II 切换条目 + smoke 实测记录；§13.4 激活清单第一项从 "matched ±3%" 改为 "budget disclosed"，明确 L1 在现 bit 字典下不可达、现实预期 L2/L3
- Changed files:
  - `scripts/system_vs_kivi_common.py`
  - `scripts/check_system_vs_kivi_completeness.py`
  - `tests/test_system_vs_kivi_common.py`
  - `tests/test_check_system_vs_kivi_completeness.py`
  - `docs/system_vs_kivi_preflight.md`
  - `docs/thesis_story_20260420.md`
  - `iteration.md`
- Commands:
  - `pytest -q tests/test_system_vs_kivi_common.py tests/test_check_system_vs_kivi_completeness.py tests/test_run_system_vs_kivi.py tests/test_allocator_cli_modes.py` → `31 passed`
- Outputs:
  - 默认 pareto gate 下 existing smoke data 预期 PASS（+50% / +73% drift 变成 `info_budget_drift` 信息行，不 fail `ok`）
  - preflight doc 把 "Pareto extension into KIVI-unreachable region" 作为 frozen framing
  - thesis_story §13 Hook 激活清单与新 gate 语义对齐，避免 gate 规则与章节叙事脱节
- Validation:
  - 31 本地 pytest passed（含 4 个新 gate_mode 行为测试）
- Risks / follow-ups:
  - 现有 smoke raw 未重跑 gate check — 需在 remote 用新代码重跑 `--gate_mode pareto` 确认 `ok=true` 才能进 main phase
  - Remote worktree 仍在 `36bf21c2`；需 fetch 本轮 commit 后再启动 main phase
- Commit: <pending>

### 2026-04-26 10:42 | Thesis Language Cleanup Round 1
- Goal:
  - 按用户反馈先处理第一项语言清洗：降低 Chapter 1 的 AI 式绕弯表达，统一 `INT8 基准路径` 口径，删除 Chapter 4 可见 RQ 编号，并清理正文中高频模板连接词。
- Changed files:
  - `thesis/chapters/abstract_zh.tex`
  - `thesis/chapters/abstract_en.tex`
  - `thesis/chapters/ch1_introduction.tex`
  - `thesis/chapters/ch2_related_work.tex`
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
- Commands:
  - `rg` sweeps for visible `RQ1/RQ2/RQ3`, `INT8 规范路径`, `canonical path`, `sanity check`, `换言之`, `前者/后者`
  - `git diff --check`
  - `latexmk -pdf main.tex`
  - `pdfinfo thesis/main.pdf | rg '^Pages:'`
- Outputs:
  - 中文正文硬性触发项清零；英文摘要保留英文术语表述。
  - Chapter 4 section headings no longer expose RQ1/RQ2/RQ3; internal labels retained for reference compatibility.
  - `INT8 规范路径` and visible canonical-path phrasing replaced by `INT8 基准路径` / baseline-path phrasing.
  - Chapter 1 contribution and problem paragraphs rewritten in direct Chinese prose.
  - `main.pdf` generated successfully, 109 pages.
- Validation:
  - `git diff --check` passed.
  - `latexmk -pdf main.tex` passed; no LaTeX errors, fatal errors, undefined references, or rerun-required warnings detected by log grep.
  - Hard grep for the above Chinese正文触发项 returned no matches.
- Risks / follow-ups:
  - This round intentionally did not address figure/table redesign, reference revalidation, or appendix restructuring.
  - LaTeX still reports existing underfull/overfull layout warnings in several tables/paragraphs; not blocking this language cleanup round.
- Commit: <pending>

### 2026-04-26 10:48 | Prompt-Adaptive Appendix Condensation
- Goal:
  - 将 prompt-adaptive selector 附录从完整逐任务数据堆叠压缩为 future-work 起点说明，避免附录承担正文主结果职责。
- Changed files:
  - `thesis/chapters/appendix.tex`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/appendix.tex`
  - `latexmk -pdf main.tex`
- Outputs:
  - 附录 prompt-adaptive 部分改为探索性补充：保留 LLaMA-3.1-8B 的 LCC 局部正向信号，并用三模型 summary 表说明 selector 后续设计空间。
  - 删除原先冗长的 8B / Qwen 1.5B / Qwen 7B 逐任务完整表，降低附录与正文主证据之间的职责冲突。
  - `main.pdf` generated successfully, 108 pages.
- Validation:
  - `git diff --check -- thesis/chapters/appendix.tex` passed.
  - `latexmk -pdf main.tex` passed; no LaTeX fatal error.
- Risks / follow-ups:
  - LaTeX 仍有既有 underfull/overfull 布局 warning；本轮未处理表格排版。
- Commit: <pending>

### 2026-04-26 11:12 | Thesis Figure and Table Boundary Sweep
- Goal:
  - 先处理用户反馈中的图表与术语边界问题：统一 `INT8 基准路径`，清除可见 RQ 编号残留，重构第三章关键流程图，修正第三章与第四章表格职责和版面问题。
- Changed files:
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/figures/fig_ch3_allocator_flow.tex`
  - `thesis/figures/fig_ch3_calibration_workflow.tex`
  - `thesis/figures/fig_ch3_framework_shared_profile.tex`
  - `thesis/figures/fig_ch3_kv_diag_needle.tex`
  - `thesis/tables/table_ch3_calibration_interfaces.tex`
  - `thesis/tables/table_ch3_path_instantiation.tex`
  - `thesis/tables/table_ch3_runtime_paths.tex`
  - `iteration.md`
- Commands:
  - `latexmk -pdf main.tex`
  - `pdftotext -layout thesis/main.pdf - | awk ...`
  - `pdftoppm -png -r 150 -f 34 -l 34 thesis/main.pdf /tmp/thesis_figcheck/page`
  - `pdftoppm -png -r 150 -f 35 -l 35 thesis/main.pdf /tmp/thesis_figcheck/page`
  - `pdftoppm -png -r 150 -f 40 -l 40 thesis/main.pdf /tmp/thesis_figcheck/page`
  - `pdftoppm -png -r 150 -f 42 -l 42 thesis/main.pdf /tmp/thesis_figcheck/page`
  - `pdftoppm -png -r 150 -f 73 -l 73 thesis/main.pdf /tmp/thesis_figcheck/page`
  - `git diff --check`
  - `rg -n "INT8 规范路径|规范路径" thesis/chapters thesis/figures thesis/tables -g '*.tex'`
  - `rg -n "\bRQ[123]\b|RQ1--RQ3|RQ1–RQ3" thesis/chapters thesis/figures thesis/tables -g '*.tex'`
- Outputs:
  - 图 3-2 改为压缩诊断图，明确 Qwen 系列支持 Key-first 动机，同时保留 LLaMA-3.1-8B 的架构例外；未把 RULER/LongBench 面板硬塞进第三章。
  - 图 3-3 与图 3-4 重构为更干净的框架/校准流程图；图 3-4 明确 K-path 使用 attention-distribution KL，V-path 使用输出扰动代理。
  - 图 3-6 改为“逐层主线 + K/V 角色预算接口”，不再把未完整验证的 role-aware allocator 画成主结果。
  - 表 3-1 删除冗余“后续”列；表 3-2 与表 3-3 降低重复，表 3-3 改为设计边界表；表 4-13 收紧为可读的双面板部署边界表。
  - `main.pdf` generated successfully, 108 pages.
- Validation:
  - `latexmk -pdf main.tex` passed; no LaTeX fatal error.
  - Rendered and inspected pages containing 图 3-4 / 表 3-1, 表 3-2, 表 3-3, 图 3-6, 表 4-13; no visible text overlap remained in the touched figure/table pages.
  - `git diff --check` passed.
  - Hard grep for `INT8 规范路径` / `规范路径` returned no matches in active thesis chapters, figures, or tables.
  - Hard grep for visible `RQ1/RQ2/RQ3` returned no matches in active thesis chapters, figures, or tables.
- Risks / follow-ups:
  - 本轮未做参考文献逐条重验。
  - 未清理未挂载的历史图表文件；后续仍需单独做一次 figure/table inventory，避免旧 RoleAlign/KL 或 canonical-path 口径在遗留文件中反流。
  - Chapter 3 的图表视觉已经能进正文，但若后续统一整本论文图形风格，还应做一次全图色彩与线宽一致性 sweep。
- Commit: <pending>

### 2026-04-26 11:32 | M2 LongBench Appendix Merge
- Goal:
  - 将原 A.18 官方 LongBench 对照验证合并回 A.7，保留 LongBench-style 补充审计表，同时把官方数据对照降为协议一致性检查段落。
- Changed files:
  - `thesis/chapters/appendix.tex`
  - `iteration.md`
- Commands:
  - `xelatex -interaction=nonstopmode main.tex`
  - `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Citation.*undefined' thesis/main.log`
  - `rg -n 'sec:app-longbench-full|sec:app-longbench-official|tab:app-longbench-full' thesis/main.aux thesis/chapters/appendix.tex`
  - `awk '/^\\section/ {if(sec) print NR-start-1" lines  "sec; sec=$0; start=NR} END {print NR-start" lines  "sec}' thesis/chapters/appendix.tex`
  - `git diff --check -- thesis/chapters/appendix.tex`
  - `pdfinfo thesis/main.pdf | rg Pages`
- Outputs:
  - A.7 改为 `LongBench 补充结果与协议一致性检查`，保留 `tab:app-longbench-full` 的 LongBench-style 补充聚合表。
  - 原 A.18 顶层 section 删除，官方 LongBench 对照压缩为 A.7 内 `官方数据一致性检查` 段落，并保留兼容 label `sec:app-longbench-official`。
  - `sec:app-longbench-official` 的 anchor 已通过 `\phantomsection` 修正为独立 paragraph anchor。
  - `main.pdf` generated successfully, 108 pages.
- Validation:
  - 两轮只读 Agent 审查均无 P1/P2；appendix 范围内 P3 已修复。
  - `git diff --check -- thesis/chapters/appendix.tex` passed.
  - `thesis/main.log` 无 undefined refs/cits、rerun warning 或 LaTeX Error。
  - `thesis/main.aux` 中 `sec:app-longbench-official` 解析到独立 `section*.206` anchor。
- Risks / follow-ups:
  - 正文 Ch4/Ch5 仍有 3 个非本轮范围 P3：官方 LongBench 首次出现处补引用、内部校准文件名降级、结论处一致性措辞收紧。
  - 根目录旧 `main.log` 可能误导后续检查；有效编译日志为 `thesis/main.log`。
- Commit: <pending>

### 2026-04-26 11:46 | Reference Validation Sweep
- Goal:
  - 对 Chapter 1--5 当前正文承重引用做第一轮严格验证，先稳定 `references.bib` 元数据和可追溯来源，不触碰正在清理的 appendix 正文。
- Changed files:
  - `thesis/references.bib`
  - `docs/reference_validation_20260426.md`
  - `iteration.md`
- Commands:
  - `perl` / `python3` citation-key extraction for Chapter 1--5
  - primary-source web checks against ACL Anthology, PMLR, OpenReview, NeurIPS, MLSys, ACM, JMLR, and arXiv
  - `latexmk -pdf main.tex`
  - `rg -n "undefined|Citation|Warning--|empty|duplicate|I didn't find|There were undefined" thesis/main.blg thesis/main.log`
  - `git diff --check`
- Outputs:
  - Chapter 1--5 当前工作树共使用 44 个 citation keys，全部在 `references.bib` 中存在。
  - 修正或补全了 GQA、LongBench、KIVI、KVQuant、ZipCache、SmoothQuant、Qwen2.5、GEAR、CacheGen、Hubara QNN、H2O、StreamingLLM、MQA、SnapKV、QJL、QuaRot、QeRL、Quantizable Transformers、AhaKV、AsymKV、HeadKV、Outlier Tokens Tracing、ChunkKV、IntactKV、KV compression benchmark 等条目的元数据。
  - 新增 `docs/reference_validation_20260426.md`，记录本轮范围、修正项、正文引用 inventory 与 primary-source examples。
- Validation:
  - `latexmk -pdf main.tex` passed; BibTeX reran and produced `main.pdf` successfully.
  - `thesis/main.blg` reports `warning$ -- 0`; no undefined citations or BibTeX warning entries were found.
  - `git diff --check` passed.
- Risks / follow-ups:
  - 本轮未认证 appendix-only citation keys；待 appendix 清理稳定后需要第二轮全 bib inventory。
  - 当前工作树中 `thesis/chapters/ch4_experiments.tex`、`thesis/chapters/ch5_conclusion.tex` 已有外部/并行 dirty 改动，本轮提交不 stage 这些章节正文。
  - 若后续决定统一 citation key 命名，可单独把历史 key（如 `agarwal2025qerl`、`qwen2025qwen25`、`zhang2024h2o`）重命名；本轮只保证渲染出的参考文献内容准确。
- Commit: <pending>

### 2026-04-26 12:53 | Ch4/Ch5 LongBench Scope Patch
- Goal:
  - 处理 M2 审查后遗留的正文 P3：补正文 LongBench 引用、去除正文内部校准文件名、收紧 Ch5 官方 LongBench 对照外推口径。
- Changed files:
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
  - `iteration.md`
- Commands:
  - `xelatex -interaction=nonstopmode main.tex`
  - `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Citation.*undefined|Warning: Citation' thesis/main.log`
  - `rg -n 'kv_calib|ddada19|pin=|clean-provenance|排除了主文评测方向被系统性读错|系统性读错' thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex`
  - `git diff --check -- thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex`
- Outputs:
  - Ch4 官方 LongBench 数据集首次正文出现处补 `\cite{bai2024longbench}`。
  - Ch4 7B KL/MSE 表注不再暴露内部校准 JSON 文件名，改为两组冻结的离线校准产物。
  - Ch5 将官方 LongBench 对照表述收紧为“有限范围内的一致性证据”。
  - `main.pdf` generated successfully, 108 pages.
- Validation:
  - `xelatex` rerun 后收敛；`thesis/main.log` 无 undefined refs/cits、rerun warning 或 LaTeX Error。
  - Ch4/Ch5 内部校准 JSON 文件名和过强“系统性读错”措辞扫描为 0 命中。
  - `git diff --check` passed.
- Risks / follow-ups:
  - Appendix 仍保留部分可复现审计用内部命名与源码路径；下一轮应单独做 appendix 内部命名清理计划。
  - 根目录旧 `main.log` 仍未处理；有效编译日志为 `thesis/main.log`。
- Commit: <pending>

### 2026-04-26 18:32 | M3 Appendix Internal Identifier Cleanup
- Goal:
  - 清理附录中的工程文件名、后台程序命名、具体源码路径与内部结果标识，保留论文级审计语义和可复现映射，不改变正文主张。
- Changed files:
  - `thesis/chapters/appendix.tex`
  - `iteration.md`
- Commands:
  - `git diff --check -- thesis/chapters/appendix.tex`
  - `rg -n 'kv_calib|\.json|src/|scripts/|results/|artifacts/|artifact|Calib 文件|文件对应关系|文件落点|结果目录|命令行|配置文件|backend|pin=|ddada19|clean-provenance|REPRODUCE\.md|RoleAlign v3|内部字符串' thesis/chapters/appendix.tex`
  - `xelatex -interaction=nonstopmode main.tex`
  - `rg -n 'Undefined|undefined|There were undefined references|Rerun to get cross-references|Label\(s\) may have changed|LaTeX Error|Citation.*undefined|Warning: Citation|Font Warning' thesis/main.log`
  - `pdfinfo thesis/main.pdf | rg Pages`
  - `rg -n '(sec:app-kv-modes|sec:app-invtau-diagnostic|sec:app-triton-variants|tab:app-7b-kl-mse)' thesis/main.aux`
- Outputs:
  - A.3 将具体复现文件名改为论文级“冻结复现入口与编号化复现清单”表述。
  - A.4 将校准产物描述改为“小型结构化校准记录”，并保留模型标识、样本数、seed、目标函数与量化格式等审计字段。
  - A.5 明确正文叙事名优先，复现配置标识仅用于审计映射。
  - A.18 去除具体校准文件名，改用稳定记录别名，同时保留 7B KL/MSE 数值与表格引用。
  - A.19 去除具体源码路径和后端命名，改为论文级实现别名与功能说明。
  - `main.pdf` generated successfully, 108 pages.
- Validation:
  - 两轮只读 Agent 审查完成；最终无 P1/P2/P3 阻断问题。
  - `git diff --check -- thesis/chapters/appendix.tex` passed.
  - 内部工程命名、文件路径、provenance leak 与后台命名扫描为 0 命中。
  - `thesis/main.log` 无 undefined refs/cits、rerun warning、LaTeX Error 或 Font Warning。
  - `sec:app-kv-modes`、`sec:app-invtau-diagnostic`、`sec:app-triton-variants` 与 `tab:app-7b-kl-mse` 均在 `main.aux` 中存在。
- Risks / follow-ups:
  - 本轮只做内部命名清理，不压缩 A.7/A.8/A.10-A.13/A.17 等历史/系统补充材料。
  - 后续 M4 应进入机制与系统补充重排，优先处理体量压缩和 A.14/A.16 合并。
- Commit: <pending; planned `docs(appendix): remove internal engineering identifiers`>
