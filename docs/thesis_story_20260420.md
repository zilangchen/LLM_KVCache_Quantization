# 论文升级故事线（2026-04-20）

**日期**：2026-04-20
**作者**：Claude（基于与用户 + Codex 的多轮讨论整理）
**文档身份**：论文升级阶段的**叙事 source-of-truth**

---

## 0. 文档用途

这份文档是论文升级后的**叙事主线文件**。后续改 `thesis/chapters/*.tex` 的叙事起点以本文件为准。

### 它承担什么

- 持久化论文升级后的 7 段故事主线（§1-§7）
- 固化 L2 三个 Phase 在故事中的精确嵌入位置
- 固化各模型（Mistral / 3B / 1.5B / 14B / 7B）在故事中的角色分工
- 给出写作纪律（§8）与数据引用指引（附表）

### 它不承担什么

- 数据结构 / 目录分布 / 文件数量 → 见 `docs/data_asset_inventory_20260420.md`
- 什么能写 / 不能写的口径边界 → 见 `docs/freeze_20260419.md`
- 运行时论文升级状态 → 见 `docs/thesis_upgrade_live_plan.md`
- 实验队列状态 → 见 `docs/mainline_execution_queue.md`

### 维护规则

**只 append，不 rewrite**。如有新判断或修正，在文档末尾 append 一个"修订记录"段，不改 §1-§8 的既定叙事。

---

## 1. 起点：从 attention 误差传播分析推出的假设

论文起点不是经验观察，而是一个从 attention 计算过程推出的理论分析。

标准 attention：

$$z_i = \frac{q^\top k_i}{\sqrt{d}}, \quad a_i = \mathrm{softmax}(z)_i, \quad o = \sum_i a_i v_i$$

KV Cache 量化后输出误差分解：

$$\hat o - o = \underbrace{\sum_i (\hat a_i - a_i) v_i}_{\text{K 误差 → attention 分布扭曲}} + \underbrace{\sum_i \hat a_i (\hat v_i - v_i)}_{\text{V 误差 → content 聚合偏移}}$$

由此提出一个**理论动机驱动的假设**（theoretically motivated hypothesis，非定理）：

> 在 KV Cache 量化中，若以注意力行为的保持度作为优化对象，相比以数值范数作为优化对象，更贴近模型真实的功能损伤。

整篇论文是一层一层地验证这个假设。

### 关键措辞

- 不说"我们发现 behavior 更重要"
- 改说"我们从 attention 公式出发提出一个可验证的假设"
- 前者是事后总结，后者才是研究叙事

---

## 2. 第一层：Behavior 作为静态校准原则

### 2.1 INT8 canonical path

INT8 是最干净的验证场景。完成完整闭环：
- behavior-guided 静态校准目标函数
- per-layer scales 校准产物
- 自定义 generate loop + Triton 融合核
- 与 FP16 近乎无损（int8↔fp16 Δ=+0.02）

**INT8 的位置**：不是"最强设置"，而是"规范验证路径"——证明这套方法论能闭环。

### 2.2 INT4 推进到更困难的低比特

过程记录：
1. 直接把 INT8 对称方案迁到 INT4 → 效果很差
2. 引入 K per-channel + V per-token 非对称架构（与 KIVI 同构）+ behavior-guided 离线 percentile → 效果显著改善，接近前沿

**结论**：behavior 原则在 INT4 下仍具备现实意义——前提是量化架构合理。

### 2.3 INT4 略弱于 KIVI 的诚实分析（三层）

| 层 | 内容 | 叙事强度 |
|---|---|---|
| L1 经验事实 | 相同协议下静态 INT4-RoleAlign 略弱于动态 KIVI | fact |
| L2 经验解释 | 低比特下量化架构（K per-channel / V per-token）影响可能大于校准方式 | suggests |
| L3 开放猜想 | 真正决定 INT4 效果的可能是架构本身 | open question → Discussion |

### 2.4 第一层结论

经过 INT8 + INT4 两层验证，可以稳妥地说：

> Behavior 原则作为静态校准原则是有现实意义的——它已经足够成为一个合理、可执行、被实证支持的设计原则。

这不是"behavior 已严格证明优于所有数值代理"。

---

## 2.5 【预留接口】INT4 层面 Allocator vs KIVI 正式对比

> **状态**：预留接口（hook）。是否激活取决于 `.agents/execplans/2026-04-20_allocator-vs-kivi-claim-package.md` 的执行进度（见 §13）。
> **激活条件**：实验完成且结论达 L1（systematic win）或 L2（quality win + non-inferior systems）。
> **未激活时**：§2.3 的三层诚实分析（L1 事实 / L2 suggests / L3 open question）保留为第一层的底线写法，不触发任何其他章节改动。

### 2.5.1 实验设计要点

- 4 个对比系统：`kivi_style` / `rolealign_static` / `rolealign_allocator_fixed_eqmem` / `rolealign_allocator_auto_eqmem`
- 同 INT4 cache format（K per-channel + V per-token）
- Matched KV memory（±3% 硬约束）
- 5 model × 5 task × {quality, PPL, Needle, RULER, TTFT, TPOT, memory}

### 2.5.2 四级可能结论

| 级 | 条件 | 对本节的影响 |
|---|---|---|
| L1 systematic win | quality win + robustness non-inferior + systems non-inferior | 本节 + §3.5 + §9.2 C2 升级 + §11 表 9 全部激活 |
| L2 quality win + non-inferior systems | quality 系统胜 + latency/memory 不输 | 本节写 quality 级主论点；§3.5 allocator 级从属 |
| L3 Pareto advantage | 在 Pareto 前沿占据更好位置 | 本节弱化为 Pareto advantage 叙述 |
| L4 mechanism-only | 仅 allocator 增量可辨识 | 本节删除，证据进 Discussion |

### 2.5.3 激活时的论文写法起始句模板

> "为进一步检验 behavior-guided 校准在 matched INT4 KV memory budget 下相对 KIVI-style 的系统性关系，我们在 ±3% memory band 内对 `{kivi_style, rolealign_static, rolealign_allocator_*}` 进行 5 model × 5 task 的正式对比。[结果表述] 表 9 给出完整数据。"

---

## 3. 第二层：Behavior 扩展到预算分配

### 3.1 从 calibration 自然过渡

Calibration 的副产品是每层对 behavior 的敏感度画像。于是一个自然问题出现：

> 既然知道哪些层更敏感，为什么还要全层同预算？

这就是 allocator 的起点——**不是另起一个分支，是同一原则换一个层次**。Behavior 在第一层回答"怎么量化"，在第二层回答"哪里该多保护"。

### 3.2 Allocator 的真实收获是 regime 地图

Allocator 实验没有给出跨模型统一的 fixed-k 最优，而是给出了：

> 不同 family / scale / task 落在不同的 operating regimes。

Allocator 的贡献变成了：

> **把 allocation 从"手工调参问题"推进成"结构识别问题"。**
> Behavior-guided allocator 的价值在于揭示这张结构地图，而不是在地图上插一面旗。

### 3.3 【L2 Phase A 嵌入】role-aware 粒度扩展

L2 Phase A（K/V asymmetric）把 allocator 颗粒度从 per-layer 进一步细化到 per-role。

**叙事位置**：本章末尾的粒度扩展小节。

**定位（三层诚实度）**：
- **事实层**：在 role-aware 颗粒度下跑通、呈现与 layer-wise 一致的 regime 结构
- **比较层**：当前调参水平下尚未超越 strongest auto-k
- **开放层**："role-aware 是有潜力的方向，但方法未熟"

### 3.4 【L2 Phase B 嵌入】Pareto 评估维度升级 ⭐

L2 Phase B（Pareto）把 allocator 研究问题从"寻找单目标最优 k"升级到"理解 quality × cost 的 Pareto 结构"。

**叙事位置**：本章第二个小高潮（**主图应进正文主图区**）。

**撑起的两个论点**：
1. **allocator 问题是真实的**：
   7B uniform_int4 在 Pareto 空间里直接崩坏——这不是抽象"量化降质"，而是一个可视化的、明确的结构事实。
2. **AutoK 作为扩展有真实信号**：
   auto-k 在多模型上稳定进入 top tier，Mistral 上是最明确正例——这给第三层（§4）的 AutoK 提供硬证据。

---

## 3.5 【预留接口】Allocator 维度上 vs KIVI 的正式主张

> **状态**：预留接口（hook），与 §2.5 共享同一套实验数据但读数维度不同（详见 §13）。
> **激活条件**：实验完成且结论 ≥ L2。
> **未激活时**：§3.4 的 Pareto 叙事已足够支撑第二层论点，跳过本节。

### 3.5.1 与 §2.5 的分工

| 维度 | §2.5（第一层 calibration） | §3.5（第二层 allocation） |
|---|---|---|
| 读数焦点 | `rolealign_static` vs `kivi_style` | `rolealign_allocator_auto_eqmem` vs `{kivi_style, rolealign_static}` |
| 回答的问题 | behavior-guided 静态校准是否 systematic 强于 KIVI 动态校准 | allocator 能否在 static RoleAlign 之上给出可辨识的独立增益 |
| 对 framework 的影响 | 加强 C2 method instance | 加强 C1 framework 的贯通性论点 |

### 3.5.2 激活时的论文写法起始句模板（≥ L2）

> "在 matched INT4 KV memory budget 下，behavior-guided allocator 在 [N] 个模型 / [M] 个任务上给出相对 `kivi_style` 的 [quality / Pareto] 优势。ablation（附录）表明 allocator 贡献了约 Δ 个百分点的独立增益，与 `rolealign_static` 的静态校准增益可分离。"

### 3.5.3 未激活时

故事线回到 §3.4 原始表述——allocator 的真实收获是 regime 地图而非 universal winner，L2 Phase B 的 Pareto 图已足够撑起 §3 的论点。

---

## 4. 第三层：AutoK 作为自然扩展

### 4.1 为什么会有 auto-k

fixed-k 跨模型不稳 + regime 真实存在 → 自然问题：

> 难道每上一个新模型都要手工扫 k ∈ {1, 3, 5, 7, 9, 11}？

AutoK 用 behavior profile 本身提示合理的预算区间，让搜索空间大幅收窄。

### 4.2 AutoK 的正确定位

- **不是**：全文第三个主方法
- **不是**：下一代普适 allocator
- **不是**：证明 framework 的关键证据
- **是**：fixed-k 不稳 + regime 明显时的 profile-guided budget proposer
- **是**：framework 的自然扩展，不是 framework 本身
- **是**：已观察到有意义的正面信号、仍有明显优化空间的方法组件

### 4.3 【L2 Phase C 嵌入】从静态 AutoK 到 Prompt-adaptive 的尝试

**叙事位置**：本章末尾的开放段 + §6 future work。

**口径**：

> AutoK 解决了"模型级预算建议"的问题，但它仍是静态策略。一个自然的下一步问题是能否把选择粒度推到 prompt 级——这引出 Prompt-adaptive 的探索。

**当前证据状态**（基于 L2 Phase C 官方 8B × 5 tasks）：
- prompt_adaptive mean = 9.725 输给 fixed_k mean = 10.027（-0.30）
- 5 task 中 3/5 错选 fallback / 1/5 tie / 1/5 独立赢（lcc, +0.40）
- selector 当前实现仍是 task-bucket 级别，**尚未构成 per-prompt routing 成立的充分证据**

---

## 5. 模型角色分工

各模型在新故事里不是一条独立实验，而是**在主故事中扮演一个有明确职责的角色**。

### 5.1 Mistral-7B —— AutoK 的 strongest positive case

**核心证据**：官方 cov80=14.76 跨 core+extend task；Pareto top tier 定位明确。

**它在故事里回答的问题**：
> AutoK 这条路，在至少一个明确的 family 上，能够以论文可接受的强度给出正面证据。

**它不回答**：auto-k 已普适胜利（错误外推）。

### 5.2 3B —— 小模型的早层结构瓶颈

**核心证据**：首层保护极其关键；中层 heuristic 可能灾难性失败。

**它在故事里回答的问题**：
> Allocator 效果与模型内部结构瓶颈强相关，不同模型有非常不同的脆弱点。

**它不回答**：所有小模型都需要早层保护（需结合 1.5B 综合判断，见 §5.3）。

### 5.3 1.5B —— 小模型趋势的辅助证据

**核心证据**：在低预算 regime 下呈现与 3B 同向的早层敏感性趋势。

**它在故事里的写法**（与 3B 合起来）：

> 3B 明确呈现早层瓶颈现象；1.5B 在其低预算 regime 下呈现同向趋势。两者共同指向小模型在早层保护上的敏感性，是一个值得关注的结构特征。

**不独立写成主张**。

### 5.4 14B —— 大模型上仍保持高质量区间

**核心证据**：多策略进 top tier，无单一稳定赢家。

**它在故事里回答的问题**：
> 这套方法在大模型上会不会失效？

**答案**：在更大规模上，behavior-guided 的调参方式依然能稳定落在高质量区间；虽然没有单一稳定赢家，但整个 top tier 里都能看到 behavior-guided 方案的身影。

**它不回答**：14B 上某策略胜出（错误写法）。

### 5.5 7B —— Aggregation-split 的 supporting regime case

**核心证据**：k=1 下 mean 显著优于 max；k=5 下反过来（max 优于 mean）。

**它在故事里的位置**：
> Allocation 的结果会沿 aggregation 维度发生**结构分裂**——一个具体可辨识的结构现象。

**定位**：supporting regime case in main text（正文保留，不作为主轴）；需引用 `results/phase2_c2b_local/` 的诊断数据。

---

## 6. 边界与未来方向

### 6.1 Heuristic 作为强基线的地位

**必须在正文正面承认**：

> Heuristic（等距位置保护）在很多场景下是一个非常强的 baseline。

**为什么这是好事**：它让 behavior-guided allocator 的贡献无法靠"打败弱基线"成立——必须靠"**揭示结构分区 + 在特定 regime 下自然匹配**"这个更难的故事成立。而这正是本论文真正想讲的故事。

### 6.2 Per-prompt routing —— Future Work（由 L2 Phase C 指向）

**引入方式**：
> 既然不同任务落在不同 regime，能否把选择粒度推到 prompt 层面做在线 routing？L2 Phase C 的初步实验给出该方向存在局部信号的提示（如 lcc 上的独立 prompt-level win），但当前 selector 本质仍是 task-bucket 级别的策略路由，尚未构成对 per-prompt routing 成立的充分证据。更成熟的 per-prompt selector 留作 framework 的下一步开放方向。

### 6.3 更成熟的 role-aware allocator —— Future Work（由 L2 Phase A 指向）

Role-aware allocator 的粒度扩展已跑通，但尚未超越 strongest auto-k；更成熟的 role-aware 方法（如 K/V 非对称 + layer-wise 联合优化）留作下一步。

### 6.4 更系统的 quality-cost Pareto allocator —— Future Work（由 L2 Phase B 指向）

Pareto 层的发现（7B uniform_int4 崩坏 / auto-k top tier 分布）提示 allocator 可以直接以 Pareto front 为目标函数，而不是只优化 quality。

---

## 7. 整篇论文的正向收束

> 本文从 attention 误差传播分析出发，提出一个假设：在 KV Cache 量化中，更贴近模型真实损伤的分析对象是注意力行为。基于这一理论动机，本文首先在静态校准层面引入 behavior-guided 原则，并通过两个量化层次完成初步验证——INT8 证明这套原则能够支撑一条完整可落地的规范验证路径（与 FP16 近乎无损），INT4 进一步证明即便在更困难的低比特区间，该原则在合理的量化架构下仍具备竞争力。在第一层成立的基础上，本文把同一行为原则扩展到预算分配问题，探索 behavior-guided allocator。实验结果揭示出一个更深层的结构现象：allocator 的现实不是一个跨模型统一的最优配置，而是一张由 family、scale、task 共同决定的 operating regime 地图。在这一认识下，AutoK 被自然提出为 profile-guided 的预算建议机制——它是 framework 的扩展，不是 framework 本身。Mistral 给出了这条扩展路径上最清晰的正面案例；3B 揭示了小模型的早层结构瓶颈；14B 说明该思路在大模型上仍能稳定进入高质量区间；7B 则展示了 allocator 内部可见的 aggregation-split 结构分裂；Heuristic 则作为一个强基线，使得 behavior-guided 方法必须靠揭示结构而非打败弱对手来成立。综合来看，本文的贡献不是某个单点方法的普适胜出，而是：提出一个以 behavior 为中心的统一视角，并通过 calibration 与 allocation 两个层次的实证，展示这一视角在 KV Cache 量化问题中的组织力与延展性。

---

## 8. 写作纪律

| 不要写 | 改写成 | 理由 |
|---|---|---|
| "我们发现 behavior 更重要" | "基于 attention 误差传播分析，我们提出假设并通过 ... 验证" | 前者是事后总结，后者是研究叙事 |
| "我们赢了" / "我们的方法最强" | "在 ... 条件下，我们的方案落在 top tier" | 避免 universal claim |
| "我们不是 universal winner" | "我们揭示出一张由 family/scale/task 决定的 regime 地图" | 用正向语言表达边界 |
| "INT8 最强" | "INT8 canonical path 给出最干净的规范验证" | 改变 INT8 的叙事定位 |
| "AutoK 是新方法" | "AutoK 是 framework 自然长出的扩展" | 避免喧宾夺主 |
| "Prompt-adaptive 有效" | "当前 selector 本质仍是 task-bucket 级别，per-prompt routing 留作 future work" | 数据层诚实 |
| "Heuristic 被我们击败" | "Heuristic 是强基线，这让 behavior-guided 的贡献只能靠揭示结构而非打败弱对手成立" | 正面承认 baseline |

### 引用数据的优先级

1. **Level 5**（clean_rerun）→ 正文主表 / 主图
2. **Level 4**（l2_pareto）→ 正文 Pareto 主图
3. **Level 3**（phase1_official / l2_kv_asymmetric / l2_prompt_adaptive/8b）→ 第一层叙事起点 / 扩展小节 / Gate C weak/mixed 承接
4. **Level 2**（phase2_c2b_local / off-protocol）→ 附录 / supporting regime / future work seed
5. **Level 1**（artifacts / archive）→ Methods 可追溯性 / 防叙事回滑参考

（Level 分级详见 `docs/data_asset_inventory_20260420.md` Part C）

---

## 9. Research Questions 与 Contributions

### 9.1 三个 RQ

| RQ | 问题 | 回答 | 证据章节 |
|---|---|---|---|
| RQ1 | 在 KV Cache 量化中，什么样的分析对象比单纯数值误差更贴近模型真实损伤？ | 注意力行为（attention behavior） | §1 理论分析 |
| RQ2 | 以 behavior 为中心的校准原则能否落成一套完整可用的量化系统？ | 能。INT8 canonical + INT4 推进给出完整闭环 | §2 |
| RQ3 | 同一行为原则能否延伸到更高层的预算分配决策？如果能，它揭示了什么结构？ | 能。揭示出 family/scale/task-dependent 的 operating regime 地图 | §3 + §4 + §5 |

### 9.2 三个 Contributions

| # | Contribution | 支撑 RQ | 性质 |
|---|---|---|---|
| C1 | **Framework**：提出以 behavior 为中心的 KV 量化统一原则，贯通 calibration 与 allocation | RQ1, RQ3 | conceptual |
| C2 | **Method instance**：INT8 canonical path（behavior calibration + Triton 融合核）+ INT4 RoleAlign（behavior + K per-channel / V per-token）+ AutoK（profile-guided budget proposer） | RQ2 | methodological |
| C3 | **Empirical insight**：allocator 的真实现实是 family/scale/task-dependent 的 regime 地图；heuristic 是强 baseline 需正面承认 | RQ3 | empirical |

### 9.3 Contribution 叙事纪律

- **C1 是论文的 conceptual spine**，应在 Ch1 intro + Ch5 conclusion（§5.1 核心发现 + §5.4 结语）显眼讲述
- **C2 是论文的 engineering substrate**，用于 Ch3 method + Ch4 experiment section
- **C3 是论文的 research honesty**，用于 Ch5 discussion，不压低 heuristic、不宣称 universal
- 【条件激活】若 §13 Hook 达 L1：C2 增加一条 "systematic superiority to KIVI under matched budget"

---

## 10. 章节映射（故事 §X → thesis/chapters/*.tex）

这张表是 **thesis 改写的入口**。每次打开 thesis/chapters/ 的某个文件前，先查这张表确认对应故事章节。

| 故事章节 | Thesis Chapter | 写作任务 |
|---|---|---|
| §1 理论动机 | Ch1 §1.2 motivation + Ch3 §3.1 problem formulation | 理论分析段 + 公式 + hypothesis 明述 |
| §2.1 INT8 canonical | Ch3 §3.2-3.3 calibration method + Ch4 §4.1 INT8 experiment | 方法细节 + Δ=+0.02 主表（表 1） |
| §2.2 INT4 推进 | Ch3 §3.3 extension to low-bit + Ch4 §4.2 INT4 experiment | 架构选择论证 + INT4 跨模型表（表 2） |
| §2.3 INT4 vs KIVI 三层诚实分析 | Ch4 §4.2 末尾 + Ch5 §5.1 discussion | L1 / L2 进 Ch4，L3 open question 进 Discussion |
| §2.5 【Hook】Allocator vs KIVI | Ch4 §4.2.X（条件段） | 激活时写；未激活时删 |
| §3.1 从 calibration 到 allocation | Ch3 §3.4 allocator method 引入段 | 一段过渡叙事 |
| §3.2 regime 地图 | Ch4 §4.3 cross-model compare main table | clean_rerun Step 2 主表（表 3） |
| §3.3 L2 Phase A role-aware | Ch4 §4.3.X role-aware 小节 | 方向可行但未熟的定位 |
| §3.4 L2 Phase B Pareto ⭐ | Ch4 §4.3 Pareto main figure | Pareto front plot（图 3） |
| §3.5 【Hook】Allocator vs KIVI allocator 维度 | Ch4 §4.3.X（条件段） | 激活时写；未激活时删 |
| §4.1-4.2 AutoK 定位 | Ch3 §3.5 AutoK method + Ch4 §4.4 AutoK experiment | 定义 + 跨模型表现（表 4） |
| §4.3 L2 Phase C Prompt-adaptive | Ch4 §4.4.X + Ch5 §5.X future work | weak/mixed 承接 + lcc 独立点 + future direction |
| §5.1 Mistral | Ch4 §4.5 Mistral detail | strongest positive case（表 4 详细版） |
| §5.2 3B | Ch4 §4.5 + Ch5 §5.2 model-specific observation | early-layer rescue（表 5） |
| §5.3 1.5B | Ch4 §4.5 附带 + 不独立成节 | 与 3B 合讲 |
| §5.4 14B | Ch4 §4.5 + Ch5 §5.2 | top-tier but no stable winner（表 6） |
| §5.5 7B aggregation-split | Ch4 §4.6 supporting case + appendix | 引用 phase2_c2b_local（表 7） |
| §6.1 heuristic 强基线 | Ch4 主表脚注 + Ch5 §5.1 discussion | 正面承认段 |
| §6.2-6.4 Future work | Ch5 §5.3 未来工作展望 | 3 条未来方向 |
| §7 正向收束 | Ch1 §1.3 contribution 段 + Ch5 §5.4 结语（Phase 8 一起写） | 收束段 |
| §8 写作纪律 | **不进论文**，仅 writer 内部纪律 | 检查用 |
| §9 RQ + Contribution | Ch1 §1.3（Phase 8） + Ch5 §5.1（Phase 8） | intro 明述 RQ/C + Ch5 核心发现 summary |
| §12 Related Work 定位 | Ch2 Related Work | 写作蓝本 |
| §13 Hook 说明 | **不进论文**，仅 writer 内部控制 | 决定 §2.5 / §3.5 是否激活 |
| §14 旧论文处理 | **不进论文**，仅改写纪律 | 保留 / 改写 / 删除决策表 |
| §15 术语冻结表 | **不进论文**，但正文用词必须严格遵守 | 贯穿全论文 |

---

## 11. 图表与主表清单（最终方案：8 图 + 9 表 = 17 正文项）

经过 2026-04-20 多轮承重测试，论文最终保留 **8 张正文图 + 9 张正文表 + 4 张附录 + 1 条件项**。每一项都承担"去掉后故事链某节断裂"的独立承重角色。

### 支撑 C1（Framework）

- **图 ①**：Attention error decomposition 示意图（TikZ）—— 对应 §1 理论起点；K 误差→分布扭曲 / V 误差→聚合偏移
- **图 ②**：Framework overview（TikZ）—— 对应 §7 收束；calibration + allocation 两层 + behavior 原则贯通
- **图 ③**：Calibration pipeline（TikZ）—— 对应 §2 方法流程；INT8 KL search + INT4 RoleAlign 两路（去 inv_tau）
- **图 ④**：Behavior sensitivity heatmap (6 models) ⭐—— 对应 §3.2 + §5 签名视觉；跨模型 sensitivity 形状异质

### 支撑 C2（Method instance）

- **图 ⑤**：K/V role mechanism（RULER）—— 对应 §2.2；K-only INT4 vs V-only INT4 的损伤不对称 → 图 ① 理论路径的 empirical 对照
- **表 T1**：INT8 Canonical vs FP16 —— 对应 §2.1；int8↔fp16 Δ=+0.02 硬证据
- **表 T2**：INT4-RoleAlign vs KIVI Cross-Model —— 对应 §2.2-§2.3；quality / PPL / Needle 跨 4 模型
- **表 S3**：RoleAlign vs KIVI 设计差异 —— 对应 §2.2-§2.3；KIVI 对比 hub，三层关系快速索引

### 支撑 C3（Empirical insight，regime map）

- **图 ⑦**：Pareto front plot ⭐⭐—— 对应 §3.4 + §4 + §5.1；quality × kv_cache_mem_mb，3 subplot（7B/8B/Mistral-7B），7B uniform_int4 崩坏 + Mistral auto-k dominant
- **图 ⑧**：Cross-Model Regime Map heatmap —— 对应 §3.2 + §5；5 model × 4 policy types 颜色矩阵，"2 秒看到 5 个不同赢家"
- **图 ⑨**：Quality/PPL vs Scale —— 对应 §5；scale 维度连续趋势图（1.5B → 14B）
- **表 T3**：Cross-Model Compare Main Table ⭐⭐—— 对应 §3.2；4 model × 4 policy × 3 task（clean_rerun Step 2 主表）
- **表 T4**：Mistral AutoK 5-task Detail —— 对应 §5.1；strongest positive case，cov80=14.76
- **表 T5**：3B Early-Layer Rescue —— 对应 §5.2；bakv_k1 vs heuristic_k1 catastrophic gap
- **表 T6**：14B Top-Tier Distribution —— 对应 §5.4；top-3 within ~2% 定量化

### 标准章节元素

- **表 T0**：KV Cache 量化相关工作对比 —— Ch2 Related Work 标准表
- **表 S1**：实验用模型与 GQA 配置 —— Ch4 §4.1 setup 标准表

### 附录（minimal，4 项）

- **附录 P1**：FP16 基线 + 评测协议汇总（reproducibility 标准）
- **附录 P2**：实验软硬件环境（reproducibility 标准）
- **附录 A**：Prompt-adaptive 8B 5-task matrix —— 对应 §4.3 完整数据（正文只给 mean + verdict）
- **附录 B**：Off-protocol 1.5B/7B Prompt-adaptive —— Future-work seed 数据源，**OFF-PROTOCOL 明确标注**

### 【预留条件图表】（受 §13 Hook 控制）

- 若 L1/L2 激活：**表 T9** Allocator vs KIVI matched-budget comparison（§2.5 / §3.5）
- 若 L3 激活：**图 ⑩** Allocator vs KIVI Pareto overlay（基于图 ⑦ 叠加 KIVI 基线）
- 若 L4 激活：**附录表 C** Allocator contribution ablation（static vs fixed-eqmem vs auto-eqmem）

### 已明确废弃项（不进论文）

为防叙事回滑，以下元素**不进新故事论文**（原论文或早期方案中出现过，但与新故事承重测试不符）：
- 原 `ch3_invtau_heatmap.pdf`（inv_tau 降级）
- 原 Ch4 K/V 消融 3 表独立版（由图 ⑤ 承担）
- 原 Ch4 INT4 三方对比、MixedKV 跨模型、14B K/V mixed、inv_tau 温度校正 4 表（已被新故事取代或降级）
- 原 efficiency TPOT 4 表（整体废弃或仅少数降 appendix）
- 早期方案里的图 ⑥ INT4 vs KIVI summary（和 T2 重复）、表 T7 7B aggregation-split（Level 2 数据，与 §5.5 supporting 定位冲突）、表 T8 Best-Policy Summary（和 T3 重复）、表 T_mech（图 ⑤ 重复）、表 S2（正文替代）

### 数量对照

| 轮次 | 正文图 | 正文表 | 附录 | 总计 |
|---|---|---|---|---|
| 原论文 (thesis-v5-POSITIVE) | ~12 | ~24 | ~9 | ~45 |
| **本方案（M+ 2026-04-20）** | **8** | **9** | **4** | **21 + 1 条件** |

相对原论文精简约 53%，每一项都通过承重测试。

---

## 12. Related Work 定位

本节是 **Ch2 Related Work** 的写作蓝本。

### 12.1 直接对比基线

| 工作 | 关系 | Cache format | 论文处理 |
|---|---|---|---|
| **KIVI** | **最直接基线** | K per-channel + V per-token（与 RoleAlign 同构） | Ch4 §4.2 直接对比；若 §13 Hook 激活，加 matched-budget 正式 compare |
| **KVQuant** | 相关但 format 不同 | 不同压缩路径 | Ch2 描述关系；不直接数值对比 |
| **Fixed-bit uniform baselines** | 朴素 baseline | 同 format | 进 Pareto 图作为下界 |

### 12.2 概念相关但路径不同

| 工作 | 关系 | 我们的定位 |
|---|---|---|
| **TurboQuant / NVFP4** | 新兴低比特路径 | Discussion 提及；不直接对比（format/hardware 差异大） |
| **KVTuner** | allocator 方向相关 | 我们从 behavior 出发，非从 sensitivity surface fitting |
| **Attention sink / streaming-LLM** | KV cache reduction 不同路径（剪枝 vs 量化） | Related work 区分两条线 |

### 12.3 我们不做的对比

- 不对比 activation 量化（不同问题）
- 不对比 weight-only 量化（不同层次）
- 不对比 attention 近似（不同路径）

### 12.4 KIVI 作为核心对比物的三层关系

1. **Format 同构**：K per-channel + V per-token（INT4 非对称）
2. **校准方式不同**：KIVI 运行时 absmax/min；我们离线 behavior-guided KL search
3. **Allocator 层面**：KIVI 无 layer-wise budget；我们有 RoleAlign-allocator 扩展（§13 Hook 激活时成为正式对比主张）

---

## 13. 【Hook】Allocator vs KIVI Formal Compare Package 接口说明

### 13.1 Hook 状态（2026-04-20）

| 状态字段 | 值 |
|---|---|
| 当前状态 | **预留接口**（G0 BLOCKED） |
| 执行 ExecPlan | `.agents/execplans/2026-04-20_allocator-vs-kivi-claim-package.md` |
| 前置 ExecPlan | `.agents/execplans/2026-04-20_same-format-allocator-backend-enable.md`（B/B/B 版本） |
| 关键阻塞 | 缺失 3B / 8B / Mistral-7B RoleAlign calibration + backend 需支持完整 mixed-bit / asymmetric pair + 独立 kv_mode |
| 完成后插入点 | §2.5（calibration 维度）+ §3.5（allocation 维度）+ §11 条件表 9 / 图 4 |

### 13.2 Hook 四档激活规则

**L1 systematic win**：
1. §2.5 写成 "matched-budget 系统对比" 主论点段
2. §3.5 写成 "allocator 独立贡献" 主论点段
3. §9.2 C2 升级加一条 "systematic superiority to KIVI under matched budget"
4. §10 章节映射表激活 Ch4 §4.2.X / §4.3.X
5. §11 图表清单激活表 9

**L2 quality win + non-inferior systems**：
1. §2.5 写成 "quality 层面 systematic 优势 + systems 非劣" 段
2. §3.5 保留但写法弱化为 "allocator 有 quality 增益，systems 非劣"
3. §9.2 C2 不升级
4. §10 激活 Ch4 相关段，但不进 Ch1 contribution

**L3 Pareto advantage only**：
1. §2.5 / §3.5 弱化为 "在 Pareto 前沿占据更好位置"
2. 只加入 §11 图表中的 Pareto overlay（图 4）
3. 不改 §9 Contribution / §10 主章节

**L4 mechanism-only / 实验未完成**：
1. **不做任何章节改动**
2. §2.5 / §3.5 作为 stub 删除
3. §13 Hook 本身作为 "future work" 条目并入 §6
4. Related work §12.1 KIVI 只写已有三层关系（§12.4）

### 13.3 Hook 的"宁缺毋滥"原则

- 只要实验没到 L2 及以上，**不要**把任何 systematic 主张写进主线叙事
- §2.3 的三层诚实分析（L1 事实 / L2 suggests / L3 open question）**必须始终保留**——它是第一层的底线写法
- 若实验最终被决定不做，§2.5 / §3.5 / §13 整体作为 "Future Work" 段落并入 §6.2

### 13.4 激活判定清单

激活前必须满足 ExecPlan 里的硬约束：
- [ ] G0 Fairness Gate PASS（same format + matched memory ±3% + strongest fair KIVI config frozen + smoke pass）
- [ ] G1 Main Matrix Validity Gate PASS（主矩阵完整 + no failed-row + aux 齐全）
- [ ] G2 Claim Strength Gate 判定到 L1 / L2 / L3 / L4 之一
- [ ] `docs/system_vs_kivi_readout.md` + `docs/system_vs_kivi_claim_audit.md` 产出
- [ ] 本文档 §13.1 Hook 状态表从 "BLOCKED" 改成对应的 "L1" / "L2" / "L3" / "L4"
- [ ] 在附 C 修订记录 "Hook 激活日志" 小节追加条目

---

## 14. 旧论文版本（thesis-v5-POSITIVE）的处理原则

### 14.1 旧版快照

- Git tag: `thesis-v5-POSITIVE`
- 页数: 104 页
- 主叙事: 5-Contribution 体系（C1-C3 behavior / C4 boundary / C5 inv_tau × GQA）
- 状态: 已冻结，仍在 git 上可追溯

### 14.2 新故事线相对旧版的章节级调整

| Thesis 章节 | 旧版状态 | 新版处理 |
|---|---|---|
| Ch1 Introduction | 5-Contribution | **部分重写**（改为 §9.1 RQ1-3 + §9.2 C1-3） |
| Ch2 Related Work | KIVI / KVQuant / KVTuner 等 | **保留大部分**，更新 §12.1 直接对比段 + §12.4 三层关系 |
| Ch3 Method | INT8 / INT4 / Allocator 方法 | **保留方法细节**（INT8 kernel / RoleAlign / MixedKV），调整 §3.1 motivation 叙事对齐故事 §1 |
| Ch4 Experiments | 多阶段实验 + Finding 1-4 | **重写 §4.3 / §4.5**（改用 clean_rerun 数据 + 新 regime 地图叙事） |
| Ch5 Discussion | Finding 4（inv_tau × GQA） | **降级**为 discussion 补充；主讨论改为 regime 地图 + heuristic 正面承认 |
| **[保留 5 章制，Ch5 整合 Conclusion+Discussion+Future]** Ch5 Conclusion（四节：§1 核心发现 / §2 局限 / §3 Future Work / §4 结语） | 旧版 4 Finding + 5-Contribution + inv_tau × GQA 叙事 | **整章重写 Phase 8**（§1 改新 C1-3 summary + heuristic/regime/INT4 open q 等 discussion 观点；§2 去 inv_tau；§3 改新故事 3 条；§4 改正向收束） |
| Abstract（中/英） | 旧版 5-contribution | **最后重写**（新 C1-3 + 不再宣称 universal） |

### 14.3 必须重画的图

- Ch4 主图（cross-model compare）—— 用 clean_rerun Step 2 重画
- Pareto 图（图 3）—— 新增，基于 L2 Phase B
- 原 Finding 4 inv_tau × GQA 图 —— 降级到 appendix（如保留）

### 14.4 必须保留的资产

- `thesis/references.bib`
- `thesis/figures/` 下非 Ch4 主图的其他图（Ch3 method schematic 等）
- INT8 / INT4 方法段描述（§3.2-3.3）
- attention error decomposition 公式（原版若已有，直接复用）

### 14.5 改写顺序

按依赖顺序推进，不跳级：

1. **先改研究背景 + 方法 + 实验**（Ch1 §1.1/§1.2/§1.4 + Ch2 + Ch3 + Ch4）；**Ch1 §1.3 + Ch5 整章 + Abstract 放 Phase 8 最后写**（contribution 与 conclusion 互为镜像，需其它章节稳定后一起写）
2. **再改 §2-§3 对应章节**（Ch3 method + Ch4 §4.1-§4.3）—— 主线内容
3. **再改 §5-§6 对应章节**（Ch4 §4.5 + Ch5）—— 模型角色 + discussion
4. **最后改摘要**（abstract_{en,zh}.tex）—— 锁 final messaging

### 14.6 明确不重写

- 所有已有实验框架代码（`src/` / `scripts/`）
- Ch3 方法细节（scale / zero-point / calibration objective 公式）

---

## 15. 术语冻结表

论文中的关键术语一经定义，**不得在不同章节出现不同表述**。本表即术语契约。

| 中文 | 英文 | 定义 | 不要写成 |
|---|---|---|---|
| 行为 | behavior | attention distribution + attention output 的 joint 保持度 | ~~activation~~ / ~~feature map~~ / ~~representation~~ |
| behavior-guided calibration | behavior-guided static calibration | 以 attention behavior 偏移为目标函数的离线校准 | ~~behavior-based~~ / ~~attention-aware~~（不够精确） |
| behavior-guided allocator | behavior-guided budget allocator | 基于 behavior sensitivity profile 指导 layer-wise 预算分配 | ~~attention-based allocator~~ |
| Regime | operating regime | 某 (model family, scale, task) 下的 operating structure（best-k / best-policy 落点） | ~~case~~ / ~~pattern~~（不够准确） |
| Regime 地图 | regime map | 跨模型的 regime 集合 | ~~landscape~~（过于 landscape-fitting 隐喻） |
| AutoK | profile-guided budget proposer | 基于 behavior profile 提出合理预算区间的扩展机制 | ~~adaptive allocator~~ / ~~learned allocator~~（暗示在线学习） |
| 规范验证路径 | canonical validation path | INT8 上用来证明整套 framework 可闭环的干净实例 | ~~best setting~~ / ~~main result~~ |
| 静态 | static (calibration) | 离线 calibration 产物，推理时不更新 | ~~offline~~（有歧义） |
| 动态 | dynamic (calibration) | 运行时 absmax/min（KIVI 风格） | ~~online~~（暗示学习） |
| Final-ready support | final-ready support | 由 clean_rerun pin=ddada19 md5-locked canonical 数据支撑的 claim 等级 | ~~confirmed~~ / ~~validated~~（过强） |

### 15.1 关键动词契约

- **提出**（propose）—— 用于 C1 framework 与 C2 method
- **揭示**（reveal）—— 用于 C3 empirical insight
- **落成**（instantiate）—— 用于 INT8 / INT4 实例化 framework
- **扩展**（extend）—— 用于 allocator / AutoK 顺着原则长出
- **呈现**（exhibit）—— 用于 regime 地图的描述
- **不要写**：~~证明~~（prove）/ ~~建立~~（establish）/ ~~保证~~（guarantee）—— 与论文的实证级别不符

### 15.2 中英对应一致性

中文草稿和英文终稿必须一一对应本表，避免混用。例如：
- 中文"AutoK"始终对应英文"profile-guided budget proposer"
- 中文"行为"始终对应英文"attention behavior"（不是"activation behavior"）

---

## 16. 图表生成细化（每个图/表的完整 spec）

本节给出 §11 图表清单里每个图表的**精确生成 spec**。每个条目包含：Thesis position / Source data / Generation / Elements / Caption template / Note。写 thesis 时按此直接落。

**最终方案 M+ (2026-04-20)**：8 图 + 9 表 + 4 附录 + 1 条件项。废弃项见 §11 末"已明确废弃项"段。

---

### 16.1 图 ①：Attention Error Decomposition（C1 理论起点）

- **Position**：Ch3 §3.1 末尾（问题形式化段落的说明图）
- **Source**：N/A（概念示意图）
- **Generation**：`thesis/figures/fig1_error_decomposition.tex`（TikZ 手绘，**新写**）
- **Elements**：
  - 左栏：attention 流程 block（`q`, `k_i` → `z_i` → `softmax` → `a_i` → `∑a_i v_i` → `o`）
  - 中栏：量化路径（`k_i → \hat k_i` 红色箭头；`v_i → \hat v_i` 红色箭头）
  - 右栏：两条传播分支（K 误差 → Δa 分布扭曲；V 误差 → Δo 聚合偏移）
  - 底部：误差分解公式 `\hat o - o = Σ(\hat a_i - a_i) v_i + Σ\hat a_i (\hat v_i - v_i)`
- **Caption**：
  > Figure 1: Two error propagation paths of KV cache quantization through attention. Key (K) errors distort the attention distribution via softmax; Value (V) errors distort content aggregation. This decomposition motivates preserving attention **behavior** rather than raw tensor values.
- **Note**：单 head 即可，不画 multi-head；不加时间步下标避免混淆

### 16.2 图 ②：Framework Overview（C1 readability spine）

- **Position**：Ch1 §1.4 roadmap 图
- **Source**：N/A
- **Generation**：`thesis/figures/fig2_framework.tex`（TikZ，**新写**）
- **Elements**：
  - 顶部：principle box → "behavior-guided"（attention distribution + output 保持度）
  - 中层两个分支：
    - 左：第一层 calibration（INT8 canonical → INT4 RoleAlign）
    - 右：第二层 allocation（layer-wise → role-aware → AutoK）
  - 底部：empirical validation row（clean_rerun canonical + L2 Pareto + regime map）
  - 虚线箭头：calibration 输出的 sensitivity profile 喂给 allocation
- **Caption**：
  > Figure 2: Framework overview. A single behavior principle vertically connects (i) static calibration that preserves attention output, and (ii) layer-wise budget allocation driven by behavior sensitivity profiles. AutoK operates on this shared profile as a natural extension.
- **Note**：强调"一条原则贯通两层"；不把 AutoK 画成独立分支（避免喧宾夺主）

### 16.3 图 ③：Calibration Pipeline（Ch3 §3.2 方法锚点）

- **Position**：Ch3 §3.2（离线校准流程）
- **Source**：N/A（流程示意图，**改自原论文 ch3-calib-pipeline TikZ**）
- **Generation**：`thesis/figures/fig3_calib_pipeline.tex`（TikZ，**改写自原图**）
- **Elements**：
  - 输入：校准数据（WikiText-2）→ FP16 前向传播（提取 Q/K/V）
  - 两路搜索（并行）：
    - **INT8 path**：`(p_c, g) → min D_KL` 网格搜索，per-group 对称量化
    - **INT4-RoleAlign path**：`(p_K, p_V) → min D_KL` per-channel K + per-token V 非对称格式
  - 输出：校准产物 JSON（scales + percentiles）
  - **相对原论文图的变化**：移除 inv_tau 搜索分支（inv_tau 降级为诊断启发式）
- **Caption**：
  > Figure 3: Offline calibration pipeline. Both paths share the same KL divergence objective over attention behavior, differing only in search space (per-group symmetric for INT8 vs per-channel/token asymmetric for INT4-RoleAlign).
- **Note**：明确标注"两条 path 共享 KL 目标"，这是 framework 贯通性的方法层证据；**不画 inv_tau 路径**

### 16.4 图 ④：Behavior Sensitivity Profile Heatmap ⭐（C1 + C3 签名视觉）

- **Position**：Ch3 §3.3 allocator 方法引入段 **或** Ch4 §4.3 regime 地图视觉入口（推荐 Ch4 §4.3）
- **Source**：6 个 calibration JSON：
  - `artifacts/clean_rerun_20260419T09/kv_calib_kl_qwen25_1p5b_int8.json`
  - `artifacts/clean_rerun_20260419T09/kv_calib_kl_qwen25_3b_int8.json`
  - `artifacts/kv_calib_kl_qwen25_7b_int8.json`
  - `artifacts/kv_calib_kl_llama31_8b_int8.json`
  - `artifacts/clean_rerun_20260419T09/kv_calib_kl_qwen25_14b_int8.json`
  - `artifacts/clean_rerun_20260419T09/kv_calib_kl_mistral7b_int8.json`
- **Generation**：`scripts/thesis/plot_sensitivity_heatmap.py`（**新写**）
- **Elements**：
  - x 轴：6 个 model（按 scale 升序：1.5B / 3B / 7B / 8B / 14B / Mistral-7B）
  - y 轴：layer index 归一化到 [0, 1]（关键——不同 depth 跨模型对齐）
  - 色彩：per-layer behavior sensitivity（KL 偏移度）
  - 每列顶部标注：该模型 top-3 protected layer 位置（小图标）
  - 可选：每列旁边 bar chart，显示 sensitivity 集中度（top-3 占比）
- **Caption**：
  > Figure 4: Behavior sensitivity profile across 6 models, normalized by layer depth. The heterogeneity of profile shape (early-concentrated in small models, dispersed in large models, middle-peaked in Mistral) directly visualizes the **regime map is a property of sensitivity structure, not just outcome**.
- **Note**：**这是 behavior framework 的签名视觉**；必须做到 color-blind safe + 高 DPI；y 轴 normalization 是关键（否则不同 depth 无法对齐）

### 16.5 图 ⑤：K/V Role Mechanism（§2.2 架构选择的 empirical 桥梁）

- **Position**：Ch4 §4.2（支撑 K per-channel + V per-token 架构选择）
- **Source**：`thesis/figures/kv_ablation_summary_ruler.pdf`（**保留原论文图**，数据可用 clean_rerun 重跑更新）
- **Generation**：**沿用原论文**；若需数据更新，脚本未定
- **Elements**（对应原论文已有结构）：
  - 3 条曲线或 bar：K-only INT4 / V-only INT4 / 全 INT4 的 RULER 通过率
  - 跨 2-3 context length
  - 关键 callout：**K-only INT4 的退化显著大于 V-only INT4**（图 ① 理论路径的实证对照）
- **Caption**：
  > Figure 5: Empirical validation of the asymmetric K/V role predicted by Figure 1. K-only INT4 quantization causes substantially larger quality degradation than V-only INT4, supporting the architectural choice of K per-channel + V per-token asymmetric format (§3.2).
- **Note**：Caption 必须**显式 bridge 到图 ①**（"Empirical validation of ... predicted by Figure 1"），让读者看到理论→实证的连接

### 16.6 图 ⑦：Pareto Front Plot ⭐⭐（C2 + C3 + §5.1 多线交汇）

- **Position**：Ch4 §4.3 主图（紧跟 Table T3 之后）
- **Source**：`results/l2_pareto/pareto_front_v4.csv` + `pareto_plot_v4.csv`（335+ rows）
- **Generation**：`scripts/plot_l2_pareto.py`（**沿用**；核实生成 thesis-grade PDF）
- **Elements**：
  - 3 subplot（7b / 8b / mistral7b 各一），共享 y 轴
  - x 轴：`kv_cache_mem_mb`（对数刻度）
  - y 轴：normalized quality（task mean 归一化）
  - Marker：形状区分 policy family（`o` uniform / `△` bakv_fixed / `▽` heuristic / `★` bakv_auto）
  - 每 subplot 画 Pareto front 连线
  - 重点标注：**7B uniform_int4 崩坏点**（红色 × + "quality cliff"）；**Mistral bakv_auto_cov80_max**（红色圈 + "Pareto dominant"）
- **Caption**：
  > Figure 6 (in-text Figure 7 of thesis): Quality-cost Pareto front across 3 models. Each marker is a (policy, configuration) pair. **7B uniform_int4** shows a clear quality cliff, demonstrating that naive budget allocation is a real failure mode. **Mistral's auto-k** occupies the Pareto-dominant region, providing the clearest positive evidence for profile-guided budget proposal.
- **Note**：PDF 必须向量；字体嵌入；color-blind safe palette；saves `thesis/figures/fig7_pareto.pdf`；thesis 内编号为 Figure 7（因为图 ⑦ 对应 story 第 7 个视觉）

### 16.7 图 ⑧：Cross-Model Regime Map Heatmap（C3 skim 路径）

- **Position**：Ch4 §4.3 末尾（跟 Table T3 之后；Table T3 是精读 grid，图 ⑧ 是 skim 视觉）
- **Source**：`results/clean_rerun_20260419T09/summary_final.csv`（step=step2_compare，derived per-model-task best policy family）
- **Generation**：`scripts/thesis/plot_regime_map.py`（**新写**）
- **Elements**：
  - 形式 A（推荐）：5 model (行) × 4 policy types (列) 的 heatmap
    - 色彩 = 该 policy 在该 model 上的 **relative quality**（归一化到 [0, 1]）
    - 加粗框 = per-model global best
  - 可选标注：row-wise "best policy" 标签（不同行不同名）
- **Caption**：
  > Figure 7 (in-text Figure 8): Cross-model regime map. Each row is a model, each column is a policy family. **Bold** outlines per-model best policy. The fact that no two rows share the same best policy visualizes the family/scale/task-dependent regime map in 2 seconds.
- **Note**：这是 T3 的 skim 路径，不是 T3 的替代；色彩选 viridis 或 color-blind safe；确保加粗框清晰可见

### 16.8 图 ⑨：Quality/PPL vs Scale（§5 scale 维度独立可视化）

- **Position**：Ch4 §4.5（per-model case 段落前或末尾）
- **Source**：`results/clean_rerun_20260419T09/summary_final.csv`（按 model scale aggregate per-metric）
- **Generation**：`scripts/thesis/plot_scale_trend.py`（**新写**，**扩展自原 ppl_degradation_vs_scale.pdf**）
- **Elements**：
  - 2 subplot（共享 x 轴）：
    - 上：quality vs scale（5 点：1.5B/3B/8B/14B 的 LongBench mean + Mistral-7B）
    - 下：PPL vs scale（同 5 点）
  - 多条线：不同 policy（uniform_int4 / bakv_auto_cov80 / heuristic）
  - x 轴用 log scale
- **Caption**：
  > Figure 8 (in-text Figure 9): Quality and PPL trends across model scale under 4 allocator policies. The lines diverge at different scales, reflecting scale-dependent regime behavior rather than a monotonic scaling law.
- **Note**：保留原论文 ppl_degradation_vs_scale 的 data 结构，扩展为双指标 + 多 policy

---

### 16.9 表 T0：KV Cache 量化相关工作对比（Ch2 标准表）

- **Position**：Ch2 §2.4 末尾 relative positioning 段
- **Source**：手工编撰（参考各 work 的原 paper）
- **Generation**：`thesis/tables/table_t0_related_work.tex`（手工编写）
- **Elements**（列）：Method / Cache format / Calibration / Allocator / Our relation
  - 行：KIVI / KVQuant / KVTuner / TurboQuant / NVFP4 / **Ours (RoleAlign + AutoK)**
- **Caption**：
  > Table 0: Comparison of representative KV cache compression methods. Our contribution stands out in the allocator dimension: we treat calibration and allocation as two layers sharing a single behavior principle.
- **Note**：**不贬低 baseline**；保留原论文 Ch2 L260 的对比结构

### 16.10 表 S1：实验用模型与 GQA 配置（Ch4 §4.1 setup）

- **Position**：Ch4 §4.1 首个 setup 表
- **Source**：手工列出（HF model card）
- **Generation**：`thesis/tables/table_s1_models.tex`（手工编写，**扩自原论文 Ch4 L34**）
- **Elements**：
  - 行：6 model（Qwen2.5-1.5B/3B/7B/14B + Llama-3.1-8B + Mistral-7B-v0.3）
  - 列：num_layers / num_heads / num_kv_heads / H_kv ratio / head_dim / revision pin
- **Caption**：
  > Table S1: Models and GQA configurations used throughout Chapter 4. Head dimension is fixed at 128; KV heads vary from 2 (Qwen2.5-1.5B) to 8 (Mistral-7B).
- **Note**：revision 必须 pin；每模型 1 行即可

### 16.11 表 S3：RoleAlign vs KIVI 设计差异（KIVI 对比 hub）

- **Position**：Ch3 §3.2 末尾 **或** Ch4 §4.2 开头（推荐 Ch4 §4.2）
- **Source**：手工编撰（基于原论文 Ch3 L564）
- **Generation**：`thesis/tables/table_s3_rolealign_vs_kivi.tex`（手工编写，**沿用原论文结构**）
- **Elements**：
  - 行：3 维度（Cache format / Calibration / Allocator）
  - 列：KIVI-style / **RoleAlign (ours)** / 差异描述
- **Caption**：
  > Table S3: Design contrast between RoleAlign and KIVI-style. Same format, different calibration philosophy (offline behavior-guided vs runtime absmax/min), and we add allocator as framework extension.
- **Note**：KIVI 是论文 core baseline；此表是所有提到 KIVI 的地方的**引用中心**

### 16.12 表 T1：INT8 Canonical vs FP16（C2 第一层硬证据）

- **Position**：Ch4 §4.1 首个数据表
- **Source**：`results/clean_rerun_20260419T09/summary_phase1.csv`（12 rows：1.5B × 4 kv_mode × 3 task）
- **Generation**：`scripts/thesis/make_table_int8_canonical.py`（**新写**）
- **Elements**（pivot 表）：
  - 行：3 task（narrativeqa / hotpotqa / gov_report）
  - 列：4 kv_mode × {quality, Δ vs fp16}
  - 表末：mean across tasks 行
  - 加粗：int8_ours Δ=+0.02 单元格
- **Caption**：
  > Table 1: INT8 canonical path fidelity on Qwen2.5-1.5B-Instruct (clean-provenance pin `ddada19`). INT8-ours is essentially FP16-equivalent (mean Δ=+0.02), establishing the behavior-guided calibration pipeline as a closed loop.
- **Note**：标明 pin；单模型即可；7B echo 放 appendix 而非主表

### 16.13 表 T2：INT4-RoleAlign vs KIVI Cross-Model（§2.3 三层诚实分析）

- **Position**：Ch4 §4.2
- **Source**：
  - 主：`results/clean_rerun_20260419T09/raw/step2_compare/*/` 下 `*int4_ours_asym*.csv` + `*kivi_style*.csv`
  - 辅：`results/phase1_official/`（supporting only，作 Appendix 历史证据）
- **Generation**：`scripts/thesis/make_table_int4_kivi.py`（**新写**）
- **Elements**：
  - 行：4 models × 3 task = 12 rows（每 model 内 group 3 task + 1 model-mean 行）
  - 列：quality (int4_ours_asym / kivi_style / Δ) + PPL (…/Δ) + Needle (…/Δ)
  - 颜色 / 符号标注：Δ > 0 绿色 / `↑`，Δ < 0 红色 / `↓`（不加粗）
- **Caption**：
  > Table 2: INT4-RoleAlign vs KIVI-style across 4 models on 3 LongBench tasks. Quality is comparable or slightly favors RoleAlign; PPL slightly favors KIVI; Needle is on par. The difference aligns with the static vs dynamic calibration philosophies rather than a winner-take-all gap.
- **Note**：**必须保持三层诚实分析**（§2.3 L1/L2/L3）；如果 §13 Hook 激活则在此表**之下**加表 T9 matched-budget formal compare

### 16.14 表 T3：Cross-Model Compare Main Table ⭐⭐（C3 regime map 主证据）

- **Position**：Ch4 §4.3 主表（regime 地图的核心视图，紧跟图 ④ 之后）
- **Source**：`results/clean_rerun_20260419T09/summary_final.csv` + `raw/step2_compare/`（48 runs = 4 models × 4 policy × 3 task）
- **Generation**：`scripts/thesis/make_table_cross_model_compare.py`（**新写**）
- **Elements**：
  - 4 个 block（每个 model 一个）
  - 每 block：3 task × 4 policy 宽表
    - Policies: `uniform_int4_k4v4` / `bakv_k<best>` / `heuristic_k<best>` / `bakv_auto_cov80_max`
    - Per-model best-k：1.5B→k1 / 3B→k1 / 8B→k11 / 14B→TBD / Mistral→k3
  - 每行加粗 per-(model, task) best policy
  - 每 block 末：model mean 行
- **Caption**：
  > Table 3: Cross-model policy comparison under matched INT4 budget (clean-provenance pin `ddada19`). **Bold** denotes per-(model, task) best. The heterogeneity of best-policy choice across models and tasks exhibits the **family/scale/task-dependent regime map**—no single policy is uniformly optimal.
- **Note**：**C3 的核心图表**，必须正文不可移附录；加 footnote 说明 matched-budget 定义；紧跟图 ④ 和图 ⑦

### 16.15 表 T4：Mistral AutoK 5-Task Detail（§5.1 strongest positive case）

- **Position**：Ch4 §4.5.1 Mistral case 段
- **Source**：`results/clean_rerun_20260419T09/raw/step2_compare/mistral7b/` + `step3_extend/mistral7b/`
- **Generation**：`scripts/thesis/make_table_mistral_autok.py`（**新写**）
- **Elements**：
  - 行：5 task（narrativeqa / hotpotqa / gov_report / dureader / lcc）
  - 列：5 policy（uniform_int4 / bakv_k3 / heuristic_k3 / **bakv_auto_cov80_max** / kivi_style）
  - `bakv_auto_cov80` 列加粗；每行加粗 task-best
  - 表末：mean 行 + cov80=14.76 注解
- **Caption**：
  > Table 4: Mistral-7B-Instruct-v0.3 5-task detail under matched INT4 KV memory. The profile-guided auto-k budget proposer wins on 4/5 tasks (mean cov80=14.76 across core+extend), forming the strongest single-family positive case for AutoK.
- **Note**：cov80 的定义必须在 §3.4 提前给出；不要夸大成 "universal win"

### 16.16 表 T5：3B Early-Layer Rescue（§5.2 focused gap）

- **Position**：Ch4 §4.5.2 3B case 段
- **Source**：`results/clean_rerun_20260419T09/raw/step2_compare/3b/`
- **Generation**：`scripts/thesis/make_table_3b_early_layer.py`（**新写**）
- **Elements**：
  - 行：3 task
  - 列：4 policy：`bakv_k1`（protect layer 0）/ `heuristic_k1`（protect middle layer）/ `bakv_k3` / `uniform_int4`
  - 加粗：bakv_k1 相对 heuristic_k1 的 Δ
  - Footnote：强调 heuristic_k1 在某 task 上 catastrophic（Δ << 0）
- **Caption**：
  > Table 5: Qwen2.5-3B-Instruct shows an **early-layer rescue regime**. `bakv_k1` (protects layer 0) substantially outperforms `heuristic_k1` (protects middle layer), indicating that the critical layer for small-scale models is structurally model-specific and not well-served by symmetric heuristics.
- **Note**：此表讨论之后 bridge 到 1.5B（§5.3），讲小模型趋势

### 16.17 表 T6：14B Top-Tier Distribution（§5.4 定量化）

- **Position**：Ch4 §4.5.3 14B case 段
- **Source**：`results/clean_rerun_20260419T09/raw/step2_compare/14b/`
- **Generation**：`scripts/thesis/make_table_14b_toptier.py`（**新写**）
- **Elements**：
  - 行：3 task
  - 列：~8 policies（uniform / bakv_k1/k3/k5/k11 / heuristic_k1/k3/k11 / bakv_auto）
  - 加粗 top-3 per task；表末加 "top-3 within X% of top-1" 统计
- **Caption**：
  > Table 6: Qwen2.5-14B-Instruct exhibits a tight top-tier (top-3 policies within ~2% relative on each task) with no stable universal winner. This quantifies §5.4's "no stable winner" claim.
- **Note**：若某 policy gap < 0.5 绝对分数，Caption 里说明 "statistical distinguishability 需 bootstrap CI"

---

### 16.18 附录 Tables（4 项）

**附录 P1：FP16 Baseline + Evaluation Protocol**
- Position：Appendix；Source：手工汇总 + `results/clean_rerun_20260419T09/summary_phase1.csv`
- Content：FP16 基线跨 model × task 的 quality 参考值 + 评测协议（seed / greedy / n=5 等）

**附录 P2：Experimental Environment**
- Position：Appendix；Source：手工（SSH 机器配置）
- Content：GPU 型号、CUDA/PyTorch 版本、Python 版本、关键 lib 版本

**附录 A：Prompt-Adaptive 8B 5-Task Matrix**
- Position：Appendix A；Source：`docs/clean_rerun_20260419T09/completion_report_20260419.md` Part B
- Generation：手工转录 或 `scripts/thesis/make_appendix_prompt_adaptive.py`
- Content：8B × 5 task × {fixed_k / auto_k / prompt_adaptive} + mean + task_best 标注
- Caption：> Appendix Table A: Prompt-adaptive selector on Llama-3.1-8B × 5 LongBench tasks. The selector wins only on lcc (+0.40 over auto-k); the 5-task mean favors fixed-k. Treat this as exploratory toward future per-prompt routing, **not** as a current claim.

**附录 B：Off-Protocol 1.5B/7B Prompt-Adaptive**
- Position：Appendix B；Source：`results/l2_prompt_adaptive/{1p5b,7b}/`
- Generation：`scripts/thesis/make_appendix_prompt_adaptive_offprotocol.py`（**新写**）
- Content：2 model × 5 task × 3 variant，**OFF-PROTOCOL 标注**
- Caption：> Appendix Table B (**Off-protocol exploratory, NOT for Gate C**): Prompt-adaptive on Qwen2.5-1.5B / Qwen2.5-7B × 5 tasks. Behavior on these scales differs from 8B, but current selector is still task-bucket level. Reported for future-work seed only.

---

### 16.19【Hook 条件】表 T9 / 图 ⑩ / 附录表 C

仅在 §13 Hook 激活后生成：

- **表 T9**（L1/L2 激活）：Allocator vs KIVI matched-budget comparison，4 systems × 5 models × 5 tasks
- **图 ⑩**（L3 激活）：Allocator vs KIVI Pareto overlay（在图 ⑦ 之上添加 KIVI 对比线）
- **附录表 C**（L4 激活）：Allocator contribution ablation（static vs fixed-eqmem vs auto-eqmem 增量拆分）

激活时按 §13.2 的规则写入对应位置，不激活则整体废弃。

---

### 16.20 图表 Cross-Reference 矩阵

| 图/表 | 主支撑 | 故事章节 | Thesis 章节 | 数据 Level |
|---|---|---|---|---|
| 图 ① | C1 | §1 | Ch3 §3.1 | N/A |
| 图 ② | C1 readability | §7 | Ch1 §1.4 | N/A |
| 图 ③ | C2 方法锚点 | §2 | Ch3 §3.2 | N/A |
| 图 ④ ⭐ | C1 + C3 | §3.2 + §5 | Ch3 §3.3 / Ch4 §4.3 | artifacts JSON |
| 图 ⑤ | C2 机制桥梁 | §2.2 | Ch4 §4.2 | 原论文沿用 |
| 图 ⑦ ⭐⭐ | C2 + C3 + §5.1 | §3.4 | Ch4 §4.3 | L4 |
| 图 ⑧ | C3 skim | §3.2 + §5 | Ch4 §4.3 末 | L5 derived |
| 图 ⑨ | §5 scale 维度 | §5 | Ch4 §4.5 | L5 derived |
| 表 T0 | Ch2 标准 | §12 | Ch2 §2.4 | 手工 |
| 表 S1 | setup | §4.1 | Ch4 §4.1 | 手工 |
| 表 S3 | KIVI hub | §2.2 | Ch4 §4.2 | 手工 |
| 表 T1 | C2 第一层 | §2.1 | Ch4 §4.1 | L5 |
| 表 T2 | §2.3 诚实分析 | §2.2 | Ch4 §4.2 | L5 + L3 |
| 表 T3 ⭐⭐ | C3 regime map | §3.2 | Ch4 §4.3 | L5 |
| 表 T4 | §5.1 strongest | §5.1 | Ch4 §4.5.1 | L5 |
| 表 T5 | §5.2 focused | §5.2 | Ch4 §4.5.2 | L5 |
| 表 T6 | §5.4 定量化 | §5.4 | Ch4 §4.5.3 | L5 |
| 附 A | §4.3 | §4.3 | Appx A | L3 |
| 附 B | future-work seed | §4.3 末 | Appx B | L2 |

---

### 16.21 `scripts/thesis/` 目录建议

以下 11 个脚本统一放在新建目录 `scripts/thesis/`：

```
scripts/thesis/
├── make_table_int8_canonical.py         (T1)
├── make_table_int4_kivi.py              (T2)
├── make_table_cross_model_compare.py    (T3 ⭐⭐)
├── make_table_mistral_autok.py          (T4)
├── make_table_3b_early_layer.py         (T5)
├── make_table_14b_toptier.py            (T6)
├── make_appendix_prompt_adaptive.py     (Appx A)
├── make_appendix_prompt_adaptive_offprotocol.py  (Appx B)
├── plot_sensitivity_heatmap.py          (图 ④ ⭐)
├── plot_regime_map.py                   (图 ⑧)
└── plot_scale_trend.py                  (图 ⑨)
```

**不需要新脚本的产出**：
- 图 ① ② ③：TikZ 手绘，直接写 `thesis/figures/*.tex`
- 图 ⑤：沿用原论文 `kv_ablation_summary_ruler.pdf`
- 图 ⑦：沿用 `scripts/plot_l2_pareto.py`
- 表 T0 / S1 / S3：手工 LaTeX 编写
- 附录 P1 / P2：手工 LaTeX 编写

**每个 `make_table_*.py` 脚本的 contract**：
- 输入：单一 CSV 路径（或 glob 模式）
- 输出：`thesis/tables/<table_id>.tex`（LaTeX 源）+ `thesis/tables/<table_id>.md`（Markdown 调试版）
- 复用已有的 `scripts/export_tables_latex.py` 工具层

**每个 `plot_*.py` 脚本的 contract**：
- 输入：JSON artifact 路径 / CSV 路径
- 输出：`thesis/figures/<fig_id>.pdf`（向量 PDF，字体嵌入，color-blind safe）
- 使用 matplotlib + 统一 style preset

---

## 附 A. 数据引用指引（本故事 → 数据资产）

本故事线每一段对应的数据证据位置：

| 故事章节 | 数据证据源 | Level | 位置 |
|---|---|---|---|
| §2.1 INT8 canonical | `results/clean_rerun_20260419T09/raw/step1_canonical/` | 5 | Part C.1 |
| §2.2 INT4 推进 | `results/phase1_official/` + `results/clean_rerun/raw/step2_compare/*/int4_*` | 3+5 | Part C.2 + C.1 |
| §2.3 INT4 vs KIVI | `results/clean_rerun/` 中 `int4_ours_asym` vs `kivi_style` 列 | 5 | Part C.1 |
| §3.2 regime 地图 | `results/clean_rerun_20260419T09/raw/step2_compare/` (4 model × 4 policy) | 5 | Part C.1 |
| §3.3 L2 Phase A | `results/l2_kv_asymmetric/` (108 CSV) | 3 | Part C.4 |
| §3.4 L2 Phase B ⭐ | `results/l2_pareto/` (335 CSV + pareto_*_v4.csv) | 4 | Part C.3 |
| §4.2 AutoK | Pareto top tier + `results/clean_rerun/raw/step2_compare/mistral7b/bakv_auto_cov80_max/` | 4+5 | Part C.1 + C.3 |
| §4.3 L2 Phase C 官方 | `results/l2_prompt_adaptive/8b/` (15 runs) | 3 | Part C.5 |
| §5.1 Mistral | `results/clean_rerun/raw/step2_compare/mistral7b/` + step3 | 5 | Part C.1 |
| §5.2 3B | `results/clean_rerun/raw/step2_compare/3b/` | 5 | Part C.1 |
| §5.3 1.5B | `results/clean_rerun/raw/step1_canonical/1p5b/` + l2 exploratory | 5+2 | Part C.1 + C.6 |
| §5.4 14B | `results/clean_rerun/raw/step2_compare/14b/` | 5 | Part C.1 |
| §5.5 7B aggregation-split | `results/phase2_c2b_local/` (87 files) + `phase2_diag_local/` | 2 | Part C.7 |
| §6.2 Per-prompt FW | `results/l2_prompt_adaptive/{1p5b,7b}/` (off-protocol seed) + `/8b/lcc` | 2+3 | Part C.5 + C.6 |
| §6.3 Role-aware FW | `results/l2_kv_asymmetric/` | 3 | Part C.4 |
| §6.4 Pareto FW | `results/l2_pareto/` | 4 | Part C.3 |

---

## 附 B. 5 条 final-ready claim（数据支撑索引）

这 5 条来自 `docs/clean_rerun_20260419T09/completion_report_20260419.md`，均由 clean_rerun pin=`ddada19` 的 md5-locked canonical 数据支撑：

| # | Claim | 对应故事章节 | 主数据源 |
|---|---|---|---|
| 1 | INT8 canonical path fidelity（int8↔fp16 Δ=+0.02） | §2.1 | clean_rerun Step 1 |
| 2 | Mistral-specific auto-k win（cov80=14.76 跨 core+extend task） | §5.1 + §4 | clean_rerun Step 2+3 |
| 3 | 3B early-layer rescue regime | §5.2 | clean_rerun Step 2 |
| 4 | 14B top-tier but no stable winner | §5.4 | clean_rerun Step 2 |
| 5 | Heuristic is a strong baseline | §6.1 | clean_rerun Step 2+3 综合 |

---

## 附 C. 修订记录

_本节只 append，不改 §1-§8 既定叙事。_

**2026-04-20 初版**：
- 从 `docs/data_asset_inventory_20260420.md` Part A 抽出独立成文
- 内部章节编号从 A.1-A.8 改为 1-8
- 补充附 A（数据引用指引）+ 附 B（5 claim 数据支撑索引）+ 附 C（修订记录）

**2026-04-20 v2（同日晚间，用户要求"可直接指导论文修改"）**：
- 新增 §2.5 【Hook】INT4 层面 Allocator vs KIVI 正式对比（预留接口，状态 BLOCKED）
- 新增 §3.5 【Hook】Allocator 维度的 vs KIVI 正式主张（预留接口，状态 BLOCKED）
- 新增 §9 Research Questions 与 Contributions（RQ1-3 + C1-3）
- 新增 §10 章节映射（故事 §X → thesis/chapters/*.tex 的完整映射表）
- 新增 §11 图表与主表清单（按 C1/C2/C3 分组 + 条件图表）
- 新增 §12 Related Work 定位（KIVI 作为核心对比物的三层关系）
- 新增 §13 Hook 说明（四档激活规则 + 宁缺毋滥原则 + 激活判定清单）
- 新增 §14 旧论文版本（thesis-v5-POSITIVE）处理原则（章节级调整表 + 改写顺序）
- 新增 §15 术语冻结表（中英对应 + 动词契约）

### Hook 激活日志（本小节在 Hook 状态变化时 append）

- _（暂无条目。若 §13 Hook 激活，此处追加 "YYYY-MM-DD：Hook 从 BLOCKED 转为 L{1,2,3,4}" 条目 + 激活后对 §2.5 / §3.5 / §9.2 的实际修改指针）_

---

**文档结束。**
