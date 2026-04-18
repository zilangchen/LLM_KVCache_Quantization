# Behavior 主线重建备忘录

> 文档定位：**内部主线重建 memo**
>
> 本文档不是论文正文，也不是 `docs/thesis_upgrade_live_plan.md` 的替代品。  
> 它的作用是把本线程已经达成的共识固定下来，避免后续再次滑回旧主线。

---

## 1. 这份文档要回答什么

本 memo 只回答两件事：

1. **原论文最开始在讲什么，我们是如何一步一步把它击穿的**
2. **在旧主线失效之后，当前最终确定的新主线应该是什么**

本文档不做这些事：

- 不直接改 `thesis/chapters/*.tex`
- 不直接修改工作台
- 不替代实验计划
- 不把 `AutoK` 提前写成整篇论文的理论中心

---

## 2. 原论文最开始在讲什么

先用最直白的话说，原论文想讲的是这个故事：

> 长上下文推理里，KV cache 是显存和带宽瓶颈，所以需要量化。  
> 但量化不能只看普通数值误差，因为真正影响生成质量的是 attention behavior 有没有被破坏。  
> 因此，论文提出以 attention behavior 为中心的量化视角，并尝试用 attention-KL 去做诊断和校准。  
> 这条思路先在 `INT8 canonical path` 上验证，再往 `INT4 RoleAlign` 推进，最后补上 kernel / generate loop / 系统落地。

把这个故事拆开，它包含五个层次：

### 2.1 现实问题层

- KV cache 在长上下文和大 batch 下是显存与带宽瓶颈
- 量化是必须面对的工程问题

### 2.2 机制判断层

- 现有方法常看 `MSE`、重建误差等数值指标
- 原论文认为，这还不够，因为 attention 行为才是更接近真实生成质量的对象

### 2.3 主验证链层

- 论文用 `INT8 canonical path` 当主要验证实例
- 它的真正角色不是“最前沿 bit-width”，而是“最干净的验证链”

### 2.4 低比特扩展层

- 在 `INT4` 上，论文进一步推进 `RoleAlign`
- 核心想法是对 `K` 和 `V` 采用不同对待方式

### 2.5 系统闭环层

- 这不只是分析型论文
- 它还接进了 calibration、kernel、generate loop，试图形成完整系统闭环

---

## 3. 原论文里最重要的两个对象

为了避免后面混淆，先把原论文的两个对象分开：

### 3.1 `INT8 canonical path`

它的含义不是“INT8 最前沿”，而是：

> 用一个更可控、更容易归因的 setting，来验证 behavior-aligned 这套框架是否成立。

项目里对此有明确定位：

- `INT8 行为对齐量化 = canonical validated instance`
- `INT4-RoleAlign = low-bit rescue extension`

也就是说，原论文最稳定的主干其实一直是：

> `behavior-aligned diagnosis -> calibration -> INT8 quantization -> fused decode -> end-to-end validation`

### 3.2 `INT4 RoleAlign`

它原本承担的是更“前沿”的那条线：

- 更低 bit
- 更激进压缩
- 更像论文亮点

但它的问题也最集中：

- 和 `KIVI-style` 在量化格式骨架上高度重合
- 数值结果并没有形成压倒性优势

---

## 4. 我们是怎么把原论文击穿的

这里的“击穿”，不是说整篇论文什么都没了。  
更准确地说，是：

> **把它原来最想卖的那根主梁打断了。**

这条击穿链是在本线程里一点点完成的，核心有四步。

### 4.1 第一步：击穿 `INT8 上 KL 比 MSE 更强`

原论文旧主线有一个很强的隐含判断：

> `Behavior-aligned / KL calibration` 比 `MSE / percentile` 更好。

但 thesis 自己给出的结果并不是这样。

当前正式正文里的结论是：

- `INT8` 下，`KL` 和 `MSE` 在当前协议里**收敛到同一个最优点**
- 它们选出同样的 `(clip_percentile, group_size)`
- 生成出的 scale 逐位一致
- 下游指标也一致

因此，`INT8` 上真实成立的结论不是：

> `KL > MSE`

而是：

> `KL ≈ MSE`

这意味着：

- 原论文**没有证明** `Behavior-aligned calibration` 在 `INT8` 上优于 `MSE`
- 最多只能证明：
  - `KL` 是可用的
  - 它和 `MSE` 在当前 regime 下收敛

这一步已经击穿了旧主线里最重要的一条 superiority claim。

### 4.2 第二步：击穿 `INT8 canonical path` 的 novelty center 幻觉

`INT8 canonical path` 的价值一直存在，但它的价值不是“新颖性中心”，而是：

- 最干净的验证链
- 最容易完成机制归因的路径

这意味着：

- 它适合做“框架验证”
- 不适合做“最前沿论文卖点”

所以原论文在这里出现了一个根本矛盾：

- **最稳的东西不够新**
- **最想卖的新东西又不够硬**

### 4.3 第三步：击穿 `INT4 RoleAlign` 的独立方法性

本线程里我们把 `RoleAlign` 和 `KIVI-style` 的关系也说清楚了。

更准确的判断是：

- 它们共享同一个量化格式骨架：
  - `per-channel K`
  - `per-token V`
- `RoleAlign` 不是完全等于 KIVI
- 但它也不是一个彻底独立的新格式方法

它更像是：

> 在同一格式空间里，改成用离线 behavior-aligned calibration 来求参数。

这使得它的贡献从：

> “提出一个新低比特方法”

收缩成：

> “解释这个格式为什么合理，并给出一个离线可审计的参数化接口”

### 4.4 第四步：击穿 `INT4 上比 KIVI-style 更强`

原论文没法证明：

> `INT4 RoleAlign > KIVI-style`

反而 thesis 自己承认：

- `RoleAlign` 的贡献不在于打败 `KIVI-style` 的数字
- 其价值更偏向解释、诊断和离线 calibration 接口

因此，对原论文旧主线的最终判定是：

> **它不能再被写成“behavior-aligned 是一个在 INT8/INT4 上普适优于 MSE / KIVI 的方法”。**

---

## 5. 被击穿之后，原论文还有什么能保

旧主线被击穿，不等于整篇论文全塌。

还能保住的内容主要有四块：

### 5.1 Behavior 作为诊断视角

也就是：

- 用 attention behavior 而不是只用普通数值误差来理解量化损伤
- 强调 `K` 比 `V` 更关键
- 把“为什么某些格式更合理”讲清楚

这是原论文仍然最有研究味道的部分。

### 5.2 Framework 视角

原论文不是单点 trick，而是有完整链路：

- 诊断
- calibration
- quantization
- kernel
- generate loop

这条框架链仍然成立。

### 5.3 `INT8 canonical path`

它不再适合作为“最亮眼的新颖性中心”，但仍然适合作为：

- 主验证链
- canonical validated instance

### 5.4 系统闭环与工程可审计性

尤其是 calibration artifact、运行时路由和 kernel/generate loop 的接入，这些都仍然是可保资产。

---

## 6. 为什么必须升级主线

旧主线的问题，不是“写得不好”，而是：

> **核心命题和现有证据不匹配。**

如果不升级，会出现三类自相矛盾：

### 6.1 方法主张和实证结果冲突

- 旧主张：`Behavior-aligned` 更优
- 真实结果：
  - `INT8` 上没赢 `MSE`
  - `INT4` 上没赢 `KIVI-style`

### 6.2 理论中心和实验中心错位

- 旧理论中心想卖“behavior-aligned superiority”
- 但当前更稳的实验现实是：
  - family-/scale-/task-dependent regimes
  - heuristic 是强 baseline
  - fixed-k 不稳

### 6.3 `AutoK` 不适合被硬扶成主线

当前 `AutoK` 虽然有价值，但它更像：

- 方法扩展
- allocator 支线升级
- 自动化 budget proposer

它不是整篇论文的理论中心。

---

## 7. 我们最终确定的新思路

本线程最后收束出来的新主线，不是：

- `KL universally better`
- `Behavior-aligned universally better`
- `AutoK is the whole paper`

而是：

> **Behavior 应该被提升为整篇论文的统一分析与设计原则。**

更完整一点的表达是：

> 在 KV cache 量化里，真正应该被保护、分析和分配预算的对象，是 attention behavior；因此 behavior 应该作为统一视角，用来组织 calibration、allocation 和 policy selection。

这就是当前最终确定的主思路。

---

## 8. 新主线的三层结构

这是本线程达成的最重要结构性结论。

### 8.1 第一层：理论 / 原则层

> **Behavior is the right object to preserve and diagnose in KV cache quantization.**

翻成人话：

- 不只看数值误差
- 要看 attention behavior 有没有被破坏
- 这是整篇文章的核心视角

### 8.2 第二层：框架层

> **Behavior-guided KV cache quantization and allocation**

也就是：

- calibration 可以由 behavior 来驱动
- allocation 也可以由 behavior 来指导
- 它们属于一个统一框架，而不是两个零散小技巧

### 8.3 第三层：方法 / 实例层

在这个统一框架下面，再挂具体实例：

- `INT8 canonical calibration`
- `behavior-guided mixed-precision allocation`
- `AutoKAllocator / auto-k proposer`

这三者的关系是：

- `INT8 canonical`：验证链
- `Allocation`：框架扩展
- `AutoK`：自动化方法贡献

---

## 9. 为什么不再把 `AutoK` 当主线

这是本线程最终已经明确下来的判断：

> **AutoK 是 contribution，不是 theory。**

更准确地说，`AutoK` 的位置应该是：

> **一个 profile-aware automatic budget proposer，在 behavior-guided allocation 框架下作为方法扩展出现。**

它的性质是：

- 是方法
- 是扩展
- 是 allocator 线的升级

但它不是：

- 整篇论文的理论中心
- 整篇论文唯一主张
- 当前最稳的 claim

---

## 10. `Behavior-Aligned Calibration` 和 `Behavior-Guided Allocation` 的区别

这两个概念现在必须彻底分清。

### 10.1 `Behavior-Aligned Calibration`

它在做的是：

> 找量化参数

典型参数包括：

- `group_size`
- `clip_percentile`
- `k_scale / v_scale`
- `inv_tau`

这里的“校准产物”，就是 calibration JSON，也就是一份告诉运行时“该怎么量化”的参数说明书。

### 10.2 `Behavior-Guided Allocation`

它做的不是重新找 scale，而是：

> 根据 behavior-derived profile 去分配预算

也就是决定：

- 哪些层保护
- 每层给多少 bit
- 哪些层留 `INT8`
- 哪些层降到 `INT4`

### 10.3 当前 allocator 里的 behavior 到底怎么算

当前实现并没有在 allocator 阶段重新直接优化 attention-KL。  
它的实际逻辑是：

1. 先读取 behavior-aligned calibration 产出的 JSON
2. 从中取出 `k_scale`
3. 把 `k_scale` 聚合成每层 sensitivity profile
4. 再基于这个 profile 做 `top_k / heuristic / random / auto_k_coverage`

因此，最准确的话不是：

> allocator 直接在做 behavior-aligned optimization

而是：

> allocator 是 **behavior-derived / behavior-guided**

这个区分很重要。

---

## 11. 当前推荐的总命名

本线程最终比较认同的总方向是：

### 推荐总主线名

**Behavior-Guided KV Cache Quantization and Allocation**

它的优点是：

- 能把 calibration 和 allocation 都包进去
- 不会像 `Behavior-Aligned` 那样带着过强的 superiority 包袱
- 也不会像 “AutoK paper” 那样把支线写成全篇中心

### 可接受的备选说法

- **A Behavior-Centric Framework for KV Cache Quantization**
- **Behavior-Informed KV Cache Precision Control**
- **From Behavior-Aligned Calibration to Behavior-Guided Allocation**  
  这个更适合作为副标题或章节名

---

## 12. 当前 allocator / auto-k 实验在测什么

这一点也已经在本线程里澄清了：

> 当前 `Phase 2` allocator / auto-k 升级实验，主要不是在测 `PPL`。

它们主要在测：

### 12.1 下游任务效果

用的是 LongBench 风格任务指标，例如：

- QA：`F1`
- Summarization：`Rouge-L`
- Classification：`Accuracy`
- Code：`Edit Similarity`

### 12.2 效率 / 资源指标

同时记录：

- `latency_ttft_ms`
- `latency_tpot_ms`
- `gpu_peak_mem_mb`

因此，这些实验结果代表的是：

> **不同 allocation / auto-k policy 在真实长上下文任务上的保真度，以及它们在延迟和显存上的代价。**

它们不是单纯的 calibration proxy，也不是单纯的 PPL 对比。

---

## 13. 当前结果说明了什么

到目前为止，allocator 线最稳的解释不是：

> 存在单一的普适最优 `k`

而是：

> **不同 family / scale / task 落在不同的 operating regimes 里；heuristic 是强 baseline；fixed-k 不稳；profile-aware allocation 值得继续推进。**

因此，当前 phase2 结果最主要支撑的是：

### 13.1 fixed-k 不是好主方法

- 手工 sweep 很笨重
- 可迁移性差
- 新模型一来，旧的 `k` 经常失效

### 13.2 allocation 更像一个 profile-aware policy problem

- 不同模型预算偏好不同
- 不同任务区分度不同
- heuristic 仍然很强

### 13.3 auto-k 有价值，但还只是支线方法贡献

- 它在往“自动 budget proposer”方向走
- 但它当前更适合作为 contribution
- 不适合作为整篇论文的理论主线

---

## 14. 当前最终确定的写法边界

这一节最适合后续写论文时直接拿来做口径检查。

### 14.1 现在可以写的说法

- behavior 是 KV cache 量化中更合适的分析与设计对象
- behavior 可以统一组织 calibration 与 allocation
- `INT8 canonical path` 是一个 canonical validated instance
- behavior-derived profile 可以指导 layer-wise mixed-precision allocation
- allocator 的有效配置呈现 family-/scale-/task-dependent regimes
- `AutoK` 是行为驱动框架下的自动化 budget proposer 扩展

### 14.2 现在不能再写的说法

- `Behavior-aligned calibration universally beats MSE`
- `RoleAlign universally beats KIVI-style`
- `AutoK` 已经是整篇论文的理论中心
- 存在单一固定 `k` 可以跨模型泛化
- behavior-guided allocator 已经完成最终 clean 验证

---

## 15. 一句话结论

如果把整篇论文的重建结果压成一句话，就是：

> **旧主线把 behavior-aligned 讲成“普适更优方法”，但现有证据只足以支持它作为统一的分析与设计原则；因此新论文主线应从“behavior superiority”切换为“behavior-guided quantization and allocation framework”，并把 AutoK 降到该框架下的方法扩展位置。**

---

## 16. 可直接复述版

### 16.1 三句话讲原论文

1. 原论文说 KV cache 量化不能只看数值误差，要看 attention behavior 有没有被破坏。
2. 它先用 `INT8 canonical path` 试图验证 behavior-aligned 这条路，再把这套思路往 `INT4 RoleAlign` 推。
3. 但最后它既没证明 `INT8` 上 `KL > MSE`，也没证明 `INT4` 上 `RoleAlign > KIVI-style`。

### 16.2 三句话讲“我们怎么把它击穿的”

1. `INT8` 上，`KL` 和 `MSE` 实际上收敛到同一个点，所以没有 superiority。
2. `INT4 RoleAlign` 和 `KIVI-style` 在格式骨架上高度重合，结果又没有明显优势。
3. 所以旧主线里“behavior-aligned 是普适更优方法”这根主梁被打断了。

### 16.3 三句话讲新主线

1. 真正该保留的不是“KL 更优”这个旧主张，而是“behavior 是更合理的分析和设计对象”。
2. 因此，整篇论文应改成由 `Behavior` 统一组织 calibration、allocation 和 policy selection。
3. `AutoK` 是这个框架下的自动化 allocator 扩展，是贡献，但不是理论主线。

---

## 17. 参考材料

### 项目内材料

- `objective.md`
- `thesis/chapters/ch3_method.tex`
- `thesis/chapters/ch4_experiments.tex`
- `thesis/chapters/ch5_conclusion.tex`
- `scripts/calibrate_behavior.py`
- `scripts/adaptive/behavior_aligned_allocator.py`
- `scripts/eval_longbench.py`
- `docs/thesis_upgrade_live_plan.md`
- `docs/phase2_final_readout.md`
- `docs/auto_k_selector_experiment_plan.md`

### 外部文献

- [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://arxiv.org/abs/2402.02750)
- [KVTuner: Sensitivity-Aware Layer-Wise Mixed-Precision KV Cache Quantization for Efficient and Nearly Lossless LLM Inference](https://arxiv.org/abs/2502.04420)
- [KVmix: Gradient-Based Layer Importance-Aware Mixed-Precision Quantization for KV Cache](https://arxiv.org/abs/2506.08018)
- [AsymKV: Enabling 1-Bit Quantization of KV Cache with Layer-Wise Asymmetric Quantization Configurations](https://aclanthology.org/2025.coling-main.158.pdf)
