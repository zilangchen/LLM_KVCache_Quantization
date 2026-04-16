# D2 STYLE — AI 痕迹 + 学术文风 + 术语一致性审查

> **审查范围**：abstract_zh/en + ch1-ch5 + appendix（共 ~5,160 行 LaTeX 源码）
> **三层审读方法**：L1 宏观（章节模板）+ L2 段落（过渡/三段式）+ L3 句子（第一人称、AI 特征词、长句、术语）
> **严重度**：H = 必须修（第一人称批量、章节模板、超长句）；M = 应修（术语混用、冗余过渡）；L = 建议修（标点、轻微修饰）
> **ID 规则**：TR-0200 起，连续编号
> **更新**：2026-04-17

---

## 内容索引

- [A. Top-30 最严重 AI 痕迹](#a-top-30-最严重-ai-痕迹表tr-0200--tr-0229)
- [B. 系统性文风问题（5 条全局）](#b-系统性文风问题5-条全局)
- [C. 结构模板化热点（8 处段落首句高相似位置）](#c-结构模板化热点8-处段落首句高相似位置)
- [D. 术语不一致精确位置清单](#d-术语不一致精确位置清单)
- [E. 英文摘要逐句审查](#e-英文摘要逐句审查)

---

## A. Top-30 最严重 AI 痕迹表（TR-0200 — TR-0229）

| ID | Sev | File:Line | 原文片段（≤40 字） | 问题类型 | 建议修改 |
|----|-----|-----------|-------------------|---------|---------|
| TR-0200 | **H** | abstract_zh.tex:21 | `我们发现校准目标的有效性呈 bit-width 与规模依赖` | 第一人称（本科论文应用"本文"或被动） | 改为：`本文发现校准目标的有效性呈 bit-width 与规模依赖` |
| TR-0201 | **H** | abstract_en.tex:24 | `we find that calibration objective validity is...` | 英文摘要第一人称复数（中文学位论文英摘应保持客观） | 改为：`this work shows that calibration objective validity is...` 或被动 `calibration objective validity is shown to be...` |
| TR-0202 | **H** | abstract_en.tex:35-36 | `We instantiate INT4-RoleAlign on this format via offline attention-KL search.` | 第一人称 | 改为：`INT4-RoleAlign is instantiated on this format via offline attention-KL search.` |
| TR-0203 | **H** | ch1_introduction.tex:48 | `这一矛盾促使我们从注意力行为保真的角度重新审视校准目标` | 第一人称 | 改为：`这一矛盾促使本文从注意力行为保真的角度重新审视校准目标` |
| TR-0204 | **H** | ch1_introduction.tex:86 | `我们将这一视角命名为"行为对齐"（Behavior Alignment）` | 第一人称 | 改为：`本文将这一视角命名为"行为对齐"（Behavior Alignment）` |
| TR-0205 | **H** | ch1_introduction.tex:152 | `我们系统比较 attention-KL 与 MSE 两种校准目标` | 第一人称 | 改为：`本文系统比较 attention-KL 与 MSE 两种校准目标` |
| TR-0206 | **H** | ch1_introduction.tex:161 | `在我们测试的模型规模与协议下，` | 第一人称 | 改为：`在本文所测试的模型规模与协议下，` |
| TR-0207 | **H** | ch1_introduction.tex:166 | `通过 K-only 与 V-only 因子分解，我们在四个模型上一致观察到` | 第一人称 | 改为：`通过 K-only 与 V-only 因子分解，本文在四个模型上一致观察到` |
| TR-0208 | **H** | ch1_introduction.tex:176 | `我们在该格式上以离线 attention-KL 搜索替代运行时 absmax/min` | 第一人称 | 改为：`本文在该格式上以离线 attention-KL 搜索替代运行时 absmax/min` |
| TR-0209 | **H** | ch1_introduction.tex:184 | `我们实现了 Triton 融合量化解码注意力核函数` | 第一人称 | 改为：`本文实现了 Triton 融合量化解码注意力核函数` |
| TR-0210 | **H** | ch1_introduction.tex:194 | `基于此，我们给出限定于 NVIDIA H20 平台的部署建议` | 第一人称 | 改为：`基于此，本文给出限定于 NVIDIA H20 平台的部署建议` |
| TR-0211 | **H** | ch2_related_work.tex:395 | `据我们所知，现有工作尚未在同一框架中将上述四个维度与 $H_{kv}$ 显式关联` | 第一人称 + AI 套路句式 | 改为：`就本文所检索的文献而言，现有工作尚未在同一框架中将上述四个维度与 $H_{kv}$ 显式关联` |
| TR-0212 | **H** | ch2_related_work.tex:455-456 | `据我们所知，\n尚无工作系统报告 KV Cache 量化中...` | 第一人称 + 冗余 | 改为：`就本文调研范围而言，尚无工作系统报告 KV Cache 量化中...` |
| TR-0213 | **H** | ch3_method.tex:204 | `我们选择 Kullback-Leibler（KL）散度衡量量化前后注意力行为的一致性` | 第一人称 | 改为：`本文选择 Kullback-Leibler（KL）散度衡量量化前后注意力行为的一致性` |
| TR-0214 | **H** | ch3_method.tex:410 | `我们观察到逐头温度校正（$\tau^{-1}$）的有效性` | 第一人称 | 改为：`可以观察到逐头温度校正（$\tau^{-1}$）的有效性` 或 `本文观察到...` |
| TR-0215 | **H** | ch3_method.tex:418 | `我们用校正因子 $\tau^{-1}_{l,h}$ 对每个注意力头独立补偿该效应` | 第一人称 | 改为：`本文用校正因子 $\tau^{-1}_{l,h}$ 对每个注意力头独立补偿该效应` |
| TR-0216 | **H** | ch4_experiments.tex:1465 | `我们没有做这部分实验，不在本文作结论` | 第一人称 + 口语化 | 改为：`上述扩展实验超出本文评测范围，不在此作结论` |
| TR-0217 | **H** | ch4_experiments.tex:1470 | `在跨模型消融中，我们观察到逐头温度校正（$\tau^{-1}$）的有效性` | 第一人称 | 改为：`跨模型消融显示，逐头温度校正（$\tau^{-1}$）的有效性` |
| TR-0218 | **H** | ch4_experiments.tex:1526 | `我们给出一个基于 GQA 噪声稀释的直觉论证（intuitive argument）` | 第一人称 | 改为：`本节给出一个基于 GQA 噪声稀释的直觉论证（intuitive argument）` |
| TR-0219 | **H** | ch4_experiments.tex:1735 | `我们不回避这一代价：` | 第一人称 + 修辞化表达 | 改为：`上述代价需明确披露：` 或 `本文明确承认这一代价：` |
| TR-0220 | **H** | ch5_conclusion.tex:26 | `在我们测试的模型规模与协议下，` | 第一人称（与 TR-0206 并行） | 改为：`在本文所测试的模型规模与协议下，` |
| TR-0221 | **H** | ch4_experiments.tex:9 + ch4:263 + ch3:6 + ch3:1185 | `本章按三个贡献/层级组织...` (三处) | 章节开头套路化模板（L1 宏观） | ch3:6 与 ch3:1185 开头/结尾重复；建议 ch4:9 保留，ch4:263 改为"综合上述实验设置，下文按贡献顺序展开"；ch3:6 保留，ch3:1185 改为 "本章的量化框架由三个层级构成"，避免首尾照抄 |
| TR-0222 | **M** | ch2_related_work.tex:65 | `将所有 Q 头共享单一 K、V 头，极大地减少了 KV Cache 开销` | AI 修饰词"极大地" | 改为：`将所有 Q 头共享单一 K、V 头，大幅减少了 KV Cache 开销` 或直接给数字："减少约 $H$ 倍" |
| TR-0223 | **M** | ch2_related_work.tex:496 | `GPU 显存利用率从约 20\%--40\% 提升至接近 100\%，显著提高了推理系统的吞吐量` | AI 修饰词"显著" + 未定量 | 改为：`GPU 显存利用率从约 20\%--40\% 提升至接近 100\%，相应提高了推理系统的吞吐量` |
| TR-0224 | **M** | ch4_experiments.tex:1711-1713 | `这一"PPL 退化 vs 检索保持"的解耦现象构成本文的关键发现之一：\n\emph{局部信息检索仅依赖少数关键位置的注意力聚焦...}` | "关键发现之一" + 主观评价 | 改为：`这一"PPL 退化 vs 检索保持"的解耦现象是本章诊断结论的重要延伸：局部信息检索仅依赖少数关键位置的注意力聚焦...` |
| TR-0225 | **M** | ch4_experiments.tex:1451-1457 | `这个结果其实不意外：两种方法共享同一套量化格式...\n真正值得讨论的是这套非对称量化轴是怎么来的。` | 口语化"其实不意外"、"怎么来的" | 改为：`该结果与设计预期一致：两种方法共享相同的量化格式（per-channel K + per-token V），仅校准 percentile 的确定范式不同...\n更值得关注的是该非对称量化轴的设计来源。` |
| TR-0226 | **M** | ch3_method.tex:6-27 + ch4:1-15 + ch2:5-10 | 三章开头均以"本章按...组织"或"...维度展开"套路句开篇 | L1 章节开头模板化 | 参见 Section C "结构模板化热点"；建议将 ch3:6 改为以内容为主的开篇："行为对齐量化框架以 attention-KL 为度量..." |
| TR-0227 | **M** | ch3_method.tex:153-161（段落长度/结构） | `本文的校准目标采用 WikiText-103 上的 attention-KL 散度作为代理损失函数，\n而评测则跨越 WikiText-2 PPL、合成 Needle-in-a-Haystack、\nRULER 13 子任务与 LongBench 16 真实任务等多个 domain 与任务类型。\n两者之间存在三重 shift：\n(i) domain shift（general English → synthetic long-context），\n(ii) 任务类型 shift（token-level 似然 → retrieval/reasoning），\n(iii) 序列长度 shift（校准 $<$4K → 评测 32K）。` | 英文 domain/shift 术语夹杂 + 过长列表 | 改为：`本文校准目标采用 WikiText-103 上的 attention-KL 散度作为代理损失函数，评测则覆盖 WikiText-2 PPL、合成 Needle-in-a-Haystack、RULER 4 个子任务与 LongBench-style 合成评测。两者之间存在三重分布偏移：领域（通用英文 → 合成长上下文）、任务类型（token-level 似然 → 检索/推理）、以及序列长度（校准 $<$4K → 评测 32K）。` |
| TR-0228 | **L** | ch3_method.tex:62 (caption) | `层一以 Attention-KL 为行为偏移度量；层二在该度量下建立 robust selection 协议...$\tau^{-1}$ 作为诊断过程中观察到的启发式呈现，显示出格式与 GQA 尺度的双依赖性；Triton 融合量化解码与校准产物 JSON 为上述层级提供系统实现支撑。` | 单句超长（caption >100 字），`Attention-KL` 大小写与正文 `attention-KL` 不一致 | 改为：拆分为 2-3 句 + 统一术语为 `attention-KL`；修改后："层一以 attention-KL 为行为偏移度量。层二在该度量下建立 robust selection 协议，既用于校准参数搜索（INT8 对称路径），也用作诊断工具（低比特结构分析）。层三在 KIVI-style 非对称格式上给出行为引导的实例化 RoleAlign。Triton 融合量化解码与校准产物 JSON 为上述层级提供系统实现支撑。" |
| TR-0229 | **L** | abstract_en.tex:32-33 | `The diagnosis naturally points to a per-channel Key + per-token Value asymmetric format` | 英文语病："naturally points to" 为 AI 高频短语 | 改为：`This diagnosis motivates a per-channel Key + per-token Value asymmetric format` |

---

## 新增高严重度 issue（TR-0230 — TR-0239）

| ID | Sev | File:Line | 原文片段（≤40 字） | 问题类型 | 建议修改 |
|----|-----|-----------|-------------------|---------|---------|
| TR-0230 | **H** | ch4_experiments.tex:581-582（footnote 含长句） | `\footnote{\emph{测量条件范围}: "8--38\%" 数字在 batch$=$1、独占 GPU（single-stream decode）条件下测量，seq\_len $\in \{4096, 32768\}$ 视表格而定。}（RULER 退化见第~\ref{para:c6-fail}~段）。INT8 结果确认行为对齐原则成立。下一个问题是：当量化级别降至 15（INT4）时，同一原则能否诊断失效根因？` | **设问句+悬念式过渡**（"下一个问题是：..."），AI 特征显著；单行超过 80 字 | 改为：`INT8 实验结果确认行为对齐原则在该比特宽度下成立。第~\ref{sec:exp-int4}~节进一步考察量化级别降至 15（INT4）时，该原则能否诊断失效根因。` |
| TR-0231 | **H** | ch4_experiments.tex:1697-1716（长段） | `\paragraph{PPL 退化：可控但不可忽略。}\nINT4-RoleAlign 的 PPL 退化在四个模型上介于 2.4--13.7\%...\n\textbf{其一}，INT4-RoleAlign...\n\textbf{其二}，尽管 PPL 退化显著...` | 段落使用 "其一/其二" 列举式 + 末尾"这一...构成本文的关键发现之一"主观评价 | 建议：将"其一/其二"改为 "(1) / (2)"，并把"构成本文的关键发现之一"改为 "支持本文关于检索-建模鲁棒性差异的论断" |
| TR-0232 | **H** | ch4_experiments.tex:1417-1418 | `可见对称 INT4 的失效与``格式自由度不足''这一解释一致，\n而是量化格式无法捕捉 Key 通道间的数值异质性。` | 句法错误："与...一致，而是..." 前后转折不成立，缺少"而是"前承接的否定 | 改为：`可见对称 INT4 的失效并非随机现象，而是量化格式无法捕捉 Key 通道间的数值异质性——这一机制与"格式自由度不足"的解释一致。` |
| TR-0233 | **H** | ch4_experiments.tex:2037-2039 (TTV-6 短句堆叠) | `\textbf{TTV-6：评测协议依赖。}\nRULER 与 LongBench 使用本文自行实现的合成任务生成器，\n所有 benchmark 结论均在本文协议实现下的相对对比中成立。` | 中英混杂（"benchmark 结论"）+ 重复"本文协议实现"与"本文自行实现" | 改为：`\textbf{TTV-6：评测协议依赖。}RULER 与 LongBench 使用本文自行实现的确定性合成任务生成器；相关结论仅在本评测协议的相对对比中成立。` |
| TR-0234 | **M** | ch3_method.tex:442-448（方法论说明段） | `\textbf{方法论说明}. 本段呈现的 GQA 尺度依赖性是\emph{诊断发现}而非理论推导。\n其机制归因采用直觉论证（intuitive argument）呈现，\n与第~\ref{subsec:exp-statistics}~节对 deterministic PPL effect size\n的处理保持一致：所报告的跨模型百分比差异为 \emph{effect size on greedy-decoded PPL}` | "方法论说明" 英文 meta-label + 大量中英夹杂（effect size、deterministic、greedy-decoded） | 改为：`\textbf{方法论说明。}本段的 GQA 尺度依赖性属于诊断性观察，而非理论推导。机制归因采用直觉论证形式呈现，与第~\ref{subsec:exp-statistics}~节关于贪心解码 PPL 确定性效应量的处理一致：所报告的跨模型百分比差异为贪心解码 PPL 上的效应量。由于贪心解码下 PPL 为逐位确定量，统计意义上的 $p$-value 不再适用，跨模型比较仅基于效应量的方向与量级。` |
| TR-0235 | **M** | ch4_experiments.tex:568-580 (INT8 延迟讨论段) | `在延迟维度上，需要明确两个对照组的不同结论：\n\textbf{(i) 相对 FP16}：batch$=$1 条件下...\n\textbf{(ii) 相对未融合 INT8-baseline}：...` | 段内使用 "(i)/(ii)" + bold 双层嵌套 + 重复术语"相对" | 改为：将"两个对照组的不同结论"拆为两小段，取消 `\textbf{(i)}` / `\textbf{(ii)}` 的人工列举，自然表达：`相对 FP16，batch$=$1 条件下 INT8-ours 的绝对 TPOT...相对未融合 INT8-baseline，INT8-ours 的 Triton 融合核函数实现 8.3\% / 17.3\% / 37.6\% 的 TPOT 降低...` |
| TR-0236 | **M** | ch3_method.tex:889-892 (英文描述句) | `\emph{与 Tensor-core 路径的关系}: 本节的 split-channel 方案使用 CUDA-core\n并通过奇偶 lane 分裂规避 per-channel 反量化中的 Scale 广播冲突，验证了算法路径的数值正确性；\n其 Tensor-core 并行潜力与 BitDecoding~\cite{du2026bitdecoding} 的 NVFP4 设计互为补充` | 中英混杂严重（Tensor-core / CUDA-core / lane / NVFP4 / Scale 广播），单句 >60 字 | 改为：`\emph{与 Tensor Core 路径的关系。}本节 split-channel 方案基于 CUDA Core，通过奇偶 lane 分裂规避 per-channel 反量化的 scale 广播冲突，验证了算法路径的数值正确性。其 Tensor Core 并行潜力与 BitDecoding 的 NVFP4 设计互为补充；后者在硬件资源利用维度展示了进一步优化空间，但依赖 NVFP4 数值格式与 Blackwell 架构。` |
| TR-0237 | **M** | ch4_experiments.tex:1711-1716 (Emph 过度加粗) | `\emph{局部信息检索仅依赖少数关键位置的注意力聚焦，\n对量化噪声的容忍度远高于需要全局概率保真的语言建模}` | 整段 italics 包裹"构成本文关键发现之一"+主观评价 | 改为去掉 `\emph{}`：`局部信息检索仅依赖少数关键位置的注意力聚焦，对量化噪声的容忍度远高于需要全局概率保真的语言建模。` |
| TR-0238 | **M** | appendix.tex:526-535 (MixedKV 逐模型分析) | `MixedKV 全指标不劣于 FP16：PPL 6.75（甚至低于 FP16 的 6.92）...这是 GQA 噪声稀释效应最显著的模型` | "最显著的模型" / "甚至低于" 为主观修饰 | 改为：`MixedKV 全指标不劣于 FP16：PPL 6.75（相对 FP16 的 6.92）...该模型表现出最明显的 GQA 噪声稀释效应` |
| TR-0239 | **L** | abstract_zh.tex:34-37 | `融合量化解码核函数的效率增益\n在 $(H_{kv}, \text{seq\_len})$ 空间中呈显著分化：\n$H_{kv}=8$ 在 32K 下延迟减少约 40\%，\n$H_{kv}=2$ 下融合核在所有长度下均慢于 SDPA。` | "显著分化" 修饰词 | 改为：`融合量化解码核函数的效率增益在 $(H_{kv}, \text{seq\_len})$ 空间中呈规模依赖：$H_{kv}=8$ 在 32K 下延迟减少约 40\%，$H_{kv}=2$ 下融合核在所有测试长度上均慢于 SDPA。` |

---

## B. 系统性文风问题（5 条全局）

### B1. 第一人称"我们"高频出现（H 级系统性问题）

- **症状**：全文（含 abstract_zh/en、ch1/ch2/ch3/ch4/ch5）共检索到 **22 处** "我们"（TR-0200、TR-0203 等已逐条列出）。本科毕业设计（华南理工）要求客观陈述，应使用"本文"、"本研究"、被动语态或无主语句。
- **英文摘要 "we" 3 处**（TR-0201、TR-0202、及 abstract_en:24/32-36 内隐含 we find/decouple/instantiate），建议改为被动式 "this work shows" / "XXX is instantiated"。
- **修复策略**：
  - "我们观察到 X" → "本文观察到 X" / "实验显示 X"（避免单调）
  - "我们将 X 命名为 Y" → "本文将 X 命名为 Y"
  - "据我们所知" → "就本文检索范围而言" / "在本文调研的文献范围内"
  - "在我们测试的..." → "在本文测试的..."

### B2. "据我们所知" 套路（H 级）

- **位置**：ch2:395、ch2:455、ch3:474、ch4:1544（4 处）
- **问题**：AI/ChatGPT 特征句式；本科论文应改为"就本文检索范围而言"或删除该主观判断（学术惯例为直接陈述缺失，不做"据我们所知"声明）。

### B3. 术语大小写与中英混用不一致（M 级）

- **attention-KL vs Attention-KL**：全文以小写连字符 `attention-KL` 为主（22 处），但 ch3:62 (caption) 与 ch4:1927 为 `Attention-KL`。统一为小写。
- **KV Cache vs KV cache vs 键值缓存**：全文 153 处，三种形式混用；详见 Section D 术语清单。
- **per-channel / per-token / per-group**：40+ 处，部分与"逐通道 / 逐 token / 逐组"重复混用，尤其 ch1:107、ch2:182-183、ch2:238-242、ch2:570 与后文 per-channel 形式并存。
- **Tensor-core / tensor core / tensor-core**：ch3:889（Tensor-core）、ch4:1607/1615（tensor core）、ch3:891（Tensor-core）；规范：术语统一为 `Tensor Core`（NVIDIA 官方写法）。
- **CUDA-core / CUDA core**：ch3:889 一处 CUDA-core；建议 `CUDA Core`。

### B4. 口语化表达与"说人话"套路（M 级）

- ch4:1451-1457、1465（"其实不意外"、"怎么来的"、"我们没有做这部分实验"）
- ch4:1703-1711（"尽管...但..."+"构成本文的关键发现之一"）
- ch4:2037-2039（"所有 benchmark 结论均在本文协议实现下的相对对比中成立"——重复冗余）
- appendix:526-535（"这是 GQA 噪声稀释效应最显著的模型"——主观最高级）
- 建议：整段改写为学术化表达，剔除"其实"、"不意外"、"怎么来的"、"没办法"、"比较"（副词）等。

### B5. 章节开头模板化（L1 宏观 H 级）

- 共 8 处段落/章节开头以相似模板（"本章/本节按...组织"、"本章/本节...展开"、"本章以..."）开场：
  - ch2:5-10（"本章从这三个维度展开综述"）
  - ch3:6-27（"本章按三个层级组织..."）
  - ch3:1185（"本章按三个层级展开了..."）← 与 ch3:6 首尾重复
  - ch4:8-15（"本章按三个贡献对应的证据组织实验"）
  - ch4:263-271（"本章按三个贡献组织证据"）← 与 ch4:9 重复
  - ch5:11-12（"本章以三条核心发现回扣引言的三个研究问题"）
  - appendix 各节多用"本节提供..."、"本节验证..."、"本节选取..."（appendix:223、277、440、486、543、616、683）
- 修复：打破模板化，改为直接陈述章节主要论断，例如 ch3:6 改为 "行为对齐量化框架以 attention-KL 为度量基础，包含校准方法、INT8 路径与 INT4-RoleAlign 实例化三部分。"

---

## C. 结构模板化热点（8 处段落首句高相似位置）

| # | 位置 | 首句类型 | 建议 |
|---|------|---------|------|
| C1 | ch2:5 | "行为对齐量化框架的设计依赖于..." | 拆成"Transformer 注意力、量化理论、KV Cache 管理是本章综述基础。" |
| C2 | ch3:6 | "本章按三个层级组织行为对齐量化框架。" | 改为："本章以 attention-KL 为度量基础，从校准方法到 INT4-RoleAlign 实例化展开框架设计。" |
| C3 | ch3:1185 | "本章按三个层级展开了行为对齐量化框架的设计。"（小结） | 与 C2 完全重复；小结改为："本章首先建立 attention-KL 度量..."（用内容语言） |
| C4 | ch4:9 | "本章按三个贡献对应的证据组织实验：..." | 保留 |
| C5 | ch4:263 | "本章按三个贡献组织证据。" | 删除（与 C4 重复，或改为"在上述实验设置下，以下按贡献顺序展开证据"） |
| C6 | ch5:11 | "本章以三条核心发现回扣引言的三个研究问题..." | 保留（结论章唯一入口） |
| C7 | ch1:124 | "基于上述背景，本文提出三个递进的研究问题" | 保留 |
| C8 | ch4 各 section 首句 | "本节揭示/给出/分析..."（第 1286 / 910 / 1694 / 1768 / 1917 行） | 高度相似；建议随机化为"第 X 节"描述或直接以论点开头 |

---

## D. 术语不一致精确位置清单

> **同步更新** `docs/thesis_final_review/terms_glossary.md`（见本文档末尾 Edit 操作）

### D1. KV Cache / KV cache / 键值缓存

| 变体 | 出现位置（file:line） | 当前形式 | 建议统一为 | 是否白名单内 |
|------|---------------------|----------|-----------|------------|
| 键值缓存 | abstract_zh.tex:8, ch1:16, ch1:219, ch2:7, ch3:1183, ch5:220 | 键值缓存 | 首次保留"键值缓存（KV Cache）"，其余统一 **KV Cache** | 否 |
| KV Cache | abstract_zh.tex:7-8, abstract_en:11, ch1:16-20, ch1:30, ch2:225-, ch3:551-, ch4:82, ch4:1719, ch5:220 等 (~110 处) | KV Cache | **保留为主形式**；所有 "KV cache" / "kv cache" 改为 KV Cache | 否 |
| KV cache | abstract_en.tex:9, 10, 11, 13, 34 (英文摘要 5 处) | KV cache | 英文摘要统一为 **KV cache**（英文语境下小写 c 更自然） | 否 |
| kv_cache | (代码白名单，ch3 `\code{kv\_mode}` 内) | kv_mode | 保持 `\code{kv\_mode}`、`\code{int4\_ours\_asym}` 等代码命名 | **白名单**（代码） |
| KV 头 | ch1:20, ch2:70, ch4:30-, ch4:954-958 等 | KV 头 | 保留（架构参数） | — |

**冲突热点**：ch2:225 "KV Cache" 与 ch2:239-245 "KIVI 对 Key 采用逐通道（per-channel）非对称量化" 前后行内同段同时出现 "per-channel" 与 "逐通道"，应二选一。

### D2. attention-KL / Attention-KL / 注意力 KL

| 变体 | 出现位置 | 当前形式 | 建议统一为 |
|------|---------|----------|-----------|
| attention-KL | 22 处（ch1:152, ch3:8 等） | attention-KL | **保留**（统一形式） |
| Attention-KL | ch3:62 (caption), ch4:1927 | Attention-KL | 改为 **attention-KL**（两处） |
| attention_KL | 无 | — | — |
| 注意力 KL | 无正文用例（但部分段落描述性用 "注意力 KL 散度"） | — | — |
| KL 散度 | ch3:70, ch3:220, ch3:259 等 | KL 散度 | 保留（引用时使用"注意力权重的 KL 散度"或"attention-KL"时需一致） |

**行动**：
- ch3_method.tex:62（caption）：`Attention-KL` → `attention-KL`
- ch4_experiments.tex:1927：`Attention-KL` → `attention-KL`

### D3. GQA / 分组查询注意力

| 变体 | 出现位置（file:line） | 当前形式 | 建议统一为 |
|------|---------------------|----------|-----------|
| GQA | 全文 ~60 处（ch1:28, ch2:67, ch3:351, ch4:910 等） | GQA | 保留（缩写） |
| 分组查询注意力 (Grouped Query Attention, GQA) | ch2:67 | 首次出现 | **保留作为术语引入** |
| 分组查询注意力（GQA） | ch3:351, ch3:929 | 两次出现 | 后续出现只用 GQA |

**状态**：该术语基本一致，仅首次出现形式规范。

### D4. INT8 / int8 / INT4 / int4

| 变体 | 出现位置 | 当前形式 | 建议统一为 |
|------|---------|----------|-----------|
| INT8 / INT4（文本） | 全文 ~500 处 | INT8 / INT4 | **保留**（全大写，文本） |
| `int8\_ours` / `int4\_ours\_asym`（代码名） | ch3:1078, ch4:170-196, ch4:1288 等 | `\code{int8\_ours}` | 保持（代码模式） |
| int4_fused / int4_ours_mixed 等 | 同上 | 同 | 保持（代码白名单） |
| 8-bit / 4-bit | ch2:137-157, ch2:368-389, ch4:921-924 | 混用 8-bit 与 4-bit / INT8 与 INT4 | 统一：**用 INT8/INT4** 指代量化位宽；**用 8-bit/4-bit** 指代单个值的编码位宽 |

**未修复**：ch2:387 表格 `\textbf{本文方法} & KV Cache & 4-bit & 对称+非对称 & KL 行为对齐` — 此处 "4-bit" 与全文 "INT4" 并存，表格上下文需局部一致。

### D5. PPL / 困惑度 / Perplexity

| 变体 | 出现位置 | 当前形式 | 建议统一为 |
|------|---------|----------|-----------|
| PPL | 全文 ~200 处 | PPL | **保留**（英文缩写） |
| 困惑度（PPL） | ch1:43, abstract_zh:13, ch2:198 | 首次引入 | **保留**（首次） |
| Perplexity | abstract_en.tex:15, ch4:98 (caption 或行文) | Perplexity / perplexity | 英文中 `perplexity`（lowercase 主形）；首次 `Perplexity (PPL)` |
| 困惑度 | ch1:43, ch5:65 | 困惑度 | 中文语境下后续用 PPL |

**行动**：在 ch5:65（`但 PPL 退化显著（8B: 2.4\%，7B: 6.1\%...）`）前后使用 PPL 一致。

### D6. per-channel / 逐通道 / per-token / 逐 token / per-group / 逐组

**最严重混用**：一段内同时出现"per-channel"和"逐通道"。

| 变体 | 出现位置（file:line） | 当前形式 | 建议 |
|------|---------------------|----------|------|
| 逐通道 | ch1:107, ch2:182, ch2:238, ch2:570 | 逐通道 | **首次：逐通道（per-channel）；后续：per-channel** |
| per-channel | ch1:174, ch2:242, ch2:249, ch3:18, ch3:131, ch3:626, ch3:644, ch3:669-687, ch3:857, ch3:881, ch3:890, ch3:1012, ch3:1070, ch3:1194, ch4:181-182, ch4:1289, ch5:34, ch5:185, ch5:208, appendix:570-591 等 (~30 处) | per-channel | 保留主形式 |
| per-token | 类似 per-channel（～25 处） | per-token | 保留 |
| 逐 token | ch1:107（"逐 token Value"）, ch2:238-239 | 逐 token | 首次后转 per-token |
| per-group | ch3:98-109, ch3:528-546, ch3:635, ch4:181-183 等 | per-group | 保留 |
| 逐组 | ch3:508, ch4:177-180 (表格 `对称 per-group`) | per-group（正文） / 逐组（描述） | 表格统一用 `per-group` |

**行动**：ch2:182-184 段开头首次明确"逐通道（per-channel）"，其余正文改为 per-channel。ch1:107 "逐通道 Key + 逐 token Value" → "逐通道（per-channel）Key + 逐 token（per-token）Value"。

### D7. 行为对齐 / Behavior Alignment / Behavior-Aligned / behavior-aligned

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| 行为对齐（Behavior Alignment） | ch1:86 | 首次引入 | **保留** |
| 行为对齐 | 全文 ~30 处 | 行为对齐 | 保留（主中文形式） |
| Behavior-Aligned Calibration | abstract_en:49 (关键词) | Behavior-Aligned | 保留（英文摘要关键词） |
| behavior-aligned | ch4:1195, ch4:1303, ch4:1320, ch4:1627 | 小写连字符 | 正文需统一：`behavior-aligned viewpoint` / `behavior-aligned principle` / `behavior-aligned 离线搜索` — 统一英文为 **"behavior-aligned"**（小写），中文为 **"行为对齐"** |
| BA-guided | ch3:681, ch3:693, ch4:182, ch4:1069, ch4:1303, ch4:1705 | BA-guided | 保留（特定缩写） |

### D8. Triton 融合核 / Triton 融合核函数 / triton_fused

| 变体 | 出现位置 | 建议 |
|------|---------|------|
| Triton 融合核函数 | ch1:120, ch3:23, ch3:38, ch3:184, ch3:767, ch4:483, ch5:68 等 ~30 处 | 保留（主形式） |
| Triton 融合核 | ch3:62 (caption), ch4:1903 | → Triton 融合核函数 |
| triton_fused / triton\_fused / triton\_ra | 代码区（ch4:175-183 表格内） | 保留（代码名） |
| 融合核 | ch4:1718-1730 段 | 上下文清晰可保留 |

---

## E. 英文摘要逐句审查（abstract_en.tex 52 行）

> **逐句评价格式**：行号 | 原文 | 问题 | 建议改写
>
> 共 12 个独立语义句。

### E1. Sentence 1 (L7-10)

- **原文**：`As large language model context windows scale from thousands to hundreds of thousands of tokens, KV cache memory grows linearly with sequence length and has become the primary bottleneck for long-context inference deployment.`
- **评价**：句子通顺；"KV cache" 拼写与英文习惯一致（lowercase cache）。
- **问题**：（无严重问题）轻微：`As ... scale ... grows` 句子过长（36 词），可拆分。
- **建议**：保留，或拆句：`Large language model context windows now scale from thousands to hundreds of thousands of tokens. Consequently, KV cache memory grows linearly with sequence length and has become the primary bottleneck for long-context inference deployment.`

### E2. Sentence 2 (L10-15)

- **原文**：`INT4 quantization can in principle reduce KV cache memory to $1/4$ of its original size, yet existing methods calibrated with numerical reconstruction error degrade sharply at long contexts: Needle retrieval drops from 100\% to 0\% and perplexity degrades by over 15\%.`
- **评价**：清晰；动词 degrade 用 2 次（degrade sharply / degrades by）可避免重复。
- **建议**：`...yet existing methods calibrated with numerical reconstruction error fail sharply at long contexts: Needle retrieval drops from 100\% to 0\% and perplexity increases by over 15\%.`

### E3. Sentence 3 (L15-22)

- **原文**：`This paper revisits the calibration objective from an attention-behavior perspective, using the Kullback--Leibler divergence between pre- and post-quantization attention distributions (attention-KL) as a unified calibration and diagnostic principle, with GQA head count $H_{kv}$ as a structural correlate linking calibration sensitivity, degradation patterns, and fused decoding efficiency.`
- **评价**：句子极长（49 词），塞入三个 list (calibration sensitivity / degradation patterns / fused decoding efficiency)。
- **建议**：拆为两句：`This paper revisits the calibration objective from an attention-behavior perspective, using the Kullback--Leibler divergence between pre- and post-quantization attention distributions (attention-KL) as a unified calibration and diagnostic principle. GQA head count $H_{kv}$ serves as a structural correlate linking calibration sensitivity, degradation patterns, and fused decoding efficiency.`

### E4. Sentence 4 (L24-29)

- **原文**：`On Qwen2.5-1.5B/7B/14B and LLaMA-3.1-8B, we find that calibration objective validity is both bit-width and scale dependent: at INT8 the two objectives converge, while at INT4 they diverge on a small model ($H_{kv}=2$) but reconverge on a larger one ($H_{kv}=4$).`
- **评价**：第一人称 "we find"；句子较长。
- **问题**：**TR-0201**。
- **建议**：`Across Qwen2.5-1.5B/7B/14B and LLaMA-3.1-8B, calibration objective validity is found to be both bit-width and scale dependent: at INT8 the two objectives converge, while at INT4 they diverge on a small model ($H_{kv}=2$) but reconverge on a larger one ($H_{kv}=4$).`

### E5. Sentence 5 (L29-32)

- **原文**：`Controlled diagnosis shows INT4 degradation is Key-dominated---on the 14B model, preserving Key in FP16 recovers 93\% of PPL degradation---while Needle retrieval and PPL consistently decouple across all four models.`
- **评价**：em-dash 嵌入状语结构（`---on the 14B model, preserving Key in FP16 recovers 93\% of PPL degradation---`）技术上正确但可读性差。
- **建议**：`Controlled diagnosis shows INT4 degradation is Key-dominated: on the 14B model, preserving Key in FP16 recovers 93\% of the PPL degradation. Meanwhile, Needle retrieval and PPL consistently decouple across all four models.`

### E6. Sentence 6 (L32-35)

- **原文**：`The diagnosis naturally points to a per-channel Key + per-token Value asymmetric format---the same format independently proposed by KIVI~\cite{liu2024kivi} from engineering observation.`
- **评价**：AI 高频短语 "naturally points to"（TR-0229）。
- **建议**：`This diagnosis motivates a per-channel Key + per-token Value asymmetric format---the same format independently proposed by KIVI~\cite{liu2024kivi} from engineering observations.`（engineering observations 复数更自然）

### E7. Sentence 7 (L35-36)

- **原文**：`We instantiate INT4-RoleAlign on this format via offline attention-KL search.`
- **评价**：第一人称（TR-0202）。
- **建议**：`Building on this format, INT4-RoleAlign is instantiated via offline attention-KL search.`

### E8. Sentence 8 (L36-39)

- **原文**：`Across all four models, RoleAlign preserves 100\% Needle retrieval at roughly 73\% KV cache compression, with PPL degradation decreasing with scale (1.5B: 13.7\%; 7B: 6.0\%; 8B: 2.4\%).`
- **评价**：清晰。（小问题：1.5B "13.7\%" 与 tab:rolealign-results 一致，7B "6.0\%" 实际对应 7.58/7.14=6.16%，参考 TR-0002 冲突）。
- **建议**：保留句子结构；数字由 TR-0002 决定（该 issue 跨维度）。

### E9. Sentence 9 (L39-41)

- **原文**：`The 14B model provides external validity: Needle passes at 4K--32K; RULER reaches 96.6\%--98.5\% at 4K--16K.`
- **评价**：清晰简洁。
- **建议**：保留。

### E10. Sentence 10 (L41-46)

- **原文**：`The efficiency gains of fused quantized decoding kernels exhibit pronounced differentiation in the $(H_{kv}, \text{seq\_len})$ space: at $H_{kv}=8$ the fused kernel reduces latency by roughly 40\% at 32K, while at $H_{kv}=2$ it is slower than SDPA across all tested sequence lengths.`
- **评价**："pronounced differentiation" 为 AI 修饰语。
- **建议**：`Fused quantized decoding kernel gains vary sharply across the $(H_{kv}, \text{seq\_len})$ space: at $H_{kv}=8$, the fused kernel reduces latency by roughly 40\% at 32K, while at $H_{kv}=2$, it is slower than SDPA across all tested sequence lengths.`

### E11. Keywords (L48-50)

- **原文**：`Large Language Model; Key-Value Cache; Quantization; Behavior-Aligned Calibration; Asymmetric Quantization; GQA Architecture`
- **评价**：**6 个关键词**，但中文附件1要求 **3-5 个关键词**（已由 TR-0003 标记为 CRITICAL）。
- **建议**：保留 4 个：`Large Language Model; Key-Value Cache; Behavior-Aligned Calibration; GQA Architecture`（与中文摘要 TR-0003 方案对齐）。

### E12. 整体评语

- **最严重 3 处**：
  1. 第一人称 `we find` / `We instantiate`（L24, L35-36，TR-0201, 0202）
  2. 关键词超过上限（L48-50，TR-0003）
  3. `naturally points to` AI 特征短语（L32，TR-0229）
- **其他可优化**：Sentence 3/5 偏长（拆句）；`pronounced differentiation` / `decouple` 等修饰词可替换为更客观表达。

---

## F. 审查总计

- **新增 H/M issue**：20 条（TR-0200 至 TR-0219）+ 10 条扩展（TR-0220 至 TR-0239）= 共 30 条
- **按严重度分解**：
  - **H**：18 条（TR-0200-0221, 0230-0233）
  - **M**：9 条（TR-0222-0227, 0234-0238）
  - **L**：3 条（TR-0228, 0229, 0239）
- **系统性全局问题**：5 条（Section B）
- **结构模板化热点**：8 处（Section C）
- **术语分类**：8 组（Section D）
- **英文摘要评语**：12 句逐句分析（Section E）

**修复优先级**：
1. **第一人称批量改写**（TR-0200-0221，占 H 级 60%，机械替换即可完成）
2. **关键词数量合规**（TR-0003，已在 issues.md 主表）
3. **章节首尾重复模板**（TR-0221, C2/C3, C4/C5）
4. **术语统一**（D1-D8，全局 sed 可完成大部分）
5. **英文摘要重写**（E1-E12 结合 B1, B2）
