# AIGC Revision Tracker

This file records paragraph-level AIGC-polish changes. Each entry maps one detector segment to one source paragraph, records the preserved claim set, review gates, verification commands, and commit hash.

## Source Reports

- HTML statistics report: `/Users/chenzilang/Downloads/main (2)/main_AIGC统计报告.html`
- Concise PDF report: `/Users/chenzilang/Downloads/main (2)/main_AIGC简洁报告.pdf`
- Original comparison PDF: `/Users/chenzilang/Downloads/main (2)/main_AIGC原文对照报告.pdf`

## Global Result Snapshot

- Overall suspected AIGC ratio: 20.38%
- Highest-risk chapters: Chinese abstract 72.0%, English abstract 72.0%, Chapter 3 32.0%, Chapter 1 24.0%, Conclusion 14.0%

## Segment 48

- Report segment: 48
- Source paragraph: `thesis/chapters/ch5_conclusion.tex`, line 51
- Detector excerpt begins: `和单一随机种子。这个设置足以检查...`
- Status: applied

### Diagnosis

- Main AIGC triggers: `从...上看` template, long boundary sentence with paired negative clauses, and list-like examples attached by `例如`.
- Rewrite goal: preserve all evaluation-scope limits while making the paragraph read as a direct limitation statement.
- Style constraints: avoid `xxxx 上`, keep the LongBench official-data boundary precise, and preserve every example of real application distribution.

### Preserved Information

- The main matrix uses LongBench-style synthetic benchmark tasks under unified generation rules.
- The official LongBench real-data comparison only covers Qwen2.5-1.5B.
- It covers NarrativeQA, HotpotQA, and GovReport.
- Each task has at most 50 samples.
- The comparison uses a single random seed.
- This setup can check whether a small set of official tasks reverses the main-protocol direction.
- It does not represent broader real application distributions such as multi-turn QA, tool use, repository-level code retrieval, long report summarization, or domain document QA.
- PPL, Needle, RULER, and task-level metrics reduce single-metric bias.
- Long-context quality still needs more observation dimensions.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
评测协议给出第一层边界。正文主矩阵使用统一生成规则下的 LongBench 风格合成基准任务；官方 LongBench 真实数据对照只覆盖 Qwen2.5-1.5B、NarrativeQA/HotpotQA/GovReport 三个任务、每任务最多 50 个样本和单一随机种子。这个设置可以检查少数官方任务是否反转主协议方向，但它还不能代表更开放的真实应用分布，包括多轮问答、工具调用、代码仓库级检索、超长报告摘要和领域文档问答。PPL、Needle、RULER 与任务级指标共同降低了单一度量偏差；长上下文质量仍需要更多观察维度继续补充。
```

### Verification

- `git diff --check -- thesis/chapters/ch5_conclusion.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch5 evaluation boundary`

## Segment 47

- Report segment: 47
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 784
- Detector excerpt begins: `从机制上看，这一解释是合理的...`
- Status: applied

### Diagnosis

- Main AIGC triggers: formulaic mechanism opener, repeated `在...下/上` structures, and English-style terms `setting`, `attention`, `quantization noise`, and `ranking`.
- Rewrite goal: keep the mechanism intuition while reducing English-style Chinese and preserving the interpretive boundary.
- Style constraints: translate nonessential English terms, avoid `xxxx 上/下`, and keep `解释性推断` rather than a proven mechanism.

### Preserved Information

- The paragraph gives a mechanism-level interpretation, not a theorem.
- Smaller or more sensitive models and more aggressive low-bit settings make softmax ranking more fragile to Key error.
- Attention-distribution misalignment can appear before tensor-norm degradation.
- KL-like distribution proxies can be more diagnostic in such cases.
- Larger models, higher bit-width, or smoother architectures may keep quantization noise within a stable ranking region.
- KL and MSE parameter choices may converge in those settings.
- The claim remains an interpretive inference rather than a mechanism theorem.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
这种解释可以作为机制层面的读法。较敏感的小模型或更激进的低比特设置中，softmax 排序对 Key 误差更脆弱，注意力分布错位可能先于张量范数恶化出现，KL 这类分布代理因而更有诊断价值；模型更大、位宽更高或架构更平滑时，量化噪声未必足以把排序推离原本稳定区域，KL 与 MSE 搜索到的参数也就更容易收敛。上述判断仍属于\emph{解释性推断}，尚未构成机制定理。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 kl mse mechanism`

## Segment 46

- Report segment: 46
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 782
- Detector excerpt begins: `因此，7B这块证据的关键在于...`
- Status: applied

### Diagnosis

- Main AIGC triggers: `因此...关键在于` template, colon-style bold conclusion, `7B 这块证据`口语化表达, and `在...上` phrasing.
- Rewrite goal: preserve the convergence evidence while making the paragraph read as a measured table interpretation.
- Style constraints: avoid `xxxx 上`, avoid unnecessary colon usage, keep all calibration parameters and PPL values unchanged.

### Preserved Information

- Table~\ref{tab:ch4-kl-mse-convergence} is the minimal empirical support for the question.
- Qwen2.5-7B-Instruct KL and MSE objectives search to the same parameter pair.
- The shared parameter pair is $k_{\mathrm{pct}}=100.0$ and $v_{\mathrm{pct}}=99.9$.
- The corresponding `\texttt{INT4-RoleAlign}` PPL values are identical at 7.1121.
- The key reading is that KL and MSE have highly converged in the 7B setting.
- Appendix~\ref{subsec:app-7b-kl-mse} provides supplementary comparisons.
- The result suggests model scale and robustness may modulate KL/MSE differences.
- The main-text evidence mainly supports the bounded claim that convergence has appeared.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
表~\ref{tab:ch4-kl-mse-convergence} 提供了这一问题的最小实证支撑。Qwen2.5-7B-Instruct 的 KL 与 MSE 目标最终搜索到同一组参数，即 $k_{\mathrm{pct}}=100.0$、$v_{\mathrm{pct}}=99.9$；对应的 \texttt{INT4-RoleAlign} PPL 完全一致，均为 7.1121。7B 结果的关键读数是，\textbf{该设定中 KL 与 MSE 已经高度趋同。} 结合附录第~\ref{subsec:app-7b-kl-mse}~节的补充对照，这一结果提示模型规模与鲁棒性可能调节二者差异；当前正文证据主要支持“趋同已经出现”这一判断。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 kl mse convergence`

## Segment 45

- Report segment: 45
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 692
- Detector excerpt begins: `表4-13 的 Panel A说明...`
- Status: applied

### Diagnosis

- Main AIGC triggers: template-like `具体而言`, colon-style conclusion, `Qwen2.5-14B 上` phrasing, and mixed English `memory traffic`.
- Rewrite goal: preserve every deployment number while turning the paragraph into a bounded reading of Panel A.
- Style constraints: avoid `xxxx 上`, avoid unnecessary colon expansion, translate `memory traffic` to `访存流量`, and keep the H20/batch/backend boundary explicit.

### Preserved Information

- Panel A supports the deployment reading.
- 4K is treated as a noise-range reference rather than evidence for deployment value.
- Qwen2.5-14B with Triton fused path has a -0.44 ms difference at 4K.
- Differences at 8K, 16K, and 32K are -14.54 ms, -33.26 ms, and -77.08 ms.
- Relative reductions are about -17\%, -28\%, and -40\%.
- The trend is monotonic over the reported length points.
- After 8K, longer historical KV increases the fused path's time advantage over the reference path.
- The conclusion is limited to Qwen2.5-14B, H20, `\texttt{batch=1}`, and the current backend combination.
- As memory traffic rises, fused-path bandwidth savings can gradually outweigh fixed scheduling overhead.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS after changing `memory traffic` to `访存流量`, smoothing `Panel A` wording, and merging the bounded conclusion.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
表~\ref{tab:ch4-deployment-boundary} 中 Panel A 的读数表明，融合路径的部署价值主要随序列长度拉长显现，4K 单点仅能作为噪声范围内的参照。Qwen2.5-14B 采用 Triton 融合路径时，相对参考路径的时间差在 4K 仅为 -0.44\,ms；序列长度增至 8K 后，时间差扩大为 -14.54\,ms，16K 为 -33.26\,ms，32K 为 -77.08\,ms，对应约 -17\%、-28\% 和 -40\% 的相对降幅。这个趋势在本组长度点保持单调。8K 之后，历史 KV 越长，融合路径相对参考路径的时间优势越明显。据此，第 4.5.2 节只支持一个有边界的最小结论，即在 Qwen2.5-14B、H20、\texttt{batch=1} 与当前后端组合这一适用条件内，访存流量上升后，融合路径的带宽节省能够逐步压过固定调度开销。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 deployment panel a`

## Segment 44

- Report segment: 44
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 687
- Detector excerpt begins: `控制对比不再单列成表...`
- Status: applied

### Diagnosis

- Main AIGC triggers: table-note colon, stacked protocol clauses, and rigid `不再...仅在...` phrasing.
- Rewrite goal: keep the deployment boundary note compact while preserving the empirical-crossing and n.s. interpretation rules.
- Style constraints: avoid unnecessary colon usage, preserve Panel A/B mapping and the 8B vs 14B control-comparison placement.

### Preserved Information

- Panel A and Panel B correspond to Sections 4.5.2 and 4.5.3.
- The performance crossing boundary is empirical, not a theoretical closed-form model.
- The same-$H_{kv}=8$ 8B vs 14B control comparison is reported only in Section 4.5.3 text rather than as a standalone table.
- 4K readings with $|\Delta T|<2$ ms are marked as n.s.
- n.s. readings are not used as crossing points.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
\emph{注} Panel A 与 Panel B 分别对应第 4.5.2 节与第 4.5.3 节。这里的“性能交叉边界”是经验读数，并非理论闭式模型；8B vs 14B 的同 $H_{kv}=8$ 控制对比不单独列成表，而在第 4.5.3 节正文作为补充段落报告。4K 处 $|\Delta T|<2$\,ms 的读数统一标记为 n.s.，不作为交叉点读取。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 deployment table note`

## Segment 43

- Report segment: 43
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 384
- Detector excerpt begins: `表 4-8 的配对范围是 1.5B...`
- Status: applied

### Diagnosis

- Main AIGC triggers: semicolon-heavy bookkeeping, `配对模型上` phrasing, colon-style `较窄判断`, and a rigid final negative claim.
- Rewrite goal: keep the paired comparison scope, PPL differences, Needle recovery, and bounded interpretation while improving Chinese academic flow.
- Style constraints: avoid `xxxx 上`, avoid unnecessary colon expansion, and keep RoleAlign/KIVI-style evidence bounded to the shared-format comparison.

### Preserved Information

- Paired comparison only covers 1.5B, 7B, and 8B.
- The 14B row only indicates the current RoleAlign coverage.
- RoleAlign versus KIVI-style PPL gaps are $+0.15$, $+0.05$, and $+0.00$.
- Both Needle tasks recover to 100\%.
- Upgrading from symmetric per-group format to `\texttt{per-channel K + per-token V}` restores low-bit retrieval from collapse to usability.
- Within this shared format, calibration sources produce close quality readings rather than a large quality split.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS after clarifying the paired-comparison scope and replacing `per-group` with `对称逐组格式`.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
表~\ref{tab:ch4-rolealign-kivi} 的配对比较只覆盖 1.5B、7B 与 8B 三个模型，14B 行用于标明当前 RoleAlign 覆盖范围。配对模型中，RoleAlign 相对 KIVI-style 的 PPL 差距分别为 $+0.15$、$+0.05$ 和 $+0.00$，两类 Needle 任务均恢复到 100\%。这些读数支持的判断较窄。从对称逐组格式升级为 \texttt{per-channel K + per-token V} 后，低比特检索由崩塌状态恢复到可用状态；同一格式内，不同校准来源对应的质量读数保持接近。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 rolealign paired reading`

## Segment 42

- Report segment: 42
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 379
- Detector excerpt begins: `注：Needle列中的100/100%表示...`
- Status: applied

### Diagnosis

- Main AIGC triggers: compact table-note colon, mechanical `表示...；...。...不参与...` structure, and stiff wording around the 14B boundary.
- Rewrite goal: keep the table semantics and pairwise-comparison boundary while removing unnecessary colon punctuation.
- Style constraints: keep the table note concise, preserve all task names and fixed-seed information, and avoid changing the comparison scope.

### Preserved Information

- `\texttt{100/100\%}` means both Needle-single-retrieval and MK-NIAH-2 reach 100\% pass rate.
- The generative-quality protocol uses 5 fixed seeds.
- Qwen2.5-14B currently has only RoleAlign results.
- Qwen2.5-14B is excluded from paired-difference judgment.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
\emph{注} \texttt{100/100\%} 表示 Needle-single-retrieval 与 MK-NIAH-2 两类检索任务均达到 100\% 通过率；生成式质量协议使用 5 个固定 seeds。Qwen2.5-14B 当前仅有 RoleAlign 结果，因此不纳入配对差异判断。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 rolealign table note`

## Segment 41

- Report segment: 41
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 248
- Detector excerpt begins: `造成这种阶跃而非平滑退化的原因...`
- Status: applied

### Diagnosis

- Main AIGC triggers: explanatory template beginning, colon-style handoff, strong single-cause language around softmax and `H_{kv}=8`, and repeated `会` clauses.
- Rewrite goal: preserve the mechanism intuition while making it conditional and bounded enough for a skeptical reviewer.
- Style constraints: avoid unnecessary colon usage, avoid `xxxx 上/下`, keep the Key/Value trigger question open for the next diagnostic subsection.

### Preserved Information

- Stepwise rather than smooth degradation is interpreted through softmax sensitivity to $QK^\top$ scores.
- If Key-side noise pushes the target token out of the top-$k$ score region, probability mass can move quickly to the wrong position.
- This mechanism can produce a 100\% to 0\% retrieval jump instead of a 50\%/30\%/10\% linear decay.
- LLaMA-3.1-8B retains 98\% Needle.
- The LLaMA-3.1-8B case is read against its $H_{kv}=8$ and smaller $H_q/H_{kv}$ repetition factor, with architecture and training confounders kept explicit.
- The next question remains whether Key or Value is the first trigger.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS after smoothing `阶跃式` and removing口语化 `本文对照里的`.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS after making the Key-side mechanism conditional, weakening the $H_{kv}=8$ causal reading, and replacing `崩塌阈值` with `经验触发边界`.

### Applied Revision

```tex
阶跃退化而非平滑退化，可以从 softmax 对 $QK^\top$ 分数的指数敏感性理解。在 Key 侧路径中，若量化噪声把目标 token 的分数推出 top-$k$ 区域，softmax 会把概率质量快速转移到错误位置，检索结果便更容易形成从 100\% 到 0\% 的临界跳变，而不是 50\%/30\%/10\% 这类线性衰减。LLaMA-3.1-8B 保留 98\% Needle，这一读数与 $H_{kv}=8$ 和较小 $H_q/H_{kv}$ 重复因子对应的 GQA 噪声稀释条件相符；同时，模型族、规模和训练数据差异仍可能共同影响结果。更稳妥的读法是，LLaMA-3.1-8B 作为架构例外，极低比特 Key 噪声尚未完全越过经验触发边界。接下来需要区分的是，这一崩塌首先由 Key 侧还是 Value 侧触发。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 softmax cliff mechanism`

## Segment 40

- Report segment: 40
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 246
- Detector excerpt begins: `LLaMA-3.1-8B 则保留98% Needle...`
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-style evidence unpacking, repeated boundary-signaling phrases such as `只确认一个有边界的现象`, and the loose expression `参数再调一调`.
- Rewrite goal: keep the evidence chain and bounded conclusion while making the paragraph read as a direct interpretation of Table~4-5.
- Style constraints: avoid unnecessary colon usage, avoid `xxxx 上/下` phrasing, retain the exact Needle percentages and the architecture-dependent cliff claim.

### Preserved Information

- Table~\ref{tab:ch4-int4-cliff} is the minimal evidence anchor for the stepwise collapse.
- Qwen2.5-1.5B and Qwen2.5-7B drop from 100\% Needle to 0\% under symmetric `\texttt{INT4}`.
- The same cases also show obvious language-modeling degradation.
- LLaMA-3.1-8B remains at 98\% Needle.
- The subsection's conclusion is bounded to one model class, not all architectures.
- The following analysis should focus on matching quantization format with error-propagation structure, beyond simply tuning calibration parameters.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS after replacing `在...下` and `在...上` structures.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
表~\ref{tab:ch4-int4-cliff} 给出了这一阶跃崩塌的最小证据。Qwen2.5-1.5B 与 Qwen2.5-7B 使用对称 \texttt{INT4} 时，Needle 由 100\% 直接降至 0\%，语言建模读数也同步出现明显退化；LLaMA-3.1-8B 仍保留 98\% Needle。基于这一组对照，第~\ref{subsec:ch4-int4-cliff}~节给出的结论限定为\textbf{对称 \texttt{INT4} 会使一类模型出现架构依附性的阶跃崩塌。} 这个读数将后续分析推向更结构化的问题，即量化格式如何匹配误差传播路径，而不仅是继续调整校准参数。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 int4 cliff evidence`

## Segment 39

- Report segment: 39
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 65
- Detector excerpt begins: `系统效率只读三项...`
- Status: applied

### Diagnosis

- Main AIGC triggers: clipped metric list, colon-style explanation, repeated `对应` chain with a mechanical ending.
- Rewrite goal: keep the three efficiency metrics and the H20-environment boundary while making the paragraph read as part of the protocol rather than a checklist.
- Style constraints: avoid unnecessary colon usage, use a formal cross-reference to the deployment section, and keep the conclusion bounded to the stated metrics and hardware environment.

### Preserved Information

- The system efficiency part uses three readings: TPOT, KV Cache usage, and peak memory.
- TPOT measures time per generated token during decoding.
- KV Cache usage measures cache compression benefit.
- Peak memory reflects overall runtime pressure.
- The deployment conclusion in Section~4.5 is only interpreted under these metrics and the current H20 environment.

### Review Gate

- Technical accuracy reviewer: PASS.
- Chinese academic writing reviewer: PASS after replacing `decode 阶段` with `解码阶段` and tightening `整体运行压力`.
- Cross-chapter consistency reviewer: PASS.
- Skeptical reviewer: PASS.

### Applied Revision

```tex
系统效率部分保留三项读数。TPOT 对应解码阶段生成单个 token 的时间，KV Cache 占用对应缓存压缩收益，峰值显存对应整体运行压力。第~\ref{sec:ch4-deployment}~节的部署结论限定在这三项指标与当前 H20 环境内解释。
```

### Verification

- `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing overfull hbox at line 369; no undefined references or citation warnings.
- Commit: see Git history for message `docs: polish aigc ch4 system metric boundary`

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

## Segment 38

- Report segment: 38
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 63
- Detector excerpt begins: `RULER 的失败信号是模型在组合式长上下文任务中是否维持宏平均通过率...`
- Status: applied

### Diagnosis

- Main AIGC triggers: `失败信号是` template, colon-led `前者/后者` explanation, and overly regular comparison between Needle and RULER.
- Rewrite goal: preserve the complementary metric roles while removing the formulaic contrast structure.
- Style constraints: avoid colon-style explanation, avoid `前者/后者`, keep macro-average pass rate and multi-subtask degradation, and avoid overstating either metric.

### Preserved Information

- RULER still uses macro-average pass rate.
- RULER still evaluates compositional long-context tasks.
- Needle still serves as a single-point retrieval probe.
- RULER still serves as the higher-pressure task set.
- The two metrics remain complementary in the main text.
- Needle still exposes retrieval functional thresholds.
- RULER still checks whether long-context ability degrades across multiple subtasks.

### Review Gate

- Technical reviewer: PASS; confirmed the metric roles are preserved.
- Chinese academic writing reviewer: PASS; confirmed the rewrite avoids the previous template structure.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 4 results.
- Skeptical reviewer: PASS; confirmed neither metric's scope is overstated.

### Applied Revision

```tex
RULER 用宏平均通过率观察模型在组合式长上下文任务中的稳定性。与 Needle 的单点检索探针不同，RULER 更接近高压任务组，两者在正文中承担互补角色。Needle 用于暴露检索功能临界点，RULER 则检查多个子任务中的长上下文能力是否同步退化。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 37

- Report segment: 37
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 61
- Detector excerpt begins: `任务级主矩阵采用 LongBench 风格合成任务...`
- Status: applied

### Diagnosis

- Main AIGC triggers: protocol-definition rhythm, repeated `使用` / `采用` pattern, and a stiff final caveat about official leaderboard alignment.
- Rewrite goal: keep the synthetic LongBench-style protocol boundary while making the paragraph read as a natural description of the task matrix.
- Style constraints: avoid implying official LongBench scores, keep `task-core`, keep metrics explicit, and preserve the non-alignment with community leaderboards.

### Preserved Information

- The task-level main matrix still uses LongBench-style synthetic tasks.
- The main tables still focus on the `task-core` subset.
- The covered functional categories remain single-document QA, multi-document QA, and summarization.
- QA tasks still use F1.
- Summarization tasks still use Rouge-L.
- Some extension tasks still use Edit Similarity or other text-similarity metrics.
- The protocol still supports method comparison within the same data-generation and scoring pipeline.
- Absolute scores remain protocol-local and are not directly aligned with community official leaderboards.

### Review Gate

- Technical reviewer: PASS; confirmed all metric and protocol details remain intact.
- Chinese academic writing reviewer: PASS; confirmed the rewrite is more natural.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with official LongBench boundaries and appendix aggregation.
- Skeptical reviewer: PASS; confirmed the synthetic-task boundary and non-leaderboard comparison boundary remain clear.

### Applied Revision

```tex
任务级主矩阵使用 LongBench 风格合成任务。正文主表聚焦 task-core 子集，覆盖单文档问答、多文档问答和摘要三类功能；问答任务采用 F1，摘要任务采用 Rouge-L，少量扩展任务采用 Edit Similarity 等文本相似度指标。这个协议用于在同一数据生成与评分管线内比较方法差异，绝对分数只按本文协议解释，不与社区官方榜单做直接对齐。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 36

- Report segment: 36
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 59
- Detector excerpt begins: `Needle-in-a-Haystack的失败信号是目标片段能否被精确取回...`
- Status: applied

### Diagnosis

- Main AIGC triggers: rigid `失败信号是...` opening, quoted meta phrase, and a compressed final clause that turned the metric explanation into a formulaic boundary statement.
- Rewrite goal: keep the Needle protocol exact while describing the metric as a concrete retrieval proxy.
- Style constraints: avoid quoted self-explanation, avoid overclaiming exact-match pass rate as full long-context ability, and keep the four context lengths and needle-depth scan.

### Preserved Information

- The paragraph still describes Needle-in-a-Haystack.
- The target fragment still must be precisely retrieved.
- The evaluation still covers 4K, 8K, 16K, and 32K context lengths.
- The evaluation still scans unified needle-depth settings.
- The main text still uses exact-match pass rate as the reported reading.
- The reading still serves as a functional boundary signal for retrieval, now phrased as a proxy for long-distance target-fragment retrieval ability.

### Review Gate

- Technical reviewer: PASS; confirmed the protocol details are preserved.
- Chinese academic writing reviewer: PASS; confirmed the paragraph is less mechanical.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 4 Needle and RULER usage.
- Skeptical reviewer: first pass failed because `唯一主读数` and `长距离检索能力` were too strong; final version passed after narrowing exact match to a proxy reading.

### Applied Revision

```tex
Needle-in-a-Haystack 关注目标片段能否被精确取回。评测覆盖 4K、8K、16K 与 32K 四个上下文长度，并在各长度内按统一的 needle 深度设置扫描；正文以精确匹配通过率作为主读数，将其作为长距离目标片段取回能力的代理读数。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 35

- Report segment: 35
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 57
- Detector excerpt begins: `PPL的失败信号是固定窗口内的整体likelihood退化...`
- Status: applied

### Diagnosis

- Main AIGC triggers: rigid metric-definition opening, English `likelihood` embedded in Chinese prose, mechanical causal sentence `这一设置决定...`, and a negative cross-protocol caveat.
- Rewrite goal: keep the PPL protocol fully auditable while making the paragraph read as a concise protocol note.
- Style constraints: use Chinese `语言建模似然` for likelihood, avoid `xxxx 上`, keep `32K` and `\texttt{chunk_size}=128`, and preserve the 14B fixed-prefix boundary.

### Preserved Information

- PPL still measures degradation of fixed-window language modeling likelihood.
- The evaluation protocol still uses 32K context.
- `\texttt{chunk_size}` remains fixed at 128.
- The chunk setting still constrains the history window available to each position during cross-entropy accumulation.
- Models with sufficient memory still report PPL on the full test-set protocol.
- The 14B model is still evaluated only on a fixed test-set prefix because of H20 memory constraints.
- The 14B PPL absolute value is still not used for direct cross-protocol comparison with other models; the revision states this as within-model use and same-protocol comparison.

### Review Gate

- Technical reviewer: PASS; confirmed the PPL protocol and 14B boundary remain intact.
- Chinese academic writing reviewer: first pass failed on `likelihood`, `32K 上下文协议`, and mechanical wording; final version passed after replacing them with Chinese academic phrasing.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the PPL tables and Chapter 4 protocol notes.
- Skeptical reviewer: PASS; confirmed the 14B fixed-prefix and cross-protocol comparison boundary remain explicit.

### Applied Revision

```tex
PPL 用来观察固定窗口内的整体语言建模似然是否退化。本文统一采用 32K 上下文评测协议，并将 \texttt{chunk\_size} 固定为 128；交叉熵累计时，每个位置可访问的历史窗口受该设置约束。显存充足的模型按完整测试集协议报告 PPL；14B 模型受 H20 显存约束，只使用测试集固定前缀评测，因此其绝对值仅用于该模型内部对照，跨模型比较仍以同协议读数为准。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 34

- Report segment: 34
- Source paragraph: `thesis/chapters/ch4_experiments.tex`, line 55
- Detector excerpt begins: `PPL 检查语言建模概率质量是否整体漂移...`
- Status: applied

### Diagnosis

- Main AIGC triggers: repeated `检查` sentence pattern, list-like metric enumeration, and a hard negative boundary for official LongBench that could understate its role.
- Rewrite goal: keep the failure-mode mapping while making each metric's role more concrete and keeping official LongBench as a bounded external-data sanity check.
- Style constraints: avoid unnecessary colon or parenthetical explanation, avoid overusing `检查`, keep the official LongBench comparison outside the main matrix without dismissing its value, and keep system evaluation bounded to TPOT, KV Cache footprint, and peak memory.

### Preserved Information

- The chapter still organizes metrics by quantization failure modes.
- PPL still tracks language-modeling probability-quality drift.
- Needle-in-a-Haystack still evaluates long-distance retrieval through exact-match success.
- LongBench-style synthetic tasks still provide task-level comparisons under one scoring pipeline.
- RULER still evaluates higher-pressure long-context compositional ability.
- TPOT, KV Cache footprint, and peak memory still cover deployment-side costs.
- Official LongBench real-data comparison remains outside the main matrix and is still assigned to Section~`\ref{subsec:ch4-longbench-official}`.
- The official LongBench comparison remains a protocol-consistency check, now also described as an external real-data directional check.

### Review Gate

- Technical reviewer: PASS; confirmed the metric roles remain accurate.
- Chinese academic writing reviewer: PASS; confirmed the repeated `检查` pattern was reduced.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 4 metric definitions and the official LongBench section.
- Skeptical reviewer: first pass failed because Needle and LongBench-style roles were too abstract and `只承担` could undervalue official LongBench; final version passed after restoring exact-match language and using `主要承担`.

### Applied Revision

```tex
本章的指标按失败模式组织。PPL 观察固定窗口内语言建模概率质量的整体漂移，Needle-in-a-Haystack~\cite{kamradt2023needle} 以精确匹配通过率检查长距离目标片段能否取回，LongBench 风格合成任务用于比较任务级输出在同一评分管线内的相对变化，RULER~\cite{hsieh2024ruler} 提供更高压力的长上下文组合能力检查；TPOT、KV Cache 占用与峰值显存则对应部署层代价。官方 LongBench 真实数据对照另置于第~\ref{subsec:ch4-longbench-official}~节，主要承担评测协议一致性检验与外部真实数据方向核验；本节主评测矩阵仍以 LongBench 风格合成任务为核心。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch4_experiments.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 33.3

- Report segment: 33
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 788
- Detector excerpt begins: `第 3.6 节把校准产物中的逐层 K 侧角色尺度转写为敏感度画像...`
- Status: applied

### Diagnosis

- Main AIGC triggers: compressed section-list style, quoted abstract phrase `画像形状`, over-mechanical `折叠为单一阈值`, and a broad Chapter 4 handoff that sounded like a full deployment evaluation claim.
- Rewrite goal: preserve the allocator and system handoff while correcting the AutoK coverage-threshold direction and making the Chapter 4 handoff more bounded.
- Style constraints: avoid unnecessary quotes, avoid over-abstract phrasing, avoid saying AutoK makes a final automatic decision, and keep system evaluation scoped to TPOT and related system readings.

### Preserved Information

- Section~`\ref{sec:ch3-allocator}` still turns calibration artifacts into layer-level budget decisions.
- The source signal remains the per-layer K-side role scale.
- The sensitivity profile remains `$S_{K,\alpha}$`.
- BA-`$k$` remains the main allocator.
- The normalized coverage function `$\Gamma(k)$` remains part of the AutoK mechanism.
- The coverage threshold `$\rho$` is still used by `\texttt{AutoK}` to obtain a minimum protected-layer count, now explicitly as a candidate.
- Section~`\ref{sec:ch3-deployment}` still provides offline artifact fields, fused decode kernel interfaces, and memory-access/arithmetic-intensity decompositions for the three paths.
- Chapter 4 still follows these fixed interfaces.
- Chapter 4 still reports fidelity, low-bit-path effects and boundaries, cross-model policy regimes, and system readings relative to the reference decode path.

### Review Gate

- Technical reviewer: PASS; confirmed the allocator and system handoff information is preserved.
- Chinese academic writing reviewer: first pass failed on unnatural wording and hard phrases; final version passed after replacing `用到层级预算`, `反推`, `补齐系统接口`, and `跨模型策略适用区间`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 3 allocator definitions and Chapter 4 result organization.
- Skeptical reviewer: first pass failed because the coverage-threshold direction was inaccurate and the deployment wording was broad; final version passed after stating that `\rho` is given and AutoK generates a candidate, and after narrowing system results to TPOT-style readings.

### Applied Revision

```tex
分配部分接着把校准产物转化为层级预算。第~\ref{sec:ch3-allocator}~节从逐层 K 侧角色尺度得到敏感度画像 $S_{K,\alpha}$，并据此定义 BA-$k$ 主线分配器；归一化覆盖度函数 $\Gamma(k)$ 描述前 $k$ 个保护层对敏感度画像的累计覆盖程度。给定覆盖阈值 $\rho$ 后，\texttt{AutoK} 据此生成最小保护层数候选。第~\ref{sec:ch3-deployment}~节说明系统接口，列出离线校准产物字段、融合解码核接口，以及三条路径的访存和算术强度分解。第四章将基于这些固定接口报告质量保真、低比特路径的缓解效果与边界证据、跨模型策略的适用区间，并比较融合解码路径相对参考解码的 TPOT 等系统读数。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 33.2

- Report segment: 33
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 786
- Detector excerpt begins: `第3.4 节把行为对齐落到注意力分布 KL代理上...`
- Status: applied

### Diagnosis

- Main AIGC triggers: a long outline-style sentence, colon-led enumeration of three paths, mixed English technical phrases without enough Chinese syntactic integration, and an over-compressed `unique variable` statement for the KIVI-style comparison.
- Rewrite goal: split the paragraph into the calibration rule, the three path roles, the RoleAlign artifact/runtime boundary, and the KIVI-style comparison boundary.
- Style constraints: avoid unnecessary colon and parenthetical explanation, avoid `per-channel` / `per-token` where Chinese equivalents are natural, avoid overclaiming RoleAlign as fully restoring all low-bit behavior, and spell out the KIVI-style comparison without implying identical backend details.

### Preserved Information

- Section~`\ref{sec:ch3-calibration}` still defines behavior alignment through the attention-distribution KL proxy.
- Candidate parameter search, robust selection, and fallback rules are still preserved.
- Section~`\ref{sec:ch3-paths}` still instantiates the calibration rule into three cross-bit-width paths.
- `\texttt{INT8}` remains the trusted baseline path.
- Symmetric `\texttt{INT4}` still exposes the low-bit collapse direction.
- `\texttt{INT4-RoleAlign}` still uses per-channel Key and per-token Value asymmetric quantization, rewritten as `逐通道 Key` and `逐 token Value`.
- Offline percentile parameters and axis metadata still enter the path artifact.
- Runtime still generates affine parameters according to K/V-side rules.
- Degradation remains jointly modulated by model family, scale, and GQA configuration, with the boundary delegated to Section~`\ref{sec:exp-rolealign}`.
- The KIVI-style comparison remains a same-format comparison, now bounded to K/V axis layout and asymmetric affine quantization.
- The core comparison variable remains endpoint statistics, with KIVI-style using runtime min/max and RoleAlign using evaluation-time frozen percentile parameters while still computing affine parameters from current tensors at runtime.

### Review Gate

- Technical reviewer: PASS; confirmed all method roles and runtime boundaries are preserved.
- Chinese academic writing reviewer: first pass failed on mixed English expressions and hard phrasing; final version passed after replacing `per-channel`, `per-token`, `离线 percentile`, and `按 K/V 轴`.
- Cross-chapter consistency reviewer: PASS; confirmed the RoleAlign/KIVI-style comparison matches Chapter 3 and Chapter 4.
- Skeptical reviewer: first pass failed on over-strong `恢复低比特可用性` and an imprecise `only variable` statement; final version passed after narrowing to `缓解低比特失稳` and spelling out endpoint statistics.

### Applied Revision

```tex
第~\ref{sec:ch3-calibration}~节把行为对齐具体化为注意力分布 KL 代理，并在候选参数搜索中加入稳健选择与回退规则。第~\ref{sec:ch3-paths}~节继续把同一校准规则落实到三条跨位宽路径中。\texttt{INT8} 基准路径提供可信参考，对称 \texttt{INT4} 用来暴露低比特崩塌方向，\texttt{INT4-RoleAlign} 则以逐通道 Key 与逐 token Value 的非对称量化缓解低比特失稳。该路径把离线百分位参数与轴元数据写入产物，运行时再按 K/V 两侧规则生成仿射参数；其退化幅度受模型族、规模与 GQA 配置共同调制，相关边界见第~\ref{sec:exp-rolealign}~节。与 \texttt{KIVI-style} 的对比限定在相同 K/V 轴布局与非对称仿射口径内，核心差异是端点统计规则。\texttt{KIVI-style} 在运行时用 min/max 统计确定端点，\texttt{INT4-RoleAlign} 使用离线选定并在评测前冻结的百分位参数，运行时仍按当前张量计算仿射参数，从而把校准来源差异与格式差异分开。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 33.1

- Report segment: 33
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 784
- Detector excerpt begins: `第 3.1 节把注意力近似误差代数分解为分布侧扰动...`
- Status: applied

### Diagnosis

- Main AIGC triggers: table-of-contents style summary, regular verb chain such as `分解`, `绑定`, and `提供依据`, and the English shorthand `K-cliff` appearing without enough local explanation.
- Rewrite goal: preserve the chapter-summary function while making the paragraph read as a mechanism recap rather than a compressed outline.
- Style constraints: avoid unnecessary colon or parenthetical phrasing, avoid `xxxx 下`, replace bare `K-cliff` with a clearer Chinese diagnostic description, and keep the Key-side claim bounded by the paragraph's evidence.

### Preserved Information

- Section~`\ref{sec:ch3-problem}` still provides the algebraic decomposition of attention approximation error.
- The decomposition still separates distribution-side perturbation and aggregation-side perturbation.
- Section~`\ref{sec:ch3-motivation-kv}` still provides the diagnostic link between those two paths and K/V low-bit sensitivity.
- The Key side is still identified as more likely to trigger cliff-style instability in the cited comparisons.
- The Value-side boundary is preserved by stating that it does not show degradation of the same strength in the thesis comparisons.
- The paragraph still explains why the later calibration targets and allocation rules have a mechanism basis.

### Review Gate

- Technical reviewer: PASS; confirmed the revised paragraph preserves the decomposition and K/V diagnostic meaning.
- Chinese academic writing reviewer: first pass failed on bare `K-cliff`, `低比特条件下`, and hard `机制入口`; final version passed after switching to K/V diagnostic wording and `机制线索`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 3 and Chapter 4 evidence.
- Skeptical reviewer: first pass failed because `K-cliff 诊断说明` was too strong and omitted the Value-side contrast; final version passed after narrowing the claim to a bounded empirical judgment.

### Applied Revision

```tex
本章先说明注意力误差怎样进入输出。第~\ref{sec:ch3-problem}~节通过代数分解，把注意力近似误差写成分布侧扰动与聚合侧扰动；第~\ref{sec:ch3-motivation-kv}~节再借助 K/V 对照诊断给出较窄的经验判断，Key 侧低比特扰动更容易触发断崖式失稳，Value 侧在本文对照中没有出现同等强度的退化。后续校准目标与分配规则，主要围绕这两条机制线索展开。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 32

- Report segment: 32
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 707--715
- Detector excerpt begins: `离线阶段的额外代价来自候选参数扫描...`
- Status: applied

### Diagnosis

- Main AIGC triggers: definition-heavy opening, explanatory parenthetical phrasing, and an over-compressed final sentence that implied all paths differ only by candidate-set size.
- Rewrite goal: keep the same offline complexity formula while making the paragraph less mechanical and more careful about path-specific proxy costs.
- Style constraints: avoid unnecessary parentheses, avoid English-style labels in Chinese prose where possible, avoid `xxxx 上` phrasing, and keep the complexity statement bounded to leading-order search cost.

### Preserved Information

- The offline-stage overhead still comes mainly from candidate parameter scanning.
- The variables `|\Theta_{\mathrm{path}}|`, `N`, `L`, `H_q`, `n`, and `d_k` retain the same meanings.
- The path-level offline search complexity remains `\mathcal O(|\Theta_{\mathrm{path}}| N L H_q n d_k)`.
- The use of `H_q` rather than `H_{kv}` remains tied to attention-distribution comparison at the Query-head granularity.
- `\texttt{INT8}` baseline, symmetric `\texttt{INT4}`, and `\texttt{INT4-RoleAlign}` still share the same search-flow abstraction.
- The revision no longer claims that path differences only come from candidate-set size; it also preserves proxy-specific constant-factor differences.
- The K path remains associated with KL statistics, while the V path remains associated with the output-perturbation proxy.

### Review Gate

- Technical reviewer: PASS; confirmed the complexity expression and proxy scope remain accurate.
- Chinese academic writing reviewer: first two passes failed on mechanical wording and English-style labels; final version passed after replacing `attention-distribution KL`, `K-path`, `V-path`, and `落在...上`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the preceding calibration and RoleAlign path definitions.
- Skeptical reviewer: first pass failed because the original rewrite overclaimed that differences only came from candidate size; final version passed after adding proxy-instantiation and constant-factor boundaries.

### Applied Revision

```tex
离线开销主要来自候选参数扫描。记候选集合规模为 $|\Theta_{\mathrm{path}}|$、校准样本数为 $N$、模型层数为 $L$、Query 头数为 $H_q$、每个样本的校准长度为 $n$，头维度为 $d_k$。路径级离线搜索复杂度可记为
\begin{equation}
T_{\mathrm{calib}}^{\mathrm{path}}
=
\mathcal O\!\bigl(
|\Theta_{\mathrm{path}}|\,N\,L\,H_q\,n\,d_k
\bigr),
\end{equation}
式中采用 $H_q$ 而非 $H_{kv}$，是因为这一阶次描述注意力分布 KL 代理的主要计算；该代理逐 Query 头比较参考分布与量化分布。\texttt{INT8} 基准路径、对称 \texttt{INT4} 与 \texttt{INT4-RoleAlign} 使用同一搜索流程，但各路径的代理实例化并不完全相同。K 路径沿 KL 统计计算，V 路径按输出扰动代理统计；在主导阶次表示中，路径差异主要体现为候选集合规模差异，以及代理实现带来的常数项差异。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hbox at line 369 remains unrelated to this segment.

## Segment 31b

- Report segment: 31
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 702
- Detector excerpt begins: `系统侧落地按三个分工组织...`
- Status: applied

### Diagnosis

- Main AIGC triggers: template-like three-way organization, exposed internal implementation naming, and blurred distinction between quality reference path, format comparison, and backend system readings.
- Rewrite goal: preserve the three system roles while clarifying their external paper-facing meanings.
- Style constraints: avoid unnecessary parentheses and quotes, avoid internal backend labels in paper-facing prose, and keep the Chapter 4 TPOT column relation bounded.

### Preserved Information

- The system implementation still keeps three categories of paths.
- `\texttt{INT8-Canonical}` remains supported by the `\texttt{INT8}` fused kernel.
- `\texttt{INT8-Canonical}` still validates stable closure of behavior-guided calibration under a conservative bit-width setting.
- `\texttt{INT4-RoleAlign}` still uses a reference decode path for quality and semantic-consistency checking.
- The Chapter 4 TPOT table reference path remains the timing counterpart for the reference backend.
- The `\texttt{INT4}` extension still covers system-boundary measurement.
- KIVI-style comparison and Triton fused-backend readings are both preserved.
- The next section still analyzes the three paths by memory access, storage, and compute cost.

### Review Gate

- Technical reviewer: PASS; confirmed the three-role system decomposition remains intact.
- Chinese academic writing reviewer: first pass failed on template wording, `xxxx 下`, and table-column punctuation; final version passed after rewriting the paragraph and removing unnecessary quotes/parentheses.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 4 TPOT table and Chapter 3 deployment scope.
- Skeptical reviewer: first pass failed because `torch_ref`, RoleAlign-to-table relation, and KIVI/Triton wording could confuse internal implementation with paper-facing roles; final version passed after removing the internal name and separating reference backend, KIVI-style comparison, and Triton backend readings.

### Applied Revision

```tex
系统落地保留三类路径，各自承担不同验证目标。\texttt{INT8-Canonical} 基准路径由 \texttt{INT8} 融合核支撑，用来检验行为引导校准能否在保守位宽设置中形成稳定闭环。\texttt{INT4-RoleAlign} 的质量评估主线采用参考解码实现进行语义一致性核验；第四章 TPOT 表中的参考路径 \texttt{INT4} 列对应该类参考后端的时间口径。用于系统边界测量的 \texttt{INT4} 扩展区分格式对照和后端实现，并覆盖 KIVI-style 对照以及 Triton 融合后端读数。下一节转向三条路径在访存、存储和算力维度的开销分析。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 30c-31a

- Report segment: 30 and 31
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 692--700
- Detector excerpt begins: `为兼容 GQA...`
- Status: applied

### Diagnosis

- Main AIGC triggers: mechanical formula introduction, dense parenthetical condition, and mixed English `grid/query head/block` implementation phrasing.
- Rewrite goal: preserve the GQA mapping and TPOT-cost explanation while making the paragraph less like an implementation note.
- Style constraints: avoid unnecessary parentheses, prefer Chinese terms for `grid`, and keep all mathematical symbols unchanged.

### Preserved Information

- GQA compatibility still requires mapping Query heads to shared KV heads.
- `$H_q$` and `$H_{kv}$` remain the Query-head and KV-head counts.
- The divisibility condition `$H_{kv}\mid H_q$` remains, with the statement that the GQA models in this thesis satisfy it.
- The repetition factor formula and `$h_{kv}` mapping formula remain unchanged.
- The kernel is still organized in a `$(B,H_q)$` parallel grid.
- Each Query head still directly accesses the corresponding `$h_{kv}$` slice.
- The implementation still avoids explicitly copying KV heads into `$H_q$` replicas.
- The addressing pattern still affects in-block memory-access coalescing, metadata broadcast, and register use.
- These effects are still reported together with unpacking cost in TPOT.

### Review Gate

- Technical reviewer: PASS; confirmed GQA mapping and formulas are preserved.
- Chinese academic writing reviewer: first pass failed on long formula-introduction wording and mixed `grid/query head` phrasing; final version passed after splitting the sentence and using `网格`, `访问`, and `访存合并`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 2 GQA notation and Chapter 4 TPOT/Hkv discussion.
- Skeptical reviewer: PASS; found no information loss or claim drift.

### Applied Revision

```tex
为兼容 GQA~\cite{ainslie2023gqa}，融合核需要把 Query 头映射到共享的 KV 头。记 Query 头数为 $H_q$、KV 头数为 $H_{kv}$；本文涉及的 GQA 模型均满足 $H_{kv}\mid H_q$。重复因子定义为
...
核函数按 $(B,H_q)$ 网格组织并行。每个 Query 头直接访问对应的 $h_{kv}$ 切片，因此不需要把 KV 头显式复制成 $H_q$ 个副本。这个寻址方式会影响块内访存合并、元数据广播和寄存器占用，并与反打包开销一起反映到 TPOT 中。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 30b

- Report segment: 30
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 690
- Detector excerpt begins: `INT4路径在数据表示上引入额外解包成本...`
- Status: applied

### Diagnosis

- Main AIGC triggers: dense semicolon list, mixed English implementation labels, and compressed storage/quantization semantics that could blur symmetric and asymmetric INT4 ranges.
- Rewrite goal: preserve all nibble-packing and runtime-path details while separating storage code representation from the symmetric diagnostic quantization grid.
- Style constraints: reduce engineering shorthand, avoid unnecessary parentheses, and keep fixed implementation labels only where useful.

### Preserved Information

- `\texttt{INT4}` still reduces stored payload bytes but introduces unpacking cost.
- Nibble packing still stores two 4-bit integers in one 8-bit byte.
- Packed storage still maps integer codes into the unsigned `$[0,15]$` nibble domain.
- The asymmetric `\texttt{INT4}` codebook remains `$[-8,7]$` with 16 levels.
- The symmetric diagnostic path is now explicitly tied back to `$q_{\max}=7$` and the `$[-7,7]$` grid from the calibration section.
- Reading still uses shift and mask operations to recover half-byte values.
- Dequantization remains path-dependent, with scale for the symmetric path and `$(s,\zeta)$` for `\texttt{INT4-RoleAlign}`.
- The symmetric `\texttt{INT4}` diagnostic path still uses a wrapper, explicitly materializes an INT8 intermediate tensor, and reuses the `\texttt{INT8}` fused kernel.
- `\texttt{INT4-RoleAlign}` still uses kernel-internal unpacking and reads K-side per-channel and V-side per-token `$(s,\zeta)$`.
- `\texttt{INT4-RoleAlign}` still avoids explicit INT8 intermediate tensor materialization.
- The paragraph still states that 4-bit payloads reduce global read bytes, while unpacking and register pressure reappear in TPOT.
- Appendix and Chapter 4 references remain unchanged.

### Review Gate

- Technical reviewer: PASS; confirmed the storage-domain and path-dependent dequantization semantics.
- Chinese academic writing reviewer: first pass failed on `wrapper`, `in-kernel unpack`, `per-channel`, and `每输出 token 时间`; final version passed after using `wrapper 封装`, `核内解包`, `逐通道`, and `每输出 token 的时间 TPOT`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the asymmetric quantization section, appendix variants, and Chapter 4 TPOT references.
- Skeptical reviewer: first pass failed because the original rewrite could conflict with the symmetric `[-7,7]` grid and overgeneralize `$(s,\zeta)`; final version passed after explicitly separating symmetric and asymmetric paths.

### Applied Revision

```tex
\texttt{INT4} 的表示形式减少了存储字节数，但解包开销也进入运行路径。nibble packing 将两个 4-bit 整数放入一个 8-bit 字节。写入 packed 缓存时，整数码值先平移到无符号 $[0,15]$ 域再存入 nibble；非对称 \texttt{INT4} 使用 $[-8,7]$ 的 16 级码本，对称诊断路径仍按前文 $q_{\max}=7$ 的 $[-7,7]$ 网格产生码值。读取时，核函数用位移和掩码拆出半字节，再还原为路径对应的有符号整数，并按对应参数反量化；对称路径使用 scale，\texttt{INT4-RoleAlign} 使用 $(s,\zeta)$。本文把执行路径分为两类。对称 \texttt{INT4} 诊断路径采用 wrapper 封装，先将 nibble 缓存批量反打包为 INT8 张量，再复用 \texttt{INT8} 融合核完成片上反量化、点积、online softmax 和输出累加。\texttt{INT4-RoleAlign} 的非对称融合扩展采用核内解包，核函数直接读取 K 侧逐通道与 V 侧逐 token 的 $(s,\zeta)$，在片上存储中完成 nibble 解包和非对称反量化，避免显式 INT8 中间张量物化。4-bit 载荷减少全局读取字节数，反打包和寄存器压力则会重新体现在每输出 token 的时间 TPOT 中。相关变体命名与角色见附录第~\ref{sec:app-triton-variants}~节，端到端 TPOT 数字见第四章第~\ref{subsec:ch4-tpot-4k}~节。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 29b-30

- Report segment: 29 and 30
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 658--688
- Detector excerpt begins: `融合核函数沿序列维度分块循环...`
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-led implementation listing, parentheses-heavy inline explanations, mixed `block/query` terminology, and a mechanical final sentence about division.
- Rewrite goal: keep the online-softmax recurrence and implementation detail intact while improving Chinese readability around the formulas.
- Style constraints: do not alter the mathematical recurrence, avoid unnecessary parentheses, and use consistent Chinese wording for `block`.

### Preserved Information

- The fused kernel still loops by sequence blocks.
- Each block still reads low-bit `$K_B,V_B$`, scale parameters, and metadata from quantized cache.
- Unpacking and dequantization still occur in SRAM/register on-chip storage.
- The dot product remains `$z_i = q k_i^\top / \sqrt{d_k}$`.
- `$k_i$` remains the dequantized `$i$`-th Key row vector.
- Online softmax still maintains cross-block recurrence state with the FlashAttention citation.
- The state variables remain row maximum `$m^{(r)}$`, normalization factor `$\ell^{(r)}$`, and normalized output accumulator `$o^{(r)}$`.
- `$B$` still denotes token indices in the `$r{+}1$`-th block, with only the Chinese explanatory word changed from `block` to `块`.
- `$v_i$` remains the dequantized `$i$`-th Value row vector.
- The recurrence remains equivalent to FlashAttention's online softmax.
- The implementation still keeps the unnormalized accumulator `$\tilde o^{(r+1)} = \ell^{(r+1)}\,o^{(r+1)}$`.
- The final division by `$\ell^{(\mathrm{final})}$` remains deferred until all blocks are processed, avoiding repeated division.

### Review Gate

- Technical reviewer: PASS; confirmed all recurrence semantics and implementation details are preserved.
- Chinese academic writing reviewer: first pass failed on `block` mixing, `数学等价`, and `等全部 block`; final version passed after normalizing prose and formula annotation to `块`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the FlashAttention citation, Triton kernel explanation, and following INT4 path paragraph.
- Skeptical reviewer: PASS; found no information loss or overclaim.

### Applied Revision

```tex
融合核按序列维度分块推进。每个块从量化缓存读取低比特 $K_B,V_B$ 以及对应的缩放参数和元数据，在 SRAM 和寄存器等片上存储中完成解包和反量化，并直接计算当前查询向量与该块 Key 的点积 $z_i = q k_i^\top / \sqrt{d_k}$，其中 $k_i$ 表示反量化后的第 $i$ 个 Key 行向量。随后，核函数用在线 softmax 维护跨块递推状态~\cite{dao2022flashattention}。设第 $r$ 个块的状态包含行最大值 $m^{(r)}$、归一化因子 $\ell^{(r)}$ 和归一化输出累加器 $o^{(r)}$，并令
...
B = \{\text{第 } r{+}1 \text{ 个块中的 token 索引}\},
...
这里 $v_i$ 表示反量化后的第 $i$ 个 Value 行向量。上述递推与 FlashAttention 的 online softmax 等价；实现中保留非归一化累加器 $\tilde o^{(r+1)} = \ell^{(r+1)}\,o^{(r+1)}$，待全部块处理完后再除以 $\ell^{(\mathrm{final})}$，从而避免逐步重复除法。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 29a

- Report segment: 29
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 656
- Detector excerpt begins: `自回归解码阶段每步只引入一个新的query token...`
- Status: applied

### Diagnosis

- Main AIGC triggers: template-like bottleneck statement, rigid `朴素路径...过程功能正确` sequence, and translated engineering phrasing such as `压入同一片上流水线`.
- Rewrite goal: preserve the systems motivation for the Triton fused decode kernel while making the paragraph read like normal technical exposition.
- Style constraints: reduce English-style Chinese, keep the Triton citation, and preserve the linear-growth memory cost claim.

### Preserved Information

- Autoregressive decode still adds only one new query token at each step.
- Attention still needs to access the full historical KV Cache.
- The bottleneck is still memory access.
- The naive path still reads K/V from low-bit cache, fully dequantizes them into FP16 intermediate tensors, and sends them to standard attention.
- The naive path remains functionally correct.
- Intermediate tensor materialization and memory traffic still grow linearly with sequence length.
- The `\texttt{INT8}` path still uses a Triton-based fused decode kernel.
- Dequantization, dot product, online softmax, and output accumulation are still placed in one on-chip pipeline.
- The goal remains reducing global-memory traffic.

### Review Gate

- Technical reviewer: PASS; confirmed the decode access pattern, naive path, linear cost, and fusion components are preserved.
- Chinese academic writing reviewer: first pass failed on `query token`, `压力落在访存`, and translated engineering phrasing; final version passed after using `查询 token`, `主要瓶颈来自访存`, and `放入同一条片上流水线`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the following online-softmax derivation and Chapter 4 system evaluation.
- Skeptical reviewer: PASS; found no information loss or overclaim.

### Applied Revision

```tex
自回归解码每前进一步只新增一个查询 token，但注意力仍需访问全部历史 KV Cache，主要瓶颈来自访存。朴素实现会先从低比特缓存取出 K/V，将其完整反量化为 FP16 中间张量，再交给标准注意力计算；这条路径功能正确，代价是中间张量物化和显存读写会随序列长度线性增长。\texttt{INT8} 路径采用基于 Triton~\cite{tillet2019triton} 的融合解码核，把反量化、点积、online softmax 和输出累加放入同一条片上流水线，减少往返全局内存的数据量。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 28c

- Report segment: 28
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 649
- Detector excerpt begins: `Prefill阶段按路径规则...`
- Status: applied

### Diagnosis

- Main AIGC triggers: rigid Prefill/Decode parallelism, engineering-manual verbs such as `路由`, and an imprecise statement about avoiding low-bit cache materialization.
- Rewrite goal: keep the runtime data-flow contract while clarifying that the fusion path avoids materializing dequantized intermediate tensors, not the low-bit cache itself.
- Style constraints: avoid unnecessary colon expansion and reduce raw English phrase-as-verb usage.

### Preserved Information

- During prefill, the current block's K/V are quantized and written into cache according to the path rule.
- During decode, K/V are read from the historical quantized cache.
- The read K/V are sent to the corresponding attention backend.
- The Decode path input remains limited to fixed artifacts and already-written historical cache.
- The data-flow boundary supports later fused decode kernels consuming quantized cache directly.
- The fusion statement now specifies avoidance of dequantized intermediate tensor materialization.

### Review Gate

- Technical reviewer: PASS; confirmed Prefill write, Decode read, backend handoff, and input contract are preserved.
- Chinese academic writing reviewer: first pass failed on `进入 Decode 后`, `路由`, and `中间物化`; final version passed after using `解码阶段开始后`, `送入`, and `中间张量物化`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the runtime path table and the following Triton fusion section.
- Skeptical reviewer: first pass failed because `跳过低比特缓存的中间物化` was semantically imprecise; final version passed after rewriting it as avoidance of dequantized intermediate tensor materialization.

### Applied Revision

```tex
预填充时，当前块的 K/V 先按路径规则量化并写入缓存；解码阶段开始后，系统从历史量化缓存读取 K/V，并送入相应的注意力后端。这样的数据流把 Decode 路径的输入限定为固定产物和已经写入的历史缓存，也为后续融合解码核直接消费量化缓存、避免反量化后的中间张量物化提供接口边界。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 28b

- Report segment: 28
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 647
- Detector excerpt begins: `任意 t′ <t 的历史缓存项...`
- Status: applied

### Diagnosis

- Main AIGC triggers: semicolon-heavy chaining, quoted meta-labels, mixed English `seed`, and a compressed final sentence that blurs K/V timing.
- Rewrite goal: keep the append-only cache semantics and adaptive-protection scope while making the validation and RoleAlign statements more precise.
- Style constraints: avoid unnecessary quotation marks and parentheses, avoid `xxxx 下`, and do not over-attach the multi-seed bitwise result to a chapter reference that reports the main INT8-Canonical readings.

### Preserved Information

- For any `$t'<t$`, historical cache item `$\hat x_{t'}^{(l)}$` is not rewritten at step `$t$`.
- Cache writing remains monotonic and append-only.
- Multi-random-seed bitwise consistency remains the indirect check for deterministic writing and closed history.
- Chapter~4 Section~`\ref{subsec:ch4-int8-canonical}` remains the reference for the fixed-protocol `\texttt{INT8-Canonical}` main readings.
- Adaptive protection is still enabled only for `\texttt{INT8-Canonical}` in the main experiments.
- Other symmetric path cases still use constant `$\theta_{\mathrm{path}}^{(l)}$`.
- `\texttt{INT4-RoleAlign}` still uses `$h^{K/V}$` rather than adaptive protection.
- K-side parameters remain reused after prefill, while V-side parameters remain computed with new-token writes.

### Review Gate

- Technical reviewer: PASS; confirmed the cache semantics and path scopes are preserved.
- Chinese academic writing reviewer: first pass failed on `多 seed` and a rigid semantic label; final version passed after using `多随机种子` and removing `xxxx 下` wording.
- Cross-chapter consistency reviewer: first pass failed because the Chapter~4 reference should not be written as direct proof of bitwise consistency and because K-side timing needed to be explicit; final version passed after narrowing the reference and spelling out K/V timing.
- Skeptical reviewer: PASS; found no information loss or overclaim after the cross-chapter fixes.

### Applied Revision

```tex
对任意 $t'<t$，第 $t$ 步不会改写历史缓存项 $\hat x_{t'}^{(l)}$，缓存只按时间追加。多随机种子复现中的逐位一致结果，为写入过程确定且历史缓存封闭的语义提供了间接核验；第四章第~\ref{subsec:ch4-int8-canonical}~节给出固定协议得到的 \texttt{INT8-Canonical} 主线读数。自适应保护只在主线实验的 \texttt{INT8-Canonical} 路径中开启；其余对称路径使用常量 $\theta_{\mathrm{path}}^{(l)}$。\texttt{INT4-RoleAlign} 按照 $h^{K/V}$ 给出的 K/V 两侧规则生成仿射参数，其中 K 侧在预填充后复用，V 侧随新 token 写入即时计算，不依赖自适应保护机制。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings.

## Segment 28a

- Report segment: 28
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 645
- Detector excerpt begins: `其中θ(path)表示离线冻结的路径规则...`
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-led definition lists, repeated semicolon partitioning, dense mixed English runtime terminology, and manual-like wording such as `现场计算`.
- Rewrite goal: preserve the definitions of `$\theta_{\mathrm{path}}^{(l)}$`, `$g_t$`, and `$h^{K/V}$` while turning the paragraph into normal explanatory prose.
- Style constraints: avoid unnecessary colon expansion, keep implementation terms where they are fixed field names, and avoid wording that implies online updates to frozen offline artifacts.

### Preserved Information

- `$\theta_{\mathrm{path}}^{(l)}$` remains the offline frozen path-parameter set.
- Symmetric paths still correspond to static scale.
- `\texttt{INT4-RoleAlign}` still corresponds to frozen percentile parameters `$(p_K,p_V)$`, quantization-axis markers, and boundary metadata.
- `$g_t$` still depends only on the current token's write tensor at that layer and offline parameters.
- `$g_t$` still follows the Section~`\ref{subsec:ch3-int8-baseline}` per-token maximum trigger rule.
- The current group scale is still determined by the INT8 adaptive-protection logic rather than by changing historical cache or offline artifacts.
- `$h^{K/V}$` still describes the runtime mapping for `\texttt{INT4-RoleAlign}` on K and V sides.
- K-side affine parameters are still computed once during prefill from per-channel data according to the frozen percentile and then reused.
- V-side affine parameters are still computed at each new-token write using per-token data.

### Review Gate

- Technical reviewer: PASS; confirmed the definitions and runtime dependencies are preserved.
- Chinese academic writing reviewer: first two passes failed on mixed English terminology and the `g_t` sentence; final version passed after using `静态尺度 scale`, `percentile 参数`, and a smoother adaptive-protection clause.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the INT8 adaptive rule, RoleAlign axes, runtime path table, and Chapter 4 usage.
- Skeptical reviewer: first pass failed because `刷新当前组 scale` could be read as updating offline artifacts; final version passed after changing this to scale determination by adaptive-protection logic.

### Applied Revision

```tex
这里，$\theta_{\mathrm{path}}^{(l)}$ 是离线冻结的路径参数集合。对称路径对应静态尺度 scale，\texttt{INT4-RoleAlign} 对应冻结的 percentile 参数 $(p_K,p_V)$、量化轴标记和边界元数据。$g_t$ 只读取当前 token 在该层待写入的张量与离线参数，并依据第~\ref{subsec:ch3-int8-baseline}~节的逐 token 最大值触发规则，通过自适应保护逻辑确定当前组 scale。$h^{K/V}$ 描述 \texttt{INT4-RoleAlign} 在 K 和 V 两侧的运行时映射。K 侧在预填充阶段依据冻结 percentile，用逐通道数据一次性计算 $(s_K,\zeta_K)$，之后保持不变并复用；V 侧在每个新 token 写入时，用逐 token 数据即时计算 $(s_V,\zeta_V)$。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hbox at line 369; no undefined references or citation warnings. The previous overfull hbox at lines 644--646 no longer appears after this rewrite.

## Segment 27b

- Report segment: 27
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 632
- Detector excerpt begins: `在线推理阶段第t个新token...`
- Status: applied

### Diagnosis

- Main AIGC triggers: formula-introduction wording is rigid and close to an English-style technical manual.
- Rewrite goal: keep the online write semantics while making the formula lead-in shorter and more natural.
- Style constraints: avoid unnecessary punctuation expansion and avoid changing the following equation or branch definitions.

### Preserved Information

- The sentence still refers to online inference.
- The write still concerns the $t$-th new token.
- The target layer remains the $l$-th layer.
- The following equation is still introduced as a unified notation for quantized cache writing.

### Review Gate

- Technical reviewer: PASS; confirmed that the candidate preserves the write event and does not alter the formula semantics.
- Chinese academic writing reviewer: PASS; confirmed the wording is more natural than `阶段...可写为`.
- Cross-chapter consistency reviewer: PASS; found no conflict with the runtime artifact interface or later Chapter 4 use.
- Skeptical reviewer: PASS; found no information loss or claim drift.

### Applied Revision

```tex
在线推理接收第 $t$ 个新 token 时，第 $l$ 层的量化写入统一记作
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; no undefined references or citation warnings.

## Segment 27a

- Report segment: 27
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 630
- Detector excerpt begins: `use_attn_temperature: false关闭...`
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-led field listing, parenthetical table pointer, mixed English runtime terms, and an overlong implementation sentence.
- Rewrite goal: keep the runtime artifact fields and K/V affine-parameter generation semantics while changing the paragraph from an interface dump into readable prose.
- Style constraints: avoid unnecessary parentheses and avoid YAML-style `key: value` prose when a Chinese sentence can state the same setting.

### Preserved Information

- The three paths still write different fields into `$\mathcal A_{\mathrm{path}}$`.
- Table~`\ref{tab:ch3-runtime-paths}` remains the detailed field reference.
- `\texttt{INT8}` baseline still stores per-group static scale and group metadata.
- `inv\_tau` still exists in the artifact.
- Mainline runtime still disables attention temperature by setting `\texttt{use\_attn\_temperature}` to `\texttt{false}`.
- Symmetric `\texttt{INT4}` still uses the same field organization while lowering the quantization grid to 4-bit.
- `\texttt{INT4-RoleAlign}` still adds K/V-side percentile selection records and axis metadata to quantization parameters.
- Runtime affine parameters are still generated separately by K/V role.
- K-side parameters are still computed once from per-channel data during prefill according to frozen percentiles and then reused.
- V-side parameters are still computed at each new-token write using per-token data.

### Review Gate

- Technical reviewer: initial and final passes approved the artifact-field and runtime-parameter semantics.
- Chinese academic writing reviewer: first pass failed on `字段格式`, `现场计算`, `prefill` and mixed English phrasing; final version passed after rewriting them as `字段组织`, `即时计算`, and `预填充阶段`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the runtime path table, RoleAlign K/V axes, and subsequent `h^{K/V}` rules.
- Skeptical reviewer: PASS; confirmed no information loss or implementation-semantics drift.

### Applied Revision

```tex
三条路径写入 $\mathcal A_{\mathrm{path}}$ 的字段并不相同，具体对照见表~\ref{tab:ch3-runtime-paths}。\texttt{INT8} 基准路径保存逐组静态 scale 与分组元数据，inv\_tau 字段保留在产物中，但主线运行时将 \texttt{use\_attn\_temperature} 设为 \texttt{false}。对称 \texttt{INT4} 沿用这一字段组织，只把量化网格降为 4-bit。\texttt{INT4-RoleAlign} 则在量化参数字段中增加 K/V 两侧的 percentile 选择记录与轴向元数据。运行时再按 K/V 角色生成仿射参数。K 侧在预填充阶段依据冻结 percentile，用逐通道数据一次性计算 $(s_K,\zeta_K)$，之后保持不变并复用；V 侧在每个新 token 写入时，用逐 token 数据即时计算 $(s_V,\zeta_V)$。
```

### Verification

- `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`: PASS
- `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex`: PASS, generated 101-page PDF
- Residual log notes: existing Chapter 3 overfull hboxes at lines 369 and 644--646; no undefined references or citation warnings.

## Segment 26b

- Report segment: 26
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 541
- Detector excerpt begins: `AutoK 在第 3.6.4节直接读取 Γ(k)...`
- Status: applied

### Diagnosis

- Main AIGC triggers: `直接读取` program-like wording and a compressed cause-effect sentence.
- Rewrite goal: keep the transition into the AutoK subsection while making the shared-profile relationship explicit.
- Style constraints: avoid interface-manual wording and keep AutoK framed as a suggestion mechanism.

### Preserved Information

- The AutoK rule is still introduced in Section~`\ref{sec:ch3-autok}`.
- `$\Gamma(k)$` remains the basis for AutoK.
- AutoK still gives a minimum protected-layer-count suggestion.
- The suggestion still targets reaching a coverage threshold.
- The coverage criterion and BA-`$k$` still read the same sensitivity profile.

### Review Gate

- Technical reviewer: PASS; confirmed the `$\Gamma(k)$` input, minimum protection count, and shared-profile meaning are preserved.
- Chinese academic writing reviewer: first pass failed on program-like `返回`; final version passed after switching to `以 $\Gamma(k)$ 为依据`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Section~`\ref{sec:ch3-autok}` and Chapter 4 AutoK usage.
- Skeptical reviewer: PASS; confirmed the word `建议` preserves the candidate-generator boundary and does not imply an end-to-end automatic decision.

### Applied Revision

```tex
第~\ref{sec:ch3-autok}~节随后给出 \texttt{AutoK} 的具体规则。该规则以 $\Gamma(k)$ 为依据，给出达到覆盖阈值所需的最小保护层数建议；覆盖度准则与 BA-$k$ 方案因此读取同一份敏感度画像。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 26a

- Report segment: 26
- Source paragraph: `thesis/figures/fig_ch3_coverage_curves.tex`, line 81
- Detector excerpt begins: `图3-7  敏感度覆盖度曲线示意...`
- Status: applied

### Diagnosis

- Main AIGC triggers: dash-led caption structure, slogan-like `核心直觉`, and mixed `profile` wording.
- Rewrite goal: make the figure caption self-contained by naming the axes and preserving the concentrated/diffuse profile budget contrast.
- Style constraints: avoid instruction-manual tone while keeping the caption bounded as a schematic figure.

### Preserved Information

- The figure remains a schematic sensitivity coverage curve.
- The caption still compares concentrated and diffuse sensitivity profiles.
- The horizontal axis is protection layer count `$k$`.
- The vertical axis is sorted cumulative sensitivity `$\Gamma(k)$` over the first `$k$` layers.
- Given the same coverage threshold, concentrated profiles still reach the target with smaller `$k$`.
- Diffuse profiles still require covering more layers.
- The caption still explains how `\texttt{AutoK}` uses profile shape to generate a budget suggestion.

### Review Gate

- Technical reviewer: PASS; confirmed coverage-threshold semantics and AutoK budget meaning are preserved.
- Chinese academic writing reviewer: first pass failed on `转写` and `保护更多层`; second pass failed on mechanical `可以如何依据`; final version passed after changing to `生成预算建议的方式`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with `$\Gamma(k)$`, Chapter 3 AutoK, and Chapter 4 AutoK figure interpretations.
- Skeptical reviewer: first pass failed because the AutoK causal wording was too strong and the curve axes were implicit; final version passed after adding axis semantics and preserving the schematic boundary.

### Applied Revision

```tex
\caption{敏感度覆盖度曲线示意，图中以保护层数 $k$ 为横轴，以排序后前 $k$ 层累计敏感度 $\Gamma(k)$ 为纵轴。给定相同覆盖阈值，集中型画像用较小的 $k$ 即可达到目标覆盖度；弥散型画像则需要覆盖更多层。该示意说明 \texttt{AutoK} 依据画像形态生成预算建议的方式。}
```

### Verification

- PASS: `git diff --check -- thesis/figures/fig_ch3_coverage_curves.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 25

- Report segment: 25
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 317--321
- Detector excerpt begins: `INT4-RoleAlign与KIVI-style共享per-channel Key...`
- Status: applied

### Diagnosis

- Main AIGC triggers: English-heavy path labels, markdown-style emphasis inside LaTeX, bracketed contrast phrasing, and a dense one-paragraph comparison.
- Rewrite goal: clarify that `\texttt{KIVI-style}` and `\texttt{INT4-RoleAlign}` share the same low-bit K/V format but differ in endpoint-parameter source.
- Style constraints: avoid English-style Chinese, avoid overclaiming that the searched percentile is always better than min/max, and make runtime recomputation explicit.

### Preserved Information

- `$\operatorname{Percentile}(\cdot;100)=\max$` and `$\operatorname{Percentile}(\cdot;0)=\min$` remain the endpoint identities.
- `$(p_K,p_V)=(100,100)$` remains the min-max endpoint case for K and V paths.
- `\texttt{KIVI-style}` still determines endpoints at runtime using min/max statistics.
- `\texttt{INT4-RoleAlign}` still selects percentiles `$(p_K,p_V)` through offline search.
- Runtime still computes `$(s,\zeta)` from current tensors according to the selected percentile rather than using a frozen actual range.
- The core comparison remains endpoint-parameter source, not runtime range determination versus offline frozen actual range.
- `\texttt{INT4-RoleAlign}` still searches within `$(50,100]`.
- The controlled comparison remains assigned to Section~`\ref{subsec:ch3-rolealign-vs-kivi}`.
- The K/V double-axis asymmetric layout remains linked to Figure~`\ref{fig:ch3-rolealign-axis}`.

### Review Gate

- Technical reviewer: initial and final passes approved the endpoint identities, runtime recomputation semantics, comparison target, and figure/section references.
- Chinese academic writing reviewer: first pass failed on `K-path/V-path`, mixed `channel` wording, and mechanical `真正不同的是`; final version passed after switching to `K 路径/V 路径`, `通道`, and a bounded comparison sentence.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Chapter 4 Section~`\ref{subsec:ch3-rolealign-vs-kivi}` and the shared-format/different-parameter-source reading.
- Skeptical reviewer: first pass failed because `比 min-max 更稳定` sounded proven and runtime recomputation could be misread; final version passed after narrowing this to a search objective and stating current-tensor percentile statistics explicitly.

### Applied Revision

```tex
由于 $\operatorname{Percentile}(\cdot; 100) = \max$ 且 $\operatorname{Percentile}(\cdot; 0) = \min$，端点
\begin{equation}
(p_K, p_V) = (100, 100)
\end{equation}
正好对应 K 路径与 V 路径各自的 min-max 仿射端点。这也给出与 \texttt{KIVI-style} 对照的基准情形。\texttt{KIVI-style} 在运行时用 min/max 统计确定逐通道端点和逐 token 端点；\texttt{INT4-RoleAlign} 则先通过离线搜索选定百分位 $(p_K, p_V)$，运行时仍针对当前张量统计对应百分位，并分别逐通道、逐 token 计算 $(s, \zeta)$。在该对照口径下，核心差异是端点参数来自运行时 min/max 统计，还是来自离线搜索得到的百分位；并不是一方运行时确定实际范围、另一方离线冻结实际范围。\texttt{INT4-RoleAlign} 在 $(50, 100]$ 内搜索可能相对 min-max 更稳健的百分位端点，受控比较见第~\ref{subsec:ch3-rolealign-vs-kivi}~节。K 侧沿 token 维度聚合后按通道独立确定 $(s_K,\zeta_K)$，V 侧沿通道维度聚合后按 token 独立确定 $(s_V,\zeta_V)$；双轴非对称布局见图~\ref{fig:ch3-rolealign-axis}。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 24b

- Report segment: 24
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 278
- Detector excerpt begins: `Value侧使用逐token非对称量化...`
- Status: applied

### Diagnosis

- Main AIGC triggers: compact formula lead-in, missing natural pause before the token-specific boundary, and mechanical `使用逐 token` phrasing.
- Rewrite goal: make the Value-side per-token affine-parameter setup explicit while keeping the following percentile boundary formula unchanged.
- Style constraints: avoid parenthetical explanation and keep the sentence as a clean formula handoff.

### Preserved Information

- Value side still uses per-token asymmetric quantization.
- The text now states that Value-side asymmetric quantization parameters are established per token.
- The Value matrix remains `$V^{(l)}\in\mathbb{R}^{S\times d_v}$`.
- The boundary is still defined for the `$t$`-th token.
- The following percentile-clipping boundary formula remains the continuation of this sentence.

### Review Gate

- Technical reviewer: PASS; confirmed the Value-side per-token asymmetric quantization, matrix shape, token index, and formula handoff are preserved.
- Chinese academic writing reviewer: PASS; confirmed the wording is natural and not mechanically translated.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the Key-side contrast and the `$[B,H_{kv},S]$` Value-scale shape.
- Skeptical reviewer: PASS; no omitted information, claim narrowing, or formula-connection issue found.

### Applied Revision

```tex
Value 侧则按 token 建立非对称量化参数。设第 $l$ 层 Value 矩阵为 $V^{(l)}\in\mathbb{R}^{S\times d_v}$；对第 $t$ 个 token，分位数裁剪边界定义为
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 24a

- Report segment: 24
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 276
- Detector excerpt begins: `分位数统计沿序列维度聚合...`
- Status: applied

### Diagnosis

- Main AIGC triggers: compact semicolon chain, English `K-cliff` label, and abstract `同质化压缩`.
- Rewrite goal: explain the Key-side percentile statistics as a design consequence of per-channel parameters without changing the formula semantics.
- Style constraints: avoid the English label in the sentence and keep the section handoff in natural Chinese.

### Preserved Information

- Percentile statistics are still collected along the sequence dimension.
- Each channel still independently determines a parameter pair `$(s,\zeta)$`.
- Per-channel parameters still preserve the range of different feature directions.
- The coarse `\texttt{INT4}` grid remains the source of concern.
- The effect still concerns `$qK^\top$` ranking structure.
- The paragraph still connects the design to Section~`\ref{sec:ch3-motivation-kv}` and its Key-side low-bit instability diagnosis.

### Review Gate

- Technical reviewer: PASS; confirmed the sequence aggregation, per-channel parameters, `$(s,\zeta)$`, coarse-grid mechanism, and section handoff are preserved.
- Chinese academic writing reviewer: PASS; confirmed the wording is more natural and removes the English `K-cliff` label in this local sentence.
- Cross-chapter consistency reviewer: PASS; confirmed that replacing `K-cliff` with Key-side low-bit instability does not break the Section~`\ref{sec:ch3-motivation-kv}` anchor.
- Skeptical reviewer: PASS; no omitted information, semantic drift, or over-strong causal claim found.

### Applied Revision

```tex
这些分位数沿序列维度统计，因此每个通道各自得到一组 $(s,\zeta)$。这样做的目的不是改变 Key 的计算路径，而是在粗 \texttt{INT4} 网格下保留不同特征方向的取值范围，减少通道差异被同一尺度抹平后对 $qK^\top$ 排序造成的影响。该设计承接第~\ref{sec:ch3-motivation-kv}~节中关于 Key 侧低比特失稳的诊断。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 23b

- Report segment: 23
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 256
- Detector excerpt begins: `下文公式省略 batch 与 KV head 维度...`
- Status: applied

### Diagnosis

- Main AIGC triggers: implementation shapes packed into parentheses, mixed English labels, and an overlong formula handoff sentence.
- Rewrite goal: separate notation simplification from implementation tensor shapes while keeping the Key-side formula introduction precise.
- Style constraints: avoid unnecessary parentheses and make the shape statement read as normal Chinese technical prose.

### Preserved Information

- Subsequent formulas still omit batch and KV head dimensions.
- The retained formula dimensions remain sequence length and channel dimension.
- Runtime K/V tensor shape remains `$[B, H_{kv}, S, D]$`.
- Key scale tensor shape remains `$[B, H_{kv}, D]$`.
- Value scale tensor shape remains `$[B, H_{kv}, S]$`.
- Key side still uses per-channel asymmetric quantization.
- The Key matrix remains `$K^{(l)}\in\mathbb{R}^{S\times d_k}$`.
- The following percentile-clipping boundary is still defined for the `$j$`-th channel.

### Review Gate

- Technical reviewer: PASS; confirmed all shapes, dimension omissions, quantization axis, and formula handoff are preserved.
- Chinese academic writing reviewer: first pass failed on `Key scale 形状`, `Value scale 形状`, and the mechanical implementation sentence; final version passed after rewriting them as scale tensor shapes and splitting the notation statement.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 3 runtime shapes and the following Key/Value formulas.
- Skeptical reviewer: PASS; no omitted information, dimension error, overclaim, or formula-connection risk found.

### Applied Revision

```tex
下文公式只保留序列长度与通道维度，记号中省略 batch 维度与 KV head 维度。实现中 K/V 张量形状为 $[B, H_{kv}, S, D]$，Key 的 scale 张量形状为 $[B, H_{kv}, D]$，Value 的 scale 张量形状为 $[B, H_{kv}, S]$。Key 侧采用逐通道非对称量化。设第 $l$ 层 Key 矩阵为 $K^{(l)}\in\mathbb{R}^{S\times d_k}$；对第 $j$ 个通道，分位数裁剪边界定义为
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 23a

- Report segment: 23
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 254
- Detector excerpt begins: `\texttt{INT4-RoleAlign} 把第 3.5节开头...`
- Status: applied

### Diagnosis

- Main AIGC triggers: parenthetical diagnostic packing, colon-led K/V split, and English `per-channel` / `per-token` annotations.
- Rewrite goal: turn the diagnosis into two role-specific design sentences while keeping the K/V paths tied to the same calibration discipline.
- Style constraints: avoid unnecessary parentheses and keep the handoff to formulas natural.

### Preserved Information

- `\texttt{INT4-RoleAlign}` still uses the two diagnoses introduced at the beginning of Section~`\ref{sec:ch3-paths}`.
- Key perturbation still changes `$qK^\top$` ranking.
- Value quantization error still enters aggregation through attention weights.
- Key side still uses per-channel asymmetric quantization.
- Key side still uses channel-independent parameters to preserve feature-direction ranges.
- Value side still uses per-token asymmetric quantization.
- Value side still uses the current token dynamic range for later weighted aggregation.
- Both K/V paths still follow Section~`\ref{sec:ch3-calibration}` candidate search, stability filtering, and boundary-recording discipline.

### Review Gate

- Technical reviewer: PASS; confirmed the K/V design mapping and calibration discipline are preserved.
- Chinese academic writing reviewer: first pass failed on `落到 K/V 分路设计中` and `按当前 token 的动态范围服务后续加权聚合`; final version passed after rewriting these phrases.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Section~`\ref{sec:ch3-paths}`, Section~`\ref{sec:ch3-calibration}`, and the following formulas.
- Skeptical reviewer: PASS; no over-causal wording or new claim found.

### Applied Revision

```tex
\texttt{INT4-RoleAlign} 将第~\ref{sec:ch3-paths}~节开头的两条诊断落实为 K/V 分路设计。Key 扰动会改变 $qK^\top$ 排序，因此 Key 侧采用逐通道非对称量化，用通道独立参数保留各特征方向的取值范围；Value 误差经注意力权重进入聚合，因此 Value 侧采用逐 token 非对称量化，围绕当前 token 的动态范围保留后续加权聚合所需的信息。两条分路仍沿用第~\ref{sec:ch3-calibration}~节的候选搜索、稳定性筛选与边界记录纪律。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 22b

- Report segment: 22
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 249
- Detector excerpt begins: `因此对称 \texttt{INT4} 在本文中扮演格式选择...`
- Status: applied

### Diagnosis

- Main AIGC triggers: `扮演...锚点` formulation, colon-led explanation, and abstract `互相妥协`.
- Rewrite goal: keep the format-upgrade motivation while making the two conflicting statistical dimensions concrete.
- Style constraints: avoid colon expansion and use a natural Chinese handoff into the RoleAlign section.

### Preserved Information

- Symmetric `\texttt{INT4}` remains the lower-bound reference for low-bit format choice.
- A single symmetric scale must still cover Key channel amplitude differences.
- The same scale must also cover Value dynamic range changes along tokens.
- The two dimensions remain coupled by the same parameter under the coarse `\texttt{INT4}` grid.
- The next section still turns to `\texttt{INT4-RoleAlign}`.
- The two differences are still handled through separated K/V quantization paths in the next design.

### Review Gate

- Technical reviewer: PASS; confirmed the lower-bound reference, single-scale coupling, and RoleAlign handoff are preserved.
- Chinese academic writing reviewer: first pass failed on `格式选择的下界锚点`, `这两个维度落到同一参数后`, and `独立量化轴`; final version passed after rewriting these phrases.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with the next `\texttt{INT4-RoleAlign}` subsection.
- Skeptical reviewer: PASS; no overclaim about `\texttt{INT4-RoleAlign}` superiority found.

### Applied Revision

```tex
据此，本文把对称 \texttt{INT4} 作为低比特格式选择的下界参照。单一对称 scale 需要同时覆盖 Key 通道间的幅值差异和 Value 沿 token 变化的动态范围；当这两类差异由同一个参数覆盖时，会在粗 \texttt{INT4} 网格内相互牵制。下一节转向 \texttt{INT4-RoleAlign}，把两类差异交给分开的 K/V 量化路径处理。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 22a

- Report segment: 22
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 247
- Detector excerpt begins: `第3.2节与第4.3.2节的 Qwen系列读数...`
- Status: applied

### Diagnosis

- Main AIGC triggers: colon-led evidence packing, English `cliff`, and `剂量-响应` translation phrasing.
- Main technical risk: the original wording could be read as treating `\texttt{K4V8}` as single-side Key isolation evidence, while it is a task-level contrast with `V=8`.
- Rewrite goal: keep the mechanism explanation and Qwen empirical anchor while making the evidence hierarchy and cross-model boundary explicit.
- Style constraints: avoid English-style terms where a Chinese technical phrase works, and avoid implying full causal proof.

### Preserved Information

- Section~`\ref{sec:ch3-problem}` still supplies the mechanism line.
- Key perturbations still enter logits ranking before softmax changes the attention distribution.
- Qwen-series readings still come from Section~`\ref{sec:ch3-motivation-kv}` and Section~`\ref{sec:exp-kv-sensitivity}`.
- `\texttt{K4V8}` still indicates stronger instability when Key is at 4 bit in Qwen task-level contrasts.
- `\texttt{K8V4}` still does not show instability of the same strength.
- `\texttt{K4V4}` still lowers both K and V and remains auxiliary evidence.
- Complete cross-model interpretation remains assigned to Chapter 4 tables and figures.
- The cross-model boundary is now explicit: Qwen zero-collapse is stronger, LLaMA-3.1-8B is weaker in the current comparison, and scale/training data/GQA configuration co-modulate the boundary.

### Review Gate

- Technical reviewer: PASS; confirmed the mechanism, empirical anchor, and K/V evidence hierarchy are preserved.
- Chinese academic writing reviewer: first pass failed on `cliff` and `剂量响应方向`; final version passed after using `断崖式失稳` and `同向辅助观察`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Chapter 4 Section~`\ref{sec:exp-kv-sensitivity}` and related tables/figures.
- Skeptical reviewer: first pass failed on causal strength, K4V8 evidence level, and cross-model boundary; final version passed after adding the single-side-diagnosis reference and explicit Qwen/LLaMA boundary.

### Applied Revision

```tex
前文提供了理解这一现象的机制线索。第~\ref{sec:ch3-problem}~节说明 Key 扰动先进入 logits 排序，再经 softmax 改写注意力分布；第~\ref{sec:ch3-motivation-kv}~节与第~\ref{sec:exp-kv-sensitivity}~节的 Qwen 系列读数给出经验锚点。结合前述单侧诊断，Key 降到 4 bit 的配置更直接暴露风险；任务对照中，\texttt{K4V8} 在 Qwen 系列出现断崖式失稳，而 \texttt{K8V4} 未出现同等强度退化。\texttt{K4V4} 同时压低 K 与 V，只作为同向辅助观察列出。跨模型判读仍以第四章表图为准，其中 Qwen 系列的归零更明显，LLaMA-3.1-8B 在当前对照中失稳幅度较小，具体边界还受模型规模、训练数据与 GQA 配置共同影响。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 21b

- Report segment: 21
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 225--241
- Detector excerpt begins: `为处理运行时输入分布超出校准覆盖范围的情况...`
- Status: applied

### Diagnosis

- Main AIGC triggers: explanation-first template, parenthetical hyperparameter note, and several compressed mechanism/boundary statements.
- Rewrite goal: preserve the adaptive-protection equations while making the trigger condition, runtime behavior, and engineering tradeoff easier to read.
- Style constraints: avoid unnecessary parentheses and reduce engineering jargon that sounds translated.

### Preserved Information

- Runtime samples may fall outside the calibration coverage.
- The path still adds adaptive protection beyond static scale.
- The current write tensor remains `$x^{\mathrm{cur}}_{l,j}$`.
- The dynamic scale remains `$\operatorname{absmax}(x^{\mathrm{cur}}_{l,j})/q_{\max}$`.
- The margin `$m$` remains a fixed hyperparameter, with `$m=1$` in this thesis and retained for future extension.
- The final scale remains the maximum of `$m\cdot s_{l,j}^{\mathrm{static}}$` and `$s_{l,j}^{\mathrm{dyn}}$`.
- Static parameters still dominate within calibration coverage.
- Dynamic scale still handles writes whose current-token absmax exceeds the static coverage threshold.
- The mechanism still keeps the current token inside the quantization grid and avoids direct clipping to `$q_{\max}$`.
- The `$\max$` computation remains per write step, and K/V adaptive-protection switches remain independent.
- Extreme drift may still increase quantization error as the engineering cost of clipping safety.
- Historical-cache writeback semantics remain deferred to Section~`\ref{sec:ch3-deployment}`.

### Review Gate

- Technical reviewer: PASS; confirmed equations, trigger condition, switch independence, and engineering boundary are preserved.
- Chinese academic writing reviewer: first pass failed on `固定超参`, `工程扩展入口`, and `动态尺度接管当前写入`; final version passed after rewriting these phrases.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Section~`\ref{sec:ch3-deployment}`.
- Skeptical reviewer: PASS; no overstatement of dynamic-scale benefits or missing boundary found.

### Applied Revision

```tex
运行时样本可能落到校准覆盖范围之外，因此该路径在静态缩放参数之外加入自适应保护。设当前写入张量为 $x^{\mathrm{cur}}_{l,j}$，动态尺度定义为
\begin{equation}
s_{l,j}^{\mathrm{dyn}}
=
\frac{\operatorname{absmax}\!\big(x^{\mathrm{cur}}_{l,j}\big)}{q_{\max}},
\end{equation}
保护裕度 $m$ 是固定超参数，本文取 $m=1$，并将其保留为后续扩展参数。最终缩放参数取
\begin{equation}
s_{l,j}^{\mathrm{final}}
=
\max\!\left(
m \cdot s_{l,j}^{\mathrm{static}},
\;
s_{l,j}^{\mathrm{dyn}}
\right),
\end{equation}
当前 token 仍处在校准覆盖范围内时，静态参数继续主导。若当前 token 的 $\operatorname{absmax}$ 超过 $m \cdot s_{l,j}^{\mathrm{static}}\cdot q_{\max}$ 对应的覆盖，则改用动态尺度写入当前 token，使该 token 仍落在量化网格内，避免异常值被直接压到 $q_{\max}$。$\max$ 在每个写入步单独计算，K 与 V 的自适应保护开关也分别控制。极端漂移会抬高 $s_{l,j}^{\mathrm{final}}$，进而扩大一定量化误差；这是为裁剪安全付出的工程代价。缓存写入时是否回写历史缓存的系统语义，见第~\ref{sec:ch3-deployment}~节。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 21a

- Report segment: 21
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 223
- Detector excerpt begins: `$(p_c,g)$在 $\Theta_\mathrm{path}$ 候选网格...`
- Status: applied

### Diagnosis

- Main AIGC triggers: passive construction and compact `候选网格上由...筛选选出` phrasing.
- Rewrite goal: make the candidate-grid role explicit and keep the selection rule tied to Section~`\ref{subsec:ch3-two-stage}`.
- Style constraints: avoid awkward passive wording and keep the sentence as a formula handoff rather than a new method claim.

### Preserved Information

- `$(p_c,g)$` remains the candidate pair.
- The candidate grid remains `$\Theta_\mathrm{path}$`.
- The selection still uses KL tail statistics and clipping-rate constraints.
- The rule remains attributed to Section~`\ref{subsec:ch3-two-stage}`.
- The output remains the final selected combination.

### Review Gate

- Technical reviewer: PASS; confirmed no optimization semantics changed.
- Chinese academic writing reviewer: first pass failed on `负责从中选出最终组合`; final version passed after rewriting it as `依据...选出最终组合`.
- Cross-chapter consistency reviewer: PASS; confirmed the section reference remains accurate.
- Skeptical reviewer: PASS; no omitted information or claim drift found.

### Applied Revision

```tex
候选网格 $\Theta_\mathrm{path}$ 同时枚举 $(p_c,g)$，并依据第~\ref{subsec:ch3-two-stage}~节给出的 KL 尾部统计与裁剪率约束选出最终组合。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 20b

- Report segment: 20
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 205
- Detector excerpt begins: `在该路径中，Key与Value均采用对称、逐组...`
- Status: applied

### Diagnosis

- Main AIGC triggers: dense parenthetical `per-group` explanation and a long formula-introduction sentence.
- Rewrite goal: split the quantization format, grouping rule, and variable definition while leaving the following equation unchanged.
- Style constraints: avoid unnecessary parentheses and keep the formula lead-in precise.

### Preserved Information

- Key and Value still use the same static symmetric per-group quantization in this path.
- Groups are still formed along the channel dimension.
- Each group still contains `$g=128$` elements and shares one scale parameter.
- `$x_{l,j}$` still denotes the tensor to quantize for layer `$l$` and group `$j$`.
- `$p_c$` and `$g$` remain the inputs used to define the static scale parameter.
- The following equation remains the definition of the static scale.

### Review Gate

- Technical reviewer: PASS; confirmed the format, grouping axis, group size, shared scale, notation, and equation handoff are preserved.
- Chinese academic writing reviewer: PASS; no wording issue found.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the runtime path table and the INT8 static-scale definition.
- Skeptical reviewer: PASS; no omission or new claim found.

### Applied Revision

```tex
该路径对 Key 和 Value 使用相同的静态对称逐组量化。分组沿通道维度划分，每组包含 $g=128$ 个元素并共享一个缩放参数。设第 $l$ 层第 $j$ 个分组的待量化张量为 $x_{l,j}$；给定校准百分位参数 $p_c$ 和分组大小 $g$ 后，静态缩放参数定义为
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 20a

- Report segment: 20
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 203
- Detector excerpt begins: `INT8位宽提供255级离散网格...`
- Status: applied

### Diagnosis

- Main AIGC triggers: slogan-like `第一性验证实例`, parenthetical `per-group`, and a compressed semicolon chain.
- Rewrite goal: make the INT8 role concrete as a check of the offline-selection to online-execution loop while preserving its baseline role.
- Style constraints: avoid unnecessary parentheses and keep the claim as an auditable path role rather than a broad methodological label.

### Preserved Information

- `\texttt{INT8}` still has 255 effective integer levels.
- The quantization grid is still described as relatively fine.
- Calibration-layer scale parameters remain traceable by group.
- The path still checks whether behavior-guided calibration forms a stable offline-to-online loop.
- Chapter 4 still marks the path as `\texttt{INT8-Canonical}`.
- `\texttt{INT8}` remains the compression-ratio reference for later low-bit paths.

### Review Gate

- Technical reviewer: PASS; confirmed the grid, grouped scale traceability, INT8-Canonical naming, and low-bit baseline role are preserved.
- Chinese academic writing reviewer: first pass failed on `从离线选择闭合到在线执行` and `按逐组粒度追溯`; final version passed after rewriting these as `检查离线选择与在线执行是否形成闭环` and `按组追溯`.
- Cross-chapter consistency reviewer: PASS; confirmed the Chapter 4 naming and low-bit reference role.
- Skeptical reviewer: PASS; no overclaim or factual drift found.

### Applied Revision

```tex
\texttt{INT8} 的有效整数等级为 255 级，量化网格相对细，校准层写出的 scale 参数也能按组追溯。本文先在这一设置下检查离线选择与在线执行是否形成闭环，并在第四章将该路径记为 \texttt{INT8-Canonical}。\texttt{INT8} 还提供后续低比特路径的压缩率参照。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 19b

- Report segment: 19
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 192
- Detector excerpt begins: `产物字段分两类落地...`
- Status: applied

### Diagnosis

- Main AIGC triggers: dash-packed explanation, repeated `读取`, and a route-map sentence compressed into the same paragraph.
- Rewrite goal: separate artifact categories, temperature-diagnostic boundary, and next-section handoff into shorter authorial sentences.
- Style constraints: avoid dash explanations and keep the boundary positive without weakening the fact that temperature correction is appendix-only.

### Preserved Information

- Product fields remain divided into two categories by usage.
- Path-specific calibration fields remain directly read by the online cache-writing process.
- Per-layer sensitivity statistics remain input to the budget allocation module in Section~`\ref{sec:ch3-allocator}`.
- Per-head temperature correction remains preserved as an appendix diagnostic.
- The main flow remains limited to the two product categories.
- The next two sections still cover three cross-bit-width path instantiations and the sensitivity-statistics-based allocation mechanism.

### Review Gate

- Technical reviewer: PASS; confirmed artifact categories, online read semantics, allocation input, temperature boundary, and next-section handoff are preserved.
- Chinese academic writing reviewer: first pass failed on `消费产物`; final version passed after rewriting it as `主线流程仅使用前两类产物`.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Section~`\ref{sec:ch3-allocator}` and the appendix placement of temperature correction.
- Skeptical reviewer: PASS; no new claim or boundary drift found.

### Applied Revision

```tex
产物字段按用途分成两类。路径特定校准字段由在线缓存写入过程直接读取，逐层敏感度统计则供第~\ref{sec:ch3-allocator}~节的预算分配模块使用。逐头温度校正保留在附录诊断中，主线流程仅使用前两类产物。基于这一接口边界，后两节分别展开三条跨位宽路径的实例化设计，以及由敏感度统计支撑的预算分配机制。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 19a

- Report segment: 19
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 190
- Detector excerpt begins: `K-path以pK...`
- Status: applied

### Diagnosis

- Main AIGC triggers: English-style `K-path`/`V-path`, parenthetical packing around `per-channel` and `per-token`, mixed English terminology for attention KL, and dash-packed framework wording.
- Rewrite goal: keep the two-path calibration semantics while separating K-side and V-side proxy ownership more explicitly.
- Style constraints: avoid unnecessary parentheses and dash explanations, prefer natural Chinese path names, and avoid implying that the V path is selected by attention KL tail statistics.

### Preserved Information

- `\texttt{INT4-RoleAlign}` still uses the preceding five-step flow.
- `$p_K$` and `$p_V$` remain separately selected and are not collapsed into a single attention KL score.
- K path still uses `$p_K$`, the per-channel Key asymmetric percentile-clipping parameter, with details in Section~`\ref{sec:ch3-paths}`.
- K path still uses attention-distribution KL and tail statistics.
- V path still uses `$p_V$`, the per-token Value asymmetric percentile-clipping parameter.
- V path still uses the independent output perturbation proxy `$R_V(\theta)$`; its concrete form remains assigned to Section~`\ref{sec:ch3-paths}`.
- The two paths still share the feasible-set audit framework, including clipping-rate filtering, path-specific primary ranking statistics, and secondary keys for ties or fallback.
- Thresholds, primary ranking statistics, and secondary keys remain separately specified for the K/V paths.

### Review Gate

- Technical reviewer: first pass failed because the shared framework wording was too broad and did not explicitly preserve clipping-rate filtering, tail/robust primary ranking, and secondary-key fallback; final version passed after narrowing the shared part to a feasible-set audit framework.
- Chinese academic writing reviewer: first pass failed on English-style path names and `为主序`; final version passed after using `K 路径`/`V 路径` and rewriting the ranking sentence.
- Cross-chapter consistency reviewer: PASS; confirmed the paragraph remains aligned with Section~`\ref{sec:ch3-paths}` and Section~`\ref{sec:ch3-allocator}`.
- Skeptical reviewer: first pass failed on possible V-path/KL ambiguity; final version passed after assigning K and V proxies separately.

### Applied Revision

```tex
\texttt{INT4-RoleAlign} 仍使用上述五步流程，但 $p_K$ 与 $p_V$ 分别选择，不合并为单一注意力 KL 分数。K 路径的候选参数为 $p_K$，对应逐通道 Key 非对称量化的百分位裁剪参数，具体路径见第~\ref{sec:ch3-paths}~节；该路径使用注意力分布 KL 及其尾部统计完成选择。V 路径的候选参数为 $p_V$，对应逐 token Value 非对称量化的百分位裁剪参数；该路径使用独立输出扰动代理 $R_V(\theta)$ 及其稳健统计，具体形式见第~\ref{sec:ch3-paths}~节。两条路径共享可行域审计框架，包含裁剪率过滤、依据各自代理的尾部统计或稳健统计排序、用次级排序键处理并列与回退；对应阈值、主排序统计和次级排序键在 K/V 两条路径中分别给出。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 18

- Report segment: 18
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 173--186
- Detector excerpt begins: `其中 µ(θ) 沿用第 3.4.1 节的均值代理逐候选化...`
- Status: applied

### Diagnosis

- Main AIGC triggers: dense packed definitions, parenthetical `INT8/INT4` bounds, unclear `元素比例` wording, and English-style `argmin` phrase in the prose.
- Rewrite goal: preserve the robust-selection definitions while making the roles of mean proxy, P95 tail statistic, K/V clipping rates, hard filtering, and secondary key explicit.
- Style constraints: avoid unnecessary parentheses, avoid colon-style set notation where `\mid` is clearer, and use natural Chinese for the `argmin` explanation.

### Preserved Information

- `$\mu(\theta)$` remains the candidate-wise value of the mean KL proxy from Section~`\ref{subsec:ch3-kl-target}`.
- `$q_{0.95}(\theta)$` remains the 95th percentile of the same per-position KL distribution.
- `$c_K(\theta)$` and `$c_V(\theta)$` remain Key/Value clipping-rate statistics.
- The scale remains `$s_\theta(x)$`.
- An element still counts toward the clipping rate when `$|x/s_\theta(x)| > q_{\max}$`.
- `\texttt{INT8}` still uses `$q_{\max}=127$`; `\texttt{INT4}` still uses `$q_{\max}=7$`.
- The feasible set still filters by `$c_K(\theta)\le\tau_K` and `$c_V(\theta)\le\tau_V`.
- The paper still uses `$\tau_K=\tau_V=0.01$`.
- When the feasible set is nonempty, the main selection rule still minimizes `$q_{0.95}(\theta)$`.
- `$\mu$` remains outside the main minimization target and is only a secondary sorting key for ties or the fallback rule.

### Review Gate

- Technical reviewer: PASS; confirmed definitions, thresholds, and selection rule are unchanged.
- Chinese academic writing reviewer: first pass failed on vague `元素比例`, colon-style set notation, and `主选 argmin`; final version passed after clarifying K/V clipping rates, using `\mid`, and rewriting the prose.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the KL proxy, feasible set, and fallback rule.
- Skeptical reviewer: first pass required the complete feasible-set definition and explicit hard-filter logic; final version passed after the whole natural paragraph was reviewed with formulas included.

### Applied Revision

```tex
这里的 $\mu(\theta)$ 是第~\ref{subsec:ch3-kl-target}~节均值代理对每个候选的取值，$q_{0.95}(\theta)$ 是同一逐位置 KL 分布的 95\% 分位数。$c_K(\theta)$ 与 $c_V(\theta)$ 分别记录 Key 与 Value 张量的裁剪率。对元素 $x$ 以候选 $\theta$ 对应的分组尺度 $s_\theta(x)$ 缩放后，若 $|x/s_\theta(x)|$ 超过整数上界 $q_{\max}$，该元素计入对应裁剪率；\texttt{INT8} 取 $q_{\max}=127$，\texttt{INT4} 取 $q_{\max}=7$。可行域用裁剪率阈值 $\tau_K,\tau_V$ 硬过滤候选，定义为
\begin{equation}
\Theta_{\mathrm{feasible}}
=
\{\theta \in \Theta_{\mathrm{path}}\mid c_K(\theta)\le \tau_K,\; c_V(\theta)\le \tau_V\},
\end{equation}
本文取 $\tau_K = \tau_V = 0.01$。若 $\Theta_{\mathrm{feasible}}\neq\emptyset$，选择规则为
\begin{equation}
\theta^\star
=
\arg\min_{\theta \in \Theta_{\mathrm{feasible}}}
q_{0.95}(\theta).
\end{equation}
以尾部统计 $q_{0.95}$ 为主序；$\mu$ 不参与主选择规则的最小化目标，仅在并列或下文的回退规则中作为次级排序键。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 17b

- Report segment: 17
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 133
- Detector excerpt begins: `前向KL DKL(pref∥pθ)对参考高概率位置...`
- Status: applied

### Diagnosis

- Main AIGC triggers: textbook-like semicolon structure, compact contrast among forward KL, reverse KL, and JS, and a final boundary sentence that read as appended rather than integrated.
- Rewrite goal: preserve the forward-KL design reason, the reverse-KL/JS diagnostic roles, and the independent V-path output-perturbation proxy.
- Style constraints: avoid `在...下`, keep the forward-KL claim directional rather than universal, and make the Value-path boundary explicit.

### Preserved Information

- The chosen objective remains forward KL `$D_{\mathrm{KL}}(p_{\mathrm{ref}}\|p_\theta)$`.
- Forward KL still penalizes cases where quantization underestimates high-probability positions in the reference distribution.
- The design connection to long-context retrieval and not missing key tokens is preserved.
- Reverse KL still focuses more on high-probability regions under the quantized distribution.
- JS divergence remains the more symmetric diagnostic.
- Reverse KL and JS are still retained as supplementary diagnostics.
- The Value path still uses an independent output-perturbation proxy.
- Section~`\ref{sec:ch3-paths}` remains the reference for the Value-path detail.

### Review Gate

- Technical reviewer: PASS; confirmed forward/reverse KL, JS, and V-path proxy semantics are preserved.
- Chinese academic writing reviewer: PASS; confirmed the paragraph avoids colon-led or English-style phrasing.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Section~`\ref{sec:ch3-paths}` and the KL objective.
- Skeptical reviewer: PASS; confirmed the wording does not overstate forward KL or erase supplementary diagnostics.

### Applied Revision

```tex
本文采用前向 KL $D_{\mathrm{KL}}(p_{\mathrm{ref}}\|p_\theta)$，因为当量化路径低估参考分布中的高概率位置时，该方向会给出更大的惩罚。这一取向对应长上下文检索中“不漏关键 token”的需求。反向 KL 更关注量化分布自身的高概率区域，JS 散度则更对称，二者保留为补充诊断。Value 路径不沿用这一分布代理，而使用独立的输出扰动代理，见第~\ref{sec:ch3-paths}~节。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 16

- Report segment: 16
- Source paragraph: `thesis/figures/fig_ch3_framework_shared_profile.tex`, figure caption
- Detector excerpt begins: `图3-3 行为引导量化框架总览...`
- Status: applied

### Diagnosis

- Main AIGC triggers: process-summary rhythm, repeated `随后/同一链路同步`, and a caption that did not explicitly state the online no-search boundary.
- Rewrite goal: turn the caption into a responsibility-oriented description while preserving all figure relationships and avoiding graph/text mismatch.
- Style constraints: avoid `在...下` where `依据...` is more natural, avoid engineering-heavy `只读方式`, and do not introduce a low-bit-recovery node that is not drawn in the figure.

### Preserved Information

- The figure remains the overview of the behavior-guided quantization framework.
- Offline calibration still reads calibration samples, FP16 reference behavior, and candidate quantization paths.
- Offline calibration still computes the behavioral proxy and performs robust selection.
- The frozen calibration artifact remains `\(\theta^\star\)`.
- The layer-wise behavioral sensitivity profile remains `\(\mathcal S\)` and is produced by the calibration link rather than serving as its input.
- The allocation module still reads `\(\mathcal S\)`.
- The allocation module still generates `\(b^\star\)` according to average bit-width budget `\(\bar b\)`.
- Online inference still reads `\(\theta^\star\)` and `\(b^\star\)`.
- The online phase now explicitly states that it does not re-search or update offline artifacts.
- Cache write and decode remain the online execution actions.

### Review Gate

- Technical reviewer: first and final passes both approved; confirmed all original figure-caption relationships are preserved.
- Chinese academic writing reviewer: first pass failed on `以只读方式` and `在平均位宽预算下`; final version passed after rewriting them as `读取该画像` and `依据平均位宽预算`.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the figure nodes and Section 3.3 text.
- Skeptical reviewer: first pass asked for no-search boundary and warned about possible `\mathcal S`/calibration-role ambiguity; final version passed after adding the online no-search statement and clarifying that `\mathcal S` is produced by the calibration link.

### Applied Revision

```tex
\caption{行为引导量化框架总览。离线校准链路读取校准样本、FP16 参考行为和候选量化路径，计算行为代理并完成稳健选择，输出冻结校准产物 \(\theta^\star\)。校准链路同时沉淀逐层行为敏感度画像 \(\mathcal S\)，预算分配模块读取该画像，依据平均位宽预算 \(\bar b\) 生成位宽向量 \(b^\star\)。在线推理阶段只读取 \(\theta^\star\) 与 \(b^\star\)，不重新搜索或更新离线产物，并据此执行缓存写入与解码。}
```

### Verification

- PASS: `git diff --check -- thesis/figures/fig_ch3_framework_shared_profile.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 17a

- Report segment: 17
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 131
- Detector excerpt begins: `式 (3-8) 把误差分解为分布侧...`
- Processing scope: first natural paragraph only. The detector also spans the forward/reverse KL paragraph, which will be handled in the next commit.
- Status: applied

### Diagnosis

- Main AIGC triggers: dense formula prose, semicolon-packed explanation, `偏移再经...进入聚合侧` ambiguity, and `在分布侧误差路径上` against the user's writing preference.
- Rewrite goal: preserve the MSE boundary, Key-side attention path, error-decomposition terms, variable definitions, and KL/distribution-path correspondence while improving readability.
- Style constraints: avoid `xxxx 上`, avoid implying KL covers the Value aggregation path, and keep the KL claim scoped to the distribution-side error path.

### Preserved Information

- MSE remains positioned as tensor-reconstruction comparison over elementwise K/V differences.
- Key-side error still passes through `$qK^\top$`, softmax ranking, and probability-mass allocation before affecting output.
- A low-MSE candidate can still move probability mass away from key tokens.
- Equation~`\eqref{eq:ch3-error-decomp}` still provides the two output-error paths.
- The distribution term remains `$\sum_i(\hat a_i-a_i)v_i$`.
- The aggregation term remains `$\sum_i \hat a_i(\hat v_i-v_i)$`.
- `$a_i\equiv p_{\mathrm{ref},i}^{(l,h,t)}` and `$\hat a_i\equiv p_{\theta,i}^{(l,h,t)}` are preserved.
- `$v_i$` and `$\hat v_i$` remain reference and quantized Value.
- KL still compares the distribution shift between `$a$` and `$\hat a$`.
- The final claim remains that KL is closer than elementwise reconstruction error to output-level attention behavior along the distribution-side error path.

### Review Gate

- Technical reviewer: PASS; confirmed formulas, definitions, and KL/MSE boundary are preserved.
- Chinese academic writing reviewer: first pass failed on `注意力质量移走`, `在量化后权重下`, and `在分布侧误差路径上`; final version passed after replacing them with natural Chinese expressions.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with the Chapter 3 error decomposition and V-path output perturbation boundary.
- Skeptical reviewer: PASS; confirmed the paragraph does not overstate KL as covering the Value aggregation path.

### Applied Revision

```tex
MSE 仍停留在张量重建空间，只比较 $K$ 或 $V$ 的逐元素差异。Key 侧误差进入输出前，还要经过 $qK^\top$、softmax 排序和概率质量分配；因此，即便某个候选的 MSE 较小，关键 token 的注意力概率质量仍可能发生转移。式~\eqref{eq:ch3-error-decomp} 给出对应的两条输出误差路径。分布项为 $\sum_i(\hat a_i-a_i)v_i$，聚合项为 $\sum_i \hat a_i(\hat v_i-v_i)$。这里 $a_i\equiv p_{\mathrm{ref},i}^{(l,h,t)}$、$\hat a_i\equiv p_{\theta,i}^{(l,h,t)}$，$v_i$ 与 $\hat v_i$ 分别表示参考 Value 和量化 Value。KL 直接比较 $a$ 与 $\hat a$ 的分布偏移，与分布项对应；聚合项则保留 Value 扰动经由量化后权重 $\hat a_i$ 进入输出的作用。这个分工使 KL 沿分布侧误差路径，比逐元素重建误差更贴近输出层面的注意力行为。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 15b

- Report segment: 15
- Source paragraph: `thesis/chapters/ch3_method.tex`, line 83
- Detector excerpt begins: `这一组织把整条链路切分为可独立验证的两段...`
- Status: applied

### Diagnosis

- Main AIGC triggers: abstract `这一组织` opening, compressed semicolon-packed offline/online contrast, and the dispreferred phrase `推理路径上`.
- Rewrite goal: preserve the independently verifiable offline/online split while making the execution boundary read as normal academic prose.
- Style constraints: avoid `xxxx 上`, avoid overpacked semicolon structure, and keep `\theta^\star` / `b^\star` as offline deliverables rather than online decision variables.

### Preserved Information

- The full chain is still split into independently verifiable offline and online parts.
- The offline phase still extracts reference behavior, searches path parameters, writes frozen calibration artifacts, and generates `$\mathcal{S}$`.
- The online inference phase still only reads frozen artifacts.
- The online phase still computes the scale or budget needed for current cache writes according to fixed rules.
- The framework boundary remains that inference does not repeat offline search.
- `$\theta^\star$` and `$b^\star$` remain offline deliverables, not online decision variables.
- Figure~`\ref{fig:ch3-framework-shared-profile}` remains the reference for offline/online cooperation and shared-profile transfer across calibration, low-bit recovery, and budget allocation.

### Review Gate

- Technical reviewer: PASS; confirmed frozen-artifact semantics and offline deliverable status are preserved.
- Chinese academic writing reviewer: PASS; confirmed the revision removes the dispreferred `推理路径上` phrasing and reads naturally.
- Cross-chapter consistency reviewer: PASS; confirmed alignment with Figure~`\ref{fig:ch3-framework-shared-profile}`, Section~`\ref{sec:ch3-allocator}`, and runtime-path boundaries.
- Skeptical reviewer: PASS; no loss of independent verification, online/ offline split, or figure linkage.

### Applied Revision

```tex
上述组织使校准链路和推理链路可以分开核验。离线阶段提取参考行为，完成路径参数搜索，写出冻结校准产物，并同步生成 $\mathcal{S}$。在线推理阶段只读取这些冻结产物，按照固定规则为当前缓存写入计算尺度或预算。推理阶段不重复离线搜索，这是框架的执行边界；$\theta^\star$ 与 $b^\star$ 也相应作为离线交付物保存，而不是在线决策变量。图~\ref{fig:ch3-framework-shared-profile} 给出离线—在线协作关系，以及共享画像在校准、低比特恢复和预算分配三层之间的传递方式。
```

### Verification

- PASS: `git diff --check -- thesis/chapters/ch3_method.tex docs/aigc_revision_tracker.md iteration.md`.
- PASS: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=/tmp/aigc_paragraph_build main.tex` from `thesis/`.
- Build note: PDF generation completed; log check found no undefined references or citation warnings. Existing Chapter 3 overfull hboxes at lines 369 and 644--646 remain unrelated to this segment.

## Segment 15a

- Report segment: 15
- Source paragraph: `thesis/chapters/ch3_method.tex`, lines 77--81
- Detector excerpt begins: `线优化也不重复参数搜索。最简形式下 b⋆...`
- Processing scope: first natural paragraph only. The detector also spans the following offline/online paragraph, which will be handled in the next commit.
- Status: applied

### Diagnosis

- Main AIGC triggers: compressed definition prose after the displayed equation, parenthetical `本文取...`, English-style `bit` phrasing, and `K/V 角色条件化` wording.
- Rewrite goal: preserve the allocation mapping, budget inequality, deterministic offline/online boundary, and K/V role extension while making the prose less mechanical.
- Style constraints: use `位宽` rather than `bit` in Chinese prose where possible, avoid unnecessary parentheses, and replace `角色条件化` with a more natural Chinese phrase.

### Preserved Information

- The allocation layer still decides which layers retain higher bit-width budgets.
- The average KV bit-width budget remains `$\bar b$`.
- The mapping remains `$b^\star = \mathcal{A}(\mathcal{S};\bar b)` with the same average-budget constraint.
- The allocator remains a deterministic rule.
- `$\mathcal{S}$` remains read-only input and is still converted into an integer bit-width vector `$b^\star$`.
- The online path still does not re-optimize or repeat calibration parameter search.
- The basic form remains `$b^\star\in\{b_{\min},\dots,b_{\max}\}^L`.
- The paper still uses `$b\in\{4,8,16\}$`.
- The K/V role extension remains `$L\times 2$` and stays tied to the Key/Value roles identified in Section~`\ref{sec:ch3-motivation-kv}`.
- `$\mathcal{S}$` still extends into role-wise components.
- Section~`\ref{sec:ch3-allocator}` remains the location for the concrete allocation rules.

### Review Gate

- Technical reviewer: PASS; confirmed the displayed equation, domain, budget constraint, deterministic mapping, and K/V role extension are preserved.
- Chinese academic writing reviewer: first pass failed on `处理各层保留多少位宽` and `K/V 角色条件化`; final version passed after rewriting these phrases.
- Cross-chapter consistency reviewer: PASS; confirmed consistency with Section~`\ref{sec:ch3-allocator}` and Figure~`\ref{fig:ch3-framework-shared-profile}`.
- Skeptical reviewer: PASS; no change to online/offline semantics or allocation-domain meaning.

### Applied Revision

```tex
分配层负责决定各层保留的位宽预算。设平均 KV 位宽预算为 $\bar b$，分配映射
\begin{equation}
b^\star = \mathcal{A}(\mathcal{S};\bar b),\quad \tfrac{1}{L}\sum_{l=1}^{L} b^\star_l \le \bar b,
\end{equation}
是一个确定性规则。它只读取共享画像 $\mathcal{S}$，把逐层敏感度转换为整数位宽向量 $b^\star$，在线推理时不重新优化，也不重复校准参数搜索。基础设置把 $b^\star$ 写成 $L$ 维逐层预算，$b^\star\in\{b_{\min},\dots,b_{\max}\}^L$，本文使用 $b\in\{4,8,16\}$。当预算表达进一步区分 K/V 角色时，$b^\star$ 变为 $\{b_{\min},\dots,b_{\max}\}^{L\times 2}$ 中的向量，对应第~\ref{sec:ch3-motivation-kv}~节识别的 Key/Value 双角色；此时 $\mathcal{S}$ 也拆分为角色分量。第~\ref{sec:ch3-allocator}~节给出具体规则。
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
