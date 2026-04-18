# Extend-Task Redesign Memo

> 状态：内部 memo  
> 用途：收紧 `Wave 7a / 7b` 的解释边界，避免继续把低信息量任务当成 allocator 主证据。

---

## 1. 背景

当前 extend-task 链已经覆盖：

- `Wave 7a (7B extend tasks)`
- `Wave 7b (8B extend tasks)`

共同特征已经很清楚：

- `dureader` 持续有信息量
- `lcc` 提供了额外维度，值得继续观察
- `trec / vcsum` 长期接近 floor

这意味着：extend-task 线不能继续按“4 个任务等权”来组织。

---

## 2. 新的任务分层

### 2.1 一级证据任务

#### `dureader`

定位：

- extend-task 线的主证据任务

原因：

- allocator policy 之间能拉开明显差距
- 在 7B 与 8B 上都持续有信息量

### 2.2 二级证据任务

#### `lcc`

定位：

- 补充性任务
- 用来验证 extend-task 线是否不只局限于 `dureader`

原因：

- 它不像 `trec / vcsum` 一样长期贴地
- 但当前还不足以独立扛起 allocator 主结论

### 2.3 低信息量任务

#### `trec`
#### `vcsum`

定位：

- scope / boundary disclosure
- 低信息量任务说明

原因：

- 当前在 7B / 8B extend-task 线上长期接近 floor
- 更像模型能力或 metric 地板，而不是 allocator 区分维度

---

## 3. 后续默认处理口径

### 3.1 论文写法

今后关于 extend-task 的更稳写法应当是：

> extend-task evidence is heterogeneous: `dureader` provides the clearest allocator signal, `lcc` acts as a secondary supporting task, while `trec` and `vcsum` remain low-information under the current model/metric setting.

### 3.2 工作台写法

工作台中应继续坚持：

- `dureader`：保留为 allocator 证据
- `lcc`：保留为补充任务
- `trec / vcsum`：只作为边界披露

### 3.3 主文权重

extend-task 线当前不应提升为 allocator 主 finding。  
它更适合作为：

- task heterogeneity supporting evidence
- 或附录/局限性说明的一部分

---

## 4. 后续实验设计建议

### 4.1 不再做的事

1. 不再把 `trec / vcsum` 当 allocator 主证据继续堆量
2. 不再把 “4/4 all pass” 这种机械 gate 当成强 finding

### 4.2 更合理的下一步

1. 若继续补 extend tasks，优先围绕 `dureader + lcc`
2. 若要加新任务，应优先找：
   - 不会长期贴地
   - allocator 之间有区分度
   - 和长上下文理解更相关

---

## 5. 对主线的影响

这份 memo 的作用不是削弱 extend-task，而是收紧它的解释边界：

1. 它帮助避免把低信息量任务误写成强证据
2. 它支持当前更稳的主线：
   - regime-based interpretation
   - task-dependent evidence strength
3. 它让 `Wave 7a / 7b` 更适合作为 supporting evidence，而不是 allocator 主 finding
