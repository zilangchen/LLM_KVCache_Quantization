# L2 Plan: Prompt-Adaptive Allocation

## 1. 方向定位

`Prompt-adaptive allocation` 的目标，是让 allocator 从“全局静态共享 policy”向“根据输入/任务特征选择预算策略”迈进一步。

它不是：

- head-wise allocation
- online learned controller

而是一个更轻、更现实的中间升级方向。

## 2. 为什么它属于 L2

它不属于当前 `L1`，因为当前 allocator 仍然是离线静态 policy。  
但它也不应被推到很远的 future work，因为：

- 它可以先在 policy-selection 层实现；
- 不一定要立刻碰 kernel 或 cache schema；
- 比 head-wise / learned allocator 更贴近当前工程现实。

## 3. 当前已有资产

### 3.1 静态 policy 池

当前系统已经有：

- fixed top-k
- heuristic
- random
- auto-k coverage proposer

### 3.2 多任务/多模型差异证据

当前结果已经显示：

- family-/scale-/task-dependent regimes
- 不同任务对 allocator 的区分度并不一致
- 某些任务长期低信息量

这些都说明：静态 one-policy-fits-all 已经开始显得不够自然。

## 4. 当前缺口

1. 还没有“按 prompt / task / profile 选择 policy”的路由层
2. 还没有定义 prompt-adaptive 的最小可行版本
3. 还没有验证它是否优于“直接固定用 auto-k 或 best-k”

## 5. 推荐执行顺序

### Phase A：轻量版本定义

不要上来就做真正 runtime adaptive control。  
先做最轻版本：

- task-aware selector
- prompt-length-aware selector
- profile-bucket selector

### Phase B：离线路由器

先构造一个简单的路由规则：

- 若任务/输入特征属于某类，则从现有 policy 池中选一个
- 仍然使用静态 policy JSON
- 不改 kernel

### Phase C：与静态 policy 对照

核心比较对象：

- one global best-k
- one global auto-k
- prompt/task-adaptive selector

### Phase D：决定是否值得继续升级

若轻量版本都没有价值，就没必要马上去做更重的 online adaptive allocator。

## 6. 验收标准

1. 定义一个清楚的 prompt-adaptive 最小版本
2. 能在不重写底层执行路径的前提下运行
3. 能回答“按输入特征选 policy 是否优于全局单 policy”
4. 若失败，也能明确说明为什么当前停在静态 allocator 更合理

## 7. 不做什么

- 不直接做 learned allocator
- 不做 token-region allocation
- 不做 head-wise prompt-adaptive allocation
- 不在当前阶段引入复杂在线控制器

## 8. 风险

1. 任务标签本身可能已经泄露太多信息，导致方法价值被质疑
2. 轻量路由器可能只是重新包装 heuristic
3. 若输入特征定义不稳，结果会缺乏可迁移性
4. 很容易和 auto-k 的“全局 profile-aware”定位混淆

## 9. 建议地位

这是当前 `L2` 中**第三优先级**的方向。  
它比 head-wise 更现实，但应当建立在静态 allocator 与 role-aware allocator 已经更清楚之后。
