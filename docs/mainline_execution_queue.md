# 主线执行清单

> 用途：这份文档区别于 [objective.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/objective.md)。  
> `objective.md` 负责高层目标、边界和方向分层；本文档只回答：
>
> 1. **接下来按什么顺序做**
> 2. **哪些实验已经跑过**
> 3. **哪些缺口必须补**
> 4. **哪些实验线需要重设计**
> 5. **当前脚本跑完后立刻接什么**
> 6. **后续扩展方向按什么顺序推进**

> 当前口径：
> - 这是**执行队列**，不是结果 readout
> - 这是**默认顺序建议**，不是每一步的最终 ExecPlan
> - 任何真正涉及代码或实验启动的动作，仍需在对应任务里单独起 ExecPlan

---

## 0. 当前状态快照

**更新时间**：2026-04-19 06:17 CST

### 0.1 远端实验链

- `Wave 1 (8B extended)`：已完成 **`30/30`**（21 原 + 9 auto-k backfill）
- `Wave 3 (7B random hardening)`：已完成
- `Wave 4 (14B sweep)`：已完成 **`45/45`**（36 原 + 9 auto-k backfill）
- `Wave 5 (Mistral full)`：已完成 `45/45`
- `Wave 7a (7B extend tasks)`：已完成 `36/36`
- `Wave 7b (8B extend tasks)`：已完成 `40/40`
- `Wave 6 (Qwen-3B sweep)`：**已完成 `45/45` @ 05:27 — 全 3 task GATE PASS**

### 0.2 当前远端执行形态

- **所有 Phase 2.6 exploratory wave 全部完成**
- `tmux` 为空，3 GPU 全 idle
- `3B 模型` 已缓存 + 离线 load pre-check PASS

### 0.3 跨 4 model auto-k readout（核心新证据）

| Model | Best overall | Best auto-k | Gap (auto-k - best) |
|---|---|---|---|
| **3B** (L=36, H_kv=2) | `bakv_k1` (6.90) | `cov80` (6.75) | **-0.15** |
| **8B** (L=32, H_kv=8) | `bakv_k11` (9.52) | `cov80` (9.35) | **-0.17** |
| **14B** (L=48, H_kv=8) | `uniform_int4` (7.23) | `cov90` (7.15) | **-0.08** |
| **Mistral-7B** (L=32, H_kv=8) | `cov80` (14.76) | `cov80` (14.76) | **+0.00** |

**核心结论（修正版）**：auto-k 的"胜"仍是 **Mistral-specific**，不是跨 family 普遍规律：
- 4/4 model 上 auto-k 都在 top tier（gap 绝对值 ≤0.17）
- 但只有 Mistral-7B 上 auto-k **做到并列最优**
- 3B/8B/14B 上 auto-k 均**略输 fixed best** (gap -0.08 到 -0.17)

### 0.4 3B 独特 finding（新纳入）

- `bakv_k1` 选 `[0]` **first layer**（跨模型独一无二，其他模型都选 mid-late）
- `heuristic_k1` 选 `[L//2]=[18]` → metric **3.48**（灾难性失败）
- `bakv_k1` vs `heuristic_k1`: **6.90 vs 3.48 = +98%** — behavior-guided 在 3B 上 critically 重要
- 3B `cov90 ratio` = 83%（vs 8B/Mistral 88%），heavy-tail 更显著

### 0.5 formal audit 吸收后的当前判断

- [docs/phase2_data_mainline_audit_20260419.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_data_mainline_audit_20260419.md) 已完成
- 当前最稳的 post-audit 口径：
  - `behavior-guided framework` 明显强于 `behavior superiority`
  - `auto-k` = cross-model supported strong extension / profile-aware budget proposer
  - explicit wins still mainly **Mistral-specific**
  - `3B` 最值得写的新现象不是 auto-k，而是 **early-layer bottleneck regime**
- 当前 evidence tier：
  - `candidate-main`：可用于主线重构与论文叙事收口
  - 不是 `final-ready`：clean-provenance rerun 仍是升级前提

---

## 1. 我们已经跑了什么

### 1.1 可直接服务新主线的主干资产

- `INT8 canonical path`
  - 已经足以支撑：behavior 不是空谈
  - 即使它没有普适击败 `MSE`，它仍证明了 behavior-guided calibration 作为统一视角的价值

- `INT4 / RoleAlign / low-bit rescue`
  - 已经足以支撑：behavior-guided optimization 在 low-bit setting 中也有方法价值
  - 即使它没有普适击败 `KIVI-style`，它仍证明了 behavior 视角能指导低比特优化

- `allocator / auto-k` 主线
  - 已形成从 calibration profile 到 allocation / budget proposal 的连贯链条

### 1.2 Phase 2.6 已完成或已进入的波次

- 已完成：
  - `Wave 2 sanity`
  - `Wave 1 (8B extended)`
  - `Wave 3 (7B random hardening)`
  - `Wave 4 (14B sweep)`
  - `Wave 5 (Mistral full)`
  - `Wave 7a (7B extend tasks)`
  - `Wave 7b (8B extend tasks)`
  - `Wave 6 (Qwen-3B sweep)`

### 1.3 当前已经成立的最稳结论

- `behavior` 的价值不依赖于普适 superiority，而依赖于它是否能提供统一、可解释、可继续下推到 allocation 的视角
- allocator 线目前更稳的结论是：
  - `family-/scale-/task-dependent regimes`
  - `heuristic is a strong baseline`
  - `fixed-k` 不稳
  - `auto-k` 已拿到第一批完整正面证据，但还不是 universal winner

---

## 2. 当前必须补的实验与判读缺口

### 2.1 第一优先级：吸收 formal audit + 固化 `candidate-main` 口径

当前最明确、最硬的缺口已经从“补 backfill / 跟踪 Wave 6”进一步变成：

- 把 [docs/phase2_data_mainline_audit_20260419.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_data_mainline_audit_20260419.md) 的结论正式并入工作台 / readout / queue
- 固化 cross-4-model auto-k 的 `candidate-main` 口径
- 明确 clean-provenance rerun 的 claim-critical compare set

### 2.2 为什么它是第一优先级

因为这不是“再加一点新证据”，而是：

- 当前 `L1` 数据层已经基本跑完，真正缺的是**统一判读**
- formal audit 已经把 raw data、3B anomaly、heuristic 与 extend-task 重新排了优先级
- 如果不吸收 audit，工作台与执行队列会继续停留在旧口径

### 2.3 补完后必须立刻回答的问题

1. 哪些结论现在可以正式升级为 `candidate-main`
2. 哪些结果目录可以直接引用，哪些必须带 caveat
3. clean-provenance rerun 最小 compare set 应该如何固定

---

## 3. 哪些实验线需要重设计

### 3.1 extend-task 线需要重设计，而不是继续按旧口径堆量

当前最清楚的问题是：

- `trec / vcsum` 长期 low-information
- 它们不能继续被当成 allocator 主证据

### 3.2 新的默认处理口径

- `dureader`：保留为 extend-task 主证据
- `lcc`：继续观察，作为新增 task 维度
- `trec / vcsum`：降级为 scope / boundary / low-information disclosure

### 3.3 这意味着什么

后面如果还要补 extend-task 线，正确动作不是继续机械加量，而是：

- 先重设计任务组合
- 再决定要不要继续扩大 extend-task 在正文里的权重

---

## 4. 当前脚本跑完后立刻接什么

这是本文件最重要的顺序建议。

### 4.1 默认顺序

1. **把 formal audit 的结论并入工作台与 readout**
2. **固化 cross-4-model auto-k 的 `candidate-main` 口径**
3. **固化 clean-provenance / L2 launch prerequisites**
4. **整理 extend-task evidence triage 的最终写法**
5. **单独起 `L2` launch plan，并再进入 `L2` 三条方向**

### 4.2 当前为什么先做统一 readout

因为：

- `Wave 1 / Wave 4` unified readout 已完成
- `Wave 6` 也已经完整完成 `45/45`
- formal audit 已经把 raw-data 层的可信度、主线强弱项与理论支持框架重新梳理清楚
- 当前真正阻塞的不是更多 `L1` 数据，而是把这些结论收紧成可防守的 `candidate-main` 口径，并把重心切到 `L2`

默认优先级仍然是：

> **先把当前主线缺口解释清楚，再扩新证据。**

### 4.3 当前就应该准备的东西

当前本地最该提前准备的是：

- formal audit 结论的正式吸收
- cross-4-model auto-k 统一表述
- clean-provenance rerun compare set
- `L2` 三条方向的 launch prerequisites

### 4.4 当前 GPU 空闲时的默认策略

- 当前 Phase 2.6 exploratory wave 已全部结束，GPU 处于空窗
- 默认动作应变为：
  - 先完成 `Wave 6` readout 与主线收口
  - 然后单独起 `L2` launch plan
  - 再按 `K/V asymmetric -> Pareto -> Prompt-adaptive` 的顺序占用远端 GPU

---

## 5. 后续方向的推进顺序

### 5.1 第一顺位：K/V asymmetric allocator

这是当前最自然的下一步，因为项目已经有：

- `K > V` 诊断资产
- `(k_bits, v_bits)` 路由基础设施
- `MixedKV` 执行路径

因此它不是全新方向，而是：

> **当前 framework 最顺的 role-aware 升级。**

### 5.2 第二顺位：Quality-cost Pareto analysis

这条决定 allocator 能不能从“分数现象”升级成“预算分配方法”。

它的重要性很高，但顺序仍应排在 `K/V asymmetric allocator` 后面，因为：

- 先把方法形态再推进一步
- 再系统定义 quality-cost trade-off

### 5.3 第三顺位：Prompt-adaptive allocation

这条比 `head-wise` 更现实，但仍应晚于前两条，因为：

- 它更依赖静态 allocator 的规律已经被读清
- 否则容易只是把当前不稳定规律重新包装成“动态选择器”

### 5.4 明确放后面

当前明确不作为近端主线：

- `Head-wise allocation`
- `Learned allocator`
- 更激进的 online adaptive serving allocator

---

## 6. 默认执行队列

### Queue A：当前主线收口

1. 吸收 formal audit 到工作台与主线 readout
2. 更新 cross-4-model auto-k 的 `candidate-main` 口径
3. 固化 clean-provenance rerun compare set 与 prerequisites
4. 使用 [docs/clean_provenance_launch_plan.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/clean_provenance_launch_plan.md) 单独启动 `L1 claim-critical` clean rerun

### Queue B：重新整理 extend-task 线

5. 固化 `dureader > lcc > trec/vcsum` 的证据分层
6. 将 extend-task 线从“4-task 平均”改成“高信息量 task supporting evidence”

### Queue C：L2 启动准备

7. 把 `L2` 三条方向从 planning 切到 `scripts ready / waiting launch`
8. 单独起 `L2` launch plan，明确远端启动顺序与 GPU 占用

### Queue D：L2 升级方向

9. `K/V asymmetric allocator`
10. `Quality-cost Pareto analysis`
11. `Prompt-adaptive allocation`

---

## 7. 每一项任务的交付物

### 7.1 formal audit 吸收

交付物应包括：

- 一份正式确认 `candidate-main` 与 `final-ready` 边界的总结
- 一份工作台 / 主线 / execution queue 同步更新
- 一个清晰的 clean compare set

### 7.2 cross-4-model auto-k 收口

交付物应包括：

- 一份统一表述 `3B / 8B / 14B / Mistral` auto-k 位置的总结
- 对 `Mistral-specific win` 与 `cross-scale top-tier` 的明确区分
- 对 “3B 主角是 early-layer bottleneck，不是 auto-k 准最优” 的明确区分
- 是否改变当前 family-/scale-dependent 解释的结论

### 7.3 extend-task redesign

交付物应包括：

- 哪些 task 保留
- 哪些 task 降级
- 后续 extend-task 线如何重设

### 7.4 `K/V asymmetric allocator`

交付物应包括：

- 明确的 role-aware policy schema
- 最小实验矩阵
- 与当前 MixedKV / layer-wise allocator / auto-k 的比较口径

### 7.5 `Pareto analysis`

交付物应包括：

- 统一 protocol
- quality / cost 指标定义
- 至少一组可解释的 Pareto 图

### 7.6 `Prompt-adaptive allocation`

交付物应包括：

- 一个最小 prompt/task-aware selector 定义
- 与全局静态 single-policy 的对照协议

---

## 8. 当前不该做的事

- 不要在 `Wave 7b` partial 时就升级 extend-task 的论文地位
- 不要把 3B 的主现象误写成 “auto-k close second”
- 不要把 formal audit 当成 `final-ready`
- 不要三条 `L2` 同时开工
- 不要把 `Prompt-adaptive` 提前到 `K/V asymmetric` 前面
- 不要把 parity 重新写回 superiority 叙事

---

## 9. 一句话版本

> 当前默认顺序是：  
> **先把 formal audit 的结论正式吸收到工作台与主线 readout，固化 cross-4-model auto-k 的 `candidate-main` 口径与 clean compare set；随后单独起 `L2` launch plan，再按 `K/V asymmetric allocator -> Pareto analysis -> Prompt-adaptive allocation` 的顺序推进。**
