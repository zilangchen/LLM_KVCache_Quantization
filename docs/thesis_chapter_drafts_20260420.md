# 论文章节草稿（2026-04-20）

**日期**：2026-04-20
**文档身份**：论文每章的**内容骨架 + 关键段落草稿 + 写作注意点**

---

## 0. 文档用途

### 它承担什么

- 每章目标 + 目标长度
- 每章关键论点 bullets
- 每章核心段落 200-400 字草稿模板
- 每章引用图表清单（cross-ref 到 `thesis_story_20260420.md` §16）
- 每章与故事线 §X 的对应关系
- 写作注意点（避免什么 / 必须包含什么）

### 它不承担什么

- 完整正文（需要在 thesis/chapters/*.tex 里逐段写）
- 精确用词（术语契约见 thesis_story §15）
- 图表生成脚本（见 thesis_story §16）
- 叙事结构或层级设计（见 thesis_story §1-§8）

### 配套文档

- 叙事主线：`docs/thesis_story_20260420.md`
- 图表 spec：`docs/thesis_story_20260420.md` §16
- 数据资产：`docs/data_asset_inventory_20260420.md`
- 口径边界：`docs/freeze_20260419.md`

### 维护规则

**只 append，不 rewrite**。实际改 tex 时发现草稿不够用，在本文档末尾 append 一条修订记录，不改现有草稿。

---

## 1. Abstract（中英双版）

### 1.1 目标

| 字段 | 值 |
|---|---|
| 中文长度 | ~350-450 字 |
| 英文长度 | ~250-350 words |
| 核心结构 | problem → hypothesis → method (3 pieces) → experiments → insight → contribution |
| 写作时机 | **最后写**（等所有章节定稿后） |

### 1.2 关键论点（按出现顺序）

1. KV Cache 量化真正损伤的是 attention behavior，不是单纯数值
2. Behavior 可作为**统一原则**贯通 calibration 和 allocation
3. INT8 canonical + INT4 RoleAlign 验证第一层
4. Cross-model + Pareto 揭示 regime 地图（不是 universal winner）
5. AutoK 作为 framework 自然扩展

### 1.3 中文草稿

> **[段 1：问题与假设]** 长上下文推理中，KV Cache 量化是降低显存与带宽成本的核心手段。本文从 attention 计算的误差传播分析出发，提出一个理论动机驱动的假设：在 KV Cache 量化中，更值得被保护的不是张量数值，而是由其诱导的注意力行为。
>
> **[段 2：方法]** 基于该假设，本文将 behavior 作为统一原则，贯通两层：在校准层，引入以 attention behavior 偏移为目标的离线校准，分别在 INT8（配合 Triton 融合核）和 INT4（配合 K per-channel + V per-token 非对称格式）上落成；在分配层，用校准的副产品——per-layer behavior sensitivity profile——指导预算分配，并以 AutoK 作为 profile-guided 的预算建议扩展。
>
> **[段 3：实验与发现]** 在 clean-provenance 的跨模型实验（Qwen2.5-{1.5B, 3B, 7B, 14B}、Llama-3.1-8B、Mistral-7B-Instruct-v0.3）上，INT8 规范验证路径与 FP16 近乎无损（mean Δ=+0.02），INT4 RoleAlign 与 KIVI 具有可比性。更进一步，allocator 的跨模型结果呈现出一张 family/scale/task-dependent 的 operating regime 地图：Mistral 给出 AutoK 最清晰的正面案例；3B 呈现出首层保护关键的结构瓶颈；14B 在高质量区间内无单一稳定赢家。Heuristic 作为强基线被正面承认。
>
> **[段 4：贡献定位]** 本文的贡献不是宣称某个方法的普适胜出，而是：（1）提出 behavior 作为 KV Cache 量化的统一分析与设计原则；（2）将该原则实例化为一条贯通 calibration 与 allocation 的完整 framework；（3）通过跨模型实证揭示 allocator 的现实是 regime 地图而非 universal winner。

### 1.4 英文草稿

> **[Paragraph 1]** Long-context LLM inference is bottlenecked by KV cache footprint. Motivated by an error-propagation analysis of attention, we hypothesize that what matters in KV quantization is not tensor-level numerical proximity, but the preservation of the induced **attention behavior**.
>
> **[Paragraph 2]** Taking behavior as a unifying principle, we instantiate it across two layers: (i) offline calibration minimizing behavior drift, realized in INT8 (with a fused Triton kernel) and in INT4 (with K per-channel and V per-token asymmetric format); (ii) layer-wise budget allocation driven by the behavior sensitivity profile—a byproduct of calibration—extended by AutoK, a profile-guided budget proposer.
>
> **[Paragraph 3]** Across clean-provenance experiments on 6 models, the INT8 canonical path is essentially FP16-equivalent (mean Δ=+0.02) and INT4 RoleAlign is comparable to KIVI. More importantly, the cross-model allocator results reveal a family-/scale-/task-dependent regime map rather than a universal winner: Mistral-7B provides the clearest AutoK positive case, Qwen2.5-3B exhibits an early-layer rescue regime, and Qwen2.5-14B shows a tight top-tier with no stable single winner. Heuristic allocation is a strong baseline.
>
> **[Paragraph 4]** Our contribution is not a single-method victory, but (1) proposing behavior as a unifying principle for KV quantization, (2) instantiating it into a framework connecting calibration and allocation, and (3) empirically revealing the regime-map reality of behavior-guided allocators.

### 1.5 写作注意点

- **不写**："we achieve state-of-the-art" / "our method outperforms all baselines"
- **改写为**："we reveal a regime map" / "our framework provides a principled view"
- 不具体给某个 model 的 quality 数字（留给主表）
- 5-6 个 model 在摘要**只列名**，不列分数

---

## 2. Ch1 Introduction（~2500 字 / ~3 页）

### 2.1 结构

| 节 | 目标 | 长度 |
|---|---|---|
| §1.1 Background | 长上下文推理 + KV 成本瓶颈 | ~500 字 |
| §1.2 Problem & Motivation | attention 误差分析 → 假设 | ~800 字（含图 ①）|
| §1.3 Research Questions & Contributions | RQ1-3 + C1-3 | ~600 字 |
| §1.4 Roadmap | 章节导览 + 图 ② | ~400 字 |

### 2.2 §1.2 核心段落草稿（motivation）

> 量化 KV Cache 时常用 MSE / relative error 作为代理目标。这类数值代理隐含一个前提：张量的数值越接近，模型的表现就越接近。然而该前提在 attention 结构中并不成立。
>
> 设标准 attention 为 $z_i = q^\top k_i / \sqrt{d}$，$a_i = \mathrm{softmax}(z)_i$，$o = \sum_i a_i v_i$。量化后变成 $\hat k_i, \hat v_i$。直接对输出误差做分解可得：
>
> $$\hat o - o = \sum_i (\hat a_i - a_i) v_i + \sum_i \hat a_i (\hat v_i - v_i)$$
>
> 这条式子告诉我们两件事：(i) K 的量化误差通过 logits + softmax 的非线性传播，直接影响 attention **分布**；(ii) V 的量化误差加权求和，影响 content **聚合**。**真正被下游感知的是这两条路径的最终合成，而不是 $\|\hat k_i - k_i\|$ 或 $\|\hat v_i - v_i\|$ 的范数**（见图 ①）。
>
> 基于这一观察，本文提出一个**理论动机驱动的假设**（theoretically motivated hypothesis，非定理）：
>
> **H**：在 KV Cache 量化中，以注意力行为（attention behavior）的保持度作为优化对象，相比以张量数值范数作为优化对象，更贴近模型真实的功能损伤。
>
> 本文的其余部分正是对这条假设在两个层次（calibration + allocation）上的层层验证（Ch3-Ch5）。

### 2.3 §1.3 RQ + Contribution 段草稿

> 基于假设 H，本文回答三个研究问题。**RQ1**：什么样的分析对象比单纯数值误差更贴近模型损伤？**RQ2**：以 behavior 为中心的校准原则能否落成一套完整可用的量化系统？**RQ3**：同一原则能否延伸到更高层的预算分配？如果能，它揭示了什么结构？
>
> 本文的贡献是：**C1**：提出 behavior 作为 KV 量化的统一分析与设计原则。**C2**：将该原则实例化为三个具体方法组件——INT8 canonical path（behavior calibration + Triton 融合核）、INT4 RoleAlign（behavior + K per-channel / V per-token 非对称架构）、AutoK（profile-guided budget proposer）——给出完整闭环。**C3**：通过跨 5 模型、5 任务的 clean-provenance 实验，揭示 allocator 的真实现实是一张 family/scale/task-dependent 的 operating regime 地图，而非 universal winner；在此地图中，heuristic 作为强基线被正面承认。

### 2.4 §1.4 Roadmap 草稿片段

> 本文组织如下：Ch2 综述相关工作，明确本文与 KIVI 等直接 baseline 的定位；Ch3 形式化问题并描述 behavior-guided 框架在 calibration 与 allocation 两层的具体实例化；Ch4 在 5 模型 × 5 任务的 clean-provenance 实验上给出实证，包括 INT8 canonical 路径、INT4 vs KIVI 跨模型对比、allocator 的 regime 地图（图 ⑦ Pareto 主图）、以及 per-model case 分析；Ch5 以"核心发现与收束（讨论 heuristic 强基线、regime map 的解读、INT4 open question）、局限性、未来工作、结语"四节结构整合 discussion 与 conclusion，给出完整的论文收束（见图 ② 框架总览）。

### 2.5 引用图表

- Figure ①（§1.2 末，理论动机图）
- Figure ②（§1.4 末，framework overview）

### 2.6 写作注意点

- **不写**："we propose a novel quantization method" → **改写**："we revisit KV quantization through a behavior-centric lens"
- 不给 Mistral 具体 cov80 数字（留给 Ch4）
- Hook 预留：**不需要在 intro 预告 §13 Hook**（激活再加 contribution 条目）

---

## 3. Ch2 Related Work（~1500 字 / ~2 页）

### 3.1 结构

| 节 | 目标 | 长度 |
|---|---|---|
| §2.1 KV Cache Compression Overview | 问题域 + 两条路（pruning vs quantization） | ~300 字 |
| §2.2 Quantization Methods | KIVI / KVQuant / TurboQuant / NVFP4 | ~500 字 |
| §2.3 Budget Allocation & Adaptive | KVTuner / adaptive approaches | ~300 字 |
| §2.4 Our Positioning | 三层关系 + differentiation | ~400 字 |

### 3.2 §2.2 KIVI 段草稿（最关键段落，~200 字）

> KIVI \citep{kivi2024} 在 K per-channel + V per-token 的非对称 INT4 格式下运行 absmax/min 动态校准，是目前 INT4 KV Cache 量化的强 baseline。本文与 KIVI 共享相同 cache format，差异在校准哲学：KIVI 使用运行时 absmax/min 实现动态贴合；本文提出的 RoleAlign 使用离线 behavior-guided KL search 生成静态 percentile。
>
> 这一差异的影响可能与量化架构耦合：我们的跨模型实验显示（§4.2），在同 format 下，behavior-guided 静态校准达到与 KIVI 可比的质量（同任务 ±1-3%，quality 略优、PPL 略弱、Needle 持平）。更重要的是，KIVI 本身不提供 layer-wise budget allocation，而我们以同一 behavior profile 作为输入，进一步构造了 allocator（§3.3）和 AutoK（§3.4）——这在 KIVI 的原设计之外拓展出一层能力。

### 3.3 §2.4 Positioning 段要点

- 把 KIVI 作为**核心 baseline**；其他 low-bit 方法作为 related direction
- 不直接对比 activation / weight 量化
- 不做 attention approximation 对比
- 三层关系明述（见 thesis_story §12.4）：format 同 / calibration 不同 / allocator 扩展
- 【Hook 条件】若 §13 激活，在 §2.4 末尾加一句指向 §2.5 formal compare

### 3.4 写作注意点

- **不贬低 baseline**：KIVI 必须被描述为 "state-of-the-art static counterpart"
- **明确 differentiation**：三层关系（format 同 / calibration 不同 / allocator 扩展）
- Hook 语言："future per-prompt routing" 放 §6，不在这里展开
- 引用标注：所有 KIVI/KVQuant/TurboQuant/KVTuner 必须有 bib entry（检查 thesis/references.bib）

---

## 4. Ch3 Method（~4000 字 / ~6 页）

### 4.1 结构

| 节 | 目标 | 长度 |
|---|---|---|
| §3.1 Problem Formulation | attention 误差分解 + 假设 H | ~600 字（含公式） |
| §3.2 Behavior-Guided Calibration | 目标函数 + INT8 + INT4 instantiation | ~1500 字 |
| §3.3 Behavior-Guided Allocator | layer-wise + role-aware 扩展 | ~1000 字 |
| §3.4 AutoK | profile-guided budget proposer | ~600 字 |
| §3.5 Summary | framework 总览（图 ② 复用） | ~300 字 |

### 4.2 §3.2 核心段落（INT4 三层诚实分析，~400 字）

> 将第一层原则推进到 INT4 时，我们首先尝试把 INT8 的对称量化方案直接迁移。实验表明这一简单迁移效果不足（详见 §4.2）。我们随后采用了与 KIVI 同构的 K per-channel + V per-token 非对称格式，配合 behavior-guided 离线 percentile 搜索，得到 RoleAlign（`int4_ours_asym`）。
>
> 在 Ch4 §4.2 的跨模型对比（表 T2）中，RoleAlign 与 KIVI 呈现可比性——quality 相当或略优、PPL 略弱于 KIVI、Needle 持平。我们的解读包含三层：
>
> - **(L1, 事实)** 在相同协议下 INT4 RoleAlign 的 quality 略优于或相当于 KIVI。
> - **(L2, 经验解释)** 在低比特量化中，K per-channel / V per-token 架构的选择可能比静态 vs 动态校准哲学的差异贡献更大的影响。
> - **(L3, 开放猜想)** 若此观察成立，决定 INT4 表现的主要因素可能是量化架构而非校准策略——这一点需要未来的 pure-architecture ablation 进一步验证。
>
> 我们将此作为 open question 明确留在 §5.3 Discussion。

### 4.3 §3.3 Allocator 段要点

- 从 calibration 的副产品（per-layer sensitivity profile）自然过渡
- 定义基础 layer-wise allocator：给定总预算，把高 bits 分配给 top-k 高敏感度层
- 给定 policy JSON 格式定义（输入：每层 (k_bits, v_bits)）
- Role-aware 扩展（L2 Phase A）：K 和 V 分开分配；当前实现可行但未超越 strongest auto-k（诚实标记）
- 【Hook 条件】若 §13 激活：在 §3.3 末尾加一句 "see §3.5 for matched-budget formal compare with KIVI"

### 4.4 §3.4 AutoK 段要点

- **动机**：fixed-k 跨模型不稳 + regime 真实 → 每模型手工扫不现实
- **方法**：给定 behavior profile，用 coverage 阈值（如 cov80）选择预算区间
- **定位**：framework 的自然扩展，不是 universal allocator
- 定义 cov80：按 sensitivity 降序累计到 80% 时的 k 值

### 4.5 §3.5 Summary 段要点

- 图 ② 框架图复用
- 一句话：behavior 原则 → calibration / allocation 两层 → AutoK 扩展 → 实验验证（Ch4）

### 4.6 写作注意点

- **不过度数学化**：INT8 calibration objective 给公式即可，不必 full derivation
- **RoleAlign 名字要 consistent**：定义在 §3.2.2，Ch4 复用
- Hook 语言：§3.5 末尾可预告"§4 呈现的 cross-model 结果在 §3.3 allocator 框架下展现出一张 regime 地图"
- 公式编号贯通：(1) attention → (2) error decomp → (3) behavior objective → ...

---

## 5. Ch4 Experiments（~5000 字 / ~8 页）⭐主章

### 5.1 结构

| 节 | 目标 | 长度 |
|---|---|---|
| §4.1 Setup | 模型 / 任务 / 评测 / clean-provenance pin | ~400 字 |
| §4.2 INT8 Canonical Path + INT4 vs KIVI | Table T1 + Table T2 | ~800 字 |
| §4.3 Cross-Model Compare & Pareto | Table T3 + Figure ⑦ + Figure ⑧ | ~1500 字 |
| §4.4 AutoK & Prompt-Adaptive | AutoK 总览 + Prompt-adaptive weak/mixed | ~800 字 |
| §4.5 Per-Model Case Analysis | Mistral / 3B / 1.5B / 14B | ~1000 字 |
| §4.6 7B Supporting Regime | aggregation-split 简述 | ~500 字 |

### 5.2 §4.1 Setup 必须讲清的 7 件事

1. **Models**：Qwen2.5-{1.5B, 3B, 7B, 14B}-Instruct / Llama-3.1-8B-Instruct / Mistral-7B-Instruct-v0.3
2. **Tasks**：5 LongBench tasks（narrativeqa / hotpotqa / gov_report / dureader / lcc）
3. **Protocol**：clean-provenance pin `ddada19`，md5-locked runtime files（见 MANIFEST）
4. **Calibration**：3B / 14B / Mistral-7B regen at pin；1.5B / 7B / 8B cp from exploratory with ledger
5. **Metrics**：task-level F1 / Rouge-L / BLEU；aux: PPL / Needle / RULER / TTFT / TPOT / kv_cache_mem_mb
6. **Baselines**：KIVI（static）按 §2.2 定义的 strongest fair config
7. **Disclaimer**：所有正文数字来自 Level 5 clean-provenance；exploratory 数据明确标记为 "exploratory only / not for Gate"

### 5.3 §4.3 核心段落草稿（regime 地图 readout，~400 字）

> 表 T3 给出 4 模型 × 4 policy × 3 task 的跨模型 compare（clean-provenance pin=`ddada19`）。我们并未观察到跨模型的单一最优 policy：在 Qwen2.5-1.5B 上，`bakv_k1` 胜出；在 Qwen2.5-3B 上，`bakv_k1` 同样胜出但原因与 1.5B 不同（详见 §4.5.2 的 early-layer rescue）；在 Llama-3.1-8B 上，`bakv_k11` 与 `heuristic_k11` 接近；在 Mistral-7B 上，`bakv_auto_cov80_max` 显著胜出（详见 §4.5.1）。
>
> 这种跨模型 best-policy 异质性，在图 ⑦ 的 Pareto 视图中得到进一步印证：每个模型在 quality × kv_cache_mem_mb 空间里呈现出不同的 front shape，7B 的 `uniform_int4` 甚至表现出明显的 quality cliff（naive 分配的失败样例，红色标注）；Mistral 的 `bakv_auto_cov80_max` 则占据 Pareto-dominant 区域。
>
> 我们把这种异质性明确写作一个经验发现：**allocator 的真实现实不是"寻找跨模型统一最优"，而是一张由 (family, scale, task) 共同决定的 operating regime 地图**。图 ⑧（regime map viz） 以 per-model best-policy 方式总结了这张地图，可见 5 行不共享同一 best policy——这既是本文 C3 的核心证据，也是后续 Ch5 讨论 heuristic 强基线地位的根据（§5.1）。

### 5.4 §4.4 AutoK + Prompt-Adaptive 段要点

- AutoK 在 Pareto top tier 上的分布（引表 T4 / 图 ⑦ Mistral）
- Prompt-adaptive 5-task matrix: mean 输 fixed-k 0.30，1/5 task 独立赢（lcc +0.40）
- **明确写成 weak/mixed**：Gate C weak/mixed verdict；selector 仍是 task-bucket fallback
- 详细数据指向 Appendix A（5-task matrix）+ Appendix B（off-protocol 1.5B/7B）

### 5.5 §4.5 Per-Model Case（4 小节各 250 字）

**§4.5.1 Mistral-7B**（引表 T4）：auto-k cov80=14.76，core+extend 全覆盖 4/5 task 胜出；discussion 定位为 "strongest single-family positive case for AutoK"

**§4.5.2 Qwen2.5-3B**（引表 T5）：`bakv_k1` (layer 0) vs `heuristic_k1` (middle layer) 在某 task 上差异剧烈，揭示小模型早层脆弱性；写成 "early-layer rescue regime"

**§4.5.3 Qwen2.5-1.5B**（与 3B 合讲 1 段）：与 3B 同向趋势，支持 early-layer 敏感性是小模型的结构特征（非独立主张，supporting）

**§4.5.4 Qwen2.5-14B**（引表 T6）：top-3 policy within ~2% relative，无 stable winner；写成 "top-tier but no stable single winner"

### 5.6 §4.6 7B Supporting 段草稿（~300 字）

> 除主矩阵外，我们在 7B 的诊断数据（来自 exploratory `phase2_c2b_local`，Level 2）中观察到一个 supporting regime case：**budget-aggregation coupling**。附录（Level 2 supporting） 显示在 bakv allocator 下，k=1 时 mean aggregation 优于 max，而 k=5 时 max 反超 mean——这一 split 说明 allocator 的行为不仅依赖 budget，还与 aggregation 选择交互。由于该观察来自 Level 2 exploratory 数据，我们将其作为 supporting case 而非主论点，用以支持 §5.2 的 regime map 讨论。

### 5.7 写作注意点

- **每个 per-model 子节控制在 250 字内**，避免铺开
- **Table T3 必须进正文主表位**（不能移附录），它是 C3 的视觉证据
- **Figure ⑦ 必须进正文主图位**
- Hook 预留：§4.2 末尾 + §4.3 末尾各留 LaTeX `%` 注释标记 "§2.5/§3.5 hook position (if activated)"
- 所有跨 model 数字在 Ch4 给出，Ch5 讨论时不再重复数字

---

## 6. Ch5 Conclusion draft — Part 1：核心发现 / 局限 / Future Work（对应旧 ch5_conclusion.tex §1-§3）

### 6.1 结构

| 节 | 目标 | 长度 |
|---|---|---|
| §5.1 Heuristic as Strong Baseline | 正面承认 | ~500 字 |
| §5.2 Regime Map Interpretation | 跨模型异质性的解读 | ~700 字 |
| §5.3 INT4 vs KIVI Open Questions | 架构 vs 校准的未解耦问题 | ~400 字 |
| §5.4 Limitations | 5 条诚实的 limitations | ~500 字 |
| §5.5 Broader Implications | 对 KV Cache 社区的启示 | ~400 字 |

### 6.2 §5.1 Heuristic 段草稿

> 我们的实验反复呈现一个结果：heuristic（等距位置保护）是一个非常强的 baseline——它在多个模型上与 behavior-guided allocator 接近，在某些 task 上甚至反超。我们认为这不是需要 explain away 的现象，而是 framework 自身意义的体现。
>
> 如果 behavior-guided allocator 仅靠"击败弱 baseline"来成立，它的贡献会非常脆弱。而 heuristic 作为强 baseline 的事实，反而把论文的贡献从"方法数字更高"推进到"**揭示结构分区**"这个更根本的层次：在多个模型上 heuristic 与 BAKV 的接近，本身就构成 regime map 的证据——在某些 (model, task) 区间里，"保护哪些 k 个位置"的选择空间很窄，无论用 behavior profile 还是位置启发式，top-k 集合都会落到相似位置。这是一个有价值的结构观察，而不是方法失败。

### 6.3 §5.2 Regime Map 段要点

- 引图 ⑧（regime map viz）（per-model best policy）作为 regime 地图的总结表
- 3 个 regime 解读：
  - **Small scale regime**（1.5B / 3B）：`bakv_k1` 胜，但 3B 的 early-layer rescue 是模型特异性，不是"小模型通用规律"
  - **Mid scale regime**（7B / 8B）：top-tier 聚集 k=11 附近，多 policy 接近
  - **Large scale regime**（14B）：top-tier 内无稳定赢家
  - **Cross-family**（Mistral）：AutoK 独立正面案例
- 明确声明：regime 的存在**不否定** behavior framework 的价值，而是揭示其作用方式

### 6.4 §5.3 INT4 vs KIVI Open Questions 段草稿

> 在 §4.2 的 INT4 跨模型对比中，RoleAlign 与 KIVI 呈现可比性。这一观察指向一个在本文实验范围内尚未完全解耦的 open question：**低比特 KV 量化的主要决定因素究竟是量化架构（K per-channel / V per-token），还是校准策略（静态 behavior-guided vs 动态 absmax/min）？**
>
> 由于 RoleAlign 与 KIVI 共享 format，本文的对比只是揭示"同 format 下校准哲学差异有限"，但这不等于"校准策略不重要"——未来需要 pure-format ablation（同校准、不同 format）与 pure-calibration ablation（同 format、不同校准）的正交实验才能完整回答。
>
> 【条件段】若 §13 Hook 激活到 L1/L2，`rolealign_static` 与 `kivi_style` 的 matched-budget 对比会直接给出 "static calibration 的独立增益" 的正式证据，届时本段的 open question 可以具体化为更明确的 claim。

### 6.5 §5.4 Limitations 5 条

1. **实证范围**：5 model × 5 task 不覆盖所有 long-context 场景（如 reasoning / code completion long form / multimodal）
2. **INT4 vs KIVI 未完全解耦**：架构 vs 校准的相对贡献需 pure ablation（§5.3 open question）
3. **AutoK 仅在静态层面验证**：prompt-adaptive 的局部正点（lcc）未被成熟的 per-prompt selector 实现（见 §6.2 future work）
4. **Clean-provenance pin 固定**：可能不完全覆盖运行时漂移；md5-locked 保证审计但不保证泛化
5. **【条件】Allocator vs KIVI 未做 matched-budget formal compare**：见 §13 Hook；若该实验完成且达 L1/L2，本 limitation 可从列表删除

### 6.6 §5.5 Broader Implications 段要点

- 对 KV Cache 社区：behavior 视角可能启发其他 cache reduction 路径（pruning / streaming）
- 对量化社区：以下游 function preservation 为校准目标的一般化
- 对 deployment：heuristic 足够强意味着不需要对每个模型都做复杂 calibration（实用性启示）

### 6.7 写作注意点

- **§5.1 必须正面承认 heuristic**，不要 reframe 成劣势
- §5.4 写 5 条 limitation 是诚实度信号，不要只写 3 条（评审期待范围 4-6）
- Hook 预留：§5.3 和 §5.4 都有 Hook 相关 footnote
- Discussion 不重复 Ch4 具体数字；只做解读

---

## 7. Ch5 Conclusion draft — Part 2：C1-C3 Summary + 结语（对应旧 ch5_conclusion.tex §4；同时是 Ch1 §1.3 contribution 段的 draft source）

### 7.1 结构

| 节 | 目标 | 长度 |
|---|---|---|
| §6.1 Summary of Contributions | C1 / C2 / C3 回顾 | ~400 字 |
| §6.2 Future Work | 3 条方向 | ~400 字 |

### 7.2 §6.1 草稿

> 本文从 attention 误差传播分析出发，提出以 behavior 为中心的 KV Cache 量化统一原则，并通过两层实例化与跨模型实证将其验证为一个可用的 framework。
>
> (**C1**) 框架上，我们展示 behavior 原则同时贯通 calibration（§3.2）与 allocation（§3.3-§3.4）两层，使两者不再是独立优化问题，而是共享同一 behavior sensitivity profile 的两层决策。
>
> (**C2**) 方法上，INT8 canonical path 与 FP16 近乎无损（mean Δ=+0.02）证明这条思路在工程上可闭环；INT4 RoleAlign 在更低比特下与 KIVI 可比，说明该原则不局限于宽松量化场景。AutoK 作为 profile-guided budget proposer，是 framework 自然长出的扩展机制。
>
> (**C3**) 实证上，跨 5 模型、5 任务的 clean-provenance 实验揭示出一张 family/scale/task-dependent 的 regime 地图——Mistral 给出 AutoK 最清晰的正面案例，Qwen2.5-3B 呈现小模型的早层结构瓶颈，Qwen2.5-14B 呈现高质量区间的多策略共存。Heuristic 作为强基线被正面承认。这一发现让 behavior-guided allocator 的价值从"击败弱对手"升级到"揭示结构分区"。

### 7.3 §6.2 Future Work 3 条

1. **Per-prompt routing**：L2 Phase C 上 lcc 的局部正点提示这条方向有信号（见 §4.4 / Appendix A），未来工作可探索真正的 per-prompt selector，超越当前的 task-bucket fallback 实现。
2. **更成熟的 role-aware allocator**：K/V 非对称分配在当前调参水平下可行但未熟（见 §3.3），K 和 V 的 layer-wise 联合优化值得作为专项工作。
3. **【条件】Allocator vs KIVI matched-budget formal compare**：见 §13 Hook；若未来完成该正式对比实验，可以把 framework 的系统级优势固化为正式主张，从而替代当前 §5.3 的 open question。

### 7.4 写作注意点

- **不写**"we proved behavior is the optimal principle" → **改写**"we demonstrated behavior as an organizing principle"
- 不在 conclusion 提任何具体数字（除了最具标志性的 Δ=+0.02）
- Future Work 写 3 条足够，不堆砌
- 最后一段可用故事 §7 正向收束的精简版作为 closing sentence

---

## 附 A. 草稿使用指引

### A.1 改 thesis 的推荐顺序（依赖顺序）

1. **先写研究背景 + 方法 + 实验**（Ch1 §1.1/§1.2/§1.4 + Ch2 + Ch3 + Ch4）；**Ch1 §1.3 + Ch5 整章 + Abstract 放最后**（contribution 与 conclusion 互为镜像）
2. **再写 Ch3 + Ch4 主体**（Step 2-3）：方法 + 实验
3. **然后写 Ch2 + Ch5**（Step 4）：related work + discussion
4. **最后写 Abstract**（Step 5）：等所有章节定稿后

### A.2 写任何章节前的 checklist

- [ ] 已读 `thesis_story_20260420.md` §10 章节映射确认对应关系
- [ ] 已读 `thesis_story_20260420.md` §11 图表清单确认引用哪些图表
- [ ] 已读 `thesis_story_20260420.md` §15 术语冻结表确认用词
- [ ] 已读本文档对应 §N 确认草稿
- [ ] 已查 `data_asset_inventory_20260420.md` Part B 确认数据 Level

### A.3 引用数据时的 Level 纪律

- **Level 5**（clean_rerun）→ 正文主表 / 主图
- **Level 4**（l2_pareto）→ 正文 Pareto 主图
- **Level 3**（phase1_official / l2_kv_asymmetric / l2_prompt_adaptive/8b）→ 历史起点 / 扩展小节 / Gate C mixed 承接
- **Level 2**（phase2_c2b_local / off-protocol）→ 附录 / supporting regime / future work seed
- **Level 1**（artifacts / archive）→ Methods 可追溯性 / 防叙事回滑参考

---

## 附 B. 关键数字与术语清单

正文中会多次出现的关键元素，**值必须一致**：

| 元素 | 值 | 出现章节 |
|---|---|---|
| int8↔fp16 Δ | mean Δ=+0.02 | Ch4 §4.1 / Abstract / Ch5 §5.4 |
| Mistral cov80 | 14.76 cross core+extend | Ch4 §4.5.1 / Ch5 §5.4 |
| Pin | `ddada19` | Ch4 §4.1 / Abstract（"clean-provenance"） |
| Model 数 | 5（不含 7B）或 6（含 7B supporting） | Abstract / Ch4 §4.1 |
| Task 数 | 5 LongBench | Abstract / Ch4 §4.1 |
| Policy 数（主表） | 4 compare（uniform / bakv_fixed / heuristic / bakv_auto_cov80） | Ch4 §4.3 |
| Prompt-adaptive 结果 | 5-task mean: fixed 10.027 / auto 9.854 / prompt 9.725；1/5 独立 win (lcc) | Ch4 §4.4 / Appendix A |
| 3B early-layer task | narrativeqa（或 best-demonstrating task，Ch4 §4.5.2 填入） | Ch4 §4.5.2 |

### B.1 术语中英对照（复用 thesis_story §15）

关键术语必须严格使用本清单，避免同义替换：

- 行为 / attention behavior
- behavior-guided static calibration
- behavior-guided budget allocator
- AutoK / profile-guided budget proposer
- operating regime / regime map
- canonical validation path
- static vs dynamic calibration
- matched INT4 budget

---

## 附 C. 修订记录

**2026-04-20 初版**：
- 本文档初建
- 7 个 draft section（Abstract / Ch1 / Ch2 / Ch3 / Ch4 / Ch5 Part 1 / Ch5 Part 2）—— **对应旧 5 章制（Ch1-Ch5），§6/§7 是 Ch5 的两部分 draft source，非独立论文章节**
- 每章 outline + 1-2 个关键段落 draft + 引用图表 + 写作注意点
- 附 A 使用指引 + 附 B 数字术语清单 + 附 C 修订记录
- 配套 `thesis_story_20260420.md`（叙事主线）+ `thesis_story_20260420.md` §16（图表 spec）+ `data_asset_inventory_20260420.md`（数据资产）

### Hook 激活日志（Hook 激活后 append）

- _（暂无条目。若 §13 Hook 激活，追加 §2.5 / §3.5 写作草稿在本小节）_

---

**文档结束。**
