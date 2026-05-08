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

- Report segment: 2
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
