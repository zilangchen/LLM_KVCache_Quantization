# 历史目录活跃度清单

> 25 个 `results/` 子目录的完整状态。新 agent 查找数据时参考此表决定"能不能用"。
> **简要规则**：🟢 活跃（论文引用）→ 🟡 部分（不完整或已被替代）→ ⚫ 归档（完全废弃）

---

## 目录完整清单

| 目录 | 状态 | 规模 | 最新修改 | 是否论文引用 | 说明 |
|------|------|------|---------|-------------|------|
| `emnlp_defense_v1` | 🟢 活跃 | 176 runs, 289 CSV | 2026-04-04 | ✅ 主表 | **当前最新**（答辩补强） |
| `emnlp_rolealign_v2` | 🟢 冻结权威 | 171 runs, 373 CSV | 2026-04-02 | ✅ 主表 | RoleAlign 冻结权威，PPL/RULER/Latency/Memory |
| `emnlp_rolealign_v4` | 🟡 部分 | 3 runs, 194 CSV | 2026-04-03 | ❌ | T3 1.5B 重跑部分完成 |
| `emnlp_expansion_v1` | 🟡 部分 | 3 runs, 374 CSV | 2026-03-20 | ✅ 支表 | K/V 消融 + b10 校准（Claim 2 支撑） |
| `final_thesis_plus_wk3_20260221_225815` | 🟡 参考 | 341 CSV | 2026-02-22 | ❌ | Week 3 快照，历史参考 |
| `emnlp_final_raw` | ⚫ 归档 | 2136 dirs, 8677 CSV | 2026-03-25 | ❌ | Phase 5v2/6 legacy，**不要用** |
| `final_journal_v1` | ⚫ 归档 | 593 CSV | 2026-02-22 | ❌ | 早期日志，已替代 |
| `emnlp_postfix_v2` | ⚫ 归档 | 854 CSV | 2026-03-19 | ❌ | 后处理 v2，已集成 |
| `phase5v2_remote_backup` | ⚫ 归档 | 7340 CSV | 2026-03-10 | ❌ | Phase 5 远端备份 |
| `emnlp_postfix_v1` | ⚫ 归档 | 84 CSV | 2026-03-17 | ❌ | 早期后处理 |
| `final_journal_v2` | ⚫ 归档 | 58 CSV | 2026-03-11 | ❌ | 日志 v2 |
| `final_thesis_20260214_094156` | ⚫ 归档 | 135 CSV | 2026-02-14 | ❌ | 论文初稿快照 |
| `final_thesis_plus_20260219_045623` | ⚫ 归档 | 254 CSV | 2026-02-22 | ❌ | 论文 v1.1 |
| `emnlp_c6_fix` | ⚫ 归档 | 14 CSV | 2026-03-19 | ❌ | C6 bug 修复版 |
| `emnlp_final_merged` | ⚫ 归档 | 2 CSV | 2026-03-18 | ❌ | 早期合并尝试 |
| `emnlp_rolealign_v1` | ⚫ 归档 | 17 CSV | 2026-03-25 | ❌ | RoleAlign v1（被 v2 替代） |
| `int4_fused_round_20260219_0315` | ⚫ 归档 | 33 CSV | 2026-02-19 | ❌ | INT4 融合探索 |
| `int4_t2_float32_v1` | ⚫ 归档 | 23 CSV | 2026-03-12 | ❌ | INT4 T2 探索 |
| `phase5v2` | ⚫ 归档 | 54 CSV | 2026-03-25 | ❌ | Phase 5 v2 |
| `phase6_kivi` | ⚫ 归档 | 64 CSV | 2026-03-17 | ❌ | Phase 6 KIVI 实验 |
| `attention_kl` | ⚫ 空 | 0 CSV | 2026-03-20 | ❌ | 空目录（早期 attention KL 分析） |
| `calib_plots` | ⚫ 空 | 0 CSV | 2026-02-21 | ❌ | 空目录（校准绘图产物） |
| `paper_tables` | ⚫ 归档 | 13 CSV | 2026-03-23 | ❌ | 论文表格中间文件 |
| `plots` | ⚫ 空 | 0 CSV | 2026-03-20 | ❌ | 空目录 |
| `week5_smoke_remote_r2` | ⚫ 归档 | 20 CSV | 2026-02-22 | ❌ | Week 5 烟测 |

---

## 使用规则

### 🟢 活跃目录（可直接使用）
1. **首选**：`emnlp_defense_v1/` — 所有新补跑和答辩补强的数据
2. **次选**：`emnlp_rolealign_v2/` — RoleAlign 冻结权威数据
3. **支撑**：`emnlp_expansion_v1/` — K/V 消融和 b10 校准

### 🟡 部分目录（小心使用）
- `emnlp_rolealign_v4/`: T3 1.5B 重跑，只有少量 runs，**不要依赖**
- 其他 🟡 仅作历史参考

### ⚫ 归档目录（禁止使用）
- 所有 ⚫ 目录都已被替代，不应在论文中引用
- 如果 agent 误用这些目录的数据，必须**停止并报告**
- 删除的数据可以从归档目录恢复（但不要删）

---

## 归档原因快速查询

| 类别 | 归档目录 | 为什么不要用 |
|------|---------|-------------|
| **总分 bug** | `emnlp_postfix_v*`、`phase5v*` | EVL-042 修复前的数据，总分偏低 |
| **RoPE 缺失** | `emnlp_rolealign_v1` | v1 校准缺 input_layernorm + RoPE |
| **CWE bug** | 所有 < 2026-03-17 | EVL-047 修复前，CWE 子任务 0% |
| **早期探索** | `week5_*`、`int4_*round*`、`final_thesis_*` | 非完整实验，仅探索 |
| **中间产物** | `paper_tables`、`plots`、`calib_plots` | 非 raw CSV，是后处理结果 |

---

## 总体统计

- **活跃**：2 目录（447 runs, 662 CSVs）
- **部分**：3 目录（6 runs, 909 CSVs）
- **归档**：20 目录（大量 CSVs，不使用）

**活跃数据规模**：`emnlp_defense_v1` + `emnlp_rolealign_v2` 共 **~1100 CSV**，覆盖论文所有 5 个 Claim。这是答辩时的**全部证据库**。
