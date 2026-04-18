# Wave 4 Auto-K Readout

> 状态：`exploratory`  
> 更新时间：2026-04-19 04:27 CST  
> 用途：记录 `Wave 4 (Qwen-14B)` 在补齐 `auto-k` 之后的正式判读，供 `Wave 1 + Wave 4` 统一 readout、工作台和主线收口使用。

---

## 1. 数据范围

本次 readout 覆盖 `Wave 4` 新补的 `9` 条 `auto-k` 结果：

- `bakv_auto_cov70_max`
- `bakv_auto_cov80_max`
- `bakv_auto_cov90_max`

任务集合：

- `narrativeqa`
- `hotpotqa`
- `gov_report`

当前 `Wave 4` 总计数：

- 基础 sweep：`36`
- `auto-k backfill`：`9`
- 当前总量：`45`

---

## 2. 新增 9 条结果

| Policy | narrativeqa | hotpotqa | gov_report | 3-task mean |
|---|---:|---:|---:|---:|
| `bakv_auto_cov70_max` | 6.9005 | 5.4273 | 9.0202 | 7.1160 |
| `bakv_auto_cov80_max` | 6.6909 | 5.3265 | 9.3466 | 7.1213 |
| `bakv_auto_cov90_max` | 6.7967 | 5.3856 | 9.2679 | 7.1501 |

---

## 3. 当前 14B 三任务平均分位置

将 `Wave 4` 当前主要 policy 按 `narrativeqa / hotpotqa / gov_report` 三任务平均分排序，前列如下：

| Rank | Policy | 3-task mean |
|---|---|---:|
| 1 | `uniform_int4_k4v4` | 7.2345 |
| 2 | `bakv_auto_cov90_max` | 7.1501 |
| 3 | `bakv_auto_cov80_max` | 7.1213 |
| 4 | `heuristic_k3` | 7.1171 |
| 5 | `bakv_auto_cov70_max` | 7.1160 |
| 6 | `heuristic_k7` | 7.0886 |
| 7 | `uniform_int8_k8v8` | 7.0593 |
| 8 | `bakv_k1` | 7.0583 |

当前最值得注意的点是：

1. 三个 `auto-k` policy 全部进入前五；
2. 最好的 `auto-k`（`bakv_auto_cov90_max`）拿到全局第 2；
3. `auto-k` 整体上已经超过 strongest heuristic 与当前最强 behavior-guided fixed-k；
4. 但它仍然没有超过当前最优 baseline：`uniform_int4_k4v4`。

---

## 4. task-level 位置

### 4.1 `narrativeqa`

- 当前 best：`uniform_int4_k4v4 = 7.0464`
- `auto-k` 最好：`bakv_auto_cov70_max = 6.9005`

判读：

- `auto-k` 在 `narrativeqa` 上进入强竞争区间
- 但没有超过当前最优 uniform baseline

### 4.2 `hotpotqa`

- 当前 best：`heuristic_k3 = 5.6282`
- `auto-k` 最好：`bakv_auto_cov70_max = 5.4273`

判读：

- `auto-k` 在 `hotpotqa` 上有竞争力
- 但当前仍低于 strongest heuristic

### 4.3 `gov_report`

- 当前 best：`bakv_auto_cov80_max = 9.3466`
- `auto-k` 最好：`bakv_auto_cov80_max = 9.3466`

判读：

- `auto-k` 在 `gov_report` 上拿到当前 14B 的 task-best
- 这说明它并不只是“平均分接近”，而是在至少一个高信息量任务上具备实际优势

---

## 5. 当前最稳判断

`Wave 4` 现在支持的不是“14B 上 auto-k 已经成为最优统一解”，而是：

> **auto-k 在 14B 上已经进入当前最强 policy 的前列，并明显强于同波次中的 heuristic / fixed-k 行为引导策略；但它仍然没有超过最强 uniform baseline。**

这会把 14B 上的写法收紧成：

1. `auto-k` 已经不再只是 Mistral 上的局部正面信号；
2. 它在 14B 上拿到了明确的 top-tier 位置；
3. 但它仍然不是 14B 上的 universal winner。

---

## 6. 对论文主线的意义

这批结果强化了三个判断：

1. **14B 继续反对“单调 fixed-k scale-shift”旧叙事**
   - 更强信号来自 profile-aware range proposer，而不是固定 `k` 本身

2. **auto-k 在 14B 上比在 8B 上更强**
   - 8B：强二梯队，但低于 best fixed-k
   - 14B：进入全局前列，并优于 strongest heuristic / strongest fixed-k

3. **更稳的主线仍然是 regime-based**
   - `uniform_int4_k4v4` 仍然是全局最好
   - 说明 14B 的结论不是“auto-k 已普适赢”
   - 而是：profile-aware proposer 很强，但 strong baselines 仍然存在

---

## 7. 推荐写法

### 7.1 工作台短版

`Wave 4 auto-k backfill` 显示，14B 上的三组 `auto-k` policy 全部进入当前最强 policy 前列，其中 `bakv_auto_cov90_max` 拿到全局第 2，`bakv_auto_cov80_max` 在 `gov_report` 上拿到 task-best。它们整体上已经强于 strongest heuristic 与 strongest behavior-guided fixed-k，但仍低于最强 uniform baseline（`uniform_int4_k4v4`）。因此，14B 证据支持把 auto-k 写成跨 scale 的强扩展，而不支持把它写成 universal winner。

### 7.2 论文口径短版

On Qwen-14B, the auto-k range proposer becomes a top-tier policy family: all three auto-k variants rank near the top, the best one reaches second overall, and one variant achieves the best `gov_report` score. However, the strongest uniform baseline still remains first. This further supports auto-k as a strong profile-aware extension, while still favoring a regime-based interpretation over any universal winner claim.

