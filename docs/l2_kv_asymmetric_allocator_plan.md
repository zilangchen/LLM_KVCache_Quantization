# L2 Plan: K/V Asymmetric Allocator

## 1. 方向定位

`K/V asymmetric allocator` 是当前 [objective.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/objective.md) 中最自然、最靠前的 `L2` 升级方向。

它的目标不是重新发明 MixedKV，而是把项目已经具备的：

- `K > V` 敏感性诊断
- `k_bits / v_bits` 路由能力
- `MixedKV` 执行路径
- layer-wise allocation policy

从“mixed-precision heuristic”提升为**显式的 role-aware budget allocator**。

## 2. 为什么它属于 L2

它不属于当前 `L1`，因为：

- 当前 allocator 仍然主要是 `layer-wise`；
- 当前 sensitivity 仍然主要来源于单一 layer profile；
- 当前 policy 还没有真正对 `K` 与 `V` 进行独立打分与独立决策。

但它也不应该放到过远的 future work，因为：

- 项目已经有关键执行基础设施；
- 理论和经验前置证据都在；
- 它比 head-wise / learned allocator 更贴近当前主线资产。

## 3. 当前已有资产

### 3.1 执行路径

- [src/engine/generate_loop.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py)
- [src/cache/mixed_kv_cache.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/cache/mixed_kv_cache.py)

当前系统已支持 `(k_bits, v_bits)` 路由与 `per_layer_bits` policy 消费。

### 3.2 诊断资产

- `K > V` 敏感性结论
- MixedKV 已有正向经验
- `K/V` ablation 脚本与历史结果

### 3.3 allocator 资产

- [scripts/adaptive/behavior_aligned_allocator.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py)
- 当前 `top_k / heuristic / random / auto_k_coverage`

这意味着：系统已经具备 role-aware allocator 的落地土壤，但还缺少真正的 `K/V dual-score` 决策层。

## 4. 当前缺口

1. 还没有独立的 `K-score` 与 `V-score`
2. 还没有真正的 role-aware policy schema
3. 还没有 K/V asymmetric allocator 的专门实验矩阵
4. 还没有关于它和 MixedKV / fixed policy / auto-k 的清晰比较协议

## 5. 推荐的执行顺序

### Phase A：建模层

- 定义 `K-sensitive` 与 `V-sensitive` 的独立代理
- 先不碰 kernel，只在 policy 生成层做 role-aware 选择

### Phase B：policy 层

- 扩展 allocator，使其输出更显式的 role-aware `(k_bits, v_bits)` 分配
- 先保留 layer-wise 粒度，不跳 head-wise

### Phase C：实验层

- 对比：
  - fixed MixedKV
  - current layer-wise allocator
  - role-aware asymmetric allocator
- 优先跑：
  - 1.5B / 7B / 8B
  - core tasks

### Phase D：写作层

- 若成立，则把它写成 allocation 线最自然的升级
- 若不成立，则至少可以作为“为何当前 layer-wise 仍是正确 stopping point”的负结果支撑

## 6. 验收标准

这个方向若要算推进成功，至少要满足：

1. 形成一个明确的 role-aware policy schema
2. 能在现有执行路径中稳定运行
3. 形成相对于当前 MixedKV / layer-wise policy 的可解释比较
4. 能回答“role-aware 是否提供超出 layer-wise 的额外价值”

## 7. 不做什么

- 不直接跳到 head-wise K/V allocator
- 不先碰 learned allocator
- 不把它预设成必然强于当前 auto-k
- 不在没有 clean 证据前把它写进正文主结论

## 8. 风险

1. `K > V` 的诊断不一定自动转化为 allocator 收益
2. role-aware policy 可能只是复刻 MixedKV heuristic
3. 实验矩阵会膨胀
4. 容易和 auto-k 主线抢位置

## 9. 建议地位

这是当前 `L2` 中**最值得先做**的一条，因为它最直接继承当前论文已有资产。
