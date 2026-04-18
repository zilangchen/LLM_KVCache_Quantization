# Auto-K Range Proposer 实验设计草案

> 用途：这不是结果页，也不是论文正文草稿。  
> 它是一份**实验设计文档**，回答一个新问题：  
> **能否不再手工 sweep 固定 `k`，而是根据 calibration / sensitivity profile 自动提出一个高概率 `k` 区间？**

---

## 1. 问题定义

当前 allocator 实验的基本形态是：

- 先手工选一组 `k`
- 再比较不同 policy：
  - `bakv_k1 / k3 / k5 / k7 / ...`
  - `heuristic_k*`
  - `random3_k*`

这有两个问题：

1. **fixed-k 不稳**
   - 1.5B、7B、8B、14B 不一定共享同一个最优 `k`
   - 同一个模型在扩大 search space 后，也可能出现“旧 best-k 被新候选推翻”的情况

2. **fixed-k 不像方法贡献**
   - 手工 sweep `k` 更像实验协议
   - reviewer 更容易问：  
     “你是不是只是试了很多个 `k`，然后挑一个最好看的？”

因此更自然的升级方向是：

> **让模型自己提出一个最有可能的预算区间，而不是人工预先写死单个 `k`。**

---

## 2. 为什么不能只按模型大小猜 `k`

一个很自然的直觉是：

> 模型越大，应该保护的层越多。

这个直觉**有吸引力**，但不应直接当最终方法。

### 原因 1：现有跨模型证据并不单调

- 旧版 `phase2_final_readout` 给出的口径是：
  - 1.5B → `k=1`
  - 7B → `k=5`
  - 8B → `k=1`（但很弱）
- 这不支持“参数量单调决定 best-k”

### 原因 2：同一模型扩展 search space 后，结论也可能变化

- 8B `Wave 1` 新结果显示：
  - `bakv_k11` 当前优于 `bakv_k9`
  - 也优于 `heuristic_k11`
- 这说明：
  - “更大模型可能需要更大 budget”这个直觉**被增强了**
  - 但它更像是**需要根据 profile 自动选预算**
  - 不是简单用参数量写规则：`if 8B then k=11`

### 原因 3：真正起作用的可能不是参数量，而是 profile

allocator 当前依赖的是：

- calibration 产物
- layer sensitivity
- aggregation 方式（`max` / `mean`）

所以更合理的候选方法是：

> **profile-aware auto-k**

而不是：

> **size-only hard-coded k**

---

## 3. 方法候选

下面这些候选都比“只按模型大小硬编码 `k`”更合理。

### 3.1 Threshold-based auto-k

规则：

- 先计算每层 sensitivity
- 设一个阈值 `τ`
- `sensitivity >= τ` 的层全部保护

优点：

- 最直接
- 最好解释
- `k` 自动由 profile 决定

风险：

- 阈值 `τ` 本身需要选
- 不同模型的 sensitivity 量纲可能不完全可比

---

### 3.2 Coverage-based auto-k range

规则：

- 将 layer sensitivity 从大到小排序
- 选择最小的 `k`
- 让前 `k` 层覆盖总 sensitivity 的 `p%`
- 不只输出一个 `k`，而是输出 `70% / 80% / 90%` 三档 coverage 对应的候选区间

例如：

- `p = 70% / 80% / 90%`
- 输出：
  - `candidate_ks = [k70, k80, k90]`（去重后）
  - `recommended_k = k80`

优点：

- 非常直观
- 容易写进论文
- “保护最重要的那一部分层”很好解释

我目前最推荐这个作为**主候选**，并且已经作为 v1 直接接入当前 Phase 2 policy 生成链。

---

### 3.3 Elbow / Knee-point auto-k

规则：

- 对排序后的 sensitivity 曲线找拐点
- 拐点之前的层保护，之后不保护

优点：

- 数据驱动感更强
- 看起来更像自动发现“预算窗口”

风险：

- 拐点检测容易不稳定
- 对噪声敏感

---

### 3.4 Percentile-based auto-k

规则：

- 保护 top `q%` 的层，而不是固定层数

例如：

- top 10%
- top 20%

优点：

- 简单
- 容易跨不同层数模型迁移

风险：

- 本质上还是比例版 fixed-k
- 解释力不如 coverage-based

---

### 3.5 Size-only rule（只作为 ablation，不推荐主方案）

规则：

- 根据模型层数 / 参数量直接猜 `k`

例如：

- 1.5B → 1
- 7B → 5
- 8B → 9 或 11
- 14B → 更大

优点：

- 直观
- 容易实现

缺点：

- 太粗
- 容易被反例打穿
- 不像“behavior-aligned”方法，更像工程经验规则

**结论**：

> 只建议把它作为 baseline / ablation，不建议当主方法。  
> 主方法应当是 **profile-aware auto-k range proposer**。

---

## 4. 实验矩阵

### 4.1 模型顺序

建议按证据层级推进：

1. `Qwen2.5-1.5B-Instruct`
2. `Qwen2.5-7B-Instruct`
3. `LLaMA-3.1-8B-Instruct`
4. `Qwen2.5-14B-Instruct`
5. `Mistral-7B-Instruct-v0.3`

### 4.2 任务

优先 core tasks：

- `narrativeqa`
- `hotpotqa`
- `gov_report`

如果前面成立，再看是否扩展到：

- `dureader`
- `lcc`

不建议把：

- `trec`
- `vcsum`

作为 auto-k 主证据，因为它们在当前口径下信息量较弱。

### 4.3 对照组

每个模型至少比这几类：

1. **hand-tuned best-k**
   - 当前人工 sweep 找到的最好 `k`
2. **heuristic same-budget**
   - 与 auto-k 选出来的 budget 匹配
3. **random same-budget**
   - 同样 budget 的随机保护层
4. **size-only guessed-k**
   - 只按模型规模猜的 `k`

5. **auto-k recommended-k**
   - 即 `80% coverage` 对应的推荐点
   - 与 hand-tuned best-k 正面对比

---

## 5. 评估指标

### 5.1 质量指标

- 使用任务官方指标：
  - `f1`
  - `rouge_l`
  - 等已有 protocol

### 5.2 方法指标

除了最终分数，还要记录：

1. **selected k / candidate_ks**
2. **avg_bits**
3. **protected_layers**
4. **vs hand-tuned best-k 的差距**
5. **vs heuristic same-budget 的差距**

### 5.3 稳健性指标

- 3/3 task win consistency
- 不同模型 family 上是否稳定
- 是否比固定单一 `k` 更稳

---

## 6. 成功标准

auto-k 若要算成功，我建议至少满足下面 3 条里的 2 条：

1. **逼近 hand-tuned best-k**
   - 平均分与 hand-tuned best-k 的差距在小阈值内
   - 例如 `≤ 1% ~ 3%`

2. **优于固定单一 k**
   - 相比“所有模型都用同一个 fixed-k”，更稳

3. **优于 heuristic / random same-budget**
   - 在同 budget 下仍体现 behavior-guided 优势

如果只能做到：

- 和 hand-tuned best-k 差不多

那它仍然有价值，因为它把：

- “人工 sweep”

升级成了：

- “自动预算选择”

---

## 7. 风险与失败模式

### 风险 1：auto-k 只是复刻手工 best-k，没有额外价值

解释：

- 如果它只是近似 hand-tuned best-k，但没有更稳
- 那贡献更像“自动化工具”，不是新 finding

### 风险 2：不同 aggregation 下 auto-k 不稳定

解释：

- `max` / `mean` 可能导出完全不同的 `k`
- 这会让方法层叙事变复杂

### 风险 3：8B 新结果只是 search-space 扩大带来的局部翻盘

解释：

- `bakv_k11` 当前最强，并不自动意味着“更大模型都该大 k”
- 所以不能把当前 8B 结果直接拿来写 size-only 规律

### 风险 4：reviewer 会问“为什么不直接 sweep k”

回答方向：

- 因为我们想把 allocator 从实验技巧升级成**自动化决策能力**

### 风险 5：profile-aware 方法可能在某些 family 上失效

这其实不是坏事：

- 它本身也能成为“family-specific regime” 的一部分证据

---

## 8. 对论文主线的潜在价值

如果 auto-k 成立，它对论文的价值非常直接：

### 价值 1：比“单调 scale-shift”更稳

它不要求你证明：

- 模型越大，`k` 必然单调上升

只要求你证明：

- **模型 profile 可以自动决定合适预算**

这个更容易站得住。

### 价值 2：把 allocator 从“观察结果”升级成“方法能力”

也就是从：

- “我们发现不同模型 best-k 不一样”

升级成：

- “我们的方法可以自动决定该保护多少层”

### 价值 3：和 behavior-aligned framework 更一致

因为它真正依赖的是：

- calibration
- sensitivity profile
- behavior signal

而不是手工经验。

---

## 9. 当前推荐路线

我建议：

### 主候选

- **coverage-based auto-k**

### 次候选

- `threshold-based auto-k`
- `elbow-based auto-k`

### baseline / ablation

- `size-only guessed-k`

---

## 10. 当前工作结论

这条线现在已经足够值得推进，但口径应当是：

> **8B 扩展结果增强了“更大 budget 可能更好”的直觉；**
> **真正值得升级成方法贡献的不是“模型越大 -> k 越大”的硬规则，**
> **而是“根据 profile 自动决定该保护多少层”的 auto-k selector。**

它目前最适合在论文里扮演的角色是：

- `thesis_upgrade_live_plan` 中的**升级候选**
- 不是已经成立的最终结论
