# L2 Plan: Quality-Cost Pareto Analysis

## 1. 方向定位

`Pareto analysis` 的目标，是把当前 allocator 线从“主要比较 task quality”升级为“同时比较质量与成本的预算分配方法”。

它回答的问题不是：

- 谁分数更高？

而是：

- 谁在相同成本下质量更高？
- 谁在相同质量下成本更低？
- 哪些 policy 处在新的 quality-cost Pareto front 上？

## 2. 为什么它属于 L2

它不属于当前 `L1`，因为现有 allocator 主线主要仍是 quality-first 证据组织。  
但它也不是很远的 future work，因为：

- 仓库已经具备 latency / memory / PPL / Needle 的现成入口；
- allocator 若想从“实验技巧”升级成“预算分配方法”，Pareto 是自然必需的。

## 3. 当前已有资产

### 3.1 质量评测入口

- [scripts/eval_longbench.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/eval_longbench.py)
- [scripts/eval_ppl.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/eval_ppl.py)
- [scripts/eval_needle.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/eval_needle.py)

### 3.2 成本评测入口

- [scripts/profile_latency.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/profile_latency.py)
- [scripts/profile_memory.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/profile_memory.py)

### 3.3 已有图像资产

- `pareto_quality_efficiency.pdf`

这说明：工具链已经有了，但 allocator 线还没有把它们组织成完整的 Pareto story。

## 4. 当前缺口

1. allocator policy 还没有统一的 quality-cost evaluation protocol
2. `LongBench / extend tasks / PPL / Needle / latency / memory` 还没有被组织到同一比较框架
3. 还没有明确哪些指标是 primary，哪些是 supporting
4. 还没有定义 allocator 的 Pareto front 口径

## 5. 推荐执行顺序

### Phase A：定义协议

- 明确 quality 维：
  - LongBench-style score
  - extend-task informative tasks
  - PPL
  - Needle

- 明确 cost 维：
  - TTFT
  - TPOT
  - peak memory
  - avg_bits

### Phase B：最小矩阵

- 不要一上来全模型全任务
- 先挑：
  - 7B / 8B / Mistral
  - fixed best-k
  - heuristic
  - auto-k
  - one role-aware candidate（若已有）

### Phase C：可视化

- 画 Pareto front
- 标出被完全支配的 policy
- 明确哪些点是真正的新 trade-off

### Phase D：论文映射

- 若 Pareto front 清楚，可把 allocator 从“分数改进”升级成“budget allocation method”
- 若不清楚，也能反过来证明 allocator 只是 quality-side extension，而不是完整系统方法

## 6. 验收标准

1. 形成一个统一的 quality-cost evaluation protocol
2. 至少一组模型/任务上能画出有解释力的 Pareto 图
3. 能明确回答哪些 policy 位于 Pareto front
4. 能为论文提供“allocator 是否真的值得升格”的判断依据

## 7. 不做什么

- 不在这一层引入 serving concurrency 压测
- 不做全平台 benchmarking
- 不把 Pareto 分析扩张成系统论文
- 不让它取代当前主线中的 behavior/regime 解释

## 8. 风险

1. 不同指标之间可能相互冲突，导致 front 很难解释
2. `trec / vcsum` 等低信息量任务会污染结论
3. 成本评测比质量评测更容易受环境噪声影响
4. 若矩阵太大，执行成本会上升很快

## 9. 建议地位

这是当前 `L2` 中**第二优先级**的方向。  
它不能替代 `K/V asymmetric allocator`，但它决定 allocator 能不能从“实验现象”升级成“预算分配方法”。
