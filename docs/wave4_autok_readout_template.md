# Wave 4 Auto-K Readout Template

> 状态：待填写模板  
> 用途：`Wave 4 (Qwen-14B)` 的 `9-run auto-k backfill` 已全部落盘；本模板用于快速填数并产出正式判读。

---

## 1. 快照

- 更新时间：`<YYYY-MM-DD HH:MM CST>`
- 基础 `Wave 4`：`36/36`
- `auto-k backfill`：`9/9`
- 当前总计数：`45`

### 当前 backfill 进度

| Coverage | gov_report | hotpotqa | narrativeqa | 状态 |
|---|---|---|---|---|
| `cov70` | `<score>` | `<score>` | `<score>` | `done` |
| `cov80` | `<score>` | `<score>` | `<score>` | `done` |
| `cov90` | `<score>` | `<score>` | `<score>` | `done` |

---

## 2. 新增 9 条结果表

| Policy | narrativeqa | hotpotqa | gov_report | 3-task mean |
|---|---:|---:|---:|---:|
| `bakv_auto_cov70_max` | `<...>` | `<...>` | `<...>` | `<...>` |
| `bakv_auto_cov80_max` | `<...>` | `<...>` | `<...>` | `<...>` |
| `bakv_auto_cov90_max` | `<...>` | `<...>` | `<...>` | `<...>` |

---

## 3. 当前 14B 三任务平均分位置

将 `Wave 4` 当前主要 policy 的三任务平均分重新排序：

| Rank | Policy | 3-task mean |
|---|---|---:|
| 1 | `<policy>` | `<score>` |
| 2 | `<policy>` | `<score>` |
| 3 | `<policy>` | `<score>` |
| 4 | `bakv_auto_covXX_max` | `<score>` |

要特别对照的旧基线：

- `uniform_int4_k4v4`
- `heuristic_k3`
- `heuristic_k7`
- `uniform_int8_k8v8`
- `bakv_k1`

---

## 4. task-level 位置

### 4.1 `narrativeqa`

- 当前 best：`<policy = score>`
- auto-k 最好：`<policy = score>`
- 判读：`<一句话>`

### 4.2 `hotpotqa`

- 当前 best：`<policy = score>`
- auto-k 最好：`<policy = score>`
- 判读：`<一句话>`

### 4.3 `gov_report`

- 当前 best：`<policy = score>`
- auto-k 最好：`<policy = score>`
- 判读：`<一句话>`

---

## 5. 必答问题

`Wave 4` 已经跑完，现在必须明确回答下面三件事：

1. `auto-k` 在 `14B` 上的总体位置是什么？
   - strongest
   - strong second tier
   - weak / non-competitive

2. `auto-k` 是否延续了 `Wave 1` 那种“强但非最优”的形态？

3. `Wave 4` 的新结果是否继续支持：
   - `heuristic / uniform` 是强 baseline
   - `regime-based interpretation`
   - 而不是 universal allocator law

---

## 6. 推荐判读分叉

### 分支 A：auto-k 进入前列但不登顶

推荐写法：

`Wave 4` 继续支持将 auto-k 写成强竞争力的 profile-aware 扩展，但不支持将其写成 14B 上的最优统一解。当前更稳的叙事仍然是 strong baselines + family-/scale-dependent regimes。

### 分支 B：auto-k 直接进入第一梯队并接近/超过当前最优

推荐写法：

`Wave 4` 将 auto-k 从 Mistral-first positive evidence 进一步扩张为跨 scale 的强扩展证据；但即便如此，若 task-level 仍保留反例，也不应把它写成 universal winner。

### 分支 C：auto-k 表现明显弱于现有强基线

推荐写法：

`Wave 4` 说明 auto-k 的正面证据当前仍主要集中在特定 family / profile 上，从而进一步支持“regime-dependent, not universal”这条主线。

---

## 7. 回写目标

正式填写后，应回写到：

1. `docs/thesis_upgrade_live_plan.md`
2. `docs/mainline_execution_queue.md`
3. 如有必要，再整合进 `docs/phase2_final_readout.md`
