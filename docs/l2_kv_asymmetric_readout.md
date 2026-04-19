# L2 Phase A — K/V Asymmetric Allocator Readout

> **Provenance level**: `exploratory`
> **Run window**: 2026-04-19 05:54 – 06:59 CST
> **Scope**: 3 model × 3 task × 4 policy = 36 runs (all GATE PASS)

---

## 1. 矩阵与 Policy

**Model × Task 矩阵**：
- Model: `1p5b` (L=28, H_kv=2), `7b` (L=28, H_kv=4), `8b` (L=32, H_kv=8)
- Task: `narrativeqa`, `hotpotqa`, `gov_report`

**4 Policy（可对比基准）**：

| Policy | avg_bits | 类别 |
|---|---|---|
| `uniform_int4_k4v4` | 4.00 | 纯 INT4 baseline |
| `bakv_k3` | 4.21-4.4 | fixed top-k behavior-guided |
| `bakv_auto_cov80_max` | 6.14-7.12 | auto-k coverage-driven |
| 🎯 **`kv_asym_avgbits5p0`** | **5.00** | **role-aware K/V asymmetric** |

---

## 2. 完整 metric（avg = mean over 3 core tasks）

### 1.5B (Qwen2.5-1.5B, L=28, H_kv=2)

| Policy | narr | hot | gov | **avg** |
|---|---|---|---|---|
| uniform_int4_k4v4 | 5.11 | 2.42 | 5.90 | 4.47 |
| bakv_k3 | 6.77 | 4.64 | 8.98 | 6.80 |
| bakv_auto_cov80_max | 6.70 | 5.01 | 9.28 | **🥇 7.00** |
| 🎯 **kv_asym_avgbits5p0** | **6.88** | 4.54 | 9.27 | 6.89 |

### 7B (Qwen2.5-7B, L=28, H_kv=4)

| Policy | narr | hot | gov | **avg** |
|---|---|---|---|---|
| uniform_int4_k4v4 | 2.71 | 5.18 | 5.29 | 4.39 |
| bakv_k3 | 7.04 | 4.96 | 8.56 | 6.86 |
| bakv_auto_cov80_max | 7.08 | 5.14 | 8.95 | **🥇 7.06** |
| 🎯 kv_asym_avgbits5p0 | 6.36 | 5.13 | 8.85 | 6.78 |

### 8B (LLaMA-3.1-8B, L=32, H_kv=8)

| Policy | narr | hot | gov | **avg** |
|---|---|---|---|---|
| uniform_int4_k4v4 | 10.24 | 6.73 | 9.24 | 8.74 |
| bakv_k3 | 9.20 | 5.84 | 9.44 | 8.16 |
| bakv_auto_cov80_max | 10.74 | 7.57 | 9.75 | **🥇 9.35** |
| 🎯 kv_asym_avgbits5p0 | 9.90 | 5.98 | 9.57 | 8.48 |

---

## 3. kv_asym 相对位置（Gate A 判读核心）

| Model | kv_asym avg | vs bakv_k3 | vs cov80 (best) | per-task win |
|---|---|---|---|---|
| **1.5B** | 6.89 | **+0.10** ✅ | -0.11 | **narr 独占最高 (6.88)** |
| **7B** | 6.78 | -0.07 | -0.28 | — |
| **8B** | 8.48 | **+0.32** ✅ | -0.87 | — |

---

## 4. 🛑 Gate A 决策：✅ 纳入 Phase B Pareto 默认策略集

### 决策依据（按 plan §3 默认规则：至少 1 model 正增益 OR 解释价值明显）

| 条件 | 命中 |
|---|---|
| ≥1 model 上 kv_asym > bakv_k3 (same-budget class) | ✅ **2/3**（1.5B +0.10, 8B +0.32） |
| 某 task 上 kv_asym 独占最高 | ✅ 1.5B narrativeqa = 6.88 > cov80 6.70 |
| Role-aware 解释价值明显 | ✅ 清晰的 K-only (首层) + V-only (中后层) 分布 |
| Bits 效率潜力 | ✅ 5 bits vs cov80 7+ bits，Pareto 候选 |

### K/V Asymmetric 选层模式（以 1.5B 为例）

```
k_only_layers = [0, 1]                                    # 首 2 层仅升 K
v_only_layers = [7, 10, 14, 17, 18, 21, 22, 23, 24, 25, 26, 27]  # 中后层仅升 V
role_slots = 14
avg_bits = 5.00
```

这符合 Phase 2.6 跨模型发现 "**K 在早层敏感，V 在中后层敏感**" 的 behavior-aligned hypothesis。

---

## 5. 诚实披露（不过度声明）

1. **kv_asym 从未是 avg 最高** — `bakv_auto_cov80_max` 在 3/3 model 上 avg 最高
2. **7B 上轻微负增益**（-0.07 vs bakv_k3）— 不是全模型正增益
3. 对比依赖 **same-budget class**：与 bakv_k3 比有意义（4.2 vs 5 bits），与 cov80 比不公平（5 vs 7 bits）
4. 本轮是 **exploratory**，不作 paper main table 唯一源；Phase 2.6B clean-provenance rerun 覆盖前不入 final claim

### 其他新发现（非 Gate A 核心）

- **8B `uniform_int4` 异常强**（8.74），比 `bakv_k3` (8.16) 高 +0.58 —— 与 Phase 2.6 14B 发现一致（uniform_int4 在某些 model 上强）

---

## 6. 下一步：Phase B Pareto

Gate A 决策**纳入** `kv_asym_avgbits5p0` 作为 Phase B Pareto 默认策略集成员：

- `uniform_int4_k4v4`
- `bakv_k3` (strongest fixed-k same-budget class)
- `bakv_auto_cov80_max` (strongest auto-k)
- 🎯 **`kv_asym_avgbits5p0`** (role-aware candidate)

Phase B 在 7B / 8B / Mistral-7B 上 3 GPU 并行跑，目标：把 Phase A 的 quality-only 排序升级为 **quality-bits Pareto trade-off**。

---

## 7. 签名

- 生成：2026-04-19 07:00 CST
- 数据来源：`results/l2_kv_asymmetric/{1p5b,7b,8b}/{narrativeqa,hotpotqa,gov_report}/longbench_task_summary_*.csv`
- Log 映射：`l2kvasym_<model>_int4mixedkv_<policy>_<task>_n50.log` → CSV
- 聚合工具：inline Python（`aggregate_l2_kv_asymmetric.py` has known CSV-schema bug，见 follow-up）
- Follow-up：修 `aggregate_l2_kv_asymmetric.py` / `aggregate_l2_prompt_adaptive.py` 走 log→CSV 映射（eval_longbench CSV schema 无 `run_name` 列）
