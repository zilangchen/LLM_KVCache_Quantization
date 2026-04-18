# 论文主线升级实时工作台

> 用途：这不是结果发布页，也不是最终 readout。  
> 它是**论文升级工作台**，用于把每一轮最新实验结果映射成：
> 1. 主线应该升级哪里  
> 2. 哪些内容升/降级、保留/放弃  
> 3. 哪些图要新增、哪些旧图要退场

> 更新原则：
> - **实时维护**：每轮关键实验完成后更新
> - **来源显式**：每条判断都标明数据/文档来源
> - **provenance 分级**：区分 `exploratory`、`candidate-main`、`final-ready`
> - **不替代**：
>   - `docs/phase2_final_readout.md`：结果判读
>   - `docs/final_results_summary.md`：历史最终总结
>   - `docs/thesis_chapter_mapping.md`：章节-图表映射
>   - `docs/thesis_figure_prompts.md`：出图 prompt

---

## 0. 当前快照

**更新时间**：2026-04-19 06:17 CST

**当前实验链状态**

| 项 | 状态 | 来源 |
|---|---|---|
| Phase 2.6 A 方案 | **全部 exploratory wave 完成 @ 2026-04-19 05:27 CST** | 远端 `tmux` / 进程状态 |
| Wave 2 sanity | 已通过 | `results/phase2_trec_vcsum_sanity/` |
| Mistral smoke | 已通过（6/6） | `results/phase2_c4_mistral7b/smoke/` |
| Wave 1 (8B extended) | 已完成（30/30；含 `9-run auto-k backfill`） | `results/phase2_c2b_llama8b_extended/` |
| Wave 3 (7B random) | 已完成（24/24） | `results/phase2_7b_random_hardening/` |
| Wave 4 (14B sweep) | 已完成（45/45；含 `9-run auto-k backfill`） | `results/phase2_c3_qwen14b/` |
| Wave 5 (Mistral full) | 已完成（45/45） | `results/phase2_c4_mistral7b/` |
| Wave 5 smoke | 已完成（6/6） | `results/phase2_c4_mistral7b/smoke/` |
| Wave 7a (7B extend tasks) | 已完成（36/36） | `results/phase2_batch4_extend_tasks_7b/` |
| Wave 7b (8B extend tasks) | 已完成（40/40） | `results/phase2_batch5_extend_tasks_8b/` |
| Wave 6 (Qwen-3B sweep) | **已完成（45/45 @ 05:27）；3 task GATE PASS；含 auto-k** | `results/phase2_c5_qwen3b/` |

**当前远端执行形态说明**

- 截至 `2026-04-19 05:27 CST`，Phase 2.6 exploratory 链全部完成：
  - Wave 1/3/4/5/7a/7b/6 + Wave 2 sanity + Mistral smoke + 18-run auto-k backfill 全 GATE PASS
- 当前 `tmux` 为空，3 GPU 全 idle
- 当前最稳的解释：
  - Phase 2.6 exploratory 层已全部收口
  - 数据可用于 `candidate-main` 层的 readout 与 叙事调整
  - 但不作最终主表唯一源；仍需 clean-provenance rerun 覆盖验证

**当前 formal audit 状态**

- [docs/phase2_data_mainline_audit_20260419.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_data_mainline_audit_20260419.md) 已完成：
  - 对已完成的 Phase 2.6 raw assets 做了结构完整性、文件完整性、跨模型 auto-k 口径、3B anomaly、heuristic baseline、extend-task 证据分级与 theory-support audit
- 当前应正式吸收的 audit 结论是：
  - **`candidate-main` 级主线已经成立**
  - **不是 `final-ready`**
  - **行为引导的主张应写成 framework + regime reading，而不是 superiority**
- 当前最重要的 provenance 判断：
  - audited result files 结构上干净
  - 但远端 worktree 生产时是 dirty 的
  - 因此当前只支撑 `candidate-main narrative support`，不支撑最终主表唯一来源
- 当前 clean-provenance 启动状态：
  - [docs/clean_provenance_launch_plan.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/clean_provenance_launch_plan.md) 已落地
  - 默认 pin：`ddada19`
  - 当前建议：单独执行 `L1 claim-critical` clean rerun，不与 `L2` exploratory 混跑

**Wave 1 (8B extended) 当前快速判读**

- `Wave 1 auto-k backfill` 已完成，新增了：
  - `bakv_auto_cov70_max`
  - `bakv_auto_cov80_max`
  - `bakv_auto_cov90_max`
- 当前 8B 三任务平均分前列是：
  - `bakv_k11` = **9.5214**
  - `bakv_auto_cov80_max` = **9.3543**
  - `bakv_auto_cov90_max` = **9.3491**
  - `bakv_auto_cov70_max` = **9.2949**
  - `bakv_mean_k3` = **8.9105**
- 这说明：
  - `auto-k` 在 8B 上已补成**强二梯队**
  - 它明显强于 heuristic / mean-k 系列
  - 但当前仍略低于 best fixed-k（`bakv_k11`）
- 当前最稳的写法：
  - **8B 现在支持“auto-k 是有竞争力的 profile-aware 扩展”**
  - **不支持“auto-k 已成为 8B 上的最优统一解”**

**Wave 4 (14B sweep) 当前快速判读**

- 当前 14B `Wave 4` 完整 36/36 结果没有支持“更大模型 => 更大固定 `k` 更好”的简单叙事
- 当前平均分前列是：
  - `uniform_int4_k4v4` = **7.2345**
  - `heuristic_k3` = **7.1171**
  - `heuristic_k7` = **7.0886**
  - `uniform_int8_k8v8` = **7.0593**
  - `bakv_k1` = **7.0583**
- 这说明：
  - **heuristic / uniform 仍是强 baseline**
  - **14B 进一步反对“单调 fixed-k scale-shift”旧叙事**
  - 更稳的解释仍然是 **family-specific regimes**
- 当前新的变化是：
  - `Wave 4 auto-k backfill` 已经全部落盘完成（`9/9`）
  - `Wave 4` 总计数现已到 `45/45`
  - 但 14B 上 auto-k 的正式位置仍需通过统一 aggregation / readout 明确写出
- 当前最稳约束：
  - 在 `Wave 1 + Wave 4` 统一 readout 出来前，不把 14B 上 auto-k 写成最终结论

**Wave 5 (Mistral full) 当前快速判读**

- `Wave 5` 是第一批**完整带 auto-k** 的 Mistral-7B full sweep，共 45/45 条 full 结果
- 当前平均分前列是：
  - `bakv_auto_cov80_max` = **14.7640**
  - `heuristic_k3` = **14.6036**
  - `random3_k1_seed42` = **14.4311**
  - `bakv_auto_cov70_max` = **14.4000**
  - `heuristic_k1` = **14.3890**
- 分 task 看：
  - `gov_report` 最优：`bakv_auto_cov80_max` = **8.9555**
  - `hotpotqa` 最优：`bakv_auto_cov80_max` = **19.0795**
  - `narrativeqa` 最优：`heuristic_k3` = **17.1133**
- 这说明：
  - **auto-k range proposer 已经拿到第一批完整 empirical 正面证据**
  - 但 **heuristic 仍然是强 baseline**，尤其在 `narrativeqa` 上更强
  - 更稳的论文写法不是“auto-k 已普遍最优”，而是：
    - **Mistral 提供了 profile-aware budget range proposer 的首批正面支持**
    - **同时继续支持 family-/task-dependent regime 的解释框架**

**跨 4 model auto-k 统一 readout（经 formal audit 收紧）**

| Model | Best overall | Best auto-k | Gap | 解读 |
|---|---|---|---|---|
| **3B** (L=36, H_kv=2) | `bakv_k1` = 6.90 | `cov80` = 6.75 | -0.15 | **not best; 主现象是 early-layer bottleneck** |
| **8B** (L=32, H_kv=8) | `bakv_k11` = 9.52 | `cov80` = 9.35 | -0.17 | **strong extension, not best** |
| **14B** (L=48, H_kv=8) | `uniform_int4` = 7.23 | `cov90` = 7.15 | -0.08 | **top tier, not winner** |
| **Mistral-7B** (L=32, H_kv=8) | `cov80` = 14.76 | `cov80` = 14.76 | +0.00 | **strongest auto-k evidence** |

- **Wave 6 (3B) 独特 finding**（新）：
  - `bakv_k1` 选 `[0]` first layer（其他模型均选 mid/late）
  - `heuristic_k1` 选 `[L//2]=[18]` → metric **3.48（灾难）**
  - `bakv_k1` vs `heuristic_k1`：**6.90 vs 3.48 = +98%**
  - **3B 上 behavior-guided 对 heuristic 形成决定性胜**
  - 3B `cov90 ratio` = 83%（8B/Mistral 为 88%），heavy-tail 更显著
- 当前最稳的跨 scale 结论（修正版）：
  - **auto-k 在 4/4 model 上都是 top tier（gap 绝对值 ≤ 0.17）**
  - **但"并列最优"仅发生在 Mistral-7B**（3B/8B/14B 都略输 fixed best ~0.08-0.17）
  - **auto-k 的"胜"仍是 Mistral-specific**，尚未在其他 3 model 上扩展成 universal winner
  - **更稳的主线**：auto-k = "profile-aware budget proposer / strong extension"，不是 "universal replacement"
  - **3B 的主角不应写成 auto-k，而应写成 early-layer bottleneck regime 与 first-layer rescue**

**当前数据资产可信度分层（audit 吸收版）**

- `can-use-directly`
  - `results/phase2_c2b_llama8b_extended/`
  - `results/phase2_c3_qwen14b/`
  - `results/phase2_c4_mistral7b/` 顶层 full 结果
  - `results/phase2_c5_qwen3b/`
  - `artifacts/allocator/sweep_8b/`
  - `artifacts/allocator/sweep_14b/`
  - `artifacts/allocator/sweep_mistral7b/`
  - `artifacts/allocator/sweep_3b/`
- `can-use-with-caveat`
  - `results/phase2_7b_random_hardening/`
  - `results/phase2_batch4_extend_tasks_7b/`
  - `results/phase2_batch5_extend_tasks_8b/`
- `not-safe-for-main-claim`
  - `results/phase2_c4_mistral7b/smoke/`
  - 任何递归混算 `phase2_c4_mistral7b` full + smoke 的统计
  - `trec`
  - `vcsum`
  - 任何未经 clean-provenance 覆盖的 `final-ready` 表述

**当前 provenance 等级**

- 本轮 A 方案自动链：**`exploratory`**
- 理由：
  - 关键 runner/orchestrator 路径已 pinned 到本地 `b6d4e54`
  - 但远端运行仍不是 clean checkout 的 gold-standard provenance
- 参考：
  - [docs/phase2_6_provenance_manifest.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_6_provenance_manifest.md)

**当前 auto-k 状态**

- `auto-k range proposer` 已在本地实现，并已进入远端后续自动链
- 当前已经**实质吃到 auto-k** 的波次：
  - `Wave 5 (Mistral full)`
  - `Wave 7a (7B extend tasks)`
  - `Wave 7b (8B extend tasks)`
- 当前已经补齐 auto-k 的已完成波次：
  - `Wave 1`
  - `Wave 4`
  - `Wave 5`
- 当前最小结构性缺口已从“补 backfill”转成：
  - 把 formal audit 的结论正式并入工作台 / readout 体系
  - 固化 cross-4-model auto-k 的 `candidate-main` 口径
  - 明确 clean-provenance rerun 的 claim-critical compare set
  - 在此基础上推进 `L2`
- 当前最稳的写法：
  - **auto-k 已从设计草案升级为完整进入实验链的扩展能力**
  - **它已经有 Mistral full、Wave 1/4 backfill 与 Wave 6 的实质支撑**
  - **但其最终跨 scale 价值仍依赖统一 readout 与 clean provenance 覆盖验证**

**当前最重要的主线约束**

1. 不把 `exploratory` 数据直接写成最终主表 claim
2. 允许用它来更新论文**叙事方向、章节权重、图像 backlog**
3. 等 clean provenance 覆盖重跑后，再把候选结论升级为 `final-ready`

---

## 1. 主线升级位置总表

| 论文位置 | 当前状态 | 建议升级 | 优先级 | 触发数据 / 来源 | 当前等级 |
|---|---|---|---|---|---|
| `thesis/chapters/ch1_introduction.tex` | 仍可读作“方法优于 baseline 的广义主张” | 升级为**边界型主张**：行为对齐 allocation 的优势是 **family-/scale-/task-dependent**，不是 universal law | 高 | [docs/phase2_final_readout.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_final_readout.md) + Phase 2.6 新链 | exploratory |
| `thesis/chapters/ch3_method.tex` | 方法章更偏“框架 + kernel + calibration” | 增加一小节或一段：**allocator/aggregation/policy 只是框架下游决策层，不是 universal optimizer**；当前更具体的升级方向是“profile-aware budget range proposer（已进入实验链，待 backfill + clean 验证）” | 中 | `Wave 1/3/5/7a` 新结果 + auto-k 实现 | exploratory |
| `thesis/chapters/ch4_experiments.tex` §主实验 | 现有主实验映射更偏旧主线 | 升级为“双层结构”：先讲 **canonical validated instance（INT8 / kernel / calibration）**，再讲 **family-specific allocation regimes** | 高 | 现有 `phase2_final_readout` + Phase 2.6 A 链 | exploratory → candidate-main |
| `thesis/chapters/ch4_experiments.tex` §扩展/局限 | 还没有充分吸纳 `A 方案` / provenance / quarantine 纪律 | 增加 **provenance / clean rerun / exploratory vs final-ready** 披露 | 高 | [docs/phase2_6_provenance_manifest.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_6_provenance_manifest.md) | candidate-main |
| `thesis/chapters/ch5_conclusion.tex` | 结论仍可能写得太宽 | 收口为：**框架有效，但配置最优解依赖模型家族与预算区间** | 高 | Phase 2.5 + 2.6 累积 | exploratory |
| 附录 / Threats to Validity | 仍未系统纳入 | 新增 provenance、低信息量任务、污染窗口与覆盖重跑计划 | 高 | Phase 2.6 docs | candidate-main |

---

## 2. 内容优先级调整

### 2.1 需要升级的内容

| 主题 | 当前建议 | 为什么升级 | 证据来源 | 当前等级 |
|---|---|---|---|---|
| **Family-specific regime map** | 升级为新主线核心之一 | 这是比“单点增益”更稳、更不易被反例击穿的叙事骨架 | [docs/phase2_final_readout.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_final_readout.md) + Phase 2.6 Wave1/Wave3 | exploratory |
| **7B aggregation-split regime** | 升级为 strongest finding 候选 | 目前最有辨识度、最像 paper-level finding 的现象 | `phase2_final_readout` | candidate-main |
| **Positional heuristic is a strong baseline** | 升级为正文显式披露 | 这能让主张更可信，也能避免 reviewer 觉得 baseline 太弱 | Phase 2.5/2.6 allocator 对比 | candidate-main |
| **Exploratory vs clean-provenance separation** | 升级到正文或附录显式说明 | 这是当前项目可信度的关键防线 | [docs/phase2_6_provenance_manifest.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_6_provenance_manifest.md) | candidate-main |
| **Mistral smoke = engineering sanity, not final cross-family claim** | 升级为文中明确限定 | 避免过度解读 smoke 级结果 | `results/phase2_c4_mistral7b/smoke/` | exploratory |
| **Auto-k / auto-budget range proposer** | 升级为新方法扩展候选（已进入实验链，并拿到 Mistral full 首轮正面证据） | 8B 扩展 sweep 提出“固定 `k` 不稳”的问题；Mistral full 进一步显示 `bakv_auto_cov80_max` 取得当前最佳平均分，使 auto-k 从方法设想升级为具备 empirical 支撑的候选扩展 | `results/phase2_c2b_llama8b_extended/` + `results/phase2_c4_mistral7b/` + [docs/auto_k_selector_experiment_plan.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/auto_k_selector_experiment_plan.md) + `scripts/adaptive/behavior_aligned_allocator.py` | exploratory |
| **3B early-layer bottleneck regime** | 升级为当前最值得写进正文的新异常现象 | `bakv_k1` 明确保护 `layer 0`，而 `heuristic_k1` 保护中层并灾难性失败，显示小模型下 first-layer rescue 的异常重要性 | `results/phase2_c5_qwen3b/` + [docs/phase2_data_mainline_audit_20260419.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_data_mainline_audit_20260419.md) | candidate-main |
| **Extend-task evidence triage (`dureader > lcc > trec/vcsum`)** | 升级为工作台正式判定 | allocator 的 extend-task 证据不能再按 4 task 平均混讲，真正有信息量的主要是 `dureader`，`lcc` 次之，`trec/vcsum` 只保留作边界披露 | `results/phase2_batch4_extend_tasks_7b/` + `results/phase2_batch5_extend_tasks_8b/` + [docs/phase2_data_mainline_audit_20260419.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_data_mainline_audit_20260419.md) | candidate-main |
| **K/V asymmetric allocator** | 升级为下一阶段主升级候选 | 当前项目已具备 `k_bits/v_bits` 路由、MixedKV 执行路径与 `K > V` 诊断资产，且 L2 v1 本地脚本链已完成并通过最小验证；下一步是单独起 launch plan | `src/engine/generate_loop.py` + `src/cache/mixed_kv_cache.py` + `docs/behavior_guided_allocation_roadmap.md` + `scripts/phase2_l2_kv_asymmetric.sh` | scripts-ready / waiting-launch |
| **Quality-cost Pareto analysis** | 升级为下一阶段实验组织候选 | 当前 allocator 线主要比较 task quality；若要把 allocation 提升为预算分配方法，必须联合纳入 latency、memory、PPL、Needle 等 cost 维度；L2 通用 runner 与聚合脚本已就位 | `scripts/profile_latency.py` + `scripts/profile_memory.py` + `scripts/eval_ppl.py` + `scripts/eval_needle.py` + `scripts/phase2_l2_pareto_eval.sh` | scripts-ready / waiting-launch |
| **Prompt-adaptive allocation** | 升级为下一阶段策略层候选 | 相比 head-wise 改造，它更适合作为静态 allocator 稳定后的下一步：先做 policy-selection 层的 prompt/task/profile-aware 控制；MVP selector 与 runner 已准备好 | `docs/behavior_guided_allocation_roadmap.md` + `scripts/adaptive/build_prompt_policy_pool.py` + `scripts/phase2_l2_prompt_adaptive.sh` | scripts-ready / waiting-launch |
| **Mistral family = wide-budget profile evidence** | 升级为正文/附录中的新 supporting evidence 候选 | `Wave 5` 中 `auto_cov80` 对应的较宽预算区间拿到当前最好平均分，提示 family-specific profile 可能把高概率预算推到更宽位置 | `results/phase2_c4_mistral7b/` + `artifacts/allocator/sweep_mistral7b/*.json` | exploratory |

### 2.2 需要降级的内容

| 主题 | 调整 | 原因 | 证据来源 |
|---|---|---|---|
| **“behavior-guided allocation universally better”** | 明确降级 / 禁止继续写 | 已被 7B/8B 差异直接打破 | [docs/phase2_final_readout.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/phase2_final_readout.md) |
| **“best-k 随模型规模单调上移”** | 降级为已被证伪的旧叙事 | 8B 并不支持单调 scale-shift | 同上 |
| **“aggregation split 是一般规律”** | 降级为 7B-specific 现象 | 1.5B / 8B 都不支持普适表述 | 同上 |
| **“F2 扩任务 4/4 PASS”** | 降级为机械 gate 现象，不作强证据 | `trec/vcsum` 为 0 信息量任务 | 同上 |
| **“只按模型大小就能直接猜 k”** | 降级为过强直觉，不当主张 | 8B 新结果强化了“更大 budget 可能更好”，但当前更合理的是 profile-aware auto-k，而不是 size-only rule | `Wave 1` 8B 新结果 + 旧 cross-model 读数 |

### 2.3 需要保留的内容

| 主题 | 保留方式 | 说明 |
|---|---|---|
| **INT8 canonical path（calibration + kernel + generate loop）** | 保留为论文方法主干 | 仍是最干净、最核心的 validated instance |
| **MixedKV / allocator 作为框架扩展** | 保留，但定位为 conditional extension | 不抢方法主线，承担“框架的下游决策层”角色 |
| **Threats / scope disclosure** | 保留并增强 | 这是把论文从“会被追着问”变成“主动交代”的关键 |

### 2.4 需要放弃或暂缓的内容

| 主题 | 动作 | 原因 |
|---|---|---|
| 用当前 exploratory 结果直接改主表数字 | 放弃 | provenance 不够 clean |
| 把 `trec/vcsum` 当 allocator 证据继续讨论 | 放弃 | 信息量低，容易稀释主线 |
| 过早把 Mistral smoke 写成跨家族最终外部有效性 | 暂缓 | 需要 full sweep / clean rerun 支撑 |
| 用旧“pure scale-shift”图表支撑当前正文 | 放弃 | 叙事已过时 |

---

## 3. 图像资料更新计划

### 3.1 需要新增的图

| 图名（暂定） | 目的 | 数据依赖 | 位置建议 | 状态 |
|---|---|---|---|---|
| **Family Regime Map** | 一张图讲清 1.5B / 7B / 8B（未来加 Mistral）在 `k` 与 aggregation 上的 regime 差异 | Phase 2.5 + 2.6 allocator 结果 | `ch4` 主图候选 | 待设计 |
| **Phase 2.6 Upgrade Dashboard** | 把 `Wave 1/3/4/5/7a/7b/6` 的新证据和主线升级动作对应起来 | A 方案链结果 | `appendix` 或 internal-only | 待定 |
| **Provenance Ladder / Coverage Plan** | 清楚区分 exploratory → candidate-main → final-ready | provenance manifest + rerun plan | 附录 / rebuttal 备用 | 待设计 |
| **Wave 1 8B Policy Comparison** | 展示 `bakv_k9/k11`、`heuristic_k9/k11`、`bakv_mean_k3/k5/k7` 的分布差异 | `results/phase2_c2b_llama8b_extended/` | `ch4` 子图候选 | 数据已开始可用 |
| **Auto-K Range Proposer Schematic** | 解释如何从 sensitivity profile 自动提出 `70/80/90` coverage 候选区间，而不是手工 sweep 固定 `k` | [docs/auto_k_selector_experiment_plan.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/auto_k_selector_experiment_plan.md) | `ch3/ch4` 过渡图候选 | 待设计 |
| **Wave 5 Mistral Policy Comparison** | 展示 `bakv_auto_cov70/80/90`、`heuristic_k*`、`uniform` 在 Mistral full 上的排序关系，说明 auto-k 的首轮 empirical 支持与 heuristic 仍强 | `results/phase2_c4_mistral7b/` | `ch4` 子图候选 | 数据已可用 |

### 3.2 建议保留并更新的数据图

| 现有图 | 动作 | 说明 |
|---|---|---|
| `thesis/figures/main_quality_dashboard.pdf` | 保留，但后续需按 clean 数据刷新 | 仍适合作为总览 |
| `thesis/figures/main_efficiency_dashboard.pdf` | 保留，但需同步主线口径 | 与主实验结构仍兼容 |
| `thesis/figures/pareto_quality_efficiency.pdf` | 保留，后续检查是否要加 provenance 注释 | 仍能服务“效率-质量折中” |
| `thesis/figures/rolealign_summary.pdf` | 暂保留，等待新主线权重再决定位置 | 可能从主文降到附录 |

### 3.3 建议放弃或降级的旧图

| 图 / 旧叙事 | 动作 | 原因 |
|---|---|---|
| 任何隐含“best-k 单调随规模上升”的图 | 放弃 | 与最新证据冲突 |
| 任何把 aggregation split 写成普适规律的图 | 降级或重画 | 只能保留 7B-specific 版本 |
| 只靠 `trec/vcsum` 0=0 支撑的扩任务图 | 放弃进入主文 | 信息量不足 |

---

## 4. 本轮最新数据如何影响文章主线

### 4.1 已经发生的升级

1. **Smoke 结果通过**
   - 含义：Mistral-7B 上 `int8_ours` 现在可以稳定运行
   - 对文章的意义：提升“工程链已修复”的可信度
   - 但当前只应写成：
     - `engineering sanity passed`
     - 不是 final cross-family claim

2. **Wave 1 已完成（21/21）**
   - 含义：8B extended sweep 的核心数据正在补齐
   - 对文章的意义：
     - 现在不只是“8B 属于哪种 regime”的问题
     - 还引入了一个更强的新问题：**固定手工 `k` 是否应该被升级为 auto-k / auto-budget 机制**
   - 当前新证据：
     - `bakv_k11`（avg=9.52）目前优于 `bakv_k9`（8.57）与 `heuristic_k11`（8.54）
     - 这**增强了**“8B 上更大 budget 可能更好”的直觉
     - 但它与旧版 `phase2_final_readout` 中“8B 弱 low-budget 偏好”的结论存在张力，说明 **8B 证据正在被重估，不能简单收束回旧叙事**
   - 当前最稳的写法：
     - 不恢复“单调 scale-shift”
     - 改写成：**8B 扩展 sweep 显示 fixed-k 口径不稳，值得转向 profile-aware auto-k 选择**

3. **Wave 3 已完成（24/24）**
   - 含义：7B random multi-seed 的稳健性证据已经补齐到当前阶段
   - 对文章的意义：
     - 7B 这条线不再只是“已启动的待定项”
     - 现在可以把它作为章节草稿中的稳定支点之一来写，但仍保持 `exploratory` 口径

4. **Wave 4 已完成（36/36）**
   - 含义：14B 已经给出完整的 cross-scale supporting evidence
   - 当前直接信号：
     - `uniform_int4_k4v4` 当前平均分最高
     - `heuristic_k3 / heuristic_k7` 仍然非常强
     - `bakv_k7 / bakv_k5` 没有形成“大模型固定大 `k` 更优”的稳定结论
   - 对文章主线的意义：
     - 14B 进一步强化了 **family-specific regime**
     - 同时再次说明 **heuristic / uniform 不能被当弱 baseline 处理**

5. **Wave 5 已完成（45/45），并给出 auto-k 的首轮完整 empirical 支持**
   - 含义：Mistral-7B full sweep 已经完成，并且这是第一波完整纳入 `bakv_auto_cov70/80/90` 的 full empirical comparison
   - 当前新证据：
     - `bakv_auto_cov80_max` = **14.7640**，当前全局平均分第一
     - `gov_report` 与 `hotpotqa` 的 task-best 都来自 `bakv_auto_cov80_max`
     - 但 `narrativeqa` 的 task-best 仍然是 `heuristic_k3` = **17.1133**
   - 对文章主线的意义：
     - 现在可以更有把握地写：**auto-k 已具备第一批完整 empirical 正面证据**
     - 但仍不能写成：**auto-k 已经普遍优于 fixed best-k / heuristic**
     - 更稳的表述是：
       - **Mistral 为 profile-aware budget range proposer 提供了第一批完整支持**
       - **同时继续支持 heuristic 作为强 baseline、task-dependent regime 仍然存在**

6. **Auto-k range proposer 已从实验设计升级为已进入实验链的扩展能力**
   - 含义：allocator 这条线不再只停留在“固定手工 `k` 的 sweep 解释”
   - 当前本地已实现，并已在远端吃到：
     - `bakv_auto_cov70_max`
     - `bakv_auto_cov80_max`
     - `bakv_auto_cov90_max`
   - 当前已完成 auto-k backfill 的关键波次包括：
     - `Wave 1`
     - `Wave 4`
   - 对文章主线的意义：
     - 现在可以正式把“从 fixed-k sweep 升级到 profile-aware budget range proposer”写成方法扩展方向
     - 但最终价值仍需依赖 `Wave 1 + Wave 4` 统一 readout 与 clean provenance 进一步确认

7. **Wave 7a 已完成，且 extend-task 证据继续表现为“部分任务有信息量、部分任务长期 floor”**
   - 含义：7B extend tasks 已经完成全部 36 条结果，并完成了从 `dureader / trec / vcsum` 到 `lcc` 的扩展验证
   - 当前直接信号：
     - `dureader` 仍然是当前最有信息量的 extend task
     - `trec / vcsum` 继续接近 floor，仍不适合作 allocator 强证据
     - `lcc` 已经提供了额外 task 维度，但当前整体仍不足以把 extend-task 结果升级成 allocator 主结论
     - `auto-k` 已明确进入 `Wave 7a`，但当前并未形成足以改变主线的跨任务强信号
   - 对文章主线的意义：
     - `Wave 7a` **没有推翻**“extend tasks 中只有一部分任务具备 allocator 区分度”的判断
     - 它更像是在扩大验证范围，而不是立即改变主线
     - 更稳的写法仍然是：
       - `dureader` 作为 extend-task allocator 证据保留
       - `trec / vcsum` 继续按 low-information tasks 处理
       - `lcc` 作为补充 task 保留，但在 clean 覆盖前不提升 extend-task 线的正文权重

8. **Wave 7b 已启动并进入 `lcc`，但当前仍主要复现 8B extend-task 的低信息量结构**
   - 含义：8B extend tasks 已从 `dureader / trec / vcsum` 推进到 `lcc`，当前已有 34 条 summary 落盘
   - 当前直接信号：
     - `dureader` 仍然是当前主要的信息量来源
     - `trec / vcsum` 在 8B extend tasks 中继续长期贴近 floor
     - `Wave 7b` 当前已进入 `lcc` 尾批，说明 extend-task 扩展验证仍在进行
   - 对文章主线的意义：
     - `Wave 7b` 目前并没有生成新的 allocator 强证据
     - 它更多是在复现：**extend tasks 的信息量高度不均衡**
     - 当前更适合把它写成“补强任务分层判断”的 supporting evidence，而不是 allocation 主 finding

### 4.2 当前主线升级建议（一句话版本）

> 论文主线应从“某种 allocator 普遍优于 baseline”升级为：  
> **behavior-guided allocation reveals family- and scale-specific operating regimes, with positional heuristic remaining a strong baseline and no single `(k, aggregation)` generalizing across model families.**

> 如果 8B 新证据和后续 14B / Mistral 继续支持“更大模型倾向需要更大 budget”，则更进一步的升级方向不是恢复 `pure scale-shift`，而是：
> **replace hand-picked fixed-k with a profile-aware automatic budget range proposer.**

---

## 5. 下一轮更新时必须回答的问题

1. `Wave 1 + auto-k backfill` 完整后：
   - 8B 更像 1.5B 模式、7B 模式，还是第四种新 regime？
   - `bakv_k11` 的领先是稳定信号，还是扩展 search space 下的局部最优？
2. `Wave 3` 已完成后：
   - 7B split regime 在写作上应提升到什么等级：`supporting evidence` 还是 `strongest finding`？
3. `Wave 5` 既然已经完成：
   - Mistral 更像“宽预算 family”，还是只是当前一轮中 `auto_cov80` 的局部最优？
   - `bakv_auto_cov80_max` 的领先在 clean rerun 下是否还能保留？
4. `Wave 4 + auto-k backfill` 完整后：
   - 14B 会强化“更大 budget 可能更好”的直觉，还是把主线重新拉回 family-specific explanation？
5. `Wave 7b` 中的 `lcc` 完整后：
   - `lcc` 是否在 8B extend tasks 上提供新的 allocator 区分度，还是继续复制“弱区分”格局？
   - `bakv_k11 / auto-k / heuristic` 在 `lcc` 上是否出现更稳定的排序关系？
6. `Wave 7a / 7b / 6` 完整后：
   - auto-k 在 extend tasks 和更小模型上的表现，是支撑“方法扩展”还是只支撑“Mistral-specific evidence”？
   - extend tasks 是否应继续作为 allocator 主证据，还是更多承担 scope / boundary 说明角色？
7. 当前 `candidate-main` 口径下，哪一组 compare set 最值得优先 clean 覆盖：
   - `3B`: `bakv_k1 / heuristic_k1 / auto_cov80 / uniform_int8`
   - `8B`: `bakv_k11 / heuristic_k11 / auto_cov80`
   - `14B`: `uniform_int4 / heuristic_k3 / auto_cov90`
   - `Mistral`: `auto_cov80 / heuristic_k3 / uniform_int8`
8. 三条 `L2` 升级方向里，应该按什么顺序推进：
   - `K/V asymmetric allocator`
   - `Quality-cost Pareto analysis`
   - `Prompt-adaptive allocation`
9. 什么时候把某条结论从 `exploratory` 升级为 `candidate-main`？
10. `auto-k range proposer` 是否能把“固定手工 k”的 sweep 问题升级成真正的方法贡献？
11. 哪一张新图最先值得投入绘制：
   - `Family Regime Map`
   - `Wave 1 8B Policy Comparison`
   - `Wave 5 Mistral Policy Comparison`
   - `Provenance Ladder`
   - `Auto-K Selector Schematic`

---

## 6. 维护协议

每轮关键实验完成后，按以下顺序更新本文件：

1. 更新 **0. 当前快照**
2. 更新 **4. 本轮最新数据如何影响文章主线**
3. 如果结论发生变化，更新：
   - **1. 主线升级位置总表**
   - **2. 内容优先级调整**
   - **3. 图像资料更新计划**
4. 若某条结论进入 clean rerun 支撑，调整其 provenance 等级：
   - `exploratory` → `candidate-main` → `final-ready`

---

## 7. 当前版本的工作结论

**现在不要急着改论文正文。**  
当前正确顺序应当是：

1. 先用这份文档持续组织 **已完成的 Phase 2.6 exploratory 证据**
2. 把章节级修改点和草稿块维护在本工作台内部
3. 等 `Wave 6` 正式 readout、clean-provenance 覆盖验证，及 `L2` 首轮 exploratory 结果更明确后，再决定哪些内容迁入正式正文

在那之前，不直接修改：

- [thesis/chapters/ch1_introduction.tex](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch1_introduction.tex)
- [thesis/chapters/ch3_method.tex](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch3_method.tex)
- [thesis/chapters/ch4_experiments.tex](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex)
- [thesis/chapters/ch5_conclusion.tex](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch5_conclusion.tex)

在那之前，allocator 这条线最值得先推进的不是“再把 fixed-k 叙事讲圆”，而是：

1. 把 **3B / 8B / 14B / Mistral** 四条线的差异和 unified auto-k 结论写清楚
2. 记清楚 **auto-k 当前实现状态、4-model supporting evidence 与 clean-provenance 边界**
3. 跟进 **extend-task** 对证据等级的影响，特别是 `dureader / lcc / trec / vcsum` 的新角色分工
4. 把 `objective.md` 中的 **L2 三条方向** 作为下一阶段升级候选单独管理，并明确本地脚本已 ready：
   - `K/V asymmetric allocator`
   - `Quality-cost Pareto analysis`
   - `Prompt-adaptive allocation`
5. 下一步先单独起 **L2 launch plan**，再决定远端启动顺序
6. 把 **章节修改草稿** 继续写在工作台里
7. 再看它是否值得升级为 `ch3/ch4` 的方法扩展

### 7.1 与 `objective.md` 的当前对齐

本工作台现在应当与新的 [objective.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/objective.md) 保持如下对齐：

- `L0`：Behavior + INT8 canonical path
- `L1`：Layer-wise allocation / Auto-k / cross-model regime reading / theory lane
- `L2`：K/V asymmetric allocator / Pareto analysis / Prompt-adaptive allocation
- `L3`：Head-wise / learned allocator / reasoning / serving

其中：

- 本工作台当前主要维护 `L1`
- 同时为 `L2` 准备升级入口
- 暂不把 `L2` 或 `L3` 直接写成正文既成事实

当前区别于 `objective.md` 的**默认执行顺序**，已单独固定在：

- [docs/mainline_execution_queue.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/mainline_execution_queue.md)

当前默认推荐顺序是：

1. 把 formal audit 的结论正式吸收入工作台与 readout 体系
2. 固化 cross-4-model auto-k 的 `candidate-main` 口径
3. 明确 clean-provenance rerun 的 claim-critical compare set
4. 单独起 `L2` launch plan，明确远端启动顺序与 GPU 占用
5. 再按 `K/V asymmetric allocator -> Pareto analysis -> Prompt-adaptive allocation` 的顺序推进 `L2`

---

## 8. 章节修改准备区（仅在工作台维护，暂不写入 thesis/）

| 章节 | 当前建议 | 具体修改位置 | 当前可写程度 | 写入门槛 |
|---|---|---|---|---|
| `ch1_introduction` | 增加“allocator 是 family-/scale-/task-dependent 决策问题”的动机段 | 问题定义与研究动机；主要贡献结尾 | 可以先写草稿 | 不直接写入 `thesis/`，等主线再稳定一轮 |
| `ch3_method` | 增加“profile-aware budget range proposer（扩展）”小节 | 方法总览之后，作为 extension subsection | 可以先写草稿 | 等 `Wave 5 + backfill` 一起形成更稳的 empirical 支撑 |
| `ch4_experiments` | 新增 `family-specific regimes` 与 `fixed-k → auto-k` 两块 | 基线方法；主实验结果后；扩展讨论区 | 应该现在就起草 | 等 `Wave 7a / 7b / 6` 与 backfill 更完整后再迁正文 |
| `ch5_conclusion` | 把收束从“普适更优”改成“框架有效但配置依赖 regime” | 核心结论段；未来工作段 | 可以先写草稿 | 等 `candidate-main` 结论更明确 |

### 8.1 本轮写作边界

- 允许写：
  - 结构性改写方向
  - 章节段落草稿
  - 图像说明草稿
- 暂不写：
  - 最终主表数字
  - `Wave 5` 的 final-ready claim
  - `Wave 7a / 7b / 6` 尚未完成时的跨任务泛化 claim
  - “auto-k 已优于 fixed best-k”的最终表述

---

## 9. 章节草稿块（仅在工作台维护，暂不写入 thesis/）

> 说明：以下内容是**章节级草稿块**，用于后续迁入正式正文。  
> 当前阶段只在工作台中维护，不直接写入 `thesis/chapters/*.tex`。

### 9.1 `ch1_introduction` 草稿块

**建议插入位置 A（v2）**：问题定义与研究动机后半段

```tex
除校准目标与低比特失效机制之外，本文的后续实验进一步表明：行为引导的层级保护策略并不对应于单一的跨模型普适最优解。不同模型家族、参数规模与任务类型在保护层数及聚合方式上的偏好存在显著差异。这一现象意味着，KV Cache 量化中的 allocator 更应被理解为一个依赖模型行为 profile 的决策问题，而非一个能够通过固定超参数统一求解的配置问题。基于这一观察，本文在主框架之外进一步考察由 calibration profile 驱动的预算区间提议机制，以替代完全依赖手工 sweep 固定 $k$ 的实验范式。
```

**建议插入位置 B（v2）**：主要贡献结尾

```tex
除上述核心贡献外，本文还提出一条正在展开的方法升级方向，即将手工设定的保护预算 $k$ 提升为由行为 profile 自动提出的预算区间（budget range proposal）。该方向当前被定位为框架下游的扩展候选，旨在回答“对于不同模型家族与尺度，应当保护多少层”这一配置问题；其完整验证仍依赖后续实验结果。
```

### 9.2 `ch3_method` 草稿块

**建议新增小节标题**

```tex
\subsection{基于行为 profile 的预算区间提议器（扩展）}
```

**建议正文草稿（v2）**

```tex
在以固定保护层数 $k$ 为核心的预算 sweep 实验中，我们观察到最优预算并不具备稳定的跨模型一致性；甚至对于同一模型，扩大候选空间后也可能推翻先前的 best-$k$ 结论。基于这一现象，本文进一步引入一个由行为 profile 驱动的预算区间提议器（budget range proposer），作为框架下游的 policy-selection 扩展。

具体地，设第 $l$ 层的敏感度为 $s_l$，将其按降序排列为 $s_{(1)} \ge s_{(2)} \ge \cdots \ge s_{(L)}$。对给定 coverage 比例 $p \in (0,1]$，定义最小保护层数
\[
k_p = \min \left\{ k : \frac{\sum_{i=1}^{k} s_{(i)}}{\sum_{j=1}^{L} s_j} \ge p \right\}.
\]
本文并不直接输出单一的 $k$，而是针对若干 coverage 水平（例如 $p \in \{0.7, 0.8, 0.9\}$）输出对应的候选集合 $\{k_{0.7}, k_{0.8}, k_{0.9}\}$，并将 $k_{0.8}$ 作为推荐点。该设计的目标不是预先宣称唯一最优预算，而是在保持解释性的前提下，将原本依赖全局手工 sweep 的搜索空间压缩为一组高概率候选区间。
```

**边界声明草稿（v2）**

```tex
需要强调的是，该预算区间提议器属于行为对齐框架下游的 policy-selection 扩展，而非本文的 canonical validated instance。本文当前的主验证实例仍然是 INT8 行为对齐校准路径；预算区间提议器的角色在于补充 fixed-$k$ 实验范式，而不是替代主方法结论。
```

### 9.3 `ch4_experiments` 草稿块

**建议新增小节标题 A**

```tex
\subsection{行为引导分配的 family-specific regimes}
```

**建议正文草稿 A（v2）**

```tex
实验结果表明，行为引导的层级保护策略并不服从单一的跨模型普适规律。相反，不同模型家族与尺度在预算偏好、聚合方式敏感性以及相对于位置启发式基线的收益结构上表现出显著差异。换言之，allocator 的作用更接近 family-, scale-, and task-dependent 的 operating regimes，而非一个可以直接跨模型迁移的 universal law。

以 8B 扩展 sweep 为例，预算搜索空间扩大后，较大的保护预算开始显示出优势：在当前结果中，\texttt{bakv\_k11} 的平均分高于 \texttt{bakv\_k9} 以及同预算的 heuristic 基线。这说明早先基于较窄候选空间形成的 fixed-$k$ 判断并不稳定。与此同时，7B 上观察到的 aggregation split 现象仍然是当前最具结构性的 finding，而 1.5B 则更接近低预算下的局部稳健 regime。因而，更稳妥的实验总结并非继续追求单一最优 $k$，而是承认不同模型落在不同的 operating regimes 中，并据此重新组织 allocator 的解释框架。

这一判断在 Mistral-7B full sweep 中获得了进一步强化。最新结果显示，profile-aware 的 \texttt{bakv\_auto\_cov80\_max} 在当前 15 组 policy 中取得最高平均分，并在多个 core tasks 上表现最优；但与此同时，\texttt{heuristic\_k3} 仍然在 \texttt{narrativeqa} 上保持领先。这说明新的证据并未将主线重新拉回某种单一的 allocator law，而是进一步支持“不同 family 与任务落在不同 regime 中”的解释框架。
```

**建议新增小节标题 B**

```tex
\subsection{从固定预算 sweep 到自动预算区间提议}
```

**建议正文草稿 B（v2）**

```tex
固定手工 sweep 保护层数 $k$ 的实验范式至少存在两个局限。第一，不同模型之间的最优预算并不稳定，而且同一模型在扩大候选空间后也可能推翻既有的 best-$k$ 判断。第二，手工 sweep 更接近实验协议，而非可迁移的方法能力。基于这一观察，本文进一步引入一个 profile-aware 的自动预算区间提议器：它不直接预测唯一最优 $k$，而是根据 layer sensitivity profile 提出一组高概率候选预算，并将中间 coverage 对应的预算作为推荐点。

这一扩展的意义并不在于立即替代所有 fixed-budget 实验，而在于将原本依赖全局手工扫描的搜索问题收缩为局部高概率验证问题。Mistral-7B full sweep 的最新结果已经为这一方向提供了第一批完整 empirical 支持，但当前更稳妥的写法仍然是将其视为行为对齐框架下游的扩展能力，并继续与 hand-tuned best-$k$、heuristic same-budget 以及 random same-budget 进行对照，而不是提前将其表述为已经确立的最终方法形态。
```

### 9.4 `ch5_conclusion` 草稿块

**建议结论补段（v2）**

```tex
除上述核心发现外，本文的最新实验还提示：行为引导的层级保护并不表现为单一的跨模型普适规律，而更接近一组 family- and scale-specific operating regimes。换言之，allocator 的有效配置取决于模型 profile、任务类型与预算区间，而非一个能够跨模型直接迁移的固定超参数。基于这一观察，固定手工预算 sweep 更适合作为分析工具，用于揭示不同模型的 regime 结构，而不应被直接等同为最终的方法形态。最新的 Mistral-7B full sweep 进一步表明，profile-aware 的 budget range proposer 已经具备首轮 empirical 支持，但该支持仍应在 clean-provenance 与 backfill 条件下完成最终确认。
```

**建议未来工作补段（v2）**

```tex
一个直接的后续方向，是将固定预算 sweep 升级为 profile-aware 的自动预算区间提议器。相比依据模型参数量直接猜测保护层数，这一路径更强调由 calibration profile 驱动的预算决策，因此更有希望将 allocator 从经验性实验协议提升为可复用、可解释的方法能力。该方向当前已经在 Mistral-7B full sweep 上获得初步正面结果，并已补齐 `Wave 1 / Wave 4` 的 backfill；下一步需要通过统一 readout 与 clean-provenance 覆盖验证来确定其最终价值。
```
