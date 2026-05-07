# Ch3 写作质量审查 — 顶刊/顶会标准对齐

> **创建日期**: 2026-05-08
> **目标**: 验证 Ch3 各小节是否达到 EMNLP / ACL / NeurIPS / ICLR senior reviewer 通过水准
> **方法**: 6 视角并行 agent 审查 → 综合分析 → 定点重写
> **范围**: thesis/chapters/ch3_method.tex（817 行 / 8 sections / 14 subsections）

---

## 6 视角评分维度

| # | 视角 | 评分关注 |
|---|---|---|
| **D1** | 顶会 Senior Reviewer | 写作 clarity / novelty 表达 / claim 边界 / 是否 conference-accept 水准 |
| **D2** | 数学严谨性审稿人 | 记号一致 / 定义完备 / 推导无 gap |
| **D3** | 复现实验者 | 能否凭描述独立复现 / 是否缺关键参数 |
| **D4** | 学术中文写作专家 | 句法 / 过渡 / 套话 / 教科书口吻 |
| **D5** | Skeptical Reader | 模糊措辞 / 可疑 claim / 反例风险 |
| **D6** | 同行博士生 | 易读性 / 概念引入 / 第一遍可懂度 |

每维度评分 **1–10**（≥8 视为顶会标准通过；6–7 需修订；≤5 需大改）。
最终 verdict：✅ Pass / 🟡 Needs revision / 🔴 Major rewrite。

---

## 章节清单与进度

| 节 | 标题 | 行范围 | 状态 |
|---|---|---|---|
| 3.1 | 注意力近似误差的代数分解与问题形式化 | 3–50 | 🟢 6-agent 已综合（6.7/10, Needs revision）|
| 3.2 | 动机诊断：K/V 敏感性不对称及其设计启示 | 51–68 | 🟢 6-agent 已综合（**6.0/10**, ⚠️ Major revision needed）|
| 3.3 | 行为引导量化框架总览 | 69–100 | ⚪ 待审 |
| 3.4.1 | 注意力分布 KL 散度目标 | 108–152 | ⚪ 待审 |
| 3.4.2 | 参数搜索空间与稳健选择准则 | 153–220 | ⚪ 待审 |
| 3.5.1 | INT8 基准路径：静态 Scale 与自适应保护 | 232–269 | ⚪ 待审 |
| 3.5.2 | 对称 INT4 的局限与格式升级动因 | 270–277 | ⚪ 待审 |
| 3.5.3 | INT4-RoleAlign：角色感知非对称量化 | 278–370 | ⚪ 待审 |
| 3.5.4 | INT4-RoleAlign 与 KIVI-style 的设计差异 | 371–398 | ⚪ 待审 |
| 3.6.1 | 逐层敏感度构建与分配策略 | 418–469 | ⚪ 待审 |
| 3.6.2 | K/V 角色感知的预算扩展 | 470–532 | ⚪ 待审 |
| 3.6.3 | 敏感度聚合、鲁棒性与覆盖度准则 | 533–572 | ⚪ 待审 |
| 3.6.4 | AutoK 的预算自动建议机制 | 573–625 | ⚪ 待审 |
| 3.7.1 | 离线校准产物与在线推理管线 | 632–681 | ⚪ 待审 |
| 3.7.2 | Triton 融合解码核函数设计 | 682–736 | ⚪ 待审 |
| 3.7.3 | 复杂度、访存与存储开销分析 | 737–811 | ⚪ 待审 |
| 3.8 | 本章小结 | 812–817 | ⚪ 待审 |

状态图例：⚪ 待审 / 🟡 审查中 / 🟢 已综合 / ✅ 已重写并验证

---

## §3.1 注意力近似误差的代数分解与问题形式化

### 行范围: thesis/chapters/ch3_method.tex line 3–50

### Status: 🟢 6-agent 审查完成 → 综合判断完成

### 6 视角综合评分

| 维度 | 分数 | 主要发现 |
|---|---|---|
| D1 顶会 Reviewer | **7.5**/10 | 形式化达标；首段密度过高、$\Delta_{\mathrm{beh}}$ 与 $\theta$"概念层 vs 实例层"未交代 |
| D2 数学严谨 | **6.5**/10 | 代数恒等式 PASS；记号约定多处隐式（$q$ 行/列、$V$ 形状、$d_v$、$Q_{\theta_K}$ 作用域、$\Delta_{\mathrm{beh}}$ 签名） |
| D3 复现实验者 | **6.5**/10 | 公式可读但不 self-contained，必须查 §3.4 才能开始实现 |
| D4 中文写作 | **6.0**/10 | 教科书口吻偏重（"本节只做两步" / "这个写法" / "只看…容易漏掉"）|
| D5 Skeptical | **6.0**/10 | L30/L40-42 三处自我说明暴露作者预期被误解；L47 因果叙事缺 Lipschitz 桥接 |
| D6 博士生 | **7.5**/10 | 骨架清晰，公式可信；但 §3.1 内部就提前承担 §3.2-3.5 术语，第一遍读有摩擦 |
| **加权平均** | **6.7**/10 | 中度修订即可达到顶会方法章首节标准 |
| **最终 Verdict** | 🟡 **Needs revision** | **不需要 Major rewrite，~15-20 处局部修订** |

### 收敛问题清单（多 agent 独立提出，按严重度排序）

#### P0（3+ agents 一致 — 必改）

**P0-1. L40-42 三段过度自我说明 / 防御性辩护**（D1, D4, D5, D6 一致指出）
- 原文："式...是在第二行加减同一中间项得到的恒等式，不是把 Key 与 Value 的影响假设为相互独立。"
- 原文："这个写法同时给出一个边界：Value 项中的权重是量化后的 $\hat a_i$..."
- 原文："后续使用分布侧代理和输出侧代理时，只把它们当作可执行的近似读数..."
- 问题："边界"语义双关、"读数""近似读数"非数学语言；reviewer 会反问"为什么作者预期我会误读？"
- 改写方向：让恒等式不言自明；保留"$\hat a_i$ 而非 $a_i$"这个数学事实但去除辩护语气；删除"代理 / 读数"提前出现

**P0-2. L30 提前 spoil 了 §3.4/§3.5 的解法**（D1, D5, D6 一致指出）
- 原文："实际执行时，对称路径使用注意力分布 KL，角色感知低比特路径则拆成 K-path 与 V-path 两个代理。"
- 问题：违反"问题形式化"小节的边界——本节应只定义问题，不暴露后续解法；让读者以为漏读了背景
- 改写方向：改为前向指针"$\Delta_{\mathrm{beh}}$ 的具体实例化见 §3.4"，不暴露路径名

**P0-3. 数学记号约定缺失**（D1, D2, D3 都提到）
- L8: $q$ 行/列向量未声明（默认列向量但 $qK^\top$ 写法暗示行向量）
- L8: $V$ 形状未给（$d_v$ 全文未引入，$v_i$ 类型不明）
- L12: $a \in \mathbb{R}^S$ 与公式中 $a \in \mathbb{R}^{1 \times S}$ 混用
- L18: $Q_{\theta_K}, Q_{\theta_V}$ 作用域未指定（per-channel / per-token / 全张量？）
- L18: $\theta_K, \theta_V$ 是函数族还是张量？参数空间 $\Theta_K$ 未给
- L28: $\Delta_{\mathrm{beh}}$ 没有形式签名（非负、对称、$x=y$ 时为 0），紧跟一句"概念层目标"试图免责

#### P1（2 agents 一致 — 应改）

**P1-1. L6 "本节只做两步" 教科书宣告**（D1, D4, D6 指出）
- 论文方法章应直接进入定义；首段同时塞入"行为""分布侧/聚合侧""逐元素重建误差"等 4 个新概念，密度过高
- 改写方向：拆成两句，去掉"本节只做两步"PPT 体

**P1-2. L47 "Key 误差先改变 logits 排序" claim 边界**（D1 + D5 指出）
- 这是 claim 不是定理。$|\hat q\hat k_i^\top - qk_i^\top|$ 与 ranking change 之间没有数学桥接（softmax 对 logits 差异敏感，但"先排序后概率"的因果叙述需要 Lipschitz / Jacobian 论证）
- D1 也指出"功能失真"非正式表达，应改"行为层失真"或 "task-relevant degradation"
- 改写方向：软化为 motivation 措辞，或加"在 softmax 输出非极端 sparse 区间下..."限定

**P1-3. L16 多头/多层一句带过**（D2 数学 + D5 反例风险）
- 原文："多层、多头情形可视为同一分析在不同层与不同头上的重复与聚合"
- D2: 至少应给记号约定 $q^{(\ell,h)}, K^{(\ell,h)}$
- D5: GQA lift 反例——LLaMA-3 8B (H_q=32, H_kv=8) 中单头量化误差通过 4 个 query head 同时放大；逐层非线性叠加。该句应是后续证明目标不是首节断言
- 改写方向：加"在 MHA 下"限定 + 记号约定 + 把 GQA 留给后续讨论

**P1-4. L49 章末路线图过于教科书化**（D4 指出）
- 顶会方法章首节通常不写"本节由 X 出发，第 Y 节据此..."这种 PPT-style 路线图
- 改写方向：删除或压成单句

**P1-5. L32 "从量化输出与参考输出的定义出发" 衔接空转**（D4 指出）
- 定义已在上文给出，此句空转
- 改写方向：直接接公式

#### P2（单 agent 提出，可考虑）

**P2-1. $\mathcal{B}(q,K,V):=(a,o)$ 命名过早**（D6）：本节内部只在末段隐式用一次，可推迟到 §3.3 命名
**P2-2. 图 3-1 标题 vs 正文措辞**（D6）："耦合传播路径" vs "不完全隔离的因果分量"——选一个
**P2-3. eq:ch3-error-decomp 操作性标注**（D3）：公式是 motivation 还是代码里直接用？需明确

### 收敛的句级改写建议（≥2 agents 同意）

| # | 原文（行号 + 原句节选） | 改写方向 | 同意 agents |
|---|---|---|---|
| 1 | L6「本节只做两步：先固定...再把...」 | 删讲义体宣告，首段拆两句 | D1, D4, D6 |
| 2 | L8 数学记号缺失 | 加「$q \in \mathbb{R}^{1 \times d_k}$ 行向量，$V \in \mathbb{R}^{S \times d_v}$，$d_v$ 为头 value 维」 | D1, D2, D3 |
| 3 | L18 $Q_{\theta_K}$ 作用域 | 加「逐元素/逐通道/逐 token，具体见 §3.4」 | D2, D3 |
| 4 | L26-28 $\Delta_{\mathrm{beh}}$ | 加形式签名「$\Delta_{\mathrm{beh}} \ge 0, \Delta_{\mathrm{beh}}(x,x)=0$；具体实例化见 §3.4」 | D1, D2, D3, D5 |
| 5 | L30 提前 spoil | 删「对称路径使用 KL，角色感知…拆成 K-path 与 V-path 两个代理」，改前向指针 | D1, D5, D6 |
| 6 | L40 自我辩护 | 整句删除或压成单句脚注 | D4, D5, D6 |
| 7 | L42 三段过度说明 | 大幅压缩或合并到一句 | D1, D4, D5, D6 |
| 8 | L47「功能失真」「先改变 logits 排序」 | 软化措辞，删因果叙事 | D1, D5 |
| 9 | L49 章末路线图 | 删除或压成单句 | D4 |

### 是否达到顶会方法章首节标准的最终判断

**Qualified yes，但需中度修订**。代数推导本身正确（D2 确认 eq:ch3-error-decomp 是恒等式 PASS），章节定位合适（"问题形式化"作为方法章首节是合理分工）。但当前版本有三类系统性问题：

1. **写作风格摆动在"教材"和"论文"之间**（D4 指出最多）：保留了"本节只做两步""这个写法""只看…容易漏掉"等讲义体
2. **过度自我说明暴露防御心理**（D5 最强批评）：作者反复用"不是 X 不是 Y"的免责式陈述，让 reviewer 怀疑前文有问题
3. **数学约定隐式过多**（D2 强烈要求）：行/列向量、形状、$d_v$、$\Delta_{\mathrm{beh}}$ 签名等顶会会要求显式

直接送审不会被作为 reject 理由（D1 判断），但会让 reviewer 在引言段做一次回读。修订后估算可达 8-9/10。

### 修订工作量估算

- 局部修订：~15-20 处
- 不需要重写整节
- 估算耗时：30-60 分钟（如逐句 Edit + xelatex 验证）

### 下一步选项（待 user 决策）

| 选项 | 说明 |
|---|---|
| A | 立即按上述清单重写 §3.1，verify 编译，commit |
| B | 跳过重写直接进入 §3.2 审查（同样 6 agents） |
| C | user 自己看清单后决定哪些采纳、哪些跳过 |

---

---

## §3.2 动机诊断：K/V 敏感性不对称及其设计启示

### 行范围: thesis/chapters/ch3_method.tex line 51–65

### Status: 🟢 6-agent 审查完成 → 综合判断完成

### 6 视角综合评分

| 维度 | 分数 | 关键判断 | 一句话核心 |
|---|---|---|---|
| D1 顶会 Reviewer | **7.5**/10 | 🟡 Needs revision | 数字过早 spoiler；§3.1→§3.2 因果桥接缺 |
| D2 数学严谨 | **6.5**/10 | 🟡 Needs revision | PPL 缺统计口径；"功能临界点"未形式化 |
| D3 复现实验者 | **4.5**/10 | 🔴 **Major rewrite** | 跨章 ref 5 个过密；记号混用；缺协议 |
| D4 中文写作 | **6.5**/10 | 🟡 Needs revision | "问题收窄" PPT 套话；路线图重复 |
| D5 Skeptical | **4.5**/10 | 🔴 **Major rewrite** | Selection bias（LLaMA 缺数字）；K4V4→K 主导 confounded |
| D6 博士生 | **6.5**/10 | 🟡 Needs revision | 记号墙 5 套；图文顺序错位 |
| **加权平均** | **6.0**/10 | 🔴 **比 §3.1 更严重** | 两个 Major rewrite 信号必须严肃对待 |

### 收敛问题清单（多 agent 独立提出）

#### P0（4-5 agents 一致 — 必改）

**P0-1. 数字证据过早 spoil 第四章**（D1, D2, D3, D5, D6 — 5 个一致）
- L56 直接给 PPL `9.31 → 1290.9`、`9.35`、RULER `0%`
- 顶会惯例：方法章给模式 / 实验章给数字
- 改写方向：保留量级感（"约两个数量级"），具体数字留给 §4 表

**P0-2. 跨章 ref 密度过高**（D1, D3, D6 — 3 个）
- line 54-56 单段引用 4 个后章 ref（fig:ch3-kv-asymmetry, tab:ch4-kv-ppl, tab:ch4-kv-multitask, fig:ch4-kv-ruler32）+ §3.3 + §3.5
- 改写方向：合并成一句"完整跨模型证据见 §4.3.2"

**P0-3. 配置记号混用 5 套**（D3, D6 — 2 个但都强烈）
- 同节出现 `K4V8` / `K8V4` / `K@INT4+V@FP16` / `K@FP16+V@INT4` / `MixedKV`
- 改写方向：节首给一句记号映射，或全节统一为 K?V? 形式

**P0-4. "功能临界点" / "结构性" 未定义反复出现**（D2, D5, D6 — 3 个）
- "功能临界点"line 52, 56, 63 三次出现都没定义
- "结构性依据 / 结构性风险提示 / 结构性"在 line 52, 63 反复，含义漂移
- 改写方向：首次出现加操作性定义（脚注或括号），删一处"结构性"减修辞密度

**P0-5. L65 末"路线图"与 §3.1 末路线图重复**（D1, D4, D6 — 3 个）
- §3.1 已预告整章结构，§3.2 末再预告 §3.3+§3.5 是冗余
- 改写方向：删整段或压成单句

#### P1（2 agents 一致 — 应改）

**P1-1. L52 "第 §3.1 节表明" 教科书回指 + 因果桥接缺**（D1+D4）
- D1 指出 §3.1 推出加性结构但 §3.2 直接说"未必同样脆弱"——需补"softmax 非线性放大 Key 扰动"机制桥
- D4 指出 PPT 回指应改成直接陈述

**P1-2. L54 "这个压缩视图只回答一个方法问题" meta-disclaimer**（D1+D4）
- 违反 feedback_meta_disclaimers
- 改写方向：删 meta 句

**P1-3. L56 "这组诊断把问题从 X 收窄到 Y" 答辩讲解口吻**（D4+D6）
- D6 还指出与 line 54 信息冗余
- 改写方向：删整句，直接以数字证据起段

**P1-4. LLaMA-3.1-8B 数字缺位**（D2, D5 — 强烈批评）
- §3.2 唯一非-Qwen 证据只是 line 63 一句"不呈现同幅度 cliff"
- D5 批为 selection bias，D2 提议补一行 LLaMA 关键数字
- 改写方向：要么补 LLaMA inline 数字，要么明确把 claim 范围限定到 Qwen 系列

**P1-5. K4V4 共同失效→K 主导 confounded inference**（D5 独立但严重）
- L65 "如果 K4V8 与 K4V4 的共同失效都指向 Key 精度下降"——K4V4 同时压 K 和 V 不能 isolate K
- 改写方向：把"共同失效"句改写为"K@INT4 单侧诊断已足够说明 K 主导，K4V4 仅作 dose-response 验证"

#### P2（单 agent 提出）

**P2-1. "% 数据纪律：本图必须是..."作者 TODO 注释不应进 final**（D3）
**P2-2. line 60 注释（line 58-60 的 `% 图题` `% 数据纪律` 块）应清理**（D3）
**P2-3. "近乎完全的检索失稳" 在 RULER=0% 下应直接"完全归零"**（D5）
**P2-4. INT4 路径未明（对称？KIVI？AsymKV？）**（D3）
**P2-5. PPL 数字 1290.9 伪精度**（D2 — "≈ 1.3×10³"或加 seed 说明）
**P2-6. 图位置（line 61）滞后于图引用（line 54）**（D6 — \input 应紧贴 line 54）

### 收敛的句级改写建议（≥2 agents 同意）

| # | 原文（行号 + 节选）| 改写方向 | 同意 agents |
|---|---|---|---|
| 1 | L56 `9.31 → 1290.9 / 9.35 / 0%` | 改为"约两个数量级" / "完全归零"等量级表述，具体数字留给 §4 表 | D1, D2, D3, D5, D6 |
| 2 | L54-56 五个跨章 ref | 合并为一句"完整跨模型证据见 §4.3.2" | D1, D3, D6 |
| 3 | 节首加记号映射 | "本节使用 K?V? 表示位宽组合，K@bit+V@bit 表示单侧诊断；MixedKV ≡ K8V4" | D3, D6 |
| 4 | "功能临界点" 首次出现 | 加脚注/括号给操作性定义 | D2, D5, D6 |
| 5 | L65 末路线图 | 删除整段或压成单句 | D1, D4, D6 |
| 6 | L52 "第 §3.1 节表明" | 改为直接陈述 + 补 softmax 非线性桥接 | D1, D4 |
| 7 | L54 "这个压缩视图只回答一个方法问题" | 删 meta 句 | D1, D4 |
| 8 | L56 "这组诊断把问题从 X 收窄到 Y" | 删整句 | D4, D6 |
| 9 | LLaMA-3.1-8B 数字补充 | 补一行 K4V8 PPL 或 RULER；或明确限定 claim 到 Qwen | D2, D5 |
| 10 | L65 "K4V4 共同失效都指向 K" | 改写为"K@INT4 单侧诊断已足够说明 K 主导" | D5 |
| 11 | line 58-60 `% 数据纪律` 作者注释 | 清理 | D3 |
| 12 | "结构性"修辞密度 | 删 line 52 或 63 一处 | D2, D5, D6 |

### 是否达到顶会方法章动机小节标准的最终判断

🟡 **Needs Major revision，不需 rewrite from scratch**。

**比 §3.1 更严重的三个点**：
1. **D3 + D5 双重 Major rewrite 信号**：前者是复现性、后者是 claim 边界——两个独立维度都报红
2. **selection bias 嫌疑**：D5 直接把 LLaMA 数字缺位定性为 cherry-picking
3. **数字过早 spoiler**：5/6 agents 同时指出，是顶会惯例的硬伤

**这一节的核心矛盾**：
- §3.2 试图同时承担"动机诊断"与"实验预览"两个职责，结果两边都没做好——既没有自包含的小规模诊断让读者能独立读懂，又把 §4 的关键数字提前暴露失去后续新鲜感

**修订策略**：
- 不要重写整节
- 但比 §3.1 改动更深（25-30 处 vs §3.1 的 15-20 处）
- 重点：把数字抽象化、记号统一、删 meta、补 LLaMA 限定

### 修订工作量估算

- 局部修订：~25-30 处
- 节首加记号映射段（~3 行）
- 不需要重写整节
- 估算耗时：60-90 分钟

### Round 1 audit 与 90cb485 commit 状态对比

§3.2 round 1 audit 是基于 90cb485 commit 之前的旧状态。当前 .tex (commit 90cb485) 已修复部分 P0/P1：

| Round 1 Issue | v0 (commit 90cb485) 状态 | 剩余处理 |
|---|---|---|
| P0-1 数字 spoiler | ✅ 已修（"约两个数量级"代替 9.31→1290.9） | — |
| P0-2 跨章 ref 5 个过密 | ❌ 未减（仍 5 次 ref：line 50 两次 + line 52 三次 + line 56 一次）| candidate v1 合并 |
| P0-3 配置记号 5 套 | ✅ 已修（line 50 加节首记号映射） | — |
| P0-4 "功能临界点"反复 | ✅ 已修（v0 现状中无该词） | — |
| P0-5 章末路线图 | ⚠️ 部分（line 58 仍有"下文将这一设计动机实例化为非对称量化路径"单句）| candidate v1 删除 |
| P1-1 §3.1 教科书回指 | ✅ 已修（直接陈述+softmax 桥接） | — |
| P1-2 meta-disclaimer | ⚠️ 首段末"本节据此诊断哪一侧最先触发任务级失稳"是 PPT 自我宣告 | candidate v1 改为研究过程式 |
| P1-3 "收窄"答辩口吻 | ✅ 已修 | — |
| P1-4 LLaMA 数字限定 | ⚠️ 部分（已提及 LLaMA-3.1-8B 但仍定性"显著较弱"）| candidate v1 加 §4 ref 限定 |
| P1-5 K4V4 confounded | ✅ 已修（"K@INT4 单侧诊断 + dose-response 验证"两步分离）| — |
| P2-1/P2-2/P2-6 | ✅ 已修（图位置、注释清理）| — |

**v1 主要改动**：跨章 ref 5 次 → 2 次（合并到末段统一引用）+ 删章末路线图 + 改首段研究过程式表达 + 对齐 v4 §3.1 风格（无章末过渡）。

---

## §3.2 候选稿 v1（基于 v0=90cb485 + Round 1 剩余 P0/P1 修复）

```latex
\section{动机诊断：K/V 敏感性不对称及其设计启示}
\label{sec:ch3-motivation-kv}

Key 与 Value 误差虽同时进入注意力输出，但二者在低比特场景下未必同等脆弱：由式~\eqref{eq:ch3-error-decomp}，Key 项需经 softmax 非线性放大后再加权进入输出，Value 项则以 $\hat a_i(\hat v_i-v_i)$ 形式线性进入聚合。后文以 K/V 单侧诊断与对称低比特锚点暴露这种不对称，为低比特路径的格式选择提供依据。

本节使用两套配置记号：\texttt{K?V?} 表示位宽组合（如 \texttt{K4V8} 即 4-bit Key 与 8-bit Value），\texttt{K@bit+V@bit} 表示以 FP16 隔离非诊断侧的单侧诊断；\texttt{MixedKV} $\equiv$ \texttt{K8V4}。图~\ref{fig:ch3-kv-asymmetry} 抽取压缩诊断视图：\texttt{FP16} 为未量化参考，\texttt{K8V8} 为高精度量化参考，\texttt{K8V4}/\texttt{K4V8} 构成同平均位宽预算下的角色对照，\texttt{K4V4} 提供对称低比特锚点。

单侧 PPL 诊断在 Qwen2.5-1.5B 上显示：单独压低 Key 精度使 PPL 相对 FP16 基线放大约两个数量级，而单独压低 Value 精度仅引起基线邻域内的微小变化。32K 任务诊断中，\texttt{K4V8} 使 Qwen2.5-1.5B 与 Qwen2.5-7B 的 RULER 通过率完全归零，\texttt{K8V4} 未出现归零式失稳。两类诊断同向指出：在 Qwen 系列当前低比特设定下，最先触发任务级失稳的是 Key 精度下降，而非 Value 的对称压缩。

\input{figures/fig_ch3_kv_diag_needle}

该不对称在不同模型族上强度不同：Qwen 系列（$H_{kv}=2$ 或 $4$）在 \texttt{K4V8} 与 \texttt{K4V4} 下出现完全的检索归零，而具有更高 $H_{kv}$ 或不同头共享结构的模型（如 LLaMA-3.1-8B，$H_{kv}=8$）失稳幅度显著较弱。本文因此把"Key 侧低比特退化"作为低比特路径设计的核心约束，但其严重性与触发位宽的具体边界仍受模型规模、训练数据与 GQA 配置共同调制。

据此，本文将低比特路径的设计目标从"对称压低 K 与 V"调整为"优先保护 Key 的表示能力，避免 4-bit 率先落在 Key 上"。这一调整的核心论据来自单侧 PPL 诊断的隔离证据（K@INT4 单独触发数量级 PPL 退化）；\texttt{K4V8}/\texttt{K4V4} 的位宽对照作为剂量-响应（dose-response）验证与之同向，但因二者同时压低 K 与 V，单独不构成 K 主导的隔离推断。完整跨模型读数与统计协议见表~\ref{tab:ch4-kv-ppl}、表~\ref{tab:ch4-kv-multitask} 与第~\ref{sec:exp-kv-sensitivity}~节。
```

### 修改对照表（v0 90cb485 → v1）

| # | 位置 | v0 (90cb485) | v1 | 来源 |
|---|---|---|---|---|
| 1 | 首段末 | "本节据此诊断哪一侧最先触发任务级失稳，为后续低比特路径的格式选择提供依据" | "**后文以 K/V 单侧诊断与对称低比特锚点暴露这种不对称**，为低比特路径的格式选择提供依据" | P1-2 + codex prefs §28 研究过程式 |
| 2 | 第二段 | "图~\ref{fig:ch3-kv-asymmetry} **从第~\ref{sec:exp-kv-sensitivity}~节抽取**压缩诊断视图..." | "图~\ref{fig:ch3-kv-asymmetry} 抽取压缩诊断视图..." | P0-2 删 §4 来源 ref |
| 3 | 第二段末 | "完整跨模型读数与统计口径见第~\ref{sec:exp-kv-sensitivity}~节。" | (删除整句) | P0-2 |
| 4 | 第三段末 | "具体读数与统计协议见表~\ref{tab:ch4-kv-ppl}、表~\ref{tab:ch4-kv-multitask} 与第~\ref{sec:exp-kv-sensitivity}~节" | (删除整句) | P0-2 |
| 5 | 第五段末 | "详见第~\ref{sec:exp-kv-sensitivity}~节。" | (删除短语) | P0-2 |
| 6 | 末段末 | (无) | "**完整跨模型读数与统计协议见表~\ref{tab:ch4-kv-ppl}、表~\ref{tab:ch4-kv-multitask} 与第~\ref{sec:exp-kv-sensitivity}~节。**" | P0-2（统一 ref 一次） |
| 7 | 章末路线图 | "继续沿用对 K 与 V 同等处理的对称压缩在结构上缺乏依据，下文将这一设计动机实例化为非对称量化路径。" | (删除整句) | P0-5 + 对齐 v4 §3.1 |

跨章 ref 计数：v0 5 次 → v1 2 次（图 ref + 末段统一引用）。

### Round 2 结果（候选稿 v1）

| Agent | v0 | v1 | Verdict | 关键发现 |
|---|---|---|---|---|
| D1 顶会 | 7.5 | 7.8 | ❌ | 末段 design decision 越位 + 首段循环论证 |
| D2 数学 | 6.5 | 7.5 | ❌ | 量级描述需内联 forward ref + PPL 任务/数据集缺 |
| D3 复现 | 4.5 | 7.2 | ❌ | 量化方案标签缺 + K@INT4 记号漂移 + 统计协议无内容预告 |
| D4 中文 | 6.5 | 7.5 | ❌ | "在...上"违 codex prefs §44 + "本文因此"违 §65 + "据此本文将"违 §19 |
| **D5 Skeptical** | 4.5 | **6.2** | ❌ | "两类诊断同向"暗示独立性事实错误 + LLaMA 缺数字 selection bias |
| D6 博士生 | 6.5 | **8.4** | ✅ PASS | 确认结构清晰；建议补 GQA 均摊 15 字 |

**Round 2 加权平均 7.43**。5/6 NOT PASS, 1 PASS。D2/D5 明确 v2 修完后可达 PASS。

### Round 2 必改清单（v2 设计输入，按改动位置归类）

#### 首段（D1 M2）

- 循环论证："Key 与 Value...未必同等脆弱"是结论前置为前提
- v2: 改为从机制 premise 出发——"由式...，Key 项需经 softmax 非线性放大..., Value 项以...线性进入聚合，两条路径在低比特预算下的脆弱程度因此可能不对称"

#### 第二段记号映射 (D6 段 2 + D1 minor 3)

- "图...**抽取**压缩诊断视图" → "图...**呈现**" (D1 minor 3)
- K@bit+V@bit 加即时说明"（仅压低标注侧位宽，另一侧保留 FP16）" (D6 P3)

#### 图 \input 位置 (D6 P2)

- v1 \input 在段 4 位置（段 3 后），但图 ref 在段 2
- v2: 移 \input 紧跟段 2（图 ref 后）

#### 第三段 (D2/D3/D4/D5 多处合并)

- "在 Qwen2.5-1.5B **上**显示" → "对 Qwen2.5-1.5B 的单侧 PPL 诊断表明" (D4 M1 + I 项)
- "单独压低 Key 精度" → "**\texttt{K@INT4+V@FP16}** 使" (D3 M2 完整记号)
- "约两个数量级" 内联 forward ref "（统计协议见表~\ref{tab:ch4-kv-ppl}）" (D2 M1)
- "单独压低 Value 精度" → "**\texttt{K@FP16+V@INT4}**" (D3 M2 完整记号)
- "两类诊断同向指出" → "同一量化配置下两类指标均显示" (D5 M1 消除独立性误导)

#### 第四段 LLaMA + GQA 机制 (D5 M2 + D6 P2)

- 加 GQA 均摊机制："单 KV 头量化误差被 $H_{kv}$ 个查询头均摊后冲击更分散" (D6 P2)
- LLaMA "失稳幅度显著较弱" → "失稳幅度较小（详见表~\ref{tab:ch4-kv-multitask}）" + ref 替代具体数字 (D5 M2 partial / D5 M3 hedge "显著"→"较小")
- 加 confounder 控制策略："本文以 $H_{kv}$ 作为组间差异的代理变量" (D5 M3)

#### 末段（D1 M1 + D4 M2/M3 + D5 M4 合并）

- 删除整句 design decision："据此，本文将低比特路径的设计目标从'对称压低 K 与 V'调整为'优先保护 Key 的表示能力，避免 4-bit 率先落在 Key 上'" (D1 M1 + D4 M3 + D5 M4 自动解决)
- 留 "因此 Key 侧低比特退化被确立为低比特路径设计的核心约束" 作 §3.2 收束（不做 design decision）
- "**本文因此把**" → 已合并删除 (D4 M2)
- 末段统一 ref 加协议类型预告："（Bootstrap 95% CI 与置换检验）" (D3 M3)

---

## §3.2 候选稿 v2（整合 Round 2 18 处必改 + 4 处 D6 建议）

```latex
\section{动机诊断：K/V 敏感性不对称及其设计启示}
\label{sec:ch3-motivation-kv}

由式~\eqref{eq:ch3-error-decomp}，Key 项需经 softmax 非线性放大后再加权进入输出，Value 项则以 $\hat a_i(\hat v_i-v_i)$ 形式线性进入聚合，两条路径在低比特预算下的脆弱程度因此可能不对称。后文以 K/V 单侧诊断与对称低比特锚点验证这种不对称，为低比特路径的格式选择提供依据。

本节使用两套配置记号：\texttt{K?V?} 表示位宽组合（如 \texttt{K4V8} 即 4-bit Key 与 8-bit Value），\texttt{K@bit+V@bit} 表示以 FP16 隔离非诊断侧的单侧诊断（仅压低标注侧位宽，另一侧保留 FP16）；\texttt{MixedKV} $\equiv$ \texttt{K8V4}。图~\ref{fig:ch3-kv-asymmetry} 呈现压缩诊断视图：\texttt{FP16} 为未量化参考，\texttt{K8V8} 为高精度量化参考，\texttt{K8V4}/\texttt{K4V8} 构成同平均位宽预算下的角色对照，\texttt{K4V4} 提供对称低比特锚点。

\input{figures/fig_ch3_kv_diag_needle}

对 Qwen2.5-1.5B 的单侧 PPL 诊断表明：\texttt{K@INT4+V@FP16} 使 PPL 相对 FP16 基线放大约两个数量级（统计协议见表~\ref{tab:ch4-kv-ppl}），而 \texttt{K@FP16+V@INT4} 仅引起基线邻域内的微小变化。32K 任务诊断中，\texttt{K4V8} 使 Qwen2.5-1.5B 与 Qwen2.5-7B 的 RULER 通过率完全归零，\texttt{K8V4} 未出现归零式失稳。同一量化配置下两类指标均显示：在 Qwen 系列当前低比特设定下，最先触发任务级失稳的是 Key 精度下降，而非 Value 的对称压缩。

该不对称在不同模型族上强度不同：Qwen 系列（$H_{kv}=2$ 或 $4$）在 \texttt{K4V8} 与 \texttt{K4V4} 下出现完全的检索归零，而具有更高 $H_{kv}$ 或不同头共享结构的模型（如 LLaMA-3.1-8B，$H_{kv}=8$）失稳幅度较小，单 KV 头量化误差被 $H_{kv}$ 个查询头均摊后冲击更分散（详见表~\ref{tab:ch4-kv-multitask}）。其严重性与触发位宽的具体边界仍受模型规模、训练数据与 GQA 配置共同调制；本文以 $H_{kv}$ 作为组间差异的代理变量。

因此 Key 侧低比特退化被确立为低比特路径设计的核心约束。这一结论的核心论据是单侧 PPL 诊断的隔离证据（\texttt{K@INT4+V@FP16} 单独触发数量级 PPL 退化）；\texttt{K4V8}/\texttt{K4V4} 的位宽对照作为剂量-响应（dose-response）验证与之同向，但因二者同时压低 K 与 V，单独不构成 K 主导的隔离推断。完整跨模型读数与统计协议（Bootstrap 95\% CI 与置换检验）见表~\ref{tab:ch4-kv-ppl}、表~\ref{tab:ch4-kv-multitask} 与第~\ref{sec:exp-kv-sensitivity}~节。
```

### 修改对照表（v1 → v2）

| # | 位置 | v1 | v2 | 来源 |
|---|---|---|---|---|
| 1 | 首段 | "Key 与 Value 误差虽同时进入注意力输出，但二者在低比特场景下未必同等脆弱：由式...，Key 项需经..." | "**由式...，Key 项需经 softmax 非线性放大..., Value 项则以...形式线性进入聚合，两条路径在低比特预算下的脆弱程度因此可能不对称。**" | D1 M2 循环论证修复 |
| 2 | 首段末 | "...暴露这种不对称" | "...**验证**这种不对称" | D1 minor 1 |
| 3 | 第二段 | "图~\ref{...} **抽取**压缩诊断视图" | "图~\ref{...} **呈现**压缩诊断视图" | D1 minor 3 |
| 4 | 第二段 | "K@bit+V@bit 表示以 FP16 隔离非诊断侧的单侧诊断；" | "K@bit+V@bit 表示以 FP16 隔离非诊断侧的单侧诊断**（仅压低标注侧位宽，另一侧保留 FP16）**；" | D6 P3 即时说明 |
| 5 | 图 \input 位置 | 段 4 位置（段 3 后） | 紧跟段 2 末（图 ref 后） | D6 P2 |
| 6 | 第三段首句 | "单侧 PPL 诊断**在 Qwen2.5-1.5B 上显示**：单独压低 Key 精度使 PPL..." | "**对 Qwen2.5-1.5B 的单侧 PPL 诊断表明：\texttt{K@INT4+V@FP16}** 使 PPL 相对 FP16 基线放大约两个数量级**（统计协议见表~\ref{tab:ch4-kv-ppl}）**" | D4 M1 + D3 M2 + D2 M1 |
| 7 | 第三段中 | "而单独压低 Value 精度仅引起..." | "而 **\texttt{K@FP16+V@INT4}** 仅引起..." | D3 M2 |
| 8 | 第三段末 | "**两类诊断同向指出**：" | "**同一量化配置下两类指标均显示**：" | D5 M1 消除独立性误导 |
| 9 | 第四段 | "...失稳幅度**显著**较弱。" | "...失稳幅度**较小，单 KV 头量化误差被 $H_{kv}$ 个查询头均摊后冲击更分散（详见表~\ref{tab:ch4-kv-multitask}）**。" | D5 M3 hedge + D6 P2 GQA 机制 + D5 M2 ref 替代数字 |
| 10 | 第四段末 | "其严重性...受模型规模、训练数据与 GQA 配置共同调制。" | "其严重性...受模型规模、训练数据与 GQA 配置共同调制**；本文以 $H_{kv}$ 作为组间差异的代理变量**。" | D5 confounder 控制策略 |
| 11 | 末段首 | "据此，**本文将低比特路径的设计目标从'对称压低 K 与 V'调整为'优先保护 Key 的表示能力，避免 4-bit 率先落在 Key 上'**。这一调整的核心论据..." | "**因此 Key 侧低比特退化被确立为低比特路径设计的核心约束。这一结论的核心论据**..." | D1 M1 删除 design decision + D4 M3 删元叙述 + D5 M4 自动解决 scope 泄漏 |
| 12 | 末段中 | "(K@INT4 单独触发数量级 PPL 退化)" | "**(\texttt{K@INT4+V@FP16}** 单独触发数量级 PPL 退化)" | D3 M2 完整记号 |
| 13 | 末段末 | "完整跨模型读数与统计协议见表..." | "完整跨模型读数与统计协议**（Bootstrap 95\% CI 与置换检验）**见表..." | D3 M3 协议类型预告 |
| 14 | 删除 | v1 末段曾含"**本文因此把**'Key 侧低比特退化'作为低比特路径设计的核心约束" | (合并删除，以"因此 Key 侧低比特退化被确立..."替代，无"本文因此") | D4 M2 |

### Round 3 结果（候选稿 v2，位置纠正后全部有效）

| Agent | v0 | v1 | v2 | Verdict |
|---|---|---|---|---|
| **D1 顶会** | 7.5 | 7.8 | **8.3** | ❌ NOT PASS（认识论跳跃 P1）|
| **D2 数学** | 6.5 | 7.5 | **8.0** | ❌ NOT PASS（$H_{kv}$ 数学错误 P1） |
| D3 复现 | 4.5 | 7.2 | **8.1** | ✅ PASS（BH-FDR P2 建议）|
| D4 中文 | 6.5 | 7.5 | **8.8** | ✅ PASS（P1 倒装 + P2 元叙述）|
| D5 Skeptical | 4.5 | 6.2 | **8.1** | ✅ PASS |
| D6 博士生 | 6.5 | 8.4 | **9.0** | ✅ PASS（独立确认 D2 数学错误）|

**v2 加权平均 8.38**。4/6 PASS, 2/6 NOT PASS。D6 独立确认 D2 的 $H_{kv}$ 数学错误。

### Round 3 v3 必改清单

#### P1 必改（数学/逻辑错误）

- **D1 P1（认识论跳跃）**：v2 首段"可能不对称" → 末段"被确立为核心约束"跳跃过大。**v3 处理**：第三段末加桥接句"这一诊断结果与首段基于式~\eqref{eq:ch3-error-decomp} 的机制预测一致"。
- **D2 P1（$H_{kv}$ 数学错误）**：v2 "被 $H_{kv}$ 个查询头均摊"——$H_{kv}$ 是 KV 头总数，不是共享同一 KV 头的查询头数量。**v3 处理**："被其对应的 $H_q/H_{kv}$ 个查询头共享，$H_{kv}$ 较大时每组 KV 头影响的查询头数更少"。

#### P2 必改（codex prefs 违规 + 协议精度）

- **D4 P1（codex prefs §45 "主语+因此"倒装）**：v2 首段末"脆弱程度**因此**可能不对称"。**v3 处理**：删"因此"。
- **D4 P2（codex prefs §19 元叙述）**："**本文以** $H_{kv}$ **作为**组间差异的代理变量"。**v3 处理**：改"$H_{kv}$ 在此充当组间差异的代理变量"。
- **D2 P2 建议**：v2 第三段 "（统计协议见表）" 锚定的是统计协议而非原始读数。**v3 处理**：改"（原始读数与统计协议见表~\ref{tab:ch4-kv-ppl}）"。
- **D3 P2 建议**：v2 末段 "Bootstrap 95% CI 与置换检验" 缺 BH-FDR + "置换检验"应精确为 sign-flip。**v3 处理**：改"（Bootstrap 95\% CI、sign-flip 置换检验与 BH-FDR 多重比较校正）"。

---

## §3.2 候选稿 v3（整合 Round 3 6 处必改）

```latex
\section{动机诊断：K/V 敏感性不对称及其设计启示}
\label{sec:ch3-motivation-kv}

由式~\eqref{eq:ch3-error-decomp}，Key 项需经 softmax 非线性放大后再加权进入输出，Value 项则以 $\hat a_i(\hat v_i-v_i)$ 形式线性进入聚合，两条路径在低比特预算下的脆弱程度可能不对称。后文以 K/V 单侧诊断与对称低比特锚点验证这种不对称，为低比特路径的格式选择提供依据。

本节使用两套配置记号：\texttt{K?V?} 表示位宽组合（如 \texttt{K4V8} 即 4-bit Key 与 8-bit Value），\texttt{K@bit+V@bit} 表示以 FP16 隔离非诊断侧的单侧诊断（仅压低标注侧位宽，另一侧保留 FP16）；\texttt{MixedKV} $\equiv$ \texttt{K8V4}。图~\ref{fig:ch3-kv-asymmetry} 呈现压缩诊断视图：\texttt{FP16} 为未量化参考，\texttt{K8V8} 为高精度量化参考，\texttt{K8V4}/\texttt{K4V8} 构成同平均位宽预算下的角色对照，\texttt{K4V4} 提供对称低比特锚点。

\input{figures/fig_ch3_kv_diag_needle}

对 Qwen2.5-1.5B 的单侧 PPL 诊断表明：\texttt{K@INT4+V@FP16} 使 PPL 相对 FP16 基线放大约两个数量级（原始读数与统计协议见表~\ref{tab:ch4-kv-ppl}），而 \texttt{K@FP16+V@INT4} 仅引起基线邻域内的微小变化。32K 任务诊断中，\texttt{K4V8} 使 Qwen2.5-1.5B 与 Qwen2.5-7B 的 RULER 通过率完全归零，\texttt{K8V4} 未出现归零式失稳。同一量化配置下两类指标均显示：在 Qwen 系列当前低比特设定下，最先触发任务级失稳的是 Key 精度下降，而非 Value 的对称压缩；这一诊断结果与首段基于式~\eqref{eq:ch3-error-decomp} 的机制预测一致。

该不对称在不同模型族上强度不同：Qwen 系列（$H_{kv}=2$ 或 $4$）在 \texttt{K4V8} 与 \texttt{K4V4} 下出现完全的检索归零，而具有更高 $H_{kv}$ 或不同头共享结构的模型（如 LLaMA-3.1-8B，$H_{kv}=8$）失稳幅度较小，单 KV 头量化误差被其对应的 $H_q/H_{kv}$ 个查询头共享，$H_{kv}$ 较大时每组 KV 头影响的查询头数更少（详见表~\ref{tab:ch4-kv-multitask}）。其严重性与触发位宽的具体边界仍受模型规模、训练数据与 GQA 配置共同调制；$H_{kv}$ 在此充当组间差异的代理变量。

因此 Key 侧低比特退化被确立为低比特路径设计的核心约束。这一结论的核心论据是单侧 PPL 诊断的隔离证据（\texttt{K@INT4+V@FP16} 单独触发数量级 PPL 退化）；\texttt{K4V8}/\texttt{K4V4} 的位宽对照作为剂量-响应（dose-response）验证与之同向，但因二者同时压低 K 与 V，单独不构成 K 主导的隔离推断。完整跨模型读数与统计协议（Bootstrap 95\% CI、sign-flip 置换检验与 BH-FDR 多重比较校正）见表~\ref{tab:ch4-kv-ppl}、表~\ref{tab:ch4-kv-multitask} 与第~\ref{sec:exp-kv-sensitivity}~节。
```

### 修改对照表（v2 → v3）

| # | 位置 | v2 | v3 | 来源 |
|---|---|---|---|---|
| 1 | 首段末 | "...脆弱程度**因此**可能不对称" | "...脆弱程度可能不对称"（删"因此"） | D4 P1（§45 主语+因此倒装） |
| 2 | 第三段末 | "...在 Qwen 系列当前低比特设定下，最先触发任务级失稳的是 Key 精度下降，而非 Value 的对称压缩。" | "...而非 Value 的对称压缩**；这一诊断结果与首段基于式~\eqref{eq:ch3-error-decomp} 的机制预测一致**。" | D1 P1 认识论跳跃 |
| 3 | 第三段量级 ref | "（统计协议见表~\ref{tab:ch4-kv-ppl}）" | "（**原始读数与**统计协议见表~\ref{tab:ch4-kv-ppl}）" | D2 P2 |
| 4 | 第四段 GQA 机制 | "单 KV 头量化误差被 **$H_{kv}$ 个**查询头**均摊后冲击更分散**" | "单 KV 头量化误差被**其对应的 $H_q/H_{kv}$ 个**查询头**共享，$H_{kv}$ 较大时每组 KV 头影响的查询头数更少**" | D2 P1 数学错误 + D6 独立确认 |
| 5 | 第四段末 | "**本文以** $H_{kv}$ **作为**组间差异的代理变量" | "**$H_{kv}$ 在此充当**组间差异的代理变量" | D4 P2 元叙述 |
| 6 | 末段统计协议 | "（Bootstrap 95\% CI 与**置换检验**）" | "（Bootstrap 95\% CI、**sign-flip 置换检验与 BH-FDR 多重比较校正**）" | D3 P2 协议精度 |

### Round 4 结果（候选稿 v3）— 全部 PASS ✅

| Agent | v0 | v1 | v2 | v3 | Verdict |
|---|---|---|---|---|---|
| D1 顶会 | 7.5 | 7.8 | 8.3 | **8.6** | ✅ PASS |
| D2 数学 | 6.5 | 7.5 | 8.0 | **8.8** | ✅ PASS |
| D3 复现 | 4.5 | 7.2 | 8.1 | **9.0** | ✅ PASS |
| D4 中文 | 6.5 | 7.5 | 8.8 | **9.2** | ✅ PASS |
| D5 Skeptical | 4.5 | 6.2 | 8.1 | **8.6** | ✅ PASS |
| D6 博士生 | 6.5 | 8.4 | 9.0 | **9.2** | ✅ PASS（封版） |

**v3 加权平均 8.90**（v2 8.38 → v3 8.90，+0.52）。

### D5/D6 "何时停止"判定（关键决策依据）

- D5：「§3.2 可以停止迭代。当前版本已达答辩与预投稿合理边界。」
- D6：「v3 封版，可投稿。每增加一轮改动的边际收益已低于引入新问题的风险。」

### Round 4 D5/D6 提的 R1/R2/P3（不阻塞，归档供终稿）

- D5 R1: 桥接句"机制预测"方向性依赖读者从公式推导 K 更脆弱
- D5 R2: GQA 单因素归因 $H_{kv}$（$H_q$ 也参与调制）
- D2 P3: $H_q/H_{kv}$ 前提显式化（"$H_q$ 由 16 降至 32" 数值路径自含）
- D1 P3: 末段"被确立"缺模型族范围限定（"在本文评测模型族范围内"）
- D4 P3: 第四段 GQA 双层推导句节奏略密
- D6 P3: BH-FDR 在括号内可考虑收口为"完整统计协议"

### ✅ §3.2 落地（v3 → thesis/chapters/ch3_method.tex line 45-58）

**Edit 完成时间**：2026-05-08
**xelatex 编译验证**：pass 1 + pass 2 通过，96 页，零 LaTeX Error，零 undefined references
**.tex 行数变化**：+6 -6（净零，6 段重写：首段、记号映射、PPL 诊断、LLaMA、末段；图 \input 位置移到段 2 后）
**git diff --check**：✅ OK
**Underfull 警告**：line 756（与 §3.2 无关，是已有问题）

---

## §3.2 6-Agent 4-Round 审查总结

**结论**：§3.2 经过 4 轮迭代（v0→v3）+ 24 个 agent 报告（6 reviewer × 4 rounds）后达到 PhD 论文方法章动机诊断节的合理标准。

**关键演化**：
- v0 (commit 90cb485) → v1: 跨章 ref 5→2 + 删章末路线图 + 首段研究过程式表达
- v1 → v2: 18 处必改一次集中（D1 末段越位 + D2 量级 ref + D3 完整记号 + D4 三处 codex prefs + D5 同向独立性 + D6 GQA 机制）
- v2 → v3: 6 处必改（D1 认识论跳跃桥接 + D2 $H_{kv}$ 数学修正 + D2 量级 ref 措辞 + D3 BH-FDR + D4 倒装 + D4 元叙述）

**6-agent multi-perspective 审查的实战收益**：
1. D2 抓出 v2 的 $H_{kv}$ 数学错误（"$H_{kv}$ 个查询头均摊"应为"$H_q/H_{kv}$ 个查询头共享"），D6 round 3 也独立确认——级联 cross-validation 让 v3 必改优先级毋庸置疑
2. D5 v0=4.5 → v3=8.6 的 +4.1 大幅上升：selection bias / claim 边界 / spec gap 类问题需要正面回应（hedge / 桥接 / 删 over-claim），一旦回应到位分数立即跃升
3. v3 一次合并 6 处来自 4 个不同 reviewer 的反对，全部 PASS 验证"reviewer-centric 修复反向产生 cross-reviewer 加分"模式
4. §3.2 比 §3.1 收敛快一轮（4 轮 vs 5 轮），原因是 §3.2 v0 起点已是 commit 90cb485 部分修复后状态

**§3.2 vs §3.1 横向对比**：

| 维度 | §3.1 | §3.2 |
|---|---|---|
| 类型 | Problem formalization（数学严谨） | Motivation diagnosis（数据/证据） |
| 轮数 | 5 (v0→v4) | 4 (v0→v3) |
| Agent 报告数 | 30 | 24 |
| v 终态加权 | 9.02 | 8.90 |
| 最严苛 reviewer | D5 (round 4 NOT PASS) | D5 (round 1+2 NOT PASS) + D3 (round 1 4.5) |
| 关键 critical bug | $\Delta_{\mathrm{beh}}$ KL 代理 gap | $H_{kv}$ 均摊数学错误 |

---

## §3.1 D 阶段（候选稿质量门）— Round 1 审查

### Round 1 评分汇总

| Agent | 分数 | Verdict | 关键发现 |
|---|---|---|---|
| D1 顶会 | 8.5 | ✅ PASS | 形式签名、首段、章末过渡均达标 |
| D2 数学 | 9.0 | ✅ PASS | 7 项数学严谨核查全过 |
| D3 复现 | 9.0 | ✅ PASS | 跨章引用合理；占位符延迟到 §3.5 合规 |
| **D4 中文** | **7.0** | 🔴 **NOT PASS** | 6 处中文写作残留 |
| D5 Skeptical | 8.5 | ✅ PASS | "概念层"hedge 已配 falsifier 钩子 |
| D6 博士生 | 8.5 | ✅ PASS | 概念引入流畅，可一遍读懂 |

### D4 NOT PASS 的 6 个具体问题（必改）

1. **L6 末句**「下文先固定单头 Decode 注意力的记号，再对量化引起的输出误差作精确代数分解」— "先 X 再 Y" 教科书路线图
2. **L6 第二句**「因此本文不以 X 作为唯一对象，而是把 Y 共同视作...」— 双重否定 hedge
3. **L26**「于是，KV Cache 量化在概念层上的目标可写为」— "于是"+"在概念层上"+"可写为" 三连套话
4. **L30 末**「其形式在概念层成立，不要求各量化路径共享同一标量损失」— "概念层" meta hedge 残留
5. **L40**「系恒等代数变形」— "系"文言味重 + 与上文"精确代数展开"重复
6. **L47**「由此，KV Cache 量化在本文中被形式化为...；第~\ref...~节进一步诊断...」— 结尾"由此...下文"过渡套话

### 高价值 Minor 建议（采纳决策）

| 来源 | 建议 | 决策 |
|---|---|---|
| D1+D6 同向 | L16 多头声明前移到 L8 之前 | ✅ 采纳（写作流畅度）|
| D6 | L40 显式命名「聚合侧/Value 通路、分布侧/Key 通路」 | ✅ 采纳（术语锚点）|
| D1 | L8 $d_v=d_k$ 加经验事实说明 | ✅ 采纳（防理论读者质疑普适性）|
| D1 | L40 "并非独立" → "耦合"或"非加性可分" | ✅ 采纳（措辞收紧）|
| D6 | L30 加 KL/JSD 实例 | ❌ 不采（违反 D5 spoiler 警告）|
| D2/D3 | L18 加可微/作用域 polymorph | ❌ 不采（D3 已自承 §3.5 解决）|

### 候选稿 v1（待 Round 2 审查）

```latex
\section{注意力近似误差的代数分解与问题形式化}
\label{sec:ch3-problem}

下游任务感知到的是注意力分布 $a$ 与输出 $o$，而非 $K, V$ 的逐元素重建距离；本文据此将 $(a,o)$ 共同作为需保持的行为对象。

本节默认在单头 MHA 设定下展开。约定 $q$ 视作行向量 $q\in\mathbb{R}^{1\times d_k}$，历史上下文长度为 $S$，$K\in\mathbb{R}^{S\times d_k}$、$V\in\mathbb{R}^{S\times d_v}$ 由其行向量 $k_i, v_i$ 拼接而成；本文实验涵盖的 Qwen2.5/LLaMA-3 系列均满足 $d_v=d_k$ 约定（参见第~\ref{sec:ch2-kv-memory}~节）。标准单头注意力可写为
\begin{equation}
a=\mathrm{softmax}\!\left(\frac{qK^\top}{\sqrt{d_k}}\right), \qquad o=aV,
\end{equation}
其中 $a\in\mathbb{R}^{1\times S}$ 表示注意力分布（按分量索引为 $a_i\in\mathbb{R}$），$o\in\mathbb{R}^{1\times d_v}$ 表示注意力输出。基于此，本文将注意力行为形式化为如下联合对象：
\begin{equation}
\mathcal{B}(q,K,V):=(a,o).
\end{equation}
多层、多头情形按层索引 $\ell$ 与头索引 $h$ 重复，记为 $q^{(\ell,h)}, K^{(\ell,h)}$ 等；GQA/MQA 下查询头到 KV 头的映射已在第~\ref{sec:ch2-kv-memory}~节给出。

设 $Q_{\theta_K}(\cdot)$ 与 $Q_{\theta_V}(\cdot)$ 分别表示作用于 Key 与 Value 的量化映射；参数 $\theta_K, \theta_V$ 的具体含义（scale、zero-point、bit-width 等）以及作用域（逐元素、逐通道或逐 token）由量化路径决定，详见第~\ref{sec:ch3-paths}~节。量化后的 Key 与 Value 记为
\begin{equation}
\hat K = Q_{\theta_K}(K), \qquad \hat V = Q_{\theta_V}(V),
\end{equation}
对应的量化后注意力分布与输出为
\begin{equation}
\hat a=\mathrm{softmax}\!\left(\frac{q\hat K^\top}{\sqrt{d_k}}\right), \qquad \hat o=\hat a \hat V.
\end{equation}
KV Cache 量化的目标即
\begin{equation}
\min_{\theta_K,\theta_V}\Delta_{\mathrm{beh}}\big((a,o),(\hat a,\hat o)\big),
\end{equation}
其中 $\Delta_{\mathrm{beh}}: (\mathbb{R}^{1\times S}\times\mathbb{R}^{1\times d_v})^2 \to \mathbb{R}_{\ge 0}$ 满足 $\Delta_{\mathrm{beh}}(x,x)=0$，刻画量化前后注意力行为的联合偏移；$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（第~\ref{sec:ch3-calibration}~节）。

由 $\hat o=\hat a\hat V$ 与 $o=aV$ 的定义，输出误差可作如下精确代数展开：
\begin{align}
\hat o-o
&=\sum_{i=1}^{S}\hat a_i\hat v_i-\sum_{i=1}^{S}a_i v_i \\
&=\sum_{i=1}^{S}(\hat a_i\hat v_i-\hat a_i v_i)+\sum_{i=1}^{S}(\hat a_i v_i-a_i v_i) \\
&=\sum_{i=1}^{S}\hat a_i(\hat v_i-v_i)+\sum_{i=1}^{S}(\hat a_i-a_i)v_i.
\label{eq:ch3-error-decomp}
\end{align}
式~\eqref{eq:ch3-error-decomp} 是恒等变形。右侧第一项（聚合侧/Value 通路）描述 Value 侧内容被量化后如何进入聚合结果；右侧第二项（分布侧/Key 通路）描述 Key 侧扰动经 logits 与 softmax 改变注意力分布后如何传到输出。其中第一项的权重为量化后分布 $\hat a_i$ 而非参考分布 $a_i$，因此聚合侧误差与 Key 侧扰动并非加性可分——若 Key 量化已改变 $\hat a$，聚合项的有效权重也随之变化。

% 图题：图 3-1 注意力误差的两条耦合传播路径及其精确代数分解
\input{figures/fig1_error_decomposition}

由式~\eqref{eq:ch3-error-decomp}，下游任务感知到的是注意力行为偏移而非 $K, V$ 的逐元素距离：Key 侧扰动通过 $q\hat K^\top$ 与 softmax 影响分布形态，Value 侧扰动则在已量化分布 $\hat a$ 加权下进入输出。仅以张量重建误差为度量，将忽略 softmax 非线性与加权聚合共同导致的行为层失真。

至此，KV Cache 量化被形式化为注意力行为保持问题。
```

### 修改对照表（v0 commit dd869e4 → v1 候选稿）

| # | 位置 | v0 | v1 | 来源 |
|---|---|---|---|---|
| 1 | §3.1 首段 | 三句结构: motivation+对象+路线图 | 单句直接陈述 | D4 NOT-PASS-1+2 |
| 2 | L8 多头声明 | 在 line 16 | 前移到 line 8 之前 | D1+D6 |
| 3 | L8 $d_v=d_k$ | "本文沿用 §2.2 约定" | "本文实验涵盖 Qwen2.5/LLaMA-3 均满足... §2.2" | D1 |
| 4 | L26 | "于是，KV Cache 量化在概念层上的目标可写为" | "KV Cache 量化的目标即" | D4 NOT-PASS-3 |
| 5 | L30 末 | "其形式在概念层成立，不要求各量化路径共享同一标量损失。具体实例化..." | "$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（§3.4）" | D4 NOT-PASS-4 |
| 6 | L40 | "系恒等代数变形" + "并非独立" | "是恒等变形" + "并非加性可分" | D4 NOT-PASS-5 + D1 minor |
| 7 | L40 path 命名 | 无 | 加「聚合侧/Value 通路」「分布侧/Key 通路」 | D6 minor |
| 8 | L47 | "由此...第~\ref...~节进一步诊断..." | "至此，KV Cache 量化被形式化为注意力行为保持问题。" | D4 NOT-PASS-6 |

### Round 2 结果（候选稿 v1）

| Agent | 分数 | Verdict |
|---|---|---|
| D1 顶会 | 8.5 | ✅ PASS |
| D2 数学 | 9.0 | ✅ PASS |
| D3 复现 | 8.0 | ✅ PASS |
| **D4 中文** | **7.0** | 🔴 **NOT PASS** |
| D5 Skeptical | 8.0 | ✅ PASS |
| D6 博士生 | 8.5 | ✅ PASS |

**D4 NOT PASS 关键问题**（与 codex prefs `/Users/chenzilang/.codex/rules/writing_preferences.md` 对齐）：

1. L334「本文据此将 $(a,o)$ 共同作为需保持的行为对象」— meta 自述
2. L336「本节默认在单头 MHA 设定下展开」— 教科书结构性自述
3. L340「基于此，本文将注意力行为形式化为如下联合对象」— 「基于此，本文将...」违反 codex prefs §核心风格
4. L375「至此，KV Cache 量化被形式化为注意力行为保持问题」— 模板式总结收束
5. L373 与 L334 内容重复（"下游任务感知到的是行为偏移而非张量距离"）

## §3.1 候选稿 v2（按 codex prefs + Round 2 D4 反馈重写）

```latex
\section{注意力近似误差的代数分解与问题形式化}
\label{sec:ch3-problem}

下游任务感知到的是注意力分布 $a$ 与注意力输出 $o$，而非 $K, V$ 的逐元素重建距离。因此本文以 $(a,o)$ 这对联合对象作为量化保持的目标，并在单头 MHA 设定下推导其代数分解。

约定 $q$ 视作行向量 $q\in\mathbb{R}^{1\times d_k}$，历史上下文长度为 $S$，$K\in\mathbb{R}^{S\times d_k}$、$V\in\mathbb{R}^{S\times d_v}$ 由其行向量 $k_i, v_i$ 拼接而成；本文实验涵盖的 Qwen2.5/LLaMA-3 系列均满足 $d_v=d_k$ 约定（参见第~\ref{sec:ch2-kv-memory}~节）。标准单头注意力可写为
\begin{equation}
a=\mathrm{softmax}\!\left(\frac{qK^\top}{\sqrt{d_k}}\right), \qquad o=aV,
\end{equation}
其中 $a\in\mathbb{R}^{1\times S}$ 表示注意力分布（按分量索引为 $a_i\in\mathbb{R}$），$o\in\mathbb{R}^{1\times d_v}$ 表示注意力输出。注意力行为记作联合对象
\begin{equation}
\mathcal{B}(q,K,V):=(a,o).
\end{equation}
多层、多头情形按层索引 $\ell$ 与头索引 $h$ 平行展开，记为 $q^{(\ell,h)}, K^{(\ell,h)}$ 等；GQA/MQA 下查询头到 KV 头的映射已在第~\ref{sec:ch2-kv-memory}~节给出。

设 $Q_{\theta_K}(\cdot)$ 与 $Q_{\theta_V}(\cdot)$ 分别表示作用于 Key 与 Value 的量化映射；参数 $\theta_K, \theta_V$ 的具体含义（scale、zero-point、bit-width 等）以及作用域（逐元素、逐通道或逐 token）由量化路径决定，详见第~\ref{sec:ch3-paths}~节。量化后的 Key 与 Value 记为
\begin{equation}
\hat K = Q_{\theta_K}(K), \qquad \hat V = Q_{\theta_V}(V),
\end{equation}
对应的量化后注意力分布与输出为
\begin{equation}
\hat a=\mathrm{softmax}\!\left(\frac{q\hat K^\top}{\sqrt{d_k}}\right), \qquad \hat o=\hat a \hat V.
\end{equation}
KV Cache 量化的目标即
\begin{equation}
\min_{\theta_K,\theta_V}\Delta_{\mathrm{beh}}\big((a,o),(\hat a,\hat o)\big),
\end{equation}
其中 $\Delta_{\mathrm{beh}}: (\mathbb{R}^{1\times S}\times\mathbb{R}^{1\times d_v})^2 \to \mathbb{R}_{\ge 0}$ 满足 $\Delta_{\mathrm{beh}}(x,x)=0$，刻画量化前后注意力行为的联合偏移；$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（第~\ref{sec:ch3-calibration}~节）。

由 $\hat o=\hat a\hat V$ 与 $o=aV$ 的定义，输出误差可作如下精确代数展开：
\begin{align}
\hat o-o
&=\sum_{i=1}^{S}\hat a_i\hat v_i-\sum_{i=1}^{S}a_i v_i \\
&=\sum_{i=1}^{S}(\hat a_i\hat v_i-\hat a_i v_i)+\sum_{i=1}^{S}(\hat a_i v_i-a_i v_i) \\
&=\sum_{i=1}^{S}\hat a_i(\hat v_i-v_i)+\sum_{i=1}^{S}(\hat a_i-a_i)v_i.
\label{eq:ch3-error-decomp}
\end{align}
式~\eqref{eq:ch3-error-decomp} 是恒等变形。右侧第一项（聚合侧/Value 通路）描述 Value 侧内容被量化后如何进入聚合结果；右侧第二项（分布侧/Key 通路）描述 Key 侧扰动经 logits 与 softmax 改变注意力分布后如何传到输出。第一项的权重为量化后分布 $\hat a_i$ 而非参考分布 $a_i$，因此聚合侧误差与 Key 侧扰动并非加性可分——若 Key 量化已改变 $\hat a$，聚合项的有效权重也随之变化。仅以张量重建误差为度量，将遗漏 softmax 非线性与加权聚合在式~\eqref{eq:ch3-error-decomp} 中共同造成的耦合失真。

% 图题：图 3-1 注意力误差的两条耦合传播路径及其精确代数分解
\input{figures/fig1_error_decomposition}
```

### 修改对照表（v1 → v2）

| # | 位置 | v1 | v2 | 来源 |
|---|---|---|---|---|
| 1 | 首段 | 单句 + L336 单独段「本节默认在...」 | 合并：「...因此本文以 $(a,o)$ 这对联合对象作为量化保持的目标，并在单头 MHA 设定下推导其代数分解」 | codex prefs §核心风格 + D4 |
| 2 | $\mathcal{B}$ 引入 | "基于此，本文将注意力行为形式化为如下联合对象" | "注意力行为记作联合对象" | codex prefs §核心风格（meta 自述） |
| 3 | 多头声明 | "按...重复" | "按...平行展开" | 用词更技术化 |
| 4 | 章末 L373 段 | 独立段重复首段 claim | 合并到 L368 段末（"将遗漏 softmax 非线性..."）| D4 + 偏好"段落节奏要自然" |
| 5 | L375「至此...」 | 独立总结句 | **删除整句** | codex prefs §核心风格 + D4 |
| 6 | "忽略" → "遗漏" | "将忽略" | "将遗漏" | D5 minor "忽略主语不明确" |

### codex prefs 对照核查（v2）

| codex prefs 条款 | v2 是否符合 |
|---|---|
| 写得像作者在推导自己的研究设计 | ✅（"在单头 MHA 设定下推导其代数分解"） |
| 避免"基于这一考虑""这一安排使本文能够" | ✅（已删） |
| 段落节奏要自然，避免整齐第一/第二/第三 | ✅（无 enumeration） |
| 多用具体机制，少用抽象评价 | ✅（"聚合侧/Value 通路""分布侧/Key 通路"绑公式右侧两项） |
| 把格式选择和计算图角色直接绑定 | ✅（Key 进入 $q\hat K^\top$ 与 softmax，Value 在 $\hat a$ 加权下） |
| 已经引入过的领域词直接使用 | ✅（"Decode-only" 未出现因 §3.1 不需要; 量化记号统一） |
| 避免"xxxx 上"位置化表达 | ✅（无） |
| 避免冒号式展开 | ✅（无 ":" 展开） |
| 避免"本文因此"英文式中文 | ✅（用"因此本文以..."正常顺序） |
| 章节过渡写得短而直接 | ✅（无章末路线图） |

### Round 3 结果（候选稿 v2）

| Agent | 分数 | Verdict | 关键判断 |
|---|---|---|---|
| D1 顶会 | 8.5 | ✅ PASS | 形式化达标；末段"耦合失真"作为 §3.4 解法动机微弱 spoiler |
| D2 数学 | 8.2 | ✅ PASS | 7/8 ✅；2 minor gap：$\Delta_{\mathrm{beh}}$ 弱定义脚注 + 多头优化语义未消歧 |
| D3 复现 | 8.5 | ✅ PASS | $\Delta_{\mathrm{beh}}$ 完整签名让 `BehaviorLoss` 抽象类可写 |
| D4 中文 | 8.8 | ✅ PASS | 4 处 v1 NOT-PASS 全部 ✅；codex prefs 12 项 11 ✅ + 1 ⚠️ |
| **D5 Skeptical** | **6.5** | 🔴 **NOT PASS** | 4 处实质必改：耦合失真未定义 + 代数分解 vs §3.4 KL 语义断裂 + $d_v=d_k$ 作用未说 + GQA 适用性缺桥 |
| **D6 博士生** | **7.8** | ❌ **NOT PASS** | 2 处必改：首段无路线预告 + 段 5 动机后置 |

**Round 3 加权平均**：(8.5+8.2+8.5+8.8+6.5+7.8)/6 = **8.05**，但 D5 / D6 NOT PASS 不容忽略。

### Round 3 必改清单分流（v3 设计依据）

#### 必采纳（实质问题）

- **D5-1（末段"耦合失真"）**：删除新造术语，精确锚定到第二项分布偏移 + 第一项权重 $\hat a_i$
- **D5-2（代数分解 vs §3.4 KL 语义断裂）**：§3.1 末段桥接「离线校准据此采用注意力分布上的 KL 散度作为 $\Delta_{\mathrm{beh}}$ 的可执行代理（§3.4）」
- **D5-3（$d_v=d_k$ 作用）**：补「由此 $q$ 与 $o$ 同维」
- **D5-4（GQA 单头适用性）**：补「本节代数分析对每个 KV 头独立成立，多个查询头共享同一组 KV 量化误差」
- **D2 Gap 1**：补「$\Delta_{\mathrm{beh}}$ 作为损失函数使用，无需满足度量空间的对称性或三角不等式」
- **D2 Gap 2**：补「多头情形下 $(\theta_K, \theta_V)$ 按层与头独立实例化」

#### 部分采纳

- **D6-2（动机前置）**：保持位置在公式之后但末段重组，把"张量重建误差并不刻画这种交叉依赖"作为正向技术陈述（不用 D6 建议的"传统张量重建度量无法捕捉..."否定开场，避免违反 codex prefs §核心风格"少用防御式负向"）

#### 不采纳

- **D6-1（首段路线预告）**：D6 建议「本节首先给出标准注意力记号，继而形式化量化映射，最终精确分解」是 PPT 式路线图，违反 codex prefs §具体偏好第 28 行「研究过程式 ≠ PPT 式」。codex prefs 作为用户偏好硬约束，优先级高于 D6 阅读体验。

#### Codex prefs 反馈（D4 提出，待用户决策）

- 建议补充条款 1：交叉引用密度控制（同节内 `\ref{}` 超过 2 次时合并）
- 建议补充条款 2：批评对象显式引出规则（方法推导段内批评式收尾必须先引出被批评对象）

---

## §3.1 候选稿 v3（综合 Round 3 必采纳 + 部分采纳）

```latex
\section{注意力近似误差的代数分解与问题形式化}
\label{sec:ch3-problem}

下游任务感知到的是注意力分布 $a$ 与注意力输出 $o$，而非 $K, V$ 的逐元素重建距离。因此本文以 $(a,o)$ 这对联合对象作为量化保持的目标，并在单头 MHA 设定下推导其代数分解。

约定 $q$ 视作行向量 $q\in\mathbb{R}^{1\times d_k}$，历史上下文长度为 $S$，$K\in\mathbb{R}^{S\times d_k}$、$V\in\mathbb{R}^{S\times d_v}$ 由其行向量 $k_i, v_i$ 拼接而成；本文实验涵盖的 Qwen2.5/LLaMA-3 系列均满足 $d_v=d_k$ 约定，由此 $q$ 与 $o$ 同维（参见第~\ref{sec:ch2-kv-memory}~节）。标准单头注意力可写为
\begin{equation}
a=\mathrm{softmax}\!\left(\frac{qK^\top}{\sqrt{d_k}}\right), \qquad o=aV,
\end{equation}
其中 $a\in\mathbb{R}^{1\times S}$ 表示注意力分布（按分量索引为 $a_i\in\mathbb{R}$），$o\in\mathbb{R}^{1\times d_v}$ 表示注意力输出。注意力行为记作联合对象
\begin{equation}
\mathcal{B}(q,K,V):=(a,o).
\end{equation}
多层、多头情形按层索引 $\ell$ 与头索引 $h$ 平行展开，记为 $q^{(\ell,h)}, K^{(\ell,h)}$ 等；本节代数分析对每个 KV 头独立成立，GQA/MQA 下查询头到 KV 头的映射已在第~\ref{sec:ch2-kv-memory}~节给出，多个查询头共享同一组 KV 量化误差。

设 $Q_{\theta_K}(\cdot)$ 与 $Q_{\theta_V}(\cdot)$ 分别表示作用于 Key 与 Value 的量化映射；参数 $\theta_K, \theta_V$ 的具体含义（scale、zero-point、bit-width 等）以及作用域（逐元素、逐通道或逐 token）由量化路径决定，详见第~\ref{sec:ch3-paths}~节。量化后的 Key 与 Value 记为
\begin{equation}
\hat K = Q_{\theta_K}(K), \qquad \hat V = Q_{\theta_V}(V),
\end{equation}
对应的量化后注意力分布与输出为
\begin{equation}
\hat a=\mathrm{softmax}\!\left(\frac{q\hat K^\top}{\sqrt{d_k}}\right), \qquad \hat o=\hat a \hat V.
\end{equation}
KV Cache 量化的目标即
\begin{equation}
\min_{\theta_K,\theta_V}\Delta_{\mathrm{beh}}\big((a,o),(\hat a,\hat o)\big),
\end{equation}
其中 $\Delta_{\mathrm{beh}}: (\mathbb{R}^{1\times S}\times\mathbb{R}^{1\times d_v})^2 \to \mathbb{R}_{\ge 0}$ 满足 $\Delta_{\mathrm{beh}}(x,x)=0$，刻画量化前后注意力行为的联合偏移；其作为损失函数使用，无需满足度量空间的对称性或三角不等式。$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（第~\ref{sec:ch3-calibration}~节），多头情形下 $(\theta_K, \theta_V)$ 按层与头独立实例化。

由 $\hat o=\hat a\hat V$ 与 $o=aV$ 的定义，输出误差可作如下精确代数展开：
\begin{align}
\hat o-o
&=\sum_{i=1}^{S}\hat a_i\hat v_i-\sum_{i=1}^{S}a_i v_i \\
&=\sum_{i=1}^{S}(\hat a_i\hat v_i-\hat a_i v_i)+\sum_{i=1}^{S}(\hat a_i v_i-a_i v_i) \\
&=\sum_{i=1}^{S}\hat a_i(\hat v_i-v_i)+\sum_{i=1}^{S}(\hat a_i-a_i)v_i.
\label{eq:ch3-error-decomp}
\end{align}
式~\eqref{eq:ch3-error-decomp} 是恒等变形。右侧第一项（聚合侧/Value 通路）描述 Value 侧内容被量化后如何进入聚合结果；右侧第二项（分布侧/Key 通路）描述 Key 侧扰动经 logits 与 softmax 改变注意力分布后如何传到输出。第一项的权重为量化后分布 $\hat a_i$ 而非参考分布 $a_i$，因此聚合侧误差与 Key 侧扰动并非加性可分——Key 量化通过 $\hat a$ 同时改变第二项的分布偏移与第一项的聚合权重。张量重建误差并不刻画这种交叉依赖；离线校准据此采用注意力分布上的 KL 散度作为 $\Delta_{\mathrm{beh}}$ 的可执行代理（第~\ref{sec:ch3-calibration}~节）。

% 图题：图 3-1 注意力误差的两条耦合传播路径及其精确代数分解
\input{figures/fig1_error_decomposition}
```

### 修改对照表（v2 → v3）

| # | 位置 | v2 | v3 | 来源 |
|---|---|---|---|---|
| 1 | $d_v=d_k$ 约定 | "...均满足 $d_v=d_k$ 约定（参见 §2.2）" | "...均满足 $d_v=d_k$ 约定，**由此 $q$ 与 $o$ 同维**（参见 §2.2）" | D5-3 |
| 2 | 多头声明 | "按...平行展开...GQA/MQA 下查询头到 KV 头的映射已在 §2.2 给出" | "按...平行展开...**本节代数分析对每个 KV 头独立成立**，GQA/MQA 下...给出，**多个查询头共享同一组 KV 量化误差**" | D5-4 |
| 3 | $\Delta_{\mathrm{beh}}$ 定义 | "刻画量化前后注意力行为的联合偏移；$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（§3.4）" | "刻画量化前后注意力行为的联合偏移；**其作为损失函数使用，无需满足度量空间的对称性或三角不等式。**$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（§3.4），**多头情形下 $(\theta_K, \theta_V)$ 按层与头独立实例化**" | D2 Gap 1+2 |
| 4 | 末段"耦合失真" | "Key 量化已改变 $\hat a$，聚合项的有效权重也随之变化。仅以张量重建误差为度量，将遗漏 softmax 非线性与加权聚合在式~\eqref... 中共同造成的耦合失真" | "**Key 量化通过 $\hat a$ 同时改变第二项的分布偏移与第一项的聚合权重。张量重建误差并不刻画这种交叉依赖；离线校准据此采用注意力分布上的 KL 散度作为 $\Delta_{\mathrm{beh}}$ 的可执行代理（§3.4）**" | D5-1 + D5-2 + D6-2 部分 |

### Round 3 NOT PASS issue 处理验证表

| Issue | 来源 | v3 处理 |
|---|---|---|
| 末段"耦合失真"未定义 | D5-1 | ✅ 删除该术语，精确化为"分布偏移 + 聚合权重" |
| §3.1 vs §3.4 语义断裂 | D5-2 | ✅ 末段补 KL on $a$ 桥接句 |
| $d_v=d_k$ 作用未说 | D5-3 | ✅ 补"由此 $q$ 与 $o$ 同维" |
| GQA 适用性缺桥 | D5-4 | ✅ 补"本节代数分析对每个 KV 头独立成立...多个查询头共享同一组 KV 量化误差" |
| $\Delta_{\mathrm{beh}}$ 弱定义 | D2 Gap 1 | ✅ 补"作为损失函数使用，无需对称/三角" |
| 多头优化语义 | D2 Gap 2 | ✅ 补"$(\theta_K, \theta_V)$ 按层与头独立实例化" |
| 段 5 动机后置 | D6-2 部分 | ✅ 末段重组，"张量重建误差并不刻画" → 立即接 KL 桥接（正向陈述，不用否定开场） |
| 首段路线预告 | D6-1 | ❌ 不采纳（违反 codex prefs §段落衔接是研究过程式 vs PPT 式） |

### codex prefs 12 项 (A-L) 再核查（v3）

A. 推导研究设计 ✅；B. 正向克制 ✅；C. 防御式负向 ✅（仅"无需满足"和"并不刻画"两处技术 spec 必要负向）；D. 具体机制 ✅（"分布偏移 + 聚合权重"绑定第一/第二项）；E. 元叙述 ✅；F. 段落节奏 ✅；G. 教科书过渡词 ✅；H. 冒号式展开 ✅；I. 位置化"上"表达 ✅；J. 英文式倒装 ✅；K. 章节过渡 ✅（无章末路线图）；L. 衔接研究过程式 ✅。

### Round 4 结果（候选稿 v3）

| Agent | v3 分数 | Verdict | 关键发现 |
|---|---|---|---|
| D1 顶会 | 9.0 | ✅ PASS | 末段 KL 桥接是合理桥接非 spoiler；$Q_{\theta_K}$ 列举 minor 仍未修 |
| D2 数学 | 9.2 | ✅ PASS | Gap 1+2 修复；2 minor：$d_v=d_k$ 因果语气；$\min$ 公式无层/头下标 |
| D3 复现 | 9.2 | ✅ PASS | KL 桥接句使复现率 80%→87%；零阻塞性障碍 |
| D4 中文 | 8.6 | ✅ PASS | 3 minor：第 529 行括号 ref 删；第 537 行三逗号拆；"据此"→"因此" |
| **D5 Skeptical** | **7.5** | 🔴 **NOT PASS** | 4 处 P1/P2：KL 代理 gap + GQA 共享悬挂 + 无对称三角暴露 spec + $(a,o)$ 缺正面论证 |
| D6 博士生 | 8.6 | ✅ PASS | **明确「我的 PASS 与 codex prefs 一致，不是伪 PASS」**；接受 v3 拒绝路线预告 |

**Round 4 加权平均**：(9.0+9.2+9.2+8.6+7.5+8.6)/6 = **8.68**。5/6 PASS，D5 仍 NOT PASS。

### Round 4 D5 NOT PASS 处理分流

| D5 issue | 性质 | v4 处理 |
|---|---|---|
| P1 #1: KL 代理 gap（KL 只直接惩罚第二项，第一项聚合误差需间接论证） | 真 valid 实质问题 | ✅ 末段补论证桥：「KL 直接惩罚第二项分布偏移，经 $\hat a$ 在第一项中的权重作用间接约束聚合侧」 |
| P1 #2: GQA "多个查询头共享同一组 KV 量化误差" 悬挂 | D5 自己 round 3 建议措辞引发，删半句即可 | ✅ 删除该半句，回到中性「对每个 KV 头独立成立 + GQA 映射在 §2.2」 |
| P2: "无需对称/三角"暴露 spec | 与 D2/D4/D6 三人共识冲突（保留派 3:1 反对派 2） | ❌ 不动（D2 数学家明确判定为充分覆盖散度类公理子集；D5 是 metalevel 焦虑非数学问题） |
| P2: $(a,o)$ 联合目标缺正面论证 | valid minor | ✅ 末段补一句：「两条通路同时进入输出，单独追踪 $a$ 或 $o$ 均会遗漏一侧」 |

### Round 4 其他 minor 一并处理

| 来源 | issue | v4 处理 |
|---|---|---|
| D2 minor 1 | "由此 $q$ 与 $o$ 同维"因果语气暗示推导依赖 | 不动（与 D4 minor 1 同位置，但 D4 是建议删括号 ref，措辞保留） |
| D2 minor 2 | $\min$ 公式无层/头下标，与"按层与头独立实例化"散文断层 | ✅ 改 v3 的"按层与头独立实例化"为"对每个 $(\ell, h)$ 独立求解"，与 $q^{(\ell,h)}$ 记号对齐 |
| D4 minor 1 | 第 529 行括号 ref 与第 537 行重复 | ✅ 删第 529 行 `（参见第~\ref{sec:ch2-kv-memory}~节）`（约定已在正文自包含） |
| D4 minor 3 | 第 561 行"据此"→"因此" | ✅ 改用"因此"（codex prefs §具体偏好第 65 行推荐） |
| D1 minor / D6 可选 | $Q_{\theta_K}$ 三种作用域列举越界 | 不动（presentation minor，不阻塞 PASS，且 §3.3 才正式定义） |
| D6 可选 | 首段加结论预告"...刻画两条传播路径的耦合结构" | ✅ 采纳（不是 PPT 路线图而是结论预告，符合 codex prefs） |

---

## §3.1 候选稿 v4（综合 Round 4 D5 必改 + minor 优化）

```latex
\section{注意力近似误差的代数分解与问题形式化}
\label{sec:ch3-problem}

下游任务感知到的是注意力分布 $a$ 与注意力输出 $o$，而非 $K, V$ 的逐元素重建距离。因此本文以 $(a,o)$ 这对联合对象作为量化保持的目标，并在单头 MHA 设定下推导其代数分解，刻画两条传播路径的耦合结构。

约定 $q$ 视作行向量 $q\in\mathbb{R}^{1\times d_k}$，历史上下文长度为 $S$，$K\in\mathbb{R}^{S\times d_k}$、$V\in\mathbb{R}^{S\times d_v}$ 由其行向量 $k_i, v_i$ 拼接而成；本文实验涵盖的 Qwen2.5/LLaMA-3 系列均满足 $d_v=d_k$ 约定，由此 $q$ 与 $o$ 同维。标准单头注意力可写为
\begin{equation}
a=\mathrm{softmax}\!\left(\frac{qK^\top}{\sqrt{d_k}}\right), \qquad o=aV,
\end{equation}
其中 $a\in\mathbb{R}^{1\times S}$ 表示注意力分布（按分量索引为 $a_i\in\mathbb{R}$），$o\in\mathbb{R}^{1\times d_v}$ 表示注意力输出。注意力行为记作联合对象
\begin{equation}
\mathcal{B}(q,K,V):=(a,o).
\end{equation}
多层、多头情形按层索引 $\ell$ 与头索引 $h$ 平行展开，记为 $q^{(\ell,h)}, K^{(\ell,h)}$ 等；本节代数分析对每个 KV 头独立成立，GQA/MQA 下查询头到 KV 头的映射已在第~\ref{sec:ch2-kv-memory}~节给出。

设 $Q_{\theta_K}(\cdot)$ 与 $Q_{\theta_V}(\cdot)$ 分别表示作用于 Key 与 Value 的量化映射；参数 $\theta_K, \theta_V$ 的具体含义（scale、zero-point、bit-width 等）以及作用域（逐元素、逐通道或逐 token）由量化路径决定，详见第~\ref{sec:ch3-paths}~节。量化后的 Key 与 Value 记为
\begin{equation}
\hat K = Q_{\theta_K}(K), \qquad \hat V = Q_{\theta_V}(V),
\end{equation}
对应的量化后注意力分布与输出为
\begin{equation}
\hat a=\mathrm{softmax}\!\left(\frac{q\hat K^\top}{\sqrt{d_k}}\right), \qquad \hat o=\hat a \hat V.
\end{equation}
KV Cache 量化的目标即
\begin{equation}
\min_{\theta_K,\theta_V}\Delta_{\mathrm{beh}}\big((a,o),(\hat a,\hat o)\big),
\end{equation}
其中 $\Delta_{\mathrm{beh}}: (\mathbb{R}^{1\times S}\times\mathbb{R}^{1\times d_v})^2 \to \mathbb{R}_{\ge 0}$ 满足 $\Delta_{\mathrm{beh}}(x,x)=0$，刻画量化前后注意力行为的联合偏移；其作为损失函数使用，无需满足度量空间的对称性或三角不等式。$\Delta_{\mathrm{beh}}$ 的具体实例化由量化路径决定（第~\ref{sec:ch3-calibration}~节），并对每个 $(\ell, h)$ 独立求解。

由 $\hat o=\hat a\hat V$ 与 $o=aV$ 的定义，输出误差可作如下精确代数展开：
\begin{align}
\hat o-o
&=\sum_{i=1}^{S}\hat a_i\hat v_i-\sum_{i=1}^{S}a_i v_i \\
&=\sum_{i=1}^{S}(\hat a_i\hat v_i-\hat a_i v_i)+\sum_{i=1}^{S}(\hat a_i v_i-a_i v_i) \\
&=\sum_{i=1}^{S}\hat a_i(\hat v_i-v_i)+\sum_{i=1}^{S}(\hat a_i-a_i)v_i.
\label{eq:ch3-error-decomp}
\end{align}
式~\eqref{eq:ch3-error-decomp} 是恒等变形。右侧第一项（聚合侧/Value 通路）描述 Value 侧内容被量化后如何进入聚合结果；右侧第二项（分布侧/Key 通路）描述 Key 侧扰动经 logits 与 softmax 改变注意力分布后如何传到输出。两条通路同时进入输出，单独追踪 $a$ 或 $o$ 均会遗漏一侧。第一项的权重为量化后分布 $\hat a_i$ 而非参考分布 $a_i$，因此聚合侧误差与 Key 侧扰动并非加性可分——Key 量化通过 $\hat a$ 同时改变第二项的分布偏移与第一项的聚合权重。张量重建误差并不刻画这种交叉依赖；离线校准因此选择以注意力分布上的 KL 散度作为 $\Delta_{\mathrm{beh}}$ 的可执行代理（第~\ref{sec:ch3-calibration}~节），KL 直接惩罚第二项的分布偏移，并经 $\hat a$ 在第一项中的权重作用间接约束聚合侧。

% 图题：图 3-1 注意力误差的两条耦合传播路径及其精确代数分解
\input{figures/fig1_error_decomposition}
```

### 修改对照表（v3 → v4）

| # | 位置 | v3 | v4 | 来源 |
|---|---|---|---|---|
| 1 | 首段末 | "...单头 MHA 设定下推导其代数分解。" | "...单头 MHA 设定下推导其代数分解**，刻画两条传播路径的耦合结构**。" | D6 可选 + D5 P2 一并 |
| 2 | 第二段尾 | "...由此 $q$ 与 $o$ 同维（参见第~\ref{sec:ch2-kv-memory}~节）。" | "...由此 $q$ 与 $o$ 同维。" | D4 minor 1（与第三段 §2.2 ref 重复） |
| 3 | 多头声明段 | "...对每个 KV 头独立成立，GQA/MQA 下查询头到 KV 头的映射已在第~\ref{sec:ch2-kv-memory}~节给出，**多个查询头共享同一组 KV 量化误差**。" | "...对每个 KV 头独立成立，GQA/MQA 下查询头到 KV 头的映射已在第~\ref{sec:ch2-kv-memory}~节给出。" | D5 P1 #2（删悬挂半句） |
| 4 | $\Delta_{\mathrm{beh}}$ 段尾 | "...多头情形下 $(\theta_K, \theta_V)$ **按层与头独立实例化**。" | "...**并对每个 $(\ell, h)$ 独立求解**。" | D2 minor 2（与 $q^{(\ell,h)}$ 记号对齐） |
| 5 | 末段中部 | "...第二项（分布侧/Key 通路）描述 Key 侧扰动经 logits 与 softmax 改变注意力分布后如何传到输出。第一项的权重为..." | "...第二项（分布侧/Key 通路）描述 Key 侧扰动经 logits 与 softmax 改变注意力分布后如何传到输出。**两条通路同时进入输出，单独追踪 $a$ 或 $o$ 均会遗漏一侧。**第一项的权重为..." | D5 P2（$(a,o)$ 联合论证） |
| 6 | 末段末 | "...离线校准**据此采用**注意力分布上的 KL 散度作为 $\Delta_{\mathrm{beh}}$ 的可执行代理（第~\ref{sec:ch3-calibration}~节）。" | "...离线校准**因此选择以**注意力分布上的 KL 散度作为 $\Delta_{\mathrm{beh}}$ 的可执行代理（第~\ref{sec:ch3-calibration}~节）**，KL 直接惩罚第二项的分布偏移，并经 $\hat a$ 在第一项中的权重作用间接约束聚合侧**。" | D4 minor 3 + D5 P1 #1（KL 代理论证桥） |

### Round 4 NOT PASS issue 处理验证表

| Issue | 来源 | v4 处理 |
|---|---|---|
| P1 #1: KL 代理 gap | D5 round 4 | ✅ 末段补"KL 直接惩罚第二项...经 $\hat a$ 间接约束聚合侧" |
| P1 #2: GQA 共享悬挂 | D5 round 4 | ✅ 删"多个查询头共享同一组 KV 量化误差" |
| P2: $(a,o)$ 缺正面论证 | D5 round 4 | ✅ 末段补"两条通路同时进入输出，单独追踪 $a$ 或 $o$ 均会遗漏一侧" |
| D2 minor 2: $\min$ 公式断层 | D2 round 4 | ✅ 改"按层与头独立"为"对每个 $(\ell, h)$ 独立求解" |
| D4 minor 1: 括号 ref 重复 | D4 round 4 | ✅ 删第 529 行 `（参见 §2.2）` |
| D4 minor 3: "据此"→"因此" | D4 round 4 | ✅ 已改 |
| P2: 无对称/三角 spec gap | D5 round 4 | ❌ 不动（D2/D4/D6 三人共识保留） |
| D2 minor 1: $d_v=d_k$ 因果语气 | D2 round 4 | ❌ 不动（核心逻辑不依赖此约定，但表述合理） |
| D1 minor / D6 可选: $Q_{\theta_K}$ 列举 | D1/D6 round 4 | ❌ 不动（presentation minor） |

### codex prefs 12 项 (A-L) 再核查（v4）

A 推导研究设计 ✅；B 正向克制 ✅；C 防御式负向 ✅（"无需满足"+"并不刻画"两处技术 spec 必要负向）；D 具体机制 ✅（v4 新增"KL 直接惩罚第二项...间接约束聚合侧"是技术机制具体化）；E 元叙述 ✅；F 段落节奏 ✅；G 教科书过渡词 ✅（"因此选择"是 codex prefs §具体偏好第 65 行明确推荐）；H 冒号式展开 ✅；I 位置化"上"表达 ✅；J 英文式倒装 ✅；K 章节过渡 ✅；L 衔接研究过程式 ✅。

### Round 5 结果（候选稿 v4）— 全部 PASS ✅

| Agent | v0 | v1 | v2 | v3 | v4 | Verdict |
|---|---|---|---|---|---|---|
| D1 顶会 | 7.5 | 8.5 | 8.5 | 9.0 | **9.2** | ✅ |
| D2 数学 | 6.5 | 9.0 | 8.2 | 9.2 | **9.4** | ✅ |
| D3 复现 | 6.5 | 9.0 | 8.5 | 9.2 | **9.5** | ✅ |
| D4 中文 | 6.0 | 7.0 | 8.8 | 8.6 | **8.7** | ✅ |
| **D5 Skeptical** | 6.0 | 8.0 | 6.5 | 7.5 | **8.5** | ✅ **撤回 NOT PASS** |
| D6 博士生 | 7.5 | 8.5 | 7.8 | 8.6 | **8.8** | ✅ |

**v4 加权平均 9.02**（v3: 8.68 → v4: 9.02，+0.34）。

### D5 关键判定（"何时停止"）

D5 round 5 明确判：「v4 达到 PhD 论文方法章首节的合理标准...**停止建议：此稿提交。** 继续迭代的边际收益（精化"间接约束"的措辞）低于边际风险（改动末段引入新的连贯性问题）。剩余可疑点均属于答辩响应层面，不是论文修改层面。」

D5 4 处必改处理：
- P1 #1 (KL 代理 gap): ⚠️ 部分解决但**答辩可承担类**——KL 约束 $\hat a_i$ 权重，V 侧幅度由 $\theta_V$ 联合最小化承担，在方法章首节颗粒度下合理
- P1 #2 (GQA 共享悬挂): ✅ 完全解决（删半句）
- P2 (无对称/三角): **D5 撤回反对**（D2/D4/D6 三人共识正确）
- P2 ($(a,o)$ 联合论证): ✅ 解决（"两条通路同时进入输出..."补足正面论证）

### Round 5 各 reviewer 提的可选优化（不阻塞，归档供后续打磨）

| 来源 | 优化建议 | 决策 |
|---|---|---|
| D1 | "间接约束聚合侧"两跳因果链可加破折号短注 | 归档（minor presentation） |
| D1 | $Q_{\theta_K}$ 作用域列举越界（连续 5 轮提到） | 归档（presentation minor，§3.3 才正式定义） |
| D2 | "单独追踪 $a$ 或 $o$"措辞精度（追踪 $o$ 不存在"遗漏一侧"） | 归档（不影响理解） |
| D2 | "间接约束聚合侧"应限定为"权重分布 $\hat a_i$" | 归档（D5 已判答辩可承担） |
| D2 | $d_v=d_k$ 因果语气"由此"→"即"（学术规范微调） | 归档 |
| D4 | 末段密度 v3 5 句→v4 6-7 句潜在 P3 | 归档（D6 同 warning，但都判 PASS） |
| D6 | 末段最后一句可改为更轻量 forward hook（"§3.4 将以此为依据..."） | **拒绝**（这等于撤回 D5 P1 #1 要求的论证桥；D2 派精化方向更优） |

### ✅ §3.1 落地（v4 → thesis/chapters/ch3_method.tex line 3-46）

**Edit 完成时间**：2026-05-08
**xelatex 编译验证**：pass 1 + pass 2 通过，96 页，零 LaTeX Error，零 undefined references
**.tex 行数变化**：+7 -11（净减 4 行：删 v0 章末过渡 + 合并 v0 图后段到末段）
**git diff --check**：✅ OK
**Underfull 警告**：line 140 / line 756（与 §3.1 无关，是已有问题）

---

## §3.1 6-Agent 5-Round 审查总结

**结论**：§3.1 经过 5 轮迭代（v0→v4）+ 30 个 agent 报告（6 reviewer × 5 rounds）后达到 PhD 论文方法章首节的合理标准。

**关键演化**：
- v0 → v1: 修复 D4 round 1 的 6 处中文写作残留（"于是""至此""系恒等"等）
- v1 → v2: 删除 v1 残留的"基于此""至此"等 codex prefs 违规
- v2 → v3: 修复 D5 round 3 的 4 处实质问题（耦合失真未定义、KL 桥接、$d_v=d_k$ 作用、GQA 适用性）+ D2 Gap 1+2
- v3 → v4: 修复 D5 round 4 的 KL 代理 gap + 删 GQA 共享悬挂 + 补 $(a,o)$ 正面论证 + D4/D2 minor

**6-agent multi-perspective 审查的实战收益**：
1. D5 持续升级问题暴露 v0/v1 hedge 掩盖的真 spec gap（"概念层成立"删后 $\Delta_{\mathrm{beh}}$ 弱定义显形）
2. D4 锁定 codex prefs ground truth 实现写作风格收敛（v2 后 ±0.2 区间）
3. D2 数学 + D5 怀疑的级联效应：D2 标的 minor 在 D5 视角升级为 critical
4. D6 主动判"何时停止"：v4 round 5 D6 + D5 双双判 v4 已达答辩可提交标准

---


## §3.3 行为引导量化框架总览 — 审改循环

**目标行**: ch3_method.tex line 60-90 (v0)

### Round 1 综合（v0 审）

加权综合: **6.23 / 10** — 🔴 不通过，需 v1

| Agent | 分数 | Verdict | 关键问题 |
|-------|------|---------|---------|
| D1 顶会 | 6.5 | 🟡 | 双 label / 章末路线图过密 / claim 边界提前暴露 §3.6/§3.7 |
| D2 数学 | 5.2 | 🟡 | $s^{(l)}$ 类型未声明 / $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 与 §3.1 桥接缺 / $\mathcal{A}$ 守恒约束缺 / producer 责任不明 |
| D3 复现 | 7.2 | 🟡 | $\mathcal{S}$ 存储格式 / 双 label / AutoK routing 悬挂 |
| D4 中文 | 5.8 | 🔴 | line 72/78/84 PPT 式分层（§28）/ line 66 元叙述（§19）/ line 90 章末路线图 / line 64 教科书回指 |
| D5 Skeptical | 5.8 | 🟡 | 单调性 axiom 化（应降级归纳假设）/ line 70 与 line 97 矛盾 / $\mathcal{A}$ 函数族未说明 |
| D6 博士生 | 7.8 | 🟡 | $\Delta^{\mathrm{cal}}$ 上标未解释 / AutoK 无铺垫 / $s^{(l)}$ 类型不清 |

### Round 1 必改清单（按一致性排序）

**P0 — 多 agent 一致 (必改):**
- **P0-1 删除章末路线图 line 90** (D1, D4, D5, D6 一致) — 与 §3.1 v4 / §3.2 v3 风格冲突
- **P0-2 删除 PPT 式 "在框架的第一层/第二层" line 72/78/84** (D1, D4, D5) — codex prefs §28
- **P0-3 删除 \label{sec:ch3-overview} line 62** (D1, D3) — multiply defined warning，且无外部 \ref 引用

**P1 — 写作风格 (必改):**
- **P1-1 line 64 "前两节给出两个约束"** (D1, D4, D6) — 教科书回指改为直接进入设计推导
- **P1-2 line 66 "本文将...记为"** (D1, D4) — 元叙述包装去掉，直接定义符号
- **P1-3 line 82 "最基础的输出是逐层预算；进一步的输出可以包含"** (D4) — 模板列举改为机制推导
- **P1-4 line 84 "执行时只有两个阶段"** (D4) — PPT 式分阶段，先写动机再导出分工
- **P1-5 删除 line 86-87 % 注释行** (D1) — figure file 已有 \caption，注释冗余

**P1 — 数学严谨 (必改):**
- **P1-6 $s^{(l)} \in \mathbb{R}_{\geq 0}$ 类型声明** (D2, D6) — 在 eq.(1) 旁
- **P1-7 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 与 §3.1 $\Delta_{\mathrm{beh}}$ 显式桥接** (D1, D2, D6) — "在校准样本上的有限样本估计"
- **P1-8 $\mathcal{A}$ 函数族说明** (D2, D5, D6) — "确定性、规则型映射"
- **P1-9 $\mathcal{A}$ 预算守恒约束** (D2) — $\frac{1}{L}\sum b^\star_l \le \bar b$
- **P1-10 $\mathcal{S}$ producer 责任** (D2, D5) — "由校准层在处理校准样本时作为副产物输出"
- **P1-11 line 70 单调性 hedge 降级为归纳假设 + forward ref** (D5) — 不写为接口语义，改为"本文归纳采用 + §4 验证"
- **P1-12 删除 line 70 "二者共享离线来源和行为读法"** (D5) — 与 line 97 路径相关代理矛盾
- **P1-13 AutoK 推迟到 §3.6 引入** (D5, D6) — 当前段无铺垫

**P2 — 可选 (单 agent):**
- $\Theta$ "离散候选集" 性质说明 (D2)
- $b^\star$ 维度二义性显式化 (D2)

### v1 候选稿（应用 P0/P1 修订）

```latex
\section{行为引导量化框架总览}
\label{sec:ch3-framework}

§3.1 把量化质量评判从张量重建误差移至注意力行为差异 $\Delta_{\mathrm{beh}}$，§3.2 把低比特退化定位为 Key 侧主导。本节据此组织框架接口：离线校准模块按候选量化路径搜索行为代理最优的参数；预算分配模块在同一离线链路上读取逐层敏感度统计量，输出每层（或每个角色）保留多少 bit。

逐层行为敏感度画像
\begin{equation}
\mathcal{S}=\{s^{(l)}\}_{l=1}^{L},\quad s^{(l)}\in\mathbb{R}_{\geq 0},
\end{equation}
是离线校准链路在处理校准样本时作为副产物输出的逐层标量统计量；分配模块以只读方式读取它，不发起新的校准搜索。$\mathcal{S}$ 不预设唯一计算公式，由路径相关代理实例化（第~\ref{sec:ch3-calibration}~节）。本文取 $s^{(l)}$ 越大表示第 $l$ 层在量化扰动下注意力行为越不稳定，并归纳地采用单调假设——读数越高的层在预算受限时保留更高位宽的边际收益越大；该假设的实验支撑见第~\ref{sec:exp-allocator}~节。

校准层把"如何量化"组织为参数选择问题。设候选量化参数空间 $\Theta$ 是离散候选集合（如 per-layer scale 候选格点），校准层求解
\begin{equation}
\theta^\star = \arg\min_{\theta\in\Theta}\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta),
\end{equation}
其中 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta)$ 是 §3.1 的 $\Delta_{\mathrm{beh}}$ 在有限校准样本上的代理估计——把 §3.1 联合行为目标限制到离线校准集，转化为可执行计算。给定一条路径及其候选参数家族，校准层输出 $\theta^\star$ 供在线缓存写入直接读取；不同位宽与格式的差异由候选家族 $\Theta$ 与代理 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 的具体形式承担，框架不要求所有路径使用同一数值评分。

分配层把"哪里保留更高精度"组织为预算决策问题。设平均 KV bit 预算为 $\bar b$，分配映射
\begin{equation}
b^\star = \mathcal{A}(\mathcal{S};\bar b),\quad \tfrac{1}{L}\sum_{l=1}^{L} b^\star_l \le \bar b,
\end{equation}
为确定性、规则型映射（不发起在线优化也不重复参数搜索），将共享画像 $\mathcal{S}$ 转换为整数位宽向量 $b^\star$。最简形式下 $b^\star\in\{b_{\min},\dots,b_{\max}\}^L$ 是逐层预算；扩展到 K/V 角色条件化时 $b^\star\in\{b_{\min},\dots,b_{\max}\}^{L\times 2}$，对应 $\mathcal{S}$ 同步扩展为按角色分量。具体规则（含逐层、逐角色与上限自动建议）见第~\ref{sec:ch3-allocator}~节。

这一组织把整条链路切分为可独立验证的两段：离线阶段提取参考行为、搜索路径参数、写出校准产物，同步生成 $\mathcal{S}$；在线阶段只读取冻结产物，按已固定规则计算当前缓存写入所需的尺度或预算。设计的核心约束是推理路径上不重复离线搜索，因此 $\theta^\star$ 与 $b^\star$ 都被视为框架的离线交付物，而非在线决策变量。

\input{figures/fig_ch3_framework_shared_profile}
```

### v0 → v1 修订映射

| 原 line | 问题 | v1 处理 |
|---------|------|---------|
| 62 | 双 label | 删除 \label{sec:ch3-overview} |
| 64 | 教科书回指 + "本节把这两个约束转成接口" 元叙述 | 直接引用 §3.1 / §3.2 结论作为本节起点 |
| 66 | "本文将...记为" 元叙述 | "逐层行为敏感度画像 $\mathcal{S}=...$ 是..." 直接定义 |
| 68 | $s^{(l)}$ 类型未给 | $s^{(l)}\in\mathbb{R}_{\geq 0}$ 写在 eq |
| 70 | 单调性 axiom 化 + 共享行为读法矛盾 | 降级为"本文归纳采用 + §4 验证"; 删除"共享离线来源和行为读法" |
| 70 | $\mathcal{S}$ producer 不明 | "由离线校准链路作为副产物输出" |
| 72/78 | "在框架的第一层/第二层" PPT 式 | "校准层把...组织为...问题" / "分配层把...组织为...问题" 去 PPT 标签 |
| 74 | $\Delta^{\mathrm{cal}}$ 与 §3.1 桥接缺 | "是 §3.1 $\Delta_{\mathrm{beh}}$ 在有限校准样本上的代理估计" |
| 80 | $\mathcal{A}$ 函数族 + 守恒约束缺 | eq.(3) 加 $\frac{1}{L}\sum b^\star_l \le \bar b$ + "确定性、规则型映射" |
| 82 | 模板列举 + AutoK 无铺垫 | "最简形式下...扩展到...时..." 机制推导; AutoK 推后到 §3.6 |
| 84 | "执行时只有两个阶段" PPT 式 | "这一组织把...切分为...两段" 先动机后分工 |
| 86-87 | % 注释冗余 | 删除两行 |
| 90 | 章末路线图 | 整段删除（与 §3.1 v4 / §3.2 v3 一致） |


### Round 2 综合（v1 审）

加权综合: **8.22 / 10** — ✅ PASS（阈值 8.0）

| Agent | 分数 | Verdict | 关键残留 |
|-------|------|---------|---------|
| D1 顶会 | 8.3 | ✅ | P1-A: "上限自动建议" 残留 AutoK 概念 / P1-B: "本节据此组织" meta 自述 |
| D2 数学 | 8.1 | ✅ | 全部 P1 形式 gap 修复，P2 残留 ($\Theta$ 基数 / cal 上标定义) 可接受 |
| D3 复现 | 8.3 | ✅ | M1 残留: $\mathcal{S}$ 序列化格式 / M2: $b_{\min}/b_{\max}$ candidate set |
| D4 中文 | 8.4 | ✅ | 7/7 v0 issues 全解决；§F 两处括号克制 |
| D5 Skeptical | 7.8 | 🟡 | **P1 必改: `\ref{sec:exp-allocator}` 悬空 label**（实际不存在）|
| D6 博士生 | 8.4 | ✅ | "路径相关代理" 锚定不足 / $L\times 2$ 缺 §3.2 桥接 |

### Round 2 整合修订（v1 → v2，落地版）

D5 唯一 P1 必改是事实性 label 错误，其他都是 minor 优化建议。整合为 v2 直接落地（不再 spawn Round 3）：

1. **D5 P1 必改**: `\ref{sec:exp-allocator}` → `\ref{sec:exp-cross-model}` (实际存在 label，line 392)
2. **D1 P1-A**: 删除 "（含逐层、逐角色与上限自动建议）" → "具体规则见..."（不带 AutoK 提示）
3. **D1 P1-B**: "本节据此组织框架接口" → "框架以两个离线模块落实上述约束"
4. **D4 §F**: "（如 per-layer scale 候选格点）" → "为离散候选集合，如 per-layer scale 候选格点"（破括号融入正文）
5. **D6 P1**: "路径相关代理" → "具体量化路径对应的行为代理"
6. **D6 P2**: $L\times 2$ 加 "对应 §3.2 识别的 Key/Value 双角色"
7. **D3 M2**: 加 "（本文取 $b\in\{4,8,16\}$）" candidate set 明示
8. **首段 minor**: "（或每个角色）" → "（或 Key/Value 角色）" 术语精确

D3 M1（$\mathcal{S}$ 序列化）不采纳：序列化属于 §3.7.1 实现节内容，框架总览不应破抽象层。

### v2 落地稿

```latex
\section{行为引导量化框架总览}
\label{sec:ch3-framework}

§3.1 把量化质量评判从张量重建误差移至注意力行为差异 $\Delta_{\mathrm{beh}}$，§3.2 把低比特退化定位为 Key 侧主导。框架以两个离线模块落实上述约束：校准模块按候选量化路径搜索行为代理最优的参数；预算分配模块在同一离线链路上读取逐层敏感度统计量，输出每层（或 Key/Value 角色）保留多少 bit。

逐层行为敏感度画像
\begin{equation}
\mathcal{S}=\{s^{(l)}\}_{l=1}^{L},\quad s^{(l)}\in\mathbb{R}_{\geq 0},
\end{equation}
是离线校准链路在处理校准样本时作为副产物输出的逐层标量统计量；分配模块以只读方式读取它，不发起新的校准搜索。$\mathcal{S}$ 不预设唯一计算公式，由具体量化路径对应的行为代理实例化（第~\ref{sec:ch3-calibration}~节详述）。本文取 $s^{(l)}$ 越大表示第 $l$ 层在量化扰动下注意力行为越不稳定，并归纳地采用单调假设——读数越高的层在预算受限时保留更高位宽的边际收益越大；该假设的实验支撑见第~\ref{sec:exp-cross-model}~节。

校准层把"如何量化"组织为参数选择问题。设候选量化参数空间 $\Theta$ 为离散候选集合，如 per-layer scale 候选格点，校准层求解
\begin{equation}
\theta^\star = \arg\min_{\theta\in\Theta}\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta),
\end{equation}
其中 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta)$ 是 §3.1 的 $\Delta_{\mathrm{beh}}$ 在有限校准样本上的代理估计——把 §3.1 联合行为目标限制到离线校准集，转化为可执行计算。给定一条路径及其候选参数家族，校准层输出 $\theta^\star$ 供在线缓存写入直接读取；不同位宽与格式的差异由候选家族 $\Theta$ 与代理 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 的具体形式承担，框架不要求所有路径使用同一数值评分。

分配层把"哪里保留更高精度"组织为预算决策问题。设平均 KV bit 预算为 $\bar b$，分配映射
\begin{equation}
b^\star = \mathcal{A}(\mathcal{S};\bar b),\quad \tfrac{1}{L}\sum_{l=1}^{L} b^\star_l \le \bar b,
\end{equation}
为确定性、规则型映射，将共享画像 $\mathcal{S}$ 转换为整数位宽向量 $b^\star$，不发起在线优化也不重复参数搜索。最简形式下 $b^\star\in\{b_{\min},\dots,b_{\max}\}^L$ 是逐层预算（本文取 $b\in\{4,8,16\}$）；扩展到 K/V 角色条件化时 $b^\star\in\{b_{\min},\dots,b_{\max}\}^{L\times 2}$，对应 §3.2 识别的 Key/Value 双角色，$\mathcal{S}$ 同步扩展为按角色分量。具体规则见第~\ref{sec:ch3-allocator}~节。

这一组织把整条链路切分为可独立验证的两段。离线阶段提取参考行为、搜索路径参数、写出校准产物，同步生成 $\mathcal{S}$；在线阶段只读取冻结产物，按已固定规则计算当前缓存写入所需的尺度或预算。设计的核心约束是推理路径上不重复离线搜索，因此 $\theta^\star$ 与 $b^\star$ 都被视为框架的离线交付物，而非在线决策变量。

\input{figures/fig_ch3_framework_shared_profile}
```



## §3.4.1 注意力分布 KL 散度目标 — 审改循环

**目标行**: ch3_method.tex line 90-137 (含 §3.4 父节开头段 + §3.4.1 主体, v0)

### Round 1 综合（v0 审）

加权综合: **6.23 / 10** — 🔴 不通过

| Agent | 分数 | Verdict | 关键问题 |
|-------|------|---------|---------|
| D1 顶会 | 6.2 | 🔴 | P0: 聚合公式缺失 / P0: $\Delta^{cal}$ 桥接 / P1: 反问句式 / P1: §4 边界暴露 |
| D2 数学 | 6.2 | 🟡 | P1: $D_{KL}$ 输入域 / P1: 聚合公式 / P1: ε 操作精化 / P2: $q,K$ 维度 |
| D3 复现 | 5.5 | 🟡 | P1: ε=1e-6 clamp / P1: q-RoPE/layernorm 标注 / P2: Value proxy forward ref |
| D4 中文 | 5.8 | 🟡 | 8 处违规: 3 元叙述 (§19) + 3 防御负向 (§17) + 2 反问 (§28) |
| D5 Skeptical | 7.2 | 🟡 | MED: line 133 KL claim / MED: $\Delta^{cal}$ 绑定 / MED: mass-covering 写成事实 |
| D6 博士生 | 6.8 | 🟡 | M1: 聚合缺 / M2: 反问 / M3: 防御 / M4: $v$ 未定义 / M5: ε 位置 |

### Round 1 必改清单（一致排序）

**P0 — 多 agent 一致 (必改):**
- **P0-1 聚合公式 $\Delta^{cal}(\theta) = \frac{1}{|T|}\sum d_{KL}^{(l,h,t)}$ 显式定义** (D1, D2, D6 一致)
- **P0-2 与 §3.3 $\Delta^{cal}$ 桥接显式声明** (D1, D2, D5, D6 一致)
- **P0-3 反问句式 line 125/135 改正向陈述** (D1, D4, D6)
- **P0-4 防御负向 + 元叙述清理 line 90-92, 123, 137** (D1, D4, D6)

**P1 — 必改:**
- **P1-5 ε 实现细节精化** (D2, D3, D4): "$\varepsilon=10^{-6}$ 的 clamp"
- **P1-6 q/K 经 input_layernorm + RoPE 标注** (D3): CAL-019/020 教训
- **P1-7 $D_{KL}$ 输入域 + $q,K$ 维度** (D2): $p\in\Delta^{N-1}$, $q\in\mathbb{R}^{d_k}$, $K\in\mathbb{R}^{N\times d_k}$
- **P1-8 Value proxy forward ref to §3.5** (D3, D5): \ref{sec:ch3-paths}
- **P1-9 $\hat a_i \leftrightarrow p_\theta$ 符号绑定** (D2, D6): 在 MSE 段加 $a_i\equiv p_{\mathrm{ref},i}$

**P2:**
- "属于第四章" 改 forward ref (D1)
- $v_i, \hat v_i$ 定义引用 (D6)
- mass-covering line 135 hedge (D5)

### v1 候选稿（应用 P0/P1 修订）

```latex
\section{行为引导校准目标与参数搜索策略}
\label{sec:ch3-calibration}

第~\ref{sec:ch3-problem}~节把量化质量评判落到联合行为偏移 $\Delta_{\mathrm{beh}}$，但该量在样本上无显式可执行形式。本节把第~\ref{sec:ch3-framework}~节引入的代理 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 展开为校准层可计算的具体形式：用注意力分布侧 KL 给出 Key-sensitive 路径的离线读数，并在路径相关的候选参数家族上完成稳健选择。

对称路径与角色感知低比特路径在候选参数家族与代理形式上不必相同，但都在离线样本上计算行为读数，在可行域约束下控制尾部坏案例，并把最终选择写入固定校准产物。

\subsection{注意力分布 KL 散度目标}

设第 $l$ 层、第 $h$ 个注意力头、时间步 $t$ 的 Query 与 Key 分别为 $q^{(l,h,t)}\in\mathbb{R}^{d_k}$ 与 $K^{(l,h,t)}\in\mathbb{R}^{N\times d_k}$，二者均在 \texttt{input\_layernorm} 与 RoPE 处理后取出，$N$ 为当前位置可见的上下文长度。FP16 参考路径下的注意力分布
\begin{equation}
p_{\mathrm{ref}}^{(l,h,t)}
=
\operatorname{softmax}\!\left(
\frac{q^{(l,h,t)} K^{(l,h,t)\top}}{\sqrt{d_k}}
\right)\in\Delta^{N-1}.
\end{equation}
对候选量化参数 $\theta$，记量化—反量化后的 Key 为 $\tilde K_{\theta}^{(l,h,t)}$，对应分布
\begin{equation}
p_{\theta}^{(l,h,t)}
=
\operatorname{softmax}\!\left(
\frac{q^{(l,h,t)} \tilde K_{\theta}^{(l,h,t)\top}}{\sqrt{d_k}}
\right).
\end{equation}
单位置分布偏移取前向 KL
\begin{equation}
d_{\mathrm{KL}}^{(l,h,t)}(\theta)
=
D_{\mathrm{KL}}\!\left(
p_{\mathrm{ref}}^{(l,h,t)}
\;\middle\|\;
p_{\theta}^{(l,h,t)}
\right),
\end{equation}
将第~\ref{sec:ch3-framework}~节引入的 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta)$ 实例化为校准样本集合 $T$ 上的均值
\begin{equation}
\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta)
=
\frac{1}{|T|}\sum_{(l,h,t)\in T} d_{\mathrm{KL}}^{(l,h,t)}(\theta),
\end{equation}
作为离线参数搜索的优化目标，$|T|$ 是 $(l,h,t)$ 三元组数量。

MSE 工作在张量重建空间，仅比较 $K$ 或 $V$ 的逐元素差异；而 Key 误差影响输出之前要先经 $qK^\top$、softmax 排序与概率质量分配，一个 MSE 较小的候选仍可能把关键 token 的注意力质量移走。式~\eqref{eq:ch3-error-decomp} 把误差分解为分布侧 $\sum_i(\hat a_i-a_i)v_i$ 与聚合侧 $\sum_i \hat a_i(\hat v_i-v_i)$ 两条路径，其中 $a_i\equiv p_{\mathrm{ref},i}^{(l,h,t)}$、$\hat a_i\equiv p_{\theta,i}^{(l,h,t)}$，$v_i$ 与 $\hat v_i$ 分别为参考与量化 Value。KL 直接约束 $(\hat a-a)$ 并经 $\hat a_i$ 在聚合侧传递，因此在 Key-sensitive 校准中比逐元素重建误差更贴近输出层面的注意力行为。

前向 KL $D_{\mathrm{KL}}(p_{\mathrm{ref}}\|p_\theta)$ 对参考高概率位置在量化路径下被低估的情况惩罚更强，匹配长上下文检索“不漏关键 token”的需求；反向 KL 偏向量化分布自身的高概率区域，JS 散度更对称，二者作为补充诊断保留。Value 路径使用独立的输出扰动代理，详见第~\ref{sec:ch3-paths}~节。

数值上对概率以小常数 $\varepsilon=10^{-6}$ 做 clamp 截断以避免极端尾部概率引起的不稳定，截断对 KL 取值的影响在校准产物的实际取值上可忽略；KL 在不同模型规模与 bit-width 下的收益强弱见第四章实验。
```


### Round 2 综合（v1 审）

加权综合: **8.41 / 10** — ✅ PASS (阈值 8.0)

| Agent | 分数 | Verdict | 关键残留 |
|-------|------|---------|---------|
| D1 顶会 | 8.3 | ✅ | P0: $\tilde K_\theta$ 语义 / P1: "可忽略" claim 无依据 |
| D2 数学 | 9.0 | ✅ | P3: $p_\theta\in\Delta^{N-1}$ 对称标注（v0 4 P1 全修复）|
| D3 复现 | 8.5 | ✅ | P1: ε clamp 作用对象不清（应同时对 ref/θ）|
| D4 中文 | 8.2 | ✅ | M1: line 1226 "本节把...展开为" 元叙述 (§19) / M2: 末句叠加 |
| D5 Skeptical | 7.8 | 🟡 | **MED**: 新增"截断可忽略"无背书 / mass-covering "匹配...需求"跳跃 |
| D6 博士生 | 8.6 | ✅ | 必改: $\tilde K_\theta$ 定义 / 裸文字 "第四章" 缺 \ref |

### Round 2 整合修订（v1 → v2，落地版）

整合 D1/D3/D4/D5/D6 一致 P1 必改 (mechanical 整合，不再 spawn Round 3)：

1. **D1 P0 + D6 必改-2**: $\tilde K_\theta$ 显式定义 "$= \mathrm{dequant}(\mathrm{quant}(K;\theta);\theta)$"
2. **D6 必改-1**: "见第四章实验" → "见第~\ref{chap:experiments}~章"（实际 label, line 4）
3. **D4 M1**: line 1226 "本节把...展开为" → 改为直接陈述
4. **D5 MED + D1 P1**: 删除"截断对 KL 取值的影响...可忽略"无背书声明
5. **D3 P1**: ε clamp 作用对象 → "对 $p_{\mathrm{ref}}$ 与 $p_\theta$ 均在 $[\varepsilon, 1]$ 上"
6. **D5 LOW + D1 P2**: "匹配...需求" → "对应...的设计需求"
7. **D2 P3**: $p_\theta$ 加 $\in\Delta^{N-1}$ 对称标注
8. **D5 MED 一致性**: 加 forward ref to §3.4.2 "尾部稳健选择准则延至..."

### v2 落地稿

```latex
\section{行为引导校准目标与参数搜索策略}
\label{sec:ch3-calibration}

第~\ref{sec:ch3-problem}~节把量化质量评判落到联合行为偏移 $\Delta_{\mathrm{beh}}$，但该量在样本上无显式可执行形式。代理 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 在 Key-sensitive 路径下取注意力分布侧 KL 散度作为离线参数搜索的可计算目标，并在路径相关的候选参数家族上完成稳健选择。

对称路径与角色感知低比特路径在候选参数家族与代理形式上不必相同，但都在离线样本上计算行为读数，在可行域约束下控制尾部坏案例，并把最终选择写入固定校准产物。

\subsection{注意力分布 KL 散度目标}

设第 $l$ 层、第 $h$ 个注意力头、时间步 $t$ 的 Query 与 Key 分别为 $q^{(l,h,t)}\in\mathbb{R}^{d_k}$ 与 $K^{(l,h,t)}\in\mathbb{R}^{N\times d_k}$，二者均在 \texttt{input\_layernorm} 与 RoPE 处理后取出，$N$ 为当前位置可见的上下文长度。FP16 参考路径下的注意力分布
\begin{equation}
p_{\mathrm{ref}}^{(l,h,t)}
=
\operatorname{softmax}\!\left(
\frac{q^{(l,h,t)} K^{(l,h,t)\top}}{\sqrt{d_k}}
\right)\in\Delta^{N-1}.
\end{equation}
对候选量化参数 $\theta$，记量化—反量化映射 $\tilde K_{\theta}^{(l,h,t)} = \mathrm{dequant}(\mathrm{quant}(K^{(l,h,t)};\theta);\theta)$，对应分布
\begin{equation}
p_{\theta}^{(l,h,t)}
=
\operatorname{softmax}\!\left(
\frac{q^{(l,h,t)} \tilde K_{\theta}^{(l,h,t)\top}}{\sqrt{d_k}}
\right)\in\Delta^{N-1}.
\end{equation}
单位置分布偏移取前向 KL
\begin{equation}
d_{\mathrm{KL}}^{(l,h,t)}(\theta)
=
D_{\mathrm{KL}}\!\left(
p_{\mathrm{ref}}^{(l,h,t)}
\;\middle\|\;
p_{\theta}^{(l,h,t)}
\right),
\end{equation}
将第~\ref{sec:ch3-framework}~节引入的 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta)$ 实例化为校准样本集合 $T$ 上的均值
\begin{equation}
\Delta_{\mathrm{beh}}^{\mathrm{cal}}(\theta)
=
\frac{1}{|T|}\sum_{(l,h,t)\in T} d_{\mathrm{KL}}^{(l,h,t)}(\theta),
\end{equation}
作为离线参数搜索的优化目标，$|T|$ 是 $(l,h,t)$ 三元组数量。尾部稳健的选择准则与候选参数家族延至第~\ref{subsec:ch3-two-stage}~节给出。

MSE 工作在张量重建空间，仅比较 $K$ 或 $V$ 的逐元素差异；而 Key 误差影响输出之前要先经 $qK^\top$、softmax 排序与概率质量分配，一个 MSE 较小的候选仍可能把关键 token 的注意力质量移走。式~\eqref{eq:ch3-error-decomp} 把误差分解为分布侧 $\sum_i(\hat a_i-a_i)v_i$ 与聚合侧 $\sum_i \hat a_i(\hat v_i-v_i)$ 两条路径，其中 $a_i\equiv p_{\mathrm{ref},i}^{(l,h,t)}$、$\hat a_i\equiv p_{\theta,i}^{(l,h,t)}$，$v_i$ 与 $\hat v_i$ 分别为参考与量化 Value。KL 直接约束 $(\hat a-a)$ 并经 $\hat a_i$ 在聚合侧传递，因此在分布侧误差路径上比逐元素重建误差更贴近输出层面的注意力行为。

前向 KL $D_{\mathrm{KL}}(p_{\mathrm{ref}}\|p_\theta)$ 对参考高概率位置在量化路径下被低估的情况惩罚更强，对应长上下文检索“不漏关键 token”的设计需求；反向 KL 偏向量化分布自身的高概率区域，JS 散度更对称，二者作为补充诊断保留。Value 路径使用独立的输出扰动代理，详见第~\ref{sec:ch3-paths}~节。

数值上对 $p_{\mathrm{ref}}$ 与 $p_\theta$ 均在 $[\varepsilon, 1]$ 上做 clamp 截断（取 $\varepsilon=10^{-6}$）以避免极端尾部概率引起的不稳定。KL 在不同模型规模与 bit-width 下的收益强弱见第~\ref{chap:experiments}~章。
```



## §3.4.2 参数搜索空间与稳健选择准则 — 审改循环

**目标行**: ch3_method.tex line 136-202 (v0)

### Round 1 综合（v0 审）

加权综合: **6.18 / 10** — 🔴 不通过

| Agent | 分数 | Verdict | 关键问题 |
|-------|------|---------|---------|
| D1 顶会 | 6.8 | 🟡 | P0: $R_\mathrm{path}$ 未定义 / clip-rate 未定义 / $\tau$ 阈值缺失 |
| D2 数学 | 5.8 | 🟡 | P1: clip-rate 公式 / V-path R 公式 / K-path 尾部统计公式 |
| D3 复现 | 6.2 | 🟡 | P1 阻断: clip-rate 计算 / $\tau=0.01$ / $\mathcal D_\mathrm{calib}$ forward ref |
| D4 中文 | 5.8 | 🟡 | §19 元叙述 4 处 / §17 防御负向 2 处 / enumerate 双层 |
| D5 Skeptical | 6.2 | 🟡 | **HIGH: clip-rate 循环定义** + **HIGH: §3.4.1 mean vs §3.4.2 P95 关系矛盾** |
| D6 博士生 | 6.4 | 🟡 | P1: clip-rate 缺定义式 / §3.4.1 与 §3.4.2 接口断层 |

### Round 1 必改清单

**P0 — 多 agent 一致 (5 agents):**
- **P0-1 clip-rate 操作公式定义** (D1, D2, D3, D5, D6) — 必须给 $c_K = |\{|x|>q_{\max}^{int}\}|/N$
- **P0-2 §3.4.1 mean vs §3.4.2 P95 关系显式衔接** (D5 HIGH, D6 P1) — "$\mu$ 沿用 §3.4.1 但 P95 为主序"
- **P0-3 元叙述清理** (D1, D4: L139, L145, L202; D6) — 多处 §19/§17

**P1 — 必改:**
- **P1-4 $\tau_K=\tau_V=0.01$ 数值** (D1, D2, D3)
- **P1-5 校准数据集 forward ref to §3.7** (D3) — WikiText-2, 128×512
- **P1-6 $p_K, p_V$ 提前 forward ref to §3.5.3** (D3, D5, D6)
- **P1-7 回退规则末句 + L202 "默认不启用" 防御负向删除** (D4, D5)
- **P1-8 enumerate (i)(ii)(iii) → 内嵌** (D4)
- **P1-9 \noindent\textbf{} → \paragraph{}** (D1)
- **P1-10 $\Theta_\mathrm{path}$ 离散性声明** (D2)
- **P1-11 "对称路径可直接以 KL 组织风险" hedge** (D5)

### v1 候选稿（应用 P0/P1 修订）

```latex
\subsection{参数搜索空间与稳健选择准则}
\label{subsec:ch3-two-stage}

§\ref{subsec:ch3-kl-target}~节给出均值代理 $\Delta_{\mathrm{beh}}^{\mathrm{cal}}$ 后，对一条具体路径还需要确定有限离散候选网格 $\Theta_{\mathrm{path}}$、该路径使用的行为代理 $R_{\mathrm{path}}$，以及写入在线推理系统的产物字段。图~\ref{fig:ch3-calibration-workflow} 给出参考行为提取、候选搜索、稳健选择与产物冻结四步离线流程，表~\ref{tab:ch3-calibration-interfaces} 列出 \texttt{INT8}、对称 \texttt{INT4} 与 \texttt{INT4-RoleAlign} 三条路径在这四步上各自的接口实例化。

\input{figures/fig_ch3_calibration_workflow}

\input{tables/table_ch3_calibration_interfaces}

给定候选网格 $\Theta_\mathrm{path}$ 后，路径参数的离线选择写为
\begin{equation}
\theta_{\mathrm{path}}^\star
=
\arg\min_{\theta \in \Theta_{\mathrm{path}}}
R_{\mathrm{path}}(\theta),
\end{equation}
其中 $R_{\mathrm{path}}(\theta)$ 是该路径上的稳健风险统计量。对称路径以 attention-distribution KL 的尾部统计组织 $R_{\mathrm{path}}$；角色感知低比特路径在同一选择纪律下，把 K-path 与 V-path 的代理分开定义。

对称路径（包括 \texttt{INT8} 基准与对称 \texttt{INT4} 试探路径）使用同一组本地读数。设校准样本集合为 $\mathcal D_{\mathrm{calib}}$（来源、规模与序列长度见第~\ref{sec:ch3-deployment}~节），定义
\begin{equation}
\mu(\theta)
=
\operatorname{Mean}_{(x,l,h,t)\in\mathcal D_{\mathrm{calib}}}
d_{\mathrm{KL}}^{(l,h,t)}(\theta),
\end{equation}
\begin{equation}
q_{0.95}(\theta)
=
\operatorname{P95}_{(x,l,h,t)\in\mathcal D_{\mathrm{calib}}}
d_{\mathrm{KL}}^{(l,h,t)}(\theta),
\end{equation}
\begin{equation}
c_K(\theta) = \frac{|\{x\in K^{\mathrm{cal}}: |x| > q_{\max}^{\mathrm{int}}(\theta)\}|}{|K^{\mathrm{cal}}|}, \qquad
c_V(\theta) = \frac{|\{x\in V^{\mathrm{cal}}: |x| > q_{\max}^{\mathrm{int}}(\theta)\}|}{|V^{\mathrm{cal}}|}.
\end{equation}
其中 $\mu(\theta)$ 沿用第~\ref{subsec:ch3-kl-target}~节的均值代理逐候选化作为辅助读数；$q_{0.95}(\theta)$ 是同一逐位置 KL 的 95\% 分位数，用于尾部案例排序；$c_K(\theta), c_V(\theta)$ 是量化后归一化张量绝对值越过整数上界 $q_{\max}^{\mathrm{int}}(\theta)$（\texttt{INT8} 取 127、\texttt{INT4} 取 7）的元素比例，用于过滤靠过度裁剪换取低 KL 的候选。可行域定义为
\begin{equation}
\Theta_{\mathrm{feasible}}
=
\{\theta \in \Theta_{\mathrm{path}}: c_K(\theta)\le \tau_K,\; c_V(\theta)\le \tau_V\},
\end{equation}
本文取 $\tau_K = \tau_V = 0.01$。若 $\Theta_{\mathrm{feasible}}\neq\emptyset$，选择规则为
\begin{equation}
\theta^\star
=
\arg\min_{\theta \in \Theta_{\mathrm{feasible}}}
q_{0.95}(\theta),
\end{equation}
最终以尾部统计为主序，均值 $\mu$ 仅作辅助读数与回退场景下的次级排序键。

若所有候选均违反裁剪率约束，回退规则按字典序排序：
\begin{enumerate}[label=(\arabic*),leftmargin=2.4em,itemsep=1pt,topsep=2pt]
  \item 先最小化总裁剪负担 $c_K(\theta)+c_V(\theta)$；
  \item 若 $c_K+c_V$ 相同，再比较尾部统计 $q_{0.95}(\theta)$；
  \item 若尾部统计仍相同，最后比较平均偏移 $\mu(\theta)$。
\end{enumerate}
排序第一的候选记为 $\theta^\star$，并在产物字段中标记触发回退及其原因。

\paragraph{\texttt{INT4-RoleAlign} 路径承接}
\texttt{INT4-RoleAlign} 沿用上述四步流程，但不把 $(p_K, p_V)$ 压成单一 attention-KL 分数。K-path 以 $p_K$（per-channel Key 非对称量化的百分位裁剪参数，详见第~\ref{sec:ch3-paths}~节）为候选参数，使用 attention-distribution KL 与尾部统计完成选择；V-path 以 $p_V$（per-token Value 非对称量化的百分位裁剪参数）为候选参数，使用独立的输出扰动代理。本节产出两类产物：路径特定校准字段供在线缓存写入直接读取，逐层敏感度统计供第~\ref{sec:ch3-allocator}~节的预算分配模块读取。逐头温度校正作为补充诊断收入附录，不进入主线流程。
```


### Round 2 综合（v1 审）

加权综合: **7.86 / 10** — 接近阈值（D1 8.6 / D4 8.1 通过；D2 7.4 / D3 7.6 / D5 7.6 / D6 7.6 条件通过）

| Agent | 分数 | Verdict | 关键残留 |
|-------|------|---------|---------|
| D1 顶会 | 8.6 | ✅ | P1-A enumerate 未内嵌 / P1-B V-path R 公式缺 |
| D2 数学 | 7.4 | 🟡 | GAP-1 $K^\mathrm{cal}/V^\mathrm{cal}$ 未定义 / GAP-2 $\mu$ vs $\Delta^{cal}$ 关系 / GAP-3 V-path R |
| D3 复现 | 7.6 | 🟡 | P1-A 回退 ties 多级 tiebreaker / P1-B $p_V$ 搜索域悬空 |
| D4 中文 | 8.1 | ✅ | P1-A enumerate 仍独立列表 / P1-B "本节产出"轻微元叙述 |
| D5 Skeptical | 7.6 | 🟢 | MED $\mu$ 辅助读数用途 / MED RoleAlign 是否沿用 $\Theta_\mathrm{feasible}$ |
| D6 博士生 | 7.6 | 🟡 | P1-1 $R_\mathrm{path}$ 符号断层 / P1-2 $\mu$ 双重身份 / P1-3 RoleAlign 段密度 |

### Round 2 整合修订（v1 → v2，落地版）

整合 6 agent 一致 P1 必改 (mechanical 整合)：

1. **D1 P1-B + D2 GAP-3 + D6 P1-3**: V-path $R_V(\theta)$ 给符号 + forward ref to §3.5.3
2. **D1 P1-A + D4 P1-A**: enumerate (1)/(2)/(3) → 内嵌单句 "先...再...最后..."
3. **D5 MED + D6 P1-2**: $\mu$ 双重身份澄清: "$\mu$ 不参与主选 argmin，仅作为回退次级排序键"
4. **D2 GAP-1 局部 + D6 P1-1**: $R_\mathrm{path}(\theta) = q_{0.95}(\theta)$ 显式绑定 + \label{eq:ch3-q95}
5. **D2 GAP-1 + D6 P3**: $K^\mathrm{cal}, V^\mathrm{cal}$ 与 $\mathcal D_\mathrm{calib}$ 显式绑定
6. **D4 P1-B**: "本节产出两类产物" → "产物字段分为两类"
7. **D6 P1-3**: RoleAlign 承接段拆段（K/V 路径 + 产物 + 附录处置）
8. **D5 MED RoleAlign**: K-path 与对称路径共享 $\Theta_\mathrm{feasible}$ 显式说明

不采纳:
- D3 P1-A 多级 tiebreaker (v_rel_l2_mean / log2(group_size) / clip_percentile) — 实现细节，属 §3.7 范围
- D3 P1-B $p_V$ 搜索域 — 推迟到 §3.5.3 落地（避免在 §3.4.2 暴露具体实例值）

### v2 落地稿见 git commit。



## §3.5.1 INT8 基准路径 — 审改循环

**目标行**: ch3_method.tex line 194-241 (含 §3.5 父节开头 + §3.5.1 主体, v0)

### Round 1 综合（v0 审）

加权综合: **6.53 / 10** — 🔴 不通过

| Agent | 分数 | Verdict | 关键问题 |
|-------|------|---------|---------|
| D1 顶会 | 6.5 | 🟡 | P0-1 $s^\mathrm{dyn}$ 公式缺 / P0-2 $m$ 无值 / P1 元叙述 4 处 |
| D2 数学 | 8.2 | ✅ | P2: $s^\mathrm{dyn}$ + $m$ + $g$ 维度 / P3: $q_\max$ 数值 |
| D3 复现 | 5.2 | 🔴 | P1 阻断: $s^\mathrm{dyn}$ = absmax/127 / $m=1.0$ / $q_\max=127$ |
| D4 中文 | 5.2 | 🔴 | §18 元叙述 5 处 / §17 防御负向 3 处 / §19 PPT 3 处 |
| D5 Skeptical | 7.0 | 🟡 | P2: max 机制 trade-off 未披露 / "主导"无条件使用 |
| D6 博士生 | 7.2 | 🟡 | P1: line 241 "其一/其二" PPT / line 229 $m$ 来源不明 |

### Round 1 必改清单

**P0 — 4+ agent 一致:**
- **P0-1 $s^\mathrm{dyn}$ 计算公式** (D1, D2, D3, D6) — 代码: $\mathrm{absmax}/q_\max$
- **P0-2 $m$ 取值** (D1, D2, D3, D6) — 代码: $m=1.0$（下界保护，非放大）
- **P0-3 元叙述清理** (D1, D4, D6) — line 197/199/207/241 多处
- **P0-4 "其一/其二" PPT 段删除** (D1, D4, D6) — line 241 整段重写

**P1:**
- $q_\max=127$ 显式 (D1, D2, D3)
- $g=128$ 分组维度沿通道 (D2, D3)
- K/V 自适应开关独立 (D3)
- "只在必要时触发" → "每步 max" (D3)
- max trade-off 量化误差扩大 (D5)
- $q\in\mathbb Z$ 引入句 (D1)

### v1 候选稿（应用 P0/P1 修订）

```latex
\section{跨位宽量化路径的实例化设计}
\label{sec:ch3-paths}

第~\ref{sec:ch3-calibration}~节给出的离线校准流程与稳健选择纪律不规定唯一位宽或唯一量化格式。后文先用 \texttt{INT8} 基准路径检查校准闭环能否在保守位宽下稳定落地，再用对称 \texttt{INT4} 试探路径暴露直接降位宽后的结构困难，最后用 \texttt{INT4-RoleAlign} 把低比特路径改写为 K/V 角色分离的非对称格式，并在方法层面区分它与 \texttt{KIVI-style}~\cite{liu2024kivi} 的参数来源。三条路径共享第~\ref{sec:ch3-calibration}~节的参考行为提取、可行域约束、尾部优先选择和固定产物输出，差异仅在参数接口、量化轴与行为代理。

\input{tables/table_ch3_path_instantiation}

\subsection{INT8 基准路径：静态 Scale 与自适应保护}

\texttt{INT8} 位宽提供 255 级离散网格，校准层输出的 scale 误差可逐 token 精确追溯，本文以此作为行为引导校准闭环的第一性验证实例。压缩率上 \texttt{INT8} 也作为后续低比特路径的对照基线。

在该路径中，Key 与 Value 均采用对称、逐组（per-group，沿通道维度每 $g=128$ 个元素一组共享一个缩放参数）的静态量化。记第 $l$ 层第 $j$ 个分组内的待量化张量为 $x_{l,j}$，对给定校准百分位参数 $p_c$ 与分组大小 $g$，静态缩放参数为
\begin{equation}
s_{l,j}^{\mathrm{static}}
=
\frac{\operatorname{Percentile}\!\big(|x_{l,j}|; p_c\big)}
{q_{\max}},
\end{equation}
其中 $q_{\max}$ 表示对称量化网格的正端点（\texttt{INT8} 取 127）。令 $q\in\mathbb{Z}$ 为量化整数输出，量化—反量化写为
\begin{equation}
q
=
\operatorname{clamp}\!\left(
\operatorname{round}\!\left(\frac{x}{s_{l,j}^{\mathrm{static}}}\right),
-q_{\max},\, q_{\max}
\right),
\qquad
\hat x = q\, s_{l,j}^{\mathrm{static}}.
\end{equation}
$(p_c, g)$ 在 $\Theta_\mathrm{path}$ 候选网格上由第~\ref{subsec:ch3-two-stage}~节的 KL 尾部统计与裁剪率约束筛选选出。

为处理运行时输入分布超出校准覆盖范围的情况，本路径在静态缩放参数之外引入自适应保护机制。记当前写入张量为 $x^{\mathrm{cur}}_{l,j}$，动态尺度
\begin{equation}
s_{l,j}^{\mathrm{dyn}}
=
\frac{\operatorname{absmax}\!\big(|x^{\mathrm{cur}}_{l,j}|\big)}{q_{\max}},
\end{equation}
保护裕度 $m\ge 1$ 为固定超参（本文取 $m=1$）。最终缩放参数取
\begin{equation}
s_{l,j}^{\mathrm{final}}
=
\max\!\left(
m \cdot s_{l,j}^{\mathrm{static}},
\;
s_{l,j}^{\mathrm{dyn}}
\right),
\end{equation}
即在校准分布内静态参数主导；当当前 token 的 $\operatorname{absmax}$ 超出 $m \cdot s_{l,j}^{\mathrm{static}}\cdot q_{\max}$ 对应的覆盖时，由动态尺度接管以避免裁剪溢出。$\max$ 操作在每个写入步独立执行，K 与 V 的自适应保护开关相互独立。极端漂移下 $s_{l,j}^{\mathrm{final}}$ 增大会带来一定量化误差扩大，作为换取裁剪安全的工程代价。该机制在缓存写入时是否回写历史缓存的系统语义见第~\ref{sec:ch3-deployment}~节。
```


### Round 2 综合（v1 审）

加权综合: **8.48 / 10** — ✅ PASS（阈值 8.0）

| Agent | 分数 | Verdict | 关键残留 |
|-------|------|---------|---------|
| D1 顶会 | 8.1 | ✅ | P1-A $m\ge 1$ 冗余 / P1-B absmax 双绝对值 / P1-C 父节末 forward ref |
| D2 数学 | 9.1 | ✅ | 仅 2 P3 不阻挡 |
| D3 复现 | 9.0 | ✅ | 仅 2 P3 ($m\ge 1$ vs $>0$ / ε=1e-5 零向量保护) |
| D4 中文 | 8.6 | ✅ | P1: "以避免裁剪溢出" 轻度负向 |
| D5 Skeptical | 8.1 | 🟢 | P3: "逐 token 精确追溯" 与 per-group 矛盾 |
| D6 博士生 | 7.5 | 🟡 | **P1: "逐 token" 粒度矛盾 / P1: $m=1$ 公式保留动机** |

### Round 2 整合修订（v1 → v2，落地版）

1. **D5 P3 + D6 P1**: "逐 token 精确追溯" → "逐组（per-group）精确追溯"
2. **D1 P1-B + D6 P2**: $\operatorname{absmax}(|x^\mathrm{cur}|)$ → $\operatorname{absmax}(x^\mathrm{cur})$（去双重绝对值）
3. **D1 P1-A**: "$m\ge 1$ 为固定超参（本文取 $m=1$）" → "$m$ 为固定超参（本文取 $m=1$）"
4. **D4 P1**: "由动态尺度接管以避免裁剪溢出" → "由动态尺度接管以维持当前 token 的量化覆盖"
5. **D6 P2**: 加 "防止异常 token 被强制截断至 $q_{\max}$" 在 max trade-off 段
6. **D1 P1-C**: 父节末加 forward ref to §3.6 allocator

### v2 落地稿见 git commit。



## §3.5.2 对称 INT4 的局限与格式升级动因 — 审改循环

**目标行**: ch3_method.tex line 243-249 (短节, v0)

### Round 1 综合（v0 审）

加权综合: **7.41 / 10**

| Agent | 分数 | Verdict | 关键问题 |
|-------|------|---------|---------|
| D1 顶会 | 7.0 | 🟡 | P1: 17 倍数值未给 / cliff 方向 finding 提前暴露 |
| D2 数学 | 7.2 | 🟡 | G1 P2: INT4 15 级缺失 / G3 P2: "难以响应"无定量证据 |
| D3 复现 | 9.2 | ✅ | P2: "Qwen 系列" 限定缺失 (forward ref 全部 grep 验证存在) |
| D4 中文 | 6.2 | 🟡 | P1-A "这里引用..." 元叙述 / P1-B "难以响应" 防御 / P2-A 章节过渡过重 |
| D5 Skeptical | 7.3 | 🟢 | P2: "Value 时序动态范围" → "Value 逐 token 动态范围" |
| D6 博士生 | 8.5 | ✅ | 必改: line 247 forward ref 密度过高 |

### Round 1 整合修订（v0 → v2 直接落地）

1. **D1 P1 + D2 G1**: 加 "INT8 255 级 vs INT4 15 级，等级密度差约 17 倍"
2. **D4 P1-A + D6 必改**: 删除 "这里引用这些读数只作为..." 元叙述，改为括注
3. **D4 P1-B + D2 G3**: "继续细调...难以响应..." → 正向机制 "单一对称 scale 既要...又要...互相妥协"
4. **D3 P2**: "Qwen 读数" → "Qwen 系列读数"
5. **D5 P2**: "Value 时序动态范围" → "Value 逐 token 的动态范围"
6. **D4 P2-A + D6**: 章节过渡精简
7. **D2 G4**: "K4V4 作为剂量-响应辅助观察" 与 §3.2 v3 证据分级对齐
8. **D1 P2**: 删除 "本节把对称 INT4 视作一次低比特压力测试" 元叙述 → "扮演格式选择的下界锚点"

### v2 落地稿

```latex
\subsection{对称 INT4 的局限与格式升级动因}

直接把上述对称路径从 \texttt{INT8} 降到对称 \texttt{INT4} 后，量化网格首先变粗。\texttt{INT8} 提供 255 级有效等级，而对称 \texttt{INT4} 只剩 15 级（等级密度差约 17 倍）；原先可由细粒度缩放参数吸收的分布差异被压到这个粗网格内。

第~\ref{sec:ch3-problem}~节给出了机制理由：Key 扰动先进入 logits 排序，再经 softmax 改写注意力分布。第~\ref{sec:ch3-motivation-kv}~节与第~\ref{sec:exp-kv-sensitivity}~节的 Qwen 系列读数为此提供经验锚点：\texttt{K4V8} 在 Key 侧先暴露 cliff，\texttt{K8V4} 未出现同强度失稳；\texttt{K4V4} 同时压低 K 与 V，作为剂量-响应辅助观察一并列出，完整跨模型判读见第四章相关表与图。

因此对称 \texttt{INT4} 在本文中扮演格式选择的下界锚点：单一对称 scale 既要在 \texttt{INT4} 网格上覆盖 Key 通道间的幅值异质性，又要承担 Value 逐 token 的动态范围变化，两个维度被压在同一参数上互相妥协。下一节将低比特路径改写为 \texttt{INT4-RoleAlign}，把这两个维度分配到独立量化轴上。
```

