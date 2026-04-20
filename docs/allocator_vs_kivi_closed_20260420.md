# Allocator vs KIVI Hook — 正式关闭报告

> **状态**：`L4_CLOSED`
> **决定日期**：2026-04-20
> **决定人**：用户（陈梓浪）
> **归档 commit**：`0156335 decision(thesis): close Allocator-vs-KIVI Hook at L4_mechanism_only`
> **面向对象**：thesis 写作 agent / 下一个 session 的自己 / 审稿前回溯者

---

## 1. TL;DR

**"Allocator-enabled RoleAlign vs KIVI-style formal compare" 这条 claim 路线正式放弃。**

不再预留 conditional Hook。论文里所有 "如 Hook 激活到 L1/L2 则..." 的条款、占位段、带条件的 Future Work 说明，**全部简化或删除**，保留一条普通 Future Work 条目即可（详见 §5 下游 actions）。

Allocator 作为**方法贡献**继续留在 §3（"behavior-guided per-layer bit allocation"），**不 claim 它系统性超越 KIVI**。

---

## 2. 关闭的依据（G2 aggregate 实测）

经过完整的 5-model × 5-task × 3-system main phase（360 CSV，EXIT=0，0 sample failure，Pareto gate `ok=true`）后，对比 `kivi_style` vs `rolealign_allocator_auto_eqmem` 的 quality delta：

### 2.1 整体统计（win_threshold |Δ|=0.5）

| 指标 | 值 |
|---|---|
| Total cells (model × task) | 25 |
| Allocator wins | 7 (28%) |
| Ties | 14 (56%) |
| **Allocator loses** | **4 (16%)** |
| Mean Δ | **+0.192**（quality 量级 5-20，相当 ~1-3% 相对提升）|
| Min / Max Δ | −2.279 / +2.735 |
| **G2 Level** | **L4_mechanism_only** |

### 2.2 Budget cost（相对 KIVI baseline）

| Model | KIVI MB | Allocator MB | **Budget Ratio** |
|------|---------|------------|--------------|
| 1p5b | 8.42 | 12.64 | **1.501×** |
| 3b | 10.83 | 17.86 | **1.649×** |
| 8b | 38.50 | 66.62 | **1.730×** |
| mistral7b | 38.50 | 66.62 | **1.730×** |
| 14b | 57.75 | 105.00 | **1.818×** |

### 2.3 Per-model 极化（关键观察）

| Model | Wins | Ties | Loses | Win rate | Pattern |
|------|------|------|-------|----------|---------|
| 1p5b | 1 | 4 | 0 | 20% | 整体微正，dureader 异常 +29.9% |
| 3b | 0 | 5 | 0 | 0% | **完全打平** |
| 8b | 2 | 2 | 1 | 40% | 混合（hotpotqa +50% vs dureader −6%）|
| **14b** | **3** | **2** | **0** | **60%** | ⭐ 唯一干净赢 |
| **mistral7b** | **1** | **1** | **3** | **20%** | ⚠️ **反向输**（dureader −24%）|

### 2.4 核心事实

> **用 50-80% 额外 KV 内存，换来平均 ≤3% 的 quality 提升，且 16% 的 cell 反向更差。**

这不是 Pareto advantage（allocator 在 mistral7b 被 KIVI 严格 dominate：更多内存 + 更差分数）。这是 **Pareto side-step**——两个系统在 Pareto plane 上交叉，各有胜负，没有清晰优势方向。

---

## 3. 判定逻辑：为什么是 L4 不是 L3

按 `docs/thesis_story_20260420.md §13.2` 的四档规则：

| Level | 定义 | 当前数据能达到吗？ |
|-------|------|----------------|
| L1 systematic win | win rate ≥ 80% 且 no lose | ❌ 28% win + 16% lose |
| L2 quality win | win rate ≥ 60% + lose ≤ 20% | ❌ 28% < 60% |
| L3 Pareto advantage only | "在 Pareto 前沿占据更好位置" | ⚠️ 语义上要求 allocator 至少**不被 dominate**；mistral7b 被 KIVI 严格 dominate（allocator 用更多 memory + 更低 quality），不成立 |
| **L4 mechanism-only** | Hook 作为 future work 并入 §6 | ✅ **唯一诚实定位** |

曾一度考虑的 "L3 + per-model decomposition" framing **不诚实**：
- 14b 单独看确实像 L2，但单 model 不构成 systematic claim
- mistral7b 反向失败不是 "caveat"，是**证伪**"allocator 系统优于 KIVI"假设
- 用"mean Δ >0" 包装成 Pareto advantage 忽略了 mistral 的 Pareto-dominated 事实

---

## 4. 用户决策原话（审计留证）

> "我觉得那我们就不用写这个了，因为我们用了更多的成本还不一定能保证稳赢的话，那我们为什么还要再做这个呢？"

—— 2026-04-20 session, in context of G2 aggregate readout.

---

## 5. 下游 thesis-writing agent 的 action list

### 5.1 thesis_story §13（已完成，参考对齐）

- `docs/thesis_story_20260420.md §13.1` 已改为 `L4_CLOSED`，附 decision date + G2 数据 + 用户原话
- `docs/thesis_story_20260420.md §13.4` 激活清单 G0/G1/G2 gate 全部 ✅，最终 L4
- **你不需要再动 §13**

### 5.2 thesis chapters 要做的简化（handoff 给你执行）

以下是我 grep 过的、包含 allocator-vs-KIVI conditional 条款的 line 位置（基于 `0156335` HEAD 时的状态，如已被后续 commit 动过请 re-grep）：

**A. `thesis/chapters/ch2_related_work.tex:330`**

当前：
> 相对其它 KV Cache 量化方法，本文只做定性 positioning，不做 matched-budget 级别的数值对比。

**保留原样**。这句本来就是"不做"语义，不是条件 Hook。无需改。

**B. `thesis/chapters/ch4_experiments.tex`**

- `line 308`：`"为 §2.5 预留的 Allocator-vs-KIVI matched-budget 正式对比留出 Hook 位置"` → **删除"为 §2.5 预留...Hook 位置"整句**，改成单独一句简述 "本章不包含 formal Allocator-vs-KIVI compare"
- `line 630-639`：
  - `"(b) matched-budget 正式对比缺口——...正式的 Allocator-vs-KIVI matched-budget 对比构成一个独立的实验包"` → 保留主句（客观说明 compare 不在本文 scope）
  - `"% HOOK POSITION（§2.5 Allocator-vs-KIVI matched-budget formal compare）"` + `"% 当前状态：Hook BLOCKED（2026-04-20）"` + `"% 当 Hook 激活到 L1/L2 时，在此插入："` → **三行 comment 全部删除**（Hook 永不激活，占位注释是死代码）
- `line 661-679`：`"Budget band 的定义（非严格 matched-budget）"` 段落
  - `"严格 matched-budget 的 Allocator-vs-KIVI formal compare 作为条件 Future Work（story §13 Hook、第 \ref{sec:conclusion-future} 节）"` → 去掉"条件" 二字，改为 "作为 Future Work（第 \ref{sec:conclusion-future} 节）"，去掉 "story §13 Hook" 引用

**C. `thesis/chapters/ch5_conclusion.tex`**

- `line 76`：`"若 Hook（story §13）激活则可具体化为正式 claim"` → **整句删除**（因为已决定不激活，保留这句是 meta 自我否定式 disclaimer，违反 `feedback_meta_disclaimers.md`）
- `line 157-161`：
  ```
  \item \textbf{【条件性 Limitation】Allocator-vs-KIVI matched-budget formal compare 未完成}。
  ...
  若 Hook 激活到 L1/L2，本条 limitation 可以从列表中删除，
  ```
  → 改写为普通 limitation 条目：去掉 "【条件性】" 标签，去掉 "若 Hook 激活..." 整句。最终形如：
  > `\item \textbf{Limitation}: 本文不包含 Allocator-vs-KIVI matched-budget formal compare；所提出的 allocator 在方法章保留作为 per-layer bit allocation 机制，但未宣称系统性超越 KIVI。`
- `line 193`：`"story §13 Hook 的正式对比包是本文的第一个条件 Future Work"` → 改为 "Allocator-vs-KIVI matched-budget formal compare 作为 Future Work 之一"（去掉"条件"和 story §13 引用）

### 5.3 **不要做的事**

- ❌ 不要删除 allocator 本身的方法描述（§3 / §3.5 的 "behavior-guided per-layer bit allocation"）—— allocator 作为方法贡献保留
- ❌ 不要删除已有的 allocator 机制图（如图 2 Framework / 图 4 Sensitivity Heatmap 里的 allocator 部分）
- ❌ 不要反向改写成 "我们的 allocator 不如 KIVI" —— 事实是 "我们 allocator 作为 mechanism 有 scale-dependent 趋势，未来需要在更广 bit dictionary 下正式对比 KIVI"
- ❌ 不要重新 spawn ExecPlan 尝试找"更好的 policy" —— 用户明确放弃这个方向
- ❌ 不要在 abstract/intro 强调 allocator 对 KIVI 的比较 —— allocator 的定位是 "per-layer bit allocation 机制"，不是 "KIVI killer"

### 5.4 **一定要做的事**

- ✅ 所有 "Hook 激活/条件" 类措辞清零（上面 5.2 列表）
- ✅ 普通 Future Work 条目保留一条："matched-budget formal Allocator-vs-KIVI compare（需要扩展 bit dictionary 至 2-bit 或重新搜索 budget-matched policy）"
- ✅ 如果 §4.X 里有用 `\ref{sec:hook-allocator-kivi}` 之类的引用，清理到普通段落引用

---

## 6. 保留下来的 infrastructure（未来 future work 时可复用）

这些是在这轮尝试中产生的代码/脚本/配置，**不要删**——它们独立于 Hook claim，下次 revisit 时有价值：

| 项 | 路径 | 用途 |
|---|------|------|
| pareto/strict gate_mode 双模式 checker | `scripts/check_system_vs_kivi_completeness.py` | 以后若重试 allocator claim 可复用 |
| `SVK_MODEL_PATH_<KEY>` env override | `scripts/system_vs_kivi_common.py` | ModelScope 路径覆盖 HF id，无需改代码默认值 |
| phase runner | `scripts/run_system_vs_kivi.py` | smoke/main/ablation 三 phase |
| G2 aggregator | `scripts/aggregate_system_vs_kivi.py` | 产出 quality pivot + win/tie/lose 判定 |
| 通用 tmux watchdog | `scripts/remote_watchdog.sh` + `.agents/skills/remote-server/SKILL.md` | 任何远端长任务等待场景 |
| allocator backend | `int4_ours_asym_alloc` kv_mode + `src/cache/role_aware_allocator_cache.py` | allocator 仍是论文方法贡献 |
| 5 个 rolealign calib | `artifacts/kv_calib_rolealign_{1p5b,3b_v3,8b_v3,14b_v3,mistral7b_v3}.json` | allocator 运行前置数据 |
| 实测数据 | 远端 `/root/autodl-tmp/LLM_KVCache_Quantization_systemvkivi_36bf21c/results/system_vs_kivi/raw/main/`（360 CSV）+ `smoke/`（90 CSV）+ aggregate/（G2 产物）| audit trail，不进正文但可查 |

---

## 7. 不做的事（明确）

- ❌ **不启动 ablation phase**：L4 定位下 ablation（auto-k vs fixed-k mechanism 分解）没有 claim 支撑作用，跑 3-5h × 3 卡 ≈ 9-15 GPU-hour 为不支撑 claim 的实验做机制分解，不符合科研纪律
- ❌ **不跑 bit dictionary 扩展实验**（加 2-bit / 3-bit）：超出本论文 scope
- ❌ **不重跑 policy 搜索**：搜一个 matched-budget + 仍能赢 KIVI 的 policy 成功率极低（数学上 `{4,8,16}` bit 字典下只剩 ≤1 层可升 bit），投入产出比不合理

---

## 8. 时间线（commit 链）

| Commit | 内容 |
|--------|------|
| `ab082e5` | parser/CLI allocator kv_mode 接入 5 个 eval/profile entrypoints（初版混合 Phase 6 thesis 改动，SessionEnd hook 所致）|
| `36bf21c` | iteration 记录 parser/CLI wiring 收口 |
| `30c548d` | 新增 `scripts/remote_watchdog.sh` + skill 规则 |
| `d4dd704` | pareto gate_mode 初版（初始 P2 版本，与 Phase 6 thesis 同 commit）|
| `679c55c` | Pareto gate Codex R1/R2 P2 follow-ups（info_budget_drift 分离到独立 key；compared_systems ∩ expected_systems）|
| `8a87d89` | `SVK_MODEL_PATH_<KEY>` env override |
| `e12f8ec` | chain launcher（等 GPU 0 空闲自动启 14B）|
| **`0156335`** | **本决定：Hook L4_CLOSED + G2 aggregator + iteration 决定记录** |

---

## 9. 一句话总结（用于 thesis 审稿 QA 和未来自己）

> 我们做了完整的 Allocator-vs-KIVI 5-model formal comparison 实验，数据显示 allocator 需要 1.5-1.8× 的 KV 内存开销才能获得约 1-3% 的平均 quality 提升，且 16% 的 (model, task) 组合反向更差（尤其 Mistral-7B）。cost/benefit 不支持 systematic claim，因此本文把该 comparison 定位为 Future Work，allocator 本身作为 per-layer bit allocation 机制在方法章保留。

---

*End of report. HEAD at report creation: `0156335`.*
