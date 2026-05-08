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
