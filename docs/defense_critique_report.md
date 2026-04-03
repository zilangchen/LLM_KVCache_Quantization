# 论文全面质询与审评报告

> 生成时间：2026-04-03
> 基于论文全文（5 章 + 附录，102 页）、项目代码和实验数据的深度分析

---

## Phase 1：严格答辩质询（10 个维度）

### Q1. 创新性深度 — "Attention-KL 真的是新的吗？"

**攻击力：严重**

| # | 尖锐问题 |
|---|---------|
| 1 | TensorRT 自 2017 年就使用基于 KL/entropy 的 INT8 校准（Migacz 2017）。你的 Attention-KL 与 TensorRT 的 activation KL calibration 的本质区别是什么？仅仅是"把 KL 从激活层搬到 softmax 输出"这一步是否构成足够的创新？ |
| 2 | 知识蒸馏文献（Hinton 2015）早已将 teacher-student 的 softmax 输出 KL 散度作为标准训练目标。你的方法在概念上与"量化模型对 FP16 模型做 attention-level 蒸馏"有何区别？ |
| 3 | 你声称 Attention-KL 是"统一原则"（贡献一），但实际上 INT4 对称路线即使用了 KL 校准也完全失败（Needle 0%）。一个"统一"原则在低比特下失效，这不恰恰说明它不够统一吗？ |
| 4 | per-head inv_tau 搜索本质上就是 7 个候选值的 grid search，最终论文又决定不使用它（mainline 关闭 tau）。为什么要花大篇幅描述一个最终被抛弃的组件？ |

**作者可能的辩解**：TensorRT 的 KL 用于激活值分布，我们的 KL 用于注意力权重分布，目标不同。
**再反驳**：这种区别是应用层面而非方法层面的。核心数学工具完全相同（KL on softmax output），创新性主要来自"在 KV Cache 量化场景应用 KL"——这更像是一个合理的工程选择而非原理性突破。

---

### Q2. INT4 失败的诚实度 — "你是否在选择性展示结果？"

**攻击力：致命**

| # | 尖锐问题 |
|---|---------|
| 1 | 项目记录显示 INT4 unified gate 失败后你回退到了 `thesis-safe-v1` 标签（commit 9d7dbea）。这意味着你的论文数据不是最新实验结果，而是回退到一个"安全版本"。这是否构成结果 cherry-pick？ |
| 2 | 11 个 canonical claims 中有 3 个 FAIL（C6 RULER -2.64%, C7 Needle -2.0%, C8 PPL -15.92%），但论文的摘要和结论几乎只强调成功的部分（INT8 成功、Needle 恢复到 100%）。失败的 claims 在摘要中完全没有提及——这是否属于 framing bias？ |
| 3 | C6 FAIL 的解释是"非 mainline 消融变体拉低均值"——但你为什么要把消融变体混入 mainline 的 claim 验证中？如果只看 mainline 配置，C6 本应 PASS。这种聚合方式是否人为制造了一个可以"解释掉"的失败？ |
| 4 | INT4-RoleAlign 的 PPL 退化在 1.5B 上高达 13.7%——对于你声称的"核心方法贡献"，这个退化幅度在实际部署中可接受吗？ |

**作者可能的辩解**：我们诚实报告了所有失败，并在 Limitations 中充分讨论。
**再反驳**：诚实报告是底线，不是加分项。问题在于论文的叙事结构将失败包装为"诊断发现"而非承认方法局限。"INT4 对称量化失败"被重新叙述为"通过诊断透镜发现 Key 主导退化"——这是否是用修辞技巧将失败转化为贡献？

---

### Q3. 基线公平性 — "KIVI 基线被削弱了吗？"

**攻击力：严重**

| # | 尖锐问题 |
|---|---------|
| 1 | 你的 KIVI-style 基线明确缺少原论文的残差补偿等工程优化（ch4 表4.1 注释）。INT8-ours 享受了 Triton 融合 kernel、自适应保护、KL 校准的全套待遇，而 KIVI 使用的是 torch_ref。这种不对称对比是否公平？ |
| 2 | 表 4.12 显示 INT4-RoleAlign 的 PPL 在所有三个模型上不优于甚至略差于 KIVI-style（1.5B: 13.7% vs 12.0%；7B: 6.1% vs 5.5%）。既然你的方法连不完整的 KIVI 都没打赢，完整版 KIVI 岂不是更好？ |
| 3 | 为什么不直接运行 KIVI 的官方代码作为基线？ |
| 4 | int8_baseline 使用固定 percentile 99.9——这是一个很弱的 baseline。更强的 baseline 应该是 grid search 多个 percentile 后选最优。你是否选择了一个偏弱的基线来放大自己方法的优势？ |

---

### Q4. 统计可靠性 — "n=5 能证明什么？"

**攻击力：严重**

| # | 尖锐问题 |
|---|---------|
| 1 | n=5 的符号翻转检验，最小可达 p 值为 1/33 ≈ 0.031。经 BH-FDR 校正后，几乎不可能达到显著性。你的"非劣性"声明实质上是"效应太小/样本太少，检测不到差异"——这与"确认无差异"完全不同。 |
| 2 | PPL 的 Bootstrap CI 半宽为 ±0.00（表4.7），这意味着 5 个 seed 产出完全相同的 PPL（贪婪解码下合理）。那 CI 就是退化的——0 方差意味着检验无意义。你的统计框架在 PPL 指标上实质上是空转的。 |
| 3 | 以 n=5 检测 Cohen's d_z ≈ 1.5 的效应需要 80% power——你的非劣性阈值（PPL ≤0.5%）对应的效应量远小于此。你能否计算出你的检验实际能检测到的最小 PPL 退化是多少？ |
| 4 | 为什么不增加到 n=10 或 n=20 seeds？贪婪解码下 PPL 不变，那 seed 变异的来源到底是什么？ |

---

### Q5. 评测方法局限 — "你的 benchmark 可信吗？"

**攻击力：致命**

| # | 尖锐问题 |
|---|---------|
| 1 | LongBench 使用自行实现的合成数据源，将同一噪声句子重复 240 次并插入锚点答案。这种"在重复文本中找唯一不同内容"的任务本质上是模式匹配而非阅读理解。你如何保证它能代表真实的长上下文理解能力？ |
| 2 | RULER 中 CWE 和 VT 子任务在所有模式（包括 FP16）下得分为 0%。这意味着 50% 的 RULER 子任务提供零区分度。为什么保留这些子任务在聚合指标中？这人为压低了所有方法的绝对分数。 |
| 3 | FP16 的 S-NIAH 得分仅 8.33%，而单独的 Needle 评测中 FP16 达 100%。两者都是 passkey 检索任务，为何差 12 倍？是否因为 RULER 的 exact match 评分过严或 task 生成器有 bug？ |
| 4 | chunk_size=128 的 PPL 评测中，每个 chunk 内新生成的 KV 实际上是 FP16 精度（未量化）。这是否导致 PPL 结果系统性低估了量化的实际影响？chunk_size=1 的全量化 PPL 测试为什么没有对 INT8-ours 做？ |
| 5 | 为什么不在至少一个官方 benchmark 上运行实验？即使只对 FP16 和 INT8-ours 在官方 LongBench 上做一次验证，也能大幅提升结论的可信度。 |

---

### Q6. 系统效率声明 — "量化后反而更慢？"

**攻击力：严重**

| # | 尖锐问题 |
|---|---------|
| 1 | INT8-ours 的 TPOT 为 47.14ms，而 FP16 仅为 24.39ms——量化后延迟增加了 93%。你的"8-38% 延迟降低"是相对于 int8_baseline（51.43ms），而非 FP16。这种 framing 是否有误导性？ |
| 2 | INT4-RoleAlign 声称 73% 显存压缩，但延迟增加 2-2.5x。一个更慢但省显存的方法，在什么场景下是有价值的？你能给出一个具体的部署场景吗？ |
| 3 | int8_baseline（无融合 kernel）比 FP16 还慢，说明"量化不融合 = 更慢"。那你的效率收益本质上来自 Triton kernel 而非量化方法本身。如果给 FP16 也写一个 Triton 融合 kernel，差距是否会缩小？ |
| 4 | 所有效率数据都在 batch=1 下。生产环境中 batch=8-128 才是常见设置。为什么主实验不包含 batch>1 的数据？ |

---

### Q7. 泛化性不足 — "三个小模型够吗？"

**攻击力：中等**

| # | 尖锐问题 |
|---|---------|
| 1 | 你的最大模型仅 8B 参数。KV Cache 压力在 13B/70B 模型上最为突出——你如何保证方法在大模型上有效？ |
| 2 | 上下文长度锁定 ≤32K。Qwen2.5 支持 128K，LLaMA-3.1 支持 128K。为什么不测试更长的上下文？ |
| 3 | 所有模型都是 decoder-only + GQA。MHA（Multi-Head Attention）和 MQA（Multi-Query Attention）模型上的表现如何？你的 GQA 依赖性结论在 MHA 下是否还成立？ |
| 4 | 单张 H20 GPU——效率结论能否推广到 A100/H100？ |

---

### Q8. 理论深度 — "公式推导够严格吗？"

**攻击力：中等**

| # | 尖锐问题 |
|---|---------|
| 1 | GQA 噪声功率 ∝ 1/H_kv 的推导假设了跨 KV 组的量化噪声独立。但同一层的不同 KV 组处理的是相同 hidden state 经不同投影——噪声不太可能独立。你验证过这个假设吗？ |
| 2 | SQNR 公式 6.02b+1.76 假设输入均匀分布。Key/Value 激活值明显不是均匀分布——你的 289 倍噪声比是否高估了？ |
| 3 | "Key 决定看哪里"是一个直觉性比喻，而非严格论证。Value 量化噪声也会通过 o = softmax(QK^T)V_hat 传播到输出——你能否给出 Key 噪声 vs Value 噪声对输出的定量贡献比？ |

---

### Q9. 校准产物问题 — "你的核心贡献有 bug？"

**攻击力：严重**

| # | 尖锐问题 |
|---|---------|
| 1 | 你论文的核心贡献是"行为对齐校准"，但 1.5B 主模型的校准产物 Q 向量缺少 input_layernorm 和 RoPE 预处理（v3_quick）。这意味着校准时的 QK^T 点积与实际推理时不一致——你在用错误的行为来做"行为对齐"。这不是自相矛盾吗？ |
| 2 | 修正版对比验证被列为"未来工作"。对于一篇以校准为核心贡献的论文，核心产物有已知缺陷却不修复——这是否说明工作尚未成熟？ |
| 3 | 7B 和 8B 模型的校准产物是否也有同样的问题？ |

---

### Q10. 定位与写作 — "本科论文投顶会？"

**攻击力：中等**

| # | 尖锐问题 |
|---|---------|
| 1 | 这是一篇中文本科毕业论文（102页），目标却是投 EMNLP 2026。从毕设到会议论文需要大幅改写——当前版本是否只是一个 draft？ |
| 2 | 论文中"贡献四"占据了核心地位，但 INT4-RoleAlign 本质上是 KIVI 的量化轴 + 离线 percentile 搜索。EMNLP 的新颖性门槛是否能接受这个增量？ |
| 3 | Related Work 对 KL-based calibration 的先驱工作（TensorRT、KD 文献）讨论不足。 |

---
---

## Phase 2：多角度审稿人审评

---

### Reviewer A — Model Compression & Quantization Expert

#### Summary
This paper proposes a "Behavior Alignment" framework for KV Cache quantization centered on using Attention-KL divergence as a unified calibration objective and diagnostic lens. The INT8 path delivers near-lossless quality with 44% KV memory reduction and 8-38% TPOT reduction. The INT4-RoleAlign path recovers Needle from 0% to 100% at 73% KV compression but incurs 2.4-13.7% PPL degradation and 2-2.5x latency overhead.

#### Strengths
- **S1.** Clear and well-motivated principle — the "numerical proxy mismatch" framing is compelling.
- **S2.** Thorough diagnostic methodology — controlled K/V ablation yielding actionable Key-dominant finding.
- **S3.** Rigorous statistical framework — 5-seed Bootstrap CI, BH-FDR correction, explicit evidence maturity levels.
- **S4.** Commendable transparency about limitations — calibration bug, synthetic benchmarks, RULER C6 failure all disclosed.
- **S5.** Complete INT8 operating point — genuinely deployable with 100% Needle, <0.3% PPL, 44% KV memory.

#### Weaknesses
- **W1 [Major]**: INT4-RoleAlign has limited novelty beyond KIVI's quantization axis design. Per-channel K + per-token V asymmetric is identical to KIVI. Table 4.12 shows RoleAlign PPL is slightly worse than KIVI on all three models.
- **W2 [Major]**: Incomplete and potentially unfair KIVI baseline — missing residual compensation, uses torch_ref not fused kernel.
- **W3 [Major]**: The Attention-KL calibration objective is not novel — TensorRT has used KL-based INT8 calibration since 2017.
- **W4 [Major]**: LongBench evaluation uses self-implemented synthetic data, severely limiting external validity.
- **W5 [Minor]**: INT4-RoleAlign latency regression (2-2.5x) makes it impractical as presented.
- **W6 [Minor]**: Calibration artifact bug on 1.5B primary model not resolved.
- **W7 [Minor]**: Limited model scale (≤8B) and diversity (all GQA, no MHA/MQA).

#### Questions for Authors
- Q1. What concrete metric does RoleAlign improve over calibration-free KIVI?
- Q2. Did you actually compute per-layer KL values to drive the diagnosis, or was diagnosis based on downstream metrics?
- Q3. Could percentile-based static scale + same adaptive protection achieve comparable INT8 results?
- Q4. Is the i.i.d. quantization noise assumption across KV groups validated?
- Q5. Why retain CWE/VT (both 0% for all modes) in RULER aggregate?
- Q6. How sensitive are PPL results to chunk_size?
- Q7. Have you verified INT4-RoleAlign results on 1.5B are not affected by the calibration bug?

#### Missing References
TensorRT INT8 Calibration (Migacz 2017), SqueezeLLM, QuaRot, MiKV, Coupled Quantization

#### Scores
| Dimension | Score |
|-----------|-------|
| Soundness | 3/4 |
| Presentation | 3/4 |
| Contribution | **2/4** |
| Overall | **2/5** |
| Confidence | 4/5 |
| **Recommendation** | **Borderline Reject** |

---

### Reviewer B — LLM Inference Systems Expert

#### Summary
The system consists of offline KL-based calibration producing <10KB JSON artifacts, a Triton fused decode kernel for INT8, and INT4-RoleAlign using torch_ref decode. Experiments on single H20 GPU at batch=1 show INT8 nearly doubles decode latency vs FP16 (47ms vs 24ms) while saving 44% KV memory.

#### Strengths
- **S1.** Intellectually honest reporting of negative results (3 out of 16 expectations FAIL).
- **S2.** Diagnostic methodology using attention-KL as both calibration and diagnostic instrument is genuinely interesting.
- **S3.** Rigorous statistical framework far exceeding the norm.
- **S4.** Complete and well-documented implementation with issue tracking identifiers.
- **S5.** Low calibration cost (<10KB JSON, 15-50 min).

#### Weaknesses
- **W1 [Major]**: Primary efficiency claim is misleading — INT8 TPOT 47ms vs FP16 24ms is a 93% increase in absolute latency.
- **W2 [Major]**: Missing comparison with FlashInfer, Flash-Decoding++, QServe fused kernels. Triton kernel doesn't use tensor cores.
- **W3 [Major]**: Batch=1 is unrepresentative of real serving (production is batch=8-128+).
- **W4 [Major]**: INT4-RoleAlign 2-2.5x latency + 13.7% PPL degradation has unclear practical value.
- **W5 [Minor]**: Triton kernel is not publication-level systems work (no autotune, no split-K, no pipelining).
- **W6 [Minor]**: Self-implemented benchmarks limit external validity.
- **W7 [Minor]**: Single GPU (H20) limits generalizability.

#### Questions for Authors
- Q1. What is INT8-ours absolute TPOT vs FP16 at batch=8, 16, 32?
- Q2. What fraction of H20 peak memory bandwidth does the kernel achieve?
- Q3. What concrete metric does RoleAlign improve over calibration-free KIVI?
- Q4. How frequently does the adaptive dynamic path trigger?
- Q5. How confident are you INT8 results hold with corrected calibration?
- Q6. Why no INT4 Triton kernel with in-kernel unpacking?

#### Missing References
FlashInfer, Flash-Decoding++, QoQ/QuaRot, KVQuant, GEAR, CacheGen

#### Scores
| Dimension | Score |
|-----------|-------|
| Soundness | **2/4** |
| Presentation | 3/4 |
| Contribution | **2/4** |
| Overall | **2/5** |
| Confidence | 4/5 |
| **Recommendation** | **Borderline Reject** |

---

### Reviewer C — NLP Evaluation & Long-Context Expert

#### Summary
Evaluation spans PPL (WikiText-2, cs=128), Needle (4K-32K), self-implemented LongBench-style synthetic benchmark, self-implemented RULER variant, and system metrics, with 5-seed Bootstrap CI and BH-FDR correction.

#### Strengths
- **S1.** Principled calibration objective with theoretical grounding (SQNR analysis, GQA noise dilution).
- **S2.** Honest reporting of negative results including 3 FAIL claims.
- **S3.** Controlled K/V ablation cleanly isolates Key quantization as dominant factor.
- **S4.** Reproducibility infrastructure (fixed seeds, greedy decoding, pinned revisions).
- **S5.** Statistical framework appropriate for small sample size.

#### Weaknesses
- **W1 [Major]**: Self-implemented LongBench synthetic generator — noise repeated 240 times, anchor template leaks answer format, qualitatively different from real tasks.
- **W2 [Major]**: RULER CWE/VT at 0% for ALL modes including FP16 — 50% of RULER provides zero discriminative signal. S-NIAH FP16 only 8.33% while Needle 100%.
- **W3 [Major]**: n=5 seeds provides critically low statistical power. PPL variance is zero (greedy decoding), making CI degenerate.
- **W4 [Major]**: chunk_size=128 PPL substantially underestimates quantization impact. INT8-ours cs=1 data is conspicuously absent.
- **W5 [Minor]**: Needle tests only retrieval, not comprehension or reasoning.
- **W6 [Minor]**: S-NIAH exact_match vs Needle contains_match methodological inconsistency.
- **W7 [Minor]**: Missing cs=1 PPL for INT8-ours is the most critical missing data point.

#### Questions for Authors
- Q1. Can you provide INT8-ours PPL at chunk_size=1?
- Q2. Why does FP16 S-NIAH score only 8.33% while Needle achieves 100%?
- Q3. Have you considered running official RULER or LongBench evaluation?
- Q4. What is the statistical power of your sign-flip test at n=5 for detecting 1% PPL degradation?
- Q5. Is the CWE distractor frequency ~90x target frequency intentional?
- Q6. Have you measured effective context length needed to solve LongBench synthetic tasks?
- Q7. How does 13.7% PPL degradation translate to downstream task performance?

#### Missing References
TOST framework (Schuirmann 1987), KVQuant, GEAR, KIVI full implementation

#### Scores
| Dimension | Score |
|-----------|-------|
| Soundness | **2/4** |
| Presentation | 3/4 |
| Contribution | **2/4** |
| Overall | **2/5** |
| Confidence | 4/5 |
| **Recommendation** | **Borderline Reject** |

---

### Reviewer D — Attention Mechanism Theory Expert

#### Summary
The paper uses KL divergence between FP16 and quantized softmax attention distributions as unified calibration objective and diagnostic lens. Key theoretical contributions include SQNR analysis, GQA noise dilution argument, and the "retrieval vs language modeling" decoupling insight.

#### Strengths
- **S1.** Principled diagnostic methodology — "principle -> diagnosis -> design -> boundary" workflow is genuinely novel.
- **S2.** Honest and thorough reporting of negative results (inv_tau shown to be harmful, 3 FAIL claims disclosed).
- **S3.** Cross-architecture ablation revealing GQA dependence — H_kv=2 vs 4 vs 8 provides strong evidence.
- **S4.** Careful statistical framework above the norm.
- **S5.** The "retrieval vs language modeling" decoupling insight is theoretically interesting and practically important.

#### Weaknesses
- **W1 [Major]**: KL divergence objective lacks formal justification for optimality. Forward KL vs Reverse KL choice never discussed.
- **W2 [Major]**: GQA noise dilution analysis is empirically motivated, not rigorously derived. Independence assumption unstated.
- **W3 [Major]**: The causal claim "Key decides where to look" lacks formal rigor — Value noise propagation never bounded.
- **W4 [Major]**: SQNR analysis conflates two different ratios (257x vs 289x) and oversimplifies (assumes uniform distribution).
- **W5 [Minor]**: Temperature correction theory-experiment contradiction insufficiently analyzed.
- **W6 [Minor]**: Calibration artifact deficiency on primary model undermines the framework's own terms.
- **W7 [Minor]**: INT4-RoleAlign shows no clear advantage over KIVI-style on PPL.
- **W8 [Minor]**: Extreme value statistics argument needs tighter conditions.

#### Questions for Authors
- Q1. Have you measured actual inference-time KL divergence (not just calibration-time)?
- Q2. Have you measured correlation structure of quantization errors across KV heads?
- Q3. Why forward KL and not reverse KL or Jensen-Shannon?
- Q4. Can you explain the mechanism by which BA-guided calibration trades PPL for Needle recovery?
- Q5. Why does KIVI catastrophically degrade at chunk_size=1 while RoleAlign remains stable?
- Q6. What prevents Needle failure in INT4-RoleAlign without adaptive protection?
- Q7. Have you considered continuous optimization of inv_tau (vs discrete grid search)?

#### Missing References
Bondarenko et al. (EMNLP 2021), LLM.int8() (Dettmers NeurIPS 2022), RPTQ (Yuan 2023), FlexGen (Sheng ICML 2023), ZeroQuant-V2 (Yao 2023)

#### Scores
| Dimension | Score |
|-----------|-------|
| Soundness | **2/4** |
| Presentation | 3/4 |
| Contribution | **3/4** |
| Overall | **3/5** |
| Confidence | 4/5 |
| **Recommendation** | **Borderline Accept** |

---
---

## Phase 3：综合汇总

### 审稿人评分汇总

| 审稿人 | Soundness | Presentation | Contribution | Overall | Recommendation |
|--------|-----------|-------------|-------------|---------|---------------|
| A (量化) | 3 | 3 | **2** | **2** | Borderline Reject |
| B (系统) | **2** | 3 | **2** | **2** | Borderline Reject |
| C (评测) | **2** | 3 | **2** | **2** | Borderline Reject |
| D (理论) | **2** | 3 | **3** | **3** | Borderline Accept |
| **均值** | **2.25** | **3.0** | **2.25** | **2.25** | — |

**Meta-Review**：3 Borderline Reject + 1 Borderline Accept = 整体倾向 Reject

---

### 全部问题优先级排序表

| 优先级 | 类别 | 问题 | 来源 | 可修复性 | 当前状态 |
|--------|------|------|------|---------|---------|
| **P0** | 评测 | LongBench 合成源无法代表真实长上下文理解 | C-W1, Q5-1 | 中 | T1-1 官方 LongBench 计划中 |
| **P0** | 评测 | RULER CWE/VT 全模式 0%，可能是实现 bug | C-W2, Q5-2 | 高 | EVL-047/048 已修复，正在重跑验证 |
| **P0** | 评测 | INT8-ours 缺 chunk_size=1 PPL 数据 | C-W4, Q5-4 | 高 | **Exp-3 正在跑** |
| **P0** | 校准 | 1.5B 主模型校准产物 Q 向量缺 layernorm+RoPE | A-W6, Q9-1 | 高 | **CAL-034 已修复，v3 产物已生成** |
| **P1** | 新颖性 | INT4-RoleAlign 量化轴与 KIVI 完全相同 | A-W1, Q3-2 | 低 | Exp-4 KIVI 对比计划中 |
| **P1** | 新颖性 | Attention-KL 校准非原创（TensorRT 2017） | A-W3, Q1-1 | 低 | **W-3 已补充 TensorRT 引用和讨论** |
| **P1** | 公平性 | KIVI 基线被系统性削弱 | A-W2, Q3-1 | 中 | Exp-4 KIVI 增强计划中 |
| **P1** | 效率 | INT8 绝对延迟比 FP16 高 93%，framing 误导 | B-W1, Q6-1 | 高 | **W-1 已修正效率 framing** |
| **P1** | 统计 | n=5 统计功效不足，PPL 方差=0 检验退化 | C-W3, Q4 | 中 | E-3 n=10 计划中 |
| **P1** | 理论 | KL 最优性无形式化证明 | D-W1, Q8 | 中 | E-2 KL 消融计划中 |
| **P2** | 效率 | 缺少 FlashInfer 等 SOTA kernel 对比 | B-W2 | 中 | 论文 Limitations 讨论 |
| **P2** | 效率 | batch=1 不代表生产场景 | B-W3, Q6-4 | 高 | **W-1 已引用 batch>1 数据** |
| **P2** | 理论 | GQA 1/H_kv 分析独立性假设未验证 | D-W2 | 中 | 论文讨论 |
| **P2** | 泛化 | 仅 ≤8B 模型、≤32K 上下文 | Q7 | 低 | 论文 Limitations |
| **P2** | 评测 | S-NIAH 8.33% vs Needle 100% 矛盾 | C-W6 | 高 | **W-2 已添加评分差异说明** |
| **P3** | 理论 | SQNR 289x 混淆两个数值 | D-W4 | 高 | **W-4 已统一为 289 + 脚注解释** |
| **P3** | 写作 | inv_tau 大篇幅描述但最终不用 | Q1-4 | 高 | ✅ 已标注为"可选增强" |
| **P3** | 缺引 | TensorRT, QuaRot, FlashInfer 等 | A/B 缺失引用 | 高 | **W-3 已补充 TensorRT + QuaRot** |

---

## 补充：审查 Agent 发现的新攻击面（2026-04-03 下午）

### 攻击面 6 [高危]：K/V 消融缺 PPL

**问题**："你说 Key 主导退化，但只看了检索任务。PPL 上 K/V 分离效应未知。"

**应对**：Exp-11（K/V 消融 PPL）已写好脚本，待跑。结果将直接写入论文 ch4 K/V 消融表。

### 攻击面 7 [高危]：Adaptive vs KL 谁是真功臣

**问题**："如果给 percentile baseline 也加 adaptive，是不是也能 Needle 100%？KL 贡献了什么？"

**答辩回答**：int8_baseline 使用 per-token 动态 scale（每次 append 重新计算 absmax），天然不存在"校准范围外裁剪"问题——因此 adaptive 保护机制对 int8_baseline 无意义（它解决的是**静态** scale 的问题）。两种 scale 策略各有优缺点：动态 scale 鲁棒但不支持 Triton 融合 kernel（scale 在运行时才确定），静态 scale 需要 adaptive 保护但支持融合 kernel 加速。KL 校准在静态 scale 体系中提供了最优的 scale 选择（相比 percentile 在 KL 散度空间上更优），而 adaptive 是这个体系的鲁棒性保障。

### 攻击面 2 补充：KL 在 INT4 下有害

**答辩回答**："统一原则的'统一'体现在 KL 的双重角色，不是说它在所有 bit-width 上都是最优校准目标。KL 作为校准目标在 INT8 有效（256 级别提供充足搜索空间），作为诊断透镜在 INT4 有效（揭示 Key 主导退化），但作为校准目标在 INT4 对称格式下不适用——15 个离散级别使 KL 优化景观高度不规则。INT4 的失败恰恰是诊断透镜发挥作用的起点。"

### 诊断结果（已写入论文）

- **G2 跨头相关性**：ρ = 0.024（独立性假设成立）
- **G5 K/V 噪声比**：2.15x（Key 主导有定量支撑）

---

## 第二轮审查（2026-04-03 Session 2，6 角度并行）

### 审稿人 1：EMNLP/ACL 资深审稿人（Efficient LLM Inference 方向）

**Overall Score: 5/10 | Recommendation: Borderline Reject**

#### Strengths
1. 叙事逻辑链完整自洽（原则→诊断→设计→边界）
2. K/V 消融实验严谨、GQA 架构依赖发现有独立贡献价值
3. 统计框架规范（Bootstrap CI + BH-FDR）
4. 自我批评和局限性分析充分
5. 工程完成度高（Triton kernel、9 种量化模式）

#### 致命问题
1. **INT4-RoleAlign 与 KIVI 差异极小，novelty 不足** — 共享完全相同量化格式，仅校准方式不同。PPL 退化在 1.5B/7B 上甚至劣于 KIVI（13.7% vs 12.0%、6.1% vs 5.5%），离线校准成本换来零/负收益
2. **KIVI 基线实现不完整** — 未含残差补偿等完整工程优化，所有 KIVI 对比结论建立在弱化基线上
3. **模型规模覆盖不足** — 仅 1.5B-8B，2026 年 EMNLP 需要 70B+ 验证

#### 严重问题
4. attention-KL 校准增益未被严格隔离（与 adaptive protection 混淆）
5. INT4 对称路径上 KL 校准反而恶化结果，质疑"统一目标"声称
6. 评测基准使用合成数据源，无法横向对比
7. 解码延迟全面退步（INT4 TPOT +2-2.5x）
8. chunk_size=128 可能系统性低估量化影响

#### 必须回答的 10 个问题
1. BA-guided percentile 校准相对 KIVI 无校准方案的定量改进在哪？
2. KL 散度在什么条件下是有效的校准目标？（INT4 对称失效）
3. 为什么不使用官方 LongBench/RULER？
4. Adaptive static scale 的 novelty 是什么？（取 max 太直观）
5. 完整 KIVI 实现下 INT4-RoleAlign 优势如何变化？
6. 70B+ 模型上校准成本和收益如何？
7. K/V 消融为何不含 PPL？
8. chunk_size=1 压力测试能否扩展到 7B/8B？
9. 已弃用的 inv_tau 为何占方法章节整节篇幅？
10. Needle 100% vs PPL 13.7% 退化的理论解释？

#### 缺失引用
MiKV, SqueezeLLM, FlashAttention-3, DeepSeek-V3 MLA, FP8 量化, HF quanto/bitsandbytes

### 审稿人 2：系统架构教授（高性能计算方向）

**评级: B+ / A- | 角色: 答辩委员**

#### 致命问题
1. INT4-RoleAlign 与 KIVI 核心差异不足支撑"核心贡献"定位（PPL 持平甚至略差）
2. 校准产物 v3_quick 存在已知缺陷却用于全部主实验

#### 严重问题
3. INT8 batch=1 TPOT 比 FP16 高近 2 倍，"高效推理"名不副实
4. 与工业界推理系统（vLLM/TRT-LLM/FlashInfer）完全没有对比
5. LongBench 使用合成数据，结果不可横向对比
6. 三个模型都属小模型（≤8B），缺乏大模型验证
7. INT4 核心贡献缺乏融合核函数支撑，延迟 2-2.5x

#### 应答核心策略
- 承认增量有限，强调"方法论路径"（诊断驱动）而非"点性能"
- batch=1 延迟：重新定位为"显存高效推理"，展示 batch>1 吞吐量优势
- 工业框架：定位为方法论研究（校准原则），非系统性能竞赛

---

### 审稿人 3：NLP/机器学习教授

**评级: B+ | 角色: 答辩委员**

#### CRITICAL 问题
1. KL 校准在 INT4 下反而劣于 baseline → "统一校准目标"叙事破裂
2. INT4-RoleAlign 与 KIVI 共享格式但 PPL 更差 → 贡献在哪里？
3. 3 个 ≤8B 模型能否支撑泛化性结论？

#### HIGH 问题
4. 未与 KVQuant/QuaRot/GEAR 直接对比
5. 消融实验混杂因素无法分离（KL vs adaptive vs Triton）
6. 校准产物 Q 向量缺少 layernorm + RoPE

#### 关键洞察
- "KL 在 INT4 校准上失败本身就是诊断信号"是最强防守论据
- 不要过度辩护，直面局限比强行自圆其说更获尊重

---

### 审稿人 4：工业界实践者（NVIDIA/Google 级）

**实用性评分: 4.5/10 | 核心判断: INT8 有条件可部署，INT4 暂不值得**

#### 阻碍部署的关键缺陷
1. 与 vLLM/TRT-LLM/SGLang 完全脱节，无法进入生产链路
2. batch=1 延迟翻倍（47ms vs 24ms）在低并发场景致命
3. Triton vs CUDA kernel 性能鸿沟（未利用 tensor core）
4. 缺少 prefill 阶段量化方案
5. 校准数据域偏移风险（仅 WikiText-103）
6. INT4 PPL 13.7% 退化在生产不可接受

#### 改进建议（短期）
- 补充 FP8 对比（H100 时代默认选择，论文完全未提及！）
- 补充 batch>1 端到端吞吐量
- 补充非 WikiText 域校准鲁棒性
- 定位为"可移植的方法论贡献"而非完整推理系统

#### Rebuttal 最强/最弱防守点
- **最强**: 校准样本数不敏感（B10 消融）
- **最弱**: batch=1 延迟翻倍（TRT-LLM 在 batch=1 下不退化）

---

### 审稿人 5：数学/统计教授（信息论方向）

**角色: 答辩委员 | 数学推导总体质量: 良好，无根本性错误**

#### 高优先级问题（答辩必问）
1. **M-7**: 为何用 Bootstrap 而非 t-test？（n=5 不满足正态性假设，Needle 二值指标非对称）
2. **M-8**: sign-flip 检验 n=5 最小 p=0.031，统计功效极低，"未达显著性 ≠ 无效应"
3. **M-11**: "未达统计显著性"与"无实质退化"是不同的统计声明，论文措辞混淆

#### 中优先级
4. **M-1**: KL 散度方向选择（zero-avoiding vs zero-forcing）缺乏论证
5. **M-4**: 量化噪声跨 token 独立性假设过强（per-group Scale 共享）
6. **M-5**: 临界长度 n* 推导需补充 CLT 条件说明
7. **M-9**: sign-flip 检验配对结构未显式定义

#### 低优先级
8. **M-2**: "尾部敏感性"应改为"峰值保护"
9. **M-3**: ε-截断后概率不归一
10. **M-6**: SQNR 均匀分布假设声明
11. **M-13**: p_c 到 p_K/p_V 符号过渡不清晰
12. **M-14**: 量化级别数（15/16）表述不一致

#### 整体评价
公式正确、数值验算无误。SQNR 推导和 Q 预缩放等价性最干净。主要问题在统计框架的解释和局限性声明不够显式。

---

### 审稿人 6：论文写作与学术规范教授

**写作质量评分: B+ | 角色: 答辩委员**

#### 结构问题
1. **第四章过长**（~50 页）：大量非核心消融应下沉至附录
2. **第一章与第二章叙述重叠**：1.3 节"国内外研究现状"与第二章重复
3. **结论章 \chapter* 格式问题**

#### 论证缺陷
4. **INT4-RoleAlign vs KIVI 贡献偏弱**：三个模型上 PPL 全部不优于 KIVI，需重新定位贡献
5. **Claim 1 因果归因不纯净**：KL vs adaptive vs Triton 三因素混淆
6. **KL 在 INT4 下反效果未充分解释**：为何优化反而比不优化更差？
7. **inv_tau 占 3 页但最终不用**：应大幅缩减至 1 页

#### AI 痕迹检测
- **中等程度**：核心技术内容扎实，非纯 AI 生成
- 模板化表达："完整闭环""完整论证链"出现过于频繁
- 摘要与结论高度雷同，可逐句对应
- "一言以蔽之"等口语化表达

#### 关键修改建议
- 第四章下沉 30% 内容到附录
- 第一章 1.3 节缩减为极简概述
- 摘要与结论独立撰写，不互相复制
- chunk_size=1 下 KIVI PPL=9442 的数据从附录提升到正文
- 第一章末尾明确列出三个研究问题，匹配第五章回答结构

#### 缺失引用
FlashAttention-3, FP8 KV Cache, DeepSeek-V2 MLA, AdaRound/BRECQ

---

## 第三轮审查（2026-04-03 Session 2，defense-review skill 执行）

### 审稿人 1：系统架构教授 | 评级 B+

**致命问题**：
- F-1: INT4-RoleAlign 对 KIVI 无实质指标优势，PPL 1.5B/7B 反而更差
- F-2: INT4 延迟 +2-2.5x，INT8 batch=1 也比 FP16 慢，"高效推理"名不副实

**严重问题**：S-1 校准产物缺陷 | S-2 LongBench 合成数据 | S-3 KIVI 基线不完整 | S-4 PPL 统计检验无意义 | S-5 单卡 H20 无规模化验证

**核心应答**：定位为方法论贡献（诊断驱动设计路径），不与 KIVI 做性能竞赛。batch=1 延迟→重定位为"显存高效"。

---

### 审稿人 2：NLP/ML 教授 | 评级 B+

**CRITICAL**：
- C1: KL 理论基础薄弱——无 attention-KL → output error 的形式化上下界
- C2: INT4-RoleAlign vs KIVI 增量模糊（PPL 更差、Needle 持平）

**HIGH**：H1 模型≤8B | H2 缺 KVQuant/QuaRot/GEAR 对比 | H3 校准产物缺陷 | H4 统计检验方法论问题

**核心应答**：承认数值增量有限，强调方法论路径价值。准备 sketch proof（attention-KL → output error 上界代理）。

---

### 审稿人 3：顶会审稿人 | Score 5.5/10 | Recommendation: Borderline Reject

**Strengths**：论证链完整 | 实验诚实度高 | K/V 消融设计精良 | 统计规范 | 检索/LM 解耦发现

**Major Weaknesses**：
- W1: INT4-RoleAlign vs KIVI 增量有限
- W2: KL 校准 vs 诊断功能未分离
- W3: 实验规模不足（≤8B 单 GPU）
- W4: INT4 延迟 2-2.5x

**10 个必答问题**核心：BA percentile 增量在哪？KL 诊断不可替代性？消融为何未完成？Q 向量缺陷量化？PPL 退化 vs Needle 100% 解耦机制？

---

### 审稿人 4：数学/统计教授 | 总体：正确自洽无根本错误

**高优先级**：
- P1: SQNR 公式适用条件（均匀分布假设 vs 实际高斯）需显式声明
- P2: GQA 噪声稀释等权假设 + 跨模型 sigma 一致性未验证
- P3: Bootstrap n=5 覆盖率 + 非劣性检验逻辑需集中化

**中优先级**：P4 BH-FDR 族定义 | P5 sign-flip p=0.0909 离散性 | P6 KL 信息论语义映射 | P7 ε 截断影响

**答辩必备**：为何 Bootstrap 非 t-test？n=5 功效多大？forward vs reverse KL？

---

### 审稿人 5：工业实践者 | 实用性 4.5/10

**核心判断**：INT8 有条件可部署，INT4 暂不值得

**关键缺陷**：
1. 与 TRT-LLM/vLLM/SGLang 完全脱节
2. batch=1 延迟翻倍
3. Prefill 量化缺失
4. INT4 PPL 13.7% 不可接受
5. 完全未提及 FP8

**最强建议**：重新定位为"分析/诊断工具论文"，INT4-RoleAlign 降级为验证性设计

---

### 审稿人 6：论文写作教授 | 待补充（Agent 超时未返回完整结果）

---

## 跨三轮审查的共识问题 TOP 5

| 排名 | 问题 | 提及次数 | 严重程度 |
|------|------|---------|---------|
| 1 | INT4-RoleAlign vs KIVI 差异太小 | 12/12 审稿人 | 致命 |
| 2 | 模型规模 ≤8B + 缺 SOTA 对比 | 10/12 | 严重 |
| 3 | batch=1 延迟退化 + "高效推理"名不副实 | 8/12 | 严重 |
| 4 | KL 校准增益未隔离（vs adaptive/Triton）| 7/12 | 严重 |
| 5 | 评测用合成数据 + FP8 未对比 | 6/12 | 中等 |
