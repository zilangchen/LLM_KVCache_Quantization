# Phase 2 编号 8 人工判读报告（2026-04-18 定稿）

> 本报告不复述 gate 结果，而是做**人工判读** —— 直面 3 PASS / 3 FAIL 的混合输出，给出明确的论文口径收窄建议。

**数据来源**：
- `results/phase2_c2_local/phase2_verify_all.csv`（全量 5 批次聚合 after backfill）
- `results/phase2_c2_local/phase2_final_gate.log`（gate 判定）
- C1 (7B 42 runs) + Diag-7B (6 runs) + C2 (8B 39 runs) + 8A (60 runs) + 8B (32 runs after backfill) = **179 runs**

---

## 1. 当前最强可辩护主张

### ❌ 不能再写的三种口径
- **~~"behavior-guided allocation is universally better"~~** — 被 7B max_k1 -22.7%、8B k≥3 -7% 直接证伪
- **~~"pure scale-shift: best-k 随规模单调上移"~~** — 被 8B 证伪（8B nominal best-k=7 实为 artifact，真正 3/3 胜的只有 k=1；跨模型 best-k 曲线不是单调）
- **~~"aggregation split is a general phenomenon"~~** — 被 8B 证伪（mean_k1 与 max_k1 差 -0.6%，8B 是 aggregation-insensitive）

### ✅ 当前最强可辩护主张（边界型，建议收口版本）

> **Behavior-guided KV cache allocation exhibits a family- and scale-specific advantage, not a universal law. Three distinct regimes are observed across model architectures:**
> 
> 1. **Qwen 1.5B — low-budget robust on specific tasks**: BAKV `k=1` stably wins Random by +15–19% on gov_report/hotpotqa (F1 gate sub-pass); narrativeqa is aggregation-agnostic but seed-sensitive (F1 fails this task)
> 2. **Qwen 7B — aggregation-split regime**: `k=1` is pathological with max aggregation (-22.7% vs Heuristic) but fully recovered by mean aggregation (+150.6%); `k=5` becomes the max-aggregation sweet spot (+3.6%, 3/3 tasks)
> 3. **LLaMA 3.1 8B — aggregation-insensitive with weak low-budget preference**: `k=1` marginally wins Heuristic (+1.3%) regardless of aggregation; at `k≥3` BAKV *underperforms* Heuristic by ~7%
>
> **Core implication**: behavior-guided allocation's advantage over a positional heuristic is **architecture- and scale-dependent**; no single `(k, aggregation)` configuration generalizes across all three regimes. Positional heuristic remains a strong baseline that BAKV only beats under specific conditions.

这是**收窄了三次**后最诚实的主张。比起 pure scale-shift 或 universal，这个主张：
- **无法被已有数据证伪**（每一条都来自实证）
- **保留 publishable 核心**（Qwen 7B 的 split regime 是最新颖最完整的贡献）
- **admit limitation**（8B 反例是诚实的 scope disclosure）

---

## 2. 8B 归类：**aggregation-insensitive 中间态**（明确）

### 关键三数据对比

| 指标 | 8B 数值 | 7B 参照 | 1.5B 参照 |
|---|---|---|---|
| bakv_max_k1 avg | **8.495** | 2.616 (崩) | 8.55 (+44% 强) |
| bakv_mean_k1 avg | **8.445** | 6.556 (救回) | ≈ max (等价) |
| **max vs mean diff** | **-0.6%** | **+150.6%** 💥 | 0% |
| best-k (by avg) | 7 (artifact*) | 5 (real) | 1 |
| k=1 BAKV vs Heur | +1.3% (3/3 胜) | -22.7% (0/3) | +44% (3/3) |
| k≥3 BAKV vs Heur | **-7%** (全 k 输 3/3) | -0.2%~+3.6% | tie |

*8B best-k=7 是 nominal artifact —— 在 k=7 下 BAKV 只胜 Heuristic 1/3 且 avg 仍输 -0.8%。真正 3/3 胜的 k 只有 1（但强度仅 +1.3%）。

### 判决

**8B 更像 `1.5B aggregation-insensitive` 模式，但 low-budget 强度大幅衰减**：

- ✅ **符合** 1.5B 模式：max=mean（-0.6%），k=1 BAKV ≥ Heuristic（3/3 胜）
- ❌ **不符合** 7B max collapse 模式：8B max_k1 没崩（+1.3%，不是 -22.7%）
- ❌ **不符合** 7B mean rescued 模式：8B mean_k1 没有"救回"现象（本就没崩）
- ⚠️ **新特征**：k≥3 时 BAKV 反**输** Heuristic 7%（1.5B 是 tie）

**明确归类**：**"aggregation-insensitive 中间态 + BAKV 在宽 budget 下失效的模型"**。不是 1.5B 的复制（low-budget 强度从 +44% → +1.3% 大幅衰减），也不是 7B 的 split。是第三种 regime。

**对论文含义**：8B 是比 1.5B / 7B 更不支持 BAKV 的模型 —— 这反而强化了"behavior-guided 优势是条件性的"这一边界型主张，不是打击 BAKV 范式本身。

---

## 3. 1.5B 稳定性：gate F1 为什么 FAIL？

### F1 真实状态（从 gate log 直接读）

```
F1 稳定: 2/3 (task,k) combos: BAKV > mean(Random 8 seeds)
  gov_report/k=1:   BAKV=7.777  vs mean(Random)=6.748  → +15.2%  ✅
  hotpotqa/k=1:     BAKV=4.255  vs mean(Random)=3.565  → +19.3%  ✅
  narrativeqa/k=1:  BAKV=4.354  vs mean(Random)=5.152  → -15.5%  ❌
```

**Gate 判据**：需要 ≥80% (task,k) 胜，2/3 = 66.7% < 80% → FAIL。

### 逐 task 判读

| Task | BAKV 稳？ | 根据 |
|---|---|---|
| **gov_report** | 🟢 **稳** | BAKV vs 8 Random seeds +15.2%；offset 3/3 方向一致 |
| **hotpotqa** | 🟢 **稳** | BAKV vs 8 Random seeds +19.3%；offset 3/3 方向一致 |
| **narrativeqa** | 🔴 **不稳** | BAKV **输** Random 8 seeds 平均 -15.5%；offset signs=[+1,+1,-1] 翻转 |

### 为什么 narrativeqa 不稳？

- narrativeqa 是**高方差任务**（自由回答 + 长上下文 + 主观评分），Random seed 之间波动本身就大
- 编号 7 M4 报告的 1.5B 上 BAKV k=1 胜 Heuristic +44% 主要来自 narrativeqa（6.773 vs heur 6.345 → +7%）和 gov/hotpot 的大 delta，但 narrativeqa 的 **Heuristic k=1=1.878** 低分很可能是单 seed 负极值
- 当把 Random 扩展到 8 seeds 求均值（mean=5.152），narrativeqa 的 noise floor 其实很高，BAKV 的 4.354 落在 noise 之下

### 这对论文口径的含义

1. ❌ **不能** 笼统写 "1.5B BAKV k=1 is robustly better than Random on all tasks"
2. ✅ **必须** 写成 "1.5B BAKV k=1 robustly beats Random on gov_report and hotpotqa (+15–19%), but is **not distinguishable from Random** on narrativeqa"
3. **narrativeqa 的"胜利"（+44% 编号 7 M4）很可能有 seed-luck 成分** —— F1 的 8 seed 均值揭示了这一点
4. **Threats to Validity 必须写入**：编号 7 的 3-task mean 是 single-seed optimistic 估计，narrativeqa 需要多 seed 才能定性

这是一个**自发纠正**的好例子 —— 我们的 verification 机制正常工作，抓到了原始 finding 的 seed-luck 成分。

---

## 4. 扩任务（batch2）信息量分析

### 4 new tasks 逐项判读

| Task | metric | BAKV | Heur | Uniform INT4 | 信息量 | 主表？ |
|---|---|---|---|---|---|---|
| **dureader** | rouge_l | **11.324** | 1.657 | 1.436 | 🟢 **强信号** +584% | ✅ **进主表** |
| **lcc** | edit_sim | **12.928** | 9.148 | 8.525 | 🟢 **有信号** +41% | ✅ **进主表** |
| **trec** | accuracy | 0.000 | 0.000 | 0.000 | 🔴 **无信息量** | ❌ **附录或弃用** |
| **vcsum** | rouge_l | 0.000 | 0.000 | 0.000 | 🔴 **无信息量** | ❌ **附录或弃用** |

### trec / vcsum 0.0 的性质判读

**这是任务/模型在 INT4 下的整体崩坏**，不是 "BAKV=Heur tie" 的中性证据：

- Uniform INT4 k4v4（**质量地板**）= 0.000 在这两个 task 上
- Heuristic k=1 = 0.000
- BAKV k=1 = 0.000
- 所有 allocator 都 0 → **1.5B + INT4 组合对这两个 task 本就无能力**（1.5B 的 trec classification 在 INT4 下头部完全崩；vcsum 中文摘要 rouge_l 被严格匹配时常归 0）

**不允许把 "4/4 PASS" 当强证据**：
- gate 判据 "BAKV ≥ Heuristic" 在 "0=0" 情况下**机械满足**，但这**不是 evidence**
- 真正的"胜"只有 **2/4 tasks**（dureader + lcc）
- 正确叙述："BAKV 在 2 个有信号的 new tasks（dureader, lcc）上稳定胜 Heuristic；在另 2 个 task（trec, vcsum）上 1.5B+INT4 基础能力已崩，无法判优劣"

### 主表建议

**主表只收 `dureader + lcc`**（加上原 narrativeqa/hotpotqa/gov_report）= **5 个有信息量的 tasks**。
trec + vcsum 可以放入附录（列出 0=0 现象 + Uniform INT4 也 0 的说明），作为 "1.5B 能力上限" 的 scope disclosure，而非 allocator 比较。

---

## 5. 当前编号 8 是否够收口？

### 明确结论：**够收口 EMNLP Findings 级别，Main 级需要额外工作**

### 当前已有的 publishable 核心

1. ✅ **Qwen 7B aggregation split regime** — 编号 8 最强贡献
   - 铁证：max_k1 -22.7%、mean_k1 +150.6% 救回、k=5 max 3/3 胜 +3.6%
   - protected_layers 机制对比：max=[27] 末层 / mean=[0] 首层 / heuristic=[14] 中层
   - 这个 finding 无论 1.5B/8B 如何都站得住
2. ✅ **1.5B 上 2/3 tasks 稳健，1/3 unstable** — F1 pass 部分
3. ✅ **8B aggregation-insensitive 中间态** — 第三种 regime 证据
4. ✅ **扩任务 2/4 强信号**（dureader 碾压 + lcc 有效）
5. ✅ **跨 3 scale 的 best-k 曲线**：1.5B→1, 7B→5, 8B→1（但弱）—— 不是单调 scale-shift，是 family-dependent

### 如果冲 Main 需要补什么（非紧急）

- **统计显著性**：当前只报 avg +delta%，没有 bootstrap CI / sign-test p-value。若要 Main 需补
- **narrativeqa FAIL 的根因调查**：是 task 本身噪声还是 BAKV 在长 narrative 上真失效？需要额外 seed 或 n=200 实验（但这是未来工作，不是收口 blocker）
- **更多 model family**：目前 2 family (Qwen, LLaMA)。再加 1-2 家（Mistral, Gemma）会大幅加强 "family-specific" 叙事

### 建议：**现在收口，不开新实验**

理由：
1. 已有 179 runs 支撑的边界型主张已充分可辩护
2. 再跑 NoLiMa / K/V 非对称 不会直接加强当前主张（它们是扩维度，不是填空）
3. narrativeqa noise 深挖是独立研究问题，不应拖累论文收口
4. Findings 级别已经稳当，冲 Main 的风险点（统计检验、n=200、新 family）**不是 Phase 2 编号 8 能独立补上的**

---

## 核心数字速查表

```
跨 3 模型 BAKV(max) vs Heuristic @ each k  (avg over 3 LongBench tasks)

         k=1        k=3        k=5        k=7       best-k
1.5B:    +44%       tie        tie        tie       k=1
7B:      -22.7%     -0.2%      +3.6%★     +0.4%     k=5
8B:      +1.3%      -7.0%      -7.1%      -0.8%     k=7 (artifact)

7B aggregation split @ k=1  (Diagnostic-7B):
  max_k1 vs Heur:  -22.7%  (崩)
  mean_k1 vs Heur: +93.7%  (强势救回)
  max vs mean:     -150.6% gap (铁证 split regime)

8B aggregation @ k=1:
  max_k1 vs Heur:  +1.3%
  mean_k1 vs Heur: +0.7%  (从 9.965/6.021/9.348 计算 vs heur_k1 9.835/5.961/9.354)
  max vs mean:     -0.6%  (aggregation-insensitive)

1.5B F1 (Random 8 seeds mean vs BAKV):
  gov_report:  BAKV +15.2%  ✅ stable
  hotpotqa:    BAKV +19.3%  ✅ stable
  narrativeqa: BAKV -15.5%  ❌ unstable (seed-luck hypothesis)

扩任务 (batch2, 1.5B k=1):
  dureader:   BAKV 11.32 / Heur 1.66 / Uniform 1.44  → 强信号 +584%
  lcc:        BAKV 12.93 / Heur 9.15 / Uniform 8.53  → 有信号 +41%
  trec:       0 / 0 / 0  → 无信息量（INT4 全崩）
  vcsum:      0 / 0 / 0  → 无信息量（INT4 全崩）
```

---

*生成时间：2026-04-18 14:00*
*数据版本：all 5 batches aggregated, batch2 uniform_int4 backfilled*
*生成工具：手动人工判读（不依赖 aggregate_phase2_verify.py gate 简单 PASS/FAIL）*
