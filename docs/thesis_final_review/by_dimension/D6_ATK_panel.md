# D6 攻击性答辩模拟 — 华南理工大学本科毕业答辩委员会视角

> **审查者**：华工工科资深教授（30 年本科毕设评阅经验）
>
> **审查日期**：2026-04-17
>
> **立场**：最严厉答辩委员（adversarial），专挑 AI 辅助写作痕迹、贡献虚胖、数据失控等"本科毕设常见高危点"，目的是让论文真正能扛住答辩现场 15 分钟连珠炮式追问。
>
> **评分标准**：本科生毕业设计（论文）评分标准（工科、理科类专业），见 `/tmp/thesis_spec_fujian_3.txt`。
>
> **论文版本**：`thesis/main.pdf`（114 页），`thesis/chapters/*.tex` 全部最新。

---

## A. 最严厉攻击 Top-20

| ID | 维度 | 问题（当堂质问） | 论文痛点 file:line | 难度 | 应对建议 |
|----|------|----------------|------------------|------|---------|
| **A01** | 创新性 | INT4-RoleAlign 明确写了"与 KIVI 独立提出的格式一致"——既然格式是一样的，你的真贡献到底是什么？只换了一个 percentile 搜索就能算独立贡献吗？ | `abstract_zh.tex:28-29`；`ch1_introduction.tex:174-177`；`ch5_conclusion.tex:34-35`；`ch3_method.tex:625-629` | **H** | 承认格式沿用 KIVI，强调真贡献是"通过 attention-KL 诊断视角发现 Key 主导失效→推导出该格式的合理性"，即"提供了该格式的行为层面解释+离线校准参数化"。诚实回答比辩解更能打动评委。 |
| **A02** | 工作量 | 14B 只跑了 1 seed，RULER 只测 4K/8K/16K（32K 未测）——请问这能否称为"完整的四模型验证"？为什么摘要敢写"四模型保持 Needle 100%"？ | `ch4_experiments.tex:1325`（`1.5B/7B/8B 为 3 seeds，14B 为 1 seed`）；`ch4_experiments.tex:1375-1377`（14B RULER 4K--16K，32K 因显存限制未测）；`abstract_zh.tex:20, 32-33`；`ch5_conclusion.tex:39-40` | **H** | 必须如实披露 14B 限 1 seed、32K 未测，强调 14B 作用是"外部效度锚点"而非完整 validation；承诺补跑或已在第四章边界声明中披露。切勿说"已完整验证"。 |
| **A03** | 实验严谨性 | **摘要 7B PPL 退化写 "6.0%"，主表 `tab:rolealign-results` 写 "+6.1%"，两处数字都打不齐，这叫严谨吗？** | `abstract_zh.tex:31`（"7B: 6.0%"）；`abstract_en.tex:39`（"7B: 6.0%"）；`ch4_experiments.tex:1353`（"\textbf{+6.1%}"）；`ch5_conclusion.tex:38`（"7B: 6.0%"）；issues.md TR-0002 | **H** | 这是已知 CRITICAL（TR-0002 open），必须在正式提交前统一为 6.1%（从原始数据 7.58/7.14≈6.16% 计算得出）。当场承诺 24h 内修复。 |
| **A04** | 合规 | **`\keywordszh` / `\keywordsen` 各写了 6 个关键词，附件1《写作规范》明确要求 3--5 个，你是否审读过学校写作规范？** | `abstract_zh.tex:39`（6 个：大语言模型、键值缓存、量化、行为对齐校准、非对称量化、GQA 架构）；`abstract_en.tex:48-50`（6 个英文关键词对应）；issues.md TR-0003 | **H** | 同样是已知 CRITICAL，建议保留"大语言模型 / 键值缓存 / 行为对齐校准 / GQA"4 个，中英对齐。 |
| **A05** | 结论过强 | 你摘要写"PPL 退化随模型规模减弱（1.5B:13.7%, 7B:6.0%, 8B:2.4%）"暗示单调趋势，但 14B 退化 7.6% 明显打破单调性——**为什么摘要不披露这个反常？** | `abstract_zh.tex:31`（摘要只报 1.5B/7B/8B）；`ch4_experiments.tex:1362, 1371-1373`（14B: 7.6%）；`ch4_experiments.tex:1964-1972`（正文 §综合讨论"PPL 非单调现象"披露但摘要未披露） | **H** | 必须在摘要补充 14B 7.6% 或改措辞为"大致随规模减弱，14B 例外"。当前摘要措辞是 cherry-picking。 |
| **A06** | 创新性 | 你 claim 贡献一"校准目标有效性的 bit-width 与规模依赖"——但你自己第 163 行写"本贡献属于经验观察而非方法创新"，那这还能算"主要贡献"吗？ | `ch1_introduction.tex:151-163`（贡献一；最后一句"经验观察而非方法创新"） | **M** | 可答：作为科学性观察，揭示了 INT8/INT4 校准行为的定性差异，对未来校准设计有指导价值，因此作为 contribution 叙述合理。但应准备被追问"这是否算学术贡献"。 |
| **A07** | 实验严谨性 | K/V 消融实验的 PPL 表（`tab:kv-ablation-ppl`）只用单 seed（1234），你的理由是"贪心解码下 PPL 确定性"——但 `scripts/eval_ppl.py` 历史上有**静默 fallback bug** 把 asym 路径误走 INT8，你怎么证明这次单 seed 就没踩类似坑？ | `ch4_experiments.tex:999-1002`（单 seed 1234，引用确定性说明）；`ch5_conclusion.tex:80-89`（已自曝 EVL-037 型 fallback bug 导致早期 9.42 实为 INT8 结果） | **H** | 必须展示本次确认了 kv_mode 分支在 eval_ppl.py 中已修复；展示 details CSV 中记录的 kv_mode 一致性。论文已自爆同类 bug 的情况下，评委会刨根到底。 |
| **A08** | 可复现性 | 你的复现脚本在哪？`final_scripts/reproduce/` 目录不存在，`scripts/` 下一堆 `exp*.sh` 看起来是开发用脚本，一个新人拿你的论文复现你的数据需要几个小时？ | 项目根下 `ls final_scripts/reproduce/ → no reproduce dir`；`scripts/` 只有 `exp2_*`、`exp3_*`、`ablation_*` 等开发脚本散落 | **H** | 必须承认当前没有 user-facing "one-click reproduce" 脚本。承诺在最终提交前整理 `scripts/reproduce/ch4_main_table.sh`、`ch4_rolealign.sh`、`ch4_phase_boundary.sh` 三个入口，并在附录添加复现步骤。 |
| **A09** | 结论过强 | "Needle 与 PPL 解耦"你在 1.5B/7B/8B/14B 上都观察到了——但这是**同一个方法 INT4-RoleAlign** 的观察。你有没有在对称 INT4（灾难配置）上看到解耦？如果灾难方法 Needle 和 PPL 一起崩，那"解耦"就只是 RoleAlign 的特性而非普遍规律。 | `ch4_experiments.tex:437-445`（对称 int4_baseline/int4_ours/int4_fused 三个都是 PPL 崩+Needle 0%，并未"解耦"）；`ch4_experiments.tex:1711-1716`（解耦 claim 仅在 RoleAlign 下成立） | **H** | 应限定 claim 为"在 RoleAlign 配置下 Needle 与 PPL 对 INT4 量化噪声的敏感度不同"，避免暗示"解耦是 INT4 的通用规律"。 |
| **A08b** | 实验严谨性 | Needle 100% 实在太漂亮了——你有没有测过 adversarial cases（针被放在极高深度、needle 字面上与 haystack 相似、多 needle 干扰）？标准 Needle-in-a-Haystack 是偏易基准，100% 对 INT4 来说过于乐观。 | `ch4_experiments.tex:104-110`（只测 4K/8K/16K/32K × 20 depth levels，没有 adversarial/multi-needle） | **M** | 诚实回答：论文未做 adversarial 测试；MK-NIAH 2-key 是接近测试（ch4:1348 "100/100"），但未做完全对抗版本。承诺在边界声明补充。 |
| **A09b** | 格式合规 | 你第 5 章用了 `\chapter*` + `\setcounter{chapter}{5}` 手工制造"结论"章节，这是否符合华工论文模板要求？为什么不直接用 `\chapter{结论}`？ | `ch5_conclusion.tex:5-9`（`\chapter*{结论} / \addcontentsline / \setcounter{chapter}{5}`） | **L** | 应答：这是中国学位论文常见写法，"结论"不编号但计入目录。可向教师请教本校要求。 |
| **A10** | 工作量 | KIVI 对比方面——你论文 L825-846 自曝"未复现原文的 FP16 residual buffer + 分组 Scale 更新"，这意味着你的 KIVI baseline **不是 KIVI**，是一个简化版。用简化版对比自己的方法然后 claim "不劣于 KIVI" 合适吗？ | `ch4_experiments.tex:825-846`（自承实现差异）；`ch5_conclusion.tex:119-122`（局限声明）；`ch4_experiments.tex:2032-2035`（TTV-5 单实现威胁） | **H** | 必须坚持"比较的是 KIVI 核心量化轴策略"这一限定；不能 claim "击败 KIVI"。建议答辩时把这一限定作为主动澄清而非被动澄清。 |
| **A11** | 实验严谨性 | 表 `tab:kv-ablation-longbench` 中 K4V8 在 Qwen2.5-7B 上 LongBench 降到 0.80 而 1.5B 是 2.58、8B 反而涨到 8.92——这个 U 字形/反 U 字形曲线你怎么解释？单模型单指标的异常反转是否暗示实验有 bug？ | `ch4_experiments.tex:1070-1072`（1.5B: 2.58, 7B: 0.80, 8B: 8.92） | **M** | 可用 GQA 噪声稀释 + 模型能力差异解释；但 8B > FP16 基线（7.92）的现象需要承认"可能是 LongBench 合成数据对 K4V8 的某些噪声模式敏感度异常"，建议展示 3 seeds 的 std 确认不是单次异常。 |
| **A12** | 结论过强 | 你声称 INT4-RoleAlign "PPL 退化随规模减弱"——但 1.5B 的 13.7% vs KIVI 的 12.0% 本方法更差，7B 的 6.1% vs KIVI 的 5.5% 还是更差，只有 8B 持平。**你用 behavior-aligned 搜索反而比 runtime absmax 更差**，这如何解释"行为对齐的优越性"？ | `ch4_experiments.tex:1345-1362`（主表）；`ch4_experiments.tex:1419-1456`（论文自己承认 1.5B/7B 略差 0.6--1.7 pp） | **H** | 论文已承认（ch4:1426-1432），建议答辩时主动说"RoleAlign 相对 KIVI 在 PPL 上并无优势；真正的方法论贡献是诊断视角，不是数值击败"。避免防守性辩解。 |
| **A13** | 创新性 | 你第二章综述 62 个 cite，其中 KIVI / KVQuant / ZipCache 都已涉及非对称 / 非均匀 / 重要性 + 混合精度量化——你的方法和他们的差异只在 "KL 校准驱动 percentile 搜索"。这个差异能支撑本科毕设创新点吗？ | `ch1_introduction.tex:107-110`（列 KIVI、KVQuant、ZipCache）；`ch2_related_work.tex` 62 cite 覆盖；`ch3_method.tex:691-728`（BA percentile 方法） | **H** | 必须准备好"本科毕设 vs 硕博"的差异认识：本科毕设要求"能综合运用+有新见解"，不要求顶会级创新。强调"三个递进贡献 + GQA 结构性分析 + 工程落地"是本科级的完整工作链。 |
| **A14** | 合规 | 参考文献格式：bib key 命名很随意（`qwen2025qwen25`、`grattafiori2024llama3`、`du2026bitdecoding`），GB/T 7714 不要求 key 命名但**期刊卷期、页码完整性**严格要求——你是否逐条核查过所有 78 条 cite 的完整性？ | `thesis/references.bib` 共 78 个条目；部分条目（如 `du2026bitdecoding`）是 2026 年文章 | **M** | 至少要承诺答辩前用自动化工具（`bibtexparser`）跑一遍完整性检查，把缺页码、缺卷期的条目统计出来。78 条 cite 对本科毕设属于中高位工作量。 |
| **A15** | 答辩表现 | 你能当场用黑板写出 INT4-RoleAlign 的核心公式吗？不看 PPT 的情况下，**BA-guided percentile 搜索的优化目标函数** 是什么？ | `ch3_method.tex:719-726`（公式 eq:ch3-ba-percentile：`argmin_{(p_K,p_V)} (1/|D|) Σ D_KL(p_ref‖p_asym)`） | **H** | 必须现场能写：$(p_K^*, p_V^*) = \arg\min_{(p_K,p_V)\in\mathcal{P}_K\times\mathcal{P}_V} \frac{1}{|\mathcal{D}|}\sum D_{\mathrm{KL}}(p_{\mathrm{ref}} \| p_{\mathrm{asym}})$；并解释 $\mathcal{P}_K=\mathcal{P}_V=\{99.0, 99.5, 99.9, 99.95, 99.99, 100.0\}$，$|网格|=36$。 |
| **A16** | 答辩表现 | KL 散度你用的是 forward 还是 reverse？物理含义是什么？你为什么选 forward？ | `ch3_method.tex:253-268`（forward KL，zero-avoiding 含义） | **M** | 必须能说清 forward KL ($D_{\mathrm{KL}}(p_{\mathrm{ref}} \| p_{\mathrm{quant}})$) 的 zero-avoiding 特性，即"参考分布有权重的位置强制量化分布也要有权重"，对应防止量化遗漏关键 token。 |
| **A17** | 实验严谨性 | 你的 RoPE 修复（CAL-019/020）自己写在第五章的"校准框架局限"里——说"1.5B 主模型校准产物缺 input_layernorm 和 RoPE"，但"修正版验证 INT8 影响 0.05%"。这意味着**你论文报告的 INT8 数字用的是有 bug 的校准产物**。为什么不重跑？ | `ch5_conclusion.tex:105-117`（"1.5B 主模型校准产物的 Q 向量预处理缺少 input_layernorm 和 RoPE"） | **H** | 必须明确："修正版对比验证表明对 INT8 的 PPL 影响仅 0.05%（<0.01 绝对值），对 INT4-RoleAlign 影响为零（BA percentile 校准独立于 RoPE）"，因此主表数字落在 0.5% 非劣性阈值内。但评委可能进一步追问"为什么不重跑验证 RULER/LongBench"，需诚实承认"未做完整重跑"。 |
| **A18** | 格式合规 | LongBench 这一节你自己承认"合成数据源，与官方不可直接对比"——为什么还要在主表主贡献表里列 LongBench 分数？这是否误导读者？ | `ch4_experiments.tex:124-129`（合成数据声明）；`ch5_conclusion.tex:97-101`（局限再次声明）；`ch4_experiments.tex:421-470`（主表仍列 LongBench 列） | **M** | 答辩时强调"LongBench 用于方法间相对比较而非绝对水位"；附录 `sec:app-longbench-official` 已用 3 个官方子任务验证方向性。若评委不接受，准备承诺"从主表移除 LongBench，改为附录补充"。 |
| **A19** | 答辩表现 | 你贡献三"融合核效率"—— $H_{kv}=2$ 下融合核在所有长度均慢于 SDPA，这叫"贡献"还是"失败"？为什么不干脆删掉这个贡献？ | `ch4_experiments.tex:1847-1862`（Phase Boundary 表）；`abstract_zh.tex:36-37`（自陈$H_{kv}=2$ 融合核始终慢于 SDPA） | **M** | 必须坚持"提供了结构性 (H_kv, seq_len) 部署建议"的 framing——它不是性能贡献，是**部署选型指导**（$H_{kv}≥4$ 用融合核，$H_{kv}=2$ 用 SDPA）。这是工程论文的常见写法。 |
| **A20** | 工作量 | 你工作量描述——4 个模型 × 9 种 kv_mode × 4 个基准 × 5 seeds，计算量看起来很大，但实际主表仅 1 模型（Qwen2.5-1.5B）全矩阵，其他模型 subset。**请量化你真正跑完的 (模型, mode, 基准, seed) 组合数**。 | `ch4_experiments.tex:27-53`（5 个模型列表，Mistral 只在 K/V 消融）；`ch4_experiments.tex:61-88`（decode 参数表）；`tab:main-results` 只给 1.5B；`tab:cross-model` 只给 Qwen-7B/LLaMA-8B INT8 部分 | **M** | 必须准备"实验组合数"工作量表：(1) INT8 全矩阵 4 模型 × 4 基准 × 5 seeds = 80 runs + K/V 消融 5 模型 × 3 seeds ≈ 45 runs + INT4-RoleAlign 4 模型 × 4 基准 × 3 seeds ≈ 48 runs + profiling 4 模型 × 4 序列长度 × 10 runs = 160 runs + 校准产物生成 4 模型 × 2 bit-width = 8 runs。总计 **~340 次实验**，这在本科毕设中属于中高位工作量。 |

---

## B. 评分模拟

> 按附件 3《本科生毕业设计（论文）评分标准》三阶段给分。标注**扣分项**，说明给分档次依据。

### B.1 平时成绩（30 分）

| 项目 | 预期档次 | 预期分数 | 扣分项 |
|------|---------|---------|--------|
| 学习态度 | 优秀 | 28/30 × 比例 | 从 iteration.md 和审查流程可见学生非常认真，迭代超过 6 轮，Codex 审查交叉验证 7 轮。无扣分。 |
| 学习能力 | 良好 | -1 | 能综合运用模型量化、Triton、统计检验知识，但部分实现差异（KIVI 简化）和 bug（RoPE 缺失）显示对基础理论的掌握仍有提升空间。 |
| 文献阅读 | 优秀 | 0 | 参考文献 78 条、第二章 62 cite，覆盖量化、注意力加速、长上下文评测三大方向。优秀档。 |
| 文献综述 | 良好 | -1 | 第二章综述较为完整，但 AI 味道较重（多用"系统性"、"隐含假设"等套话）。良好偏上。 |
| 外文翻译 | 良好 | 0 | 英文摘要通顺，术语准确。无扣分。 |

**平时成绩预估：26.5 / 30（良好偏上，≈88 分）**

### B.2 审阅成绩（30 分）

| 项目 | 预期档次 | 预期分数 | 扣分项 |
|------|---------|---------|--------|
| 工作量 | 良好--优秀 | -1 | 总实验组合数 ~340 次，4 模型 × 9 kv_mode × 多基准，属于本科毕设中高位。但 14B 仅 1 seed、LongBench 合成不做官方完整对比，扣 1 分。 |
| 技术水平 | 良好 | -3 | **数据失控**：摘要 7B 6.0% 与主表 6.1% 不一致（A03, TR-0002）；关键词超标（A04, TR-0003）；RoPE 缺失 bug 自曝；静默 fallback bug 自曝。设计基本合理、分析基本正确，但**数据准确性有明显瑕疵**，仅达"比较准确"档。 |
| 学术水平 | 良好 | -2 | 三个贡献中贡献一自陈"经验观察非方法创新"（A06）；贡献二真内核与 KIVI 重合（A01）；贡献三 $H_{kv}=2$ 部分为负面结果（A19）。能"正确分析并有新见解"但"成果比较突出"存疑——评委可能给中等档。 |
| 文字表达 | 良好 | -2 | **AI 辅助写作痕迹**：过度使用"系统性"、"结构性关联"、"双重依赖"、"规模依赖"等高级抽象词；大量长句；部分段落像机器改写而非人类写作。中英文结构严谨但不够自然。 |

**审阅成绩预估：22 / 30（中等偏上，≈73 分）**

### B.3 答辩成绩（40 分）

| 项目 | 预期档次 | 预期分数 | 扣分项 |
|------|---------|---------|--------|
| 个人陈述 | 良好 | -3 | 若能在 10 分钟内讲清三贡献 + 论证链路 "视角→诊断→实例化→边界"，可达良好；但若陷入细节（如温度校正消融）或讲不清 GQA 头数关联的物理机制，降档。 |
| 回答问题 | 良好--中等 | -6 | **关键答辩风险点**：(A01) KIVI 重合解释能否服人、(A03) 数据不一致当场被抓、(A05) 14B 打破单调性能否坦然回答、(A17) RoPE bug 为何不重跑。若这 4 题答不好可能被降到中等档。 |

**答辩成绩预估：31 / 40（良好，≈77 分）**

### B.4 总分估算

- 平时：26.5 + 审阅：22 + 答辩：31 = **79.5 / 100（中等偏上，接近良好）**
- **修复 Top-5 CRITICAL 后预估可提升至 83--86（良好）**
- **修复后若答辩现场表现佳，可冲刺 87--90（良好偏上）**
- 冲击"优秀"（≥90）**极其困难**，核心障碍是 A01 创新性争议 + A02 工作量完整性 + A12 RoleAlign 在 PPL 上未击败 KIVI 这三点都是结构性的，已无法通过修辞补救。

---

## C. 若要强答辩通过，论文必须修改的 Top-5（CRITICAL）

### C1. 【TR-0002, A03】摘要 PPL 数字统一（24h 内必改）

- **问题**：中英文摘要 "7B: 6.0%" vs 主表 "+6.1%" 不一致
- **修改位置**：`abstract_zh.tex:31`、`abstract_en.tex:39`、`ch5_conclusion.tex:38`
- **改为**：统一 `7B: 6.1%`（从原始 7.58/7.14≈6.16% 四舍五入）
- **风险**：若不改，答辩现场被抓即视为"数据失控"，直接从良好档降至中等档

### C2. 【TR-0003, A04】关键词数量合规（24h 内必改）

- **问题**：6 个关键词超附件 1 的 3--5 上限
- **修改**：`abstract_zh.tex:39` 和 `abstract_en.tex:48-50` 各保留 4 个
- **推荐**：`大语言模型；键值缓存；行为对齐校准；GQA` / `Large Language Model; Key-Value Cache; Behavior-Aligned Calibration; GQA`
- **风险**：格式不合规会直接被评阅教师给 -1 到 -2 分

### C3. 【A02】14B 外部效度边界明确标注

- **问题**：摘要/引言中 "四个模型" claim 误导读者以为完整验证
- **修改**：
  - `abstract_zh.tex:20` "在 Qwen2.5-1.5B/7B/14B 与 LLaMA-3.1-8B 四个模型上" → "在 Qwen2.5-1.5B/7B 与 LLaMA-3.1-8B 三个模型上完整验证，Qwen2.5-14B 作为外部效度锚点（Needle 4K--32K、RULER 4K--16K）"
  - `ch1_introduction.tex:77-78` 同步修改
- **风险**：不改会被 A02 直击"工作量虚胖"

### C4. 【A05】摘要披露 14B 非单调性

- **问题**：摘要"PPL 退化随规模减弱"暗示单调，14B 7.6% 打破该趋势
- **修改**：`abstract_zh.tex:31-33`、`abstract_en.tex:36-40` 将"PPL 退化随模型规模减弱（1.5B: 13.7%，7B: 6.0%，8B: 2.4%）"改为"PPL 退化大致随模型规模减弱，但 14B（7.6%）出现非单调例外"
- **风险**：不改直接被 cherry-picking 指控

### C5. 【A08】补充 one-click 复现入口脚本

- **问题**：`final_scripts/reproduce/` 目录不存在，`scripts/` 下散落开发脚本，非熟悉本项目的人难以复现
- **修改**：新建 `scripts/reproduce/` 目录，至少包含：
  - `ch4_main_table.sh`（跑表 4.2 主表）
  - `ch4_rolealign_cross_model.sh`（跑表 4.14 RoleAlign 跨模型）
  - `ch4_phase_boundary.sh`（跑表 4.22 Phase Boundary）
  - `README.md` 说明依赖版本、GPU 要求、预期运行时间
- **修改附录**：`appendix.tex` 新增"复现指南"小节指向这些脚本
- **风险**：本科毕设若无 one-click reproduce，再严谨的数据也会被评委质疑"只是我会跑"

### C6（bonus, 非严格 CRITICAL 但强烈建议）. 【A07, A17】RoPE bug 和 fallback bug 的完整补救路径披露

- **问题**：第五章自曝两个严重 bug，但未说清补救程度
- **修改**：`ch5_conclusion.tex:80-117` 明确补充：
  - (a) EVL-037 fallback bug：已在 eval_ppl.py v2 修复（明确分支到 asym 路径），附录展示 `diff` 证据
  - (b) CAL-019/020 RoPE bug：已重跑修正版 INT8 + INT4-RoleAlign 的 PPL 一致性验证（PPL 影响 0.05%），但 RULER/LongBench 未完整重跑——应列入"后续工作"而非"已修复"
- **风险**：评委若问到细节，模糊回答会极度伤害可信度

---

## 附：答辩现场可能的"连珠炮追问链"（panel 模拟，2 分钟 N 连）

```
评委: 你的主要创新点是什么?
你: 三个贡献...

评委: (打断) 贡献二你说得最响, 但格式来自 KIVI, 对吗?
你: 是的, 格式共享, 但参数化方式不同...

评委: 那既然参数化方式不同是你的创新, 为什么 PPL 上 RoleAlign 比 KIVI 还差?
你: 在 1.5B 和 7B 上差 0.6-1.7 个百分点, 但 Needle 都保持 100%...

评委: 可 KIVI 的 Needle 也是 100% 啊! 你的行为对齐校准带来了什么?
你: (关键时刻) ...

评委: 摘要写 7B: 6.0%, 表格写 6.1%, 这是印刷错误还是数据问题?
你: 我会在终版统一...

评委: 那你还有多少类似的不一致? 你敢保证全篇没有第二处吗?
你: ...
```

**唯一对策：在提交前把 Top-5 CRITICAL 全部修完，并预演这串追问 2--3 遍，建立"诚实+限定 claim+强调诊断视角的方法论价值"的三位一体回答框架。**
