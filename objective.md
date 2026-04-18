# 项目名称

面向高效推理的大语言模型 KV Cache 行为驱动量化与预算分配框架

**目标会议**：EMNLP 2026  
**当前文件角色**：高层目标、主线、边界与决策日志的唯一入口  
**不承担的职责**：本文件不是实验矩阵、脚本说明书、阶段任务清单，也不是论文工作台的替代品

---

## 1. 项目定位

本项目当前的目标，不是证明某一种 behavior-aligned 方法在所有设置下普适优于传统基线，而是建立一个以 attention behavior 为统一对象的 KV cache quantization-and-allocation framework。

这篇论文当前的身份应当被理解为：

- 一篇以 **behavior** 为中心组织 calibration、allocation 与 policy selection 的框架型论文；
- 一篇在 **INT8 canonical path** 上完成最干净验证的系统型论文；
- 一篇把 **layer-wise allocation / auto-k / role-aware budget control** 作为扩展层逐步展开的论文；
- 一篇强调 **family-/scale-/task-dependent regimes**，而非单一 universal law 的论文。

---

## 2. Mission

本项目的核心任务，是把论文主线重建为一个更稳、更可审计、与当前证据一致的版本。

当前 mission 包括四点：

1. 把 **behavior** 提升为 KV cache quantization 中统一的分析与设计原则，而不再把它写成单点 superiority claim；
2. 在 **canonical INT8 path** 上验证 behavior-guided diagnosis / calibration / fused decode / generate loop integration 这条最干净的系统闭环；
3. 展示 **behavior-derived profile** 如何自然支撑 layer-wise mixed-precision allocation 与 automatic budget proposal；
4. 将 allocator 线的结果收束为 **regime-based interpretation**，而不是继续追求“单一最优固定 `k`”或“普适最佳 policy”的旧叙事。

这里需要明确一个已经达成的共识：

- 在 `INT8` 上，behavior-guided 路径的价值**不依赖于必须普适击败 `MSE`**；
- 在 `INT4` 上，behavior-guided 低比特优化的价值**也不依赖于必须普适击败 `KIVI-style`**；
- 只要这条路径能够在关键 setting 上达到**可竞争、同级别、可审计**的结果，同时提供更统一的解释与后续 allocation 接口，它就已经证明 `behavior` 不是空谈，而是一个有研究价值和方法价值的统一视角。

---

## 3. 新主线的三层结构

### 3.1 Principle

**Behavior is the right object to preserve, diagnose, and allocate budget for in KV cache quantization.**

换句话说：

- 不只看数值误差；
- 要看 attention behavior 是否被破坏；
- behavior 不只是诊断视角，也应该成为设计和预算控制的统一对象。

### 3.2 Framework

**Behavior-guided KV cache quantization and allocation** 应被视为一个统一框架，而不是若干零散技巧的拼接。

在这个框架下：

- calibration 是 behavior-guided 的参数决策层；
- allocation 是 behavior-derived profile 驱动的预算决策层；
- policy selection 则是面向不同模型家族、任务和预算约束的下游控制层。

### 3.3 Instances and Extensions

在这一统一框架下，当前论文采用如下分层：

- **INT8 canonical path**：canonical validated instance；
- **layer-wise mixed-precision allocation**：框架扩展；
- **auto-k / budget range proposer**：allocation 线的自动化扩展；
- **role-aware K/V allocator**：下一阶段的自然升级方向。

这一分层还隐含一条当前论文必须写清楚的连续性：

- `INT8 canonical path` 证明 behavior-guided diagnosis / calibration 具有独立价值；
- `INT4` 说明 behavior-guided optimization 在更激进 bit-width 下仍然成立，即使它不以普适超越 `KIVI-style` 为前提；
- `allocation / auto-k / role-aware control` 则把同一个 behavior-derived profile 继续下推到预算分配层。

因此，当前论文真正要讲清楚的，不是“behavior 在每一层都更强”，而是：

> **behavior 把 calibration、low-bit rescue、allocation 和 budget control 串成了同一个 framework。**

---

## 4. 当前阶段要回答的核心问题

### RQ1：统一原则

Behavior 是否应被视为 KV cache quantization 的统一分析与设计对象，而不仅仅是一个辅助诊断视角。

### RQ2：Canonical Validation

在 canonical INT8 path 上，behavior-guided calibration、fused decode、generate loop integration 是否构成一个干净、可审计、可复现的验证链。

### RQ3：Allocation Regimes

Behavior-derived profile 是否能够支持 layer-wise mixed-precision allocation，并且其有效配置是否呈现 **family-/scale-/task-dependent regimes**，而不是单一的 universal law。

### RQ4：Automatic Budget Proposal

固定 hand-picked `k` 是否不稳定，从而需要 profile-aware automatic budget proposal 作为 allocation 的自然升级。

---

## 5. 分层方向图

### L0：论文主心脏

- Behavior as unified principle
- INT8 canonical validated instance

### L1：当前主扩展

- Layer-wise allocation
- Auto-k / budget range proposer
- Cross-model regime reading
- Theory / explanation lane

### L2：下一阶段升级

- K/V asymmetric allocator
- Quality-cost Pareto analysis
- Prompt-adaptive allocation

### L3：Future Work

- Head-wise allocation
- Learned allocator
- Reasoning-oriented validation
- Serving/runtime integration

---

## 6. 当前方向的层级解释

### 6.1 已经成立或正在主线上推进的方向

- **INT8 canonical path**：仍是当前最稳的 primary validated instance；
- **Layer-wise allocation**：当前 allocator 主线的实际实现形态；
- **Auto-k / budget range proposer**：已经进入实验链，当前作为 allocation 的自动化扩展推进；
- **Cross-model reading**：已不再是未来设想，而是当前主线证据的一部分；
- **Theory / explanation lane**：不是空未来，而是正在推进的解释层，用于回答 K/V 非对称性、heuristic 强基线、以及 regime 差异的来源。

当前还应明确保留以下方法论判断：

- `INT8` 上与 `MSE` 的 competitive parity，已经足以说明 behavior-guided calibration 不是空谈；
- `INT4` 上与 `KIVI-style` 的 competitive parity，已经足以说明 behavior-guided optimization 在 low-bit setting 中具有解释与指导价值；
- allocator 线的意义，不是把前述结果重新包装成新的 superiority claim，而是把同一个 behavior-derived profile 继续推进到 budget allocation 问题。

### 6.2 下一阶段最自然的升级

- **K/V asymmetric allocator**  
  当前项目已经具备 K/V bit-width routing、MixedKV execution path 与 K>V 敏感性诊断等关键前置资产；下一阶段的自然升级，是把这些资产从 mixed-precision heuristic 提升为显式的 role-aware K/V allocator。

- **Quality-cost Pareto analysis**  
  当前 allocator 线主要比较 task quality；更强的版本需要进一步联合考察 latency、memory、PPL、Needle 等指标，将 allocation 从“分数比较”升级为“预算分配方法”。

- **Prompt-adaptive allocation**  
  在静态、profile-aware allocator 稳定之后，prompt-adaptive allocation 是比 head-wise 更现实的下一阶段升级方向。

### 6.3 明确降为 Future Work 的方向

- Head-wise allocation
- Learned allocator / predictor
- 更激进的 online allocator
- Serving-side runtime scheduling

---

## 7. 当前不做什么

当前阶段明确不再以以下目标作为论文主线：

- 不再追求“Behavior-aligned calibration universally beats MSE”；
- 不再追求“RoleAlign universally beats KIVI-style”；
- 不再把单一固定 `k` 写成跨模型可迁移的 universal policy；
- 不把 Auto-k 写成整篇论文的理论中心；
- 不把 head-wise allocation 与 learned allocator 纳入当前主线；
- 不把 exploratory 结果直接写成 final-ready claim。

---

## 8. 成功标准

本项目当前阶段的成功标准是：

1. 论文主张与现有证据一致，不再依赖已被击穿的旧 superiority 叙事；
2. `INT8 canonical path` 与 exploratory extensions 的边界清晰；
3. `INT8 / INT4` 结果被解释为 behavior 视角的有效性证明，而不是只在“是否击败 baseline”这一维度上评判；
4. allocation 结果被收束为 regime-based interpretation，而非单一最优规律；
5. auto-k 被放在正确位置：具备 empirical 支撑的扩展，而非整篇论文的理论中心；
6. K/V asymmetric allocator、Pareto analysis、prompt-adaptive allocation 的层级被写清，不再混入当前主线；
7. provenance、clean rerun 与可复现性纪律被保留，并在后续计划中持续执行。

---

## 9. 工作边界与维护规则

`objective.md` 只承担高层目标、边界、方向分层和决策日志的职责。

具体执行信息应下沉到以下文件：

- `docs/thesis_upgrade_live_plan.md`：论文主线的实时工作台与章节映射；
- `experiment_sop.md`：实验流程、归档与执行规范；
- 每轮 ExecPlan：当前任务的具体目标、风险、验证与文件改动范围；
- 各 phase / readout 文档：阶段性实验结果和判读。

今后如需新增方向，必须先判断其属于：

- 当前主线；
- 下一阶段升级；
- 还是 Future Work。

未经讨论，不得直接扩张主线。

---

## 10. Decision Log

### 2026-03-25 | 旧版定位：INT8 为主要验证实例，RoleAlign 为低比特扩展

保留 `INT8 canonical path` 作为最稳的 primary validated instance；  
`INT4-RoleAlign` 降级为 low-bit rescue extension。

### 2026-04-19 | 主线重建：从 superiority 叙事转向 behavior-guided framework

明确放弃以下旧主线写法：

- `Behavior-aligned calibration universally beats MSE`
- `RoleAlign universally beats KIVI-style`
- 单一 fixed-`k` 跨模型可泛化

明确保留并强化以下新主线：

- Behavior 作为统一分析与设计原则；
- INT8 canonical path 作为主验证链；
- Allocation 作为框架扩展层；
- Auto-k 作为 allocation 线的自动化方法扩展；
- 当前 allocator 结果应被解释为 family-/scale-/task-dependent regimes。

### 2026-04-19 | 共识补强：competitive parity 也能证明 behavior 视角有用

明确确认以下口径：

- `INT8` 上即使没有普适击败 `MSE`，只要 behavior-guided calibration 达到同级别、可审计结果，就足以证明 behavior 不是空谈；
- `INT4` 上即使没有普适击败 `KIVI-style`，只要 behavior-guided optimization 达到同级别、可解释结果，就足以证明 behavior 在 low-bit rescue 中具有方法价值；
- 因此，当前论文的主张重点应是 **behavior 作为统一框架原则的连续性**，而不是每个子 setting 上的普适 superiority。

### 2026-04-19 | 方向分层确认

将项目方向正式分层为：

- L0：论文主心脏（Behavior + INT8 canonical path）
- L1：当前主扩展（Layer-wise allocation / Auto-k / cross-model reading / theory lane）
- L2：下一阶段升级（K/V asymmetric allocator / Pareto / prompt-adaptive）
- L3：Future Work（head-wise / learned allocator / reasoning / serving integration）
