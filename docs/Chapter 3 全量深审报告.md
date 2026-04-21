# Chapter 3 全量深审报告

## 0. 审查元信息

- 审查日期：`2026-04-22`
- 审查对象：[/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter 3 Draft.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter%203%20Draft.md:701) 中 `## 最终可回写正文块` 的 `3.1–3.8`
- 唯一裁决来源：
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter 3 Draft.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter%203%20Draft.md:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:1)
- 真实性核对来源：
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int8.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int8.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym_v2.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym_v2.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym_gqa.py](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym_gqa.py:1)
  - [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:1)

## 1. Round 0 基线

- 最终回写区包含 `8` 个 `\section{...}`，对应 `3.1–3.8`
- 当前 labels：
  - `sec:ch3-problem`
  - `sec:ch3-motivation-kv`
  - `sec:ch3-framework`
  - `sec:ch3-calibration`
  - `sec:ch3-paths`
  - `sec:ch3-allocator`
  - `sec:ch3-deployment`
  - `sec:ch3-summary`
  - `subsec:ch3-rolealign`
  - `subsec:ch3-rolealign-vs-kivi`
- 当前正文使用的外部 refs：
  - `sec:exp-kv-sensitivity`
  - `sec:exp-int4-cross-model`
- 当前基线结论：
  - 无 section / figure / table 跳号
  - 无零证据句段
  - 存在跨章引用、图表纪律、术语一致性与 repo 语义对齐冲突

## 2. 冻结 Readiness 结论

**整章当前状态：`不可冻结`**

原因不是“整章不可信”，而是 `3.1–3.8` 中仍有多处高优先级冲突未处理，尤其集中在：

- `3.1` 的反向公式引用 label 缺失
- `3.3` 的图 3-3 落位与 framework 图资产未同步
- `3.4` 的 `RoleAlign` 校准纪律与 artifact 口径强于真实实现
- `3.5` 的 `INT8` 静态 scale 公式与 cross-ref / KIVI 边界表述
- `3.6` 的表 3-3 仍是占位注释，policy family 未实体定义
- `3.7` 的 `INT4` kernel 语义与 artifact 量级公式失真
- 全章术语仍存在 4 类统一性冲突

### 2.1 分节状态

| 小节 | 当前状态 | 说明 |
|---|---|---|
| `3.1` | 必须改写后才能冻结 | 正文可用，但缺失 `eq:ch3-error-decomp` backward label |
| `3.2` | 有冲突待审批 | 正文主体可用；图 3-2 证据来源与第四章锚点口径未定 |
| `3.3` | 必须改写后才能冻结 | 图 3-3 落位错误，旧 framework 图资产未同步，收口句弱化 shared profile |
| `3.4` | 必须改写后才能冻结 | `RoleAlign` K/V 选择统计、artifact 字段、`inv_tau` 口径与 repo 有漂移 |
| `3.5` | 必须改写后才能冻结 | `INT8` static scale 公式过理想化，cross-ref 错误，KIVI 边界句有过度解释 |
| `3.6` | 必须改写后才能冻结 | 表 3-3 缺失实体内容；role-aware 例子与 repo 不完全同构 |
| `3.7` | 必须改写后才能冻结 | `INT4` Triton 语义泛化过头，artifact 量级公式低估，phase-boundary label 缺失 |
| `3.8` | 可冻结 | 内容边界正确；仅受全章术语统一建议影响 |

## 3. A. 全量冲突清单

说明：

- 本清单是去重后的 retained conflicts
- 未列出的正文段落，按本轮深审结论均可视为 `可冻结`
- 每条记录都保留了计划要求的固定字段

### F-001

- `finding_id`: `F-001`
- `round_id`: `R3`
- `agent_name`: `Cross-Ref-Consistency`
- `section_id`: `3.1`
- `paragraph_id`: `3.1.error-decomp`
- `claim_excerpt`: `输出误差可作如下精确的代数展开`
- `conflict_type`: `编号/格式冲突`
- `severity`: `HIGH`
- `story_ref`: `—`
- `writing_ref`: `—`
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter 3 Draft.md:742](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter%203%20Draft.md:742), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:348](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:348)
- `approval_needed`: `no`
- `recommended_action`: 在该公式块补 `\label{eq:ch3-error-decomp}`，否则第四章 `\eqref{eq:ch3-error-decomp}` 失效。

### F-002

- `finding_id`: `F-002`
- `round_id`: `R2+R3`
- `agent_name`: `Section-3.2 + Cross-Ref-Consistency`
- `section_id`: `3.2`
- `paragraph_id`: `3.2-P5`
- `claim_excerpt`: `本图必须是第 4.3.2 节完整证据的压缩视图`
- `conflict_type`: `编号/格式冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:225](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:225), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:355](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:355)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:678](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:678)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:345](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:345), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:659](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:659)
- `approval_needed`: `no`
- `recommended_action`: 删除硬编码 `4.3.2`；若图 3-2 压缩的是 K/V 机制诊断，应指向 `4.2.1 / sec:exp-kv-sensitivity`，不是 `4.3` regime-map。

### F-003

- `finding_id`: `F-003`
- `round_id`: `R2+R3`
- `agent_name`: `Section-3.2 + Cross-Ref-Consistency`
- `section_id`: `3.2`
- `paragraph_id`: `3.2-P5`
- `claim_excerpt`: `主纵轴为 Needle，RULER 仅作图注/脚注支持`
- `conflict_type`: `施工文档冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:225](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:225)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:707](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:707)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:418](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:418), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:558](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:558)
- `approval_needed`: `yes`
- `recommended_action`: 若继续以第四章现有证据为源，则应改成 `RULER 主图 + 其他证据支撑`；只有在第四章补出同源 Needle 版 K/V 消融图后，才能批准 `Needle 主纵轴`。

### F-004

- `finding_id`: `F-004`
- `round_id`: `R3`
- `agent_name`: `Cross-Ref-Consistency`
- `section_id`: `3.2`
- `paragraph_id`: `3.2-P3/P5`
- `claim_excerpt`: `完整的跨模型读数、逐任务结果与统计检验将在第 \\ref{sec:exp-kv-sensitivity} 节中统一给出`
- `conflict_type`: `结构/逻辑冲突`
- `severity`: `MEDIUM`
- `story_ref`: `—`
- `writing_ref`: `—`
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:234](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:234), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:345](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:345), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:659](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:659)
- `approval_needed`: `no`
- `recommended_action`: 拆分桥接口径：统计框架指向 `4.1.4`，K/V 机制消融指向 `4.2.1`，跨模型/逐任务读数指向 `4.3/4.4`。

### F-005

- `finding_id`: `F-005`
- `round_id`: `R1+R2`
- `agent_name`: `Writing-Spec-Arbiter + Section-3.3`
- `section_id`: `3.3`
- `paragraph_id`: `3.3-P6`
- `claim_excerpt`: `% 图 3-3 建议置于此处`
- `conflict_type`: `施工文档冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:234](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:234)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1064](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1064)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch3_method.tex:92](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch3_method.tex:92)
- `approval_needed`: `no`
- `recommended_action`: 图 3-3 必须前移到 `3.3-P2` 后、`3.3-P3` 前。

### F-006

- `finding_id`: `F-006`
- `round_id`: `R2`
- `agent_name`: `Section-3.3`
- `section_id`: `3.3`
- `paragraph_id`: `3.3-P7`
- `claim_excerpt`: `图 3-3 行为引导量化框架总览：校准与分配共享同一行为敏感度画像`
- `conflict_type`: `施工文档冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:234](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:234)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1144](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1144)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/fig_ch3_framework_overview.tex:77](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/fig_ch3_framework_overview.tex:77)
- `approval_needed`: `yes`
- `recommended_action`: 旧 framework 图资产仍混入 KL、路径实例与 Triton；若保留当前 caption，必须同步重画/替换图资产。

### F-007

- `finding_id`: `F-007`
- `round_id`: `R2+R3`
- `agent_name`: `Section-3.3 + Terminology-Consistency`
- `section_id`: `3.3`
- `paragraph_id`: `3.3-P8`
- `claim_excerpt`: `围绕同一 behavior-guided principle 展开的两层决策……系统层则负责把前两者固化为可执行的推理接口`
- `conflict_type`: `story 冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:53](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:53), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1043](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1043)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:583](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:583), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1143](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1143)
- `approval_needed`: `yes`
- `recommended_action`: 把中心对象收回为 `behavior sensitivity profile`，并把系统层描述弱化为“最终在系统落地中闭环”。

### F-008

- `finding_id`: `F-008`
- `round_id`: `R2`
- `agent_name`: `Section-3.4`
- `section_id`: `3.4`
- `paragraph_id`: `3.4-P11`
- `claim_excerpt`: `RoleAlign 的 K-path 用 robust P95 KL 选 p_K，V-path 用独立稳健统计选 p_V`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:248](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:248)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1537](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1537)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:953](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:953), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:814](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:814)
- `approval_needed`: `yes`
- `recommended_action`: 若以 repo 为准，应改为 `K-path 按 avg_kl 选 k_percentile，V-path 按 avg_weighted_output_mse 选 v_percentile`；若坚持 `robust P95`，需先补实现。

### F-009

- `finding_id`: `F-009`
- `round_id`: `R2`
- `agent_name`: `Section-3.4`
- `section_id`: `3.4`
- `paragraph_id`: `3.4-P12`
- `claim_excerpt`: `RoleAlign 仍共享“可行域约束 + 尾部稳健优先 + artifact 输出接口”`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:248](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:248)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1553](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1553)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1678](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1678), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:618](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:618)
- `approval_needed`: `yes`
- `recommended_action`: 降格为“统一的是 offline workflow 与 K/V 分角色 artifact interface；RoleAlign 当前实现不复用对称路径的 clip-feasible + P95-first 规则”。

### F-010

- `finding_id`: `F-010`
- `round_id`: `R1+R2`
- `agent_name`: `Repo-Truth-Arbiter + Section-3.4`
- `section_id`: `3.4`
- `paragraph_id`: `3.4-P13`
- `claim_excerpt`: `artifact 包括 static scale / zero-point / percentile / group metadata / 保护参数`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:248](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:248)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1559](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1559)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1735](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1735), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1781](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1781), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:780](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:780), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1019](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1019)
- `approval_needed`: `no`
- `recommended_action`: 对称路径应写 `k/v_scale + clip/group metadata + inv_tau + rescue flags`；RoleAlign 应写 `k_percentile + v_percentile + inv_tau (+ search_results)`；不要把 `zero-point` 写成持久化 calibration artifact 常驻字段。

### F-011

- `finding_id`: `F-011`
- `round_id`: `R2`
- `agent_name`: `Section-3.4`
- `section_id`: `3.4`
- `paragraph_id`: `3.4-P15`
- `claim_excerpt`: `inv_tau 已降格为附录探索项，主线默认不依赖`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:237](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:237)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1568](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1568)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1757](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1757), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:844](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:844), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1037](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/generate_loop.py:1037)
- `approval_needed`: `yes`
- `recommended_action`: 收紧为“`inv_tau` 不是 3.4 统一 workflow 的必要前提，但当前 artifact 仍可记录该字段，且部分 low-bit 变体可显式启用”。

### F-012

- `finding_id`: `F-012`
- `round_id`: `R1+R2`
- `agent_name`: `Repo-Truth-Arbiter + Section-3.5`
- `section_id`: `3.5`
- `paragraph_id`: `3.5-P7`
- `claim_excerpt`: `s_static = Percentile(|x_{l,j}|; p_c) / q_max`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:259](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:259)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1727](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1727)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:766](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:766), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/cache/int8_cache.py:350](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/cache/int8_cache.py:350)
- `approval_needed`: `yes`
- `recommended_action`: 若要 strict repo 对齐，应写成“对样本级 group absmax 的 percentile”；若保留抽象公式，需要你批准“省略统计层级”。

### F-013

- `finding_id`: `F-013`
- `round_id`: `R1+R2+R3`
- `agent_name`: `Format-Numbering-Arbiter + Section-3.5 + Cross-Ref-Consistency`
- `section_id`: `3.5`
- `paragraph_id`: `3.5-P25`
- `claim_excerpt`: `第四章第 \\ref{sec:exp-int4-cross-model} 节中的对比结果`
- `conflict_type`: `编号/格式冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:272](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:272)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2205](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2205)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:582](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:582)
- `approval_needed`: `no`
- `recommended_action`: 把 `\ref{sec:exp-int4-cross-model}` 改成 `\ref{subsec:exp-int4-cross-model}`。

### F-014

- `finding_id`: `F-014`
- `round_id`: `R1+R3`
- `agent_name`: `Story-Arbiter + Cross-Ref-Consistency`
- `section_id`: `3.5`
- `paragraph_id`: `3.5-P24/P25`
- `claim_excerpt`: `对比结果才可以被解释为“在同一 role-aware format family 下，离线行为引导校准是否带来额外价值”`
- `conflict_type`: `story 冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:272](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:272)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2205](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2205)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:645](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:645)
- `approval_needed`: `yes`
- `recommended_action`: 降格为“用于观察同一 role-aware format family 下的整体表现差异”；若要声明“离线校准独立增益”，需先补 `pure-calibration / pure-format` 正交消融。

### F-015

- `finding_id`: `F-015`
- `round_id`: `R1`
- `agent_name`: `Story-Arbiter`
- `section_id`: `3.5`
- `paragraph_id`: `3.5-P24`
- `claim_excerpt`: `RoleAlign 不只是一个“选择了不同 percentile”的技巧，而是一套可向预算分配与系统落地自然延伸的 low-bit path`
- `conflict_type`: `story 冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:265](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:265)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2167](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2167)
- `repo_ref`: `—`
- `approval_needed`: `yes`
- `recommended_action`: 在 `3.5.4` 中只保留“同一 role-aware format family 下 calibration philosophy/interface 的分叉”，不要在 KIVI 边界节里提前把 RoleAlign 写成向 allocation / deployment 的延伸枢纽。

### F-016

- `finding_id`: `F-016`
- `round_id`: `R2`
- `agent_name`: `Section-3.6`
- `section_id`: `3.6`
- `paragraph_id`: `3.6-P13`
- `claim_excerpt`: `可分别定义 \\mathcal P_K / \\mathcal P_V 与两套 K/V 位宽`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:280](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:280)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2559](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2559)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:97](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:97), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:312](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:312), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:421](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:421)
- `approval_needed`: `yes`
- `recommended_action`: 若要 strict repo 对齐，应补一句“当前脚本实际按 `k_score/v_score` 排名后分配 `role_slots`”；若接受框架级示意，可经你审批后保留。

### F-017

- `finding_id`: `F-017`
- `round_id`: `R1+R2`
- `agent_name`: `Story-Arbiter + Section-3.6`
- `section_id`: `3.6`
- `paragraph_id`: `3.6-P23`
- `claim_excerpt`: `% 表 3-3 建议置于本小节末尾 / 表题：表 3-3 分配层策略的输入、选择规则与对应记号`
- `conflict_type`: `施工文档冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:507](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:507)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2812](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2812), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2857](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2857)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:140](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:140), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:243](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:243), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:486](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/adaptive/behavior_aligned_allocator.py:486)
- `approval_needed`: `no`
- `recommended_action`: 必须把表 3-3 真正写入最终回写区，至少冻结 `Uniform / BA-k / Heuristic-k / BA-AutoK` 的输入、规则、第四章记号与定位。

### F-018

- `finding_id`: `F-018`
- `round_id`: `R2`
- `agent_name`: `Section-3.7`
- `section_id`: `3.7`
- `paragraph_id`: `3.7.2-P3`
- `claim_excerpt`: `INT4 路径统一写成 kernel 内 nibble unpack 后复用同一流水线`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:3132](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:3132)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4.py:1](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4.py:1), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym.py:1](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym.py:1), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/patch_model.py:809](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/engine/patch_model.py:809)
- `approval_needed`: `no`
- `recommended_action`: 改成两类口径：对称 `INT4` 当前主实现是 wrapper 先 materialize 成 `INT8` 再复用 `INT8` kernel；非对称 `INT4` Triton 变体才是 kernel 内 unpack。

### F-019

- `finding_id`: `F-019`
- `round_id`: `R2`
- `agent_name`: `Section-3.7`
- `section_id`: `3.7`
- `paragraph_id`: `3.7.3-P3`
- `claim_excerpt`: `packed INT4 block bytes / AI 近似直接拿来解释“当前”融合路径`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:3283](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:3283)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4.py:1](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4.py:1), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym.py:1](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/kernels/triton_decode_attn_int4_asym.py:1)
- `approval_needed`: `yes`
- `recommended_action`: 若保留，应显式限定为“packed low-bit fused 理想路径 / 非对称 Triton 变体的近似解释”，不要写成当前对称 `INT4` wrapper 的精确成本。

### F-020

- `finding_id`: `F-020`
- `round_id`: `R1+R2`
- `agent_name`: `Repo-Truth-Arbiter + Section-3.7`
- `section_id`: `3.7`
- `paragraph_id`: `3.7.3-P4`
- `claim_excerpt`: `canonical artifact 规模写成 O(L d_k/g)；RoleAlign 主要是低维参数`
- `conflict_type`: `仓库真实性冲突`
- `severity`: `HIGH`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:133)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:3283](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:3283)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1778](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/calibrate_behavior.py:1778), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/cache/int8_cache.py:93](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/src/cache/int8_cache.py:93)
- `approval_needed`: `no`
- `recommended_action`: 至少改成 `O(L H_{kv} d_k/g)` 级别，并说明 persisted `RoleAlign` payload 还包含 `inv_tau/search_results`；若只谈 runtime-essential payload，需显式排除审计字段。

### F-021

- `finding_id`: `F-021`
- `round_id`: `R3`
- `agent_name`: `Cross-Ref-Consistency`
- `section_id`: `3.7`
- `paragraph_id`: `3.7.structure-gap`
- `claim_excerpt`: `所有关于 TPOT、性能交叉边界……统一留到第四章的部署效率小节讨论`
- `conflict_type`: `编号/格式冲突`
- `severity`: `HIGH`
- `story_ref`: `—`
- `writing_ref`: `—`
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:929](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch4_experiments.tex:929)
- `approval_needed`: `no`
- `recommended_action`: 恢复一个承接 phase-boundary 理论的子小节并保留 `\label{subsec:ch3-phase-boundary}`，否则第四章反向引用断裂。

### F-022

- `finding_id`: `F-022`
- `round_id`: `R3`
- `agent_name`: `Terminology-Consistency`
- `section_id`: `3.3`
- `paragraph_id`: `3.3-P1`
- `claim_excerpt`: `behavior-guided quantization framework`
- `conflict_type`: `结构/逻辑冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:39](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:39), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:53](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:53)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1237](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1237), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1249](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1249)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/objective.md:57](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/objective.md:57)
- `approval_needed`: `no`
- `recommended_action`: 框架短名统一为 `behavior-guided framework`；若需全称，只在首次出现时写 `behavior-guided quantization-and-allocation framework`。

### F-023

- `finding_id`: `F-023`
- `round_id`: `R3`
- `agent_name`: `Terminology-Consistency`
- `section_id`: `3.3 / 3.4 / 3.8`
- `paragraph_id`: `3.3-P2 / 3.3-P4 / 3.3-P6 / 3.4.2-P4 / 3.8-P2`
- `claim_excerpt`: `逐层行为敏感度画像 / layer-level sensitivity profile / 同源 sensitivity profile`
- `conflict_type`: `结构/逻辑冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:127](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:127), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:234](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:234)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:890](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:890), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:919](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:919), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1249](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1249)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter 3 Draft.md:83](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter%203%20Draft.md:83)
- `approval_needed`: `no`
- `recommended_action`: 正式名统一为 `behavior sensitivity profile`；首次可写 `behavior sensitivity profile（行为敏感度画像）`，后文不再混用其他别名。

### F-024

- `finding_id`: `F-024`
- `round_id`: `R3`
- `agent_name`: `Terminology-Consistency`
- `section_id`: `3.3 / 3.4`
- `paragraph_id`: `3.3-P3 / 3.3-P6 / 3.4-P2`
- `claim_excerpt`: `INT8 规范路径 / 低比特 role-aware 路径`
- `conflict_type`: `结构/逻辑冲突`
- `severity`: `MEDIUM`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:40](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:40), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:259](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:259), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:265](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:265)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1669](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1669), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:1737](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:1737)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter 3 Draft.md:664](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter%203%20Draft.md:664)
- `approval_needed`: `no`
- `recommended_action`: 路径对统一写成 `INT8 canonical path` 与 `INT4-RoleAlign`；类别表达只作为补语，不作为正式名。

### F-025

- `finding_id`: `F-025`
- `round_id`: `R3`
- `agent_name`: `Terminology-Consistency`
- `section_id`: `3.4 / 3.5 / 3.7`
- `paragraph_id`: `3.4.2-P3 / 3.5.3-P1 / 3.5.3-P4 / 3.5.3-P5 / 3.5.3-P6 / 3.5.4-P2 / 3.5.4-P3 / 3.7.3-P2 / 3.7.3-P4`
- `claim_excerpt`: `RoleAlign / INT4-RoleAlign`
- `conflict_type`: `结构/逻辑冲突`
- `severity`: `LOW`
- `story_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:265](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:265), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:272](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_story_20260420.md:272)
- `writing_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2001](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2001), [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This is Chapter 3 Writing.md:2205](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/This%20is%20Chapter%203%20Writing.md:2205)
- `repo_ref`: [/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter 3 Draft.md:665](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/Chapter%203%20Draft.md:665)
- `approval_needed`: `no`
- `recommended_action`: 统一回写为 `INT4-RoleAlign`；若坚持简称，需首次显式声明“下文简称 RoleAlign”，并全章一致。

## 4. B. 待你审批清单

以下项目不应由我静默裁决，需要你明确拍板：

1. **图 3-2 的证据主轴**
   - 选项 A：批准 `Needle 主纵轴，RULER 只作脚注/图注`
   - 选项 B：按当前第四章现有资产，改成 `RULER 主图`
   - 影响：决定 `3.2-P5` 与第四章 `4.2/4.3` 的图证据耦合方式

2. **3.3 收口中心对象**
   - 选项 A：严格回到 `behavior sensitivity profile`
   - 选项 B：保留 `behavior-guided principle` 的更泛化说法
   - 影响：决定 `3.3-P8` 是否仍以 shared profile 为第三章中轴

3. **RoleAlign 在 3.4 的真实口径**
   - 选项 A：正文完全按 repo 写：`K-path=avg_kl`，`V-path=avg_weighted_output_mse`
   - 选项 B：保留更强的 `robust P95` 叙述，并后续补实现
   - 影响：决定 `3.4-P11/P12` 是否是正文漂移还是待实现目标

4. **`inv_tau` 的主线定位**
   - 选项 A：写成“不是 workflow 必要前提，但 artifact 可记录，部分变体可启用”
   - 选项 B：继续写成“主线默认不依赖”
   - 影响：决定 `3.4-P15` 是否严格贴 repo 还是优先贴冻结写作口径

5. **`3.5-P7` 的 `INT8` static scale 公式**
   - 选项 A：收紧成“sample-level group absmax 的 across-sample percentile”
   - 选项 B：保留当前抽象公式，并接受“省略统计层级”
   - 影响：决定 `3.5.1` 是 schematic 还是 implementation-faithful

6. **`3.5.4` 是否可以把 RoleAlign 写成向 allocation/deployment 自然延伸**
   - 选项 A：不可以；KIVI 边界节只谈 calibration philosophy/interface
   - 选项 B：可以保留扩展性一句
   - 影响：决定 `3.5-P24/P25` 是否触发 story 侧越界

7. **`3.6-P13` 的 role-aware allocator 例子**
   - 选项 A：补一句当前 repo 实际按 `role_slots + combined ranking`
   - 选项 B：保留抽象 dual-mask 示例
   - 影响：决定 `3.6` 是框架示意优先还是 strict repo 同构优先

8. **`3.7.3-P3` 的低比特 AI / bytes 公式**
   - 选项 A：显式限定为 ideal fused / asym Triton 近似解释
   - 选项 B：删去对 `INT4` 当前实现的直接解释
   - 影响：决定 `3.7` 理论开销节是否继续携带 low-bit fused 理想路径近似

## 5. C. 可直接冻结清单

### 5.1 完全通过的整节

- `3.8`：三段均可冻结

### 5.2 可直接冻结的正文主体

除 `A. 全量冲突清单` 中明确点名的段落/图注/公式块之外，其余正文段落均已通过本轮深审，可视为：

- 与 `story` 主线不冲突
- 与 `This is Chapter 3 Writing` 的职责切分不冲突
- 在当前仓库中有可追溯锚点

### 5.3 证据覆盖结论

- `3.1–3.8`：**无零证据句段**
- 这意味着当前问题不是“幻觉泛滥”，而是：
  - 口径强于 repo
  - cross-ref / label 漏洞
  - 图表资产与冻结 caption 未同步
  - 全章术语未完全统一

## 6. D. 覆盖摘要

### 6.1 去重后 retained conflicts

- 总数：`25`
- 其中高优先级（`HIGH`）：`11`
- 中优先级（`MEDIUM`）：`11`
- 低优先级（`LOW`）：`3`

### 6.2 按类型统计

| 类型 | 数量 |
|---|---:|
| `仓库真实性冲突` | 10 |
| `施工文档冲突` | 4 |
| `编号/格式冲突` | 5 |
| `story 冲突` | 3 |
| `结构/逻辑冲突` | 3 |

### 6.3 审查覆盖说明

- Round 0：完成段落索引、labels/refs 索引、claim ledger 基线
- Round 1：完成 6 个横向 agent 的全章扫描
- Round 2：完成 `3.1–3.8` 全部 section agent 逐段审查
- Round 3：完成术语一致性、cross-ref 一致性、零证据句段审查
- Round 4：本报告为主控汇总结果

## 7. 最终判断

当前第三章的最终判断是：

- `哪些段落完全可信`
  - 除冲突清单点名处外，其余段落均可信
- `哪些段落冲突但由你决定`
  - 见 `B. 待你审批清单`
- `哪些段落必须重写`
  - `3.1.error-decomp`
  - `3.3-P6`
  - `3.4-P13`
  - `3.5-P25`
  - `3.6-P23`
  - `3.7.2-P3`
  - `3.7.3-P4`
  - 以及所有必须随之同步的 cross-ref / 术语 / 图注位置修订

在这些项处理完成前，第三章不应被视为最终稿，也不应直接回写到 `thesis/chapters/ch3_method.tex`。
