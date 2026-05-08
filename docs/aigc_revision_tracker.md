# AIGC Revision Tracker

This file records paragraph-level AIGC-polish changes. Each entry maps one detector segment to one source paragraph, records the preserved claim set, review gates, verification commands, and commit hash.

## Source Reports

- HTML statistics report: `/Users/chenzilang/Downloads/main (2)/main_AIGC统计报告.html`
- Concise PDF report: `/Users/chenzilang/Downloads/main (2)/main_AIGC简洁报告.pdf`
- Original comparison PDF: `/Users/chenzilang/Downloads/main (2)/main_AIGC原文对照报告.pdf`

## Global Result Snapshot

- Overall suspected AIGC ratio: 20.38%
- Highest-risk chapters: Chinese abstract 72.0%, English abstract 72.0%, Chapter 3 32.0%, Chapter 1 24.0%, Conclusion 14.0%

## Segment 1.1

- Report segment: 1
- Source paragraph: `thesis/chapters/abstract_zh.tex`, Chinese abstract paragraph 1
- Detector excerpt begins: `长上下文推理使大语言模型的解码瓶颈...`
- Suspected segment size in report: 781 characters for the full Chinese abstract segment; this entry covers paragraph 1 only.
- Status: applied

### Diagnosis

- Main AIGC triggers: template-like opening, dense parallel structure, colon-style mechanism expansion, repeated abstract verbs such as `提出`, `作为`, `连接`, and a highly regular problem-method sentence chain.
- Rewrite goal: preserve the abstract's technical claim while making the paragraph read like the author's own research framing.
- Style constraints: avoid unnecessary colon expansion, avoid over-strong claims, use `降低缓存位宽` rather than vague `精度`, keep Chinese causal flow natural.

### Preserved Information

- Long-context decoding shifts the LLM decoding bottleneck toward KV Cache storage and memory access.
- Lower cache bit-width directly reduces memory footprint.
- Tensor-level reconstruction error is insufficient to characterize functional shift after the cache enters attention.
- Key-side perturbations can affect logits, softmax, and attention distribution.
- Value-side perturbations mainly propagate through weighted aggregation to the output representation.
- The thesis proposes a behavior-aligned KV Cache quantization framework.
- The framework treats attention distribution, aggregation output, and task behavior as shared calibration and auditing objects.
- The framework connects quantization-parameter selection, low-bit recovery, and layer-wise budget allocation.

### Review Gate

- Technical accuracy reviewer: PASS; suggested avoiding `单步计算`, `压低`, and over-strong chain wording.
- Chinese academic writing reviewer: PASS; suggested replacing `压低`, `行为读数`, and `贯通`.
- Cross-chapter consistency reviewer: PASS; no conflict with Chapters 1, 3, 4, or 5.
- Skeptical reviewer: PASS with minor revision; warned that `单步计算` narrows `计算负载`.

### Applied Revision

```tex
长上下文解码中，KV Cache 会随序列长度持续累积，大语言模型的解码瓶颈也从计算负载进一步转向缓存存储与访存开销。降低缓存位宽可以直接减少显存占用，但当量化缓存进入注意力计算后，张量级重建误差不足以说明其功能偏移。Key 侧误差可能经 logits 与 softmax 改写注意力分布；Value 侧误差则主要通过加权聚合影响输出表示。围绕这一传播差异，本文提出面向高效推理的 KV Cache 行为对齐量化框架，把注意力分布、聚合输出和任务表现作为共同的校准与审计对象，并以这些行为信号连接量化参数选择、低比特恢复和层间预算分配三个决策环节。
```

### Verification

- `git diff --check -- thesis/chapters/abstract_zh.tex docs/aigc_revision_tracker.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc zh abstract paragraph 1`

## Segment 1.2

- Report segment: 1
- Source paragraph: `thesis/chapters/abstract_zh.tex`, Chinese abstract paragraph 2
- Detector excerpt begins: `方法上，本文首先构建以 attention-distribution KL...`
- Suspected segment size in report: 781 characters for the full Chinese abstract segment; this entry covers paragraph 2 only.
- Status: applied

### Diagnosis

- Main AIGC triggers: list-like method sequencing, repeated abstract verbs such as `构建`, `提出`, `用于`, `从而形成`, and a long sentence chain that compresses three method stages into two highly regular clauses.
- Rewrite goal: keep all method objects and decision links while reducing template-like transitions and improving paragraph rhythm.
- Style constraints: keep `attention-distribution KL`, `INT8`, `INT4`, `\texttt{INT4-RoleAlign}`, `behavior-guided fixed-$k$`, and `\texttt{AutoK}` unchanged; avoid overclaiming that the allocation rule is globally optimal.

### Preserved Information

- The method starts from an INT8 baseline path calibrated with attention-distribution KL as a proxy target.
- The INT8 path establishes a reproducible behavior-fidelity anchor under a conservative bit-width.
- The thesis proposes `\texttt{INT4-RoleAlign}` for the INT4 setting.
- `\texttt{INT4-RoleAlign}` uses per-channel Key and per-token Value asymmetric formats.
- Key-side attention-ranking shift and Value-side output perturbation are treated separately.
- The rewrite keeps the boundary that the two propagation mechanisms should not be collapsed into a single reconstruction target.
- Offline calibration artifacts are summarized into layer-wise behavioral sensitivity profiles.
- The same profile supports behavior-guided fixed-$k$ allocation, comparison with positional heuristic baselines, and `\texttt{AutoK}` coverage-based budget proposals.
- The paragraph links calibration results to budget allocation without claiming cross-model universal optimality.

### Review Gate

- Technical accuracy reviewer: PASS; suggested preserving `KL as proxy target`, avoiding new `parameter entry` wording, and keeping the single-reconstruction-target boundary explicit.
- Chinese academic writing reviewer: PASS; suggested replacing the instruction-like opening and removing engineering phrases such as `供...读取`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapters 1, 3, 4, and 5, including the INT8 anchor, RoleAlign format, and allocation terminology.
- Skeptical reviewer: PASS; suggested replacing `进入 INT4 后` and replacing the abstract `evidence chain remains consistent` ending with a more concrete calibration-to-allocation link.

### Applied Revision

```tex
方法路径上，本文先在保守位宽下以 attention-distribution KL 作为代理目标构建 INT8 基准路径，建立可复核的行为保真锚点。随后在 INT4 设置下，\texttt{INT4-RoleAlign} 采用 per-channel Key 与 per-token Value 的非对称格式，分别刻画 Key 侧注意力排序偏移和 Value 侧输出扰动，避免把两类传播机制压缩为单一重建目标。离线校准产物再汇总为逐层行为敏感度画像，用于 behavior-guided fixed-$k$ 分配、位置启发式基线比较和 \texttt{AutoK} 覆盖率预算建议，由此衔接校准结果与预算分配。
```

### Verification

- `git diff --check -- thesis/chapters/abstract_zh.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc zh abstract paragraph 2`

## Segment 1.3

- Report segment: 1
- Source paragraph: `thesis/chapters/abstract_zh.tex`, Chinese abstract paragraph 3
- Detector excerpt begins: `在覆盖 Qwen2.5、LLaMA-3.1 与 Mistral...`
- Suspected segment size in report: 781 characters for the full Chinese abstract segment; this entry covers paragraph 3 only.
- Status: applied

### Diagnosis

- Main AIGC triggers: dense numerical inventory, repeated `在...上` location-style phrasing, long semicolon chains, and the English-style connector `本文因此表明`.
- Rewrite goal: preserve every experimental number and boundary while making the evidence paragraph read less like a detector-friendly result template.
- Style constraints: keep the six-model scope, all reported numbers, all model names, and the conditional nature of the system speed result; avoid expanding claims beyond the current experimental protocol.

### Preserved Information

- Experiments cover six open-source instruction models from the Qwen2.5, LLaMA-3.1, and Mistral families.
- KV Cache quantization and allocation are family-, scale-, and task-dependent.
- Qwen2.5-1.5B INT8 differs from FP16 by about `$+0.02$` in the three-task mean.
- Symmetric INT4 causes stepwise retrieval collapse on Qwen models.
- K/V role diagnosis identifies Key-side low-bit noise as the more direct instability trigger.
- Mistral-7B gives the clearest single-model `\texttt{AutoK}` support with core mean 14.76 and extend mean 15.69.
- Qwen2.5-3B shows an early-layer protection regime, with behavior-guided `$k=1$` core mean 6.90 above middle-layer heuristic 3.48.
- Qwen2.5-14B has Uniform INT4 and AutoK-cov90 core means of 7.23 and 7.15, indicating close high-performance strategies without a stable winner.
- INT4 achieves about 73.4\% KV Cache capacity reduction on four representative models.
- Fused-decode time benefit remains conditioned by `$H_{kv}$`, sequence length, and backend implementation.
- The conclusion remains that uniform bit-width compression only captures part of the KV Cache quantization problem; behavior preservation, K/V role asymmetry, and conditional allocation must be modeled together.

### Review Gate

- Technical accuracy reviewer: PASS; suggested removing `仅有` and retaining `系统评估显示` to preserve neutral evidence wording.
- Chinese academic writing reviewer: PASS; confirmed removal of `本文因此`, unnecessary colon-style expansion, and most `在...上` phrasing.
- Cross-chapter consistency reviewer: PASS; verified all key numbers against Chapter 4 tables and Chapter 5 conclusions.
- Skeptical reviewer: PASS with small revisions; requested neutral `$+0.02$` wording and a conclusion that keeps the thesis-level inference.

### Applied Revision

```tex
实验覆盖 Qwen2.5、LLaMA-3.1 与 Mistral 三个模型族的六个开源指令模型，结果显示 KV Cache 量化与预算分配具有明确的模型族、规模和任务依赖性。Qwen2.5-1.5B 的 INT8 基准路径相对 FP16 的三任务均值差约为 $+0.02$，支持其作为保守位宽下的行为保真实例；Qwen 系列的对称 INT4 出现检索阶跃崩塌，K/V 角色诊断进一步显示，Key 侧低比特噪声是更直接的失稳触发源。跨模型分配实验中，Mistral-7B 的 \texttt{AutoK} 给出最清晰的单模型支持，core mean 为 14.76，extend mean 为 15.69；Qwen2.5-3B 呈现早层保护有效区间，behavior-guided $k=1$ 的 core mean 为 6.90，高于中层 heuristic 的 3.48；Qwen2.5-14B 中 Uniform INT4 与 AutoK-cov90 的 core mean 分别为 7.23 与 7.15，说明高性能策略接近而无稳定最优。系统评估显示，INT4 路径在四个代表性模型上可实现约 73.4\% 的 KV Cache 容量压缩，但融合解码的时间收益仍受 $H_{kv}$、序列长度与后端实现共同调制。这些结果表明，统一位宽压缩只能描述 KV Cache 量化问题的一部分；更合适的结构化建模应同时纳入注意力行为保持、K/V 角色差异恢复与条件化预算分配。
```

### Verification

- `git diff --check -- thesis/chapters/abstract_zh.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc zh abstract paragraph 3`

## Segment 2.1

- Report segment: 2; also covers report segment 3 because that sentence is inside the same source paragraph.
- Source paragraph: `thesis/chapters/abstract_en.tex`, English abstract paragraph 1
- Detector excerpt begins: `Long-context inference in large language models increasingly moves...`
- Suspected segment size in report: 281 words for the full English abstract segment; this entry covers paragraph 1 only.
- Status: applied

### Diagnosis

- Main AIGC triggers: generic abstract opening, formulaic `but tensor-level... once...` contrast, template transition `To address this problem`, and an under-specified final `connecting` clause.
- Rewrite goal: keep the English abstract aligned with the revised Chinese abstract while making the motivation and mechanism flow less generic.
- Style constraints: preserve the bottleneck claim, Key/Value propagation distinction, behavior-aligned framework, three shared targets, and three connected decision stages.

### Preserved Information

- Long-context decoding shifts the decoding bottleneck from computation toward KV-cache storage and memory bandwidth.
- Reducing cache bit-width reduces memory footprint.
- Tensor-level reconstruction error alone is insufficient once the quantized cache is used by attention.
- Key-side perturbations affect logits and softmax attention distributions.
- Value-side perturbations mainly propagate through weighted aggregation into output representations.
- The thesis develops a behavior-aligned KV-cache quantization framework for efficient LLM inference.
- Attention distributions, aggregation outputs, and task behavior remain shared calibration and auditing targets.
- Quantization-parameter selection, low-bit recovery, and layer-wise budget allocation remain linked to observed functional effects.

### Review Gate

- Technical accuracy reviewer: PASS; confirmed no missing content or unsupported performance claim.
- English academic writing reviewer: PASS; suggested replacing `Perturbations on the Key side` and tightening the final sentence.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with the Chinese abstract and Chapters 1, 3, 4, and 5.
- Skeptical reviewer: initial FAIL on a weaker candidate; final candidate PASS after restoring the bottleneck claim, replacing vague `same behavioral evidence`, and using `Key-side` / `Value-side` terminology. A later compressed version was re-approved to avoid adding an English-abstract page.

### Applied Revision

```tex
During long-context decoding, KV cache growth shifts the decoding bottleneck from computation toward cache storage and memory bandwidth. Lower cache bit-width reduces the dominant cache footprint, but tensor-level reconstruction error alone does not characterize the functional deviation that appears once attention consumes a quantized cache. Key-side perturbations can alter logits and reshape softmax attention distributions, while Value-side perturbations primarily affect output representations through weighted aggregation. This thesis develops a behavior-aligned KV-cache quantization framework for efficient LLM inference, using attention distributions, aggregation outputs, and task behavior as shared calibration and auditing targets that link quantization-parameter selection, low-bit recovery, and layer-wise budget allocation.
```

### Verification

- `git diff --check -- thesis/chapters/abstract_en.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc en abstract paragraph 1`

## Segment 2.2

- Report segment: 2
- Source paragraph: `thesis/chapters/abstract_en.tex`, English abstract paragraph 2
- Detector excerpt begins: `The framework builds an INT8 canonical path calibrated...`
- Suspected segment size in report: 281 words for the full English abstract segment; this entry covers paragraph 2 only.
- Status: applied

### Diagnosis

- Main AIGC triggers: repeated framework-method sentence pattern, `It then introduces` sequencing, passive summarization, and a generic `consistent evidence chain` ending.
- Rewrite goal: preserve the method chain while removing mechanical step framing and making the calibration-to-allocation relation more concrete.
- Style constraints: preserve INT8 canonical path, attention-distribution KL proxy, conservative bit-width anchor, `\texttt{INT4-RoleAlign}`, per-channel Key and per-token Value formats, separate Key/Value error channels, behavior-guided fixed-$k$, positional heuristic comparison, and `\texttt{AutoK}` coverage proposals.

### Preserved Information

- INT8 canonical path uses the attention-distribution KL proxy.
- INT8 establishes a reproducible fidelity anchor under a conservative bit-width.
- `\texttt{INT4-RoleAlign}` is used for INT4 quantization.
- `\texttt{INT4-RoleAlign}` uses role-aware asymmetric quantization with per-channel Key and per-token Value formats.
- Key-side attention-ranking shifts and Value-side output perturbations are separated.
- The two error channels are not reduced to a single reconstruction objective.
- The same offline calibration artifacts support layer-wise behavioral sensitivity profiles.
- The profiles support behavior-guided fixed-$k$ allocation, positional heuristic comparison, and `\texttt{AutoK}` coverage-based budget proposals.
- Calibration evidence is linked to allocation decisions without claiming global optimality.

### Review Gate

- Technical accuracy reviewer: PASS; suggested `For INT4 path` and retaining the `same offline calibration artifacts` emphasis.
- English academic writing reviewer: initial FAIL on the candidate opening `three linked steps`; final wording removes that frame and direct `First/then` sequencing.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with the Chinese abstract and Chapters 1, 3, 4, and 5.
- Skeptical reviewer: PASS with suggestions; warned that `resulting offline calibration artifacts` might imply INT4-only artifacts, so the final version keeps `same offline calibration artifacts`.

### Applied Revision

```tex
An INT8 canonical path uses the attention-distribution KL proxy to establish a reproducible fidelity anchor at a conservative bit-width. For INT4 quantization, \texttt{INT4-RoleAlign} uses role-aware asymmetric quantization with per-channel Key and per-token Value formats, separating Key-side attention-ranking shifts from Value-side output perturbations rather than reducing both error channels to a single reconstruction objective. The same offline calibration artifacts further support layer-wise behavioral sensitivity profiles for behavior-guided fixed-$k$ allocation, positional heuristic comparison, and \texttt{AutoK} coverage-based budget proposals, linking calibration evidence to allocation decisions.
```

### Verification

- `git diff --check -- thesis/chapters/abstract_en.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc en abstract paragraph 2`

## Segment 2.3

- Report segment: 2
- Source paragraph: `thesis/chapters/abstract_en.tex`, English abstract paragraph 3
- Detector excerpt begins: `Experiments across six open-source instruction models...`; report segment 3 excerpt begins `Overall, this thesis formulates...`
- Suspected segment size in report: 281 words for the full English abstract segment; this entry covers paragraph 3 only.
- Status: applied

### Diagnosis

- Main AIGC triggers: dense result inventory, long semicolon chain, repeated `with...` constructions, and a generic final thesis-summary sentence.
- Rewrite goal: keep every numerical result and boundary while reducing detector-friendly list rhythm.
- Style constraints: preserve model scope, all reported numbers, the Qwen-only INT4 collapse boundary, the Mistral-7B `\texttt{AutoK}` support claim, the Qwen2.5-3B early-layer result, the Qwen2.5-14B no-stable-winner result, and the conditional nature of system speedups.

### Preserved Information

- Experiments cover six open-source instruction models from Qwen2.5, LLaMA-3.1, and Mistral families.
- KV-cache quantization and allocation are strongly family-, scale-, and task-dependent.
- Qwen2.5-1.5B INT8 canonical path differs from FP16 by about `$+0.02$` in the three-task mean.
- Symmetric INT4 causes stepwise retrieval collapse on Qwen models.
- K/V diagnostics identify low-bit Key noise as the more direct source of instability.
- Mistral-7B gives the clearest single-model support for `\texttt{AutoK}` with core mean 14.76 and extend mean 15.69.
- Qwen2.5-3B shows an early-layer protection regime, with behavior-guided `$k=1$` core mean 6.90 versus 3.48 for the middle-layer heuristic.
- Qwen2.5-14B shows no stable winner, with Uniform INT4 and AutoK-cov90 core means 7.23 and 7.15.
- System measurements show about 73.4\% KV-cache capacity reduction for INT4 on four representative models.
- Fused-decode speedups remain conditioned by `$H_{kv}$`, sequence length, and backend implementation.
- The thesis-level conclusion remains a structured formulation of behavior preservation, K/V role asymmetry, and bit-width allocation under model- and task-dependent regimes.

### Review Gate

- Technical accuracy reviewer: PASS; suggested restoring formal `provides the clearest single-model support` and avoiding interpretive `close`.
- English academic writing reviewer: PASS; suggested `provides`, `depend on`, and keeping terminology coherent.
- Cross-chapter consistency reviewer: PASS; checked every key number and boundary against the Chinese abstract and Chapters 3--5.
- Skeptical reviewer: initial FAIL because the first candidate weakened `strongly`, changed `role` to `use`, and used a generic `Taken together` ending. The applied version restores the stronger claim and thesis-level formulation.

### Applied Revision

```tex
Experiments across six open-source instruction models from the Qwen2.5, LLaMA-3.1, and Mistral families show that KV-cache quantization and allocation are strongly family-, scale-, and task-dependent. On Qwen2.5-1.5B, the INT8 canonical path differs from FP16 by about $+0.02$ in the three-task mean, supporting its role as a conservative fidelity case. Symmetric INT4 causes stepwise retrieval collapse on Qwen models, and K/V role diagnostics identify low-bit Key noise as the more direct source of instability. In cross-model allocation, Mistral-7B provides the clearest single-model support for \texttt{AutoK}, with a core mean of 14.76 and an extend mean of 15.69. Qwen2.5-3B reveals an early-layer protection regime, where behavior-guided $k=1$ reaches a core mean of 6.90 compared with 3.48 for the middle-layer heuristic; Qwen2.5-14B shows no stable winner, with Uniform INT4 and AutoK-cov90 reaching core means of 7.23 and 7.15. System measurements show about 73.4\% KV-cache capacity reduction for the INT4 path on four representative models, while fused-decode speedups remain conditioned by $H_{kv}$, sequence length, and backend implementation. Overall, this thesis formulates KV-cache quantization as a structured problem of preserving attention behavior, respecting K/V role asymmetry, and allocating bit-width under model- and task-dependent regimes.
```

### Verification

- `git diff --check -- thesis/chapters/abstract_en.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc en abstract paragraph 3`

## Segment 4.1

- Report segment: 4
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 25
- Detector excerpt begins: `进入注意力计算后，这个前提并不总稳固...`
- Suspected segment size in report: 296 characters for segment 4; this entry covers the first source paragraph in that segment.
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-style mechanism expansion, highly regular `前提--然而--因此` reasoning, and abstract connector density.
- Rewrite goal: retain the motivation for behavior-based calibration while making the paragraph less template-like.
- Style constraints: preserve MSE, percentile clipping, the tensor-closeness working premise, softmax nonlinearity, Key perturbation, possible normalization absorption, and the static-threshold limitation.

### Preserved Information

- Current KV Cache calibration often still targets numerical reconstruction error.
- Typical examples include MSE loss and percentile-based clipping.
- These methods rely on a working premise that closer tensors imply behavior closer to the full-precision path.
- The premise is not always valid after entering attention computation.
- Softmax nonlinearity can turn small Key perturbations into visible changes in attention probability.
- Some numerically larger errors may be partially absorbed by normalization.
- Tensor error magnitude and downstream functional deviation are difficult to map one-to-one.
- Distributional differences across layers, heads, and context positions weaken static threshold explanations.

### Review Gate

- Technical accuracy reviewer: PASS; flagged `反而会` as too strong and suggested restoring `也可能`.
- Chinese academic writing reviewer: PASS; suggested replacing unclear pronouns and avoiding casual connectors.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 3 error decomposition and Chapter 4 boundary conditions.
- Skeptical reviewer: initial FAIL on over-strong `反而会`, `继续削弱`, and `由此看`; final applied version uses `也可能`, `进一步削弱`, and a direct `因此`.

### Applied Revision

```tex
当前 KV Cache 量化的校准目标仍多落在数值重建误差上，常见做法包括 MSE 损失和基于分位数的裁剪。这类方法通常沿用一个工作前提，即张量越接近原值，模型行为也越接近全精度路径。进入注意力计算后，这一前提并不总是成立：softmax 的非线性可能把较小的 Key 扰动转化为注意力概率的明显变化，而某些数值上更大的误差也可能在归一化中被部分吸收。因此，张量误差大小很难与下游功能偏移建立稳定的一一对应关系；层、头和上下文位置带来的分布差异，也会进一步削弱静态阈值的解释力。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 motivation paragraph 1`

## Segment 4.2

- Report segment: 4
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 27
- Detector excerpt begins: `因此，KV Cache量化的困难不只是继续调节超参数...`
- Suspected segment size in report: 296 characters for segment 4; this entry covers the second source paragraph in that segment.
- Status: applied

### Diagnosis

- Main AIGC triggers: repeated `因此`, colon-style enumeration, generic statement of viewpoint, and highly regular problem-to-claim structure.
- Rewrite goal: keep the same technical claim while removing template connectors and making the paragraph read as an authorial motivation rather than a slogan.
- Style constraints: avoid unnecessary colon usage, avoid `本文因此`, preserve the original strength of the `stable and usable` claim, and avoid adding unvalidated mechanism claims.

### Preserved Information

- KV Cache quantization is not only a matter of tuning hyperparameters or reducing reconstruction error.
- The relevant deviation appears after quantization error enters attention computation.
- The paragraph keeps the three observable effects: attention distribution reordering, aggregation-output deviation, and task-behavior change.
- Long-context and low-bit settings make the issue more salient.
- Same-magnitude numerical perturbations may have different consequences when they appear in different layers, attention heads, or cache roles.
- The final claim remains that minimizing global numerical error alone may not guarantee stable and usable inference.

### Review Gate

- Technical accuracy reviewer: multiple rounds flagged over-strong mechanism additions such as fixed `logits` and `Value` propagation chains; the applied version removes those additions.
- Chinese academic writing reviewer: flagged `它需要通过...来观察`, `本文认为`, and `作用于 Key 与 Value 等缓存角色` as unnatural; the applied version uses direct prose and `不同缓存角色`.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with the preceding softmax discussion, the following three-observable definition, and Chapter 3 K/V role decomposition.
- Skeptical reviewer: flagged concept drift around `内部计算路径`, `通常不足以说明`, and narrowed task metrics; the applied version avoids these terms and preserves the original `稳定和可用` boundary.

### Applied Revision

```tex
KV Cache 量化的困难并不只是继续调节超参数或降低重建误差。误差进入注意力计算以后，推理过程中实际暴露出来的是行为偏移，而不是孤立的张量差值。具体来看，这种偏移会体现为注意力分布是否被重排、聚合输出是否偏离，以及任务行为是否随之改变。长上下文和低比特设置会让这种差异更加突出；同一量级的数值扰动，出现在不同层、不同注意力头，或不同缓存角色中时，可能产生截然不同的后果。因此，单纯追求全局数值误差最小，不一定能保证模型在推理时保持稳定和可用。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 motivation paragraph 2`

## Segment 5.1

- Report segment: 5
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 41
- Detector excerpt begins: `长上下文推理放大了缓存显存和访存压力...`
- Suspected segment size in report: 298 characters for segment 5; this entry covers the KV Cache quantization related-work paragraph.
- Status: applied

### Diagnosis

- Main AIGC triggers: compact list of three papers, generic `这些工作说明`, and a broad final audit question compressed into one sentence.
- Rewrite goal: keep the literature positioning while making the paragraph more specific about why KV Cache differs from weight and activation quantization.
- Style constraints: avoid over-claiming K/V statistical differences as a forced consequence of long context, align KVQuant with Chapter 2, and keep Key/Value perturbation paths separate.

### Preserved Information

- KV Cache-specific quantization moves the discussion to the cache state itself.
- Long-context inference increases KV Cache memory footprint with sequence length and adds sustained bandwidth pressure.
- K/V statistical differences matter for quantization-format design.
- KIVI is positioned around K/V distribution differences and heterogeneous quantization axes.
- KVQuant is positioned around extreme low-bit cache representation with codebook design, Pre-RoPE Key quantization, and outlier handling.
- ZipCache is positioned around token-importance-driven differential cache compression.
- Cache compression cannot simply reuse weight or activation quantization assumptions.
- The final research question remains how calibration objectives and format choices should be audited once cache perturbations enter attention behavior.

### Review Gate

- Technical accuracy reviewer: initial candidates failed when KVQuant was described as generic `误差补偿`; final wording uses non-uniform codebook, Pre-RoPE Key quantization, and outlier handling.
- Chinese academic writing reviewer: flagged `进入...后`, `在这一基础上`, and `接受审计` as unnatural; the applied version avoids those patterns.
- Cross-chapter consistency reviewer: PASS after alignment with Chapter 2 KIVI/KVQuant/ZipCache wording and Chapter 3 Key/Value propagation paths.
- Skeptical reviewer: flagged a causal jump from long context to K/V statistical difference; the applied version separates memory/bandwidth pressure from K/V format-difference motivation.

### Applied Revision

```tex
讨论转向 KV Cache 专属量化时，关注点也从静态参数和前向过程中的瞬时激活，转到解码过程中持续累积的缓存状态。长上下文推理下，KV Cache 的显存占用随序列长度增长，缓存读写也会带来持续的带宽压力。与此同时，Key 与 Value 的统计差异提示同质化压缩格式可能不足以覆盖二者差异。KIVI~\cite{liu2024kivi} 以 K/V 分布差异和异构量化轴为设计依据，KVQuant~\cite{hooper2024kvquant} 围绕极低比特缓存表示引入非均匀码本、Pre-RoPE Key 量化与异常值处理，ZipCache~\cite{he2024zipcache} 则沿 token 重要性组织差异化缓存压缩。这些工作从不同角度表明，KV Cache 压缩需要引入区别于权重或激活量化的设计约束。本文进一步追问，Key 侧扰动经由 attention scores 和 softmax 改变权重分配、Value 侧扰动经由加权聚合影响输出表示后，校准目标与格式选择应由哪些行为信号来检验，又应受哪些边界条件约束。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 kv related work paragraph`

## Segment 5.2

- Report segment: 5
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 43
- Detector excerpt begins: `高效推理系统从另一侧缓解长上下文部署压力...`
- Suspected segment size in report: 298 characters for segment 5; this entry covers the high-efficiency inference systems paragraph.
- Status: applied

### Diagnosis

- Main AIGC triggers: defensive `不是替代关系` phrasing, colon-style explanation, and a compact `前者/后者` contrast.
- Rewrite goal: retain the system-quantization complementarity while making the boundary of this thesis explicit.
- Style constraints: avoid over-claiming stable system speedups, avoid implying production-level scheduler integration, and keep the final research question close to `可用的推理行为`.

### Preserved Information

- Efficient inference systems help relieve long-context deployment pressure.
- FlashAttention reduces intermediate-memory traffic through tiled attention computation.
- PagedAttention uses cache paging to reduce memory fragmentation and improve cache utilization.
- System optimization and KV Cache quantization act at different layers and are complementary rather than substitutable.
- System work improves attention execution and cache management.
- KV Cache quantization reduces the storage cost of cache representations.
- Low-bit K/V still enters decode-time attention computation and introduces dequantization, unpacking, GQA head mapping, and backend implementation overhead.
- The final research question remains whether compressed KV Cache preserves usable inference behavior in the actual decode attention path.

### Review Gate

- Technical accuracy reviewer: initial candidates failed when they introduced broad `stable system benefit` claims; the applied version removes that claim.
- Chinese academic writing reviewer: flagged repeated `互补`, `交汇点在于`, and `正是这一步`; the applied version uses direct prose.
- Cross-chapter consistency reviewer: PASS after adding decode-stage overhead terms aligned with Chapter 2/3.
- Skeptical reviewer: flagged `缓存调度路径` as too close to production scheduler scope; the applied version uses `decode 注意力执行路径` instead.

### Applied Revision

```tex
相关系统优化也在缓解长上下文部署压力。FlashAttention~\cite{dao2022flashattention,dao2024flashattention2} 通过分块注意力计算减少中间结果访存，分页注意力~\cite{kwon2023vllm} 则借助缓存分页缓解显存碎片并提高缓存利用率。这些系统层优化与 KV Cache 量化并不冲突，而是作用在不同层面。系统优化改善注意力执行和缓存管理，量化则降低缓存表示本身的存储成本。在 decode 阶段，低位宽 K/V 仍要参与注意力计算，并引入反量化、解包、GQA 头映射和后端实现开销。本文关注的是，压缩后的 KV Cache 在 decode 注意力执行路径中是否仍能保持可用的推理行为。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 systems related work paragraph`

## Segment 6.1

- Report segment: 6
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 70
- Detector excerpt begins: `后文围绕这条主线展开...`
- Suspected segment size in report: 259 characters for segment 6; this entry covers the chapter roadmap paragraph.
- Status: applied

### Diagnosis

- Main AIGC triggers: textbook-like chapter roadmap, semicolon chain, and repetitive `第二章/第三章/第四章/第五章` clauses in one sentence.
- Rewrite goal: keep the chapter responsibilities unchanged while using shorter sentences and a less mechanical route-map structure.
- Style constraints: preserve `与本文直接相关`, preserve the positioning role of Chapter 2, preserve `后续扩展空间`, and avoid adding new chapter claims.

### Preserved Information

- Later chapters follow the same main problem chain.
- Chapter 2 reviews model quantization, KV Cache compression, and efficient inference systems directly related to this thesis.
- Chapter 2 clarifies how this thesis connects to those research lines.
- Chapter 3 provides method design, behavior proxies, path instances, and budget allocation.
- Chapter 4 evaluates INT8 baseline fidelity, low-bit recovery, cross-model structural differences, and `\texttt{AutoK}` budget proposals.
- Chapter 5 summarizes contributions, scope of applicability, and future extension space.

### Review Gate

- Technical accuracy reviewer: flagged `直接相邻` as too narrow and `后续扩展方向` as less faithful than `后续扩展空间`; the applied version restores both meanings.
- Chinese academic writing reviewer: flagged `给出本文接续这些路线的位置` and `用实验读数检验`; the applied version uses `说明...承接关系` and `通过实验结果考察`.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
后续章节按问题链条展开。第二章梳理模型量化、KV Cache 压缩和高效推理系统中与本文直接相关的工作，说明本文与这些研究路线的承接关系。第三章进入方法设计，定义行为代理，并给出路径实例与预算分配机制。第四章通过实验结果考察 INT8 基准保真、低比特恢复、跨模型结构差异和 \texttt{AutoK} 预算建议。第五章收束全文，归纳贡献、适用范围与后续扩展空间。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 chapter roadmap`

## Segment 6.2

- Report segment: 6
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 72
- Detector excerpt begins: `以注意力行为保持重新界定 KV Cache量化对象...`
- Suspected segment size in report: 259 characters for segment 6; this entry covers the first contribution paragraph.
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-style enumeration, `这样处理之后` transition, and compact `前者/后者` contrast.
- Rewrite goal: preserve the contribution claim while making the paragraph read as a direct research-position statement.
- Style constraints: keep the existing contribution heading style, avoid weakening the `behavior carrier` definition, and avoid rewriting the shared-evidence relation into a wrong calibration/allocation dependency.

### Preserved Information

- Attention-behavior preservation redefines the object of KV Cache quantization.
- Quantized cache is treated as a behavior carrier inside the attention computation path.
- The three observable effects remain attention-distribution change, Value-aggregated output-representation shift, and task-behavior fluctuation.
- Calibration and budget allocation use the same group of behavioral evidence.
- The calibration layer uses this evidence to choose quantization parameters.
- The budget-allocation layer uses this evidence to judge which layers or roles need more protection.

### Review Gate

- Technical accuracy reviewer: first candidate failed because it weakened the `behavior carrier` definition; final candidate restores it and passed.
- Chinese academic writing reviewer: first candidate failed due to mechanical repetition; final candidate passed after removing the repeated evidence phrase.
- Cross-chapter consistency reviewer: PASS; the final wording does not reverse the calibration-profile-allocation relationship.
- Skeptical reviewer: earlier candidates failed due to over-abstract `evidence chain` wording; final candidate passed.

### Applied Revision

```tex
\noindent\textbf{以注意力行为保持重新界定 KV Cache 量化对象。} 本文把量化后的缓存视为注意力计算路径中的行为载体，关注它在行为层面呈现的三类可观测变化，包括注意力分布变化、Value 聚合后的输出表示偏移，以及任务表现波动。这组行为证据在校准层用于选择量化参数，在预算分配层用于判断哪些层或角色更需要保护。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 behavior-object contribution`

## Segment 7.1

- Report segment: 7
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 74
- Detector excerpt begins: `建立从 INT8 基准路径到低比特恢复的可复核实例链...`
- Suspected segment size in report: 416 characters for segment 7; this entry covers the second contribution paragraph.
- Status: applied

### Diagnosis

- Main AIGC triggers: stacked contribution nouns, `承担...锚点`, `进一步把...转写`, and a long system-support sentence.
- Rewrite goal: keep the instance-chain contribution intact while replacing abstract layering with concrete research actions.
- Style constraints: preserve the INT8 baseline role, low-bit RoleAlign role, AutoK budget-proposal role, and the bounded system-support scope.

### Preserved Information

- The paragraph still claims a reproducible chain from INT8 baseline to low-bit recovery.
- INT8 remains the conservative-bit-width fidelity reference.
- The INT8 path still tests whether behavior-guided calibration preserves near-full-precision task behavior under controlled settings.
- `\mbox{INT4-RoleAlign}` still uses Key/Value role differences in attention ranking and output aggregation.
- The low-bit path still supports instability analysis and path instantiation.
- `\texttt{AutoK}` still reuses the same behavioral sensitivity profile to generate budget proposals.
- Triton kernel, offline calibration artifacts, and online inference pipeline remain the system-support layer.
- The system-support claim is bounded to execution and review entry points under the current experimental protocol.

### Review Gate

- Technical accuracy reviewer: early candidate failed for narrowing `full precision` to `FP16`; final candidate restores the original boundary and passed.
- Chinese academic writing reviewer: flagged `任务读数`, repeated `支撑`, and vague `路径实例`; final candidate uses `任务表现`, role-contrast diagnostics, and a cleaner system-support sentence.
- Cross-chapter consistency reviewer: flagged an overbroad Triton-chain reading; final candidate bounds Triton and pipeline support to execution and review entry points.
- Skeptical reviewer: PASS after the candidate clarified the roles of INT8, `\mbox{INT4-RoleAlign}`, `\texttt{AutoK}`, and the system-support layer.

### Applied Revision

```tex
\noindent\textbf{建立从 INT8 基准路径到低比特恢复的可复核实例链。} INT8 基准路径先在保守位宽下提供保真参照，检验行为引导校准能否在受控设置中维持接近全精度的任务表现。进入低比特位宽后，\mbox{INT4-RoleAlign} 把 Key 参与注意力排序、Value 参与输出聚合的角色差异纳入诊断过程，用 K/V 角色对照支撑失稳分析与路径实例。\texttt{AutoK} 复用同源行为敏感度画像，生成预算建议。Triton~\cite{tillet2019triton} kernel、离线校准产物和在线推理管线属于系统支撑层，负责当前实验协议下的执行接口与复核入口。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 instance-chain contribution`

## Segment 7.2

- Report segment: 7
- Source paragraph: `thesis/chapters/ch1_introduction.tex`, line 76
- Detector excerpt begins: `识别跨模型预算策略的适用区间...`
- Suspected segment size in report: 416 characters for segment 7; this entry covers the third contribution paragraph.
- Status: applied

### Diagnosis

- Main AIGC triggers: dense label stacking, compact `在这一读法下` transition, and a long semicolon sentence.
- Rewrite goal: keep every named phenomenon while making the contribution auditable through Chapter 4 tables and figures.
- Style constraints: do not turn `\texttt{AutoK}` into a cross-model universal rule, do not make `\texttt{heuristic}` universally strong, and keep the comparison bounded to the tested setting.

### Preserved Information

- The paragraph still claims identification of cross-model budget-strategy applicability regions.
- The comparison remains tied to model family, parameter scale, task condition, and high-performance strategy regions.
- `\texttt{heuristic}` strong-baseline behavior is preserved.
- Key-layer deviation is preserved, now linked to observed profile-level quality decline.
- `\texttt{AutoK}` remains a model-level budget candidate generator, not a universal decision rule.
- Early-layer protection and high-performance cluster coexistence are both retained.
- The scope remains bounded by Chapter 4 evidence.
- The revision adds explicit audit anchors to Section~`\ref{sec:ch4-rq3}`, Table~`\ref{tab:ch4-regime-main}`, Figure~`\ref{fig:ch4-regime-heatmap}`, Table~`\ref{tab:ch4-profile-a}`, and Table~`\ref{tab:ch4-profile-b}`.

### Review Gate

- Technical accuracy reviewer: early candidates failed when they introduced new model-specific claims or narrowed the original claim too much; final candidate passed with explicit Chapter 4 anchors.
- Chinese academic writing reviewer: flagged abstract phrases such as `条件化结构`, `读数限定`, and repeated label stacking; final candidate uses concrete table/figure references and clearer sentence boundaries.
- Cross-chapter consistency reviewer: PASS; the final wording matches Chapter 4 and Chapter 5 boundaries on same-order budget comparison, `\texttt{AutoK}` as a candidate generator, and no unified ranking.
- Skeptical reviewer: repeatedly requested auditability for the high-performance region and 97\% near-cluster rule; final candidate defines the rule through Figure~`\ref{fig:ch4-regime-heatmap}` and passed.

### Applied Revision

```tex
\noindent\textbf{识别跨模型预算策略的适用区间。} 第四章第~\ref{sec:ch4-rq3}~节把跨模型分配结果放在同量级 \texttt{INT4} 预算带内比较，表~\ref{tab:ch4-regime-main} 使用 NarrativeQA、HotpotQA 与 GovReport 的三任务均值，图~\ref{fig:ch4-regime-heatmap} 用每行最高落点与达到该行最佳值 97\% 以上的近簇标出各模型的高性能区间。相关结论只对应本文测试的模型族、参数规模和任务组合，不外推为统一策略排名。\texttt{heuristic} 在多个被测试组合中表现为强基线；当保护层集合偏离高敏感层时，本文剖面结果也观察到质量下降。\texttt{AutoK} 在这里承担模型级预算候选生成器角色，而不是跨模型统一最优规则。早层保护、高性能簇共存等现象，由表~\ref{tab:ch4-profile-a}、表~\ref{tab:ch4-profile-b} 和适用区间图共同限定其成立范围。
```

### Verification

- `git diff --check -- thesis/chapters/ch1_introduction.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch1 budget-regime contribution`

## Segment 8

- Report segment: 8
- Source paragraph: `thesis/chapters/ch2_related_work.tex`, line 91
- Detector excerpt begins: `本文的后续探索中，INT8 和对称INT4并不承担同一个功能...`
- Suspected segment size in report: 311 characters.
- Status: applied

### Diagnosis

- Main AIGC triggers: long explanatory chain, repeated `用来...`, and over-compact storage/behavior boundary.
- Rewrite goal: preserve the INT8/INT4 functional split while making grid, payload, and behavior-validity boundaries more explicit.
- Style constraints: replace inappropriate `精度继续下降` with a bit-width expression, preserve `stable closure` and `确定可行后`, and avoid treating capacity reduction as path usability.

### Preserved Information

- `\texttt{INT8}` and symmetric `\texttt{INT4}` serve different roles in later chapters.
- `\texttt{INT8}` remains the conservative-bit-width check for behavior calibration, offline parameters, and online execution-path stability.
- Symmetric `\texttt{INT4}` remains the stronger low-bit stress point for observing attention-behavior instability.
- `\texttt{INT8}` symmetric quantization still uses $[-127,127]$ with 255 discrete levels.
- Symmetric `\texttt{INT4}` still uses $[-7,7]$ with 15 discrete levels.
- The discrete-level count difference remains approximately 17 times.
- `\texttt{INT4}` bit-packing still packs two 4-bit integers into one byte.
- The FP16-to-INT4 storage comparison remains approximately $1/4$, now explicitly scoped to K/V main payload.
- The revision preserves the boundary that capacity savings matter only when attention distribution, aggregation output, and task behavior remain usable.
- The sequence remains `\texttt{INT8}` stability check first, then symmetric `\texttt{INT4}` to expose possible Key-side functional breakpoints.

### Review Gate

- Technical accuracy reviewer: first candidate failed for weakening `stable closure` and omitting `确定可行后`; final candidate restores both and passed.
- Chinese academic writing reviewer: flagged `容量下降` and an awkward integer-grid sentence; final candidate uses `存储占用降低` and direct grid wording.
- Cross-chapter consistency reviewer: PASS; the final wording preserves the INT8 baseline, symmetric INT4 stress point, and Key-side breakpoint relation.
- Skeptical reviewer: initially flagged the $1/4$ capacity claim as too broad; final candidate scopes it to K/V main bit-packed payload and notes scale/metadata/alignment overhead.

### Applied Revision

```tex
后文使用 \texttt{INT8} 和对称 \texttt{INT4} 时，二者承担的检查任务不同。\texttt{INT8} 位宽较保守，用来检查行为校准、离线参数和在线执行路径能否稳定闭环；对称 \texttt{INT4} 提供更强的低比特压力，用来观察位宽继续压低后注意力行为最先在哪里失稳。二者的差别首先体现在整数网格。\texttt{INT8} 对称量化使用 $[-127,127]$ 的整数范围，共有 255 个离散等级；对称 \texttt{INT4} 只保留 $[-7,7]$，对应 15 个离散等级，离散等级数量约相差 17 倍。只按 K/V 主数据的 bit-packed 载荷计算时，\texttt{INT4} 可将两个 4 位整数写入同一个字节，使 KV Cache 占用约为 FP16 的 $1/4$；实际系统还会受到 scale、metadata 和对齐开销影响。这种存储占用降低只有在注意力分布、聚合输出和任务行为仍可保持时才有意义。若这些行为已经明显偏离，低位宽缓存即使节省显存，也难以作为有效的推理路径。因此，后文先用 \texttt{INT8} 验证行为引导校准和执行路径的稳定性，确定可行后，再用对称 \texttt{INT4} 暴露 Key 侧位宽降低可能触发的功能断点，把容量收益和行为可用性分开判断。
```

### Verification

- `git diff --check -- thesis/chapters/ch2_related_work.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 99-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch2 symmetric quantization roles`

## Segment 9

- Report segment: 9
- Source paragraph: `thesis/chapters/ch2_related_work.tex`, lines 108--110
- Detector excerpt begins: `在张量均值偏离零点或维度统计特征差异较大的情形下...`
- Suspected segment size in report: 321 characters.
- Status: applied

### Diagnosis

- Main AIGC triggers: abstract transition phrases, repeated `更敏感` pattern, `在 KV Cache 上` construction, and a compressed `softmax 排序` mechanism.
- Rewrite goal: preserve the asymmetric-quantization motivation while making the zero-point, K/V parameter freedom, quantization axis, and attention-path mechanism more precise.
- Style constraints: avoid unnecessary parentheses and colon-style unfolding, avoid `在 KV Cache 上`, and keep the discussion in Chinese academic order rather than English-style connective order.

### Preserved Information

- Nonzero-centered tensors and dimension-wise statistical differences remain the motivation for asymmetric quantization.
- Zero-point adjustment remains the mechanism by which the representable integer range better matches shifted distributions.
- Asymmetric quantization remains tied to the K/V role-diagnosis path.
- Key-side channel-scale differences and Value-side sequence-wise dynamic range remain the two named statistical concerns.
- Independent zero-points and scales remain the way to avoid forcing Key and Value into one shared parameter set.
- Quantization-axis choice still governs how error is distributed across dimensions.
- Per-channel quantization remains tied to channel-direction scale differences.
- Per-token quantization remains tied to sequence or position-related dynamic-range changes.
- Key still affects attention logits, relative ordering, and the subsequent softmax weight distribution.
- Value remains aggregated under attention weights.
- Later discussion still needs to state bit-width, K/V side, and channel/token allocation axis together.

### Review Gate

- Technical accuracy reviewer: first and later candidates passed; final candidate keeps the conditional boundary around asymmetric-range utilization and the logits-to-softmax mechanism.
- Chinese academic writing reviewer: initial candidate failed for weakening `K/V 角色诊断`, using `后续讨论因此`, and retaining some template-like phrasing; final candidate passed after restoring `角色诊断`, using `这一性质`, fixing `更适合适配`, and removing `在 KV Cache 上`.
- Cross-chapter consistency reviewer: PASS; final wording aligns with the later per-channel Key and per-token Value path without claiming an early empirical advantage.
- Skeptical reviewer: first candidate failed for over-strong zero-point, K/V, axis, and `softmax 排序` claims; final candidate passed after adding calibration/clipping scope, `更突出地表现为`, and a logits/softmax mechanism description.

### Applied Revision

```tex
当张量均值偏离零点，或不同维度的统计特征差异较大时，非对称量化通过零点调整实数值与整数编码之间的对齐关系，使可表示区间更贴合非零中心分布。在同一校准和截断口径下，这通常比对称量化更能利用有限整数范围。这一性质为后文的 K/V 角色诊断提供单独的参数化入口。本文关注的统计差异中，Key 侧更突出地表现为通道尺度差异，Value 侧更突出地表现为沿序列变化的动态范围；二者可以在量化参数层面由独立的零点与缩放因子分别刻画，而不必压进同一组共享参数。

量化轴会影响误差在不同维度上的分布方式。逐通道量化把缩放因子绑定到通道方向，更适合吸收通道间尺度差异；逐 token 量化把缩放因子绑定到时序方向，更适合刻画位置相关的动态范围变化。对 KV Cache 而言，这种轴向选择会影响误差进入不同计算角色的方式。Key 通过 $\bq\bK^\top$ 影响 attention logits 及其相对次序，再经 softmax 转化为权重分布；Value 则在这些权重下被加权聚合。后续讨论不只报告使用多少 bit，还会同时说明 bit 落在 K 还是 V 一侧、沿通道还是沿 token 分配。这样可以更清楚地呈现位宽、功能角色与量化粒度之间的关系。
```

### Verification

- `git diff --check -- thesis/chapters/ch2_related_work.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 100-page PDF
- Page-count note: this paragraph expansion shifted the generated PDF from 99 to 100 pages; no compile failure or reference error was introduced.
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch2 asymmetric quantization axes`

## Segment 10

- Report segment: 10
- Source paragraph: `thesis/chapters/ch2_related_work.tex`, lines 132--135
- Detector excerpt begins: `另一条思路先识别哪些缓存内容更值得保护...`
- Suspected segment size in report: 254 characters.
- Status: applied

### Diagnosis

- Main AIGC triggers: rigid two-route summary, repeated `精度` phrasing, broad `极端压缩或离散化路线`, and a negative closing sentence around one-time compression-ratio optimization.
- Rewrite goal: keep the related-work mapping while making the paragraph more precise about what each family contributes to low-bit KV Cache preservation.
- Style constraints: use positive bounded academic phrasing, avoid overclaiming a field-level shift, and keep the next subsection title aligned with the paper's boundary between cache management and quantization.

### Preserved Information

- The paragraph still presents low-bit recovery work as two neighboring lines.
- QuaRot, GEAR, and QServe remain the direct error-buffering or system-path group.
- ZipCache, IntactKV, and SKVQ remain the content-protection or differentiated-quantization group.
- Outlier Tokens Tracing, Atom, and QJL remain boundary references collected in Table~`\ref{tab:ch2-kv-comparison}`.
- The revision preserves the idea that low-bit recovery is not reducible to average compression ratio.
- The paragraph still motivates identifying instability sides or locations before budget allocation.
- The same behavior-derived evidence continues to connect instability diagnosis and budget allocation.
- The following subsection title remains bounded to a relationship between cache management and quantization, now phrased as `正交关系`.

### Review Gate

- Technical accuracy reviewer: first candidate failed for narrowing IntactKV to bit-width and making the title claim too strong; final candidate passed after restoring high-precision representation, using `正交关系`, and limiting the claim to a related-work motivation.
- Chinese academic writing reviewer: first and second candidates failed for口语化 expressions and a negative `避免...` ending; final candidate passed after switching to positive wording around consistent behavior evidence.
- Cross-chapter consistency reviewer: third candidate failed because `运行时行为统计` could imply online profiling; final candidate passed after changing this to `离线校准链路产生的行为敏感度画像`.
- Skeptical reviewer: first candidate failed for overly narrow method attributions; final candidate passed with broader descriptions for ZipCache, IntactKV, SKVQ, and QJL.

### Applied Revision

```tex
低比特恢复方向工作沿两条思路展开。一条思路直接缓冲量化误差。QuaRot~\cite{ashkboos2024quarot} 用旋转把 Key 通道异常值打散到多维空间，GEAR~\cite{kang2024gear} 借助残差低秩近似补偿量化误差，QServe~\cite{lin2024qserve} 把低比特格式整合到端到端系统路径中。另一类工作关注缓存内容的重要性差异，并据此保留更高精度表示或采用更细粒度的量化处理。ZipCache~\cite{he2024zipcache} 基于缓存内容的重要性差异组织混合精度保留，IntactKV~\cite{liu2024intactkv} 保留少量关键 token 的高精度表示，SKVQ~\cite{duanmu2024skvq} 则利用缓存局部性或窗口化访问特征进行更细粒度的量化处理。Outlier Tokens Tracing~\cite{su2025outliertoken}、Atom~\cite{zhao2024atom} 与 QJL~\cite{zandieh2024qjl} 分别从异常 token 追踪、低比特表示和随机投影近似等方向扩展 KV Cache 压缩的边界，本文将它们列入表~\ref{tab:ch2-kv-comparison} 作为边界参考。总体来看，这些研究提示低比特 KV Cache 的性能保持不能只看平均压缩率，还需要判断哪些内容、模型层位置或访问局部性更可能在量化后引发失稳。本文沿着这一线索，将离线校准链路产生的行为敏感度画像用于失稳诊断和预算分配，使压缩目标与分配决策建立在一致的行为证据之上。

\textbf{缓存管理与量化的正交关系。}
```

### Verification

- `git diff --check -- thesis/chapters/ch2_related_work.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 100-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch2 low-bit recovery boundary`

## Segment 11

- Report segment: 11
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 6--16
- Detector excerpt begins: `下游任务感知到的是注意力分布 a 与注意力输出 o...`
- Suspected segment size in report: 196 characters.
- Status: applied

### Diagnosis

- Main AIGC triggers: compressed contrast between behavior and tensor reconstruction, textbook-style vector setup, and implicit multi-head/GQA boundary.
- Rewrite goal: preserve the mathematical setup while making the problem statement read as a motivated method-section opening rather than a detector-like definition block.
- Style constraints: avoid `读成`-style metaphor, avoid incomplete formula lead-ins, keep the Mistral model scope precise, and retain the GQA/MQA mapping boundary.

### Preserved Information

- The target behavior remains attention distribution $a$ and attention output $o$.
- $K,V$ elementwise reconstruction distance remains acknowledged as a numeric proxy but not sufficient alone.
- $(a,o)$ remains the behavior object to preserve after quantization.
- The analysis remains introduced under a single-head attention setup before extending to multi-head settings.
- $q\in\mathbb{R}^{1\times d_k}$, $K\in\mathbb{R}^{S\times d_k}$, and $V\in\mathbb{R}^{S\times d_v}$ are preserved.
- Historical context length $S$ and row vectors $k_i,v_i$ are preserved.
- The experiment-model dimension convention $d_v=d_k$ is preserved and scoped to Qwen2.5, LLaMA-3.1, and Mistral-7B-Instruct-v0.3.
- The standard single-head attention equation is unchanged.
- $\mathcal{B}(q,K,V):=(a,o)$ remains the notation for attention behavior.
- The connection to $\Delta_{\mathrm{beh}}$ is made explicit before the formal objective.
- Multi-layer, multi-head, GQA, and MQA applicability is preserved with a query-to-KV-head mapping boundary.

### Review Gate

- Mathematical reviewer: PASS; confirmed all tensor shapes, the single-head equation, $d_v=d_k$ boundary, and GQA/MQA relation remain correct.
- Chinese academic writing reviewer: first and second candidates failed for `任务读数`, `读成`, `行为层对象`, and missing formula context; final candidate passed after changing to `行为表征`, `单头注意力记法`, and complete formula context.
- Cross-chapter consistency reviewer: first candidate failed for missing GQA/MQA and $\Delta_{\mathrm{beh}}$ linkage and overly broad Mistral wording; final candidate passed after adding query-to-KV mapping, narrowing to Mistral-7B-Instruct-v0.3, and explicitly linking $\Delta_{\mathrm{beh}}$.
- Skeptical reviewer: first and second candidates failed for residual fragment and causal-strength issues; final candidate passed after adding the equation, bounding the behavior change to the layer attention computation, and clarifying shared KV heads under GQA/MQA.

### Applied Revision

```tex
在模型生成最终输出之前，KV Cache 误差会通过注意力 logits、softmax 权重和 Value 聚合进入后续计算，并在该层注意力中体现为注意力分布 $a$ 与注意力输出 $o$ 的变化。$K,V$ 的逐元素重建距离仍可作为数值代理，但不足以单独刻画这种行为变化。基于这一观察，本文将 $(a,o)$ 视为量化后需要共同保持的行为表征，并先在单头注意力设定下展开代数分解，以说明 Key 扰动经注意力分布影响输出、Value 扰动经加权聚合影响输出的两条耦合路径。

记当前查询为行向量 $q\in\mathbb{R}^{1\times d_k}$，历史上下文长度为 $S$，$K\in\mathbb{R}^{S\times d_k}$ 与 $V\in\mathbb{R}^{S\times d_v}$ 分别由行向量 $k_i, v_i$ 拼接而成。本文实验涉及的 Qwen2.5、LLaMA-3.1 以及 Mistral-7B-Instruct-v0.3 均采用常见的 $d_v=d_k$ 设置，因此在下述单头注意力记法中 $q$ 与 $o$ 同维。标准单头注意力可写为
\begin{equation}
a=\mathrm{softmax}\!\left(\frac{qK^\top}{\sqrt{d_k}}\right), \qquad o=aV,
\end{equation}
其中 $a\in\mathbb{R}^{1\times S}$ 为注意力分布，其第 $i$ 个分量记为 $a_i\in\mathbb{R}$；$o\in\mathbb{R}^{1\times d_v}$ 为注意力输出。注意力行为记作联合表征
\begin{equation}
\mathcal{B}(q,K,V):=(a,o).
\end{equation}
后文以 $\Delta_{\mathrm{beh}}$ 刻画量化前后 $(a,o)$ 的行为偏移。多层、多头情形可按层索引 $\ell$ 与头索引 $h$ 逐一展开，记为 $q^{(\ell,h)}, K^{(\ell,h)}$ 等；GQA/MQA 下，多个 Query 头可共享同一 KV 头，本节分解可对应到每个 Query 头及其映射的 KV 头，具体映射关系已在第~\ref{sec:ch2-kv-memory}~节给出。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 100-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; unrelated to this paragraph.
- Commit: see Git history for message `docs: polish aigc ch3 problem formalization`

## Segment 12

- Report segment: 12
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 48--50
- Detector excerpt begins: `式(3-8)显示，Key侧扰动先经 logits 改变注意力分布...`
- Suspected segment size in report: 265 characters.
- Status: applied

### Diagnosis

- Main AIGC triggers: compressed mechanism summary, `放大或衰减` phrasing, dense configuration enumeration, and ambiguous evidence-source boundaries between Figure~`\ref{fig:ch3-kv-asymmetry}` and Chapter 4 tables.
- Rewrite goal: keep the K/V path interpretation and `KxVy` notation while separating mechanism explanation, diagnostic notation, figure roles, and Chapter 4 evidence sources.
- Style constraints: avoid overclaiming from the algebra alone, avoid implying Figure~`\ref{fig:ch3-kv-asymmetry}` contains FP16, and write the notation paragraph as prose rather than a configuration list.

### Preserved Information

- Equation~`\eqref{eq:ch3-error-decomp}` still separates Key-side and Value-side routes into output.
- Key-side perturbation still enters through attention logits, softmax, attention-distribution difference, and output.
- Value-side error still enters aggregation as `$\hat a_i(\hat v_i-v_i)$`.
- The possibility of K/V sensitivity asymmetry under low-bit budgets is preserved.
- K/V single-side diagnosis and symmetric low-bit references remain the experimental checks.
- `\texttt{KxVy}` remains the notation for K/V side bit-width combinations.
- `\texttt{K4V8}`, `\texttt{K4V16}`, `\texttt{K16V4}`, and `\texttt{MixedKV}` keep their original meanings.
- Figure~`\ref{fig:ch3-kv-asymmetry}` remains the compression-diagnostic view over `\texttt{K8V8}`, `\texttt{K8V4}/\texttt{K4V8}`, and `\texttt{K4V4}`.
- `\texttt{FP16}` reference and single-side PPL isolation evidence are now explicitly attributed to Chapter 4 tables.

### Review Gate

- Mathematical reviewer: initial pass; after an apparent figure-scope concern, passed again once the actual figure source was checked and confirmed that Figure~`\ref{fig:ch3-kv-asymmetry}` does not display `\texttt{FP16}`.
- Chinese academic writing reviewer: first candidate failed for English-style phrasing, `放大还是被吸收`, and dense notation listing; final candidate passed after switching to `作用于输出的路径`, `影响大小`, and clearer configuration prose.
- Cross-chapter consistency reviewer: first candidate failed because it implied Figure~`\ref{fig:ch3-kv-asymmetry}` includes `\texttt{FP16}` and blurred Table 4-6/4-7 roles; final candidate passed after separating the figure from Chapter 4 table evidence.
- Skeptical reviewer: first candidate failed for causal-strength and notation risks; final candidate passed after weakening `约束` to `提供依据`, changing `MixedKV ≡ K8V4` to `对应 \texttt{K8V4}`, and clarifying the average-bit comparison.

### Applied Revision

```tex
式~\eqref{eq:ch3-error-decomp} 区分了两类误差作用于输出的路径。Key 侧扰动先改变注意力 logits，经 softmax 归一化后表现为注意力分布差异，并由分布项传到输出；Value 侧误差则以 $\hat a_i(\hat v_i-v_i)$ 的形式，在量化后权重下进入聚合。扰动对输出的影响大小取决于分布形态、logit 间隔以及权重集中程度，因此在低比特预算下，Key 与 Value 量化误差对输出的敏感性可能不同。后文通过 K/V 单侧诊断，并以对称低比特配置作为参照，检验这种不对称是否在实验中出现，为低比特路径的格式选择提供依据。

为统一后续图表记号，本节采用 \texttt{KxVy} 表示 K/V 两侧位宽组合。\texttt{K4V8} 表示 4-bit Key 与 8-bit Value。单侧隔离配置中，\texttt{K4V16} 表示 Key 为 4-bit、Value 保持 FP16，\texttt{K16V4} 表示 Key 保持 FP16、Value 为 4-bit。在本文实验记号中，\texttt{MixedKV} 对应 \texttt{K8V4}。图~\ref{fig:ch3-kv-asymmetry} 呈现压缩诊断视图，并按三组配置组织：\texttt{K8V8} 是高位宽量化参考，\texttt{K8V4}/\texttt{K4V8} 在相同 K/V 平均位宽设置下对照 K/V 角色，\texttt{K4V4} 作为对称低比特锚点。未量化 \texttt{FP16} 参考和单侧 PPL 隔离实验结果分别由第四章表~\ref{tab:ch4-kv-multitask} 与表~\ref{tab:ch4-kv-ppl} 给出。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 13a

- Report segment: 13
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 54
- Detector excerpt begins: `对Qwen2.5-1.5B的单侧PPL诊断表明...`
- Processing scope: first natural paragraph only. The detector also spans the next paragraph opening, which will be handled in the next commit.
- Status: applied

### Diagnosis

- Main AIGC triggers: report-like `表明` plus colon structure, compressed contrast between PPL and task diagnostics, over-direct causal phrasing around Key-side triggering, and inaccurate attribution of statistical protocol to Table~`\ref{tab:ch4-kv-ppl}`.
- Rewrite goal: keep all K/V diagnostic readings while separating PPL raw evidence from task evidence, narrowing the causal wording, and making the Value-side boundary explicit.
- Style constraints: avoid colon-led explanation, avoid unnecessary parentheses, avoid English shorthand such as `cliff` in Chinese prose, and keep the claim scoped to the Qwen2.5 low-bit comparisons in this paragraph.

### Preserved Information

- `\texttt{K4V16}` still raises PPL by about two orders of magnitude relative to FP16.
- `\texttt{K16V4}` still causes only a small change near the baseline.
- The PPL raw readings are still attributed to Table~`\ref{tab:ch4-kv-ppl}`.
- In the 32K task diagnostics, `\texttt{K4V8}` still drives Qwen2.5-1.5B and Qwen2.5-7B RULER pass rates to zero.
- `\texttt{K8V4}` still does not show zero-collapse instability.
- The combined reading still identifies Key-side low-bit noise as the more direct task-level instability trigger under these Qwen2.5 comparisons.
- The Value-side boundary is preserved by saying it does not trigger instability of the same strength in the cited contrasts, rather than claiming it has no effect.
- The final interpretation remains consistent with Equation~`\eqref{eq:ch3-error-decomp}` and its Key/Value path separation.

### Review Gate

- Technical reviewer: initially requested retaining the old table-statistics wording, then passed after Chapter 4 context confirmed that Table~`\ref{tab:ch4-kv-ppl}` reports deterministic PPL raw values and does not use Bootstrap or sign-flip testing.
- Chinese academic writing reviewer: first pass failed only on the English shorthand `cliff`; final version passed after replacing it with `同等强度的失稳`.
- Cross-chapter consistency reviewer: PASS; confirmed the Table~`\ref{tab:ch4-kv-ppl}` and Table~`\ref{tab:ch4-kv-multitask}` evidence split remains coherent.
- Skeptical reviewer: first pass failed for over-causal wording and overly weak Value-side phrasing; final version passed after changing the conclusion to a narrower supported judgment.

### Applied Revision

```tex
Qwen2.5-1.5B 的单侧 PPL 诊断给出最直接的隔离读数。\texttt{K4V16} 将 PPL 相对 FP16 基线推高约两个数量级，\texttt{K16V4} 只带来基线邻域内的小幅变化，原始读数见表~\ref{tab:ch4-kv-ppl}。同一方向也出现在 32K 任务诊断中。\texttt{K4V8} 下，Qwen2.5-1.5B 与 Qwen2.5-7B 的 RULER 通过率降为零；\texttt{K8V4} 没有出现归零式失稳。两组读数共同支持一个较窄判断，即在本文这些 Qwen2.5 低比特对照中，Key 侧低比特噪声是更直接的任务级失稳触发源；Value 侧压缩并非没有影响，但在 \texttt{K16V4} 与 \texttt{K8V4} 对照中没有触发同等强度的失稳。这个判断与式~\eqref{eq:ch3-error-decomp} 对 Key/Value 两条误差路径的机制区分一致。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 14

- Report segment: 14
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 58
- Detector excerpt begins: `因此Key侧低比特退化被确立为低比特路径设计的核心约束...`
- Status: applied

### Diagnosis

- Main AIGC triggers: formulaic `因此...被确立`, parenthetical evidence packing, English-style `dose-response`, and a compressed evidence hierarchy that did not restate the Value-side contrasts.
- Rewrite goal: keep the Key-side risk conclusion while making the evidence hierarchy explicit: single-side PPL isolation is primary, task readouts are external consistency and boundary evidence.
- Style constraints: avoid unnecessary parentheses, avoid English shorthand, avoid over-claiming `\texttt{K4V8}`/`\texttt{K4V4}` as isolated Key evidence, and keep statistical-protocol references correctly assigned.

### Preserved Information

- Key-side low-bit degradation remains a design constraint for the low-bit path, now phrased as a risk point that needs priority control.
- The main isolation evidence still comes from single-side PPL diagnosis.
- `\texttt{K4V16}` still independently causes order-level PPL degradation.
- `\texttt{K16V4}` is now explicitly restated as only a small change.
- `\texttt{K4V8}`/`\texttt{K4V4}` remain same-direction task evidence under lower Key bit-width.
- `\texttt{K8V4}` remains the contrast without zero-collapse instability.
- The boundary remains that `\texttt{K4V8}` and `\texttt{K4V4}` simultaneously lower K and V and therefore cannot alone isolate K dominance.
- PPL raw readings remain assigned to Table~`\ref{tab:ch4-kv-ppl}`.
- Cross-task readings and their statistical protocol remain assigned to Table~`\ref{tab:ch4-kv-multitask}` and Section~`\ref{sec:exp-kv-sensitivity}`.

### Review Gate

- Technical reviewer: PASS; confirmed evidence hierarchy and statistical-protocol attribution.
- Chinese academic writing reviewer: first pass failed on `核心约束位置`, `数量级 PPL 退化`, and `剂量响应式信号`; final version passed after replacing these with natural Chinese expressions.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Chapter 4 Section~`\ref{sec:exp-kv-sensitivity}` and Tables~`\ref{tab:ch4-kv-ppl}`/`\ref{tab:ch4-kv-multitask}`.
- Skeptical reviewer: first pass failed because Value-side contrast was omitted and `核心约束` was too strong; final version passed after restating `\texttt{K16V4}`/`\texttt{K8V4}` and narrowing the claim to a priority risk point.

### Applied Revision

```tex
这些证据表明，Key 侧低比特退化是低比特路径设计中需要优先约束的风险点。主要隔离依据来自单侧 PPL 诊断，\texttt{K4V16} 单独使 PPL 出现数量级退化，\texttt{K16V4} 只带来小幅变化。任务读数提供外部一致性，\texttt{K4V8}/\texttt{K4V4} 在 Key 位宽降到 4 bit 后出现更强失稳，\texttt{K8V4} 未出现归零式失稳。由于 \texttt{K4V8} 与 \texttt{K4V4} 同时压低 K 与 V，它们仍只适合作为边界辅助证据，不能单独支撑 K 主导的隔离推断。PPL 原始读数见表~\ref{tab:ch4-kv-ppl}；跨任务读数及统计协议，包括 Bootstrap 95\% CI、sign-flip 置换检验与 BH-FDR 多重比较校正，见表~\ref{tab:ch4-kv-multitask} 与第~\ref{sec:exp-kv-sensitivity}~节。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 13b

- Report segment: 13
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 56
- Detector excerpt begins: `该不对称在不同模型族上强度不同...`
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-led compressed explanation, unnecessary parenthetical packing of model metadata, English-style `在不同模型族上`, and an overly direct reading of `$H_{kv}$` as a causal variable.
- Rewrite goal: preserve the Qwen/LLaMA numerical configuration and diagnostic contrast while spelling out the GQA sharing mechanism and keeping `$H_{kv}$` as a proxy variable.
- Style constraints: avoid `xxxx 上`, avoid unnecessary parentheses, avoid treating `$H_{kv}$` as a single cause, and keep the paragraph scoped to the cited contrast.

### Preserved Information

- Qwen-series `$H_{kv}$` remains 2 or 4.
- The repetition factor remains `$N_{\mathrm{rep}}=H_q/H_{kv}` and falls in `$\{6,7\}$` for the Qwen cases.
- Qwen still shows retrieval zero under `\texttt{K4V8}` and `\texttt{K4V4}`.
- LLaMA-3.1-8B remains the comparison case with `$H_{kv}=8` and `$N_{\mathrm{rep}}=4`.
- LLaMA-3.1-8B still has a smaller instability magnitude in the cited comparison.
- The GQA interpretation still states that a KV-head quantization error is shared by its mapped Query heads.
- Table~`\ref{tab:ch4-kv-multitask}` remains the evidence source.
- The boundary statement still includes model scale, training data, and GQA configuration as co-modulating factors.
- `$H_{kv}$` remains a proxy for between-group differences rather than a single causal explanation.

### Review Gate

- Technical reviewer: PASS; confirmed the `$H_q`-comparable condition and `$N_{\mathrm{rep}}` wording avoid single-variable `$H_{kv}$` causality.
- Chinese academic writing reviewer: first pass failed on `GQA 语义下` and an unnatural Query-head sharing phrase; final version passed after rewriting as `在 GQA 机制中` and `共同承受`.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Chapter 4 Table~`\ref{tab:ch4-kv-multitask}` and the architecture-modulated reading.
- Skeptical reviewer: PASS; no over-claiming or missing original information found.

### Applied Revision

```tex
这种不对称的强弱还随模型族和头共享结构改变。Qwen 系列的 $H_{kv}$ 为 2 或 4，重复因子 $N_{\mathrm{rep}}=H_q/H_{kv}$ 落在 $\{6,7\}$，在 \texttt{K4V8} 与 \texttt{K4V4} 下出现检索归零。LLaMA-3.1-8B 的 $H_{kv}=8$、$N_{\mathrm{rep}}=4$，在当前对照里失稳幅度较小。在 GQA 机制中，同一个 KV 头的量化误差会由映射到该头的一组 Query 头共同承受；在 $H_q$ 可比的对照中，较小的 $N_{\mathrm{rep}}$ 意味着共享同一 KV 头误差的 Query 头更少，相关读数见表~\ref{tab:ch4-kv-multitask}。更稳妥的解释还需要同时纳入模型规模、训练数据与 GQA 配置，$H_{kv}$ 在本文中只作为组间差异的代理变量，用于描述严重程度与触发位宽的边界变化。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.
