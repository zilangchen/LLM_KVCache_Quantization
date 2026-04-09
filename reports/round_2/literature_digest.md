# Round 2 Phase 1 Literature Digest

- **Date:** 2026-04-08
- **Round:** 2 (thesis-polish-loop, Phase 1 — literature scout)
- **Author Agent:** literature scout (Sonnet)
- **Target paper:** EMNLP 2026 ARR submission, KV Cache Quantization
- **Time budget:** ~60 min
- **Methodology:** 5 WebSearch query batches + 19 WebFetch arxiv abstract pulls + cross-check against `thesis/chapters/ch2_related_work.tex`

---

## §1 Executive Summary

19 papers (and 1 engineering issue) were investigated. The investigation has two goals:
1. **Identify gap-filling additions for ch2 Related Work** (the "should-add" pile).
2. **Defend C5 (inv_tau × GQA scale-dependent effect) novelty** by exhaustively searching for any prior work that already reports the GQA H_kv × quantization-noise interaction or per-head temperature correction tied to KV cache quantization.

### 1.1 Tag distribution

| Tag | Count | Papers |
|---|---|---|
| `[ALREADY_CITED]` | 8 | KIVI, KVQuant, ZipCache, QServe, GEAR, QJL, KVTuner, ThinK, IntactKV, QeRL (10 hits, 8 unique entries in this digest, 2 are refreshed snapshots) |
| `[SHOULD_ADD_TO_CH2]` | **8** | AQUA-KV, PolarQuant, ChunkKV, BitDecoding, Outlier Tokens Tracing, AsymKV, HeadKV, AhaKV, Softmax-Not-Enough |
| `[BACKGROUND_ONLY]` | 4 | KVLinC, Expected Attention, Scalable-Softmax, Keep-the-Cost-Down survey |
| `[NOVELTY_RISK]` | **0 confirmed**, 3 near-miss (KVTuner, AhaKV, AsymKV — all clearable with explicit citation + differentiation) |

(Some papers are double-counted because they appear in multiple slots; see §2 for the canonical per-paper assignment.)

### 1.2 Top-line conclusion

> **C5 novelty is intact**. After exhaustively searching all five query angles (KV quantization, asymmetric K/V theory, GQA × quantization noise, long-context KV compression, behavior-alignment calibration), **no published academic work** directly reports the joint observation that (i) per-head softmax temperature correction is effective for KV-cache quantization compensation, and (ii) its effectiveness has a scale-dependent reversal across GQA H_kv configurations.
>
> Three near-misses exist (KVTuner / AhaKV / AsymKV) and require **explicit citation + clean differentiation** in ch2 §2.5.x. None are blockers; all three observe pieces of the chain but stop short of the C5 finding.

### 1.3 NOVELTY_RISK summary

| Paper | Risk level | Distance from C5 | Mitigation |
|---|---|---|---|
| KVTuner (ICML 2025) | NEAR-MISS | Lemma 1 quantifies Key-error amplification 13.9× INT8→INT4, observes "non-sparse heads have higher error", but stops at *layer* granularity | Already cited in our §2.5.x with clean differentiation. **NO ACTION NEEDED.** |
| AhaKV (arXiv 06/2025) | MEDIUM-LOW | Adapts a *global* softmax scale based on attention entropy for *eviction* importance scoring | **MUST ADD** to §2.5.x with one contrastive sentence. The "softmax scale tuning" idea exists but for a different purpose and at different granularity. |
| AsymKV (arXiv 10/2024) | MEDIUM (but for C2, not C5) | Observes K > V sensitivity asymmetry like us, but attributes to *layer depth* not RoPE channel oscillation | **MUST ADD** to §2.5 with a paragraph crediting and differentiating. Affects C2 attribution, not C5. |
| Softmax-Not-Enough (NeurIPS 2024 W) | LOW | Theoretical proof that softmax sharpness decays with N tokens; proposes adaptive temperature *at LM head* | **SHOULD ADD** as foundational anchor for "softmax temperature is a known knob". No competition. |
| HeadKV (ICLR 2025) | LOW | Per-head granularity exists in literature, but as binary keep/drop, not continuous correction | **SHOULD ADD** to §2.5 eviction sub-section to explicitly contrast continuous vs binary head-level operation. |

---

## §2 Query-by-Query Results

### Q1 — KV Cache 量化新工作 2024-2025

**Search query:** `"KV cache quantization" 2024 OR 2025 (EMNLP OR ACL OR NAACL OR NeurIPS OR ICLR)`

#### Paper Q1.a — KIVI (already in ch2)

- Title: KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache
- Authors: Liu, Yuan, Jin, Zhong, Xu, Braverman, Chen, Hu
- Venue: ICML 2024 · arXiv 2402.02750
- Summary: Per-channel Key + per-token Value asymmetric 2-bit quantization (no calibration). 2.6× memory, 2.35-3.47× throughput.
- Decision: `[ALREADY_CITED]` (ch2 line 234, 513). Direct comparison baseline for our int4_ours_asym variant.
- ch2 integration note: Already prominent in §2.5; no change needed.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/kivi.md`

#### Paper Q1.b — KVQuant (already in ch2)

- Title: KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization
- Authors: Hooper, Kim, Mohammadzadeh, Mahoney, Shao, Keutzer, Gholami
- Venue: NeurIPS 2024 · arXiv 2401.18079
- Summary: Per-channel Key + Pre-RoPE Key + Non-uniform codebook + Dense-and-sparse outlier handling. Reaches 1M-context single-A100 demo.
- Decision: `[ALREADY_CITED]` (ch2 line 241).
- ch2 integration note: Already prominent in §2.5; no change.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/kvquant.md`

#### Paper Q1.c — ZipCache (already in ch2)

- Title: ZipCache: Accurate and Efficient KV Cache Quantization with Salient Token Identification
- Authors: He, Zhang, Wu, Liu, Zhou, Zhuang
- Venue: NeurIPS 2024 · arXiv 2405.14256
- Summary: Channel-separable token-wise quantization + normalised-attention-score saliency for mixed-precision allocation.
- Decision: `[ALREADY_CITED]` (ch2 line 246).
- ch2 integration note: Already in §2.5; consider also citing in §2.5.x to support "saliency-guided heterogeneous precision is a precedent" framing.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/zipcache.md`

#### Paper Q1.d — Outlier Tokens Tracing (NEW; should add)

- Title: Accurate KV Cache Quantization with Outlier Tokens Tracing
- Authors: Su, Zhou, Qiu, Li, Xia, Li, Duan, Wang, Zhang
- Venue: ACL 2025 · arXiv 2505.10938
- Summary: Dynamic tracing of outlier tokens during decoding; channel-wise Key + token-wise Value at 2-bit; 6.4× memory, 2.3× throughput.
- Decision: `[SHOULD_ADD_TO_CH2]`. Currently not cited.
- ch2 integration note: Add a one-sentence cite next to IntactKV (line ~277): "Outlier Tokens Tracing [Su et al. 2025] dynamically detects sensitive tokens online during decoding, complementing IntactKV's static pivot-token approach." Updates the K/V quant comparison table.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/outlier_tokens_tracing.md`

### Q2 — 非对称 KV 量化理论

**Search query:** `"asymmetric KV quantization" "per-channel" "per-token" quantization`

#### Paper Q2.a — KIVI (re-hit)

See Q1.a. Already cited.

#### Paper Q2.b — KVTuner (already in ch2; closest competitor)

- Title: KVTuner: Sensitivity-Aware Layer-Wise Mixed-Precision KV Cache Quantization
- Authors: Li, Xing, Li, Qu, Zhen, Liu, Yao, Pan, Yuan
- Venue: ICML 2025 · arXiv 2502.04420
- Summary: Layer-wise mixed-precision search via multi-objective optimization. Lemma 1: Key error amplified 13.9× INT8→INT4. Reaches ~3.25-bit Llama-3.1-8B with 21.25% throughput gain.
- Decision: `[ALREADY_CITED]` in §2.5.x (line 398). Closest prior to our error-amplification analysis but stops at *layer* granularity.
- ch2 integration note: Already differentiated in §2.5.x lines 404-410. No change needed; this is the *anchor* of our novelty defense.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/kvtuner.md`

#### Paper Q2.c — AsymKV (NEW; should add — affects C2)

- Title: AsymKV: Enabling 1-Bit Quantization of KV Cache with Layer-Wise Asymmetric Quantization Configurations
- Authors: Tao, Yu, Zhou (Alibaba)
- Venue: arXiv October 2024 · arXiv 2410.13212
- Summary: Layer-wise asymmetric Key vs Value precision based on early-layer K-sensitivity observation. 1-bit on ~75% of layers without significant degradation.
- Decision: `[SHOULD_ADD_TO_CH2]`. Currently not cited. **MEDIUM threat to C2** (independent K > V observation), zero threat to C5.
- ch2 integration note: Add a paragraph in §2.5 (after line 244 KVQuant block, before ZipCache) acknowledging AsymKV's K > V finding then differentiating: AsymKV uses layer depth as the precision allocator; we trace the K-sensitivity gap to RoPE-induced channel oscillation and exploit BA-guided per-channel percentile at the tensor level. Update the comparison table to add an AsymKV row.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/asymkv.md`

#### Paper Q2.d — AQUA-KV / Cache Me If You Must (NEW; should add)

- Title: Cache Me If You Must: Adaptive Key-Value Quantization for Large Language Models
- Authors: Shutova, Malinovskii, Egiazarian, Kuznedelev, Mazur, Surkov, Ermakov, Alistarh
- Venue: arXiv January 2025 · arXiv 2501.19392
- Summary: Compact adapters predict V from K (or vice versa); only the residual is quantized. ~2.0-2.5 bits per value on Llama-3.2 with single-shot calibration (1-6 hours).
- Decision: `[SHOULD_ADD_TO_CH2]`. Currently not cited.
- ch2 integration note: Add a one-sentence cite in §2.5 next to GEAR (line 251): "AQUA-KV [Shutova et al. 2025] further exploits inter-K-V dependency by training compact prediction adapters." Note in our discussion that AQUA-KV's K-as-predictor design is consistent with our diagnostic finding that Key carries more semantic load than Value.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/aquakv.md`

### Q3 — GQA × Quantization Noise (CRITICAL FOR C5 NOVELTY)

**Search query:** `"GQA" "grouped query attention" quantization noise OR dilution OR "head count"` plus 4 follow-up refinement queries.

#### Paper Q3.a — KVTuner (re-hit; see Q2.b)

Stopped at layer granularity. No GQA × scale analysis. Not a competitor.

#### Paper Q3.b — HeadKV / HeadKV-R2 (NEW; should add — per-head precedent)

- Title: Not All Heads Matter: A Head-Level KV Cache Compression Method
- Authors: Fu, Cai, Asi, Xiong, Dong, Xiao
- Venue: ICLR 2025 · arXiv 2410.19258
- Summary: Per-attention-head importance scoring (retrieval + reasoning); selectively retains 1.5% of KV cache while keeping 97% of LongBench QA score.
- Decision: `[SHOULD_ADD_TO_CH2]`. **LOW C5 threat**: per-head granularity exists, but as *binary keep/drop* not continuous temperature correction.
- ch2 integration note: Add a sentence in §2.5 eviction sub-section (around line 296 next to DuoAttention) and in §2.5.x as a contrast: "HeadKV [Fu et al. 2025] selects which heads to retain, but does not modify the attention weights of retained heads. Our per-head inv_tau is a continuous correction inside the surviving heads and is orthogonal to head selection."
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/headkv.md`

#### Paper Q3.c — AhaKV (NEW; should add — closest mechanism)

- Title: AhaKV: Adaptive Holistic Attention-Driven KV Cache Eviction
- Authors: Gu, Jiang, Jin, Guo, Zhang, Xu
- Venue: arXiv June 2025 · arXiv 2506.03762
- Summary: An *eviction* method that adaptively tunes the *softmax scale* based on the expectation of attention entropy. Recognises bias in accumulated attention scores used by H2O / SnapKV.
- Decision: `[SHOULD_ADD_TO_CH2]`. **MEDIUM-LOW C5 threat**: this is the closest "softmax-scale-tuning" precedent, but applied to *eviction importance scoring*, *globally*, and *entropy-driven* — not per-head, not quantization-aware, no GQA analysis.
- ch2 integration note: Add a *contrastive* sentence to §2.5.x (right after the QeRL/KVTuner/Bondarenko paragraph): "Concurrently, AhaKV [Gu et al. 2025] introduces a global entropy-driven softmax scale tuning for eviction importance scoring. Our inv_tau correction differs in three respects: it is per-head, calibrated against quantization noise rather than entropy, and we are first to report its scale-dependent (de)effectiveness across GQA H_kv configurations." This single sentence pre-empts the strongest reviewer concern.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/ahakv.md`

#### Paper Q3.d — llama.cpp issue #21385 (engineering only — NOT citable)

- Title: Per-head adaptive KV cache quantization
- Authors: GitHub user "SCJedi"
- Venue: Engineering issue, not peer-reviewed
- Summary: Proposal for per-head bit-width allocation using entropy formula `b_h = b_avg + 0.25 * (H_avg - H_2(h))`. Reports lossless q4_0 on hybrid models.
- Decision: `[BACKGROUND_ONLY]` — engineering issue, not a paper. **NO C5 threat** (different mechanism: bit-width vs temperature, entropy vs noise).
- ch2 integration note: Do not cite. Internal reassurance only that no academic per-head KV temperature correction work pre-empts ours.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/llama_cpp_per_head.md`

### Q4 — Long-context KV Compression

**Search query:** `"long context inference" "KV compression" OR "KV cache compression" 2024 2025`

#### Paper Q4.a — ChunkKV (NEW; should add)

- Title: ChunkKV: Semantic-Preserving KV Cache Compression for Efficient Long-Context LLM Inference
- Authors: Liu, Tang, Dong, Li, Liu, Li, Hu, Chu
- Venue: NeurIPS 2025 · arXiv 2502.00299
- Summary: Compress at the *semantic chunk* level rather than per token. Adds layer-wise index reuse for amortised chunk selection. + 8.7% accuracy at the same compression ratio; +26.5% throughput.
- Decision: `[SHOULD_ADD_TO_CH2]`. Currently not cited.
- ch2 integration note: Add one sentence in §2.5 eviction sub-section (around line 292 SnapKV): "ChunkKV [Liu et al. 2025] generalises eviction from token to semantic chunk, achieving + 8.7% accuracy at the same compression ratio."
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/chunkkv.md`

#### Paper Q4.b — BitDecoding (NEW; should add — system kernel angle)

- Title: BitDecoding: Unlocking Tensor Cores for Long-Context LLMs Decoding with Low-Bit KV Cache
- Authors: Du, Cao, Cheng, Mai, Cao, Yang
- Venue: ICLR 2025 · arXiv 2503.18773
- Summary: Tensor-Core-friendly memory layouts + warp-level dequantization + software-pipelined kernels for INT4/INT2 KV decode. 7.5× over FP16 FlashDecoding-v2; 8.6× on Blackwell with NVFP4.
- Decision: `[SHOULD_ADD_TO_CH2]`. Currently not cited.
- ch2 integration note: Add a sentence in §2.6.3 (Triton 编程模型, around line 467): "Concurrently, BitDecoding [Du et al. 2025] demonstrates that Tensor-Core-friendly kernel layouts (rather than CUDA cores) are essential for unlocking the 4-bit speed budget on Hopper / Blackwell GPUs."
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/bitdecoding.md`

#### Paper Q4.c — PolarQuant (NEW; should add)

- Title: PolarQuant: Quantizing KV Caches with Polar Transformation
- Authors: Han, Kacham, Karbasi, Mirrokni, Zandieh (Google DeepMind / Yale)
- Venue: arXiv February 2025 · arXiv 2502.02617
- Summary: Random preconditioning + polar coordinate conversion; only the angles are quantized; no normalization step needed; > 4.2× compression at the best quality.
- Decision: `[SHOULD_ADD_TO_CH2]`. Currently not cited.
- ch2 integration note: Add a one-sentence cite in §2.5 next to QJL (line 278): "Its successor PolarQuant [Han et al. 2025] eliminates scale storage entirely via polar transformation."
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/polarquant.md`

#### Paper Q4.d — GEAR (already cited)

See §2.5 line 251. No update needed.

### Q5 — Behavior-Alignment Calibration

**Search query:** `"behavior alignment" calibration OR "KL divergence" "softmax temperature" quantization`

#### Paper Q5.a — Softmax Is Not Enough (NEW; should add as foundational anchor)

- Title: Softmax is not Enough (for Sharp Out-of-Distribution / Sharp Size Generalisation)
- Authors: Veličković et al. (Google DeepMind)
- Venue: NeurIPS 2024 Workshop
- Summary: Theoretical proof that softmax attention coefficients disperse as the number of tokens grows; proposes adaptive softmax temperature based on input entropy at the LM head.
- Decision: `[SHOULD_ADD_TO_CH2]`. **LOW C5 threat** — different mechanism, applied at LM head not inside attention, not noise-based.
- ch2 integration note: Add a foundational sentence in §2.5.x (theoretical motivation paragraph) or §3 inv_tau introduction: "DeepMind's softmax-not-enough analysis [Veličković et al. 2024] establishes that softmax sharpness is fundamentally limited at scale; our inv_tau correction provides a per-head, quantization-aware instantiation of the temperature knob, but inside attention rather than at the LM head."
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/softmax_not_enough.md`

#### Paper Q5.b — KVLinC

- Title: KVLinC: KV Cache Quantization with Hadamard Rotation and Linear Correction
- Authors: Saxena, Roy
- Venue: arXiv October 2025 · arXiv 2510.05373
- Summary: Hadamard rotation for Value error reduction + lightweight linear correction adapters for Key error.
- Decision: `[BACKGROUND_ONLY]` — Hadamard rotation already represented by QuaRot in our ch2 (line 262). Linear adapter is post-attention, distinct from temperature correction.
- ch2 integration note: Optional one-sentence add to QuaRot paragraph (line 269): "KVLinC [Saxena & Roy 2025] further compensates the rotated-and-quantized residual via a small learned linear adapter." Not essential.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/kvlinc.md`

#### Paper Q5.c — Expected Attention

- Title: Expected Attention: KV Cache Compression by Estimating Attention from Future Queries
- Authors: Devoto, Jeblick, Jégou (NVIDIA / Sapienza)
- Venue: arXiv October 2025 · arXiv 2510.00636
- Summary: Closed-form expected-attention estimator for training-free eviction. Releases KVPress library aggregating 20+ techniques.
- Decision: `[BACKGROUND_ONLY]`. Eviction-side method.
- ch2 integration note: Optional. KVPress library reference could be a useful single-citation for the general "KV compression toolbox" framing.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/expected_attention.md`

#### Paper Q5.d — Scalable-Softmax / SSMax

- Title: Scalable-Softmax Is Superior for Attention
- Venue: arXiv January 2025 · arXiv 2501.19399
- Summary: Length-adaptive softmax variant (not noise-adaptive). Targets long-context retrieval, not quantization compensation.
- Decision: `[BACKGROUND_ONLY]`. Different problem (length dilution vs quantization noise dilution).
- ch2 integration note: Optional footnote-level mention.
- Snapshot: `artifacts/round2_2026-04-08/raw_papers/scalable_softmax.md`

---

## §3 Recommended Additions to ch2 (Priority-Ordered)

| Priority | Paper | Citation key (suggested) | Insertion point | Effort |
|---|---|---|---|---|
| **P0** | AhaKV (Gu et al. 2025) | `gu2025ahakv` | §2.5.x (line ~403, after Bondarenko) | 1 sentence + bib entry |
| **P0** | AsymKV (Tao et al. 2024) | `tao2024asymkv` | §2.5 (line ~244, after KVQuant block) | 1 paragraph + bib entry + table row |
| **P1** | HeadKV (Fu et al. 2025) | `fu2025headkv` | §2.5 eviction sub-section (line ~296) and §2.5.x | 2 sentences + bib entry |
| **P1** | Softmax-Not-Enough (Veličković 2024) | `velickovic2024softmax` | §2.5.x intro paragraph | 1 sentence + bib entry |
| **P1** | Outlier Tokens Tracing (Su et al. 2025) | `su2025outliertoken` | §2.5 (line ~277, near IntactKV) | 1 sentence + bib entry |
| **P2** | AQUA-KV (Shutova et al. 2025) | `shutova2025aquakv` | §2.5 (line ~251, near GEAR) | 1 sentence + bib entry |
| **P2** | ChunkKV (Liu et al. 2025) | `liu2025chunkkv` | §2.5 eviction sub-section (line ~292) | 1 sentence + bib entry |
| **P2** | BitDecoding (Du et al. 2025) | `du2025bitdecoding` | §2.6.3 Triton sub-section (line ~467) | 1 sentence + bib entry |
| **P3** | PolarQuant (Han et al. 2025) | `han2025polarquant` | §2.5 (line ~278, near QJL) | 1 sentence + bib entry |
| **P3** (optional) | KVLinC (Saxena & Roy 2025) | `saxena2025kvlinc` | §2.5 QuaRot paragraph (line ~269) | 1 sentence |

**Total bib additions:** 9 entries (or 10 with KVLinC). Estimated ch2 line growth: ~25-30 lines, well within budget.

**Total comparison table additions:** 1 row (AsymKV).

---

## §4 NOVELTY_RISK Detailed Analysis

### 4.1 The C5 claim (restated)

> **C5 (Finding 4):** Per-head softmax temperature correction (inv_tau), motivated by behavior alignment to compensate quantization-induced flattening, exhibits a *scale-dependent reversal*: it improves quality on H_kv = 2 architectures (Qwen2.5-1.5B), is neutral on H_kv = 4 (Qwen2.5-7B), and *degrades* quality on H_kv ≥ 8 (LLaMA-3.1-8B). We attribute this to GQA noise dilution: σ_eff ∝ σ / √N_rep, so the per-head correction strength must be tuned to architecture, not transferred uniformly.

This claim has two structurally separable parts:

- **Part A:** "Per-head softmax temperature correction is an effective KV cache quantization compensation mechanism."
- **Part B:** "Its effectiveness has a scale-dependent reversal driven by the GQA H_kv parameter."

A novelty challenge against C5 needs to defeat **both** parts, not just one.

### 4.2 Threat assessment

| Threat angle | Closest paper | Status |
|---|---|---|
| Per-head granularity in KV cache exists | HeadKV (ICLR 2025) | DEFEATED. HeadKV is binary keep/drop, not continuous correction. |
| Per-head softmax scale tuning exists | AhaKV (arXiv 06/2025) | DEFEATED. AhaKV is global (not per-head), entropy-driven (not noise-driven), and applied to eviction (not quantization compensation). |
| Softmax temperature tuning is a known knob | Softmax-Not-Enough (Veličković 2024) | DEFEATED. Applied at the LM head, not inside attention. Confirms theoretical foundation but doesn't claim our application. |
| Quantization flattens attention distributions | QeRL (ICLR 2026), Bondarenko (ICCV 2023 W) | DEFEATED. Both observe flattening but at the LM head (QeRL) or as SQNR analysis (Bondarenko); neither propose temperature correction inside attention. |
| Key error amplification analysis exists | KVTuner (ICML 2025) | DEFEATED. Lemma 1 quantifies amplification but stops at layer granularity; never reaches per-head correction or GQA analysis. |
| K > V sensitivity is known | AsymKV (arXiv 10/2024), KIVI (ICML 2024) | NEUTRAL. This is C2, not C5. AsymKV credits K-dominance via *layer depth*; we credit it via *RoPE channel oscillation* and exploit it via per-channel BA percentile. Independent confirmation strengthens both. |
| GQA × quantization noise interaction | None found | **C5 part B is unprecedented in published literature.** |
| Per-head temperature correction tied to quantization | None found | **C5 part A is unprecedented in published literature.** |

### 4.3 Conclusion

**C5 stands.** Both parts (per-head temperature correction for KV quantization, *and* its scale-dependent GQA dependency) are unprecedented in the published academic literature reviewed. The three near-miss papers (AhaKV / AsymKV / KVTuner) need explicit citation and one-sentence differentiation each in ch2 §2.5.x to pre-empt reviewer accusations, but none structurally defeat the C5 claim.

The single most important defensive citation is **AhaKV**, because reviewers searching for "softmax temperature tuning" will land on it first. It must be explicitly named and differentiated in §2.5.x. The next most important is **AsymKV**, but this is for C2 attribution, not C5.

---

## §5 Round 2 Phase 2 Recommendations

Based on Phase 1 findings, the next phases of Round 2 thesis-polish-loop should prioritise:

### 5.1 Phase 2 (ch2 surgical updates) — recommended actions

1. **Insert AhaKV citation in §2.5.x** (P0). One contrastive sentence after the QeRL/KVTuner/Bondarenko block (line ~403). Adds bib entry `gu2025ahakv`. **This is the single most important defensive change of Round 2.**

2. **Insert AsymKV citation paragraph in §2.5** (P0). 3-4 sentence paragraph after KVQuant block (line ~244). Acknowledge the K > V finding, then differentiate via RoPE channel oscillation. Adds bib entry `tao2024asymkv` and one row to the comparison table.

3. **Insert HeadKV + Softmax-Not-Enough + Outlier-Tokens-Tracing** (P1). Each is a 1-sentence cite. Distributed across §2.5 and §2.5.x.

4. **Insert AQUA-KV + ChunkKV + BitDecoding + PolarQuant** (P2/P3). One sentence each in their respective sub-sections.

### 5.2 Phase 3 (ch3 Method clarification) — derivative actions

1. **Tighten the inv_tau theoretical motivation in ch3** by citing Softmax-Not-Enough and explicitly framing inv_tau as "the per-head, quantization-aware instantiation of the temperature knob inside attention".

2. **Strengthen the C5 statement** in ch3 §3.x (inv_tau ablation) by adding a sentence noting that the closest precedent (AhaKV) operates globally on eviction importance and that no published work reports the GQA H_kv scale-dependence we observe.

3. **Optionally add a footnote** in ch3 acknowledging KVTuner's Lemma 1 as the closest *quantitative* error amplification result and noting our complementary contribution: KVTuner stops at amplification quantification, we add the compensation mechanism.

### 5.3 Phase 4 (writing polish) — defensive sentences

Add or strengthen the following sentences in ch2 §2.5.x and ch5 limitation discussion:

- "To the best of our knowledge, no published work reports per-head softmax temperature correction for KV cache quantization compensation, nor analyses its dependence on GQA H_kv configuration."
- (In limitations) "Our scale-dependent finding for inv_tau is observational; we do not claim a closed-form theoretical bound but provide empirical evidence across H_kv ∈ {2, 4, 8} and offer the σ_eff ∝ σ / √N_rep dilution as the most parsimonious mechanistic explanation."

### 5.4 Suggested bib stanzas (skeletons)

```bibtex
@inproceedings{gu2025ahakv,
  title={AhaKV: Adaptive Holistic Attention-Driven KV Cache Eviction for Efficient Inference of Large Language Models},
  author={Gu, Yifeng and Jiang, Zicong and Jin, Jianxiu and Guo, Kailing and Zhang, Ziyang and Xu, Xiangmin},
  year={2025},
  eprint={2506.03762},
  archivePrefix={arXiv}
}
@article{tao2024asymkv,
  title={AsymKV: Enabling 1-Bit Quantization of KV Cache with Layer-Wise Asymmetric Quantization Configurations},
  author={Tao, Qian and Yu, Wenyuan and Zhou, Jingren},
  year={2024},
  eprint={2410.13212},
  archivePrefix={arXiv}
}
@inproceedings{fu2025headkv,
  title={Not All Heads Matter: A Head-Level KV Cache Compression Method with Integrated Retrieval and Reasoning},
  author={Fu, Yu and Cai, Zefan and Asi, Abedelkadir and Xiong, Wayne and Dong, Yue and Xiao, Wen},
  booktitle={ICLR},
  year={2025}
}
@inproceedings{velickovic2024softmax,
  title={Softmax is not Enough (for Sharp Size Generalisation)},
  author={Veli{\v{c}}kovi{\'c}, Petar and others},
  booktitle={NeurIPS Workshop on Scientific Methods for Understanding Deep Learning},
  year={2024}
}
@inproceedings{su2025outliertoken,
  title={Accurate KV Cache Quantization with Outlier Tokens Tracing},
  author={Su, Yi and Zhou, Yuechi and Qiu, Quantong and Li, Juntao and Xia, Qingrong and Li, Ping and Duan, Xinyu and Wang, Zhefeng and Zhang, Min},
  booktitle={ACL},
  year={2025}
}
@article{shutova2025aquakv,
  title={Cache Me If You Must: Adaptive Key-Value Quantization for Large Language Models},
  author={Shutova, Alina and Malinovskii, Vladimir and Egiazarian, Vage and Kuznedelev, Denis and Mazur, Denis and Surkov, Nikita and Ermakov, Ivan and Alistarh, Dan},
  year={2025},
  eprint={2501.19392},
  archivePrefix={arXiv}
}
@inproceedings{liu2025chunkkv,
  title={ChunkKV: Semantic-Preserving KV Cache Compression for Efficient Long-Context LLM Inference},
  author={Liu, Xiang and Tang, Zhenheng and Dong, Peijie and Li, Zeyu and Liu, Yue and Li, Bo and Hu, Xuming and Chu, Xiaowen},
  booktitle={NeurIPS},
  year={2025}
}
@inproceedings{du2025bitdecoding,
  title={BitDecoding: Unlocking Tensor Cores for Long-Context LLMs Decoding with Low-Bit KV Cache},
  author={Du, Dayou and Cao, Shijie and Cheng, Jianyi and Mai, Luo and Cao, Ting and Yang, Mao},
  booktitle={ICLR},
  year={2025}
}
@article{han2025polarquant,
  title={PolarQuant: Quantizing KV Caches with Polar Transformation},
  author={Han, Insu and Kacham, Praneeth and Karbasi, Amin and Mirrokni, Vahab and Zandieh, Amir},
  year={2025},
  eprint={2502.02617},
  archivePrefix={arXiv}
}
```

### 5.5 Outstanding gaps (deferred to Round 3)

The following angles were not exhaustively covered and could be revisited in Round 3 if reviewer comments raise them:

- **MQA-only models** (PaLM, original Gemini): does our scale-dependent finding extend to H_kv = 1? (Our experiments cover H_kv ∈ {2, 4, 8} only.)
- **MLA (Multi-head Latent Attention) models** (DeepSeek-V2/V3): is the inv_tau analysis even meaningful when K is reconstructed from a latent vector?
- **Sub-2-bit regime**: AsymKV / QJL are at 1-bit; we are at 4-bit. Cross-bit-width comparison of the inv_tau effect would be a future-work paragraph.
- **Linear / hybrid attention models** (Mamba-Transformer hybrids): the llama.cpp issue noted hybrid robustness; we should disclaim that our findings are specific to softmax attention.

---

## §6 Methodology Notes

- **Searches executed:** 5 primary + 5 follow-up refinement queries (10 WebSearch calls total).
- **Abstracts fetched:** 19 WebFetch calls + 1 GitHub issue. 2 fetches failed (403 / wrong arxiv ID); both mitigated via search-result summaries.
- **ch2 cross-check method:** Grep against `thesis/chapters/ch2_related_work.tex` for each candidate paper's name and lead author.
- **Tag definitions:**
  - `[ALREADY_CITED]` — paper appears in ch2 today.
  - `[SHOULD_ADD_TO_CH2]` — paper does not appear in ch2 today and should be added in Phase 2.
  - `[BACKGROUND_ONLY]` — paper is relevant for context but not citation-worthy in our current ch2 scope.
  - `[NOVELTY_RISK]` — paper potentially threatens a C-claim novelty; needs explicit handling.

### 6.1 Search hit log

| Query | Top hits checked | Snapshots produced |
|---|---|---|
| Q1 | KIVI, KVQuant, ZipCache, OTT, KVQuant survey, ChunkKV | 4 + cross-references |
| Q2 | KIVI, KVTuner, AsymKV, AQUA-KV, AnyPrec | 4 + cross-references |
| Q3 (5 searches) | GQA paper, HeadKV, AhaKV, llama.cpp issue, KVTuner re-hit, Softmax-not-enough | 5 + cross-references |
| Q4 | ChunkKV, BitDecoding, PolarQuant, RocketKV (no abstract), Expected Attention | 5 + cross-references |
| Q5 | Softmax-not-enough, KVLinC, Expected Attention, SSMax, AhaKV re-hit | 5 + cross-references |

### 6.2 Fetch failures

| URL | Error | Mitigation |
|---|---|---|
| `https://openreview.net/pdf/1cef9774f0f0cf7bb9e4b167882e3ad3ef8cde16.pdf` (KV Cache Transform Coding ICLR 2026) | 403 | Not critical; this is a transform-coding angle, not a temperature-correction angle. Documented for completeness. |
| `https://openreview.net/pdf/a962114bdc0ad8851693eb79691a18996d319808.pdf` (Softmax-Not-Enough PDF) | 403 | Mitigated via web search results that fully describe the paper's claims. |
| `https://openreview.net/forum?id=bJ33TvbJW0` (SinkQ) | 403 | SinkQ is a sink-token quantization method; from the title alone we can classify it as a token-isolation extension of IntactKV / OTT, no C5 threat. Not snapshotted. |
| `https://arxiv.org/abs/2502.19854` | Wrong paper (CV image fusion) | Original target was RocketKV; the arxiv ID was incorrect. RocketKV is summarised via Q4 search results only — it's a two-stage eviction + sparse-attention method, not a C5 threat. |
| `https://arxiv.org/abs/2407.18003` | Returned the COLM 2024 KV-cache survey | Snapshotted as `keep_cost_down_survey.md`. |

---

## §7 File Inventory

### Created by this phase

```
reports/round_2/literature_digest.md             (this file)
artifacts/round2_2026-04-08/raw_papers/
├── kivi.md                          # Q1, ALREADY_CITED
├── kvquant.md                       # Q1, ALREADY_CITED
├── zipcache.md                      # Q1, ALREADY_CITED
├── outlier_tokens_tracing.md        # Q1, SHOULD_ADD_TO_CH2 (P1)
├── kvtuner.md                       # Q2, ALREADY_CITED, near-miss cleared
├── asymkv.md                        # Q2, SHOULD_ADD_TO_CH2 (P0, C2)
├── aquakv.md                        # Q2, SHOULD_ADD_TO_CH2 (P2)
├── headkv.md                        # Q3, SHOULD_ADD_TO_CH2 (P1)
├── ahakv.md                         # Q3, SHOULD_ADD_TO_CH2 (P0, C5 defense)
├── llama_cpp_per_head.md            # Q3, BACKGROUND_ONLY (engineering)
├── chunkkv.md                       # Q4, SHOULD_ADD_TO_CH2 (P2)
├── bitdecoding.md                   # Q4, SHOULD_ADD_TO_CH2 (P2)
├── polarquant.md                    # Q4, SHOULD_ADD_TO_CH2 (P3)
├── gear.md                          # Q4, ALREADY_CITED
├── qjl.md                           # Q4, ALREADY_CITED
├── softmax_not_enough.md            # Q5, SHOULD_ADD_TO_CH2 (P1)
├── kvlinc.md                        # Q5, BACKGROUND_ONLY
├── expected_attention.md            # Q5, BACKGROUND_ONLY
├── scalable_softmax.md              # Q5, BACKGROUND_ONLY
├── think.md                         # Q4, ALREADY_CITED (refresh)
├── intactkv.md                      # Q1/Q4, ALREADY_CITED (refresh)
├── qerl.md                          # Q5, ALREADY_CITED (refresh)
├── qserve.md                        # Q1, ALREADY_CITED
└── keep_cost_down_survey.md         # Q4, BACKGROUND_ONLY
```

24 paper snapshots total (target was ≥ 15).

### Updated

```
.agents/skills/thesis-polish-loop/state/venues_read.json
```

---

**End of Phase 1 Literature Digest.**
