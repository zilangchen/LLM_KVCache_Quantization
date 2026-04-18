# Wave 1 Auto-K Readout

> 状态：`exploratory`  
> 更新时间：2026-04-19 04:18 CST  
> 用途：记录 `Wave 1 (8B extended)` 在补齐 `auto-k` 之后的最新判读，供工作台、主线收口和后续 `Wave 1 + Wave 4` 统一 readout 使用。

---

## 1. 数据范围

本次 readout 只覆盖 `Wave 1` 新补的 `9` 条 `auto-k` 结果：

- `bakv_auto_cov70_max`
- `bakv_auto_cov80_max`
- `bakv_auto_cov90_max`

任务集合：

- `narrativeqa`
- `hotpotqa`
- `gov_report`

当前 `Wave 1` 总计数：

- 基础 sweep：`21`
- `auto-k backfill`：`9`
- 当前总量：`30`

---

## 2. 新增 9 条结果

| Policy | narrativeqa | hotpotqa | gov_report | 3-task mean |
|---|---:|---:|---:|---:|
| `bakv_auto_cov70_max` | 10.6595 | 7.6771 | 9.5482 | 9.2949 |
| `bakv_auto_cov80_max` | 10.7415 | 7.5672 | 9.7543 | 9.3543 |
| `bakv_auto_cov90_max` | 10.9275 | 7.5368 | 9.5830 | 9.3491 |

---

## 3. 当前 8B 三任务平均分位置

将 `Wave 1` 当前主要 policy 按 `narrativeqa / hotpotqa / gov_report` 三任务平均分排序，前列如下：

| Rank | Policy | 3-task mean |
|---|---|---:|
| 1 | `bakv_k11` | 9.5214 |
| 2 | `bakv_auto_cov80_max` | 9.3543 |
| 3 | `bakv_auto_cov90_max` | 9.3491 |
| 4 | `bakv_auto_cov70_max` | 9.2949 |
| 5 | `bakv_mean_k3` | 8.9105 |
| 6 | `bakv_mean_k5` | 8.6082 |
| 7 | `bakv_k9` | 8.5695 |
| 8 | `heuristic_k11` | 8.5416 |
| 9 | `heuristic_k9` | 8.3514 |

---

## 4. task-level 位置

### 4.1 `narrativeqa`

- 当前 best：`bakv_k11 = 11.1405`
- `auto-k` 最好：`bakv_auto_cov90_max = 10.9275`

判读：

- `auto-k` 在 `narrativeqa` 上非常接近当前 best fixed-k
- 但尚未超过 `bakv_k11`

### 4.2 `hotpotqa`

- 当前 best：`bakv_k11 = 7.8840`
- `auto-k` 最好：`bakv_auto_cov70_max = 7.6771`

判读：

- `auto-k` 在 `hotpotqa` 上是强竞争者
- 但当前仍低于 best fixed-k

### 4.3 `gov_report`

- 当前 best：`bakv_k9 = 9.7799`
- `auto-k` 最好：`bakv_auto_cov80_max = 9.7543`

判读：

- `auto-k` 在 `gov_report` 上几乎贴近当前 best fixed-k
- 但尚未形成明确超越

---

## 5. 当前最稳判断

`Wave 1` 现在支持的不是“8B 上 auto-k 已经赢了”，而是：

> **auto-k 在 8B 上已经补成强二梯队，并且明显强于 heuristic / mean-k 系列；但它仍然略低于当前 best fixed-k。**

这会把当前主线进一步收紧成：

1. `auto-k` 在 8B 上已经拿到**完整、竞争力很强**的正面证据；
2. 但它**不是 8B 上的当前最优 policy**；
3. 因此它更适合被写成：
   - 一个有 empirical 支撑的 profile-aware 扩展；
   - 而不是 fixed-k 的普适替代者。

---

## 6. 对论文主线的意义

这批结果强化了三个判断：

1. **fixed-k 口径并不稳**
   - 因为 `bakv_k9` 和 `bakv_k11` 各自在不同 task 上占优
   - 说明单一手工 `k` 并不自然

2. **auto-k 是强扩展，但仍非 universal winner**
   - 它已经可以和 best fixed-k 直接竞争
   - 但还没有在 8B 上把 fixed-k 全面压下去

3. **更稳的主线仍然是 regime-based**
   - 8B 上的 `auto-k` 结果，支持“profile-aware budget proposal 值得写”
   - 不支持“auto-k 已经普适优于所有 baseline”

---

## 7. 推荐写法

### 7.1 工作台短版

`Wave 1 auto-k backfill` 显示，8B 上的 `bakv_auto_cov80/90` 已经进入当前最强政策的前列，并明显强于 heuristic / mean-k，但仍略低于 best fixed-k（`bakv_k11`）。因此，8B 证据支持把 auto-k 写成一个已具备竞争力的 profile-aware 扩展，而不是把论文主线改写成“auto-k 已普遍最优”。

### 7.2 论文口径短版

On LLaMA-3.1-8B, the auto-k range proposer becomes a strong competitive policy family, substantially outperforming heuristic baselines while remaining slightly below the best hand-picked fixed-k. This supports auto-k as a meaningful profile-aware extension, but not yet as a universal replacement for fixed-k selection.

---

## 8. 后续依赖

这份 readout 还不是最终 auto-k 结论。后续必须接：

1. 填完 `Wave 4 auto-k` 正式 readout
2. 做 `Wave 1 + Wave 4` 统一 readout
3. 再判断 auto-k 是否已经从 `Mistral-first positive evidence` 扩张到更稳的跨 family / scale 扩展
