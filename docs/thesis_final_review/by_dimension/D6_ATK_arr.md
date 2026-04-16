# D6_ATK: EMNLP ARR 2026 Reviewer 2 Simulated Attack

**维度**: D6b — ARR 2026 视角的对抗性审查（novelty/soundness/clarity/reproducibility/ethics）
**审阅者设定**: Reviewer 2, ACL Rolling Review, 量化/KV cache 方向资深审稿人（对 novelty 敏感，对基线完整性挑剔）
**审阅对象**: `thesis/main.pdf`（114 页）+ `thesis/chapters/*.tex`
**权威数据源**: `results/final/final_data/INDEX.md`（717 runs, frozen 2026-04-17）
**生成日期**: 2026-04-17

---

## ⚠ 重要说明：本文件的定位

根据用户 v5 决策（Q1 = A），**ARR 视角仅作附带输出，不驱动论文修改**：
- 答辩优先级高于 ARR
- 所有 M-A / L-A 级别问题仅在此文件追踪，不进 `issues.md` 主表
- 若 ARR 修复建议与答辩写作纪律冲突，**校方（答辩）优先**
- 本文件的目的：若未来决定投 EMNLP ARR 2026，此份审查清单作为 revision starting point

---

## A. 模拟 ARR review（五项打分 + 理由）

使用 ARR 2026 官方五维度 rubric（1=poor, 5=excellent）。

### Soundness: 3.5 / 5

**理由**：
- ✅ 实验协议扎实：greedy decoding + 5 seeds + Bootstrap CI + sign-flip permutation + BH-FDR（$\alpha=0.05$），统计框架在当代 LLM 评测中确实处于较高水位（作者自己引用 Bean 2025 的 16% 统计检验覆盖率作为对照，这个引用是合适的）。
- ✅ 控制变量严谨：K-only / V-only / K4V8 消融设计干净，四模型一致性观察可信。
- ✅ 核心结论（Key 主导退化、GQA 稀释）有 14B 外部效度验证（K 恢复 93% vs V 恢复 64%）。
- ⚠ **关键弱点 1**：14B 仅 1 seed（见 ch4 L1325 "14B 为 1 seed"）。在 ACL/EMNLP 评审中，外部效度 claim 用 1 seed 是 reviewer 必然指出的 red flag。作者在 ch4 L244-250 论证了 greedy PPL 的位级确定性，理论上合理，但 Needle 不是位级确定（depth 级别采样），14B Needle 1 seed 较脆弱。
- ⚠ **关键弱点 2**：LLaMA-3.1-8B 的 INT8 校准"相对 FP16 偏高 16%"（ch5 L110），作者标注为"次优性"但未修复。ARR reviewer 会追问：这不是校准方法的泛化失败吗？
- ⚠ **关键弱点 3**：陈述"KL 至少不劣于 MSE"（abstract L27、ch5 L27）但实际 PPL 上 RoleAlign 略差于 KIVI-style（1.5B: 13.7% vs 12.0%, 7B: 6.1% vs 5.5%, 详见 ch4 L1447-1457）。作者在这一段承认"单看 PPL 数字去比较 RoleAlign 和 KIVI 并不是一个有信息量的判断"——ARR reviewer 会 flag 为 self-contradiction。
- ⚠ **Threat-to-Validity**：作者自述 $H_{kv}$ 与模型规模 part共变（ch5 L238-241）。结论 causal 解释薄弱。这是诚实的声明，但也削弱了贡献。

**Reviewer 2 literal comment**: "The diagnostic claim that INT4 degradation is Key-dominated is supported by careful ablations. However, the paper's central methodological proposal (attention-KL calibration) fails to produce a clear numerical win over KIVI's calibration-free baseline on PPL in 3 of 4 models. The authors acknowledge this in §4.7 but frame it as 'PPL not being a meaningful comparison metric' — this line of reasoning is circular and should be addressed more directly."

### Novelty: 2.5 / 5

**理由**：
- ✅ attention-KL × $H_{kv}$ 的联合分析框架是新颖的组织视角。
- ✅ $\tau^{-1}$ 与 GQA 的双向效应（Finding 4，附带贡献 C5）是文献中未见报道的观察（ch4 L1543-1544 明确声明据作者所知未被系统报道）。
- ❌ **核心原创性争议**：
  - **KL 校准本身**早就是 TensorRT entropy calibration（2017 Migacz）的常规工具——作者在 ch2 L207-213 和 ch4 L350-355 都正确归因。问题在于 novelty 被挤压到"把 KL 从激活层推到 attention 层"这一点上，而这一点在 ARR reviewer 看来是 **incremental contribution**（微创新）。
  - **per-channel K + per-token V 非对称格式**是 KIVI (ICML 2024) 的原创贡献。作者在 abstract L32-35 和 ch3 L17-18 明确承认 "the same format independently proposed by KIVI from engineering observation"。这是非常诚实的归属。但这也意味着 RoleAlign 的 novelty 只在于"用 KL 搜索 percentile 代替 absmax/min"——这是**方法上的小增量**。
  - ch4 L1447-1457 自己承认：4-bit 只有 15 级别，两种 scale 的差被量化粒度直接吸收，"最终量化映射几乎看不出差异"。这段话对 ARR reviewer 是致命的：**如果你的方法在方法对比上 indistinguishable from KIVI**，EMNLP 录用的门槛就不清楚了。
- ⚠ **与 SmoothQuant 的潜在 collision**：SmoothQuant (2023) 也提到了 "smooth 激活分布"的思路。作者没有讨论自己的 attention-KL 与 SmoothQuant 的"通过数学等价变换将量化难度迁移"的异同。Reviewer 会追问。

**Reviewer 2 literal comment**: "The paper's novelty claim rests on three pillars: (1) attention-KL calibration objective; (2) RoleAlign as instantiation; (3) $H_{kv}$-aware deployment. Pillar (1) is an incremental extension of TensorRT's entropy calibration from layer-wise activation to attention weight space. Pillar (2) shares the exact quantization format with KIVI (ICML 2024) — the authors commendably acknowledge this, but the actual methodological differentiator (offline KL search vs runtime absmax/min) is shown in §4.7 to produce indistinguishable results at 4-bit. Pillar (3) is primarily an empirical observation rather than a novel mechanism. The combined novelty is significant but not transformative for EMNLP main track."

### Clarity: 3.5 / 5

**理由**：
- ✅ 章节结构清晰，Chapter 4 明确按 C1/C2/C3 证据组织。
- ✅ tab:kv-modes（ch4 L165-197）把 9 种 KV 模式的校准/bit-width/kernel/量化轴四维对比讲得很好。
- ⚠ **Abstract 长句问题**（L24-40，问题中明确点名）：L32-35 "The diagnosis naturally points to a per-channel Key + per-token Value asymmetric format---the same format independently proposed by KIVI from engineering observation." 这句 134 词（连接 L24 起的句子）过长。ARR reviewer 会建议拆成 3-4 个短句。
- ⚠ **术语一致性**：
  - "INT8-ours" / "int8\_ours" / "INT8-Canonical"（fig:main-quality-dashboard）/ "int8\_ours (mainline)" 四个名字交叉使用
  - "INT4-RoleAlign" / "int4\_ours\_asym" / "int4\_ours\_asym_ba" 也混用
  - "attention-KL" vs "behavior-aligned" vs "KL 校准" vs "行为对齐" 在中英语境混杂
- ⚠ **Abstract 数字不一致**：
  - abstract_en L39 "7B: 6.0%" vs introduction L179 "7B: 6.0%" — 这里是一致的
  - 但 ch4 L1422-1423 表 4.5 写"Qwen2.5-7B 为 6.1%" — 散文 vs 表格不一致（差 0.1%）。MEMORY.md 已标记此为 known issue（"7B 6.0%(散文)/6.1%(表格)"）。ARR reviewer 会追问。
- ⚠ **图 1 的论证链复杂**：ch1_pipeline_gemini_cropped.png 试图同时展示 C1/C2/C3 三条证据链 + $H_{kv}$ 中心地位，对首次阅读者信息密度过高。

**Reviewer 2 literal comment**: "The paper is well-organized overall but suffers from terminology inconsistency: the same method (e.g., 'int8_ours' vs 'INT8-Canonical') uses different names across sections. The abstract's key sentence describing the asymmetric format proposal is 134 words and difficult to parse on first reading. A number mismatch (7B PPL degradation: 6.0% in prose vs 6.1% in Table 4.5) suggests inconsistent rounding or last-minute data update."

### Reproducibility: 4.0 / 5

**理由**：
- ✅ 模型 revision 固定（ch4 L33 "revision \code{989aa7}"）。
- ✅ seeds 明确（质量 1234-1238, 效率 1234-1241, ch4 L82-83）。
- ✅ env/versions.txt + env/requirements_freeze.txt（ch4 L58-59）。
- ✅ 校准产物路径明确（ch4 L374 "artifacts/kv\_calib\_\{kl,mse\}\_1p5b\_\{int8,int4\}.json"）。
- ⚠ **代码 repo 未公开**：全文未见 GitHub URL。EMNLP ARR 2026 要求 Responsible NLP Checklist 中的 "Will code be made publicly available?" — 目前答案不明。这是 **reproducibility score 从 4.5 扣到 4.0 的主要原因**。
- ⚠ **BitDecoding 评测**（ch5 L124-131）：作者发现 BitDecoding 在 GQA 下数值错误，但该结论是否可复现给其他 reviewer？附录是否有 minimal repro？需要补充。

**Reviewer 2 literal comment**: "The paper does an excellent job documenting model revisions, seeds, and calibration artifacts. However, the code repository URL is conspicuously missing. For ARR submission, a link to an anonymized review copy (e.g., OSF, anonymous.4open.science) is strongly expected."

### Ethics / Dataset: 4.0 / 5

**理由**：
- ✅ WikiText, LongBench, RULER 使用合规（均为公开学术 dataset）。
- ✅ ch4 L125-127 明确声明 LongBench 使用 **自行实现的合成数据**（不是官方数据集），避免绝对分数误导的伦理风险。
- ✅ 校准数据使用 WikiText-103 子集（ch4 L163-168），校准-评测数据 split 清楚（不构成 data contamination）。
- ⚠ **未使用的 NLP checklist 项**：
  - 模型的**代际倾向**（Qwen2.5, LLaMA-3.1 是 2024-2025 模型，是否有价值观对齐讨论？）— 作为技术论文不强制，但 Responsible NLP Checklist 会问。
  - **能源消耗**：714 runs 在 H20 上跑的碳足迹（Responsible NLP Checklist "Describe the computational budget"）— 附录里有 versions.txt 但没看到具体 GPU hours 汇总。
- ⚠ **Dataset License 显式声明缺失**：正文中未见"WikiText-103 License: CC BY-SA"等显式 license 声明。ARR checklist 明确要求。

**Reviewer 2 literal comment**: "Dataset usage is clean and contamination-free. However, the paper lacks explicit dataset license declarations and an energy/compute budget table, both required by the ARR 2026 Responsible NLP Checklist."

---

## B. 推荐等级：**Major Revision**

**推荐类别**: Major Revision（非 Strong Reject，非 Minor Revision）

**理由**：
- 论文的**工程价值和实验系统性**非常扎实（Soundness 3.5，Reproducibility 4.0），这排除了 Strong Reject。
- 但 **Novelty 2.5** 是 EMNLP main track 的硬伤：
  - 核心方法（attention-KL、asymmetric format）都有明确 prior art
  - 自己在 §4.7 承认 RoleAlign 与 KIVI 在 4-bit 下 indistinguishable
  - 附带贡献 C5（$\tau^{-1}$ × GQA 双向效应）是真正有 novelty 的观察，但被放在**探索性观察**的定位上，而非主贡献
- 主要修改方向：
  1. **重新定位 novelty**：把 C5（inv_tau × GQA）从"探索性观察"升格为主贡献之一，或明确承认这是 diagnostic framework 的附属 finding
  2. **补齐 14B 多 seed**：至少 3 seed，消除 "14B 1 seed" 的 red flag
  3. **修复 LLaMA INT8 16% PPL 偏差**：ch5 L110 标记的"次优性"必须解决，否则方法泛化性受质疑
  4. **discussion 对 SmoothQuant 思想关系的明确澄清**（见 C3 问题）
  5. **诚实面对 PPL indistinguishability**：把 §4.7 L1447-1466 的"单看 PPL 不是有信息量的判断"这段 argument 从 defensive 改为 constructive（e.g., 用 attention-KL 作为 figure of merit）

**若不改就投递的预期结果**：Reject（概率 ~60%）/ Major Revision（概率 ~35%）/ Accept（概率 ~5%）。

---

## C. Top-15 Reviewer 挑刺点（ARR 视角）

| # | 问题 | 严重度 | 论文 file:line | if-keep 建议（答辩优先） | if-ARR-submit 必修 |
|---|------|--------|----------------|------------------------|-------------------|
| C1 | **14B 外部效度仅 1 seed**：核心 "14B: K 恢复 93% vs V 恢复 64%" claim 统计基础薄弱 | **M-A** | ch4 L1325 "14B 为 1 seed"；ch4 L1130-1143 tab:14b-kv-ablation "3 seeds"（互矛盾） | 答辩前解释统计框架即可 | 补跑 2 个额外 seed（4 GPU-hours 估算），更新表 |
| C2 | **RoleAlign vs KIVI PPL 无差异被作者自己点破**：ch4 L1447-1457 "两种 scale 的数值差被量化粒度直接吸收" 削弱 RoleAlign novelty | **M-A** | ch4 L1447-1466 | 答辩时强调"方法差异在 diagnostic framework 而非 PPL 数字" | 重构 §4.7：把 "PPL indistinguishable" 从 defense 改为 constructive framing（e.g., RoleAlign 的贡献在 offline search 的可解释性与 deployment predictability，而非 PPL 增益）|
| C3 | **SmoothQuant 思想关系未讨论**：SmoothQuant 也提"通过数学变换平滑量化难度"，与 attention-KL 的"行为保真"思路有关联 | **M-A** | ch2 L330-336（仅提 SmoothQuant 名字，未讨论思路关联） | 答辩无需 | ch2 新增 paragraph：明确声明 attention-KL 与 SmoothQuant 的 orthogonality（SmoothQuant 在 format/activation dimension，attention-KL 在 objective dimension）|
| C4 | **abstract 长句 134 词**：L24-40 几乎是一个连续 argument，难以一次读懂 | L-A | abstract_en L24-40 | 答辩 abstract 可不改 | 拆成 3-4 个独立句子，每句聚焦一个 finding |
| C5 | **术语不一致**：int8_ours / INT8-Canonical / int8_ours (mainline) 四个名字 | L-A | fig:main-quality-dashboard caption; tab:main-results; 散文各处 | 答辩统一即可 | 全文 replace_all 统一用一个 canonical name（推荐 "INT8-ours" 作为主名，alias 只在 caption 说明） |
| C6 | **7B PPL 数字不一致**：散文 6.0% vs 表 6.1%（MEMORY.md 已记录）| L-A | ch4 L1422-1423 vs tab:rolealign-results L1353 | 答辩前对齐 | 统一为一个数字（建议取表 6.1%，因为来自 authoritative data） |
| C7 | **代码 repo 未公开**：全文无 GitHub URL，不符合 ARR checklist | **M-A** | 全文 | 答辩无需 | 必须准备 anonymized code repo（OSF / anonymous.4open.science），放在 abstract 或 §1.4 脚注 |
| C8 | **LLaMA-3.1-8B INT8 16% PPL 偏差被搁置**：作者自述 "8B 展现一定次优性" | **M-A** | ch5 L110-114 | 答辩可声明 "主表聚焦 1.5B 不影响核心结论" | 必须修复或提供 root-cause 分析（可能与 $H_{kv}=8$ 下校准偏好不同有关）|
| C9 | **inv_tau × GQA 的 novelty 被低估**：放在 "探索性观察"（ch4 L1467）而非主贡献 | **M-A** | ch4 L1467-1554 | 答辩可继续弱化 | ARR 投稿时考虑升格为 Finding 4 主贡献之一，这是本文最有 novelty 的观察 |
| C10 | **KL forward vs reverse 选择未充分论证**：ch5 L196-202 作为 future work 列出，但这是 INT4 低比特下的核心设计决策 | L-A | ch3 校准章节；ch5 L196-202 | 答辩可答 "forward KL 在理论上 zero-avoiding 保护关键 token" | 正文加 0.5 page discussion + 对 1.5B 做 forward/reverse 消融对比 |
| C11 | **chunk_size=1 灾难性退化被隐藏在附录**：INT4-RoleAlign PPL > 10,000 是严重缺陷 | **M-A** | ch5 L71-78；app:chunksize | 答辩可说 "cs≥8 稳定" | 正文 §4.10 必须明确讨论部署边界，不能只在附录 |
| C12 | **Bootstrap CI 用在 deterministic PPL 上是不合适的**：ch4 L244-250 已自述 PPL 位级确定，但主表仍列 $\pm 0.00$ 的 CI | L-A | tab:main-results L429-449 | 答辩时解释 "保留形式统一性" | 主表去掉 PPL 的 $\pm$（视觉上暗示统计检验但实际无意义） |
| C13 | **FP8 KV Cache 对比完全缺失**：H100/H200 主流部署选项，无对比无法声称 INT4 是合理压缩目标 | **M-A** | ch2 L407-424（只提 FP8 存在，无实验） | 答辩可说 "H20 不支持 FP8"（需验证）| ARR 必须补 FP8 对照（至少在同一模型上跑 PPL + Needle）|
| C14 | **bit-width 依赖 claim 用 2 个模型验证**：INT4 下 KL vs MSE 的分歧/趋同在 1.5B（分化）和 7B（趋同）上各只一个数据点 | L-A | ch4 L389-395 | 答辩可说 "规模依赖性与 $H_{kv}$ 一致" | 补充 8B 或 14B 的 INT4 KL vs MSE 搜索，验证 claim 的外推 |
| C15 | **Energy / compute budget 缺失**：Responsible NLP Checklist 明确要求 | L-A | 全文无 | 答辩无需 | 附录加一页 "Computational Budget"：717 runs 总 GPU-hours，H20 功耗估算 |

**严重度分布**: M-A × 8, L-A × 7

---

## D. 与答辩视角的冲突标注

以下 ARR 建议与答辩写作纪律**明确冲突**，按用户决策（答辩优先）标注：

| # | ARR 建议 | 答辩建议（校方优先） | 决策 |
|---|---------|---------------------|------|
| Conflict-1 | **C9**: 升格 inv_tau × GQA 为 Finding 4 主贡献 | 答辩讲究"3 个核心贡献简洁" | **答辩优先**：保持 C1/C2/C3 三分法 + Finding 4 作为附属 |
| Conflict-2 | **C2**: 重构 §4.7 把 "PPL indistinguishable" 从 defense 改为 constructive | 答辩时强调"KIVI 基线的完整实现"避免引火烧身 | **答辩优先**：保留当前 defensive framing |
| Conflict-3 | **C11**: cs=1 灾难性退化必须正文讨论 | 答辩聚焦 mainline 结果，避免暴露"极端压力测试失效" | **答辩优先**：保持附录位置 |
| Conflict-4 | **C13**: ARR 必须补 FP8 对比 | 答辩时间紧，FP8 实验工作量大 | **答辩优先**：ch2 L413-424 的声明已足够，不补实验 |

---

## E. 总结评价

**核心判断**: 论文在**工程执行（实验系统性 + 统计框架 + 可复现性）**上达到 EMNLP 水准（Findings/Main 均可），但在 **methodological novelty** 上达不到 EMNLP main track 的 bar（预计 Findings 可能更合适）。

**建议投稿目标排名**（若 ARR 2026 投稿）：
1. **EMNLP 2026 Findings**（预期录用率 ~35%）— 推荐首选
2. **NAACL 2026 Findings 或 Main** — 可选（novelty 门槛类似）
3. **ICLR Workshop on ML Systems** — 备选（系统型工作友好）
4. **EMNLP 2026 Main Track** — 不推荐（除非完成 C1-C3、C7-C9 等 M-A 修复）

**最小 ARR 投稿前修复清单**（按工作量排序）：
- [1 day] C5, C6, C4, C10：格式/术语/数字统一
- [0.5 day] C7：建 anonymized repo
- [0.5 day] C15：加 compute budget 表
- [4 GPU-hours] C1：14B 补 2 seed
- [4 GPU-hours] C14：8B/14B INT4 KL vs MSE 补充
- [8 GPU-hours] C13：FP8 KV Cache 实验（H100 上，若可访问）
- [无需实验] C2, C3, C8, C9, C11, C12：写作重构，总计 2-3 days

**总预算**：~2 days 写作 + ~20 GPU-hours 实验 + 1 day polishing = **1 周内可提交 ARR**。
