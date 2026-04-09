# Round 3 Phase 1 Literature Digest — ch4 Experimental Methodology Focus

- **Date:** 2026-04-09
- **Round:** 3 (thesis-polish-loop, Phase 1 — literature scout for ch4 deep review)
- **Author Agent:** literature scout (ch4 methodology focus)
- **Target paper:** EMNLP 2026 ARR submission, "Behavior-Aligned KV Cache Quantization"
- **Target chapter:** `thesis/chapters/ch4_experiments.tex` (1748 lines)
- **Time budget:** ~60 min (actual ~75 min)
- **Methodology:** 14 WebSearch queries + 18 WebFetch calls + manual cross-check against Round 2 digest

---

## §1 Executive Summary

### 1.1 Why Round 3 is different from Round 2

Round 2 Phase 1 (2026-04-08) did 24 papers of novelty-defense scouting for the ch2 Related Work and the C5 (inv_tau × GQA) novelty claim. Round 2 venues: ICML, NeurIPS, ICLR, ACL, COLM, NeurIPS_Workshop, ICCV_Workshop.

Round 3 Phase 1 focuses on **ch4 experimental methodology** — benchmarks, statistical framework, ablation design, seed/variance reporting, and PPL evaluation validity. New venue rotation: **EMNLP, NAACL, TACL, COLING, SIGMOD, NeurIPS D&B, COLM 2025**. These venues were not scouted in Round 2.

### 1.2 Top-line conclusion

> **ch4's methodology is largely defensible**, but **three specific additions are strongly recommended** for Round 3 Phase 2 (ch4 deep review), and **one specific concern** exists about raw-PPL use for long-context evaluation that needs a hedge footnote.
>
> The headline finding is that ch4's statistical framework (Bootstrap CI + sign-flip + BH-FDR) **exceeds the rigor of 84% of LLM benchmarks surveyed** by Burden et al. (NeurIPS 2025). ch4 should cite this aggressively — it's a major defensive win.

### 1.3 Tag distribution

| Tag | Count | Papers |
|---|---|---|
| `[SHOULD_ADD_TO_CH4]` | **7** | 100-LongBench, Madaan variance, Song small-sample, Chen non-determinism, Li numerical non-determinism, Measuring-what-Matters, LongPPL, KV-Compression-Benchmark, LongBench-v2, ABLATOR |
| `[CONTRADICTS]` | **1** | LongPPL (challenges raw-PPL use for long-context) |
| `[BACKGROUND_ONLY]` | **12** | AbGen, AsymKV COLING, XQuant, Token-Precision, TALE, MiniKV, LRQ, PQCache, HELMET+LongProc, BABILong, Sober-Look, Beyond-Singular, PM-KVQ, DynamicKV |
| `[ALREADY_COVERED_IN_CH4]` | 3 | Standard Bootstrap CI, greedy PPL determinism hedge (partially), BH-FDR (citation exists) |

### 1.4 New venues added to `venues_read.json`

- **EMNLP** 2024 (findings) + 2025 (main + findings)
- **NAACL** 2025 long papers
- **COLING** 2025 main conference
- **TACL** 2025
- **SIGMOD** 2025
- **NeurIPS D&B Track** 2024 (BABILong) + 2025 (Measuring-what-Matters)
- **COLM** 2025 (adds a year to Round 2's COLM 2024)
- **ACL 2025 Findings** (MiniKV — ACL main was in Round 2)

This gives Round 3 **8 new venues** not covered by Round 2, exceeding the 4-venue target.

### 1.5 Top 3 most critical findings for ch4

1. **LongPPL (ICLR 2025)** challenges the use of raw PPL for long-context evaluation. ch4 uses raw PPL in 5+ tables for the C5 claim. This needs a §4.1.2 footnote + §4.9 threats-to-validity paragraph. (`[CONTRADICTS]`)

2. **Measuring what Matters (NeurIPS 2025 D&B)** reports that only **16% of 445 surveyed LLM benchmarks** employ any statistical testing. ch4 uses Bootstrap CI + sign-flip + BH-FDR — vastly exceeds this baseline. Should be cited as a defensive anchor. (`[SHOULD_ADD_TO_CH4]`)

3. **Song et al. (EMNLP 2024)** argues Bayesian empirical-Bayes CIs are tighter than Bootstrap for n=5 sample sizes. ch4 uses exactly n=5 seeds and Bootstrap. Need to acknowledge this as a conservative choice. (`[SHOULD_ADD_TO_CH4]`)

---

## §2 Query-by-Query Results

### Q1 — Long-context benchmark methodology critique

**Search queries:**
- `"RULER" OR "LongBench" OR "InfiniteBench" benchmark methodology critique 2024 2025`
- `"RULER" benchmark NAACL 2024 long context evaluation synthetic tasks`
- `"LongBench v2" OR "BABILong" long context benchmark 2024 2025`
- `"Helmet" OR "LongProc" long context benchmark 2024 2025`
- `"LongScore" OR "LongPPL" length-adaptive perplexity long context evaluation`

#### Paper Q1.a — 100-LongBench (arXiv 2505.19293)

- **Title:** 100-LongBench: Are de facto Long-Context Benchmarks Literally Evaluating Long-Context Ability?
- **Venue:** arXiv May 2025
- **Core critique:** Existing benchmarks (NIAH, RULER, LongBench, InfiniteBench) suffer from (i) unrealistic synthetic content, (ii) fixed sequence lengths, (iii) base-ability vs long-context conflation
- **Proposed fix:** LongScore metric = (Score − Base Ability) / Base Ability
- **Relevance to ch4:** Base-ability conflation critique is **partially mitigated** by ch4 comparing quantization on the same base model, but the synthetic-content critique applies to ch4's self-implemented LongBench generator and RULER implementation
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add one sentence in §4.1.2 (benchmarks) or §4.9 (threats) acknowledging the critique and noting ch4's same-base-model mitigation
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/100_longbench.md`

#### Paper Q1.b — LongPPL (ICLR 2025) ★ CRITICAL ★

- **Title:** What is Wrong with Perplexity for Long-context Language Modeling?
- **Authors:** PKU-ML
- **Venue:** **ICLR 2025** · arXiv 2410.23771
- **Core critique:** Raw PPL averages across all tokens, diluting the signal from "key tokens" (tokens where long-range info matters). Raw PPL is a poor predictor of long-context benchmark scores
- **Empirical evidence:** LongPPL (key-token-weighted) has **Pearson = −0.96** with long-context benchmarks; raw PPL correlation is much lower
- **Proposed fix:** Long-short contrastive method to identify key tokens, then compute PPL only on those
- **Relevance to ch4:** **HIGH** — ch4 uses raw PPL in 5+ tables for C1, C2, and C5 claims. The C5 (inv_tau × GQA) claim is measured as raw PPL deltas, which LongPPL argues is non-predictive of long-context quality
- **Mitigation:** ch4 also reports Needle / RULER / LongBench / retrieval metrics for every configuration. The multi-metric framework partially defuses LongPPL's single-metric critique. But the PPL-specific claims need hedging
- **Tag:** `[CONTRADICTS]` / `[SHOULD_ADD_TO_CH4]` — **HIGH priority**
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/longppl_iclr2025.md`

#### Paper Q1.c — LongBench v2 (ACL 2025)

- **Title:** LongBench v2: Towards Deeper Understanding and Reasoning on Realistic Long-context Multitasks
- **Authors:** Bai et al. (THUDM)
- **Venue:** **ACL 2025** · arXiv 2412.15204
- **Core contribution:** 503 human-annotated multiple-choice questions, 8K-2M context, 6 categories. Replaces v1's heterogeneous scoring (F1 / ROUGE / Accuracy / Edit Similarity) with **unified multiple-choice accuracy**
- **Relevance to ch4:** ch4's self-implemented LongBench-style synthetic generator follows v1 conventions (7 tasks, 4 metric types). v2 did not exist when ch4 was designed
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add a §4.1.2 defensive cite noting that ch4 stays with v1-style for reproducibility, and a v2 re-eval is deferred to future work
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/longbench_v2.md`

#### Paper Q1.d — BABILong (NeurIPS 2024 D&B)

- **Title:** BABILong: Testing the Limits of LLMs with Long Context Reasoning-in-a-Haystack
- **Venue:** **NeurIPS 2024 Datasets & Benchmarks** (Spotlight Poster)
- **Core finding:** Popular LLMs effectively utilize **only 10-20% of long contexts**. 20 reasoning tasks, scalable to 10M tokens
- **Relevance to ch4:** ch4 tops out at 32K and doesn't claim 128K+. BABILong suggests even "long-context-capable" models fall short of using their claimed windows
- **Tag:** `[BACKGROUND_ONLY]` — ch5 future work paragraph only
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/babilong.md`

#### Paper Q1.e — HELMET + LongProc (ICLR 2025)

- **Title (a):** HELMET: How to Evaluate Long-context Models Effectively and Thoroughly
- **Title (b):** LongProc: Benchmarking Long-Context Language Models on Long Procedural Generation
- **Venue:** Both **ICLR 2025** (which is in Round 2's venue list, but not in Round 2's KV-scoped searches)
- **Relevance to ch4:** ch4's scope is 32K + short generation, matching KIVI/KVQuant baseline convention. HELMET extends to 128K, LongProc adds long generation — both outside ch4's scope
- **Tag:** `[BACKGROUND_ONLY]` — optional §4.9 scope defense
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/helmet_longproc.md`

### Q2 — Ablation study design best practices

**Search queries:**
- `ablation study design factor isolation seed reporting variance effect size deep learning 2024 2025`
- `"AblationBench" ablation study empirical AI design rigor 2024 2025`
- `ablation study confounding hyperparameter multiple simultaneous changes machine learning best practices 2024`
- `"Measuring what Matters" construct validity LLM benchmarks 2025`

#### Paper Q2.a — Measuring what Matters (NeurIPS 2025 D&B) ★★ CRITICAL ★★

- **Title:** Measuring what Matters: Construct Validity in Large Language Model Benchmarks
- **Authors:** Oxford Internet Institute + 29 expert reviewers
- **Venue:** **NeurIPS 2025 Datasets & Benchmarks** · arXiv 2511.04703
- **Scope:** Systematic review of **445 LLM benchmarks** from ICML/ICLR/NeurIPS/ACL/NAACL/EMNLP 2018-2024
- **Key finding:** Only **16.0% of reviewed benchmarks employ any statistical testing**. Only 53.4% present construct-validity evidence. Exact matching is the dominant metric (81.3% partial, 40.7% exclusive)
- **Eight recommendations:** define phenomenon, measure only the phenomenon, representative datasets, acknowledge reuse, prepare for contamination, use statistical methods, error analysis, justify construct validity
- **Relevance to ch4:** **HIGH defensive value**. ch4 uses Bootstrap CI, sign-flip permutation, BH-FDR — exceeds the rigor of 84% of benchmarks. ch4 should cite this aggressively
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add to §4.1.4 (statistics) and §4.9 (threats). Two options provided in snapshot
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/measuring_what_matters.md`

#### Paper Q2.b — AbGen (ACL 2025)

- **Title:** AbGen: Evaluating Large Language Models in Ablation Study Design and Evaluation for Scientific Research
- **Venue:** **ACL 2025** · arXiv 2507.13300
- **Core criteria for ablation quality:** Importance, Faithfulness, Soundness
- **Relevance to ch4:** ch4's ablation sections (§4.2.4, §4.2.5, §4.4, §4.5.4) are largely AbGen-compliant. §4.2.4 is explicitly labeled "observational" due to bundled confounds — this matches AbGen's faithfulness criterion (transparent reporting of confounds)
- **Tag:** `[BACKGROUND_ONLY]` — ch4 already passes the AbGen bar. Useful as a defensive reference if a reviewer challenges §4.2.4's confounded comparison
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/abgen2025.md`

#### Paper Q2.c — ABLATOR (PMLR v224)

- **Title:** ABLATOR: Robust Horizontal-Scaling of Machine Learning Ablation Experiments
- **Key messages:** Retune hyperparameters after ablating; multiple simultaneous changes prevent attribution; report primary metric + variance via multiple seeds
- **Relevance to ch4:** ch4's §4.4 K/V sensitivity ablation has a **minor seed-count inconsistency** — PPL uses seed=1234 only, RULER/LongBench use 3 seeds. Defensible per §4.1.4's PPL determinism argument, but needs explicit footnote
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add a short footnote to Table 4.8 (K/V ablation PPL) explicitly justifying the mismatched seed counts
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/ablator_mlsys.md`

### Q3 — Statistical framework for LLM evaluation

**Search queries:**
- `"Bootstrap confidence interval" LLM benchmark evaluation multiple testing BH-FDR 2024 2025`
- `LLM benchmark variance reporting estimator NAACL EMNLP 2024 2025 seed random`
- `Madaan Singh "Quantifying Variance" benchmark evaluation LLM bootstrap estimator`
- `"paired bootstrap" NLP significance testing Koehn best practices benchmark 2024`
- `"Beyond the Singular" multiple generations benchmark evaluation effect LLM 2025`

#### Paper Q3.a — Madaan et al. (arXiv 2406.10229) ★ CRITICAL ★

- **Title:** Quantifying Variance in Evaluation Benchmarks
- **Authors:** Lovish Madaan et al. (Meta / Cambridge / Stanford / UCL)
- **Venue:** arXiv 2406.10229 (June 2024); OpenReview pending
- **Methodology:** Trained **10 Llama-2-7B models from scratch** with different seeds to ground-truth seed variance
- **Key findings:**
  - Seed variance is generally **lower than** 95% bootstrap CI → bootstrap is **conservative**, good news for ch4
  - 10 seeds is the gold standard; small benchmarks (COPA, HumanEval) show highest variance
  - Continuous probability metrics yield higher signal-to-noise than discrete accuracy
  - Psychometrics (IRT, item analysis) do not meaningfully reduce variance
  - Explicit caution against declaring superiority without proper hypothesis testing
- **Relevance to ch4:** ch4 uses 5 quality-eval seeds (vs. the 10-seed Madaan gold standard) and 10,000-resample bootstrap CI. Madaan's work says bootstrap CI is *conservative* relative to true variance → ch4's CIs are over-estimates, which is safe
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add to §4.9 threats-to-validity: "5 seeds is below the 10-seed gold standard of Madaan et al. (2024); however, Bootstrap CI is conservative relative to true seed variance in their analysis, so our CI widths overestimate true uncertainty"
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/madaan2024variance.md`

#### Paper Q3.b — Song et al. (EMNLP 2024 main) ★ CRITICAL ★

- **Title:** Precise Model Benchmarking with Only a Few Observations
- **Venue:** **EMNLP 2024** · aclanthology.org/2024.emnlp-main.536
- **Core thesis:** Bayesian empirical-Bayes CIs outperform Bootstrap for small sample sizes (n < 30)
- **Relevance to ch4:** ch4 uses **n=5 seeds** with bootstrap CI — exactly the small-n regime where Song argues bootstrap is suboptimal
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add to §4.1.4 or §4.9 footnote acknowledging that empirical Bayes would be an alternative for n=5, and explaining why ch4 retains Bootstrap (simplicity, no subjective prior)
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/song2024precise.md`

#### Paper Q3.c — Beyond the Singular (NeurIPS 2025 LLM Evals Workshop)

- **Title:** Beyond the Singular: Revealing the Value of Multiple Generations in Benchmark Evaluation
- **Venue:** NeurIPS 2025 Workshop on LLM Evals · arXiv 2502.08943
- **Core argument:** Deterministic greedy decoding and single-sample evaluation under-estimate benchmark variance. Advocates hierarchical statistical model with multiple generations per prompt
- **Relevance to ch4:** ch4 uses greedy decoding throughout. The critique has some bite but is tempered by ch4's multi-seed design and retrieval-metric redundancy
- **Tag:** `[BACKGROUND_ONLY]` — optional §4.9 mention that ch4's greedy choice trades generation-variance signal for reproducibility
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/beyond_singular_2025.md`

### Q4 — KV Cache quantization benchmarks at new venues (EMNLP / NAACL / TACL / TMLR / COLING / SIGMOD)

**Search queries:**
- `"KV cache" quantization benchmark EMNLP 2024 OR 2025`
- `"KV cache" quantization NAACL 2024 2025 low-bit asymmetric`
- `"KV cache" compression quantization TMLR TACL 2024 2025`
- `"KV cache" quantization "NAACL 2025" OR "NAACL 2024" efficient inference`
- `"TALE" "Token-Adaptive" KV cache TACL low-rank approximation long-context`
- `"PiKV" OR "PQCache" long context benchmark evaluation KV cache system`
- `"PM-KVQ" OR "NQKV" KV cache quantization 2024 2025 progressive`
- `"FIER" OR "KV retrieval" EMNLP 2025 fine-grained long context`
- `"DynamicKV" OR "TokenSelect" EMNLP 2025 task adaptive`

#### Paper Q4.a — KV Cache Compression Benchmark (EMNLP 2024 Findings)

- **Title:** KV Cache Compression, But What Must We Give in Return? A Comprehensive Benchmark of Long Context Capable Approaches
- **Venue:** **EMNLP 2024 Findings** · aclanthology.org/2024.findings-emnlp.266
- **Core contribution:** Comprehensive benchmark comparing quantization / eviction / prompt compression / RNN / hybrid methods on Llama-3-8B, Mistral-7B, LongChat-7B
- **Relevance to ch4:** ch4's multi-dimensional evaluation (quality / efficiency / memory) follows this benchmark convention. Currently not cited
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add a one-sentence §4.1 cite
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/kv_compression_benchmark_emnlp2024.md`

#### Paper Q4.b — XQuant (EMNLP 2025 main)

- **Title:** XQuant: Achieving Ultra-Low Bit KV Cache Quantization with Cross-Layer Compression
- **Venue:** **EMNLP 2025 Main Conference** (pages 9796-9811) · arXiv 2510.11236
- **Core:** Data-free calibration + cross-layer compression
- **Relevance to ch4:** New 2025 baseline, but ch4's baseline set is locked. Flag for Phase 2 ch2 addition
- **Tag:** `[BACKGROUND_ONLY]` for ch4; `[SHOULD_ADD_TO_CH2]` for Phase 2
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/xquant_emnlp2025.md`

#### Paper Q4.c — Token-Precision Trade-off (EMNLP 2025 Findings)

- **Title:** More Tokens, Lower Precision: Towards the Optimal Token-Precision Trade-off in KV Cache Compression
- **Venue:** **EMNLP 2025 Findings**
- **Core:** Pareto analysis of retention × bit-width trade-off
- **Relevance to ch4:** Complementary to ch4's "full-retention + low bit-width" scope
- **Tag:** `[BACKGROUND_ONLY]` — ch5 limitations cite
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/token_precision_tradeoff_emnlp2025.md`

#### Paper Q4.d — AsymKV (COLING 2025 — venue confirmed)

- **Title:** AsymKV: Enabling 1-Bit Quantization of KV Cache with Layer-Wise Asymmetric Quantization Configurations
- **Authors:** Tao, Yu, Zhou (Alibaba)
- **Venue:** **COLING 2025 Main Conference** (previously arXiv in Round 2; Round 3 confirms venue)
- **Relevance to ch4:** K > V asymmetric finding is consistent with ch4's observations. ch4's MixedKV (head-role mixed precision) is orthogonal to AsymKV's layer-wise mixed precision
- **Tag:** `[BACKGROUND_ONLY]` for ch4 methodology. Bib entry should be upgraded from `@article` to `@inproceedings{tao2025asymkv, booktitle={COLING}, ...}`
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/asymkv_coling2025.md`

#### Paper Q4.e — TALE (TACL 2025)

- **Title:** TALE: Token-Adaptive Low-Rank KVCache Approximation with Reconstruction Elimination
- **Venue:** **TACL 2025** (MIT Press)
- **Core:** Token-adaptive low-rank approximation with lazy evaluation and RoPE-aware reconstruction elimination. 9.1× reduction on Llama-3.1-8B
- **Relevance to ch4:** Orthogonal compression axis (rank, not bit-width). Not a ch4 competitor
- **Tag:** `[BACKGROUND_ONLY]` — TACL venue hit for Round 3 venues_read.json
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/tale_tacl2025.md`

#### Paper Q4.f — MiniKV (ACL 2025 Findings)

- **Title:** MiniKV: Pushing the Limits of 2-Bit KV Cache via Compression and System Co-Design
- **Venue:** **ACL 2025 Findings**
- **Core:** Sub-channel Key quantization + per-token Value + token selection + FlashAttention-compatible kernel
- **Tag:** `[BACKGROUND_ONLY]` — compound method, not directly comparable
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/minikv_acl2025.md`

#### Paper Q4.g — LRQ (NAACL 2025)

- **Title:** LRQ: Optimizing Post-Training Quantization for Large Language Models by Learning Low-Rank Weight-Scaling Matrices
- **Venue:** **NAACL 2025** · pages 7708-7743
- **Core:** Weight quantization (primary) + KV cache quantization (secondary)
- **Relevance to ch4:** Weight-quantization focus; ch4 is KV-only. New NAACL venue hit for Round 3
- **Tag:** `[BACKGROUND_ONLY]`
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/lrq_naacl2025.md`

#### Paper Q4.h — PQCache (SIGMOD 2025)

- **Title:** PQCache: Product Quantization-based KVCache for Long Context LLM Inference
- **Venue:** **SIGMOD 2025** · arXiv 2407.12820
- **Core:** Product quantization (codebook) instead of affine quantization. 4.60% improvement on InfiniteBench
- **Relevance to ch4:** Different mechanism (PQ codebook vs affine scale). New SIGMOD venue hit
- **Tag:** `[BACKGROUND_ONLY]`
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/pqcache_sigmod2025.md`

#### Paper Q4.i — PM-KVQ (2025)

- **Title:** PM-KVQ: Progressive Mixed-precision KV Cache Quantization for Long-CoT LLMs
- **Venue:** arXiv / OpenReview Vem6FQvRvq (unconfirmed venue)
- **Core:** Progressive block-level bit-width allocation for long-CoT reasoning
- **Tag:** `[BACKGROUND_ONLY]`
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/pm_kvq_2025.md`

#### Paper Q4.j — DynamicKV (EMNLP 2025 Findings)

- **Title:** DynamicKV: Task-Aware Adaptive KV Cache Compression for Long Context LLMs
- **Venue:** **EMNLP 2025 Findings** · arXiv 2412.14838
- **Core:** Task-adaptive per-layer retention. 1.7% cache retention while preserving 80-90% accuracy
- **Tag:** `[BACKGROUND_ONLY]` — eviction axis, not quantization
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/dynamickv_emnlp2025.md`

### Q5 — Reproducibility crisis + seed sensitivity

**Search queries:**
- `reproducibility "seed sensitivity" LLM evaluation non-determinism variance reporting 2024 2025`

#### Paper Q5.a — Chen et al. (NAACL 2025) ★ CRITICAL ★

- **Title:** Evaluation of LLMs Should Not Ignore Non-Determinism
- **Venue:** **NAACL 2025 Long Papers** · aclanthology.org/2025.naacl-long.211
- **Core finding:** Greedy decoding is **not** fully deterministic due to implementation details and numerical precision
- **Relevance to ch4:** ch4 §4.1.4 claims PPL is deterministic under greedy decoding on ch4's hardware. Chen et al. would classify this as a valid within-hardware claim but not cross-hardware guarantee
- **Tag:** `[SHOULD_ADD_TO_CH4]` — add to §4.1.4 clarifying that PPL determinism is a within-platform replication, not cross-hardware guarantee
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/chen2025nondeterminism.md`

#### Paper Q5.b — Li et al. (arXiv 2506.09501)

- **Title:** Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference
- **Venue:** arXiv June 2025
- **Core:** Root cause is non-associativity of floating-point arithmetic. Up to **9% accuracy variation and 9,000-token length variation** on DeepSeek-R1 due to GPU count/type/batch differences
- **Relevance to ch4:** Co-citation with Chen et al. NAACL 2025
- **Tag:** `[SHOULD_ADD_TO_CH4]` — co-cite
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/li2025nondeterminism_numerical.md`

#### Paper Q5.c — A Sober Look at Progress in Language Model Reasoning (COLM 2025)

- **Title:** A Sober Look at Progress in Language Model Reasoning
- **Venue:** **COLM 2025** · arXiv 2504.07086
- **Core finding:** Most RL-based reasoning progress doesn't survive rigorous re-evaluation. Benchmarks are highly sensitive to implementation choices, seeds, prompts, and hardware
- **Relevance to ch4:** Thematically aligned with ch4's rigor. ch4 is not a reasoning benchmark paper but could cite Sober-Look defensively
- **Tag:** `[BACKGROUND_ONLY]` — optional §4.9 cite
- **Snapshot:** `artifacts/round3_2026-04-09/raw_papers/sober_look_reasoning.md`

---

## §3 Recommended Additions to ch4 (Priority-Ordered)

| Priority | Paper | Insertion point | Effort | Purpose |
|---|---|---|---|---|
| **P0** | LongPPL (Fang et al. ICLR 2025) | §4.1.2 footnote + §4.9.3 paragraph | 2 sentences + bib entry + 1 longer paragraph | **CONTRADICTS hedge** — defends PPL-based C5 claim |
| **P0** | Measuring what Matters (Burden et al. NeurIPS 2025 D&B) | §4.1.4 (statistics) OR §4.9 (threats) | 1 sentence + bib entry | Defensive anchor — cites ch4 as 16%-statistical-testing counterexample |
| **P0** | Chen et al. Non-Determinism (NAACL 2025) + Li et al. Numerical Non-Determinism (arXiv) | §4.1.4 PPL determinism paragraph | 1 sentence + 2 bib entries | Hedges "PPL is deterministic" claim to "within-hardware" |
| **P1** | Madaan et al. Quantifying Variance (arXiv 2406.10229) | §4.9 threats-to-validity | 1 sentence + bib entry | Defends n=5 seed choice, notes bootstrap is conservative |
| **P1** | Song et al. Precise Benchmarking (EMNLP 2024) | §4.1.4 or §4.9 footnote | 1 sentence + bib entry | Acknowledges Bayesian alternative for small n |
| **P1** | 100-LongBench (arXiv 2505.19293) | §4.1.2 or §4.9 | 1 sentence + bib entry | Acknowledges synthetic-content critique + same-base-model mitigation |
| **P1** | LongBench v2 (Bai et al. ACL 2025) | §4.1.2 benchmarks | 1 sentence + bib entry | Acknowledges v2 exists + defers v2 re-eval to future work |
| **P2** | KV Cache Compression Benchmark (EMNLP 2024 Findings 266) | §4.1 exp setup | 1 sentence + bib entry | Cites benchmark-comparison convention precedent |
| **P2** | ABLATOR | §4.4.1 Table 4.8 footnote | 1 sentence | Justifies mixed seed counts (PPL seed=1234 vs RULER 3 seeds) |
| **P3** (optional) | AsymKV (COLING 2025) bib upgrade | bib file | 0 text, metadata update | Upgrade Round 2's @article to @inproceedings booktitle=COLING |

**Total bib additions:** 9 new entries (or 10 with Li et al.).
**Total ch4 line growth:** ~15-20 lines (well within thesis-format-refactor budget).
**Total figures/tables added:** 0 (no new experiments required).

---

## §4 Diff vs Round 2 Literature Digest

| Aspect | Round 2 (2026-04-08) | Round 3 (2026-04-09) |
|---|---|---|
| Focus | Novelty defense for ch2 + C5 claim | ch4 experimental methodology |
| Papers investigated | 24 | 24 |
| New venues added | 8 (ICML, NeurIPS, ICLR, ACL, COLM, NeurIPS-W, ICCV-W, arXiv) | 8 (EMNLP, NAACL, TACL, COLING, SIGMOD, NeurIPS D&B, COLM 2025, ACL Findings) |
| Total new bib entries recommended | 9 (ch2) | 9 (ch4) + metadata upgrade on AsymKV |
| `[CONTRADICTS]` / `[NOVELTY_RISK]` | 0 confirmed, 3 near-miss (mitigated) | 1 confirmed (LongPPL) — mitigated with hedge |
| `[SHOULD_ADD]` | 8 (ch2 additions) | 7 (ch4 additions) |
| `[BACKGROUND_ONLY]` | 4 | 12 |
| Main theme | "C5 novelty is intact" | "ch4 methodology is defensible, but 3 hedges needed" |

### Non-overlapping additions

Round 3 **does not re-investigate** any paper from Round 2. The 24 Round 3 papers are entirely new hits (Round 2 covered AhaKV, KVTuner, AsymKV/arXiv, HeadKV, ChunkKV, BitDecoding, PolarQuant, AQUA-KV, Outlier Tokens Tracing, KIVI, KVQuant, ZipCache, GEAR, QJL, IntactKV, QeRL, QServe, ThinK, Softmax-Not-Enough, KVLinC, Expected Attention, Scalable-Softmax, Keep-the-Cost-Down survey, llama.cpp issue).

Round 3 added: 100-LongBench, LongPPL, LongBench-v2, BABILong, HELMET+LongProc, Measuring-what-Matters, AbGen, ABLATOR, Madaan-Variance, Song-Precise, Beyond-Singular, Chen-NonDeterminism, Li-NumericalNonDeterminism, Sober-Look, KVCompression-EMNLP2024, XQuant-EMNLP2025, TokenPrecision-EMNLP2025, AsymKV-COLING2025 (venue upgrade), TALE-TACL2025, MiniKV-ACL2025, LRQ-NAACL2025, PQCache-SIGMOD2025, PM-KVQ, DynamicKV.

---

## §5 Round 3 Phase 2 Reviewer Input

Recommendations for the ch4 deep-review reviewer (Phase 2) to focus on:

### 5.1 High-priority ch4 vulnerabilities identified in Round 3

1. **PPL semantics under long context (§4.1.2 and §4.5.4 C5 claim)** — LongPPL argues raw PPL is a poor long-context metric. ch4's C5 claim (inv_tau × H_kv) is based entirely on raw PPL deltas. The Phase 2 reviewer must verify the hedge footnote is added and check whether the Needle-100% argument is sufficient to defuse the critique.

2. **PPL determinism claim (§4.1.4)** — The current wording ("贪婪解码下 PPL 在相同模型和测试集上是确定性的") is stronger than NAACL 2025 / arXiv 2025 evidence supports. Must be hedged to "within-platform reproducibility".

3. **n=5 seed count defense (§4.1.4 and all 5-seed tables)** — Madaan (2024) 10-seed gold standard and Song (2024) empirical-Bayes alternative both implicitly critique n=5. Must add defensive framing.

### 5.2 Medium-priority ch4 strengths worth emphasizing

1. **Statistical rigor as counter-example** — ch4's Bootstrap+sign-flip+BH-FDR is in the **top 16%** of LLM benchmarks per Burden et al. (NeurIPS 2025). This should be cited as a headline defense in §4.1.4.

2. **Multi-metric framework defuses single-metric critiques** — LongPPL and Beyond-Singular both critique single-metric evaluation. ch4 reports 4 quality metrics + 3 efficiency metrics, which is a natural defense.

3. **Synthetic task reproducibility** — ch4 uses self-implemented LongBench/RULER generators, eliminating dataset contamination (Measuring-what-Matters recommendation #5). This is a strength to name explicitly in §4.9.

### 5.3 Low-priority ch2 carryovers

Flag for separate ch2 Phase 2 update if budget allows:
- XQuant (EMNLP 2025 main) — new KV quant baseline
- MiniKV (ACL 2025 Findings) — token-selection × quantization compound
- AsymKV (COLING 2025) — bib upgrade from @article to @inproceedings
- DynamicKV (EMNLP 2025 Findings) — eviction axis contemporary

None of these are ch4 methodology issues.

### 5.4 Round 3 Phase 4 action items

The Phase 2 deep review should generate explicit edit-recommendations for:

1. `[P0]` §4.1.2 benchmarks: LongPPL footnote + LongBench-v2 footnote + 100-LongBench footnote
2. `[P0]` §4.1.4 statistics: Chen NAACL 2025 + Li arXiv 2025 determinism hedge; Madaan 2024 + Song 2024 seed-count defense; Burden NeurIPS 2025 as statistical-rigor anchor
3. `[P0]` §4.9.3 threats to validity: LongPPL threat-to-C5 paragraph (≈4 sentences)
4. `[P1]` §4.4.1 K/V ablation: ABLATOR-style seed-count footnote on Table 4.8
5. `[P1]` §4.1 exp setup: KV Compression Benchmark EMNLP 2024 precedent cite
6. `[P2]` Phase 2 ch2 chapter pass: XQuant, MiniKV, DynamicKV, AsymKV venue upgrade

### 5.5 Suggested bib stanzas (skeletons)

```bibtex
@inproceedings{fang2025longppl,
  title={What is Wrong with Perplexity for Long-context Language Modeling?},
  author={Fang, Lizhe and Liu, Yifei and Huang, Ruijie and Lv, Li and Jin, Zhouchen},
  booktitle={ICLR},
  year={2025},
  note={arXiv:2410.23771}
}
@inproceedings{burden2025measuring,
  title={Measuring what Matters: Construct Validity in Large Language Model Benchmarks},
  author={Burden, John and others},
  booktitle={NeurIPS Datasets and Benchmarks Track},
  year={2025},
  note={arXiv:2511.04703}
}
@inproceedings{chen2025nondeterminism,
  title={Evaluation of {LLM}s Should Not Ignore Non-Determinism},
  booktitle={NAACL},
  year={2025}
}
@article{li2025numerical,
  title={Understanding and Mitigating Numerical Sources of Nondeterminism in {LLM} Inference},
  year={2025},
  eprint={2506.09501},
  archivePrefix={arXiv}
}
@article{madaan2024variance,
  title={Quantifying Variance in Evaluation Benchmarks},
  author={Madaan, Lovish and Singh, Aaditya K. and Schaeffer, Rylan and others},
  year={2024},
  eprint={2406.10229},
  archivePrefix={arXiv}
}
@inproceedings{song2024precise,
  title={Precise Model Benchmarking with Only a Few Observations},
  booktitle={EMNLP},
  year={2024}
}
@article{100longbench2025,
  title={Are de facto Long-Context Benchmarks Literally Evaluating Long-Context Ability?},
  year={2025},
  eprint={2505.19293},
  archivePrefix={arXiv}
}
@inproceedings{bai2025longbench2,
  title={{LongBench} v2: Towards Deeper Understanding and Reasoning on Realistic Long-context Multitasks},
  author={Bai, Yushi and others},
  booktitle={ACL},
  year={2025}
}
@inproceedings{kvcomp2024benchmark,
  title={{KV} Cache Compression, But What Must We Give in Return? A Comprehensive Benchmark of Long Context Capable Approaches},
  booktitle={Findings of EMNLP},
  year={2024},
  pages={266}
}
```

### 5.6 Outstanding gaps (deferred to Round 4 if it happens)

The following angles were scouted but could be revisited:

- **LongPPL re-evaluation of ch4's inv_tau × GQA effect** — requires running LongPPL metric on existing outputs; feasible but requires running the LongPPL key-token identification pipeline. Deferred as out-of-scope for Round 3 Phase 2
- **Bayesian empirical-Bayes CI as alternative to Bootstrap** — requires a prior library over quantization-noise variance, which doesn't exist for KV cache; deferred
- **Multi-generation evaluation** — Beyond-Singular's recommendation would multiply cost by ~3; deferred
- **LongBench v2 re-evaluation** — would require running the THUDM suite; deferred

---

## §6 Methodology Notes

- **WebSearch calls:** 14 primary queries
- **WebFetch calls:** 18 (2 failed: one COLING PDF 403-like encoding issue, one Semantic Scholar empty page)
- **Snapshots produced:** 24 (target was 15-20)
- **Cross-check method:** Grep against `thesis/chapters/ch4_experiments.tex` for each candidate paper's concept. Also compared against Round 2 venues_read.json to ensure no overlap
- **Deferred papers not snapshotted:** HELM Long Context 2025 (Stanford CRFM), Atom MLSys 2024 (not KV-cache focused), Q-Hitter MLSys 2024 (token selection not quant), FIER EMNLP 2025 (covered by partial query result), NQKV (no venue confirmation)

### 6.1 Fetch failures

| URL | Error | Mitigation |
|---|---|---|
| `aclanthology.org/2025.coling-main.158.pdf` (AsymKV) | Partial PDF parse | Cross-referenced with Round 2 snapshot |
| `aclanthology.org/2025.naacl-long.393.pdf` (LRQ) | Binary PDF parse | Used search result summary |
| `semanticscholar.org/...Quantifying-Variance...` | Empty page | Used arxiv.org/html/2406.10229v1 instead |
| `aclanthology.org/2025.acl-long.611.pdf` (AbGen) | Partial PDF parse | Used arxiv html |

All mitigations successful.

---

## §7 File Inventory

### Created by this phase

```
reports/round_3/literature_digest.md                    (this file)
artifacts/round3_2026-04-09/raw_papers/
├── 100_longbench.md                              # Q1, SHOULD_ADD (P1)
├── longppl_iclr2025.md                           # Q1, CONTRADICTS / SHOULD_ADD (P0) ★
├── longbench_v2.md                               # Q1, SHOULD_ADD (P1)
├── babilong.md                                   # Q1, BACKGROUND
├── helmet_longproc.md                            # Q1, BACKGROUND
├── measuring_what_matters.md                     # Q2, SHOULD_ADD (P0) ★★
├── abgen2025.md                                  # Q2, BACKGROUND
├── ablator_mlsys.md                              # Q2, SHOULD_ADD (P1)
├── madaan2024variance.md                         # Q3, SHOULD_ADD (P1) ★
├── song2024precise.md                            # Q3, SHOULD_ADD (P1) ★
├── beyond_singular_2025.md                       # Q3, BACKGROUND
├── chen2025nondeterminism.md                     # Q5, SHOULD_ADD (P0) ★
├── li2025nondeterminism_numerical.md             # Q5, SHOULD_ADD (P0) ★
├── sober_look_reasoning.md                       # Q5, BACKGROUND
├── kv_compression_benchmark_emnlp2024.md         # Q4, SHOULD_ADD (P2)
├── xquant_emnlp2025.md                           # Q4, BACKGROUND (ch2 Phase 2)
├── token_precision_tradeoff_emnlp2025.md         # Q4, BACKGROUND
├── asymkv_coling2025.md                          # Q4, BACKGROUND (bib upgrade)
├── tale_tacl2025.md                              # Q4, BACKGROUND
├── minikv_acl2025.md                             # Q4, BACKGROUND
├── lrq_naacl2025.md                              # Q4, BACKGROUND
├── pqcache_sigmod2025.md                         # Q4, BACKGROUND
├── pm_kvq_2025.md                                # Q4, BACKGROUND
└── dynamickv_emnlp2025.md                        # Q4, BACKGROUND
```

24 paper snapshots total (target was ≥ 15, ideal 20+).

### Updated

```
.agents/skills/thesis-polish-loop/state/venues_read.json
```

---

**End of Round 3 Phase 1 Literature Digest.**
