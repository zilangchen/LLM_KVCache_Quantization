# Option D''' 实施计划：论文叙事重构（四方审查定稿版）

> 本版本整合了 Codex adversarial review + 4 个并行审查 agent（EMNLP Reviewer×2 + 答辩委员会 + Meta Reviewer）的全部反馈。

## 一、论文身份

> **本文研究 GQA 架构下的 behavior-aligned KV cache quantization。**
> Attention-KL 是统一的校准与诊断原则，$H_{kv}$ 是与低比特失效模式、
> 温度校正分化和融合解码效率一致性变化的**结构性关联变量**。
> INT8 提供 canonical validation，INT4-RoleAlign 是 low-bit instantiation，
> 14B 与 BitDecoding 结果用于外部效度与边界分析。

**定位说明**（回应 R1 "RoleAlign = KIVI incremental" 质疑）：
本文的贡献不在 RoleAlign 这个方法本身（它确实是 KIVI + KL percentile search），
而在**诊断框架**——解释 per-channel BA percentile 为什么有效（K 主导退化 + GQA 噪声稀释），
以及融合核何时有效（phase boundary）。创新在诊断，不在方法。

---

## 二、Research Questions

位置：`ch1_introduction.tex` L125-145

```latex
\begin{description}
  \item[\textbf{RQ1}] \emph{KV Cache 量化应优化什么目标？其有效性是否随模型规模变化？}
  \item[\textbf{RQ2}] \emph{低比特量化为何失效？失效模式是否与 $H_{kv}$ 结构性关联？}
  \item[\textbf{RQ3}] \emph{诊断结论能否导出有效的低比特设计，
    并伴随可部署的效率收益？}
\end{description}
```

**审查修订**：原 RQ4 (融合核 crossover) 合并入 RQ3——"诊断→设计→部署"是自然递进（R3 指出 RQ4 与 RQ1-3 叙事断裂）。从 4 个 RQ 缩减为 3 个。

---

## 三、Contributions（4 条）

**审查修订**：从 5C 缩减为 4C（R1/R3/R4 共识：5C 稀释信号。C5 合并入 C3）。

### C1: 校准目标有效性的 bit-width 与规模依赖

在 INT8 下 KL 和 MSE 趋同；在 INT4 下 1.5B ($H_{kv}=2$) 上两者选出不同 percentile（99.5 vs 99.0，scale 差异 12.35%），而 7B ($H_{kv}=4$) 上趋同到相同参数（100.0/99.9）。

结论句：
> 在我们测试的模型规模与协议下，KL 至少不劣于 MSE，并在小模型 INT4 设置下表现更优。

**性质说明**：这是 empirical observation，不是 method contribution。

### C2: Key 主导退化的诊断与 $H_{kv}$ 结构性关联

四个模型一致观察到 INT4 退化由 Key 侧主导。14B K/V ablation：K 保持 FP16 恢复 93% PPL 退化（5.04→4.71），V 保持 FP16 仅恢复 64%。Needle 与 PPL 的解耦跨 1.5B-14B 一致。

**这是论文最强的 contribution**（R2 评 A）。

### C3: RoleAlign 跨模型规模验证与大模型外部效度

（原 C3 + C5 合并）

在 4 个模型上 INT4-RoleAlign 保持 Needle 100%，KV 压缩 ~73%，PPL 退化随规模减弱（1.5B: 13.7%, 7B: 6.0%, 8B: 2.4%, 14B: 7.6%）。

**14B 外部效度**：
- Needle 在 4K-32K 全通过
- RULER 在 4K-16K 达到 96.6%-98.5%（32K 因显存限制未测）
- 1.5B 上 INT4 与 FP16 的 RULER 差距不足 1%（证明低分是模型能力上限）

**PPL 非单调说明**（回应 R1 "14B 7.6% breaks trend vs 8B 2.4%"）：
14B 退化反弹可能与校准数据量、模型族差异（Qwen vs LLaMA）或 outlier 分布有关，在 Ch4 讨论中明确标注。

### C4: $(H_{kv}, \text{seq\_len})$ 空间中的融合核效率特征与部署建议

**审查修订**：crossover claim 限定在**长序列**（8K+），不声称 4K crossover（R2 指出 4K Δ=0.4ms 统计不显著）。

在 8K+ 序列长度下，Triton 融合核相对 naive dequant+SDPA 的优势随 $H_{kv}$ 和 seq_len 增大而**显著**增长：
- $H_{kv}=8$, 8K: Δ=-14.5ms (17%), **t >> 3**
- $H_{kv}=8$, 16K: Δ=-33.3ms (28%)
- $H_{kv}=8$, 32K: Δ=-77.1ms (40%)
- $H_{kv}=2$: 融合核在所有测试序列长度下均慢于 SDPA

8B ($H_{kv}=8$, LLaMA) 与 14B ($H_{kv}=8$, Qwen) 在短序列下的 crossover 幅度一致（Δ≈-0.4ms），为 $H_{kv}$ 而非模型规模主导提供支持证据，但**不做因果声称**。

部署建议：$H_{kv}\geq 4$ 且 seq>8K 使用融合核；$H_{kv}=2$ 使用 SDPA。**限 NVIDIA H20 平台**（其他 GPU Phase Boundary 可能不同）。

不放入 C4 的内容（各归原位）：
- inv_tau × GQA 尺度依赖 → Ch4 实验发现
- in-kernel percentile → Ch3 方法实现

---

## 四、核心主张

> 本文的核心主张是：attention-KL 提供了 GQA 架构下 KV cache quantization 的统一校准与诊断原则，而 $H_{kv}$ 是与低比特失效模式、温度校正分化和融合解码效率一致性变化的结构性关联变量。在当前模型集合中，$H_{kv}$ 与模型规模部分共变，因此相关结论应理解为结构性证据而非严格受控因果识别。

---

## 五、Ch2 Related Work

### 结构重组（3 条线）

1. **KV quantization / calibration**: KIVI, KVQuant, QuIP, GEAR, QServe 等
2. **K/V asymmetry / low-bit rescue**: per-channel K + per-token V, MixedKV 等
3. **GQA-aware inference efficiency**: FlashDecoding, PagedAttention, Split-K 等

### Gap 声明

> 据我们所知，现有工作尚未将 $H_{kv}$ 作为统一的结构性关联变量，联合分析校准目标灵敏度、K/V 退化不对称性、温度校正方向与融合解码 kernel 的效率特征。

工作量：~60-80 行重组

---

## 六、Ch3 Method

### 修改点 1: KL 校准段落补 7B 趋同（~15 行新增）
### 修改点 2: Phase Boundary 理论分析（~40 行新 subsection）
- 只写 cost intuition（SM 利用率 vs bandwidth saving）
- **不写任何具体数字**
### 修改点 3: in-kernel percentile 方法（~25 行新增）
- top-2/bottom-2 公式 + 机制
- **不写 TPOT 改善数字**
### 修改点 4: inv_tau × GQA（保持不变）

---

## 七、Ch4 Experiments 重构

### 新 section 结构

```
4.1 实验设置
    + Evidence Pools / Protocol Map 表（新增）
4.2 校准目标的 bit-width 与规模依赖（含 7B KL=MSE）
4.3 低比特失效的结构性诊断（含 14B K/V ablation）
4.4 INT4-RoleAlign 实验结果
    4.4.1 PPL + Needle 跨模型（含 14B）
    4.4.2 RULER（14B 4K-16K + 1.5B FP16 baseline anchor）
    4.4.3 Synthetic LongBench proxy
    4.4.4 inv_tau 的 GQA 尺度依赖（实验发现）
4.5 GQA-Aware 部署效率分析（C4 核心）★
    4.5.1 Phase 1 TPOT 对比表
    4.5.2 长序列 TPOT Scaling（含 CI 区间）
    4.5.3 Phase Boundary 分析（限 8K+ 显著区间，带 CI）
    4.5.4 8B vs 14B 同 Hkv 控制对比
    4.5.5 KV Cache 内存对比
    4.5.6 部署建议（限 H20 平台）
4.6 综合讨论
    4.6.1 主要发现（4 条，以 GQA 为组织轴）
    4.6.2 BitDecoding engineering case study（~1 页 limitation）
    4.6.3 PPL 非单调说明（14B 7.6% vs 8B 2.4%）
    4.6.4 实验结论概要
    4.6.5 Threat-to-validity（扩充版）
```

### 新增 Tables（8 张）

| 编号 | 内容 |
|------|------|
| Tab 4-A | Phase 1 TPOT (4 模型 × 5 backends) |
| Tab 4-B | 长序列 TPOT (14B, 4 seq × 4 backends, **含 CI**) |
| Tab 4-C | Phase Boundary Δ 表 (**4 模型** × 4 seq, **含 CI 和显著性标注**) |
| Tab 4-D | 14B RULER task breakdown (4 tasks × 3 sl) |
| Tab 4-E | 1.5B FP16 vs FI RULER (4 sl × 4 tasks) |
| Tab 4-F | 14B K/V Ablation PPL |
| Tab 4-G | 7B KL vs MSE percentile + PPL |
| Tab 4-H | Memory/Batch sweep |

### 新增 Figures（4 张）

| 编号 | 内容 |
|------|------|
| Fig 4-1 | $(H_{kv}, \text{seq\_len})$ Phase Boundary heatmap（**带 CI 区间，4K 标灰**） |
| Fig 4-2 | 14B 长序列 TPOT line chart（**带 error bar**） |
| Fig 4-3 | PPL 退化 vs 模型规模（**标注 14B 非单调**） |
| Fig 4-4 | 1.5B RULER task breakdown (FP16 vs INT4) |

### 14B 口径统一规则

> 14B Needle 在 4K-32K 全通过；RULER 在 4K-16K 达到 96.6%-98.5%，32K 未测。

Needle 和 RULER **不并排写在同一句里**。

### LongBench 命名规则

- `Synthetic LongBench proxy` — 覆盖 1.5B/14B
- `Official LongBench anchor` — 7B/8B 尝试但因 HF_HUB_OFFLINE 未完成

### Phase Boundary 报告规则（回应 R2 统计质疑）

- **4K 的 crossover (Δ≈0.4ms)**：标注为 "within noise, not significant"，图中标灰
- **8K+ 的差距 (Δ=14-77ms)**：标注为 "significant"，带 CI 区间
- 不做 "crossover at exactly 4K" 的绝对 claim

---

## 八、Ch5 Findings（4 条，对应 4C）

```
Finding 1: 校准目标灵敏度的 bit-width 与规模依赖
Finding 2: Key 主导退化与 Hkv 结构性关联
Finding 3: RoleAlign 跨规模验证 + 14B 外部效度
Finding 4: 融合核效率的 (Hkv, seq_len) 特征
```

BitDecoding → Limitations section，不作为 Finding。

---

## 九、7B KL=MSE Provenance

**Day 0 必须完成**：aggregate 到 appendix table。

```
7B KL calib:  k_percentile=100.0, v_percentile=99.9, PPL=7.1121
7B MSE calib: k_percentile=100.0, v_percentile=99.9, PPL=7.1121
7B FP16:      PPL=6.7097
数据: results/emnlp_p012_batch/runs/ppl_{kl,mse,fp16}_7b_s*/
Calib: artifacts/kv_calib_{rolealign_7b_v3,mse_7b_int4_rolealign_v1}.json
```

---

## 十、Threat-to-Validity（扩充版，回应 R3）

必须包含以下 5 条声明：

1. **$H_{kv}$/规模共变**：$H_{kv}$ 与模型规模部分共变（1.5B/2, 7B/4, 8B/8, 14B/8）。8B 与 14B 共享 $H_{kv}$=8 但参数量差 1.75×，短序列 crossover 幅度一致（Δ≈−0.4 ms），为 $H_{kv}$ 结构性关联提供支持。但相关结论应理解为结构性证据而非严格因果识别。

2. **解码策略依赖**：所有实验使用 greedy decoding (temp=0)。量化误差在 sampling (temp>0) 下的表现未知。部署建议限定于 greedy/near-greedy 场景。

3. **硬件依赖**：所有 TPOT 数据来自单张 NVIDIA H20 (96GB, sm_90)。Phase Boundary 在 A100/H100 上可能因 SM 数量和带宽比不同而移位。

4. **校准数据分布依赖**：仅用 WikiText-103 校准。代码、多语言等分布外数据的适用性未验证。

5. **单实现威胁**：KIVI baseline 为自实现（核心量化轴策略一致，未复现全部工程优化）。RoleAlign 与 KIVI 的差异可能混入实现差异。

---

## 十一、执行顺序（修订版，7 天）

```
Day 0: 证据池清单 + 7B KL=MSE aggregate appendix table + 8B 长序列数据确认
Day 1: Ch1 (RQ×3 + Contributions×4 + 核心主张) + Abstract
Day 2: Ch2 (3 条线重组) + Ch3 (KL 规模依赖 + Phase Boundary 理论 + in-kernel pct)
Day 3: Ch4 Tables×8 + Figures×4 制作
Day 4: Ch4 Section 4.2-4.4 写作
Day 5: Ch4 Section 4.5-4.6 写作（Phase Boundary + 讨论）
Day 6: Ch5 Findings + TTV 扩充 + 全文口径检查
Day 7: 编译 + 格式 + 页数控制 + 交叉引用
```

---

## 十二、验收标准

```bash
rg -n "universally safe|首个系统|从未被系统" docs/option_d_plan.md  # 应为空
rg -n "crossover at 4K|crossover at exactly" thesis/chapters/     # 应为空
```

- [x] Ch3 无实验结果数字
- [x] 14B Needle/RULER 长度范围处处一致且分开写
- [x] BitDecoding 不是主 Finding（在 Limitations）
- [x] LongBench synthetic/official 区分明确
- [x] 7B KL=MSE 有 appendix 出处
- [x] Ch2 只有一套方案（3 条线）
- [x] Contributions 4 条（不是 5 条）
- [x] RQ 3 个（不是 4 个）
- [x] Phase Boundary 的 4K claim 标灰 / not significant
- [x] TTV 包含 5 条声明（Hkv/规模、解码策略、硬件、校准数据、单实现）
- [x] 工作量 7 天（不是 5.5 天）

---

_四方审查定稿: 2026-04-12_
_审查来源: Codex adversarial review + R1(novelty) + R2(experiments) + R3(defense) + R4(meta)_
_状态: D''' final — 可直接用于动稿_
