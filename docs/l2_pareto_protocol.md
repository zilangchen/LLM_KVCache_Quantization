# L2 Spec: Quality-Cost Pareto Protocol

> 角色：protocol spec  
> 对应高层计划：`docs/l2_pareto_analysis_plan.md`

---

## 1. 目标

把 allocator 线从“主要看 quality 排名”升级为：

> **quality-cost Pareto comparison**

换句话说，不再只问：

- 谁分数更高？

而是同时问：

- 在相同成本下谁质量更高？
- 在相同质量下谁成本更低？
- 哪些点位于新的 Pareto front？

---

## 2. 指标协议

## 2.1 Quality 维

### Primary

1. `LongBench` core-task score
2. `extend-task` 中的高信息量任务
   - 优先 `dureader`
   - 次选 `lcc`

### Secondary

3. `PPL`
4. `Needle`

### 默认排除

以下不作为 primary allocator evidence：

- `trec`
- `vcsum`

---

## 2.2 Cost 维

### Primary

1. `TTFT`
2. `TPOT`
3. `peak memory`
4. `avg_bits`

### Secondary

5. `tok/s`

---

## 3. 最小比较矩阵

### 3.1 模型

第一轮只建议：

1. `7B`
2. `8B`
3. `Mistral-7B`

### 3.2 Policy

第一轮建议固定比较这些：

1. `uniform_int4_k4v4`
2. strongest `heuristic`
3. strongest fixed-k
4. strongest `auto-k`
5. one `role-aware` candidate（若已存在）

---

## 4. 测量纪律

### 4.1 基本要求

1. latency / memory 测量必须在干净环境中进行
2. 比较组使用一致 batch / seq_len / gen_len
3. 成本与质量的结果必须能回到同一个 policy id

### 4.2 不允许的做法

1. 一边换 policy，一边换 batch size
2. 把 noisy latency 当成强结论
3. 把 `trec / vcsum` 纳入 primary Pareto front

---

## 5. 输出格式

### 5.1 表

至少输出：

| Model | Policy | Quality | TTFT | TPOT | Peak Mem | Avg Bits | Pareto? |
|---|---|---:|---:|---:|---:|---:|---|

### 5.2 图

至少两张：

1. `quality vs avg_bits`
2. `quality vs TPOT`

可选：

3. `quality vs peak memory`

---

## 6. Pareto 判定规则

一个点若被另一点同时满足：

- quality 更高或相等
- 且 cost 更低或相等
- 且至少一维严格更优

则前者支配后者。

最后需要明确标出：

1. front 上的点
2. 被完全支配的点
3. “接近 front 但不稳定”的点

---

## 7. 成功判据

只要出现下面任一情形，这条线就值得继续：

1. `auto-k` 或 role-aware allocator 进入 Pareto front
2. 现有强 baseline 被明显支配
3. 可以明确证明某类 policy 只是“高分幻觉”，不是真 trade-off

---

## 8. 首轮结束后必须回答的问题

1. allocator 是否真的有 budget allocation method 的资格？
2. `auto-k` 带来的收益更偏 quality，还是更偏 trade-off 改善？
3. role-aware allocator 是否比当前 layer-wise 更容易推到 front 上？
