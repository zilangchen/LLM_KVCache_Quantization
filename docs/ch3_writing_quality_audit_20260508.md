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
