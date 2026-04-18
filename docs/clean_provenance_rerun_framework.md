# Clean-Provenance Rerun Framework

> 用途：定义从当前 `exploratory` 结果过渡到 `candidate-main / final-ready` 的 clean-provenance 覆盖框架。

---

## 1. 背景

当前 Phase 2.6 的大量结果已经能够支持主线升级，但其 provenance 仍主要属于：

- `exploratory`

原因不是数据无效，而是：

- 远端工作树不是严格的 clean checkout gold standard
- 一部分链路是在持续演进中接起来的
- 因此当前结果适合更新叙事和工作台，不适合作为最终唯一 publishable claim

---

## 2. 目标

clean-provenance rerun 的目标不是把所有 exploratory 结果全重跑一遍，而是：

1. 覆盖**真正进入论文主张**的关键波次
2. 保证：
   - 代码 pin 明确
   - 校准产物来源明确
   - 结果目录与代码 provenance 对齐
3. 回答：
   - exploratory 结论是否在 clean 条件下复现

---

## 3. 三层 provenance 纪律

### Layer 1: Exploratory

- 允许快速承接
- 用于发现信号、更新工作台、收紧主线
- 不直接作为 final claim 唯一来源

### Layer 2: Candidate-Main

- 关键方法与关键结果在较稳定路径下复核
- 可进入论文草稿与主表候选

### Layer 3: Final-Ready

- clean checkout
- 关键 artifact 与结果全可追溯
- 与论文最终表述一一对应

---

## 4. 覆盖优先级

### Priority A：必须覆盖

1. `INT8 canonical path`
2. `Wave 1 + Wave 4 + Wave 5` 中真正进入 auto-k 主线的结果
3. allocator 主结论所依赖的核心模型/任务组合

### Priority B：建议覆盖

4. extend-task 线中的高信息量任务
   - 主要是 `dureader`
   - 次要是 `lcc`

### Priority C：可延后

5. 低信息量任务
6. 不进入正文主 claim 的 exploratory 支撑结果

---

## 5. 推荐执行顺序

### Step 1：代码与环境 pin

需要明确：

- pin commit
- 远端 clean checkout
- 运行环境版本
- 关键脚本 md5 / provenance

### Step 2：关键 calibration clean 化

优先 clean 的不是所有模型，而是：

- 进入主表或主 finding 的模型
- 当前依赖最新脚本修复的模型

### Step 3：关键 wave 覆盖重跑

优先顺序：

1. canonical path
2. auto-k 关键主张组合
3. extend-task 高信息量组合

### Step 4：探索层 vs clean 层比对

至少回答：

1. 均值排名是否稳定
2. task-best 是否稳定
3. 主结论是否发生翻转

---

## 6. 一致性判断门槛

clean rerun 不要求逐数完全相同，但至少要满足：

1. 主结论方向不翻转
2. top-tier policy 的相对位置基本稳定
3. task-level 最优与强基线关系不发生根本变化

如果出现以下情况，则不能直接继承 exploratory 结论：

- auto-k 从前列掉到明显弱势
- heuristic / uniform 的相对地位根本翻转
- 关键 regime 结论不再成立

---

## 7. 交付物

一次完整的 clean-provenance rerun 应至少产出：

1. pin 信息
2. rerun manifest
3. 结果目录 provenance 说明
4. exploratory vs clean 对照表
5. 升级后的主线判读

---

## 8. 当前建议

在当前阶段，不要一边继续扩新方向，一边无限延后 clean-provenance。  
更合理的顺序是：

1. 先补完 `Wave 4 backfill`
2. 统一判读 `Wave 1 + Wave 4`
3. 跑 `Wave 6`
4. 然后尽快进入 clean-provenance 覆盖框架
