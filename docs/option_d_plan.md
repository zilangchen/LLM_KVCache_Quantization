# Option D'' 实施计划：论文叙事重构（最终定稿版）

## 一、论文身份

> **本文研究 GQA 架构下的 behavior-aligned KV cache quantization。**
> Attention-KL 是统一的校准与诊断原则，$H_{kv}$ 是解释低比特失效模式、
> 温度校正分化和融合解码效率 crossover 的关键结构变量。
> INT8 提供 canonical validation，INT4-RoleAlign 是 low-bit instantiation，
> 14B 与 BitDecoding 结果用于外部效度与边界分析。

---

## 二、Research Questions

位置：`ch1_introduction.tex` L125-145

```latex
\begin{description}
  \item[\textbf{RQ1}] \emph{KV Cache 量化应优化什么目标？其有效性是否随模型规模变化？}
  \item[\textbf{RQ2}] \emph{低比特量化为何失效？失效模式是否呈 GQA 架构依赖？}
  \item[\textbf{RQ3}] \emph{诊断结论能否导出有效的低比特设计？}
  \item[\textbf{RQ4（新增）}] \emph{INT4 融合解码核的效率是否存在架构依赖的 crossover？}
\end{description}
```

RQ1-RQ3 保持原有核心，微调措辞。RQ4 新增，对应 Phase Boundary。

---

## 三、Contributions（5 条）

位置：`ch1_introduction.tex` L147-206，重写。

### C1: 校准目标有效性的 bit-width 与规模依赖

在 INT8 下 KL 和 MSE 趋同；在 INT4 下 1.5B ($H_{kv}=2$) 上 KL 和 MSE 选出不同 percentile（99.5 vs 99.0，scale 差异 12.35%），而 7B ($H_{kv}=4$) 上两者趋同到相同参数（100.0/99.9）。

结论句：
> 在我们测试的模型规模与协议下，KL 至少不劣于 MSE，并在小模型 INT4 设置下表现更优。

数据来源：1.5B 历史数据 + C1 补实验 7B KL=MSE PPL=7.1121

### C2: Key 主导退化与 GQA 架构依赖

四个模型一致观察到 INT4 退化由 Key 侧主导。14B K/V ablation：K 保持 FP16 恢复 93% PPL 退化（5.04→4.71），V 保持 FP16 仅恢复 64%。Needle 与 PPL 的解耦跨 1.5B-14B 一致。

数据来源：14B ppl_ablation_K16V4=4.709, K4V16=4.813

### C3: RoleAlign 跨模型规模验证

在 4 个模型上 INT4-RoleAlign 保持 Needle 100%，KV 压缩 ~73%，PPL 退化随规模减弱（1.5B: 13.7%, 7B: 6.0%, 8B: 2.4%, 14B: 7.6%）。14B Needle 在 4K-32K 全通过；RULER 在 4K-16K 达到 96.6%-98.5%（32K 因显存限制未测）。1.5B 上 INT4 与 FP16 的 RULER 差距不足 1%。

数据来源：Stage 5 14B 全套 + 1.5B fp16 RULER baseline

### C4: $(H_{kv}, \text{seq\_len})$ Phase Boundary 与部署建议

Triton 融合核与 naive dequant+SDPA 在 $(H_{kv}, \text{seq\_len})$ 空间中存在 phase boundary：$H_{kv}=2$ 时融合核始终慢于 SDPA，$H_{kv}=4$ 时在 ~32K 处 crossover，$H_{kv}=8$ 时在 4K-8K 处即反超。部署建议：$H_{kv}\geq 4$ 且 seq>8K 使用融合核；$H_{kv}=2$ 使用 SDPA。

不放入 C4 的内容（各归原位）：
- inv_tau × GQA 尺度依赖 → 保留为实验发现（Ch4 消融 section）
- in-kernel percentile → Ch3 方法实现支撑

数据来源：Stage 7 rerun + 8B 长序列补跑

### C5: 大模型外部验证与质量保持

14B 模型在 32K Needle 100%、16K RULER 96.6% 证明 RoleAlign 在大模型上质量良好。1.5B FP16 RULER baseline (55%) 与 INT4 FI (56%) 差距 <1%，证明低分数是模型能力上限而非量化退化。

BitDecoding (HPCA 2026) → 降级为 Discussion/Limitations 中的 ~1 页 engineering case study，不作为主 finding。

---

## 四、核心主张

位置：`ch1_introduction.tex` L198-206

> 本文的核心主张是：attention-KL 提供了 GQA 架构下 KV cache quantization 的统一校准与诊断原则，而 $H_{kv}$ 是解释低比特失效模式、温度校正分化和融合解码效率 crossover 的关键结构变量。在当前模型集合中，$H_{kv}$ 与模型规模部分共变，因此相关结论应理解为结构性证据而非严格受控因果识别。

---

## 五、Ch2 Related Work

位置：`ch2_related_work.tex`

### 结构重组（3 条线）

1. **KV quantization / calibration**: KIVI, KVQuant, QuIP, GEAR 等
2. **K/V asymmetry / low-bit rescue**: per-channel K + per-token V, MixedKV 等
3. **GQA-aware inference efficiency**: FlashDecoding, PagedAttention, Split-K 等

### Gap 声明

> 据我们所知，现有工作尚未将 $H_{kv}$ 作为统一解释变量，联合分析校准目标灵敏度、K/V 退化不对称性、温度校正方向与融合解码 kernel 的 crossover。

工作量：~60-80 行重组

---

## 六、Ch3 Method

### 修改点 1: KL 校准段落补 7B 趋同

位置：L287 附近，新增 ~15 行

内容：7B 上 KL/MSE 搜索到相同 percentile (100.0/99.9)，PPL 一致 (7.1121)。更大模型的 calibration landscape 更平坦。

### 修改点 2: Phase Boundary 理论分析

位置：L883 "GQA 支持机制" 之后，新增 ~40 行 subsection

内容：Triton 融合核 grid=(B, Hkv) 的 SM 利用率分析 + naive 路径的三次 HBM 访存分析。给出 bandwidth saving vs SM penalty 的 cost intuition。**不写具体数字**——具体 crossover 位置和 TPOT 数值全部留给 Ch4。

### 修改点 3: in-kernel percentile 方法描述

位置：L841 区域，新增 ~25 行

内容：top-2/bottom-2 两次 reduction 近似 percentile 的方法。公式 + 机制。**不写 "-31%" 或 "53/53"**。

### 修改点 4: inv_tau × GQA（L395-466）

保持不变。已经是 GQA-centric。

---

## 七、Ch4 Experiments 重构

### 新 section 结构

```
4.1 实验设置
4.2 校准目标的 bit-width 与规模依赖（含 7B KL=MSE）
4.3 低比特失效的结构性诊断（含 14B K/V ablation）
4.4 INT4-RoleAlign 实验结果
    4.4.1 PPL + Needle 跨模型（含 14B）
    4.4.2 RULER（14B 4K-16K + 1.5B FP16 baseline anchor）
    4.4.3 Synthetic LongBench proxy
    4.4.4 inv_tau 的 GQA 尺度依赖（实验发现，非 C4）
4.5 GQA-Aware 部署效率分析（C4 核心）★
    4.5.1 Phase 1 TPOT 对比表
    4.5.2 长序列 TPOT Scaling
    4.5.3 Phase Boundary 二维分析
    4.5.4 KV Cache 内存对比
    4.5.5 部署建议
4.6 综合讨论
    4.6.1 主要发现（5 条，以 GQA 为主线）
    4.6.2 BitDecoding case study（~1 页 limitation/engineering note）
    4.6.3 实验结论概要
    4.6.4 Threat-to-validity（含 Hkv/规模共变声明）
```

### 新增 Tables

| 编号 | 内容 |
|------|------|
| Tab 4-A | Phase 1 TPOT (4 模型 × 5 backends, 不含 BD) |
| Tab 4-B | 长序列 TPOT (14B, 4 seq × 4 backends) |
| Tab 4-C | Phase Boundary Δ 表 (4 模型 × 4 seq) |
| Tab 4-D | 14B RULER task breakdown (4 tasks × 3 sl) |
| Tab 4-E | 1.5B FP16 vs FI RULER (4 sl × 4 tasks) |
| Tab 4-F | 14B K/V Ablation PPL |
| Tab 4-G | 7B KL vs MSE percentile + PPL |
| Tab 4-H | Memory/Batch sweep |

### 新增 Figures

| 编号 | 内容 |
|------|------|
| Fig 4-1 | $(H_{kv}, \text{seq\_len})$ Phase Boundary heatmap（核心图） |
| Fig 4-2 | 14B 长序列 TPOT line chart |
| Fig 4-3 | PPL 退化 vs 模型规模 |
| Fig 4-4 | 1.5B RULER task breakdown (FP16 vs INT4) |

### 14B 口径统一规则

论文任何位置提到 14B 结果时：
> 14B Needle 在 4K-32K 全通过；RULER 在 4K-16K 达到 96.6%-98.5%，32K 未测。

Needle 和 RULER **不并排写在同一句里**，必须分开说明长度范围。

### LongBench 命名规则

- `Synthetic LongBench proxy (4K)` — Phase 2/3/4 使用
- `Official LongBench anchor (3-task sanity check)` — Stage 6 尝试但因 HF_HUB_OFFLINE 未完成

Ch4 开头加一张 **Evidence Pools / Protocol Map** 表，列清每类评测的数据来源和覆盖范围。

---

## 八、Ch5 Findings

```
Finding 1: 校准目标灵敏度的 bit-width 与规模依赖
Finding 2: Key 主导退化跨模型规模验证
Finding 3: RoleAlign 在大模型上保持质量
Finding 4: (Hkv, seq_len) Phase Boundary
(BitDecoding 不作为 Finding，放 Limitations)
```

---

## 九、7B KL=MSE Provenance

**动稿前必须完成**：把 7B 数据 aggregate 到 appendix table。

```
7B KL calib:  k_percentile=100.0, v_percentile=99.9, PPL=7.1121
7B MSE calib: k_percentile=100.0, v_percentile=99.9, PPL=7.1121
7B FP16:      PPL=6.7097
数据位置：results/emnlp_p012_batch/runs/ppl_{kl,mse,fp16}_7b_s*/
Calib 文件：artifacts/kv_calib_{rolealign_7b_v3,mse_7b_int4_rolealign_v1}.json
```

---

## 十、Threat-to-Validity 必须包含的声明

> 在当前模型集合中，$H_{kv}$ 与模型规模部分共变（1.5B/$H_{kv}$=2, 7B/4, 8B/8, 14B/8），因此相关结论应理解为结构性证据而非严格受控因果识别。8B 与 14B 共享 $H_{kv}$=8 但参数量相差 1.75×；短序列 TPOT crossover 在两者上一致（Δ≈−0.4 ms），为 $H_{kv}$ 主导假设提供支持，但不排除模型规模的次要贡献。

---

## 十一、执行顺序

```
Day 0: 证据池清单 + 7B KL=MSE aggregate appendix table
Day 1: Ch1 (RQ + Contributions + 核心主张) + Abstract
Day 2: Ch2 (3 条线重组) + Ch3 (KL 规模依赖 + Phase Boundary 理论 + in-kernel pct)
Day 3-4: Ch4 (Section 4.2-4.6 + Tables + Figures)
Day 5: Ch5 Findings + 全文口径检查 + 编译
```

---

## 十二、验收标准

```bash
# 执行以下检查，理想结果全部为空：
rg -n "\[D' 修订\]|Codex 指出|✓|✗" docs/option_d_plan.md
rg -n "universally safe|首个系统" docs/option_d_plan.md
rg -n "32K 时快 40%|53/53|-31%" docs/option_d_plan.md  # Ch3 里不该有
```

- [x] Ch3 模板无实验结果数字
- [x] 14B Needle/RULER 长度范围处处一致
- [x] BitDecoding 不是主 Finding
- [x] LongBench synthetic/official 区分明确
- [x] 7B KL=MSE 有 appendix 出处
- [x] Ch2 只有一套方案

---

_最终定稿: 2026-04-12_
_状态: D'' final — 可直接用于动稿_
