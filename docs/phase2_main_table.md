# Phase 2 编号 6 M3 主表：Layer-wise Allocator MVP（Qwen2.5-1.5B）

kv_mode 固定 `int4_mixed_kv`；5 policy 按 `(task, policy_name)` 区分。所有非 uniform policy avg_bits=4.429（3 层 INT8 + 25 层 INT4）。

| task | metric | Uniform INT4 | Uniform INT8 | BAKV Top-3 | Heuristic-3 | Random-3 (seed42) |
|---|---|---|---|---|---|---|
| gov_report | rouge_l | 5.896 | 9.298 | 8.979 | 9.009 | 6.233 |
| ↳ Δ vs UInt4 |  | (基线) | +57.7% | +52.3% | +52.8% | +5.7% |
| hotpotqa | f1 | 2.421 | 4.969 | 4.637 | 4.653 | 2.958 |
| ↳ Δ vs UInt4 |  | (基线) | +105.2% | +91.5% | +92.2% | +22.2% |
| narrativeqa | f1 | 5.107 | 6.364 | 6.773 | 6.345 | 4.799 |
| ↳ Δ vs UInt4 |  | (基线) | +24.6% | +32.6% | +24.2% | -6.0% |

## M4 硬 Gate 判定（Codex 修改版 v2）

**硬 Gate**：BAKV Top-3 平均分 > Random-3 平均分 **且 ≥2/3 tasks 胜**

- **gov_report**: BAKV=8.979 vs Random=6.233 → BAKV > Random
- **hotpotqa**: BAKV=4.637 vs Random=2.958 → BAKV > Random
- **narrativeqa**: BAKV=6.773 vs Random=4.799 → BAKV > Random

- **平均分**: BAKV=6.796 vs Random=4.663 → **PASS**
- **任务胜率**: BAKV 胜 3/3 tasks → **PASS** (需要 ≥2/3)

### 🟢 M4 硬 Gate PASS → 允许进编号 7（Budget Sweep + 消融）

## 次 Gate 参考（加分项）：BAKV Top-3 > Heuristic Top-3 ?

- **gov_report**: BAKV=8.979 vs Heuristic=9.009 → BAKV ≤ Heuristic
- **hotpotqa**: BAKV=4.637 vs Heuristic=4.653 → BAKV ≤ Heuristic
- **narrativeqa**: BAKV=6.773 vs Heuristic=6.345 → BAKV > Heuristic

- **Heuristic 胜率**: BAKV 胜 1/3 tasks
- **次 Gate 参考**: attention-KL lens 未显著优于位置启发 — 论文需弱化 lens 独占性
