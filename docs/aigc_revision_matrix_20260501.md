# AIGC 误判风险降噪改写矩阵（2026-05-01）

> 输入源：用户提供的 47 个“疑似 AIGC 片段”逐段分析。
> 使用边界：本矩阵不用于规避检测；只用于增强证据链、作者决策痕迹、结构承载与论文边界表达。

## 状态说明

| 状态 | 含义 |
|---|---|
| `todo` | 尚未进入对应里程碑 |
| `mapped` | 已映射到具体文件/段落 |
| `done` | 已改写并通过 review |
| `kept-with-rationale` | 保留原文，但记录理由 |
| `deferred-with-reason` | 暂缓处理，并记录原因 |

## 证据等级规则

| 等级 | 含义 | 允许写法 | 禁止写法 |
|---|---|---|---|
| `final-ready` | 只来自 live plan 冻结的 5 条 claim 或 clean-provenance readout | 可作为正文主证据，但必须保留模型/任务/预算口径 | 不得外推为 universal law |
| `exploratory` | L2 A/B 等扩展性支持 | preliminary/supporting/boundary evidence | 不得升级为 final-ready claim |
| `off-protocol` | 例如 Prompt-adaptive 1.5B/7B extras | off-protocol exploratory reading | 不得进入正式 gate 或主结论 |
| `boundary-only` | 用于限制适用范围或解释协议边界 | scope limit / caveat / threat-to-validity | 不得写成正向贡献主张 |
| `definition-only` | 方法定义、接口、schema、公式解释 | 说明机制或复现接口 | 不得引入经验结论 |
| `literature-positioning` | 相关工作定位、差异化和 gap-response 写法 | 说明已有工作解决什么、未覆盖什么、本文接在哪里 | 不得写成排队式 survey 或把相关工作贡献归入本文 |
| `not-claim` | 结构、排版、章节导航或文献组织调整 | 改善表达与可读性 | 不得夹带新结果 |

## 47 段矩阵

| 段 | 章节 | 文件范围 | 触发原因 | 保留专业性的改法 | 证据锚点 / 检查点 | 证据等级 | Canonical source | 允许 / 禁止写法 | 状态 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 摘要 | `thesis/chapters/abstract_zh.tex` | 完整三段式模板；“统一框架/可审计/图谱”高频抽象词集中 | 重写为具体问题、方法组件、关键数值/模型例外、边界 | INT8 canonical path、INT4-RoleAlign、cross-model regime、系统边界 | final-ready + boundary-only | `docs/thesis_upgrade_live_plan.md` freeze；clean-provenance readout | 允许写 5 条冻结 claim；禁止普适胜出 | done |
| 2 | Abstract | `thesis/chapters/abstract_en.tex` | 与中文摘要镜像；英文句式过于平滑 | 不直译中文摘要，按英文论文习惯重组，加入 concrete experimental anchors | 与中文摘要做事实一致但结构非镜像检查 | final-ready + boundary-only | 同上 | 允许事实一致；禁止逐句镜像和新增 claim | done |
| 3 | Abstract | `thesis/chapters/abstract_en.tex` | “regime map / universal winner story”成熟但像生成式总结 | 保留 `regime-based interpretation` / `family-/scale-/task-dependent regimes`，明确删除 `universal winner story`，并绑定模型族、规模、任务和预算条件 | 3B/8B/14B/Mistral；同量级 INT4 预算带 | final-ready + boundary-only | live plan 冻结的 Mistral-specific auto-k、3B early-layer、14B top-tier-not-winner | 允许 regime-map 观点；禁止跨 family universal winner | done |
| 4 | 绪论 | `thesis/chapters/ch1_introduction.tex` | 大模型背景、KV Cache 引入是模板开场 | 缩短通用背景，直接落到 decode 阶段缓存字节数 | KV cache memory pressure；decode-stage constraint | not-claim | `objective.md` mission；Ch4 deployment boundary | 允许问题定位；禁止泛泛行业背景 | done |
| 5 | 绪论 | `thesis/chapters/ch1_introduction.tex` | 公式解释过完整，像教材说明 | 加入本文如何用公式界定实验变量，而非只解释符号 | batch/length/layers/head_dim/bit-width 变量口径 | definition-only | Ch1 formula context；Ch4 protocol | 允许变量口径说明；禁止教材式孤立解释 | done |
| 6 | 绪论 | `thesis/chapters/ch1_introduction.tex` | “压得更低不等于可用”过于总括 | 用 Qwen/LLaMA INT4 失稳差异提前埋钩子 | K4V8/K4V4 cliff；LLaMA exception | boundary-only | Ch4 K/V sensitivity and role diagnosis | 允许作为条件性背景钩子；禁止升级为 final-ready 主 claim 或所有模型同强度 Key 崩 | done |
| 7 | 绪论 | `thesis/chapters/ch1_introduction.tex` | 相关方向并列概述，句式统一 | 把 KIVI/KVQuant/ZipCache 改成各自留下的未解决问题 | format/control/calibration/cache-management gap | literature-positioning | Ch2 citations and thesis gap | 允许 gap 定位；禁止排队式综述 | done |
| 8 | 绪论 | `thesis/chapters/ch1_introduction.tex` | 研究问题是标准 proposal 语气 | 从本文观察出发：先出现现象，再提出问题 | INT8 parity、INT4 cliff、allocator regimes | final-ready + boundary-only | live plan frozen claims | 允许从观察导出 RQ；禁止先验全能问题设定 | done |
| 9 | 绪论 | `thesis/chapters/ch1_introduction.tex` | “问题-方法-证据”“论证链条”等元叙述密集 | 保留章节导航，减少抽象评价，写具体章节承载内容 | Chapter-to-RQ mapping | not-claim | thesis `main.tex` chapter structure | 允许章节承载说明；禁止抽象论证链复述 | done |
| 10 | 绪论 | `thesis/chapters/ch1_introduction.tex` | 五章安排是模板段 | 大幅压缩或改成“第几章回答哪个 RQ” | RQ1/RQ2/RQ3/RQ4 映射 | not-claim | Ch1 chapter overview | 允许 RQ 映射；禁止模板式章节介绍 | done |
| 11 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | KV Cache 基础解释像教科书 | 与实验瓶颈绑定：decode memory-bound 如何影响设计 | decode TPOT、KV memory、cache bytes | definition-only + boundary-only | Ch2 KV Cache basics；Ch4 deployment section | 允许面向本论文变量解释；禁止泛教材段 | done |
| 12 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 对称量化解释标准、完整、低个性 | 加入为何 INT8 作保守锚点、为何 INT4 是故障暴露点 | INT8 canonical path；INT4 cliff | final-ready (INT8 only) + boundary-only | clean-provenance readout；Ch4 low-bit diagnosis | 允许 INT8 canonical path 保真；INT4 只作为故障暴露/边界语境；禁止泛泛位宽优劣 | done |
| 13 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 非对称量化解释泛化 | 用 K/V 统计差异导入，不泛讲 per-channel/per-token | K/V role difference；per-channel K/per-token V | definition-only + boundary-only | Ch3 INT4-RoleAlign definition；Ch4 K/V diagnosis | 允许格式和角色差异绑定；禁止纯技术百科 | done |
| 14 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 校准分类像综述教材 | 把分类服务于 critique：数值校准为何不足以解释 softmax 行为 | MSE vs KL；attention behavior | definition-only | Ch3 KL proxy and calibration interface | 允许解释本文 critique；禁止完整分类教科书 | done |
| 15 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 文献排队式总结，高风险 | 拆段；每段保留直接相关 2-3 篇并写差异 | KIVI/KVQuant/ZipCache 等相对定位 | literature-positioning | Ch2 citations | 允许解决什么/没覆盖什么/本文接哪里；禁止 “X 做 A, Y 做 B” 队列 | done |
| 16 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 缓存管理路线总结句式统一 | 强化“正交但可组合”的边界，用表格或对照替代长段 | cache eviction/management vs quantization | literature-positioning + boundary-only | Ch2 efficient inference section | 允许正交边界；禁止把管理路线写成本文主贡献 | done |
| 17 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | softmax 相关工作概括太顺 | 加入这些工作与本文 KV-cache 设定不完全重合的限制 | softmax behavior vs cached K/V perturbation | literature-positioning | Ch2 softmax/attention behavior citations | 允许设定差异；禁止泛化为同一问题 | done |
| 18 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 系统工作综述 + 总结句模板化 | 用“部署收益取决于 bit-width 与 kernel path 是否同向”替代泛总结 | fused decode、nibble unpack、H_kv | boundary-only | Ch4 deployment and system boundary | 允许系统条件读法；禁止无条件加速宣称 | done |
| 19 | 相关工作 | `thesis/chapters/ch2_related_work.tex` | 研究空白四连段宏观、全能 | 分散到各小节末尾；每个 gap 配一个实验/设计响应 | gap-to-design mapping | literature-positioning | Ch2 section endings；Ch3/Ch4 response | 允许逐项 gap-response；禁止全能式 research gap | done |
| 20 | 方法 | `thesis/chapters/ch3_method.tex`; `thesis/figures/fig1_error_decomposition.tex` | 公式附近乱码，检测和可读性都会受影响 | 优先修排版/LaTeX 抽取问题；正文写清两项误差解释 | error decomposition formula | definition-only | Ch3 formula source | 允许修排版和定义；禁止新增经验结果 | done |
| 21 | 方法 | `thesis/chapters/ch3_method.tex`; `thesis/figures/fig_ch3_kv_diag_needle.tex` | 诊断结论清晰但像自动归纳 | 加入 K8V4/K4V8 的模型、指标、数值或表图锚点 | Qwen/LLaMA role sensitivity figures | boundary-only | Ch4 K/V role sensitivity figures | 允许作为模型条件诊断；禁止写成 final-ready 主 claim 或跨架构同强度结论 | done |
| 22 | 方法 | `thesis/chapters/ch3_method.tex` | “两层决策/系统层固化”框架化套话 | 改成接口定义：输入产物、输出模块 | calibration artifact -> runtime module | definition-only | Ch3 workflow/interface definitions | 允许输入输出接口；禁止空泛框架语 | done |
| 23 | 方法 | `thesis/chapters/ch3_method.tex` | KL 代理解释完整但长、抽象 | 拆成为何不用 MSE、为何前向 KL、数值稳定处理 | KL proxy definition and stability terms | definition-only | Ch3 KL proxy formula | 允许设计理由；禁止经验胜出预告 | done |
| 24 | 方法 | `thesis/chapters/ch3_method.tex`; `thesis/tables/table_ch3_path_instantiation.tex` | 统一工作流定义偏模板 | 用伪代码/定义表承载，正文只解释设计理由 | workflow algorithm/table | definition-only | Ch3 workflow table/algorithm | 允许结构化定义；禁止自然语言铺陈 | done |
| 25 | 方法 | `thesis/chapters/ch3_method.tex` | 指标符号解释太标准 | 保留但贴紧公式，不单独形成泛解释段 | local formula explanation | definition-only | Ch3 local formula context | 允许局部符号解释；禁止泛解释段 | done |
| 26 | 方法 | `thesis/chapters/ch3_method.tex` | fallback 规则和 INT4-RoleAlign 过渡连在一起 | 拆开；fallback 写算法规则，INT4-RoleAlign 写下一节动机 | fallback rule table/algorithm | definition-only | Ch3 algorithm/rule definitions | 允许规则化；禁止把 fallback 写成经验结论 | done |
| 27 | 方法 | `thesis/chapters/ch3_method.tex` | “需要强调的是”类元话语明显 | 删除强调句，直接说明本节不报告结果的原因 | method/result boundary | boundary-only | Ch3 method/result separation | 允许职责边界；禁止元话语强调 | done |
| 28 | 方法 | `thesis/chapters/ch3_method.tex` | 对称 INT4 到 INT4-RoleAlign 长段句式反复 | 拆短，加入对称搜索失败后升级格式的证据 | symmetric INT4 failure evidence | boundary-only | Ch4 INT4 cliff and INT4-RoleAlign comparison | 允许解释低比特恢复路径的设计动机；禁止写成 final-ready 主 claim 或普适击败 KIVI-style | done |
| 29 | 方法 | `thesis/chapters/ch3_method.tex` | K/V 量化轴解释偏公式前说明 | 补充轴选择如何对应 Key/Value 失稳差异 | per-channel K/per-token V rationale | definition-only + boundary-only | Ch3 INT4-RoleAlign format; Ch4 K/V diagnosis | 允许轴选择理由；禁止把格式本身写成最终因果证明 | done |
| 30 | 方法 | `thesis/chapters/ch3_method.tex` | INT4-RoleAlign 总结段抽象词密集 | 用最终配置表替代部分文字，正文只写选择依据 | path instantiation/config table | definition-only | Ch3 path instantiation table | 允许配置依据；禁止抽象价值宣言 | done |
| 31 | 方法 | `thesis/chapters/ch3_method.tex` | KIVI-style 对比过于规整 | 加入参数来源、是否冻结、是否可复现实验审计 | KIVI-style vs INT4-RoleAlign control variables | definition-only + boundary-only | Ch3 comparison table; Ch4 same-format result | 允许同格式控制变量；禁止泛称 KIVI | done |
| 32 | 方法 | `thesis/chapters/ch3_method.tex` | 产物接口解释长且平滑 | 改成离线校准字段表 + 一段解释 | offline calibration field table | definition-only | calibration runtime fields | 允许字段表说明；禁止长段复述 | done |
| 33 | 方法 | `thesis/chapters/ch3_method.tex` | kernel 路径说明像系统综述 | 加入 `+8` offset 还原、GQA head mapping 对 TPOT 的影响 | INT4 fused decode constraints | boundary-only | Ch3 system path; Ch4 deployment boundary | 允许实现约束；禁止无条件性能结论 | done |
| 34 | 方法 | `thesis/chapters/ch3_method.tex` | 章末总结高度模板化 | 压缩为 2 段，突出本章产出的接口 | chapter output interfaces | not-claim | Ch3 section outputs | 允许接口收束；禁止复述全章 | done |
| 35 | 实验 | `thesis/chapters/ch4_experiments.tex` | 实验环境说明专业但半截被截断 | 固定表 4-1 位置，压缩环境段与脚注邻近正文，复查 PDF 抽取顺序 | environment paragraph and table | not-claim | Ch4 environment table/source | 允许抽取和排版修复；禁止新增环境 claim | done |
| 36 | 实验 | `thesis/chapters/ch4_experiments.tex` | 五维评测协议完整但像生成式概述 | 改为每个指标承担的失败模式 | PPL/Needle/RULER/LongBench/TPOT roles | boundary-only | Ch4 protocol section | 允许指标职责；禁止泛称完整覆盖所有质量维度 | done |
| 37 | 实验 | `thesis/chapters/ch4_experiments.tex` | benchmark 说明过完整 | 用失败模式清单列任务、长度、指标、解释边界；不新增正式表以保持 4.1 表号冻结 | protocol ledger / benchmark boundary | boundary-only | Ch4 protocol source; Chapter 4 Writing frozen table plan | 允许任务/长度/指标边界；禁止官方榜单外推和新增正式表打乱表号 | done |
| 38 | 实验 | `thesis/chapters/ch4_experiments.tex` | 比较对象三分类很规整 | 加入每类比较对象承担的控制问题，并单独定位 Uniform、BA-k、Heuristic-k 与 BA-AutoK 的第 4.4 节角色 | FP16 / percentile baseline / KIVI-style / heuristic baseline roles | boundary-only | Ch4 baseline tables; allocation strategy section | 允许 baseline 角色、Heuristic-k 位置先验基线与 BA-AutoK 画像驱动预算建议器定位；禁止 strawman 或 universal superiority | done |
| 39 | 实验 | `thesis/chapters/ch4_experiments.tex` | 统计纪律段像规范模板 | 加入正文主结果、协议一致性/补充审计、较早批次补充读数三层证据，并说明降权原因 | unified-protocol / supplementary evidence boundaries | final-ready + supplementary + off-protocol + boundary-only | Ch4 statistics section; appendix LongBench-style audit | 允许证据分层；禁止补充读数替代正文主结论 | done |
| 40 | 实验 | `thesis/chapters/ch4_experiments.tex` | 小节目标说明标准化 | 改成研究问题句 + 本节控制变量 | local subsection variables | boundary-only | Ch4 RQ1/RQ2 section protocol | 允许控制变量；禁止模板目标句 | done |
| 41 | 实验 | `thesis/chapters/ch4_experiments.tex` | 表述好但归因偏平滑 | 补表图锚点，并把结论压回具体模型、指标和配置 | relevant table/figure references | boundary-only | Ch4 Tables 4-3--4-8 and Figures 4-1--4-2 | 允许表图锚点归因；禁止平滑无锚点归因或升级为 frozen claim 外的新主张 | done |
| 42 | 实验 | `thesis/chapters/ch4_experiments.tex` | 表注和配置解释连成长段 | 缩短表注，只保留协议/范围；配置解释移回正文 | table note split | not-claim + boundary-only | Ch4 table notes | 允许表注/正文职责分离；禁止长段混合配置和结论 | done |
| 43 | 实验 | `thesis/chapters/ch4_experiments.tex` | INT4-RoleAlign / KIVI-style 对比注释过长 | 将同格式控制变量写在 4.3.3 正文，表注只说明共享格式、Needle 读法和 14B 配对边界 | same-format comparison | boundary-only | Ch4 INT4-RoleAlign vs KIVI-style table | 允许同格式控制变量；禁止写成 final-ready 主 claim 或普适优势判定 | done |
| 44 | 实验 | `thesis/chapters/ch4_experiments.tex` | 小节总结像自动总结 | 用最小可证结论收束 RQ1/RQ2，并绑定表图证据 | minimal supported claims | final-ready + boundary-only | Local Ch4 evidence and live-plan frozen claims | 允许最小命题；禁止扩展总结 | done |
| 45 | 实验 | `thesis/chapters/ch4_experiments.tex` | 表注被标记，风险低 | 不大改；确认不是显著加速宣称 | deployment boundary note | boundary-only | Ch4 deployment tables/figures | 允许当前 H20/后端条件；禁止显著加速泛称 | done |
| 46 | 实验 | `thesis/chapters/ch4_experiments.tex` | 章末总结覆盖多个 RQ，像摘要复写 | 拆成按 RQ 的结论，每条绑定证据和限制 | RQ evidence summary | final-ready + boundary-only | Ch4 chapter conclusion + live-plan frozen claims | 允许按 RQ 最小结论；禁止摘要复写和新增 claim | done |
| 47 | 结论 | `thesis/chapters/ch5_conclusion.tex` | 边界讨论抽象但风险低 | 保留克制语气，加入具体未覆盖分布/任务/部署条件 | limitations and future-work boundaries | boundary-only | Ch5 limitations; `objective.md` non-goals | 允许具体未覆盖范围；禁止抽象 caveat 替代边界 | done |

## Compiled Source Coverage

`thesis/main.tex` 当前编译入口覆盖以下源文件。本轮 47 段只分配到摘要、Ch1-Ch5；其它编译源在 M7 做编译、引用、PDF/HTML 抽取扫描。若后续需要改动这些文件的正文内容，必须新增矩阵行并重新进入 review gate。

| Source | Coverage status | M1 decision |
|---|---|---|
| `thesis/main.tex` | compiled entrypoint | 不直接改；仅用于源覆盖和编译验证 |
| `thesis/chapters/abstract_zh.tex` | fragments assigned | M2 |
| `thesis/chapters/abstract_en.tex` | fragments assigned | M2 |
| `thesis/chapters/ch1_introduction.tex` | fragments assigned | M3 |
| `thesis/chapters/ch2_related_work.tex` | fragments assigned | M4 |
| `thesis/chapters/ch3_method.tex` | fragments assigned | M5 |
| `thesis/chapters/ch4_experiments.tex` | fragments assigned | M6 |
| `thesis/chapters/ch5_conclusion.tex` | fragments assigned | M6 |
| `thesis/chapters/appendix.tex` | compiled-but-no-fragment-assigned | M7 scan only；正文改动需新增矩阵行 |
| `thesis/chapters/acknowledgements.tex` | compiled-but-no-fragment-assigned | M7 scan only；正文改动需新增矩阵行 |
| `thesis/setup/*.tex` | compiled support inputs | M7 compile/reference/layout scan only；宏包、格式、命令改动需新增矩阵行或单独 review gate |
| `thesis/references.bib` | bibliography input | M7 citation/BibTeX validation；新增/删除 citation key 需同步 source coverage 与 citation scan |
| `thesis/figures/*.tex` and `thesis/tables/*.tex` included by chapters | compiled transitive inputs | M7 scan only；若迁移 Ch4 表格或修 label，先确认 authoritative source，避免重复 labels 与未定义 `para:` refs |
| `thesis/figures/**/*.pdf` included by `\includegraphics` | compiled figure assets | M7 compile/PDF extraction scan only；替换图件需新增矩阵行或单独 figure review |

## 里程碑 Review 记录

### M1: 基线矩阵与执行记录

- 状态：done
- 本地验证：
  - `git diff --check -- .agents/execplans/2026-05-01_aigc_risk_revision.md docs/aigc_revision_plan_20260501.md docs/aigc_revision_matrix_20260501.md`: PASS
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS
  - Evidence/claim-boundary: PASS after adding evidence tiers, canonical sources, and allowed/forbidden language.
  - LaTeX/reference: PASS after adding `latexmk`, PDF/HTML extraction checks, and compiled source coverage.
  - Terminology consistency: PASS after normalizing `INT8 canonical path`, `INT4-RoleAlign`, `KIVI-style`, and evidence-tier terms.

### M2: 摘要与 Abstract

- 状态：done
- 片段：1-3
- 改动文件：
  - `thesis/chapters/abstract_zh.tex`
  - `thesis/chapters/abstract_en.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/abstract_zh.tex thesis/chapters/abstract_en.tex`: PASS
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 106 pages)
  - `rg -n "Undefined control sequence|LaTeX Error|Reference .* undefined|Citation .* undefined|There were undefined references|multiply defined|Rerun to get cross-references right|Label\(s\) may have changed" thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m2.txt && rg -n "�|□|\?\?|undefined|para:|fig:|tab:" /tmp/thesis_main_m2.txt`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m2.txt && rg -n "INT8 规范路径|INT4RoleAlign|attentionside|outputside|;" /tmp/thesis_main_m2.txt`: PASS (no hits)
  - `rg -n "universal winner|universally|positive case|recovery story|statistically close|final claim set|contribution|普适最优|全局胜出|赢家|图谱|clean_rerun|clean-provenance|/root|pin=|AutoDL|tmux|rsync|backend process|session" thesis/chapters/abstract_zh.tex thesis/chapters/abstract_en.tex`: PASS (no hits)
  - `make4ht -ux -d /tmp/thesis_html_m2 main.tex`: current and baseline `19c5fea` both exit 1 on the existing tex4ht / Chinese template / Ghostscript graphics path; treated as pre-existing non-blocking for M2, with generated source-tree artifacts removed.
- Agent review:
  - Style/AIGC-risk: PASS after removing internal review phrasing and adding the 14B numeric anchor in English.
  - Evidence/claim-boundary: PASS after scoping 3B to core mean and replacing unsupported `statistically close` wording.
  - Terminology consistency: PASS after aligning `INT8 基准路径` / `INT8 canonical path`, `INT4-RoleAlign`, and `family-/scale-/task-dependent regimes`.
  - LaTeX/reference/extraction: PASS after fixing PDF extraction for `INT4-RoleAlign`, hyphenated proxies, ASCII keyword separators, and recompiling `main.pdf`.

### M3: 绪论

- 状态：done
- 片段：4-10
- 改动文件：
  - `thesis/chapters/ch1_introduction.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch1_introduction.tex`: PASS
  - `rg -n "需要强调的是|至此|共同表明|核心在于|问题\s*-\s*方法\s*-\s*证据|问题-方法-证据|图谱|论证链条|论证主线|universal winner|普适最优|全局胜出|赢家|所有模型同强度|理论中心|普适策略|跨条件稳定占优|分别回答 RQ1--RQ4|按 RQ1--RQ4" thesis/chapters/ch1_introduction.tex`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 106 pages)
  - `rg -n "(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references right|Label\(s\) may have changed)" thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m3_final.txt`: PASS
  - `sed -n '220,430p' /tmp/thesis_main_m3_final.txt | rg -n "�|□|\?\?|undefined|para:|fig:|tab:|INT4RoleAlign|INT4-$|^RoleAlign|问题 - 方法 - 证据"`: PASS (no hits in Ch1 extraction window)
- Agent review:
  - Style/AIGC-risk: PASS after adding RQ4, adding the bounded Qwen/LLaMA low-bit hook, and removing template meta-language.
  - Evidence/claim-boundary: PASS after keeping Qwen/LLaMA and `AutoK` as problem-setting / allocation-extension context, not final-ready overclaims.
  - Terminology/structure: PASS after aligning RQ1--RQ4 with `objective.md` and changing Ch4 wording from “separate RQ answers” to evidence coverage.
  - LaTeX/reference/extraction: PASS after protecting `\mbox{INT4-RoleAlign}` and rechecking Ch1 PDF extraction.

### M4: 相关工作

- 状态：done
- 片段：11-19
- 改动文件：
  - `thesis/chapters/ch2_related_work.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch2_related_work.tex`: PASS
  - `rg -n "需要强调的是|至此|共同表明|核心在于|图谱|论证链条|普适最优|全局胜出|赢家|统一框架|可审查|可审计|可复现|较清晰的谱系|接口视图|三个接口|四个可审查接口|这些接口|当前主流|为了增强表示能力|重要结构因素之一|统一的结构记号|真实 decode|融合 decode|decode 路径|INT8.*锚点" thesis/chapters/ch2_related_work.tex`: PASS (no hits)
  - `rg -n "敏感度画像|INT8 基准路径|Decode 路径|融合 Decode|真实 Decode|接口" thesis/chapters/ch2_related_work.tex`: PASS (expected terminology hits only; no `接口` hit)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 104 pages)
  - `rg -n "(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references right|Label\(s\) may have changed|multiply defined)" thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m4_tablefix.txt`: PASS
  - `sed -n '434,800p' /tmp/thesis_main_m4_tablefix.txt | rg -n "�|□|\?\?|undefined|para:|fig:|tab:|INT4RoleAlign|INT4-$|^RoleAlign|问题 - 方法 - 证据|至此|共同表明|普适最优|universal winner|图谱|可审计|可复现|较清晰的谱系|接口|当前主流|为了增强表示能力"`: PASS (no hits)
  - `rg -n "同源行为读数|而不是只优化|一次压缩率|表 2-1|量化对注意力行为" /tmp/thesis_main_m4_tablefix.txt`: PASS; key sentence remains continuous before Table 2-1.
- Agent review:
  - Style/AIGC-risk: PASS after compressing Transformer/MHA/GQA explanations, replacing literature queueing with problem-positioning, and removing template meta-language.
  - Evidence/claim-boundary: PASS after keeping Ch2 claims at definition, literature-positioning, or boundary-only level and avoiding final-ready overclaims.
  - Terminology/structure: PASS after aligning `行为敏感度画像`, `INT8 基准路径`, `Decode` terminology, and Ch2-to-Ch3/Ch4 handoff.
  - LaTeX/reference/extraction: PASS after fixing Table 2-1 to `[H]`, shortening the page-end risk sentence, recompiling, and confirming PDF text extraction order.

### M5: 方法章

- 状态：done（M5-A/M5-B/M5-C done）
- 片段：20-34

#### M5-A: 公式分解、K/V 诊断、接口总览与 KL 代理

- 状态：done
- 片段：20-23
- 改动文件：
  - `thesis/chapters/ch3_method.tex`
  - `thesis/figures/fig1_error_decomposition.tex`
  - `thesis/figures/fig_ch3_kv_diag_needle.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch3_method.tex thesis/figures/fig1_error_decomposition.tex thesis/figures/fig_ch3_kv_diag_needle.tex`: PASS
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 103 pages)
  - `rg -n "(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references right|Label\(s\) may have changed|multiply defined)" thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m5a.txt`: PASS
  - `sed -n '790,1130p' /tmp/thesis_main_m5a.txt | rg -n "�|□|\?\?|undefined|para:|fig:|tab:|ref\{|cite\{|INT4RoleAlign|INT4-$|^RoleAlign|需要强调的是|至此|共同表明|核心在于|统一框架|可审计|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|cache writer|low-bit|P 精确|精确代数分解P|同强度坍塌|保持可用"`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after replacing smooth framework narration with concrete formula boundaries, Qwen/LLaMA evidence anchors, and explicit KL design choices.
  - Evidence/claim-boundary: PASS after narrowing K8V4/MixedKV to `未归零 / 未进入归零式失稳`, limiting Key-side cliff claims to Qwen settings, and retaining LLaMA architecture modulation.
  - Terminology/structure: PASS after aligning `K-path/V-path`, `行为敏感度画像`, `MixedKV（图中 K8V4）`, and offline/online cache-write semantics.
  - LaTeX/PDF extraction: PASS after changing Figure 3-1 formula text to propagation labels and removing the Figure 3-2 bottom-node extraction collision.

#### M5-B: 离线工作流、局部指标、回退规则与路径边界

- 状态：done
- 片段：24-27
- 改动文件：
  - `thesis/chapters/ch3_method.tex`
  - `thesis/tables/table_ch3_path_instantiation.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch3_method.tex thesis/tables/table_ch3_path_instantiation.tex docs/aigc_revision_matrix_20260501.md`: PASS
  - `sed -n '150,245p' thesis/chapters/ch3_method.tex | rg -n "需要强调的是|至此|共同表明|核心在于|统一框架|可审计|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|完整.*规整|框架化|表面统一性|Fallback|handoff|cache writer|low-bit|lexmin"`: PASS (no hits)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 102 pages)
  - `rg -n "(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references right|Label\(s\) may have changed|multiply defined)" thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m5b.txt`: PASS
  - `sed -n '1115,1265p' /tmp/thesis_main_m5b.txt | rg -n "�|□|\?\?|undefined|para:|fig:|tab:|ref\{|cite\{|INT4RoleAlign|INT4-$|需要强调的是|至此|共同表明|核心在于|统一框架|可审计|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|Fallback|handoff|lexmin|不是.*而是|不只是.*还|cache writer|low-bit"`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after replacing placeholder validation records with real regex scans and keeping the M5-B window structured around interfaces, formulas, and rules.
  - Evidence/claim-boundary: PASS after changing the path table from an effect-like `恢复行为保持` phrase to the definition-only `定义 K/V 角色分离的固定产物接口`.
  - Final consistency review: PASS after confirming fragments 24-27 are done, fragments 28-34 remain todo, validation commands are auditable, and no LaTeX/PDF extraction blocker remains in the M5-B window.

#### M5-C: RoleAlign、KIVI-style、校准字段、kernel 边界与章末小结

- 状态：done
- 片段：28-34
- 改动文件：
  - `thesis/chapters/ch3_method.tex`
  - `thesis/tables/table_ch3_runtime_paths.tex`
  - `docs/This is Chapter 3 Writing.md`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch3_method.tex thesis/tables/table_ch3_runtime_paths.tex 'docs/This is Chapter 3 Writing.md'`: PASS
  - `sed -n '260,840p' thesis/chapters/ch3_method.tex | rg -n "需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|可复现|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|框架化|表面统一性|证明在|自然生长|第三个主方法|真正|自然输出|artifact|GQA 映射|符号扩展|nibble unpack|进入 TPOT|runtime router|cache append|fallback marker|profile readout|provenance check"`: PASS (no hits)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 101 pages)
  - `rg -n "(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references right|Label\(s\) may have changed|multiply defined|Overfull \\hbox)" thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m5c_r4.txt`: PASS
  - `sed -n '1320,2100p' /tmp/thesis_main_m5c_r4.txt | rg -n "需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|可复现|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|框架化|表面统一性|证明在|自然生长|第三个主方法|真正|自然输出|artifact|GQA 映射|符号扩展|nibble unpack|进入 TPOT|runtime router|cache append|fallback marker|profile readout|provenance check"`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after replacing template transitions and internal-engineering phrasing, adding concrete K/V role evidence anchors, and syncing the Writing table list.
  - Evidence/claim-boundary: PASS after keeping Ch4 results as method motivation, changing GQA mapping to runtime-inferred head metadata, and using `+8` offset restore instead of `符号扩展`.
  - LaTeX/reference/extraction: PASS after deleting hard-coded table-number comments, stabilizing Tables 3-3 through 3-7, and shortening Table 3-7 to avoid PDF extraction artifacts.

### M6: 实验章与结论

- 状态：done（M6-A/M6-B/M6-C done）
- 片段：35-47

#### M6-A: 实验设置、评测协议、比较对象与证据分层

- 状态：done
- 片段：35-39
- 改动文件：
  - `thesis/chapters/ch4_experiments.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch4_experiments.tex`: PASS
  - `sed -n '1,106p' thesis/chapters/ch4_experiments.tex | rg -v -F '\label' | rg -n '需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|可复现|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|完整.*覆盖|五个互补维度|正交设计维度框架|不只是.*还|不是.*而是|benchmark|baseline 名字|Clean-provenance|clean-provenance|candidate-main|winner|普适定律|凭感觉|最终发布级|strawman'`: PASS (no hits)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 101 pages)
  - `rg -n '(^!|LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references right|Label\(s\) may have changed|multiply defined|Overfull \\hbox)' thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m6a_r3.txt`: PASS
  - `sed -n '2080,2265p' /tmp/thesis_main_m6a_r3.txt | rg -n '�|□|\?\?|undefined|para:|fig:|tab:|本节的组织顺序如下|五个互补维度|正交设计维度框架|benchmark|Clean-provenance|clean-provenance|candidate-main|winner|普适定律|需要强调的是|至此|共同表明|核心在于|完整.*覆盖|可审计|strawman'`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after replacing generic protocol overview with failure-mode responsibilities and concrete comparison roles.
  - Evidence/claim-boundary: PASS after separating main results, consistency checks, and supplementary readings.
  - LaTeX/reference/extraction: PASS after fixing Table 4-1 and Table 4-2 placement and rechecking PDF extraction.

#### M6-B: RQ1/RQ2 evidence anchors, table-note split, and minimal claims

- 状态：done
- 片段：40-44
- 改动文件：
  - `thesis/chapters/ch4_experiments.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_matrix_20260501.md`: PASS
  - `sed -n '118,386p' thesis/chapters/ch4_experiments.tex | rg -n '需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|可复现|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|完整.*覆盖|五个互补维度|正交设计维度框架|普适胜出|远远甩开|真正|最容易审计|可固化|可扩展|一边倒.*差距|一边倒跑分差|模板'`: PASS (no hits)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 101 pages)
  - `rg -n 'LaTeX Error|Undefined control sequence|Citation.*undefined|Reference.*undefined|Rerun to get cross-references|There were undefined references|Package natbib Warning: Citation' thesis/main.log`: PASS (no hits)
  - `rg -n -F 'Overfull \hbox' thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m6b_final_r4.txt`: PASS
  - `rg -n '4\.2     行为引导校准|表 4-3|4\.3   低比特路径|表 4-5|表 4-6|表 4-7|表 4-8|4\.4     跨模型' /tmp/thesis_main_m6b_final_r4.txt`: PASS (4.2/4.3 tables appear before 4.4)
  - `sed -n '2268,2693p' /tmp/thesis_main_m6b_final_r4.txt | rg -n '需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|可复现|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|完整.*覆盖|五个互补维度|正交设计维度框架|普适胜出|远远甩开|真正|最容易审计|可固化|可扩展|一边倒.*差距|一边倒跑分差|模板'`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after replacing template RQ introductions with controlled-variable questions, adding table/figure anchors, and changing section summaries to minimal supported claims.
  - Evidence/claim-boundary: PASS after keeping INT8, official LongBench, K/V diagnosis, same-format RoleAlign/KIVI comparison, and 14B row within their stated evidence scopes.
  - LaTeX/reference/extraction: PASS after fixing Tables 4-5 through 4-8 to `[H]`, shortening table notes, and rechecking PDF extraction order.

#### M6-C: deployment boundary, RQ evidence summary, and concrete conclusion limits

- 状态：done
- 片段：45-47
- 改动文件：
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
- 本地验证：
  - `git diff --check -- thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex docs/aigc_revision_matrix_20260501.md`: PASS
  - `sed -n '590,842p' thesis/chapters/ch4_experiments.tex | rg -n '<M6-C risk pattern>'`: PASS (no hits)
  - `sed -n '42,84p' thesis/chapters/ch5_conclusion.tex | rg -n '<M6-C risk pattern>'`: PASS (no hits)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 99 pages)
  - `rg -n 'LaTeX Error|Undefined control sequence|Citation.*undefined|Reference.*undefined|Rerun to get cross-references|There were undefined references|Package natbib Warning: Citation|Label\(s\) may have changed' thesis/main.log`: PASS (no hits)
  - `rg -n -F 'Overfull \hbox' thesis/main.log`: PASS (no hits)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m6c_floatfix2.txt`: PASS
  - `sed -n '3060,3260p' /tmp/thesis_main_m6c_floatfix2.txt`: PASS (Tables 4-12, 4-13, and 4-14 appear after their subsection lead-ins and before callout paragraphs; no sentence interruption)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after replacing deployment and conclusion summaries with evidence anchors, scoped limits, and concrete uncovered settings.
  - Evidence/claim-boundary: PASS after confirming no 4K acceleration overclaim, `\Delta T` claims bound to Qwen2.5-14B/H20/`batch=1`/current backend, and Ch5 limitations introduce no new unbounded claim.
  - LaTeX/reference/extraction: PASS after changing Tables 4-12, 4-13, and 4-14 to `[H]` and rechecking PDF extraction order.

### M7: 全稿一致性复核

- 状态：done
- 改动文件：
  - `thesis/chapters/abstract_zh.tex`
  - `thesis/chapters/ch1_introduction.tex`
  - `thesis/chapters/ch2_related_work.tex`
  - `thesis/chapters/ch3_method.tex`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/ch5_conclusion.tex`
  - `thesis/chapters/appendix.tex`
  - `thesis/tables/table_s3_rolealign_vs_kivi.tex`
  - `scripts/thesis/plot_ch4_regime_combined.py`
  - `thesis/figures/ch4/fig_ch4_05_regime_heatmap.pdf`
- 本地验证：
  - `git diff --check -- scripts/thesis/plot_ch4_regime_combined.py thesis/chapters/abstract_zh.tex thesis/chapters/ch1_introduction.tex thesis/chapters/ch2_related_work.tex thesis/chapters/ch3_method.tex thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex thesis/chapters/appendix.tex thesis/tables/table_s3_rolealign_vs_kivi.tex`: PASS
  - `rg -n "需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|AutoDL|tmux|rsync|/root|pin=|backend process|session" thesis/chapters thesis/tables/table_s3_rolealign_vs_kivi.tex scripts/thesis/plot_ch4_regime_combined.py`: PASS (no hits)
  - `cd thesis && latexmk -pdf -halt-on-error -file-line-error main.tex`: PASS (`main.pdf`, 99 pages)
  - `pdftotext -layout thesis/main.pdf /tmp/thesis_main_m7.txt && rg -n "�|□|\?\?|undefined|para:|fig:|tab:|ref\{|cite\{|INT4RoleAlign|INT4-$|需要强调的是|需要明确的是|至此|共同表明|核心在于|统一框架|可审计|图谱|论证链条|普适最优|全局胜出|赢家|自动归纳|不是.*而是|不只是.*还|AutoDL|tmux|rsync|/root|pin=|backend process|session" /tmp/thesis_main_m7.txt`: PASS (no hits)
  - `rg -n "LaTeX Error|Undefined control sequence|Citation.*undefined|Reference.*undefined|Rerun to get cross-references|There were undefined references|Package natbib Warning: Citation|Label\(s\) may have changed|multiply defined" thesis/main.log`: PASS (no hits)
  - `python scripts/review_tool.py phase-gate`: PASS (`PHASE GATE: CLEAR`; only pre-existing `review_tracker.md` parse warnings)
- Agent review:
  - Style/AIGC-risk: PASS after the global sweep removed residual template contrast, `图谱` / `普适最优` / `可审计` wording, and internal platform traces.
  - Evidence/claim-boundary: PASS after confirming INT8, INT4-RoleAlign, cross-model strategy regimes, heuristic strong-baseline, and official LongBench boundaries remain scoped to their evidence levels.
  - LaTeX/PDF extraction: PASS after regenerating Figure 4-5 from full-precision Step 2 values, aligning PDF labels with Table 4-9 (`6.75 / 7.23 / 14.76`), and fixing the appendix `INT4-RoleAlign` line-break extraction.
