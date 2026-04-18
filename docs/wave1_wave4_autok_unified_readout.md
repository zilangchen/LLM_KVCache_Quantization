# Wave 1 + Wave 4 Unified Auto-K Readout

> 状态：`exploratory`  
> 更新时间：2026-04-19 04:27 CST  
> 用途：统一判读 `Wave 1 (8B)` 与 `Wave 4 (14B)` 的 auto-k 结果，回答 auto-k 是否已经从 `Mistral-first evidence` 扩张为更稳的跨 scale 扩展。

---

## 1. 结论先行

当前最稳的统一结论是：

> **auto-k 已经从 Mistral-only 的局部正面证据，扩张成在 `8B / 14B / Mistral-7B` 上都具备实质竞争力的 profile-aware 扩展；但它仍然不是跨模型统一最优解，因此更适合被写成 framework 下游的强扩展能力，而不是 universal winner。**

---

## 2. 两个关键波次的直接对照

### 2.1 `Wave 1 (8B)`

当前 8B 三任务平均分前列：

| Rank | Policy | 3-task mean |
|---|---|---:|
| 1 | `bakv_k11` | 9.5214 |
| 2 | `bakv_auto_cov80_max` | 9.3543 |
| 3 | `bakv_auto_cov90_max` | 9.3491 |
| 4 | `bakv_auto_cov70_max` | 9.2949 |

8B 的结论是：

- `auto-k` 已进入强二梯队
- 明显强于 heuristic / mean-k
- 但略低于 best fixed-k（`bakv_k11`）

### 2.2 `Wave 4 (14B)`

当前 14B 三任务平均分前列：

| Rank | Policy | 3-task mean |
|---|---|---:|
| 1 | `uniform_int4_k4v4` | 7.2345 |
| 2 | `bakv_auto_cov90_max` | 7.1501 |
| 3 | `bakv_auto_cov80_max` | 7.1213 |
| 4 | `heuristic_k3` | 7.1171 |
| 5 | `bakv_auto_cov70_max` | 7.1160 |

14B 的结论是：

- 三个 `auto-k` 全部进入前五
- 最好的 `auto-k` 拿到全局第 2
- `auto-k` 整体上强于 strongest heuristic 与 strongest behavior-guided fixed-k
- 但仍低于最强 uniform baseline

---

## 3. 跨 scale 的统一读法

### 3.1 auto-k 不再只是 Mistral 的局部现象

到目前为止：

- Mistral：`bakv_auto_cov80_max` 拿到当前 full sweep 平均分第一
- 8B：`auto-k` 进入强二梯队
- 14B：`auto-k` 进入 top tier，并拿到全局第 2

因此，现在已经不能把 auto-k 写成：

- 只在 Mistral 上有效
- 或只是一组偶然的 exploratory hit

### 3.2 auto-k 的强度在不同 scale 上不一样

更稳的读法是：

- `8B`：competitive but not best
- `14B`：top-tier, stronger than heuristic/fixed-k, but not best overall
- `Mistral`：strongest current average policy

这正好进一步支持：

> auto-k 的价值是 **family-/scale-dependent** 的，而不是一条统一的跨模型胜利规律。

### 3.3 strong baselines 仍然存在

这条结论同样必须写清：

- 8B 上最优仍是 `bakv_k11`
- 14B 上最优仍是 `uniform_int4_k4v4`
- Mistral 上 `heuristic_k3` 仍在 `narrativeqa` 上保留 task-best

所以当前最稳的论文写法不是：

- `auto-k beats all`

而是：

- `auto-k becomes a strong profile-aware extension with cross-scale empirical support, while strong baselines remain active and regime-dependent.`

---

## 4. 主线意义

这份 unified readout 对论文主线有三个直接作用：

1. **支持把 auto-k 正式升级为方法扩展**
   - 它已经不只是计划或局部试验
   - 而是拿到了跨多个模型尺度的正面 empirical 支撑

2. **进一步打掉 universal allocator law 的旧冲动**
   - 8B / 14B / Mistral 的最优关系并不一致
   - 说明更稳的解释仍然是 regimes，而不是单一 law

3. **给 `Wave 6` 提供清晰前文**
   - 现在跑 3B，不再是盲目加数据
   - 而是要看 3B 落在哪种 regime 里

---

## 5. 当前建议写法

### 5.1 工作台短版

`Wave 1 + Wave 4` 的统一 readout 显示，auto-k 已经从 Mistral-only 的局部正面信号扩张为跨 scale 的强扩展证据：在 8B 上它进入强二梯队，在 14B 上进入 top tier 并整体强于 heuristic / fixed-k 行为引导策略。但 strongest baseline 在不同模型上仍然不同，因此更稳的主线仍是 family-/scale-dependent regimes，而不是把 auto-k 写成 universal winner。

### 5.2 论文口径短版

Taken together, the 8B and 14B backfills show that the auto-k range proposer is no longer a Mistral-only positive signal. It becomes competitive on 8B and top-tier on 14B, which upgrades auto-k into a stronger profile-aware extension with genuine cross-scale empirical support. However, the strongest baseline still differs by model family and scale, so the evidence continues to favor a regime-based interpretation rather than any universal winner claim.

