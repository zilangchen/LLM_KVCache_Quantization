# Clean-Provenance Launch Plan

> 用途：把当前 `candidate-main` 结果升级到 `final-ready support` 所需的 clean rerun 启动方案固定下来。
>
> 这份文档不是 rerun framework 的替代品；它回答的是：
>
> 1. **现在具体该怎么启动**
> 2. **重跑哪些 compare set**
> 3. **如何判定 exploratory 是否被 clean 结果支持**

---

## 0. 当前定位

当前状态：

- `Phase 2.6` exploratory 已完成
- `formal audit` 已完成
- 当前主线已经收紧为 `candidate-main`
- 当前代码 pin 已整理并 push 到：
  - branch: `codex/phase2-a-rerun`
  - commit: `ddada19`

当前 clean-provenance 的任务，不是重跑一切，而是：

> **在 clean checkout 下覆盖真正会进入论文主张的最小 compare set。**

---

## 1. 默认 pin 与 provenance 起点

### 1.1 默认 pin

- branch: `codex/phase2-a-rerun`
- commit: `ddada19`

### 1.2 建议 tag

- `phase2-clean-rerun-v1`

### 1.3 启动前必须确认

1. 本地 `git status --short` 为空
2. `origin/codex/phase2-a-rerun` 与本地 `HEAD` 一致
3. 远端使用 **clean clone / clean worktree**
4. 关键 runtime 文件 md5 已记录

---

## 2. rerun 范围：claim-critical compare set

### 2.1 Priority A：必须覆盖

#### A1. INT8 canonical path

目标：

- 覆盖论文主心脏的 canonical validated instance
- 保证最终正文引用的 canonical path 不是只来自 exploratory

#### A2. Cross-model allocator / auto-k 主线

必须覆盖 4 个模型：

1. `Qwen/Qwen2.5-3B-Instruct`
2. `meta-llama/Llama-3.1-8B-Instruct`
3. `Qwen/Qwen2.5-14B-Instruct`
4. `mistralai/Mistral-7B-Instruct-v0.3`

每个模型只重跑最小必要策略集：

- best overall
- best auto-k
- strongest heuristic
- strongest behavior-guided fixed-k
- strongest uniform（若该模型的主张依赖 uniform 比较）

#### A3. 主张依赖的关键 reading

本轮必须能回答：

1. auto-k 是否仍然是 cross-model top-tier
2. Mistral-specific win 是否成立
3. 3B 的 early-layer bottleneck regime 是否仍成立
4. heuristic 强 baseline 的结论是否仍成立

### 2.2 Priority B：建议覆盖

#### B1. Extend-task 高信息量支持项

- `dureader`
- `lcc`

作用：

- 支撑 extend-task supporting evidence
- 不再依赖 `trec / vcsum`

### 2.3 不纳入本轮

以下内容默认不纳入本轮 clean-provenance：

- `trec`
- `vcsum`
- 低信息量 supporting-only exploratory 结果
- `L2` 三条 exploratory 结果

---

## 3. 远端 clean checkout 启动流程

### 3.1 clean workspace

建议使用单独 clean workspace，而不是复用当前 exploratory 目录。

默认流程：

1. `git fetch origin`
2. `git checkout ddada19`
3. `git status --short`
4. 确认 worktree 干净

### 3.2 必须通过的 preflight

1. 关键脚本 `--help` 正常
2. 关键脚本 `py_compile` 正常
3. 关键 runtime 文件 md5 记录完成
4. 结果根目录为空或仅含本轮初始化结构

### 3.3 provenance 记录

本轮必须新建：

- `clean rerun manifest`
- `pin + env ledger`
- `calibration provenance record`

---

## 4. calibration clean 化策略

### 4.1 默认重产对象

优先 clean 重产：

1. `14B`
2. `Mistral-7B`
3. `3B`

### 4.2 条件保留对象

以下模型可按需要保留现有可信 calibration，前提是其 provenance 足够干净：

4. `1.5B`
5. `7B`
6. `8B`

### 4.3 calibration 产物要求

每个 calibration 输出都必须绑定：

- model id
- config snapshot
- commit pin
- md5
- timestamp
- 输出路径

---

## 5. rerun 实验顺序

### Step 1：INT8 canonical path

先覆盖论文主心脏，以保证后续正文主表与核心图不依赖 exploratory 唯一来源。

### Step 2：cross-model allocator / auto-k compare set

按模型顺序建议：

1. `3B`
2. `8B`
3. `14B`
4. `Mistral-7B`

建议理由：

- 先用 `3B` 复核最特殊 regime
- 再复核 `8B/14B` 的 top-tier 但非最优位置
- 最后复核 `Mistral` 的 strongest positive signal

### Step 3：extend-task supporting evidence

只覆盖：

- `dureader`
- `lcc`

---

## 6. clean vs exploratory 对照规则

### 6.1 需要生成的对照

至少包含：

1. mean ranking stability
2. task-best stability
3. key gap stability
4. mainline judgment stability

### 6.2 默认升级门槛

可以从 `candidate-main` 升级到 `final-ready support` 的条件：

1. 主结论方向不翻转
2. top-tier policy 相对位置基本稳定
3. task-best 与强 baseline 关系不发生根本变化

### 6.3 不能直接升级的情况

若出现以下任一情况，不能直接继承 exploratory 结论：

- auto-k 从 top-tier 掉到明显弱势
- heuristic / uniform 的相对地位根本翻转
- 3B early-layer regime 消失
- Mistral-specific win 不再成立

---

## 7. 阶段性 Gate

### Gate P0：preflight

必须确认：

- clean checkout 成功
- calibration 流程正常
- 关键脚本可运行

### Gate P1：canonical path

必须确认：

- canonical path 结果在 clean 条件下稳定

### Gate P2：cross-model compare set

必须确认：

- 4-model 关键主张是否维持

### Gate P3：supporting extend-task

必须确认：

- `dureader / lcc` 是否继续支持 supporting evidence 口径

---

## 8. 最终交付物

一次完整 clean-provenance rerun 至少应产出：

1. `clean rerun manifest`
2. `pin + env + md5 ledger`
3. `calibration provenance record`
4. `exploratory vs clean comparison table`
5. `clean rerun readout`
6. 更新：
   - [docs/thesis_upgrade_live_plan.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_upgrade_live_plan.md)
   - [docs/mainline_execution_queue.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/mainline_execution_queue.md)
   - [iteration.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/iteration.md)

---

## 9. 当前建议

默认建议：

1. 先不要把 `L2` 混入 clean rerun
2. 以 `ddada19` 为 pin 单独启动 `L1 claim-critical` clean rerun
3. 完成 clean 对照后，再决定哪些结论可以升级到 `final-ready support`

一句话总结：

> **当前 clean-provenance 的任务，不是继续发现新信号，而是把已经成立的 `candidate-main` 主线变成可审计、可引用、可进入最终主表的结果支撑。**
