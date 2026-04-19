# 当前可用数据资产总览 + 价值判读（2026-04-20）

**日期**：2026-04-20
**作者**：Claude（基于 Codex 2026-04-20 结构层底账 + 实地核实 + 价值判读扩展）
**文档身份**：论文升级阶段的**数据 source-of-truth**

---

## 0. 文档用途

这份文档固化当前仓库中**可直接讨论的数据结构版图**，并承接"这些数据意味着什么"的价值层判读。

### 它承担什么

- **Part A**（结构层底账）：数据目录结构与规模记录——路径、文件数、目录组成
- **Part B**（价值判读）：每个数据族在新故事里撑起什么结论、撑不起什么结论
- **Part C**（核实 + 判断）：Codex 判断核实汇总 + 五级价值金字塔 + 风险提示
- **Part D**（使用建议）：论文改写顺序 + 文档使用纪律

### 它不承担什么

- 叙事主线 / 故事线 → 见 `docs/thesis_story_20260420.md`
- 什么能写 / 不能写的口径 → 见 `docs/freeze_20260419.md`
- 运行时论文升级计划 → 见 `docs/thesis_upgrade_live_plan.md`
- 实验队列状态 → 见 `docs/mainline_execution_queue.md`

### 阅读顺序建议

接手人先读 `thesis_story_20260420.md`（叙事主线）→ 本文 Part B（价值判读）→ 需要查具体路径或文件数量时再回 Part A（结构层底账）。

### 维护规则

**只 append，不 rewrite**。新发现或新核实在 Part C 末尾 append 修订记录，不改 Part A / Part B 的既定分层。

---

# Part A. 结构层底账（目录分布 + 文件规模）

> 本部分记录每个数据目录的路径、文件数、规模、结构。写 thesis 引用具体数据时回来查。
> 原始底账由 Codex 2026-04-20 创建，本次扩展仅做实地核实与补充。

## A.1 全局总表：当前本地可见的数据族

| 层级 | 数据族 | 本地路径 | 可用 | 规模 | 结构作用 | 备注 |
|---|---|---|---|---:|---|---|
| 冻结真源层 | Freeze 文档 | `docs/freeze_20260419.md` | 是 | 1 md | 定义 freeze scope | 只管权威边界，不含 raw 数值表 |
| 冻结真源层 | Clean rerun readout | `docs/clean_rerun_20260419T09/` | 是 | 5 md | clean-provenance 的 readout、manifest、completion report | 当前最重要的判读入口之一 |
| 冻结真源层 | 论文 live status | `docs/thesis_upgrade_live_plan.md` | 是 | 1 md (51.5K) | 当前论文主线、结果升降级、frozen 状态 | 是工作台，不是 raw data |
| 冻结真源层 | 叙事主线 | `docs/thesis_story_20260420.md` | 是 | 1 md | 论文升级后的 7 段故事主线 | **本次新增，见 §0** |
| 当前核心结果层 | clean rerun raw + summary | `results/clean_rerun_20260419T09/` | 是 | 464 files / 280 CSV | clean-provenance 结果主仓 | 当前最关键的核心结果层 |
| 扩展实验层 | L2 Phase A | `results/l2_kv_asymmetric/` | 是 | 180 files / 108 CSV | K/V asymmetric 扩展实验 | exploratory positive branch |
| 扩展实验层 | L2 Phase B | `results/l2_pareto/` | 是 | 710 files / 335 CSV / 32 JSON | Pareto v4 扩展实验 | 含 raw、汇总表、quarantine |
| 扩展实验层 | L2 Phase C | `results/l2_prompt_adaptive/` | 是 | 240 files / 135 CSV / 15 JSON | Prompt-adaptive 扩展实验 | 8B official + 1.5B/7B off-protocol |
| 本地验证层 | phase1 official | `results/phase1_official/` | 是 | 48 files | 早期官方 bundle | 更像历史 official 本地包 |
| 本地验证层 | phase1 official v2 | `results/phase1_official_v2/` | 是 | 18 files | phase1 补跑 / patch 包 | 较小 |
| 本地验证层 | phase2 c1 local | `results/phase2_c1_local/` | 是 | 2 files | 本地 gate / summary | 极简本地验证层 |
| 本地验证层 | phase2 c2 local | `results/phase2_c2_local/` | 是 | 5-7 files | 本地 gate / verify | 非当前主结果层 |
| 本地验证层 | phase2 c2b local | `results/phase2_c2b_local/` | 是 | **87 files (2.1M)** | **7B supporting regime（aggregation-split）诊断源** | **Codex 遗漏的重要层，见 B.7** |
| 本地验证层 | phase2 diag local | `results/phase2_diag_local/` | 是 | 18 CSV | 诊断型本地结果 | 小型诊断层 |
| 配置产物层 | clean rerun artifacts | `artifacts/clean_rerun_20260419T09/` | 是 | 73 JSON | clean rerun 对应 calibration / policy artifacts | 不是结果表 |
| 配置产物层 | allocator artifacts | `artifacts/allocator/` | 是 | 143 JSON | allocator sweep / l2 policy JSON | 配置与策略层 |
| 配置产物层 | calibration artifacts | `artifacts/calibration/`, `artifacts/calibration_postfix_v1/` | 是 | 8 files | 校准统计和静态产物 | 非主结果层 |
| 历史打包层 | old final package | `results/final/` | 是 | 3231 files, **250M** | 旧版 final data + final scripts | 旧打包层，不是当前 frozen 真源 |
| 历史打包层 | old canonical index | `results/_canonical/` | 是 | 17 md | 旧 canonical 索引层 | 已被更新版替代 |
| 历史打包层 | archive | `results/archive/` | 是 | 58642 files, **2.7G** | 历史轮次归档 | 本地磁盘最大占用 |

**注**：`results/phase1_smoke/` 在 Codex 2026-04-20 外部评估中被列入，但实地核实**不存在**。已从本表删除。

## A.2 当前真正应优先围绕的核心结果层

如果只关心当前论文升级最相关、最值得继续讨论的数据结构，应优先看这四组：

1. `results/clean_rerun_20260419T09/`
2. `results/l2_kv_asymmetric/`
3. `results/l2_pareto/`
4. `results/l2_prompt_adaptive/`

下面分别说明其结构。

## A.3 Clean Rerun：当前最核心的 clean-provenance 结果层

**路径**：`results/clean_rerun_20260419T09/` + `docs/clean_rerun_20260419T09/`

### A.3.1 组成

| 组件 | 路径 | 结构 |
|---|---|---|
| 汇总表 | `summary_phase1.csv`, `summary_final.csv` | 顶层 aggregate summary (92 rows 合计) |
| raw step1 | `raw/step1_canonical/1p5b/` | canonical 路径 |
| raw step2 | `raw/step2_compare/{14b,3b,8b,mistral7b}/` | compare 层 |
| raw step3 | `raw/step3_extend/{14b,3b,8b,mistral7b}/` | extend 层 |
| readout | `docs/clean_rerun_20260419T09/*.md` | 5 md：MANIFEST + overnight_report + completion_report + readout_phase1 + readout_final |

### A.3.2 结构理解

完整的 clean-provenance 结果包：raw 结果 + 聚合 summary + readout / completion / manifest 文档。

后续如果要讨论"当前 frozen 主支撑数据在哪里"，这一层是第一优先级。

### A.3.3 Provenance 硬事实（来自 MANIFEST.md）

- pin: `ddada195dcf3bbd205b627fab154ecb013f11c1c`
- branch: `codex/phase2-a-rerun`
- 9 个关键运行时文件 MD5 全部记录
- 3 个 calibration（3B / 14B / Mistral-7B）的 md5 + config + timestamp + 来源 ledger 完整

## A.4 L2 Phase A：K/V Asymmetric 扩展层

**路径**：`results/l2_kv_asymmetric/`

### A.4.1 顶层结构

```text
results/l2_kv_asymmetric/
  ├── 1p5b/
  ├── 7b/
  └── 8b/
```

每个模型下都包含 3 个 task：`gov_report` / `hotpotqa` / `narrativeqa`。

### A.4.2 叶子目录内容

每个 `<model>/<task>/` 下：
- 4 个 policy 对应的 `.log`
- 4 个 `longbench_details_*.csv`
- 4 个 `longbench_task_summary_*.csv`
- 4 个 `profile_longbench_*.csv`

### A.4.3 结构维度

| 维度 | 内容 |
|---|---|
| 模型 | `1p5b`, `7b`, `8b` |
| 任务 | `gov_report`, `hotpotqa`, `narrativeqa` |
| policy | `uniform_int4_k4v4`, `kv_asym_avgbits5p0`, `bakv_k3`, `bakv_auto_cov80_max` |

标准 **3 × 3 × 4** 结果结构。

## A.5 L2 Phase B：Pareto v4 扩展层

**路径**：`results/l2_pareto/`

### A.5.1 顶层组成

| 组件 | 路径 | 作用 |
|---|---|---|
| Pareto 汇总表 | `pareto_front_v4.csv`, `pareto_plot_v4.csv`, `pareto_table_v4.csv` | 顶层聚合 |
| raw results | `raw/` | 每个模型每个 policy 的质量/性能结果 |
| quarantine | `_quarantine_v3_20260419T0857/`, `quarantine_20260419T080547/` | 隔离区 |

### A.5.2 raw 结构

```text
results/l2_pareto/raw/
  ├── 7b/        (bakv_auto_cov80_max / bakv_k3 / heuristic_k3 / uniform_int4_k4v4)
  ├── 8b/        (bakv_auto_cov80_max / bakv_k11 / heuristic_k11 / uniform_int4_k4v4)
  └── mistral7b/ (bakv_auto_cov80_max / bakv_k3 / heuristic_k3 / uniform_int4_k4v4)
```

### A.5.3 每个 `<model>/<policy>/` 叶子目录的典型内容

- 3 个 task 的 quality 结果
- `latency` / `memory` / `needle` / `ppl`
- 常见 `manifest.json`

所以这一层是 **质量 + 成本联合结构层**，不是单纯的 longbench 结果层。

## A.6 L2 Phase C：Prompt-adaptive 扩展层

**路径**：`results/l2_prompt_adaptive/`

### A.6.1 顶层结构

```text
results/l2_prompt_adaptive/
  ├── 1p5b/       (off-protocol exploratory)
  ├── 7b/         (off-protocol exploratory)
  └── 8b/         (official protocol)
```

每个模型下包含 5 个 task：`narrativeqa` / `hotpotqa` / `gov_report` / `dureader` / `lcc`。

### A.6.2 叶子目录内容

每个 `<model>/<task>/` 下：
- 3 个 variant 的 `.log`：`global_fixed_k` / `global_auto_k` / `prompt_adaptive`
- 3 个 `longbench_details_*.csv`
- 3 个 `longbench_task_summary_*.csv`
- 3 个 `profile_longbench_*.csv`
- 1 个 `prompt_selector_resolution.json`

### A.6.3 结构维度

| 维度 | 内容 |
|---|---|
| 模型 | `1p5b`, `7b`, `8b` |
| 任务 | `narrativeqa`, `hotpotqa`, `gov_report`, `dureader`, `lcc` |
| variant | `fixed_k`, `auto_k`, `prompt_adaptive` |
| 附加对象 | `prompt_selector_resolution.json` |

完整 **3 × 5 × 3** 结果层。但从 frozen protocol：
- `8b × 5 tasks` 是 official structure（Gate C 的唯一合法读数源）
- `1p5b / 7b` 是本地保留的 off-protocol exploratory（不进 Gate C verdict）

## A.7 本地验证 / 诊断层

这些目录也在本地，但更像历史 bundle / 本地 gate / 本地 verify / 小规模诊断，而不是当前 frozen 主心脏结果层。

| 数据族 | 路径 | 结构 | 用途 |
|---|---|---|---|
| phase1 official | `results/phase1_official/` | 多个 timestamped run 目录；目录内有 `config_snapshot.yaml`；CSV 分布于顶层 | 早期官方 bundle |
| phase1 official v2 | `results/phase1_official_v2/` | 小规模 rerun / patch 结构 | 辅助补跑层 |
| phase2 c1 local | `results/phase2_c1_local/` | `summary + gate log` | 本地 gate |
| phase2 c2 local | `results/phase2_c2_local/` | `summary / verify / gate / raw 子目录` | 本地 verify |
| phase2 c2b local | `results/phase2_c2b_local/` | **flat CSV + log，87 files / 2.1M** | **7B aggregation-split 诊断主源，进正文需引用（见 B.7）** |
| phase2 diag local | `results/phase2_diag_local/` | 多个诊断 CSV | 小型诊断层 |

## A.8 配置与策略产物层：`artifacts/`

这一层回答的是"当时用了哪些 calibration / policy / allocator 配置"，不是"最终分数是多少"。

### A.8.1 全局表

| 数据族 | 路径 | 规模 | 内容类型 | 不是啥 |
|---|---|---:|---|---|
| allocator artifacts | `artifacts/allocator/` | 143 JSON | sweep policy / model-specific policy / l2 policy | 不是最终 metric 表 |
| clean rerun artifacts | `artifacts/clean_rerun_20260419T09/` | 73 JSON | clean rerun 对应 calib + policy JSON | 不是结果读数 |
| adaptive policies | `artifacts/adaptive_policies/` | 4 JSON | adaptive policy 原型 | 不是主结果层 |
| calibration | `artifacts/calibration/` | 3 files | calibration stats / config / profile 图 | 不是论文主表 |
| calibration postfix | `artifacts/calibration_postfix_v1/` | 5 JSON | 静态校准产物 | 不是 metrics |

### A.8.2 `artifacts/allocator/` 的内部结构

本地可见子类：`ablation_sens` / `l2_kv_asymmetric` / `l2_prompt_adaptive` / `sweep` / `sweep_14b` / `sweep_3b` / `sweep_7b` / `sweep_8b` / `sweep_mistral7b`。

本质上是 **策略搜索空间 / policy JSON / allocator 产物层**。

## A.9 历史打包 / 归档层

| 数据族 | 路径 | 大小 | 当前定位 |
|---|---|---|---|
| old final package | `results/final/` | 250M | 旧版 final 数据打包层 |
| old canonical index | `results/_canonical/` | 112K | 旧版 canonical 索引层 |
| archive | `results/archive/` | **2.7G** | 历史轮次归档层 |

### A.9.1 结构上的关键提醒

- `results/_canonical/INDEX.md` 已明确说明是旧 canonical index
- `results/final/README.md` 与 `results/final/final_data/INDEX.md` 对应旧 final package
- `results/archive/` 是历史轮次结果归档

这些目录对"历史追溯"有用，但**不应被当作当前 2026-04-19 frozen 主线的唯一真源**。

## A.10 当前数据结构地图

```text
A. 冻结真源 / 判读层
   docs/freeze_20260419.md
   docs/clean_rerun_20260419T09/*.md
   docs/thesis_upgrade_live_plan.md
   docs/thesis_story_20260420.md  ← 叙事主线（分离）

B. 当前核心结果层
   results/clean_rerun_20260419T09/
     ├─ summary_phase1.csv
     ├─ summary_final.csv
     └─ raw/
        ├─ step1_canonical/1p5b/
        ├─ step2_compare/{14b,3b,8b,mistral7b}/
        └─ step3_extend/{14b,3b,8b,mistral7b}/

C. 扩展实验层（L2）
   results/l2_kv_asymmetric/
     └─ {1p5b,7b,8b}/{gov_report,hotpotqa,narrativeqa}/...
   results/l2_pareto/
     ├─ pareto_*_v4.csv
     └─ raw/{7b,8b,mistral7b}/{policy}/...
   results/l2_prompt_adaptive/
     └─ {1p5b,7b,8b}/{5 tasks}/...

D. 本地验证 / 诊断层
   results/phase1_official*
   results/phase2_*_local

E. 配置 / 策略产物层
   artifacts/allocator/
   artifacts/clean_rerun_20260419T09/
   artifacts/calibration*

F. 历史打包 / 归档层
   results/final/
   results/_canonical/
   results/archive/
```

---

# Part B. 数据资产价值判读（角色层 + 价值层）

本部分承接 Part A 的结构底账。每个数据族除了路径和规模，还要回答：**它在新故事（`docs/thesis_story_20260420.md`）里扮演什么角色，撑起哪些结论，撑不起哪些结论。**

## B.1 核心主证据：Clean-Provenance Canonical（Level 5）⭐⭐⭐

**路径**：`results/clean_rerun_20260419T09/` + `docs/clean_rerun_20260419T09/` + `artifacts/clean_rerun_20260419T09/`

**它在故事里的角色**：**整篇论文的主骨架**。对应故事 §2（INT8 canonical）、§3.2（regime 地图）、§5（模型角色分工 4 个模型）全部的主证据来源。

**它撑起的 5 条 final-ready claim**：

| # | Claim | 来源 Step |
|---|---|---|
| 1 | INT8 canonical path fidelity（int8↔fp16 Δ=+0.02） | Step 1 P1 PASS |
| 2 | Mistral-specific auto-k win（cov80=14.76 跨 core+extend task）| Step 2+3 |
| 3 | 3B early-layer rescue regime（首层保护关键，中层 heuristic 灾难）| Step 2 P2 PASS |
| 4 | 14B top-tier but no stable winner（多策略进 top，无单一赢家）| Step 2 |
| 5 | Heuristic is a strong baseline（需被正面承认）| Step 2+3 综合 |

**它撑不起的**：Prompt-adaptive 成立 / 任何跨 family 的 universal winner 主张 / 7B supporting regime（需补 B.7）。

## B.2 第一层历史验证：Phase 1 Official（Level 3）⭐⭐

**路径**：`results/phase1_official/`（48 files, 36 CSV）+ `results/phase1_official_v2/`（18 files, 9 CSV）

**它在故事里的角色**：对应故事 §2（第一层 calibration）的历史验证层——它不是 frozen final claim 的主源头，但它证明了 behavior 原则从 Phase 1 就已经落到 INT8 和 INT4 上跑通过。**保证 clean_rerun 的 5 claim 不是横空出世。**

**它撑起的**：叙事起点——"behavior-guided calibration 这条线是真正被跑出来过的"。

**它撑不起的**：最终 claim（已被 clean_rerun 的 immutable canonical 取代）。

## B.3 第二层扩展证据（核心）：L2 Phase B Pareto（Level 4）⭐⭐⭐

**路径**：`results/l2_pareto/`（710 files, 335 CSV + pareto_*_v4.csv 聚合表, 12/12 policies PASS）

**它在故事里的角色**：对应故事 §3.4（L2 Phase B 嵌入，Pareto 评估维度升级）——**这是 L2 里唯一可以直接进正文主图区的段**。

**它同时撑起**：
- allocator 问题真实性（7B uniform_int4 崩坏的可视化证据）
- AutoK 正面信号（Mistral 进 top tier 的 Pareto 位置）
- heuristic 强基线地位（heuristic 在多数 Pareto 点与 BAKV 接近）

**它撑不起的**：prompt-level routing / K/V asym 超越 auto-k。

## B.4 第二层扩展证据（次级）：L2 Phase A K/V Asymmetric（Level 3）⭐

**路径**：`results/l2_kv_asymmetric/`（180 files, 108 CSV）

**它在故事里的角色**：对应故事 §3.3（L2 Phase A 嵌入，role-aware 粒度扩展）。

**它撑起的**：框架可延伸到更细粒度（role-aware）+ Gate A PASS 验证这条路通。

**它撑不起的**：role-aware 更优 / kv_asym 胜出。当前调参水平下它没有超越 strongest auto-k，需写为"可行方向但未熟"。

## B.5 第三层开放方向（官方）：L2 Prompt-adaptive 8B（Level 3）⭐

**路径**：`results/l2_prompt_adaptive/8b/`（15 runs official protocol）

**官方数据点**（来自 completion_report B 节）：

| Task | fixed-k | auto-k | prompt-adaptive | task best |
|---|---:|---:|---:|---|
| narrativeqa | 9.7318 | **10.7736** | 9.7318 | auto_k |
| hotpotqa | **8.1554** | 7.9186 | 7.9186 | fixed_k |
| gov_report | 9.4779 | **9.7230** | 9.7230 | auto_k (tie prompt) |
| dureader | **12.1569** | 9.8968 | 9.8968 | fixed_k |
| lcc | 10.6142 | 10.9558 | **11.3564** | prompt_adaptive |
| **Mean** | **10.027** | 9.854 | 9.725 | — |

**Gate C Verdict**：Weak / Mixed — prompt_adaptive mean 输 fixed_k -0.30；3/5 错选 fallback / 1/5 tie / 1/5 独立 win（lcc, +0.40 over auto_k）。

**它在故事里的角色**：对应故事 §4.3（L2 Phase C 嵌入）+ §6（future work）。

**它撑起的**：Prompt-adaptive 方向存在局部信号（lcc）+ 当前实现仍是 task-bucket fallback。

**它撑不起的**：per-prompt routing 成立（数据明确不支持，**不能写成 final claim**）。

## B.6 第三层开放方向（off-protocol）：L2 Prompt-adaptive 1.5B / 7B（Level 2）

**路径**：`results/l2_prompt_adaptive/1p5b/` + `/7b/`（各 15 runs off-protocol）

**观察**（exploratory only, non-authoritative, completion_report Q4）：
- 1p5b / 7b 上 auto_k 整体 mean 最高（与 8b 上 fixed_k 胜不同）
- 3 model 上 prompt_adaptive 都不是 best mean（仅 8b/lcc 独立 win）

**它在故事里的角色**：只进 appendix / future-work seed。**MUST NOT be written as official Gate C evidence**（completion_report Q4 明确规定）。

## B.7 辅助诊断（Codex 遗漏）：Phase 2 c2b / diag Local（Level 2）⭐

**路径**：`results/phase2_c2b_local/`（87 files, 2.1M）+ `results/phase2_diag_local/`（18 files）+ `results/phase2_c1_local/` + `results/phase2_c2_local/`

**它在故事里的角色**：**7B supporting regime case（aggregation-split）的主数据源**。对应故事 §5.5 的 7B 角色——它不进主表，但它是证明 "7B 上 k=1 偏 mean、k=5 偏 max" 的原始诊断数据。

**Codex 在 12 段判断里遗漏的一层**：Codex 只用"帮你确认结构，不负责主张"一句带过，但 `phase2_c2b_local`（87 files, 2.1M）实际上是 7B supporting regime 论证的直接证据。

**建议**：Ch4 §5 写到 7B aggregation-split 时必须引用这里的数据；附录 / Methods 层需要说明来源。

## B.8 Provenance 层：Artifacts（Level 1）⭐⭐

**路径**：
- `artifacts/allocator/`（143 JSON + 9 sweep 子目录）
- `artifacts/clean_rerun_20260419T09/`（73 JSON）
- `artifacts/kv_calib_*.json`（26 总计，含 1.5B v2 / 7B / 8B / 3B / 14B / Mistral）

**它在故事里的角色**：**论文结论不靠它，论文可信度离不开它。** 对应 Methods 章的方法可追溯性 + Reproducibility 附录。

**它撑起的**：方法过程可审计；每次 policy 生成与 calibration 产出都有 JSON + md5 可核。

## B.9 历史对照（严管）：final / _canonical / archive（Level 1）⚠️

**路径 + 体量**：
- `results/final/` 250M
- `results/_canonical/` 112K
- `results/archive/` **2.7G**（本地磁盘最大占用）

**它在故事里的角色**：叙事对照价值 + 防回滑参考，**不进正文**。

**风险提示**：
- `.gitignore` 已覆盖 `results/*`，git 上不会跟踪
- 但本地磁盘 2.7G + 250M 是显著占用
- **建议**：6 个月内归档到 cold storage，保留 `results/_canonical/INDEX.md` 指针即可

## B.10 战略文档：docs/ 下的主线口径（Level 5, 非数据但关键）⭐⭐

| 文档 | 大小 | 角色 |
|---|---|---|
| `docs/thesis_story_20260420.md` | — | **叙事主线（本次分离）** |
| `docs/freeze_20260419.md` | 3.3K | 口径控制入口（什么能写/不能写） |
| `docs/thesis_upgrade_live_plan.md` | 51.5K | 运行时论文升级计划 |
| `docs/mainline_execution_queue.md` | 14.9K | 实验队列状态（当前：已清空，进入论文写作） |
| `docs/clean_rerun_20260419T09/MANIFEST.md` | 5.8K | Clean-rerun provenance ledger |
| `docs/clean_rerun_20260419T09/completion_report_20260419.md` | 8K | Overnight 完成报告（5 questions verdict） |
| `docs/clean_rerun_20260419T09/overnight_report_20260419.md` | 16.5K | 详细执行记录 |
| `docs/clean_rerun_20260419T09/readout_{phase1,final}.md` | 1K+3K | Gate P1/P2/P3 读出 |

**它在故事里的角色**：**source-of-truth 层**，防止 Claude / 未来接手人在重写论文时回滚到旧叙事。

---

# Part C. Codex 判断核实 + 我的总体判断

## C.1 Codex 12 段判断核实汇总

| Codex 段 | 核心判断 | 核实结果 |
|---|---|---|
| §1 全局价值表 | 10 类数据的角色分工 | ✅ 正确（`phase2_*_local` 需补充为独立类，见 B.7）|
| §2 clean_rerun 是主骨架 | "整篇论文终于可以站住的主证据层" | ✅ **完全正确**，MANIFEST 硬事实支撑 |
| §3 phase1 是历史起点 | "给第一层原则提供历史与方法起点" | ✅ 正确，`phase1_smoke` 需从清单删除（不存在）|
| §4 phase1 + clean step1 合成 | "共同支撑 behavior 作为静态校准原则" | ✅ 正确 |
| §5 l2_kv_asymmetric 价值 | "框架可扩展性价值，非最终主张价值" | ✅ 正确 |
| §6 l2_pareto 结构价值 | "从 winner story 转向 regime story 的最强支撑" | ✅ **完全正确，且是 Codex 全篇最准确的一段** |
| §7 l2_prompt_adaptive 边界 | "清楚地画出了边界，不是胜利证据" | ✅ 正确（8B 官方 weak/mixed；1p5b/7b off-protocol）|
| §8 模型角色值钱点 | Mistral / 3B / 14B / 7B 各自角色 | ✅ 正确，与故事 §5 对齐 |
| §9 artifacts 价值 | "结论不靠它，可信度离不开它" | ✅ 正确 |
| §10 final/_canonical/archive | "叙事对照价值" | ⚠️ 定性正确，体量（2.7G+250M）被低估，需加磁盘管理提示（见 B.9）|
| §11 一句话压缩 | 6 类数据各自分工 | ✅ 正确，但漏了 phase2_locals（B.7）|
| §12 总体判断 | "形成一条完整研究链" | ✅ 正确 |

**总体评价**：Codex 的 12 段判断**基本全部正确**。核心定性（clean_rerun 是主骨架 / L2 Phase B 是主扩展证据 / L2 Phase C 只能写 future work / artifacts 是 provenance 层）**全部经得起实地核实**。需要修正的点只有两处：

1. **`phase1_smoke` 不存在** → 从清单删除（已在 A.1 备注）
2. **`phase2_c2b_local`（87 files, 2.1M）未被列入** → 独立为 B.7，作为 7B supporting regime 的数据源

## C.2 五级价值金字塔

Codex 给的是 4 级（主证据 / 次级支撑 / 扩展边界 / 治理追溯）。核实后精细化为 5 级：

```
Level 5: 核心主证据（immutable canonical）
        ├─ results/clean_rerun_20260419T09/
        ├─ docs/clean_rerun_20260419T09/
        └─ artifacts/clean_rerun_20260419T09/
        用途：5 条 final-ready claim 的 md5-locked 源头

Level 4: 扩展主支撑（Pareto, AutoK 硬证据）
        └─ results/l2_pareto/ (335 CSV)
        用途：Ch4 主图 + regime 地图

Level 3: 历史验证 + 次级扩展
        ├─ results/phase1_official/ + phase1_official_v2/  (45 CSV)
        ├─ results/l2_kv_asymmetric/ (108 CSV)
        └─ results/l2_prompt_adaptive/8b/ (15 CSV, weak/mixed)
        用途：第一层叙事起点 + 粒度扩展 + Gate C mixed 承接

Level 2: 开放方向 + 辅助诊断
        ├─ results/l2_prompt_adaptive/{1p5b,7b}/ (30 CSV off-protocol)
        ├─ results/phase2_c2b_local/ (87 files, 2.1M)
        └─ results/phase2_{c1,c2,diag}_local/
        用途：Future Work seed + 7B supporting regime case + 附录诊断

Level 1: Provenance + 历史对照
        ├─ artifacts/allocator/ + kv_calib_*.json (26 JSON)
        └─ results/{final,_canonical,archive}/ (旧归档)
        用途：方法可追溯性 + 防叙事回滑（不进正文）
```

## C.3 数据覆盖的真实完整度

| 故事章节（见 thesis_story.md）| 数据覆盖度 | 主要来源 |
|---|---|---|
| §1 理论动机 | N/A（纯理论分析） | — |
| §2 第一层（INT8 + INT4） | **充分** | clean_rerun Step 1 + phase1_official |
| §3.2 allocator regime 地图 | **充分** | clean_rerun Step 2 (48 runs) |
| §3.3 L2 Phase A | **中等** | l2_kv_asymmetric (108 CSV) |
| §3.4 L2 Phase B | **充分** | l2_pareto (335 CSV + v4 聚合) |
| §4 AutoK | **充分** | Pareto top tier + clean_rerun auto-k |
| §4.3 L2 Phase C | **弱/混合**（由数据决定） | l2_prompt_adaptive/8b |
| §5 Mistral/3B/14B 角色 | **充分** | clean_rerun Step 2+3 |
| §5.5 7B 角色（aggregation-split） | **中等** | phase2_c2b_local + phase2_diag_local |
| §6 Future Work | **充分**（方向清晰） | L2 三 Phase 的边界观察 |

**结论**：当前数据资产**足以支撑新故事线完整写出**，没有必须补跑的实验缺口。

## C.4 风险提示

**风险 A：磁盘增长**
- `results/archive/` 2.7G + `results/final/` 250M 是本地磁盘最大占用
- 建议：6 个月内归档到 cold storage，保留 INDEX.md 指针

**风险 B：`phase1_smoke` 不存在**
- 若 Ch4 / Methods 要追溯"behavior-guided 最早是怎么跑通的"，只能从 `results/phase1_official/` 起讲
- 不影响新故事成立，但需避免引用不存在的 smoke

**风险 C：`phase2_c2b_local` 位置需明确**
- 是 7B supporting regime case 的唯一原始数据源
- 若 Ch4 §5 写 7B aggregation-split，必须引用这里
- 建议：为它单独写一份 readout（当前只有 `docs/phase2_final_readout.md` 覆盖部分）

**风险 D：不要回滚到旧 Phase 2.5 Ch5-Finding 叙事**
- 旧 `~/.claude/plans/partitioned-sparking-newt.md` 的 "3 Regime findings / F1-F4 gate verdict" 是 phase 2.5 的 working note
- 新故事已升级为"behavior framework 贯通 calibration + allocation + AutoK"
- 写正文时若发现自己在引用 F1/F2/F3/F4 gate，**请停下回到 `docs/thesis_story_20260420.md`**

---

# Part D. 使用建议

## D.1 论文改写顺序（从数据最稳到最新探索）

**先写（依赖 Level 5 + Level 4）**：
1. Ch4 主表（INT8 canonical + cross-model compare + Mistral/3B/14B 角色）
2. Ch4 Pareto 主图（L2 Phase B，7B uniform_int4 崩坏可视化 + auto-k top tier）

**次写（依赖 Level 3）**：
3. Ch3/Ch4 第一层 calibration 方法与实验（INT8 + INT4）
4. Ch4 role-aware 小节（L2 Phase A）
5. Ch4 AutoK 段（基于 Pareto + Mistral）

**最后写（依赖 Level 2）**：
6. Ch4 / Discussion 7B aggregation-split supporting case
7. Ch4 末尾 Prompt-adaptive 段（必须写成 weak/mixed + lcc 独立点）
8. Ch5 Future Work（per-prompt routing + 更成熟 role-aware + Pareto 扩展）

## D.2 文档使用纪律

- 每次改章节前：先回 **`docs/thesis_story_20260420.md`** 确认叙事位置 + 本文 **Part B** 确认数据来源
- 每次引用数据前：检查它在 **C.2 五级金字塔**的层级（Level 5 进正文主表；Level 2 只进附录）
- 发现新事实或新判断：append 到 **Part C 末尾修订记录**（不改 Part A-B 的既定分层）
- 目录结构查询：回 **Part A**（结构层底账）

## D.3 文档维护

- 本文件 **只 append，不 rewrite**
- 若后续跑了新实验（Future Work），新建 `docs/data_asset_inventory_YYYYMMDD.md` 并在本文件尾部加指针
- 若 5 条 final-ready claim 被外部评审挑战：在 Part C 末尾 append 一条 "review feedback" 条目，不改 Part A-B

---

## 附：修订记录

_本节只 append，不改 Part A / Part B 既定分层。_

**2026-04-20 初版**：
- Codex 2026-04-20 创建结构层底账（Part A 基础）
- Claude 扩展实地核实 + 价值判读（Part B / C / D）
- 初版曾包含叙事主线（原 Part A-G），后于同日分离为 `docs/thesis_story_20260420.md`
- 本文件保留数据层 + 价值判读层，Part B-E 重新编号为 A-D
- 全局表 A.1 新增叙事主线文档指针

---

**文档结束。**
