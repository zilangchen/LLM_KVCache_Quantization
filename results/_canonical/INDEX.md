# Results Canonical Index

> **用途**：所有 agent 查找实验数据的**唯一入口**。不要再去 `emnlp_*/` 或 `phase5v2/` 等历史目录考古。
> **最后更新**：2026-04-09
> **来源**：本 INDEX 指向 `emnlp_defense_v1/` 和 `emnlp_rolealign_v2/` 两个当前权威目录。

---

## 快速入口

| 想找什么？ | 去哪 |
|-----------|------|
| Claim X 的证据（按论文叙事） | `by_claim/claimX_*.md` |
| 某类实验的所有数据（按技术分类） | `by_experiment/<type>.md` |
| 某个历史目录还能不能用 | `appendix_freshness.md` |
| 当前会话补跑/消融脚本 | `../../scripts/` |

---

## 当前论文的 5 个 Claim 及其证据

| Claim | 内容 | 证据文件 | 主要数据路径 |
|-------|------|---------|------------|
| **C1** | INT8 行为对齐校准有效性 | [claim1_int8_validated.md](by_claim/claim1_int8_validated.md) | `emnlp_defense_v1/runs/ppl_int8_n10_*` |
| **C2** | 诊断透镜定位 INT4 失效根因（Key 主导） | [claim2_diagnostic_lens.md](by_claim/claim2_diagnostic_lens.md) | `emnlp_defense_v1/runs/ppl_ablation_k*_v*` |
| **C3** | INT4-RoleAlign 检索恢复（Needle 100%） | [claim3_int4_rolealign.md](by_claim/claim3_int4_rolealign.md) | `emnlp_rolealign_v2/runs/ppl_ours_asym_*` |
| **C4** | PPL + 延迟能力边界（诚实边界） | [claim4_boundary.md](by_claim/claim4_boundary.md) | `emnlp_defense_v1/runs/tpot_*` |
| **C5** | 温度校正 × GQA scale-dependent（意外发现） | [claim5_invtau_gqa.md](by_claim/claim5_invtau_gqa.md) | `emnlp_defense_v1/runs/tau_ablation_*` + `tau_full_ra_*` |

---

## 9 类实验数据入口

| 类别 | 入口文件 | 说明 |
|------|---------|------|
| PPL 实验 | [ppl.md](by_experiment/ppl.md) | 主表 + n=10 seeds + cs sweep + K/V ablation |
| Needle 检索 | [needle.md](by_experiment/needle.md) | 4K-32K × 3 模型 × n=10 seeds |
| RULER | [ruler.md](by_experiment/ruler.md) | NIAH/VT/CWE/QA 分任务分长度 |
| LongBench | [longbench.md](by_experiment/longbench.md) | synthetic + official v2 (EVL-042 fix) |
| TPOT profiling | [tpot_latency.md](by_experiment/tpot_latency.md) | 独占 GPU 测量，3 模型 × 4 modes |
| Memory / Batch | [memory.md](by_experiment/memory.md) | KV 压缩率 + batch sweep (Exp-9) |
| Calibration | [calibration.md](by_experiment/calibration.md) | KL v3/v5 + b10 灵敏度 + Exp-2 |
| K/V ablation | [kv_ablation.md](by_experiment/kv_ablation.md) | MixedKV 4 配置（Exp-11）|
| inv_tau ablation | [invtau_ablation.md](by_experiment/invtau_ablation.md) | Claim 5 证据，3 模型 × tau on/off |

---

## 实验目录健康状态

| 目录 | 状态 | 规模 | 说明 |
|------|------|------|------|
| `emnlp_defense_v1/` | 🟢 **活跃** | 176 runs, 289 CSVs | **当前最新**（答辩补强，论文主表） |
| `emnlp_rolealign_v2/` | 🟢 **冻结权威** | 171 runs, 373 CSVs | RoleAlign 主数据，2026-04-02 冻结 |
| `emnlp_rolealign_v4/` | 🟡 部分 | 3 runs, 194 CSVs | T3 1.5B 重跑部分完成 |
| `emnlp_expansion_v1/` | 🟡 早期 | 3 runs, 374 CSVs | K/V 消融 + b10 校准（Claim 2 支撑） |
| `emnlp_final_raw/` | ⚫ 归档 | 10 dirs, 8677 CSVs | Phase 5v2/6 legacy，不要用 |
| `phase5v2*/`, `final_*/`, `week5_*/` | ⚫ 归档 | — | 早期探索，已被替代 |

**完整的 25 目录列表见 `appendix_freshness.md`**

---

## 常见查询示例

### "1.5B INT8 的 PPL 是多少？"
→ `by_experiment/ppl.md` 第 1 行
→ 答：**9.34** (n=10 seeds, bitwise 一致)

### "INT4-RA 在 8B 上的 Needle 分数？"
→ `by_claim/claim3_int4_rolealign.md`
→ 答：**100%** (3 seeds @ 4K-32K)

### "inv_tau 效应为什么 scale-dependent？"
→ `by_claim/claim5_invtau_gqa.md`
→ 答：1.5B (H_kv=2) **-1.6%**；7B (H_kv=4) **+6.0%**；8B (H_kv=8) **+3.4%**

### "TPOT 为什么 ch4 有两个数字？"
→ `by_experiment/tpot_latency.md`
→ 答：47.14 ms (seq_len=32K) vs 44.84 ms (seq_len=4K)，两者都对

### "KIVI residual buffer 的影响？"
→ `by_experiment/ppl.md`
→ 答：**零影响** — res=0/64/128 三配置 PPL 均为 **10.43**

---

## 数据更新规则

**维护者须知**：
1. **任何新实验完成后**必须更新本 INDEX + 对应的 `by_claim/` 和 `by_experiment/` 文件
2. **不要修改**原始 `emnlp_*/` 目录的 CSV（只能追加）
3. **标记过时数据**：如果某个数据被新版本替代，在原行尾加 `⚠️ 已被 X 替代`
4. **活跃度变更**：目录从活跃降级为归档时，必须先把数据迁移记录在 `appendix_freshness.md`
