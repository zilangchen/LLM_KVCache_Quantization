# L2 Spec: Prompt-Adaptive Allocation MVP

> 角色：MVP spec  
> 对应高层计划：`docs/l2_prompt_adaptive_allocation_plan.md`

---

## 1. 目标

在不改底层 kernel / cache schema 的前提下，给 allocator 增加一个最小的“按输入选择 policy”能力。

MVP 的问题不是：

- 如何做一个完整 online controller？

而是：

> **在现有 policy 池已经存在的情况下，按 prompt / task / profile 特征选择 policy，是否优于“一把梭全局单 policy”？**

---

## 2. MVP 范围

### 2.1 只做什么

1. 离线选择器
2. 从现有 policy 池中选一个 policy
3. 不改执行路径

### 2.2 不做什么

1. 不做 learned allocator
2. 不做 token-level control
3. 不做 head-wise adaptive
4. 不做在线逐 token 反馈控制

---

## 3. 推荐 MVP 版本

### 3.1 第一选择：task/profile bucket selector

MVP 推荐版本：

- 根据任务类别或 profile bucket
- 从现有 policy 池里选一个 policy

### 3.2 可接受的输入特征

1. task id
2. prompt length bucket
3. profile summary bucket

### 3.3 暂不建议作为 MVP 核心

1. 复杂语义标签
2. learned latent routing
3. 在线重估 sensitivity

---

## 4. 候选 policy 池

MVP 默认只在现有强 policy 中选择，不扩大搜索空间：

1. one global best fixed-k
2. one strongest heuristic
3. one strongest auto-k
4. 后续可加入 one role-aware candidate

---

## 5. 评价协议

MVP 需要至少比较三类对象：

1. `global fixed-k`
2. `global auto-k`
3. `prompt-adaptive selector`

### 默认任务集合

先只看：

- core tasks
- extend-task 中高信息量任务

---

## 6. 成功判据

MVP 值得继续的最低标准是：

1. 在至少一个模型上，selector 明显优于全局单 policy
2. 或者在不同 task bucket 上，selector 能稳定避免“全局单 policy 的明显失配”

---

## 7. 失败也有价值的情形

如果 MVP 失败，也要明确回答：

1. 当前静态 allocator 是否已经足够强
2. 问题是否不在“按 prompt 选 policy”，而在更底层的 role-aware / Pareto 方向

---

## 8. 输出物

应至少产出：

1. 一个明确的 selector 规则
2. 一组对照表
3. 一段说明“为什么它值得或不值得继续扩成更重版本”的结论
