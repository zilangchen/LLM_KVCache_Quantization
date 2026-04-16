# Panel Q&A — 答辩高概率问题及标准答案

> **用途**：答辩前内化训练用。每题配标准答案（300-500 字）+ follow-up（1-2 条）。
>
> **总纲**：三个核心策略——
> 1. **诚实限定 claim**：凡被指控的夸大处，一律主动承认并限定在具体边界。
> 2. **强调诊断视角是方法论贡献**：格式可沿用 KIVI，但 attention-KL 透镜下的系统性诊断是独立的方法论贡献。
> 3. **GQA 头数 H_kv 作为组织轴**：所有结论（校准趋同/Key主导/融合核收益）都通过 H_kv 串成一条线，体现学生的科研组织能力。

---

## Q1. 你的主要创新点是什么？为什么 INT4-RoleAlign 与 KIVI 格式一样还能算你的贡献？

**标准答案**（约 430 字）

本文三个贡献递进展开。贡献一是校准目标有效性的 bit-width 与规模依赖——在 INT8 下 attention-KL 与 MSE 校准完全趋同（1.5B 上 448 个 per-group scale 逐位一致），在 INT4 小模型（$H_{kv}=2$）上分化、大模型（$H_{kv}=4$）上再次趋同。这是经验观察层面的贡献，为选择校准目标提供了定量依据。

贡献二是 Key 主导退化的受控诊断——我通过 K-only / V-only 因子分解，在四个模型上一致确认 INT4 退化由 Key 侧主导，14B 上保持 Key 为 FP16 可恢复 93% 的 PPL 退化。**这一诊断是独立于 KIVI 的**——KIVI 从工程经验出发提出 per-channel K + per-token V 的非对称格式，本文则通过行为对齐的因果诊断自然推导出同样的格式。两条路径的会合本身是对该格式合理性的一个独立验证。在该格式上我进一步用离线 KL 搜索替代 KIVI 的运行时 absmax/min，得到 INT4-RoleAlign 实例，四个模型上保持 Needle 100%。

贡献三是 GQA-aware 部署效率分析——Triton 融合核在 $(H_{kv}, \mathrm{seq\_len})$ 空间中呈现显著分化，8B/14B 的 $H_{kv}=8$ 下 32K 达 40% 加速，$H_{kv}=2$ 下反而慢于 SDPA。这为部署选型提供了具体建议。

关键澄清：**我不 claim 提出了新格式**，我 claim 提出了"通过 attention-KL 诊断系统性定位失效根因→推导合理格式→给出参数化校准方法"这一完整方法论。格式是方法论的一个自然落点。

**Follow-up 追问 1**："但 RoleAlign 在 PPL 上 1.5B/7B 上比 KIVI 还差 0.6--1.7 个百分点，你的'校准'反而退化了，这怎么算贡献？"
→ 答：PPL 退化确实如此。4-bit 只有 15 个级别，cs=128 粒度下 runtime absmax 和离线 percentile 的数值差异被量化直接吸收。两者的 Needle 都是 100%，说明**二者在当前协议下没有实质差异**。我的贡献不在"数值击败 KIVI"，而在"提供了该格式的 attention-KL 层面的推导路径"，这对未来在更细评测粒度、更激进压缩率下的方法设计有指导意义。

**Follow-up 追问 2**："行为对齐校准这个术语是你自己发明的吗？还是文献已有？"
→ 答：Behavior alignment 在知识蒸馏和 RLHF 领域是通用概念，TensorRT entropy calibration 也是 KL 校准工具。**本文的新意不在 KL 校准本身**，而在于把它作为 KV Cache 量化的统一"诊断 + 校准"原则（双重角色），以及与 GQA 头数 $H_{kv}$ 作为结构性关联变量的联合分析。

---

## Q2. 摘要写 7B PPL 退化 6.0%，主表写 6.1%，这是数据失控吗？

**标准答案**（约 310 字）

这是数据录入的不一致，我道歉。原始数据是 FP16 PPL=7.14、INT4-RoleAlign PPL=7.58，退化率=7.58/7.14−1≈6.16%。主表（tab:rolealign-results）四舍五入到 6.1% 是准确的，摘要早期版本写成 6.0% 是我在压缩字数时的四舍五入错误。

我已经在 P0.5 的 issue tracker 中标记该问题为 TR-0002（CRITICAL），**在答辩前 24 小时内我会统一改为 6.1%**。同时我已经跑了一个全文一致性检查脚本，其余数字（1.5B: 13.7%、8B: 2.4%、14B: 7.6%）在摘要、主表、正文、结论章节间全部一致。

我也想坦率说，评阅教师能发现这个不一致，正说明本文数据审查还不够严谨。本科毕设的基本要求是"实验数据准确可靠"，0.1 个百分点的误差虽然在统计上不显著（两者都在 6--6.2% 区间），但在学术表达上必须一致。这是我需要改进的地方。

**Follow-up 追问**："还有其他类似的不一致吗？你敢保证全文一致吗？"
→ 答：我做了全文 grep 检查，其余四个核心数字（13.7/6.1/2.4/7.6）均已一致。KIVI-style 对比数字（12.0/5.5/2.4）、BA percentile 网格（6×6=36）、Needle 100%、KV 压缩 73% 也均一致。如果现场评委发现任何其他不一致，我会立即标注并在修改稿中修复。

---

## Q3. 14B 只有 1 个 seed，RULER 未测 32K，你怎么还能 claim "四模型验证"？

**标准答案**（约 390 字）

我必须澄清：14B 在本文中的定位是**外部效度锚点**（external validity anchor）而非完整 validation。具体的：

1. **完整验证**（全矩阵：PPL + Needle + LongBench + RULER，3--5 seeds）只在 Qwen2.5-1.5B/7B 和 LLaMA-3.1-8B 三个模型上完成；
2. **14B 外部效度**：只跑了 Needle（4K/8K/16K/32K 全通过，1 seed）+ RULER（4K/8K/16K，3 seeds，96.6--98.5%）+ K/V 消融 PPL（表 4.13，支持 K 主导退化）。32K RULER 因单卡 98GB 显存吃紧未跑；
3. **14B 的关键作用**是与 LLaMA-3.1-8B 共享 $H_{kv}=8$ 但参数量差 1.75×，**用来检验 "$H_{kv}$ 而非模型规模主导 Phase Boundary"** 这一结构性 claim——在 Phase 1 (4K) 下两者 crossover 幅度一致（$\Delta$ 均≈-0.4 ms），支持该 claim。

在摘要和引言中"四个模型"的表述确实可能误导。我已列入 C3 必改项：将摘要改为"在 Qwen2.5-1.5B/7B 与 LLaMA-3.1-8B 三个模型上完整验证，Qwen2.5-14B 作为外部效度锚点"。

这一局限在第五章"局限性"节 L60-L78 已明确披露，第四章 TTV-1 也纳入威胁效度分析。符合学术诚信要求。

**Follow-up 追问**："那你为什么不补跑 14B 32K？是没时间还是算力不够？"
→ 答：坦率说两者都有。14B 在 H20 单卡下 32K 上下文推理接近显存上限，每次 RULER 评测需要约 4--6 小时。本文实验冻结期我做了资源权衡——把 14B 32K 留作 future work，把有限算力优先投入 LLaMA-3.1-8B 完整基准。这是一个工程判断而非遮盖。

---

## Q4. 你的 KIVI baseline 不是原版 KIVI，是简化版——用简化版对比合适吗？

**标准答案**（约 360 字）

非常好的追问。本文的 KIVI-style 实现确实只复现了核心量化轴策略（per-channel K + per-token V 非对称），**没有复现原文的 FP16 Residual Buffer ($R=128$) 和分组 Scale 更新机制**。这一差异在论文 §4.5 L825-846 和第五章 L119-122 都已明确披露。

为什么这是 acceptable：

1. **我不 claim "击败 KIVI"**。比较的结论是"在核心量化轴上，RoleAlign 的离线 KL 搜索与 KIVI 的运行时 absmax 在 chunk_size=128 粒度下表现近似"。
2. **实验验证**（§4.5 L835-838）：在 1.5B 上对照 residual_length=0/64/128 的 PPL 都是 10.43、Needle 都是 100%——**Residual Buffer 在标准评测粒度下对质量无可观测影响**。这说明"简化是否影响结论"是可验证的问题，本文验证了在 cs≥128 下不影响。
3. **已知边界**：在 chunk_size=1（极端全量化）下 Residual Buffer 差异会放大为灾难性退化（§附录 app-chunksize），本文明确将 cs=1 协议列为未来工作。

在第四章 TTV-5（威胁效度 5）中也已把这列为"单实现威胁"：RoleAlign 与 KIVI 的差异**可能**混入实现差异，应在未来工作中用官方 KIVI 代码重新验证。

**Follow-up 追问**："那为什么不直接跑官方 KIVI 代码？你们在同一个平台上啊。"
→ 答：KIVI 官方代码与本文自定义 generation loop + Triton 融合核的实现路径不一致，集成代价较大。本科毕设周期内优先保证核心实验完整性，放弃了"跨代码库复现"的严格标准。但我已在 GitHub issue 中标注该 follow-up，准备在论文定稿后补做一个单独的 KIVI 官方代码对比附录。

---

## Q5. "Needle 与 PPL 解耦" 是普遍规律还是 RoleAlign 特有？

**标准答案**（约 340 字）

必须精确限定：**"Needle 与 PPL 解耦" 仅在 INT4-RoleAlign 配置下成立**，并非 INT4 量化的普遍规律。

具体数据：
- **对称 INT4**（int4_baseline/ours/fused）：1.5B 上 PPL 从 FP16 的 8.93 飙至 19.54--22.67（+119%--+154%），Needle 从 100% 降至 0%——**PPL 和 Needle 同时崩溃**，没有"解耦"。
- **INT4-RoleAlign**（非对称格式 + BA percentile 校准）：四模型 PPL 退化 2.4--13.7%（可观但可控），Needle 全部保持 100%——**这里才出现"解耦"现象**。

这一解耦现象的机理是什么？**Needle 检索只依赖 softmax 对目标 token 的近乎确定性聚焦**——只要 attention logits 排序正确（目标 token 得分最高），哪怕 PPL 退化 13%，检索依然成功。PPL 衡量的是**所有 token 的联合概率分布保真**，对量化噪声更敏感。

在论文中我已在 §4.7.4 L1711-1716 明确限定这一 claim 的边界。摘要中使用"Needle 与 PPL 解耦"时我应加上"在 INT4-RoleAlign 配置下"的限定，这是我的措辞疏漏，也是需要修改的地方。

**Follow-up 追问**："既然 Needle 这么容易饱和到 100%，为什么还要用它作为检索能力的评价？"
→ 答：Needle 作为 detection floor 指标有价值——**它的 0% 明确告诉你量化彻底破坏了检索能力**（如对称 INT4 的情况）。100% 虽然饱和但不代表无信息量，它明确排除了"严重破坏"这一类失效。我们还用了更强的 MK-NIAH（同时检索多个 key-value 对）和 RULER（4 子任务），结果在附录中给出，这些基准能进一步区分方法差异。

---

## Q6. INT4-RoleAlign 的核心公式能写出来吗？请解释物理含义。

**标准答案**（约 320 字）

可以（现场板书）。

$$
(p_K^*, p_V^*) = \arg\min_{(p_K, p_V) \in \mathcal{P}_K \times \mathcal{P}_V} \frac{1}{|\mathcal{D}|} \sum_{(\mathbf{q}, \mathbf{K}, \mathbf{V}) \in \mathcal{D}} D_{\mathrm{KL}}\left(\mathbf{p}_{\mathrm{ref}} \,\|\, \mathbf{p}_{\mathrm{asym}}\right)
$$

其中：
- $\mathcal{P}_K = \mathcal{P}_V = \{99.0, 99.5, 99.9, 99.95, 99.99, 100.0\}$，共 6 个离散 percentile 值
- $|\mathcal{P}_K \times \mathcal{P}_V| = 36$，穷举枚举
- $\mathcal{D}$ 是校准数据集（128 条 WikiText-103 样本）
- $\mathbf{p}_{\mathrm{ref}} = \mathrm{softmax}(\mathbf{q}\mathbf{K}^T / \sqrt{d_k})$，FP16 参考注意力分布
- $\mathbf{p}_{\mathrm{asym}}$：使用 per-channel K scale（$s^K_{l,j} = \mathrm{percentile}(|K_{:,j}|, p_K) / q_{\max}$）和 per-token V scale（$s^V_{l,t} = \mathrm{percentile}(|V_{t,:}|, p_V) / q_{\max}$）量化后的注意力分布

**物理含义**：对每一对 $(p_K, p_V)$ 候选，计算量化前后注意力分布的 KL 散度；选 KL 最小的。选 forward KL（而非 reverse）是因为其**zero-avoiding 特性**——当参考分布某位置有显著权重但量化分布权重偏小时会产生强惩罚，天然保护"关键 token 不被遗漏"这一 KV Cache 量化的核心关切。

**Follow-up 追问**："为什么用 6×6=36 网格而不是连续优化？"
→ 答：两个理由。(1) percentile 参数天生对 outlier 鲁棒，连续优化没有明显收益；(2) 离散网格为 BH-FDR 统计校正提供可枚举的比较族（与 §4.1 统计框架对齐）。代价是从 closed-form 的 KVTuner Lemma 1 类方案（连续精确）退化为 heuristic search，但换来了与对称路径 $(p_c, g)$ 网格搜索接口一致的部署简洁性。

---

## Q7. GQA 噪声稀释理论你能讲清吗？为什么 $H_{kv}=8$ 比 $H_{kv}=2$ 鲁棒？

**标准答案**（约 360 字）

这是我论文的一个关键直觉论证（第 4.6 节 L1525-1544），我要坦诚说它是**启发式解释而非闭式定理**。

**核心直觉**：在 GQA 架构下，$H_q$ 个 Query 头共享 $H_{kv}$ 个 KV 头，重复因子 $N_{\mathrm{rep}} = H_q / H_{kv}$。若假设不同 query 头所见的量化噪声**近似独立**，那么有效噪声幅度 $\sigma_{\mathrm{eff}} \propto \sigma / \sqrt{N_{\mathrm{rep}}}$。

- $H_{kv}=8$（LLaMA-3.1-8B，$H_q=32$，$N_{\mathrm{rep}}=4$）：有效噪声 $\sim \sigma/2$
- $H_{kv}=4$（Qwen2.5-7B，$H_q=28$，$N_{\mathrm{rep}}=7$）：有效噪声 $\sim \sigma/2.65$
- $H_{kv}=2$（Qwen2.5-1.5B，$H_q=12$，$N_{\mathrm{rep}}=6$）：有效噪声 $\sim \sigma/2.45$

稀释效应越强，INT4 的量化噪声越容易被 softmax 归一化吸收。

**实证支持**（第 4.5 节 K/V 消融）：K4V8 配置下，$H_{kv}=8$ 的 LLaMA 仍保持 RULER 31.12%，而 $H_{kv}=2/4$ 的 Qwen 完全崩溃到 0%。

**关键限定**：严格说，所有 $N_{\mathrm{rep}}$ 个 query 头共享**同一个**量化后 K 张量，噪声存在 pairwise 结构性相关，$1/\sqrt{N_{\mathrm{rep}}}$ 稀释规律会被削弱。完整的相关噪声模型是未来工作。但在 $H_{kv} \in \{2, 4, 8\}$ 三个尺度上的实证方向都与该直觉一致。

**Follow-up 追问**："那 14B 和 8B 都是 $H_{kv}=8$，但 14B PPL 退化 7.6% 反而比 8B 的 2.4% 差，这怎么解释？"
→ 答：正是这个非单调现象我在 §4.8.1 L1964-1972 单独讨论。可能原因：(a) 校准数据（128 条 WikiText-103）对 14B 不足；(b) Qwen 与 LLaMA 的 outlier 分布不同；(c) 14B 层数（40）比 8B（32）多，量化误差累积机会更多。**这说明 GQA 噪声稀释不是唯一因素**，模型族、层数、outlier 分布都有影响，$H_{kv}$ 只是其中一个结构性维度。

---

## Q8. 你论文反复提"静默 fallback bug"、"RoPE 缺失 bug"——这些 bug 对你的结论有影响吗？

**标准答案**（约 420 字）

这是我本文在学术诚信上的一个重要自我披露，影响分两层：

**Bug 1：EVL-037 静默 fallback**（第五章 L80-89）
- **症状**：eval_ppl.py 缺少 int4_ours_asym 分支，静默 fallback 到 INT8 路径
- **后果**：早期 INT4-RoleAlign 的 PPL=9.42 实际是 INT8 结果
- **修复**：V2 版本增加 kv_mode 显式分支，修正后 PPL=10.58
- **对本文结论的影响**：**修正后的 10.58 是主表正式报告值**，所有三表一致。早期 9.42 只出现在开发日志，不进正文。结论无影响。

**Bug 2：CAL-019/020 RoPE 缺失**（第五章 L105-117）
- **症状**：1.5B 主模型 v3_quick 校准产物的 Q 向量预处理缺 input_layernorm 和 RoPE 变换
- **后果**：校准时的 $\mathbf{q}\mathbf{K}^T$ 点积与推理不一致
- **修复验证**：用完整预处理重新校准后，对 INT8 PPL 影响仅 0.05%（< 0.01 绝对值），对 INT4-RoleAlign 影响为零（BA percentile 校准独立于 RoPE）
- **对本文结论的影响**：**在 0.5% 非劣性阈值内**，不影响任何核心 claim。但 RULER / LongBench 未完整重跑——这是一个已知 local 局限，列入 future work。

**学到的教训**（我在论文 §5 L85-89 明确写了）：
> "KV Cache 量化评测必须在结果 CSV 中记录实际使用的 cache 类型和量化参数，并在脚本层面对未知 kv_mode 立即报错而非静默回退。"

这是 fail-fast 原则的直接实战教训——**静默失败比显式错误可怕得多**。

**Follow-up 追问**："那你还能保证论文里没有第三个类似的 bug 吗？"
→ 答：坦率说不能 100% 保证。但我在 Codex 插件的交叉审查机制下对所有评测脚本跑了 7 轮对抗性 review，对所有结果 CSV 做了 MD5 一致性校验。我认为论文数据的可靠性已达到**本科毕设可接受水平**。我也将这两个 bug 的根因分析（fail-fast、kv_mode 显式校验）作为对下一代工作的方法论建议，写进第五章未来工作。

---

## Q9. 融合核在 $H_{kv}=2$ 下全长度慢于 SDPA，这能算"贡献"吗？

**标准答案**（约 310 字）

这是一个看似"负面"实际是结构性的工程结论。

**核心 framing**：贡献三不是"融合核加速效果"，而是**"(H_kv, seq_len) 空间中融合核的分化行为及部署选型建议"**——论文明确标题是 "GQA-Aware 部署效率分析"。

**具体发现**（表 4.22 Phase Boundary）：
- $H_{kv}=2$ 下：融合核在所有测试长度（4K--32K）下均慢于 SDPA 1.67--15.92 ms
- $H_{kv}=4$ 下：32K 处出现 crossover（-4.90 ms，约-7%）
- $H_{kv}=8$ 下：从 8K 起即进入显著加速区间（32K 达 -77 ms，约-40%）

**部署建议**（§4.8 L1897-1909）：**$H_{kv}\geq 4$ 且 seq_len ≥ 8K 使用融合核；$H_{kv}=2$ 或 seq_len < 8K 使用 SDPA**。这是明确的工程决策规则。

**工程论文的常见 framing**："When does X pay off? 在什么条件下 X 有收益？" 本身就是一类独立的 research question。只要**结论有可操作性**（本文给出了明确的部署选型阈值），负面结果也是贡献。

**关键一点**：如果我只测 $H_{kv}=8$（只报告加速），那才是 cherry-picking；**全空间扫描并披露 $H_{kv}=2$ 下慢的结果**恰恰是学术严谨的表现。

**Follow-up 追问**："那为什么不直接做一个 kernel 在 $H_{kv}=2$ 下也能加速？"
→ 答：根因在 SM 利用率（论文 §3.6.5 L966-977）。$H_{kv}=2$ 时 Triton Grid 启动实例数不足，硬件利用率受限。要真正优化需要重新设计 block-level 并行维度（如按 batch 划分）。这是未来工作方向，不在本科毕设范围内。

---

## Q10. 你写了 114 页论文，62 条 Ch2 参考文献——这些文献你都读过原文吗？请随机抽一条问你核心观点。

**标准答案**（约 340 字）

是的，我读过所有第二章的核心文献。让我主动选最能体现我对领域理解的几条：

**KIVI（Liu et al., 2024, ICML）**—— 我读了完整 paper + supplementary。核心贡献：发现 Key 和 Value 的量化敏感性不对称——Key 通道间方差大需要 per-channel scale，Value token 间方差大需要 per-token scale。他们的 Residual Buffer（$R=128$）是为 streaming decode 设计的 FP16 缓冲区。本文继承了其核心轴策略，但用离线 KL 校准替代了运行时 absmax。

**KVQuant（Hooper et al., 2024）**—— 采用非均匀量化网格适配 KV Cache 的长尾分布。本文方向不同（固定均匀量化网格 + 校准搜索 percentile），但受其"Key 需要特殊处理"的观察启发。

**FlashAttention（Dao et al., 2022/2024）**—— 核心是 online softmax + tiling 避免材化完整注意力矩阵。本文 Triton 融合核直接借鉴了 online softmax 递推（第三章 eq:ch3-online-softmax），但增加了 int8/int4 反量化路径。

**SmoothQuant（Xiao et al., 2023）**—— 通过激活-权重迁移平滑 outlier。本文不涉及权重量化，但第二章综述中用来对比"激活 outlier 处理"的两种思路。

**KVTuner（Xu et al., 2025）Lemma 1**—— 证明 Key 量化误差在 attention score 中被放大 $\sqrt{d_k}$ 倍。本文的 GQA 噪声稀释论证（§4.6）直接引用该 Lemma 作为起点。

**Follow-up 追问**（随机抽）："SmoothQuant 的 migration strength $\alpha$ 是什么意思？本文为什么不用它？"
→ 答：$\alpha$ 是控制激活-权重平滑比例的超参数（0 = 不迁移，1 = 完全迁移）。Xiao 推荐 $\alpha=0.5$。本文不适用是因为 KV Cache 量化的"激活"是 Key/Value 张量本身（而非 activation），而对应的"权重"——Q 投影矩阵——不在 KV 量化路径上。SmoothQuant 解决的是 "weight × activation" 乘法中的 outlier 问题，而 KV Cache 量化解决的是 "存储 / 反量化" 中的量化误差问题，问题结构不同。

---

## 附：答辩紧急应对条

1. **若评委抓到 C1 数据不一致**：立即道歉 + 承诺 24h 修复 + 展示 git log 证明已提交 fix。不要辩解。
2. **若评委质疑贡献一是"经验观察"**：承认性质是观察，但强调"观察的独立性"（INT8 和 INT4 对不同 H_kv 的分化行为此前未被报道）。
3. **若评委质疑 KIVI 重合**：主动说"格式共享，诊断独立"——这比被追问再答更显从容。
4. **若评委质疑 14B 工作量**：直接说"14B 仅作为外部效度锚点，完整验证在 1.5B/7B/8B"，不绕弯。
5. **若自己答不出**：承认"这是一个我没有充分验证的方向"+"我会作为后续工作补充"。**千万不要编造**。

---

> 预演次数建议：本 Q10 每题独立口头预演 3 次 + 完整串讲 1 次，总耗时约 2 小时。
