# Behavior-Guided Adaptive Allocation：主计划与扩展候选池（备用路线图）

> 文档定位：**备用路线图 / 结构化决策文档**
>
> 本文件用于整理当前论文主执行线与未来可扩展方向的关系，避免在 `编号 7` 及之后的阶段因研究问题持续扩容而打乱主计划。  
> 本文件**不是**当前唯一权威执行计划；当前权威主计划仍以：
>
> - `/Users/chenzilang/.claude/plans/partitioned-sparking-newt.md`
>
> 为准。

---

## 1. 背景与目的

截至 `2026-04-18`，论文主线已经完成以下关键阶段：

- `编号 1-4`：官方 LongBench 证据底座 + 7B 复核
- `编号 5`：Gate 5 PASS，确认 fixed-bit 路线“站得住”
- `编号 6`：Layer-wise Allocator MVP 完成，且硬 gate PASS，证明 `BAKV > Random`

这意味着论文已经从：

- `attention-KL` 只是一个解释器（diagnostic lens）

推进到：

- `attention-KL` 至少可以驱动一个最小 `layer-wise allocator`，即具备 `lens -> policy` 的第一层证据

但与此同时，随着 allocator 线被打开，研究方向开始自然扩展。典型新方向包括：

- `K/V` 非对称 allocator
- 跨模型验证
- harder benchmark
- Pareto 分析
- reasoning 外推
- head-wise / token-wise allocation
- prompt-adaptive / learned allocator
- serving integration
- theory / benchmark 论文化

这些方向**都值得做**，但它们并不适合在当前阶段全部并入主执行线。  
如果在 `编号 7` 之前或执行中把这些扩展全部塞回主计划，会出现两个明显问题：

1. 当前最关键的问题会失焦  
   即：`BAKV` 是否真的比简单位置 heuristic 更强。

2. 执行范围会不断膨胀  
   造成“实验做得越来越多，但论文主结论并没有更清楚”。

因此，本文件的核心目的，是在不否定扩展方向价值的前提下，建立一个**双轨结构**：

- **A 栏：当前主计划（Active Mainline）**
- **B 栏：扩展候选池（Expansion Candidate Pool）**

这个结构的作用不是增加计划复杂度，而是明确：

- 什么是**现在必须做**的
- 什么是**以后可以做，但现在不能自动并入主线**的

---

## 2. 当前执行状态（冻结事实）

本节只记录当前已成立的阶段事实，用于界定后续所有判断的起点。

### 2.1 已完成阶段

| 编号 | 阶段 | 当前状态 | 作用 |
|------|------|----------|------|
| 1 | 起点锁定 + 真冒烟 | 已完成 | 建立实验链路与可跑矩阵 |
| 2 | 1.5B 官方 LongBench | 已完成 | 拿到第一张官方主矩阵 |
| 3 | 整理第一张官方主表 | 已完成 | 形成主表与初步主张 |
| 4 | 7B 复核 | 已完成 | 提供跨规模一致性支撑 |
| 5 | Gate 5 | 已完成，PASS | 解锁 allocator 线 |
| 6 | Layer-wise Allocator MVP | 已完成，硬 gate PASS | 证明 `BAKV > Random` |

### 2.2 当前唯一活跃执行项

截至本文件撰写时，当前主计划里**唯一活跃的下一步**是：

- **`编号 7：Budget Sweep + 消融`**

因此：

- `编号 1-6` 视为**已完成并冻结的事实基础**
- `编号 7` 视为**当前唯一活跃执行项**
- `编号 8-10` 以及下文所有新增扩展方向，均不得自动进入执行线

---

## 3. 总原则：A 栏负责做完，B 栏负责做强

从 `编号 7` 起，计划正式采用如下治理原则：

### 原则 1：A 栏优先，B 栏冻结

在 `编号 7` 得到明确 verdict 之前：

- 只推进 A 栏中的当前活跃项
- 不因 B 栏中的任何新方向中断 `编号 7`
- 不以“顺手一起做”的方式把新方向并进当前主实验矩阵

### 原则 2：编号 7 是判定步，不是默认扩张步

`编号 7` 的使命不是“继续做更多实验”，而是回答一个更强的问题：

> `attention-KL` 驱动的 allocator，是否在不同 budget 下真正具有相对位置 heuristic 的独占方法价值？

因此，`编号 7` 的结果将被当作一个真正的闸门：

- 如果 `BAKV` 明显优于 `Heuristic`，才进入更强扩展
- 如果 `BAKV ≈ Heuristic`，则应诚实收口，而不是继续无边界扩题

### 原则 3：A 栏回答当前问题，B 栏保留未来升级空间

当前论文最重要的不是“把所有未来好方向都做掉”，而是：

- 把已经启动的 allocator 线做出清晰 verdict
- 根据 verdict 决定论文的最终身份

因此，B 栏的定位是：

- 不丢失未来最有价值的升级方向
- 但不提前消耗当前主线的执行专注度

---

## 4. A 栏：当前主计划（Active Mainline）

### 4.1 定义

A 栏指的是：

> **为了让当前论文形成清晰、可投稿、可答辩主结论而必须执行的最小闭环路线。**

它的目标不是探索所有可能性，而是让当前论文在可控范围内完成从：

- `v6-stable`

到：

- `v7-full-mvp`
- 或更高一档

的升级。

### 4.2 当前 A 栏的范围

| 编号 | 内容 | 状态 | 在 A 栏中的作用 |
|------|------|------|----------------|
| 1-4 | 官方 LongBench + 7B 复核 | 已完成 | 证明 fixed-bit 路线在现实 benchmark 上可讲 |
| 5 | Gate 5 | 已完成 | 解锁 allocator 线 |
| 6 | Allocator MVP | 已完成 | 证明 `BAKV > Random` |
| 7 | Budget Sweep + 消融 | 当前唯一活跃项 | 判断 `BAKV` 是否真正强于 `Heuristic` |
| 8 | 跨模型验证 | 条件触发 | 仅在 `编号 7` verdict 足够强时进入 |
| 11-13 | 论文收口 | 强制执行 | 任意停点都必须执行 |

### 4.3 A 栏当前只回答一个问题

当前阶段，A 栏必须把问题收紧到一个单一判定：

> **在固定 budget 下，behavior-guided allocation 是否稳定优于简单位置 heuristic，并且 `max(k_scale)` 是否比更简单聚合方式更有价值？**

这意味着，A 栏当前**不承担**以下问题：

- `K/V` 非对称 allocator 是否更优
- 是否跨架构泛化到 LLaMA
- 是否在 NoLiMa / BABILong 上仍成立
- 是否对 reasoning trace 同样有效
- 是否应升级为 online / prompt-adaptive allocator
- 是否应直接转向 serving runtime integration

这些全部转入 B 栏。

### 4.4 A 栏当前的唯一任务

当前主执行线只应理解为：

1. 完成 `编号 7`
2. 根据 `编号 7` verdict 决定是否进入 `编号 8`
3. 任意停点后执行 `编号 11-13`

换言之：

- **当前主线不是“继续无限扩展 allocator”**
- **当前主线是“让 allocator 线得到明确 verdict”**

---

## 5. B 栏：扩展候选池（Expansion Candidate Pool）

### 5.1 定义

B 栏指的是：

> **当前不并入主执行线、但在 `编号 7` 或之后可根据结果选择性纳入的增强方向。**

B 栏存在的目的不是“列愿望清单”，而是：

- 防止高价值想法在当前收敛执行中丢失
- 同时避免当前主计划被这些新想法拖散

为便于后续决策，B 栏分为三层：

- **B1：适合当前论文继续增强**
- **B2：适合下一阶段升级**
- **B3：更适合下一篇论文或长期项目**

---

## 6. B1：适合“当前论文继续增强”的候选

这类方向与当前论文最连续。一旦 `编号 7` 结果够强，它们就是最自然的增强项。

### 6.1 K/V 非对称 allocator

#### 内容

将已有 RoleAlign / K-V 不对称发现真正纳入 allocator：

- 不只决定“保护哪些层”
- 还决定“保护 K 还是 V”
- 以及 `(8,8)`、`(8,4)`、`(4,8)` 等位宽组合

#### 为什么重要

你们已有工作里最有价值的已有资产之一，就是：

- `K > V` 的敏感性不对称

如果 allocator 完全不把这一点利用起来，那么 current line 和已有论文资产的连接就不够强。

#### 更适合的纳入时机

- `编号 7` 完成后
- 且 allocator 主线确认值得继续扩展时

#### 预期价值

- 让 adaptive allocation 真正继承论文已有核心发现
- 让方法从“层保护”升级成“role-aware allocation”

---

### 6.2 跨模型验证（LLaMA-3.1-8B 优先）

#### 内容

在 `Qwen2.5-1.5B / 7B` 之外，补一个不同模型族：

- `LLaMA-3.1-8B-Instruct` 优先

#### 为什么重要

如果 allocator 线只在 Qwen 内成立，那么论文容易被质疑为：

- 同家族规律
- 而非更一般的分配现象

#### 更适合的纳入时机

- `编号 7` PASS 后
- 作为 `编号 8` 的主体或增强版

#### 预期价值

- 把结论从“Qwen 家族现象”升级为“跨模型现象”
- 显著增强论文的泛化叙事

---

### 6.3 Harder benchmark（NoLiMa 优先）

#### 内容

在官方 LongBench 之外，补更难、更能打掉 lexical shortcut 的 benchmark：

- `NoLiMa` 优先
- `BABILong` 次之

#### 为什么重要

LongBench 能证明 allocator 不是只在 synthetic benchmark 上成立，但它还不足以完全回答：

- allocator 是否真正改进了更难的长上下文理解

#### 更适合的纳入时机

- `编号 7` 或 `编号 8` 完成后
- 当主结论已经初步成立、需要增强说服力时

#### 预期价值

- 从“官方主表成立”走向“更难任务也成立”
- 提升结果的现实解释力

---

### 6.4 Pareto 分析

#### 内容

从单纯 quality 对比升级到：

- quality
- avg_bits / memory
- latency / TTFT / TPOT

的 Pareto 分析。

#### 为什么重要

当前 allocator 线如果只比较分数，会更像“质量小技巧”；  
加入 Pareto 后，它才更像一个真正的资源分配框架。

#### 更适合的纳入时机

- `编号 7` 完成后优先考虑
- 若论文要向更强版本推进，则应尽快加入

#### 预期价值

- 把 allocator 从“局部改进”升级成“预算分配方法”
- 更贴近实际 deployment / serving 叙事

---

## 7. B2：适合“下一阶段升级”的候选

这类方向和当前论文仍有较强连续性，但复杂度更高，适合在主线更稳后再纳入。

### 7.1 Reasoning validation

#### 内容

在 reasoning 模型或长 CoT 场景补一个小规模验证：

- `DeepSeek-R1-Distill-Qwen-7B`
- `MATH-500`

#### 为什么重要

如果 behavior-guided allocation 在 reasoning trace 上也成立，论文叙事会明显变强。

#### 更适合的纳入时机

- 当前 allocator 主线已经稳住
- 需要进一步提高论文上限时

#### 预期价值

- 把 allocator 从 chat / retrieval 外推到 reasoning
- 让工作更贴近 2025-2026 的热点方向

---

### 7.2 Head-wise allocation

#### 内容

从 layer-wise 扩展到 head-wise：

- 判断敏感性是层现象还是头现象
- 研究 GQA / KV head grouping 的细结构

#### 为什么重要

layer-wise 已经足够支撑 MVP，但如果要让方法更精细，head-wise 是自然下一步。

#### 更适合的纳入时机

- layer-wise 版本稳定后
- 作为方法深度增强项，而非第一优先级

#### 预期价值

- 提升方法精细度
- 让行为信号与模型内部结构更紧密对齐

---

### 7.3 Token-region allocation

#### 内容

引入序列维度：

- recent tokens 高精度
- old tokens 低精度
- 不同 token 区域不同精度策略

#### 为什么重要

当前 allocator 只回答“网络里哪里该保高 bit”，还没有回答“序列里哪里该保高 bit”。

#### 更适合的纳入时机

- 当前 layer-wise 路线成熟后
- 作为从“层级分配”走向“序列分配”的扩展

#### 预期价值

- 更贴近真实长上下文使用场景
- 更可能形成更强 memory / latency tradeoff

---

### 7.4 Prompt-adaptive allocation

#### 内容

不同输入不共享同一 policy，而是：

- 按任务类型
- 按 prompt 特征
- 按输入统计量

动态选择不同分配策略。

#### 为什么重要

当前 allocator 还是离线、静态、全局共享 policy；  
prompt-adaptive 是走向更成熟 allocator 的关键一步。

#### 更适合的纳入时机

- 静态 allocator 版本已经可信后

#### 预期价值

- 从 static allocation 升级为 input-adaptive allocation
- 更接近下一阶段的方法论文

---

## 8. B3：更适合下一篇论文或长期项目的候选

这类方向价值很高，但不应作为当前主线立即并入。

### 8.1 Learned allocator / predictor

#### 内容

从手工规则转向学习型方法：

- 小预测器
- behavior signal 作为 supervision
- 自动输出 layer/head/token budget

#### 更适合

- 下一篇方法论文
- 当前 allocator 线成功后的自然升级项目

---

### 8.2 Serving runtime integration

#### 内容

例如：

- paged KV
- vLLM
- serving-aware mixed precision
- online budget scheduling

#### 更适合

- 系统论文或系统扩展项目
- 不适合作为当前论文立即并入

---

### 8.3 理论解释

#### 内容

例如：

- attention-KL under quantization 的误差传播理论
- GQA / scale statistics / behavior signal 与 allocator 有效性的解释

#### 更适合

- theory / analysis 风格的补强项目
- 当前工作成熟后的深挖方向

---

### 8.4 Benchmark / empirical law paper

#### 内容

例如：

- retrieval-preserving ≠ reasoning-preserving
- behavior-guided allocation 的经验边界
- heuristic 何时足够、何时不够

#### 更适合

- 当前工作稳定后的 benchmark / empirical 论文化

---

## 9. 编号 7 完成后的正式分叉规则

为了避免出现“结果一般也继续扩容”的惯性，`编号 7` 完成后必须按如下规则处理。

### 9.1 情况 A：`BAKV` 明显优于 `Heuristic`

#### 判定特征

- 至少在某个关键 budget 上满足预设硬 gate
- 相对 `Heuristic` 的优势具有可清晰复述的实验支撑

#### 动作

- 允许进入 `编号 8`
- 并从 B1 中优先纳入：
  - 跨模型验证
  - Harder benchmark
  - Pareto 分析
  - `K/V` 非对称 allocator（可选）

#### 论文叙事

- behavior-guided allocation 具有独立方法价值
- `attention-KL lens -> allocator policy` 的升级成立

---

### 9.2 情况 B：`BAKV ≈ Heuristic`

#### 判定特征

- `BAKV` 相对 `Random` 仍然强
- 但相对 `Heuristic` 不形成稳定优势

#### 动作

- 不再默认继续冲更复杂方法线
- 优先进入 `编号 11-13` 收口
- 如仍需增强，只从 B1 中谨慎选择：
  - 跨模型验证
  - Harder benchmark
  - Pareto 分析

#### 论文叙事

- budget-aware allocation 是有效范式
- behavior signal 对随机分配显著有效
- 但相对简单位置 heuristic 的独占价值有限

---

### 9.3 情况 C：`编号 7` 结果混乱或不稳定

#### 判定特征

- 各 budget 下结论不一致且难解释
- 噪声过大，无法支撑明确主结论

#### 动作

- 停在 `编号 6`
- 不进入更高阶段
- 直接执行 `编号 11-13`

#### 论文叙事

- 当前最稳形态为 `v7-allocator-MVP`
- `BAKV > Random` 是最可信结论
- 更强 claim 不强行推进

---

## 10. 当前推荐执行顺序

### 10.1 当前正式主执行线

当前建议严格执行如下顺序：

1. 完成 `编号 7`
2. 根据 `编号 7` verdict 决定是否进入 `编号 8`
3. 任意停点后进入 `编号 11-13`

### 10.2 当前冻结的扩展候选池

在 `编号 7` verdict 明确前，以下方向一律只保留在候选池，不自动并入执行线：

- `K/V` 非对称 allocator
- `LLaMA-3.1-8B` 跨模型验证
- `NoLiMa / BABILong`
- Pareto 分析
- reasoning validation
- head-wise allocation
- token-region allocation
- prompt-adaptive allocation
- learned allocator / predictor
- serving integration
- theory / benchmark paper

---

## 11. 本文档的使用建议

### 11.1 它适合什么场景

本文件适合在以下场景中使用：

- 当主计划执行到 `编号 7` 附近时，用于提醒“当前主线是什么”
- 当讨论新方向时，用于区分“现在做”与“以后做”
- 当需要向 Claude / Codex / Reviewer 解释研究路线时，用于快速说明：
  - 当前执行主线
  - 扩展候选池
  - 分叉条件

### 11.2 它不适合什么场景

本文件不应用作：

- 当前唯一权威计划文件
- 远端实验调度脚本说明
- 逐命令执行清单
- 当前 gate 的唯一判定依据

这些仍应由正式主计划和具体脚本承担。

---

## 12. 最终结论

从当前状态看，最合理的治理方式不是把所有新方向都塞回主计划，而是明确分工：

- **A 栏负责把论文做完**
- **B 栏负责把论文做强**

在 `编号 7` verdict 出来之前：

- A 栏优先
- B 栏冻结

在 `编号 7` verdict 出来之后：

- 再根据结果从 B 栏中选择性纳入增强项

这能同时保证两件事：

1. 当前论文不会因扩题而失去主线
2. 未来最有价值的增强方向不会被遗忘

从研究治理角度看，这比“持续把好想法直接并回总计划”更稳、更可控，也更有利于最终把论文做成。
