# Round 2 Phase 2 — ch2 + ch3 Paper Review

- **Date:** 2026-04-08
- **Round:** 2 (thesis-polish-loop, Phase 2 — chapter deep review)
- **Reviewer agent:** paper-critic (Sonnet)
- **Target chapters:** `thesis/chapters/ch2_related_work.tex` (523 lines) + `thesis/chapters/ch3_method.tex` (1026 lines)
- **Phase 1 input:** `reports/round_2/literature_digest.md` (486 lines)
- **Round 1 anchor:** commits `2f65927..b01eee4` (T1–T9), T1/T3/T9 repositioned `inv_tau` from "optional enhancement" to "structural diagnostic byproduct / Finding 4"
- **Methodology:** full-file Read of both chapters + Phase-1 tagged grep (FP8, KIVI-gap-audit, [SHOULD_ADD] papers, GQA, symbol consistency, novelty defense, cross-chapter refs)

---

## §1 Executive Summary

### 1.1 Headline count

| Severity   | ch2 | ch3 | Total |
|------------|-----|-----|-------|
| CRITICAL   |  0  |  1  |   1   |
| MAJOR      |  5  |  3  |   8   |
| MINOR      |  3  |  4  |   7   |
| NIT        |  2  |  2  |   4   |
| **Total**  | 10  | 10  | **20**|

### 1.2 Top 5 must-fix (priority order)

1. **[CRITICAL] `ch3:65-66` + `ch3:96` residual "可选/候选增强" wording** — contradicts the T1/T3/T9 repositioning and T9 cleanup commit message. The T9 commit (`f216143`) missed two places; the overview paragraph still brands `\tau^{-1}` as "可选的...候选增强机制之一" and the calibration pipeline figure caption still labels it "可选，格式依赖". A reviewer reading §3.1 and §3.2 before reaching §3.4 will infer that `inv_tau` is an afterthought, undermining C5 novelty. **Action: rewrite both to "诊断框架的结构性产出" phrasing consistent with §3.4.**
2. **[MAJOR] ch2 has zero explicit novelty defense sentence** for `\tau^{-1}` × GQA. The digest §5.3 recommends adding "To the best of our knowledge, no published work reports per-head softmax temperature correction for KV cache quantization compensation, nor analyses its dependence on GQA $H_{kv}$." ch2 §2.5.x (lines 404–410) softened the old "首个" claim to "此前未被系统报道" but the latter is in ch3, not ch2. ch2 has no "首个/首次/to the best of our knowledge" phrase anywhere. Add the defensive anchor to ch2 §2.5.x tail.
3. **[MAJOR] AhaKV / AsymKV / HeadKV / Softmax-Not-Enough absent from ch2** — Phase 1 Q3 identifies AhaKV (arXiv 06/2025) as the single most important defensive citation because reviewers searching "softmax temperature tuning for KV cache" will land on it first; grep confirms **none** of the 9 [SHOULD_ADD_TO_CH2] papers are cited in ch2. This is the largest gap that Phase 2 can close.
4. **[MAJOR] KIVI gap audit coverage is 1/6 in ch2** — ch2's KIVI paragraphs (L234–239, L513) acknowledge the per-channel K + per-token V axis but omit the 5 other known deltas (residual buffer, async pipeline, token staging, layer strategy, Pre-RoPE Key). The thesis-internal `docs/kivi_gap_audit.md` also requires a §5 disclaimer sentence ("本文的 KIVI-style baseline... 应理解为对 KIVI 核心算法思想的验证, 而非完整系统性能的严格复现"); this sentence is missing from ch2.
5. **[MAJOR] ch3 has no "intuitive argument" disclaimer for σ_eff ∝ σ/√N_rep** in §3.4 (L395–411). The formal argument lives in ch4:1349–1353 with explicit "直觉论证 (intuitive argument)" wording, but ch3 §3.4's paragraph "GQA 尺度依赖性的诊断发现" references "温度校正与 GQA 噪声稀释之间的交互关系" without flagging that the mechanism is argued, not proved. A reviewer reading ch3 linearly will form an expectation of a theorem, reach the end of §3.4, and then be surprised to only see formal content in the *experiments* chapter. **Action: add one sentence in §3.4 explicitly framing the attribution as "一个直觉论证 (详见第~\ref{sec:exp-gqa-dilution}~节)" and naming §3.4 as "诊断发现" not "机理分析".**

### 1.3 C5 novelty defense gap overview

| Layer | Current state | Gap |
|---|---|---|
| ch2 §2.5.x softmax-quant sub-section (L394–410) | Lists QeRL, KVTuner, Bondarenko. Says "均未将因果链延伸至 attention 内部 softmax 的平坦化补偿与 GQA 架构的交互。" | Missing: AhaKV one-sentence contrast; Softmax-Not-Enough as foundational anchor; no "to the best of our knowledge" phrasing. |
| ch2 §2.5 main body (L225–374) | KIVI/KVQuant/ZipCache/GEAR/QServe/... | Missing AsymKV (K>V attribution competitor), HeadKV (per-head precedent), Outlier-Tokens-Tracing (OTT online detection), AQUA-KV (K-as-predictor), ChunkKV (chunk-level eviction), BitDecoding (tensor-core kernel), PolarQuant (scale-less). |
| ch3 §3.4 "温度校正的格式-尺度双依赖性" (L366–411) | Narrates the finding, references §2 for literature support. | References §2.5.x but §2.5.x does not yet have a cleanly differentiated AhaKV/AsymKV/etc. set of citations to "support-reference". Circular reference between ch2 and ch3 depends on Phase-2 ch2 updates landing first. |
| ch3 §3.6.3 "与 KIVI 的设计差异" table (L639–671) | `温度校正 = 格式/尺度依赖` with footnote showing 1.5B vs 7B/8B numbers | Does not reference that inv_tau was not adopted by KIVI — which is the correct null case but should be explicit in the table caption. |
| ch5 limitations | Digest §5.3 recommends adding: "Our scale-dependent finding for inv_tau is observational; we do not claim a closed-form theoretical bound..." | Not yet verified in ch5 (Phase 2 scope only covers ch2+ch3); flagged for Phase 4. |

### 1.4 AI-trace hotspot density

3 paragraphs flagged (see §4). All three are Round-1 newly written or heavily rewritten segments.

---

## §2 ch2 Review (6 dimensions)

### §2.1 FP8 对标深度

**Observation.** ch2 §2.5 contains a 12-line FP8 paragraph (L376–387) added/unified in Round-1 T7. Grep confirms 4 distinct FP8 mentions (L376/377/380/382/386) and one explicit vLLM name (L381 "vLLM 等推理框架已默认提供 FP8 KV Cache 选项"). However no specific vLLM version is cited, no TensorRT-LLM mention, no Marlin/FlashInfer FP8 kernel reference, and no concrete INT4-FP8 hybrid (e.g., QServe W4A8KV4 is cited in the main table at L342 but not linked back into the FP8 discussion). The paragraph is intellectually defensible but rhetorically thin: it answers "why not FP8" but does not cite *any* FP8 KV paper. The justification (1) "INT4 = 4-bit, FP8 = 8-bit" is correct, but (2) "行为对齐校准原则对 INT 和 FP 格式均适用" is a claim that would be stronger with a forward reference ("the same KL objective could be plugged into an FP8 calibration pipeline without changing §3.3").

Round-1 T7 removed the H20 hardware-specific justification ("实验平台 H20 的 FP8 tensor core 支持受限") — this was correct since H20 *does* support FP8. The replacement ("INT 路径为后续 <8 bit 低比特场景保留了可扩展空间") is defensible but weaker than a concrete citation could be.

**Issues.**

- **[MAJOR]** `ch2:376-387` — FP8 paragraph cites zero FP8 KV papers. Reviewers may dismiss the "why not FP8" defense as hand-wavy. Specifically missing:
  - vLLM FP8 KV cache documentation link (v0.4+, [docs](https://docs.vllm.ai/en/latest/quantization/fp8.html)) or the vLLM FP8 paper/issue.
  - TensorRT-LLM FP8 KV Cache reference.
  - At minimum one academic FP8 KV work (e.g., FP8-LM [micikevicius2022fp8] or Hopper FP8 Attention papers) to establish that FP8 KV is a research line, not just a system feature.
  **Suggestion:** add 1 citation in Phase 4 (deferred: Phase 2 scope is "diagnose", Phase 4 can add 1–2 references). Priority: MAJOR because defense of exclusion scope is part of C4 (capability boundary).

- **[MINOR]** `ch2:383` — "FP8 仅提供 8 bit 而无 4 bit 对应格式" is technically imprecise: FP4 (E2M1/E3M0) *does* exist in NVIDIA Blackwell (NVFP4). BitDecoding (Phase 1 Q4.b) explicitly reports 8.6× speedup with NVFP4. The statement is defensible for current H100/H200 but should be qualified: "当前主流部署硬件 (H100/H200) 上..." to leave room for Blackwell.

- **[NIT]** `ch2:381` — "vLLM 等推理框架" uses "等" (etc.) without naming TensorRT-LLM or SGLang explicitly. "vLLM、TensorRT-LLM 等" would be a stronger single-word fix.

### §2.2 KIVI gap audit 引用覆盖度

**Observation.** Cross-reference `docs/kivi_gap_audit.md` §2 "未实现的 KIVI 原论文特性" lists 5 items: (2.1) residual buffer, (2.2) decode K scale adaptive update, (2.3) async quantization pipeline, (2.4) token-graded storage, (2.5) per-layer strategy differentiation. Plus §3 notes 4 project-specific additions (int4_kivi_aligned, V-path BA calibration, ENG-041 truncation warning, float32 scale enforcement). And the audit §5 recommends this specific disclaimer sentence: "本文的 KIVI-style baseline 采用 KIVI 的核心量化轴策略...但不包含原论文中的残差缓冲区、异步量化流水线和 token 分级存储等工程优化，因此本文的 KIVI-style 实验结果应理解为对 KIVI 核心算法思想的验证，而非完整系统性能的严格复现。"

Grep against ch2 for "残差缓冲 | residual buffer | 异步 | token 分级 | 逐层策略 | pre-RoPE" returned **zero matches**. ch2's KIVI coverage is purely at the axis-design level (L234 per-channel K + per-token V) and the comparison-table row (L338). The disclaimer sentence is not in ch2 and not in ch4 either (spot check). Given that the INT4-RoleAlign comparison (ch3 §3.6.3) rests on the "same axis, different calibration" framing, the KIVI baseline scope must be honestly disclosed to pre-empt reviewer accusations of strawman comparison.

**Issues.**

- **[MAJOR]** `ch2:234-239` — KIVI paragraph covers only the axis design. 5/6 gap-audit deltas missing. Most important: **residual buffer** (which plausibly affects KIVI's reported accuracy) and **Pre-RoPE Key** (which KVQuant [hooper2024kvquant] highlights but our calibration artifact v3_quick explicitly did NOT have pre-RoPE — see ch3 §3.2 paragraph "校准产物版本说明" L136–143). The thesis has an internal asymmetry: ch3 discloses that our v3_quick Q vector was pre-RoPE-broken, but ch2 does not establish Pre-RoPE Key as a prior work baseline to contextualize that disclosure.
  - **Suggestion:** Phase-2 level fix: add 1 sentence to ch2:239 ("本文的 KIVI-style baseline 实现了 KIVI 的核心量化轴与 percentile 裁剪机制，不包含原论文可选的残差缓冲区、异步量化流水线与 token 分级存储；详见附录~\ref{sec:app-kivi-gap}~的差异审计。") + a pointer to a new appendix subsection copying `docs/kivi_gap_audit.md`.

- **[MAJOR]** `ch2:241-244` — KVQuant paragraph says "通过聚类方法学习最优的量化码本" but does not mention **Pre-RoPE Key quantization** which is KVQuant's most-referenced contribution and directly maps to our calibration-artifact disclosure. Given that Phase 1 explicitly flags this ("Per-channel Key + Pre-RoPE Key + Non-uniform codebook"), ch2 should add 1 sentence: "KVQuant 进一步提出 pre-RoPE Key 量化以规避 RoPE 旋转对量化网格的扭曲，此观察与本文的校准时序设计（第~\ref{sec:ch3-calibration}~节）直接相关。"

- **[MINOR]** The "KV Cache 量化相关工作比较" table at L328–359 is missing a column for "residual buffer (是/否)" which would make the KIVI-vs-ours comparison rigor machine-visible. Optional Phase-4 table extension.

### §2.3 缺失对标 (Phase 1 [SHOULD_ADD] papers)

**Observation.** Grep for "AhaKV | AsymKV | HeadKV | Softmax-Not-Enough | Outlier | OTT | AQUA-KV | ChunkKV | BitDecoding | PolarQuant | velickovic | velickovi | gu2025 | tao2024asymkv | fu2025headkv | su2025 | shutova | liu2025chunk | du2025bit | han2025polar" in ch2 returns **zero matches**. None of the 9 [SHOULD_ADD] papers from Phase 1 are currently cited. This is the single largest actionable gap of Round 2.

Priority mapping (from digest §3):

| Priority | Paper | Why it matters for ch2 |
|---|---|---|
| **P0** | AhaKV (gu2025ahakv) | Closest "softmax-scale-tuning" precedent. Must add to §2.5.x for C5 defense. |
| **P0** | AsymKV (tao2024asymkv) | Independent K>V observation. Must add to §2.5 for C2 attribution. |
| **P1** | HeadKV (fu2025headkv) | Per-head granularity exists but as binary keep/drop, not continuous correction. Must add for §2.5.x C5 defense. |
| **P1** | Softmax-Not-Enough (velickovic2024softmax) | Foundational "softmax temperature as a knob" anchor. Must add for §2.5.x. |
| **P1** | Outlier Tokens Tracing (su2025outliertoken) | Dynamic online K/V outlier detection. Should add near IntactKV. |
| **P2** | AQUA-KV (shutova2025aquakv) | K-as-predictor, consistent with our K>V finding. Should add near GEAR. |
| **P2** | ChunkKV (liu2025chunkkv) | Chunk-level eviction, strong long-context results. Should add in eviction sub-section. |
| **P2** | BitDecoding (du2025bitdecoding) | Tensor-core kernel layout. Should add in §2.6.3 Triton sub-section. |
| **P3** | PolarQuant (han2025polarquant) | Scale-less via polar transform. Should add near QJL. |

**Issues.**

- **[MAJOR]** `ch2:398-411` (§2.5.x) — **missing AhaKV + Softmax-Not-Enough**. These are the two single-sentence adds that most directly defend C5. Without them, the contrast "above works did not extend the causal chain to attention-internal softmax flattening compensation × GQA" is self-referential (defends against papers *we already cited*). Adding AhaKV's "global entropy-driven softmax scale tuning for eviction" as a contrast point pre-empts the strongest reviewer search hit.

- **[MAJOR]** `ch2:241-244` — **missing AsymKV**. AsymKV (arXiv 10/2024, Alibaba) independently observes K>V sensitivity and attributes to layer depth. This independent confirmation actually *strengthens* C2 if cited correctly, but if omitted, a reviewer will cite it and accuse the thesis of independent-rediscovery-without-credit. Per digest §4.3: "The next most important is AsymKV, but this is for C2 attribution, not C5."

- **[MAJOR]** `ch2:292-297` (eviction sub-section) — **missing HeadKV + ChunkKV**. HeadKV gives per-head binary keep/drop and is the closest per-head granularity precedent. ChunkKV gives chunk-level eviction. Each is 1 sentence.

- **[MINOR]** `ch2:276-281` — Outlier Tokens Tracing (ACL 2025) should be added next to IntactKV (L276). The natural contrast is "IntactKV preserves static pivot tokens; OTT detects outlier tokens dynamically during decoding."

- **[MINOR]** `ch2:462-467` (§2.6.3 Triton sub-section) — BitDecoding (ICLR 2025) reports tensor-core-friendly layouts beat CUDA-core layouts for INT4/INT2 KV decode. This is directly relevant to our system contribution discussion and should be 1 sentence.

- **[NIT]** `ch2:278-281` — QJL already cited; adding PolarQuant (its scale-less successor) as 1 sentence is a natural cluster.

### §2.4 GQA 结构效应铺垫

**Observation.** Grep for GQA/grouped query/H_kv in ch2 returns 11 hits, concentrated in the background §2.1 (L50–76) and the research-gap §2.7 (L517). The ch2 §2.5 quantization-methods body has exactly **0 mentions of GQA** until line 406 (the T1 repositioning sentence in §2.5.x "与 GQA 架构的交互"). The §2.1 background discusses $H_q$/$H_{KV}$ correctly and gives the 1.5B (12Q/2KV) and 7B (28Q/4KV) numbers at L74–75, establishing the notation. The §2.7 research gap item 4 (L512–517) mentions "不同模型架构（特别是不同 GQA 头数）间的差异模式" — this is the structural foreshadowing hook for C5.

However, between §2.1 (background) and §2.5.x (novelty defense), **the 300-line body of §2.5 (L228–388) never relates any existing method to $H_{kv}$ sensitivity**. For C5 to land in ch3, the reader must already know from ch2 that "GQA $H_{kv}$ is a variable dimension across published methods, yet no one reports its interaction with quantization noise". The current ch2 has this only implicitly via the table column "GQA" at L337 (just a checkmark). That checkmark says "method supports GQA" not "method analyzes GQA × quantization noise".

**Issues.**

- **[MAJOR]** Missing explicit "GQA as a variable dimension in quantization literature" paragraph. The logical place is after L324 (right before the comparison table) or as a 3-line transition in §2.5.x.
  **Suggested location:** insert before L389 (§2.5.x section header): "在 KV Cache 量化文献中，GQA 头数 $H_{kv}$ 的选择被统一视为架构超参数，现有方法主要关注 $H_{kv}$ 对显存节省的线性贡献（公式~\eqref{eq:kv_mem}），而未系统分析 $H_{kv}$ 对量化噪声敏感度的调制作用。本文第~\ref{subsec:exp-rolealign-invtau}~节的 $H_{kv} \in \{2, 4, 8\}$ 三模型消融首次报告了这一交互。"

- **[MINOR]** `ch2:111` uses "$h_{KV} = 4$" but ch2:75 uses "2 个 KV 头"（中文）without formula. Inconsistency within ch2 itself about when to render $h_{KV}$ as formula vs text. Not critical, but §2.2 can use the formula consistently for uniformity.

### §2.5 非对称 vs 对称历史脉络

**Observation.** ch2 §2.3 "模型量化技术基础" presents symmetric (§2.3.1 L133–163) then asymmetric (§2.3.2 L164–184) as a textbook pair, without a temporal/evolutionary narrative. §2.5 "KV Cache 量化相关工作" then lists KIVI (asymmetric), KVQuant (non-uniform with per-channel Key), ZipCache (saliency mixed precision), etc. without a time axis.

The narrative transition "why asymmetric" is not explicitly marked. A reader sees a list, not an evolution. The KIVI L234 paragraph starts with "其核心观察是" but does not pose the preceding question "对称量化对 KV Cache 有什么局限？" The answer is there (per-channel heterogeneity) but the question is never asked.

**Issues.**

- **[MINOR]** `ch2:228-232` — §2.5's opening paragraph should pose the symmetric→asymmetric evolution question more explicitly. Current text jumps straight to "随着大语言模型的上下文窗口不断扩大" (memory pressure framing). A single transition sentence "早期 KV Cache 量化方法直接套用对称逐张量/逐组量化, 但 Key 通道间的数值异质性使此路径在低比特下迅速饱和, 促使后续工作探索非对称量化轴" would give the reader the asymmetric-as-evolution frame that §3.6 relies on.

- **[MINOR]** `ch2:362-374` — the "正交维度" framing (quantization format vs calibration objective) is good but reversed relative to ch3 §3.6 "正交性" paragraph (L563–577). ch3 establishes the format×objective dichotomy as its own contribution, while ch2 anticipates it as background. These two paragraphs should cross-reference each other explicitly (add "(详见第~\ref{para:ch3-orthogonality}~段)" to ch2:374).

### §2.6 novelty 防御段 (inv_tau × GQA × KV quantization)

**Observation.** ch2 §2.5.x is the intended novelty defense location. Current text (L394–410):
- L394–402: lists 3 prior works (QeRL, KVTuner, Softmax Bias Correction) — good.
- L404: "上述工作均未针对 KV Cache 量化场景系统报道温度校正的规模依赖性。" — close to a novelty claim but not explicit.
- L406: "均未将因果链延伸至 attention 内部 softmax 的平坦化补偿与 GQA 架构的交互。" — this is the T1 repositioning sentence.
- L407–410: points forward to §3.4 + §4.x.

Grep for "novelty | 首个 | 首次 | to the best of our knowledge | 据我们所知 | 本文是首个" in ch2 returns **zero matches**. The Phase 1 digest §5.3 explicitly recommends adding: "To the best of our knowledge, no published work reports per-head softmax temperature correction for KV cache quantization compensation, nor analyses its dependence on GQA $H_{kv}$." This sentence is currently in no chapter.

Also: the three near-miss papers (AhaKV, AsymKV, KVTuner) need the 1-sentence differentiation each. KVTuner already has the clean differentiation (L398 Lemma 1 quantification + L405 "止步于误差放大的量化分析"). AhaKV and AsymKV are both missing entirely.

**Issues.**

- **[MAJOR]** `ch2:404-410` — novelty defense paragraph is too implicit. No "据文献调研" / "首次报告" phrase. Add: "据我们所知，目前没有已发表的工作同时报告 (i) 针对 KV Cache 量化的逐头 softmax 温度校正机制，以及 (ii) 该机制的效果对 GQA 头数 $H_{kv}$ 呈现的尺度依赖性反转。"

- **[MAJOR]** `ch2:398-403` — missing AhaKV differentiation. Per digest §3 P0 suggestion: insert 1 sentence after L402 ("Concurrently, AhaKV [Gu et al. 2025] introduces a global entropy-driven softmax scale tuning for eviction importance scoring. Our $\tau^{-1}$ correction differs in three respects: it is per-head (not global), calibrated against quantization noise (not attention entropy), and applied within the attention computation of retained tokens (not to eviction importance scoring).") This is THE single most defensive addition of Round 2.

- **[MINOR]** The §2.5.x paragraph is 17 lines (L394–410). After the P0/P1 additions it will grow to ~25–30 lines, still manageable. Suggest splitting into two sub-paragraphs: "前向分析" (QeRL/KVTuner/Bondarenko, L394–402) and "温度校正的前期工作" (AhaKV + Softmax-Not-Enough + novelty claim, new L403–415).

---

## §3 ch3 Review (6 dimensions)

### §3.1 inv_tau derivation 严谨性 (§3.4, L366–411)

**Observation.** §3.4 was heavily rewritten in Round-1 T3 (commit 2f65927). Current structure:
- L366: new title "温度校正的格式-尺度双依赖性" (good — structural framing).
- L369–372: motivation ("在执行诊断流程时, 我们发现... 这是诊断框架的一个二阶产出") — good.
- L373–380: intuitive explanation ("量化误差使注意力 logits 受近似均匀的噪声扰动, softmax 输出趋于平坦化") + equation (4.12).
- L381–383: implementation ("通过 Q 预缩放等价实现") + appendix pointer.
- L385–393: figure caption (heatmap).
- L395–411: "GQA 尺度依赖性的诊断发现" paragraph — numbers for 1.5B/7B/8B + novelty phrase.

Equation labels in §3.4: `eq:ch3-corrected-attn` (L379) only. No Lemma/Proposition/Theorem labels. Grep confirms `\label{lem:|\label{thm:|\label{prop:` returns zero in ch3.

Critically: **the GQA noise dilution σ_eff ∝ σ/√N_rep formula is NOT in ch3**. Grep for "sigma_eff | N_rep | 稀释" in ch3 returns only the GQA-support-mechanism paragraph in §3.7 (L795–809) which defines $N_{\text{rep}}$ without connecting it to quantization noise. The formal argument (with "直觉论证 (intuitive argument)" disclaimer per reviewer A's request) lives in **ch4:1349–1354**, not ch3. This creates a narrative tension: ch3 narrates a finding, ch4 proves (intuitively) why, but ch3's claim does not point forward to ch4's mechanistic attribution.

**Issues.**

- **[MAJOR]** `ch3:395-411` — the "GQA 尺度依赖性" paragraph reports the 3-model numbers and claims novelty, but never states *why* it's scale-dependent. One must jump to ch4:1349 to see "GQA 噪声稀释的直觉论证" and "$\sigma_{\text{eff}} \propto \sigma / \sqrt{N_{\text{rep}}}$". In a method chapter this is backwards — the method chapter should give the mechanism hypothesis, and the experiments chapter should test it. **Suggestion:** move a 3-line abbreviated version of the noise-dilution argument from ch4:1349–1354 into ch3 §3.4 (after L408), with the formal argument deferred to §4.x.x. Use phrasing that explicitly labels it as "直觉论证" (intuitive argument, not formal proof). This is what reviewer A flagged in Round 0.

- **[MAJOR]** `ch3:369-411` — entire §3.4 has no "intuitive argument / heuristic / future formal proof" disclaimer anywhere. Grep confirms "intuitive | 直观论证 | heuristic | 启发式 | future work | 后续工作 | 正式证明 | formal proof" in ch3 only returns hits in the unrelated §3.3 "Forward KL 方向消融... 列入后续工作" (L242). ch3 §3.4 narrates the GQA dependency as a fact without marking the causal mechanism as conjectural. **Suggestion:** add one sentence at L408: "本节给出观察性发现; 其机制归因于 GQA 噪声稀释 (详细直觉论证见第~\ref{subsec:exp-rolealign-invtau}~节, 完整推导见附录~\ref{sec:app-invtau-detail}); 我们不提出闭式理论上界, 仅以三模型消融作为实证支撑。"

- **[MINOR]** `ch3:373-380` — the "logits 受近似均匀的噪声扰动" statement is hand-wavy (no reference). It should either cite Bondarenko (ch2:401) or label the noise model as an assumption ("假设量化误差 $\delta$ 在 logits 上大致同分布").

- **[MINOR]** `ch3:379` eq `eq:ch3-corrected-attn` is the only equation in §3.4. For a 45-line section with a theoretical claim, 1 equation is thin — the Q pre-scaling identity $\bQ' = \bQ \cdot \tau^{-1}$ at L382 should also be labeled.

### §3.2 BA percentile 搜索空间 justification (§3.6.2, L622–638)

**Observation.** The T7 follow-up (commit b01eee4) added a bridging sentence: "搜索目标仍为 KL 散度 (公式 eq:ch3-kl), 但搜索空间从对称格式的 $(p_c, g)$ 切换为非对称格式的 $(p_K, p_V)$（候选值见附录表~\ref{tab:app-search-space}）". Grep confirms this sentence exists (L628–629). The actual candidate values are deferred to an appendix table (`tab:app-search-space`). I verified the appendix has matching content via the grep against ch3.

The bridge is functional but the justification for why BA-guided percentile instead of other calibration approaches (MSE / KL Grid / Lloyd-Max) is absent. §3.6.2 (L622–638) describes *how* to do BA-guided percentile but not *why* this specific parameterization.

**Issues.**

- **[MINOR]** `ch3:622-638` — no justification for why (p_K, p_V) is the right parameterization. A one-sentence motivation would strengthen: "percentile 参数化相比直接 absmax/min 的优势在于对尾部异常值的鲁棒性, 且与 KIVI~\cite{liu2024kivi} 的 percentile 裁剪机制保持接口一致, 便于在同一校准框架内交叉消融。" This gives the reviewer the "why this parameterization, not some other" answer.

- **[MINOR]** `ch3:629` — "候选值见附录表~\ref{tab:app-search-space}" but ch3 body should disclose at least the range of values (e.g., "在 $\{99, 99.5, 99.9, 99.95, 99.99, 100\}$ 候选集上") inline. Deferring all 6 candidate values to an appendix is excessive; the body should give the reader the grid density without requiring a page flip.

### §3.3 RoleAlign vs KIVI 差异 (§3.6.3, L639–671)

**Observation.** §3.6.3 uses a 4-row comparison table (L643–662) identical in structure to `docs/rolealign_design_note.md` §1 "四项明确差异". The table rows are: 量化格式 / 校准范式 / 参数确定 / 温度校正. The "温度校正" row footnote was updated in Round-1 T3 to reflect the format×scale dual dependency.

Comparing to the design note `docs/rolealign_design_note.md`:
- design note differentiates on **4 dimensions**: 校准范式 / 设计动机 / 框架归属 / 参数求解机制
- thesis table uses **4 dimensions**: 量化格式 / 校准范式 / 参数确定 / 温度校正

The thesis table has different axes than the design note — "设计动机" (motivation: observation vs diagnostic-driven) and "框架归属" (framework ownership) are omitted. The thesis does have a "设计动机" discussion at L578–588 but not in the table. Design-note differentiation 4 (parameter solving mechanism) is collapsed into the thesis table's "参数确定" row.

Quantitative contrast: the thesis table row "温度校正" now reads "格式/尺度依赖" with a footnote giving 1.5B -1.6%, 7B/8B +3.4~6.0%. This is a quantitative comparison, good. But the other 3 rows (量化格式 / 校准范式 / 参数确定) are qualitative. **There is no numerical comparison of KIVI vs RoleAlign quality** in the table. The body L664–668 gives qualitative "更稳定的检索能力保持 (PPL 退化因模型规模而异, 详见第~\ref{subsec:exp-rolealign-results}~节)" but defers numbers.

**Issues.**

- **[MINOR]** `ch3:643-662` — design note has 4 differentiation dimensions; thesis table uses a different set of 4. "设计动机" and "框架归属" from the design note are dropped; "量化格式" is added. This is defensible (the table focuses on mechanistic differences, not meta-narrative), but the body should explicitly say "本表聚焦于机制差异, 设计动机与框架归属讨论见 [above body paragraphs]" to prevent the reader from confusing the two taxonomies.

- **[MINOR]** `ch3:659-661` table footnote — the PPL numbers (1.5B -1.6%, 7B/8B +3.4~6.0%) are given in the footnote but the KIVI baseline numbers for the same 3 models are not. A reviewer will ask: "how do these RoleAlign numbers compare to KIVI's numbers?" The table should give a side-by-side single column "KIVI PPL δ" vs "RoleAlign PPL δ" at least for the 1.5B case.

### §3.4 GQA noise ∝ 1/√H_kv 标注一致

**Observation.** Grep for the $\sigma_{\text{eff}} \propto \sigma / \sqrt{N_{\text{rep}}}$ formula across the thesis:
- `abstract_en.tex:55` — stated with formula.
- `abstract_zh.tex:32` — stated with formula.
- `ch1_introduction.tex:180` — stated with formula.
- `ch3_method.tex` — **NOT PRESENT**.
- `ch4_experiments.tex:822, 1352-1354` — formula + "直觉论证 (intuitive argument)" disclaimer (L1349).
- `ch5_conclusion.tex:74-76` — stated with formula.

This is a **serious cross-chapter inconsistency**: the formula is stated in the abstracts, intro, experiments, and conclusion, but the **method chapter itself does not show it**. A reviewer reading ch3 linearly will encounter the claim "该发现揭示了温度校正与 GQA 噪声稀释之间的交互关系" (ch3:408) without being shown the mechanism — they must either back-reference ch1 or skip ahead to ch4:1349.

The "intuitive argument" disclaimer is only in ch4:1349. All other references (abstracts, ch1, ch5) state the formula as fact without hedging. If a reviewer cites the formula from ch1 or ch5, they'll expect a proof; they won't find one until ch4 where it's marked intuitive.

**Issues.**

- **[MAJOR]** Cross-chapter inconsistency in how the σ_eff formula is framed:
  - **abstracts + ch1 + ch5**: stated as mechanism without hedging.
  - **ch4**: stated with "直觉论证 (intuitive argument)" disclaimer.
  - **ch3**: not stated at all.

  The correct fix (per reviewer A's Round-0 recommendation): (1) present the formula in ch3 §3.4 as a conjecture labeled "intuitive argument", (2) verify empirically in ch4 with the same hedging, (3) keep ch1/ch5 as concise restatements but add "direct intuitive argument" clause, and (4) audit the abstracts to ensure they do not over-claim. Phase-2 flag: ch3 missing; Phase-4 action: add 3-line derivation block to §3.4 + audit abstracts.

- **[MINOR]** `ch4:1349` — "直觉论证 (intuitive argument)" good hedge but only appears once. Other parts of ch4 (L819–826, L987, L995, L1115, L1267, L1341) discuss GQA dilution without the same hedge. A sentence-level consistency pass in Phase 4 should add "直觉论证" once, propagate the label into other instances as "同一直觉论证".

### §3.5 符号一致性 (cross-chapter)

**Observation.** Grep for $H_q$/$H_{kv}$ vs $h_Q$/$h_{KV}$ across chapters:
- **ch2 L63, 69, 70, 102, 105, 111**: uses **lowercase** `$h_Q$, $h_K$, $h_V$, $h_{KV}$, $h_{KV} = 4$`.
- **ch3 L315, 350, 691, 697, 700, 799, 800, 803, 806, 807, 925, 932, 939, 1004**: uses **uppercase** `$H_q$`, `$H_{kv}$`.
- **ch4**: 43 hits, uses **uppercase** `$H_q$`, `$H_{kv}$` per grep.
- **ch5 L74**: uses `$N_{\text{rep}} = H_q / H_{kv}$` — **uppercase**.
- **abstracts**: use `$\sqrt{N_{\text{rep}}}$` but do not show $H_q$/$H_{kv}$ directly.

**This is a cross-chapter symbol shift.** ch2 consistently uses lowercase `$h_Q$, $h_{KV}$`; every other chapter uses uppercase `$H_q$, $H_{kv}$`. The capitalization convention switches at the ch2→ch3 boundary. A careful reviewer will notice and flag this as typographic sloppiness.

Also spot-check: "$N_{\text{rep}}$" is consistent across ch3/ch4/ch5/abstracts (always subscripted "rep" in roman); ch1 L180 also uses $\sqrt{N_{\text{rep}}}$. Good.

**Issues.**

- **[MAJOR]** Symbol convention inconsistency between ch2 and ch3/4/5/abstracts:
  - **ch2**: `$h_Q$, $h_K$, $h_V$, $h_{KV}$` (lowercase)
  - **ch3+**: `$H_q$, $H_{kv}$` (uppercase)

  **Suggestion:** fix ch2:63, 69, 70, 102, 105, 111 to use uppercase to match ch3–ch5. Note the case of the subscript also shifts: ch2 uses `KV` (uppercase) while ch3+ uses `kv` (lowercase), so the fix is $h_Q \to H_q$ *and* $h_{KV} \to H_{kv}$ (both capitalization layers). This is a trivial 6-character-each Phase-4 edit but must be done together to avoid half-inconsistency.

- **[NIT]** `ch3:315` — "第 $h$ 个 Query 头对应的 KV 头索引为 $\lfloor h / (H_q / H_{kv}) \rfloor$" uses plain $h$ for the loop index while L350 uses $h$ for the query-head index in the algorithm. L803 then uses $h_q$ for the same concept. Within ch3 itself there's a minor drift: $h$, $h_q$, (and at L691 the implicit loop variable). Not critical but an editor could unify.

### §3.6 ch3 ↔ ch4 引用闭环

**Observation.** ch3 contains 9 `\ref{subsec:exp-*|sec:exp-*}` pointers to ch4:
- L40: `sec:exp-kv-sensitivity` — K/V sensitivity ablation
- L142: (calibration provenance, implicit)
- L391: `subsec:exp-ablation-temperature` — inv_tau INT8 ablation
- L392: `subsec:exp-rolealign-invtau` — inv_tau cross-model
- L401: `subsec:exp-ablation-temperature` (again)
- L407: `subsec:exp-rolealign-invtau` (again)
- L559: `sec:exp-kv-sensitivity` (again)
- L581: `sec:exp-int4` — INT4 results
- L659: `subsec:exp-rolealign-invtau` (again)
- L668: `subsec:exp-rolealign-results` — RoleAlign full results
- L977: `tab:kv-modes` → ch4 kv modes table (via cross-section ref).

9 refs total in ch3 → ch4, distributed across §3.1 (overview), §3.4 (inv_tau), §3.6 (RoleAlign), §3.8 (complexity). Density: ~9/1026 ≈ 1 per 114 lines, or ~1 per section. The ratio is adequate but **clustered** in §3.4 and §3.6 — the "diagnostic sections". §3.5 (self-adaptive protection) has zero forward references to ch4. §3.7 (Triton kernels) has zero forward references.

**Issues.**

- **[MINOR]** `ch3:503-551` (§3.5 self-adaptive protection) — zero forward references to ch4. The protection-margin discussion should cite a ch4 ablation (if one exists) or at least ch4 Needle results that motivated the mechanism. If no such ablation exists, that's a method-experiments disconnect.

- **[MINOR]** `ch3:672-811` (§3.7 Triton kernel section) — zero forward references to ch4. The INT4 split-channel design (§3.7.3, L758–793) claims "max abs diff < 1e-2" and "10/10 Needle PASS" but these should be backed by a ch4 table row, not a standalone claim.

- **[NIT]** `ch3:977` — the "实验中观测到约 44% 的节省 (第四章表~\ref{tab:kv-modes})" forward reference is clean. Good template to replicate in §3.5 and §3.7.

---

## §4 AI Trace Hotspot Paragraphs (Phase 4 line-by-line targets)

**Methodology:** flagged based on being Round-1 newly written or heavily rewritten, plus stylistic markers (run-on declarative sentences, abstract nouns, lack of concrete hooks, formulaic "基于此... 因此..." transitions).

### §4.1 ch2 §2.5 FP8 paragraph (L376-387) — HIGH risk

**Line count:** 12 lines.
**Round-1 provenance:** T7 rewrite (commit a81a8bc "fix(thesis): data sync + FP8 unification").
**Suspect markers:**
- L376 "随着 NVIDIA H100/H200 等新一代硬件对 FP8 (E4M3/E5M2) 格式的原生支持" — boilerplate "随着... 的支持" opener, tech-catalog tone.
- L377 "成为一条低成本的精度-效率折中方案" — "成为一条 ... 方案" is an abstract-noun scaffold common in LLM-generated Chinese.
- L379-380 "对异常值的容忍度优于 INT8 对称量化, 且硬件加速的矩阵乘法无需额外的反量化步骤" — parallel construction "优于... 且..." is LLM-template-y.
- L382-385 "本文聚焦于 INT8/INT4 整数量化而非 FP8 的原因在于: (1)... (2)..." — numbered-justification construction is authentic human writing but can also be LLM output.
- L386-387 "FP8 KV Cache 与本文 INT8/INT4 方法的系统性对比列入后续工作" — standard thesis-polish closing, OK.

**Phase-4 action:** re-read paragraph; replace at least 2 of the boilerplate openers with concrete hooks (e.g., "vLLM v0.4 起默认提供..." with version number). Goal: every sentence should have at least one concrete noun that is paper-internal or citation-backed.

### §4.2 ch3 §3.4 inv_tau repositioning opening (L369-383) — HIGH risk

**Line count:** 15 lines.
**Round-1 provenance:** T3 rewrite (commit 2f65927 "refactor(thesis): reposition inv_tau as diagnostic framework byproduct"). This is the most aggressive rewrite of Round-1.
**Suspect markers:**
- L369-371 "在执行诊断流程时, 我们发现逐头温度校正... 的有效性与量化格式和 GQA 头数同时强相关, 这是诊断框架的一个二阶产出。" — "二阶产出" is a somewhat academic-jargon neologism; "这是... 的一个二阶产出" has the structure of an LLM-generated paraphrase.
- L372 "该机制的原始动机是补偿量化导致的注意力分布平坦化。" — passive construction "该机制的原始动机是" is LLM-y.
- L373-374 "其核心思想是: 量化误差使注意力 logits 受近似均匀的噪声扰动, softmax 输出趋于平坦化 (熵增大), 对长距离聚焦任务尤为有害。" — 3 clauses with commas, "其核心思想是" = classic LLM bridge phrase.
- L375-377 "逐头温度校正通过引入因子 $\tau^{-1}_{l,h}$ 补偿该效应, 校正后的注意力计算为:" — the passive "通过引入... 补偿... 为:" is template-y.

**Phase-4 action:** re-read. Replace at least "其核心思想是" and "该机制的原始动机是" with active voice ("这一想法源于..." / "动机来自..."). Verify "二阶产出" is the author's chosen term, not an LLM artifact — if unclear, replace with "诊断框架的一个结构性发现" (matches §3.1 L21).

### §4.3 ch3 §3.6.2 BA percentile bridge (L622-638) — MEDIUM risk

**Line count:** 17 lines.
**Round-1 provenance:** T7 follow-up (commit b01eee4 "docs(thesis): T7 follow-up — BA percentile clarification").
**Suspect markers:**
- L624-625 "INT4-RoleAlign 的主要设计区别在于参数确定范式: 不同于 KIVI-style 完全依赖运行时统计量 (absmax/min) 的无校准方案, INT4-RoleAlign 通过行为对齐框架的离线搜索确定最优的..." — very long sentence (3 lines) with nested "不同于..." clause, LLM-typical structure.
- L628-629 "搜索目标仍为 KL 散度 (公式 eq:ch3-kl), 但搜索空间从对称格式的 $(p_c, g)$ 切换为非对称格式的 $(p_K, p_V)$" — "但搜索空间从... 切换为..." is clean but mechanical.
- L636-637 "其中 $\bm{p}_{\text{asym}}$ 为使用 per-channel K Scale 和 per-token V Scale 量化后的注意力分布。" — standard "其中...为..." definition pattern, OK.

**Phase-4 action:** medium priority. The paragraph is structurally sound, just needs a sentence-length pass to break up L624-627's three-line run-on.

### §4.4 (bonus) ch3 §3.1 overview paragraph (L6-23) — MEDIUM risk

Not originally on the hotspot candidate list but flagged during reading.

**Line count:** 17 lines.
**Suspect markers:**
- L6-8 "行为对齐量化框架以注意力权重分布的 KL 散度 (attention-KL) 为统一原则, 承担双重使命: 作为校准目标搜索使注意力行为偏移最小化的量化参数, 作为诊断透镜揭示不同量化配置下的失效模式与结构性根因。" — "承担双重使命: ... 作为..., 作为..." is the exact rhetorical structure LLMs use to introduce a dual-purpose framework.
- L9 "本章围绕从原则到设计的层级结构展开:" — "围绕... 展开" is a textbook template, but feels slightly manufactured.
- L21-22 "逐头温度校正 ($\tau^{-1}$) 作为诊断框架的结构性产出呈现 (第~\ref{sec:ch3-invtau}~节)" — **this line conflicts with L65-66** which still says "可选的... 候选增强机制之一". The overview paragraph was updated in Round 1; L65-66 was not.

**Phase-4 action:** fix the L65-66 inconsistency (see §3.1 CRITICAL issue) and re-read the L6-23 paragraph for "承担双重使命" style beat.

---

## §5 Phase 3 Reviewer Focus Pointers

For the 6 expert reviewers planned in Phase 3, here is the focus guidance per reviewer type:

### §5.1 Reviewer A — Methodology + Derivation Rigor

**Primary read:** ch3 §3.3 (KL calibration, L177-260), §3.4 (inv_tau diagnostic, L366-411), §3.6.2 (BA percentile, L622-638).

**Focus questions:**
1. Is the inv_tau formula $\tau^{-1}$ given a formal derivation or an intuitive argument? (Answer: intuitive, but only marked as such in ch4:1349, not in ch3.)
2. Is σ_eff ∝ σ/√N_rep proven, stated as conjecture, or derived from an assumed noise model? (Currently in ch4 with intuitive-argument disclaimer; absent from ch3.)
3. Is the BA-guided percentile search space justified? (Partial: T7 added a bridge but no motivation for why percentile parameterization.)

**Pointer list:**
- Key CRITICAL/MAJOR: §3.1 issue #1 (residual "可选") + §3.4 issue (missing intuitive-argument disclaimer).
- Expected reviewer concern: "The 'discovery' of GQA-scale dependency is narrated but not attributed to a testable model. Move the σ_eff argument into the method chapter."

### §5.2 Reviewer B — Literature Comprehensiveness

**Primary read:** ch2 §2.5 (L225-388), §2.5.x (L389-411), §2.7 (L495-523).

**Focus questions:**
1. Is the C5 (inv_tau × GQA) novelty defense exhaustive?
2. Are the 9 Phase-1 [SHOULD_ADD] papers justified for omission or added?
3. Is the KIVI gap audit reflected in ch2?

**Pointer list:**
- Key MAJOR: §2.3 (missing 9 papers) + §2.6 (missing "首次 / to the best of our knowledge" phrase) + §2.2 (KIVI gap audit).
- Expected reviewer concern: "AhaKV (arXiv 06/2025) seems directly relevant to inv_tau; why is it not cited?"

### §5.3 Reviewer C — Experiments Traceability (forward to Phase 4+ scope)

**Primary read:** ch3 §3.4, §3.6.3 (inv_tau + RoleAlign numbers).

**Focus questions:**
1. Do the PPL numbers in ch3 §3.6.3 table footnote (1.5B -1.6%, 7B/8B +3.4~6.0%) match ch4?
2. Is the "13.7% → 12.0% (−1.6%)" math consistent?
3. Are the cross-references ch3 → ch4 complete?

**Pointer list:**
- §3.3 (table footnote missing KIVI baseline comparison).
- §3.6 (§3.5 adaptive protection + §3.7 Triton kernel both missing forward references to ch4).
- Expected reviewer concern: "Where is the 1.5B INT4-RoleAlign baseline (no inv_tau) PPL of 13.7% reported in ch4? Is it int4_ours or int4_ours_asym?"

### §5.4 Reviewer D — Notation + Typography

**Primary read:** ch2 §2.1 (L50-76), ch3 §3.7 (L795-811).

**Focus questions:**
1. Are $h_Q$/$h_{KV}$ vs $H_q$/$H_{kv}$ consistent across chapters?
2. Are equation labels complete?

**Pointer list:**
- §3.5 MAJOR: ch2 uses lowercase $h_Q$/$h_{KV}$; ch3+ uses uppercase $H_q$/$H_{kv}$. 6+ ch2 instances to fix.
- §3.1 MINOR: ch3:382 Q pre-scaling identity is not labeled as an equation.
- Expected reviewer concern: "Symbol inconsistency; §2.1 should match §3.4."

### §5.5 Reviewer E — Narrative + AI-Trace

**Primary read:** ch2:376-387 (FP8), ch3:369-383 (inv_tau), ch3:622-638 (BA bridge), ch3:6-23 (overview).

**Focus questions:**
1. Do any paragraphs read as AI-generated?
2. Is the "可选增强 / 候选增强 / 结构性产出" terminology consistent?

**Pointer list:**
- §4.1-§4.4 hotspots.
- §3.1 CRITICAL issue (ch3:65-66 + ch3:96 residue).
- Expected reviewer concern: "Overview says 'structural byproduct', body says 'optional enhancement'. Which is it?"

### §5.6 Reviewer F — Systems + Baselines

**Primary read:** ch2:462-467 (Triton), ch3 §3.7 (Triton kernels, L672-811), §3.8 (Quantization modes, L863-912).

**Focus questions:**
1. Is the KIVI baseline fair or strawman?
2. Is BitDecoding cited?
3. Is the INT4 non-symmetric fused kernel novelty claimed?

**Pointer list:**
- §2.2 MAJOR: KIVI gap-audit disclaimer missing.
- §2.3 MINOR: BitDecoding (Phase 1 Q4.b) not cited.
- §3.6 MINOR: §3.7.3 split-channel design claims not forward-referenced to ch4.
- Expected reviewer concern: "If your KIVI baseline is missing the residual buffer, how can you claim superiority?"

---

## §6 Phase 4 Action Items (priority order, file:line)

### §6.1 CRITICAL (must-do before any other edits)

1. **`thesis/chapters/ch3_method.tex:65-66`** — Replace "以及可选的逐头温度校正因子 $\tau^{-1}$ (inverse temperature), 作为框架的候选增强机制之一。" with "以及逐头温度校正因子 $\tau^{-1}$ (inverse temperature), 作为诊断框架的结构性产出。" to align with the T3/T9 repositioning.

2. **`thesis/chapters/ch3_method.tex:96`** — Figure caption sub-node "$\tau^{-1}$ 搜索" (scriptsize "可选, 格式依赖") should become "格式/尺度依赖" to match §3.4 title.

### §6.2 MAJOR (ch2 literature + novelty)

3. **`thesis/chapters/ch2_related_work.tex:244` (after KVQuant block)** — Add AsymKV 2-sentence paragraph: "AsymKV~\cite{tao2024asymkv} 独立观察到 Key 缓存比 Value 更敏感, 将此归因于层深度并据此分配逐层不对称精度。本文从 RoPE 诱导的通道振荡角度追溯同一现象, 并通过 BA-guided percentile 在张量级实现非对称校准。" + add bib entry.

4. **`thesis/chapters/ch2_related_work.tex:277` (near IntactKV)** — Add OTT 1-sentence cite: "Outlier Tokens Tracing~\cite{su2025outliertoken} 在解码过程中动态识别敏感 token, 与 IntactKV 的静态 pivot 方案互补。" + bib.

5. **`thesis/chapters/ch2_related_work.tex:292` (near SnapKV)** — Add ChunkKV 1-sentence: "ChunkKV~\cite{liu2025chunkkv} 将驱逐粒度从 token 泛化到语义 chunk 级别, 在相同压缩率下精度提升 8.7\%。" + bib.

6. **`thesis/chapters/ch2_related_work.tex:296` (near DuoAttention)** — Add HeadKV 2-sentence: "HeadKV~\cite{fu2025headkv} 提出头级 KV 选择, 按检索/推理重要性保留 1.5\% 的 KV 缓存同时保持 97\% 的 LongBench 精度。该方案在保留头内不修改注意力权重, 与本文的逐头 $\tau^{-1}$ 连续校正正交。" + bib.

7. **`thesis/chapters/ch2_related_work.tex:279` (near QJL)** — Add PolarQuant 1-sentence: "其后继 PolarQuant~\cite{han2025polarquant} 通过极坐标变换完全消除 scale 存储开销。" + bib.

8. **`thesis/chapters/ch2_related_work.tex:388` (end of §2.5, before §2.5.x)** — Add GQA-as-quantization-variable paragraph (3 lines): "在 KV Cache 量化文献中, GQA 头数 $H_{kv}$ 被统一视为架构超参数。现有方法主要关注 $H_{kv}$ 对显存节省的线性贡献 (公式~\eqref{eq:kv_mem}), 而未系统分析 $H_{kv}$ 对量化噪声敏感度的调制作用。本文第~\ref{subsec:exp-rolealign-invtau}~节的 $H_{kv} \in \{2, 4, 8\}$ 三模型消融首次报告了这一交互。"

9. **`thesis/chapters/ch2_related_work.tex:402` (after Bondarenko sentence)** — Add AhaKV contrast sentence: "同期, AhaKV~\cite{gu2025ahakv} 基于注意力熵期望提出了全局 softmax scale 调节以改进 eviction 重要性评分。本文的 $\tau^{-1}$ 校正在三个维度上与之区别: (i) 逐头 (而非全局), (ii) 基于量化噪声校准 (而非注意力熵), (iii) 作用于保留 token 的注意力计算 (而非 eviction 评分)。" + bib.

10. **`thesis/chapters/ch2_related_work.tex:404` (novelty claim)** — Add Softmax-Not-Enough foundational anchor: "DeepMind 的 Softmax-Not-Enough 分析~\cite{velickovic2024softmax} 从理论上证明 softmax 的锐度随序列长度增长而衰减, 提出在 LM head 引入自适应温度; 本文的 $\tau^{-1}$ 可视为该温度旋钮在 attention 内部的、面向量化噪声的实例化。" + bib.

11. **`thesis/chapters/ch2_related_work.tex:410` (end of §2.5.x)** — Add explicit novelty claim: "据我们所知, 目前没有已发表的工作同时报告 (i) 针对 KV Cache 量化的逐头 softmax 温度校正机制, 以及 (ii) 该机制有效性对 GQA 头数 $H_{kv}$ 呈现的尺度依赖性反转。"

12. **`thesis/chapters/ch2_related_work.tex:239` (end of KIVI paragraph)** — Add KIVI gap-audit disclaimer: "本文的 KIVI-style baseline 实现 KIVI 的核心量化轴与 percentile 裁剪机制, 但不包含原论文可选的残差缓冲区、异步量化流水线与 token 分级存储等工程优化; 差异审计详见附录~\ref{sec:app-kivi-gap}。" + new appendix section copying `docs/kivi_gap_audit.md` §2.

13. **`thesis/chapters/ch2_related_work.tex:244` (KVQuant extended)** — Add Pre-RoPE Key sentence: "KVQuant 进一步提出 pre-RoPE Key 量化以规避 RoPE 旋转对量化网格的扭曲, 此观察与本文的校准时序设计 (第~\ref{sec:ch3-calibration}~节) 直接相关; 本文 1.5B 主模型校准产物 v3\_quick 的 pre-RoPE 处理缺口详见附录~\ref{sec:app-calib-provenance}。"

### §6.3 MAJOR (ch3 rigor)

14. **`thesis/chapters/ch3_method.tex:408` (after GQA dependency claim)** — Add 3-line noise-dilution argument (mirror of ch4:1349-1354 but abbreviated): "该依赖可由 GQA 噪声稀释机制给出一个直觉论证: 由于每个 KV 头被 $N_{\text{rep}} = H_q / H_{kv}$ 个 Query 头共享, 假设各 Query 头的量化噪声近似独立, 经注意力输出聚合后有效噪声规模被稀释为 $\sigma_{\text{eff}} \propto \sigma / \sqrt{N_{\text{rep}}}$; $H_{kv}$ 越大, 稀释越强, 预先校正的温度因子越容易与天然稀释相互抵消。本文不提出闭式理论上界, 完整的直觉论证与实证支撑见第~\ref{subsec:exp-rolealign-invtau}~节, 完整推导见附录~\ref{sec:app-invtau-detail}。"

15. **`thesis/chapters/ch3_method.tex:395` (§3.4 paragraph header)** — Prepend or append the "本节给出观察性发现" disclaimer: after "诊断发现" title add "(观察性发现; 机制归因为直觉论证, 非闭式理论)".

### §6.4 MAJOR (symbol consistency)

16. **`thesis/chapters/ch2_related_work.tex:63, 69, 70, 102, 105, 111`** — Replace all `h_Q → H_q` and `h_{KV} → H_{kv}` (6 locations). Also replace `h_K → H_k`, `h_V → H_v` if present.

### §6.5 MINOR (Phase 4 polish)

17. **`thesis/chapters/ch2_related_work.tex:383`** — Qualify FP8 4-bit statement: "FP8 仅提供 8 bit 格式 (当前 H100/H200 主流部署上无 4 bit 对应; Blackwell NVFP4 尚未在本文实验平台普及)".

18. **`thesis/chapters/ch2_related_work.tex:467`** — Add BitDecoding sentence: "同期, BitDecoding~\cite{du2025bitdecoding} 证明 tensor-core 友好的内存布局对 Hopper/Blackwell GPU 上的 4-bit 解码速度至关重要, 相比 CUDA-core 方案加速 7.5×。" + bib.

19. **`thesis/chapters/ch2_related_work.tex:228-232`** — Add symmetric→asymmetric transition sentence: "早期 KV Cache 量化方法直接套用对称逐张量/逐组量化, 但 Key 通道间的数值异质性使此路径在低比特下迅速饱和, 促使后续工作探索非对称量化轴。"

20. **`thesis/chapters/ch2_related_work.tex:374`** — Add cross-reference: "该正交框架与第~\ref{para:ch3-orthogonality}~段中 INT4-RoleAlign 的设计论证相呼应。"

21. **`thesis/chapters/ch3_method.tex:622-638`** — Add parameterization justification: "percentile 参数化相比直接 absmax/min 的优势在于对尾部异常值的鲁棒性, 且与 KIVI~\cite{liu2024kivi} 的 percentile 裁剪机制保持接口一致。"

22. **`thesis/chapters/ch3_method.tex:629`** — Inline disclose the candidate set: "在候选集 $\mathcal{P}_K = \mathcal{P}_V = \{99.0, 99.5, 99.9, 99.95, 99.99, 100.0\}$ 上网格搜索 (完整值见附录表~\ref{tab:app-search-space})". (Verify exact values against `configs/exp_matrix_rolealign.yaml` before committing.)

23. **`thesis/chapters/ch3_method.tex:659-661`** — Extend Table~\ref{tab:ch3-rolealign-vs-kivi} footnote with KIVI baseline numbers on the same 3 models: "相对对照, KIVI-style 在 1.5B 上 PPL 退化 X%, 7B 上 Y%, 8B 上 Z%, 详见第~\ref{subsec:exp-rolealign-results}~节表 X。" (Fill in numbers from ch4 results.)

24. **`thesis/chapters/ch3_method.tex:503-551` (§3.5)** — Add forward reference to adaptive-protection ablation in ch4 (if exists) or to Needle PASS rate in ch4 to back the motivation.

25. **`thesis/chapters/ch3_method.tex:672-811` (§3.7)** — §3.7.3 split-channel claims "max abs diff < 1e-2" and "10/10 Needle PASS" must forward-reference a specific ch4 row or appendix validation table.

### §6.6 NIT (optional)

26. **`thesis/chapters/ch2_related_work.tex:381`** — Replace "vLLM 等推理框架" with "vLLM、TensorRT-LLM 等推理框架".
27. **`thesis/chapters/ch3_method.tex:315`** — Consider unifying the loop-index $h$ vs $h_q$ across §3.3.2 and §3.7.4.
28. **`thesis/chapters/ch3_method.tex:382`** — Label the Q pre-scaling identity as equation (`\label{eq:ch3-invtau-qprescale}`).
29. **`thesis/chapters/ch3_method.tex:734`** — "启发式选择策略" is the only "heuristic" hit in ch3; consider noting it also applies to the inv_tau intuitive argument as a higher-level meta consistency.

---

## §7 Estimates for Phase 4 scope

**ch2:** 9 bib entries to add (9 priority-P0–P3 papers) + ~30 new lines of prose + 1 new appendix subsection (KIVI gap audit) + 6 symbol fixes. Estimated Phase 4 ch2 edit time: 45–60 min.

**ch3:** 2 CRITICAL edits (~4 lines) + 2 MAJOR additions (~10 lines) + 4 MINOR additions (~8 lines) + 1 table extension. Estimated Phase 4 ch3 edit time: 30–45 min.

**Total Phase 4 scope:** ~90–105 min of thesis edits + 1 Phase 4 compile-check (xelatex) + 1 Round-2 smoke verification (0 undefined refs).

**Not in Phase 4 scope (deferred to Round 3 or later):**
- FP8 paper citation and vLLM version pinning (would require new literature scout pass).
- Full KVPress toolbox discussion (currently only Expected Attention hit, background-only).
- MQA / MLA extension of the GQA-scale finding (digest §5.5 outstanding gaps).
- Cross-bit-width comparison of inv_tau effect at 1-bit (AsymKV scale).
- Formal proof of σ_eff ∝ σ/√N_rep (keeping "intuitive argument" disclaimer is the correct Round-2 stance).

---

## §8 Summary of key findings

1. **ch3 T9 cleanup was incomplete** — two residual "可选 / 候选增强" instances in ch3:65-66 and ch3:96 directly contradict the T1/T3 repositioning. CRITICAL fix required before other edits.
2. **ch2 has zero explicit novelty defense sentence** ("首个 / to the best of our knowledge") — the softest form of C5 defense is missing from the literature chapter.
3. **ch2 cites zero of the 9 Phase-1 [SHOULD_ADD] papers** — largest actionable gap; AhaKV + AsymKV are P0.
4. **KIVI gap audit is 1/6 reflected in ch2** — residual buffer, async pipeline, token staging, layer strategy, Pre-RoPE Key all missing.
5. **σ_eff ∝ σ/√N_rep formula is absent from ch3** — it's in abstracts, ch1, ch4, ch5 but not in the method chapter that the experiments validate.
6. **Cross-chapter symbol inconsistency** — ch2 uses `$h_Q$, $h_{KV}$` (lowercase), ch3-ch5 use `$H_q$, $H_{kv}$` (uppercase).
7. **3 AI-trace hotspots** identified: ch2 FP8 paragraph, ch3 inv_tau opening, ch3 §3.1 overview; +1 bonus hotspot at ch3 §3.1 (the residual contradiction).
8. **ch3 has no "intuitive argument / heuristic / future formal proof" disclaimer** in §3.4 — only ch4 has the disclaimer, creating a ch3→ch4 dependency for the correct reading.

---

## §9 Meta

- **Files read:** `thesis/chapters/ch2_related_work.tex` (L1-523), `thesis/chapters/ch3_method.tex` (L1-1026), `reports/round_2/literature_digest.md` (L1-486), `docs/kivi_gap_audit.md` (L1-114), `docs/rolealign_design_note.md` (L1-137). Spot-checks against `ch1_introduction.tex`, `ch4_experiments.tex`, `ch5_conclusion.tex`, `appendix.tex`, `abstract_{en,zh}.tex` for symbol/formula consistency.
- **Greps executed:** 13 targeted searches (FP8, KIVI, 9 Phase-1 papers, GQA, novelty markers, symbol consistency, sigma_eff, \ref density, intuitive-argument markers).
- **Git history checked:** 2f65927 (T3 refactor) + a81a8bc (T7 FP8 unification) + f216143 (T9 cleanup) + b01eee4 (T7 follow-up).
- **No files modified** (Phase 2 scope = read + produce this document only).
- **Next phase:** Phase 3 = dispatch 6 reviewers each focused on their §5.x pointer list, then Phase 4 = apply the ordered §6 action items, then Phase 5 = re-compile + smoke + final iteration.md entry.
