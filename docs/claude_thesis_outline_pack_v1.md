# Claude 论文写作大纲包 v1

> 文档定位：**面向 Claude 的中文论文写作控制包**
>
> 本文件不是论文正文，不是实时工作台，不是实验审计报告，也不是 LaTeX 迁移说明。  
> 它的唯一用途是：**为 Claude 提供一套足够强、足够细、足够稳的中文论文写作约束，使其能够按新的主线直接生成正文，而不再滑回旧叙事。**

---

## 0. 使用方式

### 0.1 这份文件解决什么问题

当前项目已经完成了主线重构，但现有材料分散在：

- `objective.md`
- `docs/freeze_20260419.md`
- `docs/thesis_upgrade_live_plan.md`
- `docs/mainline_execution_queue.md`
- `docs/clean_rerun_20260419T09/readout_final.md`
- `docs/clean_rerun_20260419T09/completion_report_20260419.md`
- `docs/phase2_data_mainline_audit_20260419.md`
- `docs/behavior_mainline_reframing_memo.md`
- `docs/thesis_rewrite_blueprint_v1.md`

这些文件足以支撑内部判断，却不适合直接喂给 Claude 去写论文正文。  
其中，`objective.md` 负责高层 mission 与边界，frozen state 与 clean rerun readout 负责当前运行时真相，本文件则负责把二者转成可直接驱动正文生成的写作控制项。  
Claude 如果直接基于这些内部文件写作，很容易出现三类偏差：

1. 写成“内部工作台说明文”
2. 回滑到旧的 superiority 主线
3. 继续把 `AutoK` 写成全文主角

本文件的作用就是避免这三类偏差。

### 0.2 Claude 应如何使用本文件

Claude 应将本文件视为：

1. **总主线约束**
2. **章节结构蓝图**
3. **论证动作清单**
4. **图表/数据绑定表**
5. **禁写清单**

Claude 的输出目标不是“总结这个文件”，而是：

> 按本文件规定的主线、结构、证据和边界，直接写出中文论文正文。

### 0.3 本文件不做什么

- 不替代正文
- 不替代 LaTeX
- 不提供 BibTeX
- 不提供最终图表文件
- 不替代当前 frozen canonical source
- 不在这里写死尚未冻结为权威引用的具体数字

### 0.4 Frozen Source-of-Truth Priority

Claude 在使用本文件前，必须先接受以下权威优先级，不得反向用旧 readout 或旧 planning 文档覆盖。

#### 第一优先级：冻结事实源

- `docs/freeze_20260419.md`
- `docs/thesis_upgrade_live_plan.md` 的 `0'' Frozen State`
- `docs/clean_rerun_20260419T09/readout_final.md`
- `docs/clean_rerun_20260419T09/completion_report_20260419.md`

#### 第二优先级：当前 frozen results

- `results/clean_rerun_20260419T09/`
- `results/l2_kv_asymmetric/`
- `results/l2_pareto/`
- `results/l2_prompt_adaptive/`

#### 第三优先级：操作性工作台 / queue

- `docs/mainline_execution_queue.md` 的 `0'' Freeze Update`

这一层只负责承载执行更新与排程状态，**不得反向覆盖第一优先级中的冻结事实**。

#### 仅作历史参考，不得覆盖 frozen facts

- `docs/phase2_final_readout.md`
- 旧 audit / 旧 readout / 旧 planning 文档

如果 frozen state 与旧 readout、旧工作台或更早期 planning 发生冲突，**一律以 frozen state 与 clean rerun readout 为准**。

同时，`frozen`、`exploratory positive support`、`off-protocol`、`supporting regime case` 等标签是**控制包内部证据标签**。Claude 在正文里必须把它们翻译成正常论文语言，而不是原样输出。

---

## 1. 论文总主线

### 1.1 一句话总主张

本文不是一篇证明某个单点量化方法普适更优的论文，而是一篇以**注意力行为**为统一分析与设计原则、以 **INT8 规范验证路径**建立主验证链、再通过跨模型实验支持将 **KV 分配**写成随模型家族、模型规模和任务类型变化的分区结构，并将 **auto-k** 写成框架下游预算建议扩展的论文。

### 1.2 三层结构

全文应始终围绕以下三层结构展开：

1. **原则层**
   - 行为是 KV Cache 量化里更合适的统一分析对象
2. **框架层**
   - 行为导向的思路同时组织校准与预算分配
3. **实例与扩展层**
   - INT8 是规范验证实例
   - allocator 结果揭示分区结构
   - auto-k 是下游扩展，而不是理论中心

### 1.3 全文逻辑链

正文必须按以下逻辑推进：

1. 长上下文推理的现实瓶颈是 KV Cache
2. 仅用数值误差组织量化研究已经不够
3. 真正应被保护和分析的是注意力行为
4. INT8 提供了一条最干净的规范验证路径
5. 一旦进入 allocator，现实更像分区结构而不是统一最优配置
6. 在 fixed-k 不稳的背景下，auto-k 作为预算建议扩展自然出现
7. 结论必须回到边界：当前支持 framework、canonical path、regime、extension，不支持 universal winner

### 1.4 全文主语是谁

全文的主语必须是以下四者之一：

- 本文框架
- 本文观察到的结构性现象
- 本文的实验结果
- 本文在当前证据边界内能够成立的结论

全文的主语**不能**长期变成：

- 审稿人可能会怎么问
- 当前工作台怎么说
- 我们为什么要改主线
- 旧论文哪里被击穿

这些内容只服务内部重构，不应大面积进入正文。

### 1.5 当前 frozen 支撑层级

Claude 在写正文时，必须按当前 frozen 状态区分三层证据：

1. **可进入正文主支撑的 5 条 frozen support**
   - Mistral-specific auto-k win
   - 3B early-layer rescue regime（限 QA tasks）
   - 14B top-tier but no stable winner
   - INT8 canonical path fidelity
   - heuristic is a strong baseline
2. **可进入正文次级支撑的扩展证据**
   - L2 Phase A（K/V asymmetric）作为 exploratory positive support / method-extension evidence
   - L2 Phase B（Pareto）作为 exploratory positive support / method-extension evidence
3. **只能写成 mixed / appendix / future-work seed 的内容**
   - L2 Phase C official（8B × 5 tasks × 3 variants ONLY）= weak / mixed
   - 1.5B / 7B Prompt-adaptive = off-protocol exploratory only
   - `lcc` strict win datapoint 只能作为 mixed evidence 中的局部正点

---

## 2. 旧叙事删除清单

以下内容必须从正文里彻底删除，不能以“弱化版”残留。

### 2.1 必删主张

1. `KL` 在 `INT8` 上普适优于 `MSE`
2. `RoleAlign` 在 `INT4` 上显著优于 `KIVI-style`
3. `behavior-guided allocation` 普适优于 heuristic / uniform / fixed-k
4. 存在一个可跨模型迁移的统一最佳 `k`
5. `best-k` 随模型规模单调上移
6. `auto-k` 是跨模型统一最优方法
7. 本文已经给出了最终发布级主表结论

### 2.2 必降级资产

以下内容不是不能出现，而是必须降级其角色：

1. **INT8**
   - 从“最重要方法胜利”降为“规范验证路径”
2. **INT4 RoleAlign**
   - 从“核心英雄方法”降为“低比特实例化与诊断延伸”
3. **heuristic**
   - 从“弱基线”改写为“强基线”
4. **auto-k**
   - 从“下一代主方法”降为“预算建议扩展”
5. **kernel 加速**
   - 从“并列第三贡献”降为“系统实现与部署支撑”

### 2.3 必删写法

正文中不得出现以下写法风格：

1. “当前最稳的写法是……”
2. “本节的安全读法是……”
3. “这里不能写成……”
4. “本线程/本工作台/本轮 audit 表明……”
5. “candidate-main / final-ready”
6. “strong extension / regime reading / canonical path”等内部控口径短语的大面积英文直用

这些概念可转化为论文语言，但不能原样搬进正文。

---

## 3. 全局写作规则

### 3.1 风格要求

Claude 必须按以下风格写：

- 中文学术论文风格
- 贴近原 thesis / 原 PDF 的句法与章法
- 以段落推进论证，而不是以工作说明推进
- 允许保留必要英文术语括注，但正文主体必须是中文

### 3.2 语言禁忌

不得写成以下风格：

1. 工作台说明文
2. 审稿 rebuttal 文
3. 英文论文的中文直译文
4. 蓝图注释稿
5. 大段“方法定位解释”而不真正进入论文论证

### 3.3 章节节奏要求

每章都应符合原 thesis 的基本节奏：

1. 先提出本章要解决什么问题
2. 再铺必要背景或方法
3. 再压核心论证
4. 最后以一段自然过渡收束到下一章

### 3.4 图表写法要求

图表在正文中必须像论文资产，而不是作者备忘录：

- 正文中写“如图 4-2 所示”“表 4-3 给出了……”
- 不写“图意”“建议内容”“caption 草稿”
- 图注应采用论文语气，而不是设计说明语气

### 3.5 数据写法要求

数字写入正文时必须满足：

1. 数字服务论证，而不是堆砌结果
2. 数字应嵌入具体句子，不要只孤立列出
3. 数字用于支撑现象，不用于制造 winner rhetoric
4. 任何具体数值都必须可回溯到当前 frozen source-of-truth；若控制包未写死数字，Claude 不得自行补写

### 3.6 正文术语白名单与映射表

| 内部/英文术语 | 正文优先写法 | 是否允许括注英文 | 使用说明 |
|---|---|---|---|
| behavior-centric framework | 以行为为中心的框架 / 以行为为统一分析对象的框架 | 可首次括注 | 不要反复直写 framework 口号 |
| behavior-aligned calibration | 行为对齐校准 | 首次可括注 | 正文主语应是校准过程或校准产物 |
| behavior-guided allocation | 行为引导分配 | 首次可括注 | 不要把它写成已被证明普适更优的方法名 |
| canonical path | 规范验证路径 | 不建议单独保留 | 仅用于解释 INT8 的论文角色 |
| regime reading | 分区结构读法 / 结构性经验读法 | 不建议保留 | 不要在正文里频繁出现 `regime` 原词 |
| strong extension | 有力扩展 / 强扩展能力 | 不建议保留 | 只用于描述 auto-k 的角色 |
| profile-aware budget proposer | 基于画像的预算建议机制 | 不建议保留 | 不要直接写英文 |
| calibration artifact | 校准产物 | 可不括注 | 强调可固化、可审计 |
| policy artifact | 策略产物 | 可不括注 | 强调预算路由的显式化 |
| compare set | 对比集合 | 不保留英文 | 只在边界说明中使用 |
| first-layer bottleneck / rescue | 首层瓶颈 / 首层恢复 | 首次可括注 | 仅作为 3B 异常现象标签使用 |

### 3.7 公式与技术对象最小清单

#### 第二章至少应出现的公式/对象

1. KV Cache 显存占用公式
2. 自注意力基本计算式
3. GQA 中 `H_q` 与 `H_{kv}` 的最小定义
4. 对称或非对称量化的最小数学表达

#### 第三章至少应出现的公式/对象

1. 行为对象的最小定义：注意力分布或行为偏移对象
2. 校准产物应包含的关键字段
3. 策略产物应包含的关键字段
4. auto-k 的最小定义：基于层敏感度覆盖率生成预算候选

#### 第四章原则

第四章不再重复堆公式，只在需要时回指：

1. 结果支撑的对象是什么
2. 图表中的量是什么
3. 数字对应哪一种结构判断

### 3.8 相关工作引用绑定表

| 小节 | 至少应绑定的工作 | 该节允许说什么 | 该节不能暗示什么 |
|---|---|---|---|
| 2.3 量化格式方向 | KIVI, AsymKV | K/V 非对称格式的重要性 | 本文提出了全新格式 |
| 2.4 校准信号方向 | MSE/percentile line, TensorRT-KL style references | 数值代理为何常见，行为对象为何值得引入 | 本文已证明行为目标普适优于数值目标 |
| 2.5 预算分配方向 | KVTuner, KVmix | allocation 是独立研究轴 | 本文首次提出 mixed-precision allocation |
| 2.6 相邻方向 | H2O, SnapKV, AhaKV, DuoAttention | attention-derived signal 可用于压缩决策 | 这些工作直接解决了本文的问题 |
| 2.7 本文定位 | 上述各线综合 | 本文连接校准与预算分配 | 本文覆盖并超越所有相关方向 |

---

## 4. 章节级强大纲

## 4.1 中文摘要

### 使命

用一个完整、紧凑、像论文的中文摘要，回答以下四个问题：

1. 为什么要研究 KV Cache 量化
2. 为什么本文要以行为为统一分析对象
3. 本文到底做了什么
4. 本文最终得出了什么边界明确的结论

### 必须包含的内容

1. 长上下文下 KV Cache 是显存与带宽瓶颈
2. 仅靠数值误差不足以解释行为退化
3. 本文把行为提升为统一分析与设计原则
4. INT8 是规范验证路径
5. allocator 结果应读成分区结构
6. auto-k 是预算建议扩展

### 不要写成什么

1. 不要写成三贡献并列通报
2. 不要写成“我们打败了谁”
3. 不要写成“我们重构了旧主线”
4. 不要写成过多 caveat 列表

### 摘要建议结构

第一段：背景 + 问题  
第二段：本文的统一原则与方法框架  
第三段：核心实验发现  
第四段：结论与边界

---

## 4.2 第一章 绪论

### 章使命

第一章要完成三件事：

1. 重新定义研究问题
2. 给出新的贡献结构
3. 为第二章与第三章搭好逻辑桥

### 建议节结构

1. 研究背景
2. 问题定义与研究动机
3. 国内外研究现状
4. 本文研究问题
5. 本文研究内容与主要贡献
6. 论文组织结构

### 第一章核心命题

> KV Cache 量化的关键，不只是如何压缩数值表示，而是如何在压缩中保持足以支撑长上下文推理的注意力行为；基于这一判断，本文将行为提升为统一分析与设计原则，并据此重写校准、分配和预算建议三层问题。

### 第一章段落级论证清单

#### 1.1 研究背景

要回答：

- KV Cache 为什么是长上下文推理的核心瓶颈
- 量化为什么自然但又困难

节首核心句建议：

> 随着大语言模型上下文窗口持续扩大，键值缓存的显存与带宽开销已成为长上下文推理部署的核心瓶颈之一。

节尾收束句建议：

> 因此，问题已经不再只是“是否要量化”，而是“如何在压缩 KV Cache 的同时尽量保持模型的有效行为”。

#### 1.2 问题定义与研究动机

要回答：

- 现有方法的盲点是什么
- 为什么要从行为视角切入

必须出现：

- softmax 非线性导致数值误差与行为偏移不单调
- 注意力行为是更接近真实损伤的位置

禁写：

- 不要在这一节就先宣布 “KL 比 MSE 强”

#### 1.3 国内外研究现状

要回答：

- 现有工作大致有哪些路数
- 现有工作的问题不是“都不行”，而是缺少统一解释链

禁写：

- 不要写成“这些工作都没有做过，因此本文最强”

#### 1.4 研究问题

建议只保留 3 个研究问题：

1. 统一分析对象是什么
2. allocator 应该如何被理解
3. 如何从 fixed-k 脆弱性走向预算建议

#### 1.5 研究内容与贡献

贡献建议固定为四点：

1. 以行为为统一分析对象的框架
2. INT8 规范验证路径
3. allocator 的分区结构读法
4. auto-k 作为预算建议扩展

禁写：

- 不要并列写 `KL / RoleAlign / kernel` 三贡献

#### 1.6 论文组织结构

应自然过渡到第二章与第三章，不要只是机械列目录。

### 第一章图表绑定

- **图 1-1**：全文主线总览图
- **表 1-1**：研究问题与章节映射表

---

## 4.3 第二章 相关工作与理论基础

### 章使命

第二章不是“背景教学章”，而是：

> 用最小必要理论基础 + 清晰的 prior work 重排，说明本文到底站在哪一条研究线上。

### 建议节结构

1. Transformer、KV Cache 与长上下文推理基础
2. KV Cache 量化的三条设计轴
3. 量化格式方向：K/V 非对称设计
4. 校准信号方向：从数值代理到行为对象
5. 预算分配方向：混合精度与逐层预算分配
6. 相邻方向：attention-driven control 与 eviction
7. 本文定位

### 第二章核心命题

> 现有工作分别在量化格式、校准信号、预算分配和相邻的注意力控制方向上推进，但这些方向之间缺少一条统一的解释链；本文的独特位置，不是简单提出另一个更强的方法，而是把校准与预算分配放到同一个以行为为中心的框架下组织起来。

### 第二章段落级论证清单

#### 2.1 最小必要基础

只保留：

- Decoder-only Transformer
- KV Cache 在线推理中的作用
- GQA 与 `H_kv`

禁写：

- 不要写成完整 Transformer 教材

#### 2.2 三条设计轴

必须明确：

1. 格式轴
2. 校准轴
3. 预算分配轴

作用：

- 为后文的本文定位服务

#### 2.3 量化格式方向

必须正面承认：

- KIVI 是关键前作
- AsymKV 等说明 K/V 非对称不是偶然观察

禁写：

- 不要把本文写成“新格式论文”

#### 2.4 校准信号方向

要写清：

- MSE / percentile 为什么合理
- 但为什么对 KV Cache 不够
- 本文为什么主张把行为作为分析对象

禁写：

- 不要直接写成 “行为目标优于数值目标”

#### 2.5 预算分配方向

必须承认：

- KVTuner、KVmix 已经说明 allocation 本身是独立问题

本文位置要写成：

- 本文不是重复 mixed-precision 思路
- 而是把 allocation 纳入行为框架

#### 2.6 相邻方向

至少提到：

- H2O
- SnapKV
- AhaKV
- DuoAttention

作用：

- 证明 attention-derived signals 可用于压缩决策

#### 2.7 本文定位

这一节必须非常清楚：

1. 本文不是新格式论文
2. 不是 superiority 校准论文
3. 不是 winner-style allocator 论文
4. 是 behavior 框架论文

### 第二章图表绑定

- **表 2-1**：三条设计轴总表
- **表 2-2**：相关工作定位矩阵
- **图 2-1**：设计轴与本文定位示意图

---

## 4.4 第三章 方法设计

### 章使命

第三章的任务不是“堆方法细节”，而是：

> 把行为原则、校准、分配、auto-k 之间的层级关系写清楚，并建立第四章可展开的正式方法身份。

### 建议节结构

1. 设计原则：以行为为统一分析对象
2. 框架总体结构
3. 行为对齐校准
4. INT8 规范验证路径
5. 行为引导的预算分配
6. auto-k：预算建议扩展
7. 运行时集成与扩展接口

### 第三章核心命题

> 本文框架由两个离线产物和一条运行时消费路径构成：行为对齐校准回答“如何量化”，行为引导分配回答“预算花在哪”，auto-k 则在此基础上进一步回答“保护多少层”。

### 第三章段落级论证清单

#### 3.1 设计原则

核心句建议：

> 在 KV Cache 量化中，更值得被保持和分析的对象不是张量数值本身，而是由 Query、Key、Value 共同决定的注意力行为。

作用：

- 建立全文统一分析对象

#### 3.2 框架总体结构

必须写清：

- calibration artifact
- policy artifact
- runtime routing

禁写：

- 不要让框架图显得像系统堆栈图，而看不出方法逻辑

#### 3.3 行为对齐校准

必须写清：

- 它是离线校准过程
- 它生成可固化、可审计的校准产物
- 它的价值是建立框架路径，不是证明 KL 普适更优

#### 3.4 INT8 规范验证路径

必须明确：

- 为什么是 INT8
- 为什么它是“规范验证实例”

禁写：

- 不要把 INT8 写成最终低比特 hero path

#### 3.5 行为引导的预算分配

必须写清：

- 它消费的是上游导出的层敏感度画像
- 不是直接在每个候选策略上重新优化行为目标

建议用中文表达：

- 先写“行为引导分配”，括号里保留 `behavior-guided allocation`

#### 3.6 auto-k

必须明确三点：

1. fixed-k 为什么脆弱
2. auto-k 为什么自然出现
3. auto-k 为什么只是扩展，不是理论中心

#### 3.7 运行时集成与接口

必须为第四章过渡：

- 第三章最后一句应明确说：第四章将沿“规范验证路径 → 分区结构 → 扩展能力 → 证据边界”的顺序组织实验。

### 第三章图表绑定

- **图 3-1**：框架总图
- **表 3-1**：校准产物结构表
- **图 3-2**：从层敏感度画像到预算策略的关系图
- **表 3-2**：校准 / 分配 / auto-k 三层关系表

---

## 4.5 第四章 实验与分析

### 章使命

第四章是全文中心。它的任务不是展示“谁赢了”，而是：

1. 固定 5 条 frozen `final-ready support` 在正文中的角色
2. 用跨模型结果证明 allocator 更应理解为分区结构
3. 给出 L2 A/B/C 与 auto-k / Prompt-adaptive 的正确定位
4. 明确主文、次级支撑、附录和 future work 的证据边界

### 建议节结构

1. 实验设置与 frozen 证据分层
2. INT8 规范验证路径：当前能证明什么，不能证明什么
3. allocator 的跨模型分区结构总览
4. Mistral：Mistral-specific auto-k win
5. 3B：QA-style compare set 上的 early-layer rescue
6. 14B：top-tier but no stable winner
7. heuristic：强基线，但强度同样是 regime-dependent
8. 7B：supporting regime case，而不是正文中心位
9. 8B：official Prompt-adaptive matrix 与 mixed signal
10. L2 A/B/C 的方法扩展位置与对比集合边界
11. provenance 与对比集合边界

### 第四章核心命题

> 当前 frozen 证据最核心的正文支撑不是某个 allocator 的统一优胜，而是五条已经冻结的结构性结论：INT8 路径具备保真性，Mistral 上出现了 auto-k 的模型特异性正点，3B 在 QA-style compare set 上表现出首层恢复结构，14B 落在高质量但无稳定赢家的宽预算区间，而 heuristic 必须被正面承认为强基线。其余 allocator 与 Prompt-adaptive 结果主要用于补强 framework / regime 的读法，而不是制造新的 winner story。

### 第四章写作硬规则

1. 每个模型小节都必须按以下三句收束：
   - 这一节的核心现象是什么
   - 最稳定的结构性读法是什么
   - 不能从这组结果推出什么
2. 任何数字都只能服务结构判断，不能单独形成 winner 句；所有数字都必须可回溯到 frozen source-of-truth。
3. official Prompt-adaptive 只有 `8B × 5 tasks × 3 variants ONLY`；`1.5B / 7B` 一律按 off-protocol exploratory 处理。
4. 当前 selector 只能写成 `task-profile-bucket` 或 task-level routing 近似，不能写成已经成立的 per-prompt routing。
5. `表 4-5` 只能服务 auto-k / Prompt-adaptive 的角色定位，不能服务跨模型优胜比较。

### 第四章段落级论证清单

#### 4.1 实验设置与证据分层

要回答：

- 为什么这章不按 winner table 写
- 当前哪些资产可进入正文主支撑
- 哪些资产只能作为次级支撑或附录

禁写：

- 不要在这节展开长篇 provenance 讨论

#### 4.2 INT8：能证明什么，不能证明什么

要写清：

- INT8 路径证明了框架路径可落地且具备 fidelity
- 它不能证明 `KL > MSE`
- INT8 的具体数值应以当前 frozen canonical source 为准，本控制包中不写死自由引用数字

#### 4.3 allocator 的跨模型分区结构

这一节必须先给全文一个总读法，再进入各模型。

必须出现的总表观点：

- Mistral：当前最清晰的 auto-k 正点，但仍是模型特异性
- 3B：首层瓶颈与首层恢复只在 core QA-style compare set 上成立
- 14B：高质量宽预算区间内无稳定 winner
- heuristic：必须被正面承认为强基线，但其强度也随模型而变
- 7B：如需出现，只保留为 supporting note，用于补充 aggregation-split 的结构意义
- 8B：主要承担 fixed-k turning point 与 official Prompt-adaptive matrix 的平台角色

#### 4.4 7B

角色：

- 只作 supporting note
- 只用于展示 aggregation-split 如何补强分区结构读法
- 不再承担 frozen 主结论中心位，也不宜展开成完整主小节

写法要求：

- 如正文保留 7B，请压成一段短说明，不要给它独立的强展开段落
- 不要为 7B 单独制造“最具辨识度发现”的语气

#### 4.5 8B

要写清：

- 8B 是 fixed-k 旧叙事失效的重要平台
- official Prompt-adaptive 只对应 `8B × 5 tasks × 3 variants ONLY`：`narrativeqa`、`hotpotqa`、`gov_report`、`dureader`、`lcc`
- 整体结论是 weak / mixed，而不是正式主结论
- `lcc` 只能作为 mixed evidence 中的局部正点
- 当前 selector 本质上仍是 `task-profile-bucket` / task-level routing 近似，而不是真正的 per-prompt routing
- 如写 `lcc` 正点，必须与“不可外推”为同一段连续表述，不得拆成独立积极故事线

#### 4.6 14B

必须写入的代表性数字：

- `uniform_int4_k4v4 = 7.2345`
- `bakv_auto_cov90_max = 7.1501`
- `bakv_auto_cov80_max = 7.1213`
- `heuristic_k3 = 7.1171`

要写清：

- 强基线依然活跃
- 14B 落在高质量宽预算区间
- 可以写成 top-tier but not winner
- 不能写成“大模型稳定偏好更大 k”的规模规律

#### 4.7 Mistral

必须写入的代表性数字：

- `bakv_auto_cov80_max = 14.7640`
- `heuristic_k3 = 14.6036`
- `bakv_auto_cov70_max = 14.4000`

必须写成：

- auto-k 最清晰的 frozen 正面案例
- 但其成立方式是 Mistral-specific，而不是跨 family 普适成立

禁写：

- 不要直接上升为 auto-k 跨模型普适最优

#### 4.8 heuristic

必须正面写：

- heuristic 不是弱基线
- 正因为它强，allocator 的价值才更应写成结构性现象
- heuristic 的强度本身也是 regime-dependent
- 本节首句就应交代其强度也是 regime-dependent

禁写：

- heuristic 是全局稳定强基线
- heuristic 在所有模型与任务上都强
- 3B 可以被当作 heuristic 仍然稳定的证据

#### 4.9 auto-k

要写成：

- 预算建议机制
- 方法扩展层
- Mistral-specific final-ready support + L2 A/B exploratory positive support
- 不能写成跨模型统一最优
- 不能把 L2 C official 的 mixed 结果混写成 auto-k 全面成立

#### 4.10 3B

必须写入的代表性数字：

- `bakv_k1 = 6.9023`
- `heuristic_k1 = 3.48`
- 相对提升约 `+98%`

必须写清：

- 3B 的主角不是 auto-k
- 而是 core QA-style compare set 上的首层恢复现象
- 不能外推成“小模型普遍偏好低层”或“3B 普遍偏好 k=1”
- 本节首句就应写明“该现象仅限 core QA-style compare set”

#### 4.11 provenance 与对比集合边界

必须写清：

- smoke runs 不进入主文主表
- `trec`、`vcsum` 不承担 allocator 主结论
- recursive mixing 不得进入正式统计
- L2 Phase A/B 只能写成 exploratory positive support / method-extension evidence
- L2 Phase C official 只能写成 weak / mixed exploratory branch
- `1.5B / 7B` Prompt-adaptive 只能写成 off-protocol exploratory / future-work seed
- `lcc` 是 official 8B matrix 中的局部正点，但不能外推为 prompt-level routing 已成立

### 第四章图表绑定

- **表 4-1**：模型与角色表
- **表 4-2**：证据分层表
- **表 4-3**：INT8 结论边界表
- **图 4-1**：INT8 规范路径图
- **表 4-4**：跨模型分区结构总表
- **图 4-2**：模型分区结构图
- **表 4-5**：auto-k / Prompt-adaptive 当前位置表
- **图 4-3**：3B 首层恢复图
- **表 4-6**：对比集合边界表

---

## 4.6 第五章 结论与展望

### 章使命

第五章必须完成两件事：

1. 把全文收束成“framework + canonical path + regime + extension + frozen support claims”
2. 在不削弱论文的前提下，明确当前边界、mixed evidence 与未来方向

### 建议节结构

1. 研究结论
2. 研究局限性
3. 未来工作展望
4. 结语

### 第五章核心命题

> 本文的最大贡献，不在于证明某个量化方法普适更优，而在于建立了一条更稳健的问题组织方式：以行为为统一分析对象，用 INT8 规范路径验证框架可执行性，再把 allocator 的现实重写为分区结构，并在 frozen 证据边界内将 Mistral-specific auto-k、3B 首层恢复、14B top-tier no-winner 与 heuristic 强基线一并组织为可辩护的正文支撑。

这里支撑的是 framework / regime reading，而不是 superiority proof。

### 第五章段落级论证清单

#### 5.1 研究结论

必须依次回收五层：

1. behavior principle
2. INT8 canonical
3. regime-dependent allocation
4. frozen 5 claims 的正文位置
5. auto-k / Prompt-adaptive 的扩展边界

禁写：

- 不要再出现“本文证明了……普适优于……”

#### 5.2 局限性

必须承认：

- auto-k 显式胜出仍主要集中在 Mistral
- L2 A/B 仍属于方法扩展支撑，不是主心脏
- Prompt-adaptive official 目前仅得到 weak / mixed 信号
- `1.5B / 7B` Prompt-adaptive 仍是 off-protocol exploratory only
- extend-task 信息量不均匀，`lcc` 也只应写成局部正点

#### 5.3 未来工作

只保留三条：

1. K/V 非对称分配
2. 质量—成本 Pareto 分析
3. 真正超越 task-bucket routing 的 per-prompt selector

#### 5.4 结语

结尾要像论文，不要像工作总结。

核心句建议：

> 相比追求更激进但证据不足的结论，本文更希望在当前证据能够支撑的范围内，建立一条更稳定、更可辩护的研究主线。

---

## 5. 图表绑定表

| 图表编号 | 章节位置 | 服务的论证动作 | 正文应如何引出 | 图注安全写法 | 禁止写法 |
|---|---|---|---|---|---|
| 图 1-1 | 第一章 1.5 后 | 总览全文逻辑链 | “图 1-1 概括了本文的整体研究思路。” | 强调整体逻辑链 | 不写“最终赢家路线图” |
| 表 1-1 | 第一章结尾 | 固定研究问题与章节关系 | “表 1-1 给出了研究问题与章节安排之间的对应关系。” | 强调映射关系 | 不写“贡献排名” |
| 表 2-1 | 第二章 2.2 | 解释三条设计轴 | “表 2-1 概括了 KV Cache 压缩研究的三条设计轴。” | 强调组织视角 | 不写“本文在三条轴上都最优” |
| 表 2-2 | 第二章 2.7 | 定位 prior work 与本文关系 | “表 2-2 归纳了代表性工作与本文的关系。” | 强调定位 | 不写“已有工作不足以应对”式绝对否定 |
| 图 2-1 | 第二章末 | 可视化本文位置 | “如图 2-1 所示，本文位于校准与预算分配之间的连接位置。” | 强调位置 | 不写“本文覆盖所有方向” |
| 图 3-1 | 第三章 3.2 | 展示两类离线产物与运行时路径 | “图 3-1 展示了本文框架的总体结构。” | 强调框架闭环 | 不写“完整解决方案” |
| 表 3-1 | 第三章 3.3 | 说明校准产物内容 | “表 3-1 列出了校准产物应包含的关键字段。” | 强调可审计性 | 不写“最优参数表” |
| 图 3-2 | 第三章 3.6 | 解释画像如何转成策略 | “图 3-2 展示了层敏感度画像与预算策略之间的关系。” | 强调转换关系 | 不写“auto-k 总优于 fixed-k” |
| 表 3-2 | 第三章 3.6 后 | 区分三层方法身份 | “表 3-2 对比了校准、分配和 auto-k 三个层次。” | 强调层级 | 不写“auto-k 是主方法” |
| 表 4-1 | 第四章 4.1 | 固定模型角色 | “表 4-1 总结了各模型在本章中的叙事角色。” | 强调角色 | 不写“难度排序” |
| 表 4-2 | 第四章 4.1 | 说明证据层级 | “表 4-2 说明了本章使用的证据分层。” | 强调用途边界 | 不写“最终发布级” |
| 表 4-3 | 第四章 4.2 | 固定 INT8 的结论边界 | “表 4-3 给出了 INT8 路径当前可以支撑和不能支撑的结论。” | 强调边界 | 不写“INT8 superiority table” |
| 图 4-1 | 第四章 4.2 | 展示 INT8 规范验证路径 | “图 4-1 展示了 INT8 路径的校准到运行时闭环。” | 强调验证链 | 不写“最优方法流程图” |
| 表 4-4 | 第四章 4.3 | 固定跨模型分区结构读法 | “表 4-4 概括了不同模型呈现出的 allocator 分区结构。” | 强调结构差异 | 不写“各模型赢家表” |
| 图 4-2 | 第四章 4.3 后 | 可视化分区结构 | “图 4-2 进一步展示了不同模型在 allocator 空间中的位置差异。” | 强调区间和结构 | 不写“统一规律图” |
| 表 4-5 | 第四章 4.9 | 固定 auto-k / Prompt-adaptive 当前角色 | “表 4-5 对 auto-k 与 Prompt-adaptive 在不同证据层级中的位置作了汇总说明。” | 强调扩展角色与边界 | 不写“排名榜” |
| 图 4-3 | 第四章 4.10 | 展示 3B 首层恢复 | “图 4-3 直观展示了 3B 中首层保护与中层 heuristic 的差异。” | 强调异常现象 | 不写“普适低层优先规律” |
| 表 4-6 | 第四章 4.11 | 写死对比集合边界 | “表 4-6 总结了当前主文可使用与不可使用的对比资产。” | 强调边界管理 | 不写“过滤后赢家集合” |

---

## 6. 数据与 claim 边界表

### 6.1 正文主支撑：frozen 5 claims

红线：以下内容可进入正文主支撑，但仍必须写成结构性结论，不能展开成 winner rhetoric。

| 层级 | 内容 | 写法要求 |
|---|---|---|
| 正文主支撑 | INT8 canonical path fidelity | 可直接写入正文核心结论，但具体数值必须以 frozen canonical source 为准，不在本控制包中写死 |
| 正文主支撑 | Mistral-specific auto-k win | 可直接写成模型特异性正点，不可外推为跨 family 普适成立 |
| 正文主支撑 | 3B early-layer rescue regime（限 QA tasks） | 可直接写成 3B 在 core QA-style compare set 上的结构性现象，不可外推为小模型普遍规律 |
| 正文主支撑 | 14B top-tier but no stable winner | 可直接写成高质量宽预算区间中的 top-tier 现象，不可写成“更大模型稳定偏好更大 k” |
| 正文主支撑 | heuristic is a strong baseline | 可直接写成基线结论，但必须同时写清其强度也是 regime-dependent |

### 6.2 正文次级支撑：exploratory positive support / method-extension evidence

| 层级 | 内容 | 写法要求 |
|---|---|---|
| 正文次级支撑 | L2 Phase A（K/V asymmetric） | 只能写成 exploratory positive support / method-extension evidence |
| 正文次级支撑 | L2 Phase B（Pareto） | 只能写成 exploratory positive support / method-extension evidence |
| 正文次级支撑 | 8B fixed-k turning point | 只能写成结构转折平台，不写成新的 frozen 主结论 |

### 6.3 Discussion / appendix only

| 层级 | 内容 | 写法要求 |
|---|---|---|
| discussion / appendix | L2 Phase C official（8B × 5 tasks × 3 variants ONLY） | 固定写成 weak / mixed exploratory branch，不进入 final claim |
| discussion / appendix | `lcc` strict win datapoint | 只能写成 official 8B matrix 中的局部正点，不可外推为 prompt-level routing 已成立 |
| discussion / appendix | 7B aggregation-split | 只保留为 supporting note 或 discussion 段，不再承担第四章中心位 |
| discussion / appendix | `1.5B / 7B` Prompt-adaptive | 固定写成 off-protocol exploratory / future-work seed |
| discussion / appendix | `trec`、`vcsum` | 只作边界披露，不承担 allocator 主结论 |
| discussion / appendix | smoke runs / recursive mixed | 不进入主文主表 |

### 6.4 绝对不能写成正文主张的内容

1. 当前任何 “rank #1 / best / gap to best” 风格总结
2. auto-k 的跨模型统一最优说法
3. Prompt-adaptive 的 final claim
4. off-protocol Gate C 结果
5. uniform / heuristic / fixed-k 的全局胜负结论
6. “selector 已具备通用 per-prompt 自适应能力”
7. 把 mixed / 局部正点 自动升级成机制解释或统一规律

### 6.5 冲突判定规则

1. 如果一项结果同时带有正向信号和 mixed / caveat，**一律按更低层级写**。
2. 如果一项结果既可被写成局部 observation，又可能被误写成机制解释，**一律只写 observation，不写机制**。
3. 如果某数字缺少 `metric / task set / aggregation / comparison set / status` 中任一锚点，Claude 不得主动补写。

### 6.6 正文中允许使用的结论动词

优先使用：

- 表明
- 说明
- 支持
- 提示
- 暴露出
- 更适合被解释为
- 可以被写成

尽量避免：

- 证明
- 确证
- 统一解释了
- 全面优于
- 最优
- 支配

### 6.7 写作分级表

| 层级 | 内容 | 写法要求 |
|---|---|---|
| 正文主结论 | frozen 5 claims | 可直接写，但必须保持结构性、边界化表述 |
| 正文次级支撑 | L2 Phase A/B | 只能写成 exploratory positive support / method-extension evidence |
| Discussion / Appendix | 7B aggregation-split、official `lcc` datapoint、Gate C mixed signal | 限定写，不得升级成主结论或第二故事线 |
| Future Work | true per-prompt selector、更多 family 覆盖、后续 role-aware 扩展 | 只能写成未来方向 |
| 禁写 | universal winner、Prompt-adaptive final claim、off-protocol Gate C、跨模型 auto-k 统一最优 | 明确禁止 |

---

## 7. 给 Claude 的总 Prompt

以下 Prompt 可直接交给 Claude 使用。

### 7.1 总 Prompt

你现在的任务不是润色旧论文，也不是总结内部工作台，而是**按照给定的大纲包直接写一篇新的中文论文正文**。

请严格遵守以下要求：

1. 在写作前，先接受本控制包中的 frozen source-of-truth priority；若旧 readout 与 frozen state 冲突，一律以 frozen state 与 clean rerun readout 为准。
2. 使用中文写作，风格贴近一篇已经成型的中文学术论文，而不是英文会议论文的翻译稿。
3. 行文逻辑要贴近原 thesis / 原 PDF 的章节节奏：先提出问题，再铺必要背景，再展开核心论证，最后自然收束。
4. 这篇论文的总主线是：
   - 行为是 KV Cache 量化中更合适的统一分析对象
   - INT8 是规范验证路径，而不是 superiority 证明
   - allocator 的经验结果应写成分区结构，而不是 winner story
   - 当前 frozen 5 claims 可以进入正文主支撑
   - auto-k 是预算建议扩展，Prompt-adaptive 当前只允许写到 mixed / exploratory 边界
5. 不要写成工作台说明文，不要解释“为什么现在改主线”，不要写任何内部重构过程。
6. 不要出现以下写法：
   - candidate-main / final-ready
   - 当前最稳的写法
   - supporting evidence
   - 我们决定把……
   - 旧主线被击穿……
7. Related Work 必须公平准确，正面承认 KIVI、KVTuner、KVmix、AsymKV、H2O、SnapKV、AhaKV、DuoAttention 的位置。
8. 第四章不得写成 winner table 展示，必须按“INT8 规范验证 → 跨模型分区结构 → Mistral / 3B / 14B / heuristic / 7B / 8B Prompt-adaptive 的不同角色 → L2 A/B/C 与对比集合边界”来组织。
9. official Prompt-adaptive 只有 `8B × 5 tasks × 3 variants ONLY`；`1.5B / 7B` 一律不得写成正式 Gate C 或跨模型 Prompt-adaptive 证据。
10. 当前 selector 只能写成 task-level / task-profile-bucket routing 近似，不能写成已经成立的 per-prompt routing。
11. 所有数字只服务论证，不制造 winner rhetoric；若本控制包未写死某数字，你不得自行补写。
12. 图表在正文中要像正式论文资产，被自然引出；不要写“图意”“建议内容”“caption 草稿”。
13. 第五章必须像论文收口，而不是内部总结。

请严格按照本大纲包的章节结构、段落目标、图表绑定和 claim 边界来写。

---

## 8. 给 Claude 的分章 Prompt

### 8.1 中文摘要 Prompt

请写一段中文摘要，长度控制在一页摘要应有的密度内。  
要求：

- 先写背景与问题
- 再写本文的统一原则与方法层次
- 再写核心实验发现
- 最后写边界清楚的结论
- 不要写成四点贡献列表
- 不要用内部控口径语言

### 8.2 第一章 Prompt

请写“第一章 绪论”，要求：

- 使用典型中文 thesis 写法
- 保持 `研究背景 → 问题定义与研究动机 → 国内外研究现状 → 研究问题 → 研究内容与主要贡献 → 论文组织结构` 的节奏
- 贡献必须是新的四点结构
- 不能回到旧的 `KL / RoleAlign / kernel` 并列贡献写法

### 8.3 第二章 Prompt

请写“第二章 相关工作与理论基础”，要求：

- 不要写成背景教材
- 每一节都要回答“这和本文定位有什么关系”
- 用三条设计轴重排相关工作
- 明确本文不是新格式论文、不是 superiority 校准论文、不是单一 allocator winner 论文

### 8.4 第三章 Prompt

请写“第三章 方法设计”，要求：

- 把“原则—框架—实例—扩展”的层级写清楚
- 清楚区分行为对齐校准、行为引导分配、auto-k
- 让第三章足够扎实，从而第四章的 allocator 结果不会像另起一篇论文

### 8.5 第四章 Prompt

请写“第四章 实验与分析”，要求：

- 这章是全文中心
- 不能写成 winner-style 实验章
- 必须按以下逻辑展开：
  1. 实验设置与证据分层
  2. INT8 路径的边界
  3. allocator 的跨模型分区结构
  4. Mistral / 3B / 14B / heuristic / 7B / 8B Prompt-adaptive 的不同角色
  5. L2 A/B/C 的正确定位
  6. provenance 与对比集合边界
- 只允许把 frozen 5 claims 写入正文主支撑
- official Prompt-adaptive 只能写 `8B × 5 tasks × 3 variants ONLY`，且结论必须是 weak / mixed
- 当前 selector 只能写成 task-level / task-bucket 近似，而不能写成已成立的 per-prompt routing
- `1.5B / 7B` Prompt-adaptive 只能写成 off-protocol exploratory / future-work seed
- 你可以使用给定数字，但不要把它们写成胜负榜，也不要自行补写本控制包未冻结的数字

### 8.6 第五章 Prompt

请写“第五章 结论与展望”，要求：

- 回收全文五层：behavior / INT8 / frozen 5 claims / regime / auto-k 与 Prompt-adaptive 的扩展边界
- 明确局限性，但不要写得像自我否定
- 未来工作只保留三条：K/V 非对称分配、质量—成本 Pareto、真正超越 task-bucket routing 的 per-prompt selector

---

## 9. 给 Claude 的最后提醒

如果 Claude 在写作过程中遇到以下诱惑，必须主动克制：

1. 想把全文重新写成“行为导向方法比别人更强”
2. 想把 auto-k 写成整篇论文的主角
3. 想把 heuristic 写成陪衬
4. 想把第四章写成排名展示
5. 想把 7B 重新抬回正文中心位
6. 想把 official Prompt-adaptive 或 `lcc` 局部正点写成 prompt-level routing 已成立
7. 想把内部重构语言直接搬进正文

Claude 应始终记住：

> 这篇论文现在最强的地方，不是单点方法的绝对胜利，  
> 而是它终于找到了一个更稳、更像论文、也更经得起答辩和评审的组织方式。
