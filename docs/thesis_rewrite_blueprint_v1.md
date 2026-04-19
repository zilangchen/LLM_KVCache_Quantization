# Thesis Rewrite Blueprint v1

## 0. 文档定位

这不是论文正文，也不是实时工作台替代品。

这份文档的职责只有一个：

> 在当前 `candidate-main` 数据边界下，给整篇论文提供一份可执行、可审查、可持续维护的重构蓝图。

它服务于三类后续动作：

1. 章节级重写前的结构定调
2. 图表与表格系统重排
3. 后续 `L2` 扩展与 clean-provenance 覆盖时的接口对齐

当前不做的事：

- 不直接修改 `thesis/chapters/*.tex`
- 不覆盖 `docs/thesis_upgrade_live_plan.md`
- 不把当前 `candidate-main` 数字写成 `final-ready` 主表
- 不把 `AutoK` 升格成全文理论中心

---

## 1. 权威来源与使用顺序

本蓝图建立在以下文件之上，使用顺序从高到低：

1. `docs/thesis_upgrade_live_plan.md`
2. `docs/phase2_data_mainline_audit_20260419.md`
3. `docs/behavior_mainline_reframing_memo.md`
4. `docs/clean_provenance_launch_plan.md`
5. `thesis/main.tex` 与 `thesis/chapters/*.tex`
6. 当前图表 inventory 与相关结果目录

特别说明：

- `docs/thesis_chapter_mapping.md` 已过时，本轮不作为主依据。
- `docs/thesis_figure_prompts.md` 中大量 prompt 服务旧主线，只能作为旧图表 inventory 参考，不能直接沿用。

---

## 1.5 首改优先级与高危断裂点

这不是补充说明，而是当前蓝图的执行门禁。后续任何正文改写，都必须先服从这一节。

### 1.5.1 首改优先级

按风险顺序，而不是按章节顺序：

1. 先清理 `Abstract / Chapter 1 / Chapter 5` 中旧的 `C1/C2/C3` 三贡献信号
2. 再补 `Chapter 3 -> Chapter 4` 的 allocation / auto-k 方法桥
3. 再整体重写 `Chapter 2`
4. 最后才进入逐章正文改写

### 1.5.2 当前最危险的断裂点

1. `Abstract / Ch1 / Ch5` 仍可能让读者读出“KL / RoleAlign / kernel 三贡献并列”
2. `Ch3` 若不正式建立 `Behavior-Guided Allocation` 与 `AutoK` 的方法身份，`Ch4` 会像另开一篇论文
3. `Ch2` 若继续沿用“填补空白，因此更强”的骨架，会直接破坏新主线
4. 图表、caption、表头一旦回到 `winner / best / gap / rank #1` 语言，评审仍会把它读成 superiority paper

### 1.5.3 写作前硬门槛

以下任一条件不满足，正文改写应暂停：

1. `Ch1` 贡献列表还在并列 `KL / RoleAlign / kernel`
2. `Ch3` 没有正式区分 calibration / allocation / auto-k 三层
3. `Ch4` 还在按 winner-style 组织结果
4. `Ch5` 还在按旧三发现收尾
5. `Ch2` 还像背景教材章而不是定位章

---

## 2. Master Prompt

下面这段是后续进行论文重构、章节改写、图表重绘、答辩自检时应反复使用的主驱动 Prompt。

### 2.1 主驱动 Prompt

> 你现在不是在润色一篇已经成立的论文，而是在重构一篇主线已经收缩的论文。  
> 你的任务不是证明某个方法普适更优，而是把整篇论文重写成一篇在当前证据边界内仍然成立的 `behavior-centric framework` 论文。  
>  
> 你必须严格遵守以下口径：  
> 1. `behavior` 是统一的分析与设计原则，不是已被证明普适更优的单点算法。  
> 2. `INT8 canonical path` 是最干净的主验证链，它证明框架可落地，但不证明 `KL > MSE`。  
> 3. allocator 的最稳 empirical reading 是 `family-/scale-/task-dependent regimes`，不是 universal winner。  
> 4. `heuristic` 是强 baseline，必须正面承认。  
> 5. `AutoK` 是 `profile-aware budget proposer`，是 framework 下的强扩展，不是理论中心。  
> 6. 当前结果生产层多数仍是 `exploratory-produced`；当前可写层是 `candidate-main narrative`；任何 tight numeric winner claim 都必须等待 `clean-produced final-ready` 覆盖。  
> 7. `Chapter 2` 不是背景堆砌章，而是 prior work 重排与本文定位章。  
> 8. `Chapter 3` 必须正式建立 `Behavior-Guided Allocation` 与 `AutoK` 的方法身份，否则 `Chapter 4` 不得展开 allocator regime 论证。  
>  
> 在此基础上，你需要同时完成三种审判：  
> - 图表系统是否仍在服务旧主线  
> - 每章、每节、关键段落的内部结构是否支持新主线  
> - 全文从摘要到结论的逻辑链是否闭环  
>  
> 最终输出必须保证：  
> - 经得起答辩委员会追问  
> - 经得起顶会/期刊审稿对 soundness、reproducibility、related work fairness 的审视  
> - 为 `L2` 扩展与 clean-provenance rerun 预留接口，但不让它们污染当前主线

### 2.2 本蓝图采用的总读法

整篇论文的最终读法应统一为：

> 这不是一篇证明单一量化方法普适更优的论文，  
> 而是一篇以 `behavior` 为统一分析与设计原则、用 `INT8 canonical path` 建立主验证链、再通过 allocator 实验揭示 `family-/scale-/task-dependent regimes`，并把 `auto-k` 作为下游扩展的 framework 论文。

---

## 3. 当前数据、provenance 与口径基线

### 3.1 双层 provenance 规则

当前必须同时区分两层状态：

1. **结果生产层**
   - `exploratory-produced`
   - `clean-produced`
2. **叙事可写层**
   - `candidate-main`
   - `final-ready`

最关键的纪律是：

> 现在很多资产属于 `exploratory-produced + candidate-main-readable`，  
> 这不等于 `clean-produced + final-ready`。

### 3.2 当前允许写入论文草稿的核心结论

在当前 `candidate-main` 边界下，可以写入草稿的核心结论是：

1. `behavior` 适合作为统一的分析与设计原则
2. `INT8 canonical path` 是最干净的 validated instance
3. allocator 现实更像 `family-/scale-/task-dependent regimes`
4. `heuristic` 是强 baseline
5. `auto-k` 是有实证支撑的 strong extension，但不是 universal winner
6. `3B` 暴露了 `early-layer bottleneck / first-layer rescue` 这一异常 regime
7. extend-task 证据必须 triage，优先级为 `dureader > lcc > trec/vcsum`

### 3.3 当前不能写成最终主张的内容

以下内容不能写成正文中的 final claim：

1. `KL` 在 `INT8` 上优于 `MSE`
2. `RoleAlign` 明显优于 `KIVI-style`
3. `behavior-guided allocation` 普适优于所有 baseline
4. `best-k` 随模型规模单调上移
5. `auto-k` 是跨模型最优方法
6. 任何直接使用当前 `candidate-main` compare-set 紧凑数字的 tight winner claim

### 3.4 当前论文应采用的结论层级

```text
Framework Principle
    ↓
Canonical Validation (INT8)
    ↓
Allocator Regime Reading
    ↓
Auto-k Extension
    ↓
Provenance Boundary / Future Upgrade
```

---

## 4. 旧论文被击穿的地方

### 4.1 旧论文的真实问题

旧论文最大的问题不是材料不够，而是主角太多、结论层级混乱。它同时试图当成：

1. 一篇 `behavior-aligned superiority` 方法论文
2. 一篇 `INT4-RoleAlign` 低比特 hero 论文
3. 一篇 Triton kernel / deployment 系统论文

### 4.2 被击穿的关键点

1. `INT8` 上没有证明 `KL > MSE`，而是趋同
2. `INT4` 上没有证明 `RoleAlign > KIVI-style`
3. `fixed-k` 不能承担跨模型最终方法角色
4. 最新数据支持的是 regime，而不是 universal law

### 4.3 新主线为什么成立

新主线之所以成立，不是因为找到了新的 universal winner，而是因为它把真正站得住的东西重新组织起来了：

1. `behavior` 作为统一分析对象仍然成立
2. `INT8 canonical path` 仍然是最硬主干
3. allocator 结果确实揭示了 regime-dependent reality
4. `auto-k` 确实是 fixed-k 失效后的自然扩展

---

## 5. 全文总逻辑链

### 5.1 目标逻辑链

整篇论文应按以下逻辑推进：

1. **定义问题**
   - KV cache 是长上下文推理的显存与带宽瓶颈
2. **重定义分析对象**
   - 真正要保护的不是纯数值误差，而是 attention behavior
3. **建立最干净验证链**
   - 用 `INT8 canonical path` 证明 framework 可落地
4. **进入更真实的 allocator 现实**
   - 当问题进入 fixed-k / budget policy 层，现实不是 winner，而是 regime
5. **给出自然扩展**
   - `auto-k` 作为 profile-aware budget proposer 出现
6. **收口边界**
   - 当前是 `candidate-main`，不是 `final-ready`

### 5.2 每章的单句使命

- **Abstract**：给出整篇论文的最终读法
- **Chapter 1**：重新定义研究问题与贡献边界
- **Chapter 2**：重排 prior work，并校准本文位置
- **Chapter 3**：把 calibration / allocation / auto-k 的层级讲清
- **Chapter 4**：用 canonical validation + regime evidence 支撑新主线
- **Chapter 5**：按 framework / regime / extension 收口，不再拔高

### 5.3 旧逻辑必须修掉的断裂

1. 从“behavior 是更好的分析对象”直接跳到“behavior-aligned 方法更优”
2. 从 Key-dominant mechanism 直接跳到 `RoleAlign` 是 hero method
3. 从跨模型结果直接跳到 generalized law，再突然切到 kernel phase map
4. 摘要/引言继续卖 superiority，但结论已经在做 caveat 收缩

---

## 6. 图表与表格系统重排

### 6.1 图表总原则

图表系统必须从旧的：

- `RoleAlign hero`
- `scale-shift winner`
- `winner-style compare`

重排为新的：

- `Behavior framework`
- `INT8 canonical validation`
- `family regime map`
- `provenance boundary`

### 6.2 必须退出主文或显著降级的旧图/表

#### 需要移出主文或删除

1. `fig:rolealign-summary`
2. `fig:ppl-vs-scale`
3. `tab:rolealign-results`
4. `tab:kivi-int4-threeway`
5. `fig:pareto-quality-efficiency`
6. `tab:int4-tpot-cross-model`
7. `tab:phase1-tpot`
8. `tab:longseq-tpot-14b`
9. `tab:phase-boundary`

#### 需要重画或重写口径

1. `fig:ch1-pipeline`
2. `fig:ch3-framework`
3. `tab:ch3-rolealign-vs-kivi`
4. `tab:cross-model`
5. `tab:kivi-comparison`
6. `fig:ch3-invtau-heatmap`

#### 需要压缩成 summary 的表组

1. `tab:kv-ablation-ppl`
2. `tab:kv-ablation-ruler`
3. `tab:kv-ablation-longbench`

它们正文只保留一张 summary table，其余降到附录。

### 6.3 必须新增的图和表

这一节按资产层级组织，而不是按“想加多少张图”组织。

#### A. 主文核心资产（candidate-main 可用）

1. **Behavior-Centric Thesis Argument Map**
   - 位置：`Chapter 1`
   - 作用：替换旧 `fig:ch1-pipeline`

2. **Prior Work Positioning Matrix**
   - 位置：`Chapter 2`
   - 作用：定义我们与 KIVI / allocator literature 的关系

3. **Behavior-Guided Framework Figure**
   - 位置：`Chapter 3`
   - 作用：统一 calibration / allocation / auto-k 三层

4. **Cross-Model Regime Summary Table**
   - 位置：`Chapter 4`
   - 作用：跨模型稳定读法总结

5. **Family Regime Map**
   - 位置：`Chapter 4`
   - 作用：主图，展示不同 family / scale 的 regime 差异

6. **3B First-Layer Rescue Figure**
   - 位置：`Chapter 4`
   - 作用：突出 3B anomaly

#### B. Supporting-only 资产

1. **Auto-K Range Proposer Schematic**
   - 位置：`Chapter 3`
   - 作用：说明 auto-k 是 coverage-based proposer，不是手工 sweep 换壳

2. **Heuristic Baseline Reposition Table**
   - 位置：`Chapter 4`
   - 作用：把 heuristic 正式从 strawman 提升为强 baseline

3. **Extend-Task Triage Table**
   - 位置：`Chapter 4` 或 Appendix
   - 作用：控制低信息量任务污染

4. **Provenance Ladder**
   - 位置：`Chapter 4` threats 或 Appendix
   - 作用：显示 `exploratory -> candidate-main -> final-ready`

#### C. 边界型图表（建议新增）

1. **INT8 Claim Boundary Table**
   - 位置：`Chapter 4` 的 `INT8 canonical` 小节后
   - 作用：明确 `INT8` 证明了什么、没有证明什么

2. **Compare-Set Governance Table**
   - 位置：`Chapter 4` threats 或 Appendix
   - 作用：明确哪些 wave/task/assets 可以作为主文、supporting、或 final-ready only

#### D. Final-ready only 资产

以下资产在 clean-provenance 覆盖前不得进入主文：

1. cross-model winner table with tight gaps
2. auto-k final compare-set table
3. allocation quality-cost Pareto 主图
4. 当前 compare-set 赢家数字的 ranking chart
5. 任何混用 Mistral smoke 与 full 的图/表

### 6.4 图表在各章的推荐上限

- `Chapter 1`：1 图
- `Chapter 2`：1 表
- `Chapter 3`：2 图 + 1 表
- `Chapter 4`：2 图 + 2 表
- `Appendix`：1 图 + 1 表 + 若干降级 supporting assets

### 6.5 图表系统的强制规则

1. 主文任何表格只要出现 `best / winner / rank / gap to best` 这类列名，一律视为 `final-ready` 资产
2. 主文任何图表 caption 必须带 evidence-tier 标识：
   - `canonical validated instance`
   - `candidate-main evidence`
   - `supporting only`
3. Mistral 主文图表必须显式标 `full-only`
4. `trec / vcsum` 不得进入 allocator 主图主表

---

## 7. 章节级重构蓝图

## 7.1 Chapter 1 绪论

### 本章使命

把研究问题从“方法是否更优”改写成“为什么 behavior 应成为统一分析对象，以及为什么 allocator 现实需要新的读法”。

### 应保留

1. KV cache 是长上下文推理的显存/带宽瓶颈
2. `behavior` 比纯数值误差更接近真实损伤对象
3. `INT8 canonical path` 是最干净的主验证链
4. calibration / kernel / generate loop 的系统闭环

### 应删除或降级

1. `KL` 普适优于 `MSE` 的表述
2. 把 `INT4-RoleAlign` 写成 hero result 的语气
3. 把 kernel / phase-map 写成与主理论并列的中心贡献
4. `behavior-guided allocation universally better`

### 推荐结构

1. 研究背景：KV cache bottleneck
2. 问题定义：为什么从数值误差转向 behavior
3. 研究现状：格式、校准、预算分配三条线
4. 本文定位与主要贡献
5. 论文组织结构

### 本章结尾必须交代的句子

> 本文不再试图证明某个量化策略普适更优，而是提出并验证一个以 behavior 为统一原则的框架，并在 allocator 层揭示 regime-dependent 现实。

---

## 7.2 Chapter 2 相关工作与技术基础

### 本章使命

这不是背景教学章，而是**必须整体改写**的 prior work 重排与本文位置校准章。

### 应保留

1. KV cache 机制与显存背景
2. GQA / `H_kv` 的最小必要背景
3. KIVI、AsymKV、ZipCache 等关键相关工作
4. 行为失真与 attention 分布影响这一桥接点
5. mixed-precision / allocation 相关工作
6. 最小必要的系统背景

### 应压缩或删除

1. 过长 Transformer 教材内容
2. 自注意力 / MHA / GQA 的详细公式推导
3. 与新主线弱相关的通用 kernel 背景
4. “填补四个空白，因此更强”这种旧式 gap 写法

### 推荐结构

1. KV cache 机制、GQA 与长上下文瓶颈
2. KV cache 量化的三个设计轴：格式、校准、预算分配
3. K/V 非对称格式相关工作：从 KIVI 到低比特 KV quantization
4. Behavior 与 attention distortion：从数值误差到行为视角
5. Mixed-precision 与 allocation 相关工作
6. 高效注意力与系统背景
7. 本文位置：从 behavior-aligned calibration 到 behavior-guided allocation

### 本章结尾必须交代的句子

> 本文与 prior work 的差别，不是简单“更强”，而是把 calibration 与 allocation 统一到同一个 behavior-derived profile 视角下。

### 本章的硬要求

1. 必须正面承认 KIVI 是关键前作，不得写成待击败 baseline
2. 必须单独给 allocation / mixed-precision / budget policy 一节
3. 必须从“研究空白章”改写成“定位章”
4. 若章末仍出现“填补四个空白，因此更强”式总结，则视为重构失败

---

## 7.3 Chapter 3 方法设计

### 本章使命

把 calibration、allocation、auto-k 的层级关系讲清，让读者知道这不是三篇论文拼接，而是一套 framework。

### 应保留

1. 框架总体设计
2. 离线校准与在线执行两阶段
3. calibration artifact / JSON
4. `INT8` 对称路径
5. MixedKV、runtime routing、generate loop
6. `KIVI-style` 与 `RoleAlign` 的格式关系说明

### 应降级

1. `KL > MSE` 的强口气
2. `RoleAlign` 的中心地位
3. `inv_tau` 的视觉中心性
4. “与 KIVI 的差异”中的 superiority 语气
5. kernel 作为主理论的一部分

### 推荐结构

1. Behavior 作为统一设计原则
2. 框架总体设计：离线 profile 与在线执行
3. Behavior-aligned calibration
4. `INT8 canonical validated instance`
5. Behavior-guided allocation
6. Auto-k range proposer 作为下游扩展
7. 系统接口与运行时路由
8. 复杂度、显存与实现开销
9. 本章小结

### 本章必须讲清的三层

1. calibration：找量化参数
2. allocation：找预算分配
3. auto-k：找预算规模

### 本章关键限制句

> allocator 这一步不是再次直接优化 attention-KL，而是利用前一阶段得到的 behavior-derived profile 来指导预算分配。

### 本章的硬门槛

如果本章没有正式建立：

1. `Behavior-Guided Allocation` 的方法身份
2. `AutoK` 作为 coverage-based proposer 的方法身份
3. calibration / allocation / auto-k 的三层区分

则 `Chapter 4` 不得展开 allocator regime 论证。

---

## 7.4 Chapter 4 实验与结果分析

### 本章使命

从“赢家展示章”改写成“canonical validation + regime evidence + extension + boundary”四层结构。

### 应保留

1. 实验设置主体
2. `INT8` canonical reference
3. `KL vs MSE` 对比，但改成边界澄清
4. 支撑 behavior 视角的低比特诊断材料
5. 部分系统效率结果
6. threats / validity 披露

### 应删除或降级

1. `INT4-RoleAlign` 作为全文 hero 的结构
2. `RoleAlign > KIVI-style` 的主文表述
3. universal generalization 语气
4. 把 `trec/vcsum` 当 allocator 主证据
5. smoke/full 混用
6. winner-style 结果组织法

### 推荐结构

1. 实验设置与证据层级说明
2. Canonical validated instance：`INT8` 证明了什么，没证明什么
3. 从 fixed-k 到 regimes：7B 的核心发现
4. Cross-scale allocator evidence：8B、14B、Mistral
5. 3B anomaly：early-layer bottleneck 与 first-layer rescue
6. Heuristic baseline 的重新定位
7. Auto-k 作为强扩展，而非 universal winner
8. Extend-task triage：`dureader`、`lcc`、`trec/vcsum`
9. Provenance、claim boundary 与 threats
10. Supporting system evidence
11. 本章小结

### 本章的主图主表职责

- `Family Regime Map`：主图
- `Cross-Model Regime Summary Table`：主表
- `3B First-Layer Rescue Figure`：新异常现象图
- `Heuristic Baseline Reposition Table`：baseline 定位表

### 本章必须显式披露的边界

1. 当前 Phase 2.6 为 `candidate-main`
2. 当前 compare-set 支撑的是排序、结构和 regime shape
3. 紧凑 winner claim 必须等 clean-provenance rerun 覆盖

### 本章的固定收口规则

每个模型级小节结尾都必须显式写两句：

1. `stable reading`
2. `cannot over-interpret`

如果某个模型小节只给现象、不写边界，则视为违规。

---

## 7.5 Chapter 5 结论与展望

### 本章使命

收窄，不拔高；总结“现在真正知道了什么”，而不是“谁赢了”。

### 应保留

1. 核心发现
2. 局限性
3. 未来工作
4. 结语

### 应删除或降级

1. 把“趋同-分化-再收敛”当全文第一结论
2. `RoleAlign` 与 `KIVI-style` 的同级数值总结
3. kernel / deployment phase-map 作为全文收束中心
4. 任何 universal superiority 余味

### 推荐结构

1. 核心发现与收束
2. 局限性与 claim boundary
3. 未来工作：L2 extensions 与 clean-provenance
4. 结语

### 本章只收四件事

1. `behavior` 是统一分析与设计原则
2. `INT8 canonical path` 是最干净的主验证链
3. allocator 现实是 regime-dependent
4. auto-k 是 framework 下的强扩展，不是理论中心

---

## 8. Abstract 重写准则

摘要不能再按旧“三贡献并列”写。它必须按以下顺序：

1. 问题：KV cache 量化的真正挑战是行为失真，而不只是数值误差
2. 主张：`behavior` 是 unified analysis/design principle
3. 验证：`INT8 canonical path`
4. 经验现实：allocator 呈现 `family-/scale-/task-dependent regimes`
5. 扩展：`auto-k` 是 strong extension，不是 universal winner
6. 边界：当前结果为 framework 与 regime 读法提供支撑

摘要中不应再并列写：

- `INT4-RoleAlign hero result`
- kernel phase-map
- superiority 口气的三贡献列表

---

## 9. 评审与答辩风险清单

### 9.1 必须主动化解的风险

1. **Superiority 风险**
   - 不准再让审稿人读出“我们证明了 behavior-aligned 方法普适更强”

2. **Baseline 风险**
   - 必须正面承认 heuristic 是强 baseline

3. **Prior-work 风险**
   - `Chapter 2` 必须把 KIVI、mixed-precision、allocator literature 的关系讲清

4. **Provenance 风险**
   - `candidate-main` 与 `final-ready` 边界必须可见

5. **Auto-k 风险**
   - auto-k 只能写成 strong extension / top-tier evidence，不准写成 universal winner

6. **3B 过度泛化风险**
   - 3B anomaly 必须写成 anomaly / regime，不是新 universal law

7. **Smoke/full mixing 风险**
   - Mistral smoke 不能混入正文 compare set

### 9.2 三类评审视角下的防线

#### 答辩委员会

- 会问：你的论文到底在证明什么？
- 答法：证明的是 `behavior` 作为统一原则，以及 allocator 的 regime reality，不是单一 winner 方法

#### 顶会审稿

- 会问：soundness、related work、公平 baseline、claim boundary 是否清楚？
- 答法：在 `Ch2`、`Ch4`、threats 中显式处理

#### 期刊评审

- 会问：结构是否稳定、主线是否统一、图表是否服务同一问题
- 答法：通过 framework -> validation -> regimes -> extension 的单线结构统一

---

## 10. L2 接口预留方案（后移版）

当前 `L2` 必须预留，但不能污染 L1 主线。

### 10.1 L2-A: K/V asymmetric allocator

#### 位置

- `Chapter 3` 方法扩展段
- `Chapter 5` future work

#### 作用

把已有 `K > V` 诊断资产，真正变成预算分配方法。

#### 升级条件

- 必须显示相对 current symmetric mixed-kv 有稳定增益

### 10.2 L2-B: Quality-cost Pareto analysis

#### 位置

- 内部蓝图接口，不预设正文 subsection
- `Chapter 5` future work

#### 作用

决定 allocator 能否从“质量现象”升级为“预算分配方法”。

#### 升级条件

- 必须有 clean compare set 支撑

### 10.3 L2-C: Prompt-adaptive allocation

#### 位置

- `Chapter 3` extensibility sentence
- `Chapter 5` future work

#### 作用

说明静态全局 policy 之后的下一层控制，但当前不进入正文主结果。

#### 升级条件

- 必须证明 prompt-conditioned selector 超过 global static policy

---

## 11. Candidate-main / Final-ready 写作边界（强规则版）

### 11.1 生产层与叙事层的组合

允许出现的组合只有三类：

1. `exploratory-produced + candidate-main-readable`
   - 只能支撑结构性图表、stable reading、regime shape
2. `clean-produced + candidate-main-readable`
   - 可支撑更强 supporting assets
3. `clean-produced + final-ready`
   - 才允许 tight numeric winner claims 进入主文主表

### 11.2 Candidate-main 现在可进入草稿的资产类型

1. 框架图、位置图、接口图
2. 强调 `stable reading` 的 regime 图/表
3. anomaly 图表
4. provenance / triage / governance 表

但必须满足：

- 不出现 tight gap
- 不出现 winner/rank/best 列名
- caption 带 evidence-tier

### 11.3 Final-ready 前绝对不能进入主文主表的

1. cross-model winner table with tight gaps
2. auto-k final compare-set table
3. allocation quality-cost Pareto 主图
4. 当前 compare-set 赢家数字的 ranking chart
5. 任何 smoke/full 混合 compare

### 11.4 Auto-k 固定限定句

凡正文出现 `auto-k`，至少必须绑定一句限定：

1. `profile-aware budget proposer`
2. `strong extension`
3. `top-tier but not universal`
4. `explicit wins remain primarily Mistral-specific`

---

## 12. 实际写作顺序

不要按章节顺序写。推荐顺序：

0. 先清理 `Abstract / Ch1 / Ch5` 的旧 `C1/C2/C3` 信号
1. 先补 `Chapter 3` 中 allocation / auto-k 的方法身份
2. 再写 `Chapter 4` 新结构
3. 再写 `Chapter 1`
4. 再重写 `Chapter 2`
5. 最后写 `Chapter 5`
6. 最后回头重写 Abstract

原因：

- 当前论文主线的真正裁决层在数据和 audit，不在旧方法叙事
- 先把 `Ch4` 写顺，其余章节的定位才不会再次漂移

---

## 13. 一句话版本

如果只保留一句话，这篇论文现在应该被写成：

> 一篇以 `behavior` 为统一分析与设计原则、用 `INT8 canonical path` 建立主验证链、再通过 allocator 实验揭示 `family-/scale-/task-dependent regimes`，并把 `auto-k` 作为下游扩展的 framework 论文。

这句话是后续所有章节、图表、摘要、答辩陈述的统一锚点。

---

## 14. 逐章段落级蓝图

这一节不是正文代写，而是逐章的执行模板。每章都按“段落功能”来拆，不按旧稿顺序硬修。

### 14.1 Abstract 段落模板

#### 段落 1：问题与对象

功能：

- 定义 KV cache 量化问题的重要性
- 直接指出真正该保护的是 attention behavior，而不是只看数值误差

建议只说两件事：

1. 长上下文推理受 KV cache 显存/带宽约束
2. 单纯数值误差不足以解释真实质量退化

#### 段落 2：本文主张与框架

功能：

- 给出本文的总主张
- 明确本文是 `behavior-centric framework`，不是 winner method paper

必须包含：

1. `behavior` 是统一分析与设计原则
2. `INT8 canonical path` 是最干净的主验证链

#### 段落 3：经验现实与扩展

功能：

- 交代 allocator 主结果
- 收口 auto-k 的正确位置

必须包含：

1. empirical reading 是 regime-dependent
2. auto-k 是 profile-aware extension

不能包含：

- `KL > MSE`
- `auto-k universally best`
- `RoleAlign beats KIVI`

### 14.2 Chapter 1 段落模板

#### 1.1 研究背景

段落 1：

- 讲 KV cache 为什么成为长上下文瓶颈
- 只讲显存/带宽/并发三件事

段落 2：

- 讲量化为什么自然出现
- 不提前进入具体方法

#### 1.2 问题定义

段落 1：

- 从“量化会损伤质量”过渡到“损伤机制是什么”

段落 2：

- 解释为什么单看 MSE / percentile 不够
- 把 attention behavior 引出来

段落 3：

- 明确本文不再把“证明某方法更强”作为唯一问题
- 引出统一分析对象与统一设计原则

#### 1.3 本文定位

段落 1：

- 先给出 `behavior-centric framework` 定位

段落 2：

- 说明 `INT8 canonical path` 的角色

段落 3：

- 说明 allocator 结果为什么将问题推向 regime reading

段落 4：

- 说明 auto-k 是 extension，不是理论中心

#### 1.4 贡献列表

建议固定为 4 点，不要超过 4 点：

1. `behavior` 作为 unified principle
2. `INT8 canonical validated instance`
3. regime-dependent allocator reading
4. profile-aware auto-k extension

#### 1.5 章节组织

只写结构，不重复贡献。

### 14.3 Chapter 2 段落模板

#### 2.1 KV cache 与长上下文背景

段落 1：

- 只保留最小必要机制背景

段落 2：

- 用一句话把 KV cache 问题接到后面的设计轴

#### 2.2 三个设计轴

这节必须成为 `ch2` 的转轴。

段落 1：

- 定义 `format`

段落 2：

- 定义 `calibration signal`

段落 3：

- 定义 `allocation / budget policy`

结尾句必须把三条线接到 related work，而不是停留在定义。

#### 2.3 KIVI 与低比特格式线

段落 1：

- 正面承认 KIVI 的重要性

段落 2：

- 解释其解决的是格式与 runtime 轴

段落 3：

- 明确本文不把自己包装成“击败 KIVI 的单一格式方法”

#### 2.4 Behavior / calibration 线

段落 1：

- 为什么 attention distortion 值得成为分析对象

段落 2：

- behavior line 与纯数值重建线的区别

段落 3：

- 本文在这条线上的定位：不是证明 universal superiority，而是统一原则

#### 2.5 Allocation 线

段落 1：

- mixed precision / layer-wise allocation 的一般问题

段落 2：

- 现有方法为什么常停留在 heuristic / exhaustive tuning

段落 3：

- 本文在这一线上的位置：behavior-derived profile-guided allocation

#### 2.6 本文位置总结

这节必须单独成段，不能省。

必须回答：

1. 我们和 KIVI 的关系是什么
2. 我们和 generic mixed-precision allocator 的关系是什么
3. 为什么本文是 framework work，而不是单一 winner method

### 14.4 Chapter 3 段落模板

#### 3.1 Principle

段落 1：

- 定义 `behavior` 在本文里是什么意思

段落 2：

- 明确这是一种 design principle，不是结论先行的 winner claim

#### 3.2 Framework overview

段落 1：

- 给出离线 / 在线二阶段概览

段落 2：

- 引出 calibration artifact 和 policy artifact 的区别

#### 3.3 Behavior-aligned calibration

段落 1：

- 讲 calibration 产物是什么

段落 2：

- 讲它如何服务 `INT8 canonical path`

段落 3：

- 加一句边界：这一步在 `INT8` 上不等于证明 `KL > MSE`

#### 3.4 INT8 canonical validated instance

段落 1：

- 为什么选 INT8 当 canonical

段落 2：

- 它验证的是 framework 可落地，不是所有 superiority 命题

#### 3.5 Behavior-guided allocation

段落 1：

- 定义 allocation 问题：预算分给谁

段落 2：

- 说明 behavior-derived profile 怎样作为 guiding signal

段落 3：

- 明确这一步是 `guided`，不是再次直接 `aligned`

#### 3.6 Auto-k extension

段落 1：

- 说明 fixed-k 为什么不够

段落 2：

- 说明 auto-k 的 coverage-based proposer 逻辑

段落 3：

- 收一句：它是 extension，不是理论中心

#### 3.7 Runtime / system interface

段落 1：

- system integration 与 policy consumption

段落 2：

- 为未来 `K/V asymmetric` 和 prompt-adaptive 留接口

### 14.5 Chapter 4 段落模板

#### 4.1 Evidence tiers

段落 1：

- 先交代证据分层

段落 2：

- 交代当前是 `candidate-main`

#### 4.2 INT8 canonical section

段落 1：

- 讲它证明了什么

段落 2：

- 讲它没有证明什么

这一节必须避免“INT8 已证明 KL 更强”的读法。

#### 4.3 7B regime section

段落 1：

- 先给 strongest finding

段落 2：

- 再解释为什么它支持 regime 而不是 universal law

#### 4.4 8B / 14B / Mistral cross-scale section

写法顺序建议：

1. 8B：旧 fixed-k 叙事失效的转折点
2. 14B：strong baseline / broad high-quality band
3. Mistral：auto-k 最强正例

每个模型都按三段写：

1. 现象
2. 稳定读法
3. 不能过度解释的边界

#### 4.5 3B anomaly section

按两段写：

1. `first-layer rescue` 现象
2. 为什么它是 anomaly / regime，而不是 universal rule

#### 4.6 Heuristic section

必须单列，不要混在 compare 表后面一句带过。

按两段写：

1. heuristic 为什么必须被重新定位
2. 这对 allocator 叙事意味着什么

#### 4.7 Auto-k section

按三段写：

1. auto-k 为什么出现
2. 当前最强支撑是什么
3. 为什么它现在仍只能写成 strong extension

#### 4.8 Provenance / threats section

必须按三段写：

1. 当前证据层级
2. 当前可以支持什么 claim
3. clean-provenance 后才能升级什么

### 14.6 Chapter 5 段落模板

#### 5.1 核心发现

建议按四段短段收：

1. behavior principle
2. INT8 canonical path
3. regime-dependent allocator reality
4. auto-k extension

#### 5.2 局限性

至少必须写：

1. provenance 仍是 `candidate-main`
2. auto-k 仍非 universal winner
3. L2 方向尚未进入主结果

#### 5.3 未来工作

固定只写三条：

1. K/V asymmetric allocator
2. quality-cost Pareto
3. prompt-adaptive policy selection

---

## 15. 章节衔接模板

### 15.1 Abstract -> Chapter 1

建议过渡含义：

> 摘要已经给出最终读法；引言负责把这个读法拆成可回答的研究问题。

### 15.2 Chapter 1 -> Chapter 2

建议结尾句模板：

> 既然问题不再只是寻找一个普适更优的量化器，而是重新定义 calibration 与 allocation 的分析对象，就必须重新审视已有工作分别解决了哪个设计轴上的问题。

### 15.3 Chapter 2 -> Chapter 3

建议结尾句模板：

> 基于上述相关工作重排，本文的方法不应被理解为单点技巧，而应被理解为一套从 behavior-derived signal 出发、贯穿 calibration 与 allocation 的框架。

### 15.4 Chapter 3 -> Chapter 4

建议结尾句模板：

> 在这一框架下，实验的目标不再是寻找唯一 winner，而是验证 canonical path 的有效性，并识别 allocator 在不同模型族中的稳定 operating regimes。

### 15.5 Chapter 4 -> Chapter 5

建议结尾句模板：

> 因而，结论的重点不应是宣称单一方法胜出，而应是总结 framework 成立的范围、regime-dependent 的经验现实，以及 extension 的边界。

---

## 16. 逐章图表插槽与 caption 边界

### 16.1 Chapter 1

#### 图：Behavior-Centric Thesis Argument Map

- 插槽：引言最后，章节组织前
- 服务段落：`1.3 本文定位`
- caption 应写：
  - framework / validation / regimes / extension
- caption 不可写：
  - “overall superiority pipeline”
  - “proves universal optimality”

### 16.2 Chapter 2

#### 表：Prior Work Positioning Matrix

- 插槽：相关工作总结末尾
- 服务段落：`2.6 本文位置总结`
- caption 应写：
  - relation / positioning / design axis
- caption 不可写：
  - “comparison with inferior baselines”
  - “our method dominates prior work”

### 16.3 Chapter 3

#### 图：Behavior-Guided Framework Figure

- 插槽：方法总览开头
- 服务段落：`3.2 Framework overview`
- caption 应写：
  - offline calibration artifact + allocation policy + runtime execution
- caption 不可写：
  - “RoleAlign-centered architecture”

#### 图：Auto-K Range Proposer Schematic

- 插槽：`3.6 Auto-k extension`
- 服务段落：fixed-k insufficiency + coverage proposer
- caption 应写：
  - sensitivity coverage / candidate ks / recommended budget
- caption 不可写：
  - “globally optimal k selector”

### 16.4 Chapter 4

#### 表：Cross-Model Regime Summary Table

- 插槽：cross-scale evidence 小节开头
- 服务段落：模型级 stable reading 总览
- caption 应写：
  - stable reading / regime summary / candidate-main evidence
- caption 不可写：
  - “cross-model generalization proof”

#### 图：Family Regime Map

- 插槽：`4.4 Cross-scale allocator evidence`
- 服务段落：不同 family / scale 的读法差异
- caption 应写：
  - operating regimes / model-family differences
- caption 不可写：
  - “single global trend”

#### 图：3B First-Layer Rescue Figure

- 插槽：`4.5 3B anomaly`
- 服务段落：异常 regime 解释
- caption 应写：
  - anomaly / first-layer bottleneck / rescue
- caption 不可写：
  - “general law for small models”

#### 表：Heuristic Baseline Reposition Table

- 插槽：`4.6 Heuristic section`
- 服务段落：baseline 重新定位
- caption 应写：
  - heuristic remains strong baseline
- caption 不可写：
  - “heuristic is weak control”

#### 图/表：Provenance Ladder

- 插槽：`4.8 Provenance / threats`
- 服务段落：边界披露
- caption 应写：
  - exploratory / candidate-main / final-ready
- caption 不可写：
  - 暗示当前 compare-set 已 final-ready

### 16.5 Caption 与表头的强制规则

#### Caption 禁词

在 `final-ready` 前，主文图表 caption 禁用：

- `best`
- `winner`
- `optimal`
- `dominates`
- `generalizes`
- `proves`

#### 表头禁词

在 `final-ready` 前，主文表头禁用：

- `best overall`
- `winner`
- `rank #1`
- `gap to best`
- `optimal`

#### 主文允许的 coarse reading 用语

在 `candidate-main` 阶段，只允许这类口径：

- `stable reading`
- `top-tier`
- `strong extension`
- `broad high-quality band`
- `Mistral-specific explicit win`
- `regime-dependent`

---

## 17. 逐章不能写的句子黑名单

### 17.1 全文通用黑名单

以下句型不应再出现：

1. “我们证明了 behavior-aligned 方法普适优于现有方法”
2. “INT8 结果证明了 KL 优于 MSE”
3. “RoleAlign 明显优于 KIVI-style”
4. “auto-k 在所有模型上都是最佳策略”
5. “best-k 随模型规模单调上移”
6. “本文发现了统一的 allocation law”

### 17.2 Chapter 1 黑名单

1. “本文提出三个并列核心贡献：KL、RoleAlign、kernel”
2. “本文主要证明了低比特方法优于现有方法”

### 17.3 Chapter 2 黑名单

1. “KIVI 只是一个待击败 baseline”
2. “本文填补四个空白，因此优于 prior work”

### 17.4 Chapter 3 黑名单

1. “allocator 直接优化 attention-KL”
2. “auto-k searches the globally optimal protection budget”

### 17.5 Chapter 4 黑名单

1. “cross-model generalization is established”
2. “Mistral confirms universal auto-k superiority”
3. “3B reveals a general small-model law”
4. “current Phase 2.6 numbers are final-ready”

### 17.6 Chapter 5 黑名单

1. “本文最终证明了 behavior-guided quantization 普适更优”
2. “auto-k is the new theory center”

---

## 18. Claim Gate 与实际撰写流程

### 18.1 Gate A：结构 Gate

满足以下条件后，才进入正文改写：

1. `Ch1-Ch5` 的使命与衔接已经固定
2. 图表系统已经完成新旧资产分流
3. `Chapter 2` 的 prior-work 定位已收敛
4. `Abstract / Ch1 / Ch5` 的旧 `C1/C2/C3` 信号已清理
5. `Chapter 3` 已正式建立 allocation / auto-k 方法桥

### 18.2 Gate B：Candidate-main Gate

进入正文 draft 时，只允许写：

1. framework-level claims
2. regime-level readings
3. extension-level cautious claims

不允许写：

1. final-ready winner tables
2. tight numeric superiority claims
3. smoke/full 混合 compare
4. `winner / rank / gap to best` 列名或 caption

### 18.3 Gate C：Final-ready Gate

以下内容只有在 clean-provenance rerun 覆盖后才允许升级：

1. final compare-set tables
2. tight gap ranking charts
3. “near-best across models” 这类强数值句子

### 18.3.1 结果生产层升级条件

若资产仍是 `exploratory-produced`，即使 narrative 已到 `candidate-main`，也不得升级为主文 final table。

### 18.4 真正的执行顺序

1. 先清 `Abstract / Ch1 / Ch5` 的旧 `C1/C2/C3` 信号
2. 先补 `Chapter 3` 中 allocation / auto-k 的方法身份
3. 再按本蓝图重写 `Chapter 4` 结构稿
4. 用 `Chapter 4` 反推 `Chapter 1` 贡献列表
5. 重写 `Chapter 2` 定位
6. 最后收 `Chapter 5`
7. clean-provenance 完成后，再升级 final tables

### 18.5 下一轮蓝图应再细化到哪里

当真正进入正文改写前，还应再做一层：

1. 每章“保留段落 / 删除段落 / 搬移段落”清单
2. 每个新增图表的 LaTeX 插入点
3. 每章首段和末段的实际中文草稿模板

---

## 19. 正文迁移清单

这一节直接面向现有 `thesis/chapters/*.tex`。目标不是重写，而是回答：**现有正文里的每个部分，最后该怎么办。**

处理动作含义：

- `保留`：基本角色正确，只需轻微重写
- `重写`：标题可保留，但内部逻辑必须改
- `搬移`：内容本身有用，但不应留在当前位置
- `降级`：保留为 supporting / appendix / 背景弱化
- `删除`：与新主线直接冲突，不再保留

### 19.1 Abstract 迁移清单

| 当前单元 | 动作 | 原因 | 新角色 |
|---|---|---|---|
| “三方面贡献”整体框架 | `删除` | 继续编码旧 `C1/C2/C3` 三贡献结构 | 改成 `principle -> canonical validation -> regimes -> extension` |
| `attention-KL` 统一原则 | `保留` | 可作为 unified principle | 摘要第 2 段中心句 |
| `INT4-RoleAlign` 大段 hero 叙述 | `删除` | 与新主线冲突，且易被追问 KIVI | 只保留为 low-bit extension 背景，不在摘要做主角 |
| kernel 相位图第三贡献 | `降级` | 系统证据存在，但不是摘要主轴 | 如保留，只能作为 supporting system evidence 轻带 |
| 结尾“覆盖诊断、校准、部署全链路” | `重写` | 太像旧三块拼接 | 改成 framework + regimes + extension 的总收束 |

### 19.2 Chapter 1 迁移清单

| 当前单元 | 动作 | 原因 | 新角色 |
|---|---|---|---|
| `研究背景` | `保留` | 可服务 KV cache bottleneck 定义 | 继续作为开篇 |
| `问题定义与研究动机` | `保留并重写` | 方向对，但要从 winner problem 改为 object/principle problem | 引出 `behavior` 作为分析对象 |
| `国内外研究现状` | `降级` | 目前放在 `Ch1` 太抢 `Ch2` | 只保留轻量预告，把主 related work 挪到 `Ch2` |
| `本文研究内容与主要贡献` | `重写` | 目前仍是旧三贡献 | 改成四点：principle / canonical / regimes / extension |
| `fig:ch1-pipeline` | `重画替换` | 旧图仍是 C1/C2/C3 | 换成 `Behavior-Centric Thesis Argument Map` |
| `论文组织结构` | `重写` | 还在承诺旧三块 | 改成 framework-driven chapter map |

### 19.3 Chapter 2 迁移清单

| 当前单元 | 动作 | 原因 | 新角色 |
|---|---|---|---|
| `Transformer 架构与自注意力机制` | `降级并压缩` | 教材味太重 | 只保留最小必要背景 |
| `KV Cache 机制与显存分析` | `保留并压缩` | 有必要，但不应过长 | 服务问题定义 |
| `模型量化技术基础` | `重写` | 不能只讲量化常识 | 改写成“设计轴：格式 / signal / allocation” |
| `KV Cache 量化相关工作` | `重写` | 旧 related work 还在服务旧主线 | 改成 prior-work 三线：format / behavior / allocation |
| `量化对注意力分布的影响` | `保留并前移逻辑作用` | 是 behavior line 的关键桥 | 明确支撑本文分析对象 |
| `高效注意力计算` | `降级` | 仍需存在，但只能做 supporting background | 放到后半段 |
| `本章小结` | `重写` | 旧“填补空白”口气要去掉 | 改成“本文位置与 claim boundary” |
| `tab:kv_quant_compare` | `重写替换` | 当前 compare 容易引导 superiority | 换成 `Prior Work Positioning Matrix` |

### 19.4 Chapter 3 迁移清单

| 当前单元 | 动作 | 原因 | 新角色 |
|---|---|---|---|
| `框架总体设计` | `保留并重写` | 仍是正确入口 | 改成 framework > artifact > policy |
| `行为对齐校准方法` | `保留并收窄` | 需要，但要去掉 `KL superiority` 口气 | 只承担 calibration 角色 |
| `自适应保护与 INT8 对称量化配置` | `重写` | 这是 canonical path 的核心 | 变成 `INT8 canonical validated instance` |
| `KIVI-style 格式上的行为引导实例化 RoleAlign` | `降级并拆解` | 不能再当章节中心 | 只保留为 low-bit instantiation / relation to KIVI |
| `Triton 融合量化解码注意力` | `降级` | 系统重要，但不再是主轴 | 移到系统与接口后部 |
| `系统实现与复杂度分析` | `保留` | 仍可服务可落地性 | 支持 runtime routing |
| `fig:ch3-framework` | `重画替换` | 旧 caption 仍把 RoleAlign 放顶层 outcome | 换成 `Behavior-Guided Framework Figure` |
| `fig:ch3-calib-pipeline` | `保留并改 caption` | 仍有用 | 明确是 calibration artifact 产出 |
| `fig:ch3-invtau-heatmap` | `降级附录` | 不应占正文中心 | supporting only |
| `tab:ch3-rolealign-vs-kivi` | `搬移并重写` | 不应继续留在方法章中心 | 搬到 `Ch2` 或 appendix，作为 relation table |
| `tab:ch3-kv-modes` | `保留并压缩` | 可作为接口总览 | 改写成 policy/interface summary |

### 19.5 Chapter 4 迁移清单

| 当前单元 | 动作 | 原因 | 新角色 |
|---|---|---|---|
| `实验设置` | `保留并轻重排` | 仍需存在 | 开头加入 evidence tiers |
| `校准目标的 bit-width 依赖与 INT8 主线参考` | `保留并重写` | 应转成“INT8 证明了什么 / 没证明什么” | canonical validated instance |
| `低比特失效的结构性诊断：Key 主导与架构依赖` | `保留并降级` | 支撑 behavior 视角，但不再是全文中心 | 作为 supporting diagnosis |
| `KIVI-style 格式上的行为引导实例化：INT4-RoleAlign` | `降级并拆散` | 不能再作为主结果 section | 其设计/边界改写进 relation / appendix |
| `GQA-Aware 部署效率分析` | `降级` | 仍有价值，但不应与 regime 并列 | supporting system evidence |
| `综合讨论` | `重写` | 旧综合讨论不适配新主线 | 改成 provenance / claim boundary / threats |

#### Chapter 4 必须新增的结构块

1. `7B` strongest finding 小节
2. `8B / 14B / Mistral` cross-scale regime 小节
3. `3B anomaly` 小节
4. `Heuristic baseline` 单列小节
5. `Auto-k` 作为 extension 单列小节
6. `Provenance / claim boundary` 单列小节

### 19.6 Chapter 5 迁移清单

| 当前单元 | 动作 | 原因 | 新角色 |
|---|---|---|---|
| `核心发现与收束` | `重写` | 旧三发现收尾与新主线冲突 | 改成 principle / canonical / regimes / extension |
| `局限性` | `保留并强化` | 这里必须承接 provenance boundary | 显式写 `candidate-main` 边界 |
| `未来工作展望` | `保留并后移 L2` | 现在的 future 应只保留接口 | 只写 K/V asymmetric / Pareto / prompt-adaptive |
| `结语` | `重写` | 旧结尾仍有旧主线余味 | 改成 framework 收束 |

---

## 20. 逐图逐表命运清单

这一节直接处理 thesis 现有图表资产。原则是：**先判命运，再讨论重画。**

### 20.1 Chapter 1 图表命运

| 图/表 | 当前角色 | 动作 | 最终命运 |
|---|---|---|---|
| `fig:ch1-pipeline` | 旧 C1/C2/C3 总览图 | `删除并替换` | 换成 `Behavior-Centric Thesis Argument Map` |

### 20.2 Chapter 2 图表命运

| 图/表 | 当前角色 | 动作 | 最终命运 |
|---|---|---|---|
| `tab:kv_quant_compare` | KV quant 相关工作比较 | `重写替换` | 换成 `Prior Work Positioning Matrix` |

### 20.3 Chapter 3 图表命运

| 图/表 | 当前角色 | 动作 | 最终命运 |
|---|---|---|---|
| `fig:ch3-framework` | 旧 framework 主图 | `删除并替换` | 换成 `Behavior-Guided Framework Figure` |
| `fig:ch3-calib-pipeline` | calibration 流程图 | `保留并改 caption` | 继续服务 calibration artifact |
| `fig:ch3-invtau-heatmap` | 温度校正探索图 | `降级附录` | supporting only |
| `tab:ch3-rolealign-vs-kivi` | 方法差异表 | `搬移并重写` | `Ch2` relation 或 appendix |
| `tab:ch3-kv-modes` | 量化模式总览 | `保留并压缩` | 改成 policy / interface summary |

### 20.4 Chapter 4 图表命运

| 图/表 | 当前角色 | 动作 | 最终命运 |
|---|---|---|---|
| `tab:main-results` | 旧主结果表 | `保留并降口气` | 只服务 `INT8 canonical` |
| `fig:main-quality-dashboard` | 旧主质量图 | `保留并重写角色` | 只服务 canonical validated instance |
| `fig:main-efficiency-dashboard` | 旧主效率图 | `保留并重写角色` | 只服务 canonical validated instance |
| `tab:cross-model` | 旧“跨模型泛化性验证” | `重写或降级` | 若保留，必须改成 regime summary supporting table |
| `tab:kivi-comparison` | `INT8-Canonical vs KIVI-style` | `降级` | appendix / supporting |
| `tab:kv-ablation-ppl` | K/V ablation | `压缩并保留 summary` | 与相关表合并成一张 summary |
| `tab:kv-ablation-ruler` | K/V ablation | `降级附录` | appendix |
| `tab:kv-ablation-longbench` | K/V ablation | `降级附录` | appendix |
| `fig:kv-ablation-summary-ruler` | K/V 机制图 | `保留并降级角色` | supporting diagnosis |
| `fig:attn-kl-heatmap-pair` | 配对热图 | `降级附录` | supporting only |
| `tab:mixedkv-cross-model` | MixedKV 对比 | `降级` | supporting only |
| `tab:14b-kv-ablation` | 14B K/V ablation | `降级` | supporting only |
| `tab:rolealign-results` | 旧 RoleAlign 跨四模型表 | `降级附录` | appendix |
| `fig:rolealign-summary` | 旧 RoleAlign hero 图 | `删除` | 不再保留 |
| `fig:ppl-vs-scale` | 旧 scale-shift 图 | `删除` | 不再保留 |
| `tab:invtau-ablation` | 探索性观察表 | `降级附录` | appendix |
| `tab:int4-tpot-cross-model` | INT4 TPOT 对比 | `降级附录` | appendix |
| `tab:kivi-int4-threeway` | INT4 三方对比 | `降级附录` | appendix |
| `tab:phase1-tpot` | deployment 表 | `降级` | appendix 或 supporting |
| `tab:longseq-tpot-14b` | deployment 表 | `降级` | appendix 或 supporting |
| `tab:phase-boundary` | deployment 表 | `降级` | appendix 或 supporting |
| `tab:kv-memory-sweep` | memory 表 | `保留并降级角色` | supporting system evidence |
| `fig:pareto-quality-efficiency` | 旧 Pareto 主图 | `删除或禁用` | 等 future Pareto 真正 ready 再议 |

### 20.5 必须新增的新资产

| 新资产 | 目标章节 | 作用 | 当前层级 |
|---|---|---|---|
| `Behavior-Centric Thesis Argument Map` | `Ch1` | 全文主线总图 | 主文核心 |
| `Prior Work Positioning Matrix` | `Ch2` | prior-work 定位 | 主文核心 |
| `Behavior-Guided Framework Figure` | `Ch3` | calibration / allocation / auto-k 三层 | 主文核心 |
| `Auto-K Range Proposer Schematic` | `Ch3` | auto-k 是 proposer，不是全局最优搜索 | supporting-only |
| `Cross-Model Regime Summary Table` | `Ch4` | stable reading 总表 | 主文核心 |
| `Family Regime Map` | `Ch4` | 主图 | 主文核心 |
| `3B First-Layer Rescue Figure` | `Ch4` | 3B anomaly | 主文核心 |
| `Heuristic Baseline Reposition Table` | `Ch4` | heuristic 正名 | supporting-only |
| `INT8 Claim Boundary Table` | `Ch4` | 封住 `KL > MSE` 误读 | 边界型资产 |
| `Compare-Set Governance Table` | `Ch4/Appendix` | 封住 compare-set 串层 | 边界型资产 |
| `Provenance Ladder` | `Ch4/Appendix` | 结果层级 | supporting-only |
| `Extend-Task Triage Table` | `Ch4/Appendix` | 限制低信息量任务污染 | supporting-only |

---

## 21. 每章首段与末段功能

### 21.1 Abstract

- 首句功能：只定义问题，不预支方法胜负
- 末句功能：只收 framework + regimes + extension，不写 final-ready winner

### 21.2 Chapter 1

- 首段功能：讲清 KV cache bottleneck
- 末段功能：把 related work 需求自然引到 `Chapter 2`

### 21.3 Chapter 2

- 首段功能：告诉读者这章的任务是“定位”，不是“教课”
- 末段功能：明确本文不是单一 winner method，而是 framework paper

### 21.4 Chapter 3

- 首段功能：定义 principle 与 artifact / policy 的区别
- 末段功能：把实验问题切换成 canonical validation + regime reading

### 21.5 Chapter 4

- 首段功能：先交代 evidence tier，再开始结果
- 末段功能：显式收口“现在支持的读法”，并把 final-ready 留给 provenance

### 21.6 Chapter 5

- 首段功能：按四件事收束，不再回旧三贡献
- 末段功能：只保留 clean-provenance 与 L2 接口，不预支结论
