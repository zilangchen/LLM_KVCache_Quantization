# Behavior-Guided KV Cache Quantization and Allocation

> Draft status: `candidate-main` rewrite draft, not `final-ready`
>
> This file is the second-round substantive rewrite. It keeps the new paper line from `v1` but tightens the writing toward a conference-style manuscript.
>
> Reference-note convention: citation placeholders such as `[KIVI]`, `[AsymKV]`, `[KVTuner]`, `[KVmix]`, `[H2O]`, `[SnapKV]`, and `[AhaKV]` should be mapped to BibTeX keys during LaTeX migration.

## Alternative Title Candidates

1. **Behavior-Guided KV Cache Quantization and Allocation**
2. **A Behavior-Centric Framework for KV Cache Quantization**
3. **From Behavior-Aligned Calibration to Behavior-Guided Allocation in KV Cache Quantization**

## Abstract

KV cache compression is increasingly necessary for long-context large language model inference, yet its quality degradation is not fully captured by numerical reconstruction error alone. We argue that **attention behavior** is the more appropriate object to analyze and preserve, and we use it as a unifying principle to organize calibration, mixed-precision allocation, and downstream budget proposal for KV cache quantization. We first validate this view through an **INT8 canonical validated instance**, which provides the cleanest end-to-end path from behavior-aligned calibration to deployable runtime integration while deliberately avoiding the claim that behavior-based calibration universally dominates standard numeric objectives. We then study mixed-precision KV allocation across multiple model families and scales and find that the most defensible empirical reading is **regime-dependent**: allocator quality varies with family, scale, and task, positional heuristics remain strong baselines, and no single fixed protection budget or aggregation rule transfers cleanly across all models. To move beyond brittle fixed-budget sweeps, we introduce **auto-k** as a profile-aware budget proposer derived from behavior-guided sensitivity profiles. Auto-k is best understood as a strong extension rather than the theoretical center of the paper: it is competitive across models, most clearly positive on Mistral-7B, and especially informative when contrasted with sharp anomalies such as the early-layer bottleneck observed on 3B. Overall, the paper contributes a framework and a regime-based reading of KV cache quantization rather than a universal winner story.

## 1. Introduction

Long-context inference increasingly exposes KV cache memory and bandwidth as the dominant systems bottleneck for decoder-only large language models. As context length and concurrency rise, KV cache storage scales linearly with sequence length and quickly overtakes model weights as the limiting factor for efficient deployment. This makes KV cache compression a practical requirement rather than a secondary optimization for modern long-context serving.

Quantization is a natural response to this bottleneck, but the way KV cache quantization is usually analyzed remains incomplete. Many pipelines are designed around numerical proxies such as reconstruction error, clipping loss, or mean squared error. These objectives are useful, but they do not fully describe what KV cache quantization disrupts at inference time. Keys and Values participate directly in attention score computation and softmax weighting. As a result, small numerical perturbations can trigger much larger behavioral changes once they are filtered through attention logits and normalized into generation-time decisions. The central question is therefore not only whether tensors are numerically close, but whether the model's **attention behavior** remains intact.

This observation motivates the main thesis of the paper: **behavior** should be treated as the unified analysis and design principle for KV cache quantization. Under this view, calibration is not merely the search for scales and clipping rules, and mixed-precision allocation is not merely the search for a convenient protection budget. Both are decisions about how behavioral distortion enters the system and where that distortion becomes most harmful. Framed this way, diagnosis, calibration, allocation, and budget proposal become parts of one structured design problem rather than loosely connected engineering decisions.

We operationalize this view in two layers. The first is **behavior-aligned calibration**, which produces deployable calibration artifacts from behavior-sensitive signals and is most cleanly validated in an INT8 setting. The second is **behavior-guided allocation**, which consumes behavior-derived profiles to decide where higher precision should be preserved under a constrained KV budget. This distinction is crucial. Calibration determines *how* a layer is quantized; allocation determines *where* limited precision should be spent. The framework connects these decisions while preserving their methodological separation.

The role of INT8 in this paper is deliberately narrow and precise. We use an **INT8 canonical validated instance** as the cleanest end-to-end path for validating the framework: calibration artifacts can be constructed offline, consumed by the runtime, and integrated with fused decode execution in a setting that is aggressive enough to matter but controlled enough to attribute. INT8 is therefore not the frontier low-bit target of the paper. It is the most auditable setting in which the framework can be validated as a real deployment path. Accordingly, INT8 should not be read as proving that behavior-based calibration universally outperforms MSE.

Once the problem shifts from calibration to mixed-precision allocation, the empirical picture becomes more heterogeneous. Across model families, scales, and tasks, allocator behavior is better described by **family-/scale-/task-dependent operating regimes** than by a single winner story. Some models sustain a broad high-quality band across several policies; some retain strong positional-heuristic baselines; and some reveal distinct failure modes that resist a universal interpretation. In particular, smaller models may exhibit sharp early-layer bottlenecks that are almost invisible in cross-family summaries.

This shift in empirical structure also changes how method design should be interpreted. Fixed protection budgets are often too brittle to transfer across models, while positional heuristics are far stronger baselines than a simple behavior-superiority narrative would suggest. This is precisely why **auto-k** matters in the current paper: not because it has already replaced all alternatives, but because it converts behavior-derived profiles into reusable budget suggestions. We therefore present auto-k as a **profile-aware budget proposer** and a strong downstream extension of the framework, not as the theory center of the paper.

The paper makes four claims. First, it proposes a **behavior-centric framework** for KV cache quantization that links calibration and allocation through a common analysis object. Second, it establishes an **INT8 canonical validated instance** as the cleanest end-to-end validation route for this framework. Third, it argues that mixed-precision allocator outcomes are best interpreted as **regime-dependent**, not universally optimal, and it explicitly repositions heuristic baselines as serious comparators. Fourth, it introduces **auto-k** as a profile-aware extension supported by meaningful but bounded evidence, with its strongest explicit support currently concentrated in Mistral and with its interpretation constrained by provenance.

> **Figure placeholder (Figure 1): Behavior-Centric Thesis Argument Map**
>
> Show the paper's logic as `behavior principle -> INT8 canonical validation -> regime-dependent allocation findings -> auto-k extension`, with explicit annotations for what is and is not claimed.

These claims define the paper's scope. This is not a paper that seeks to prove a universal superiority theorem for one behavior-guided method. It is a paper about choosing the right design object, validating that design object through the cleanest available path, and showing that once allocation enters the picture, the right empirical reading is regime structure rather than single-method victory. Section 2 positions the paper against prior work along the axes of format, calibration signal, and allocation policy. Section 3 presents the framework and its artifact structure. Section 4 reports the empirical findings using explicit evidence tiers and claim boundaries. Section 5 discusses limitations and future extensions. Section 6 concludes.

## 2. Related Work and Positioning

The prior literature on KV cache compression becomes clearer when decomposed along three design axes: **quantization format**, **calibration signal**, and **allocation policy**. Some methods primarily innovate on how Keys and Values are represented. Others focus on how quantization parameters are chosen. A third line asks how precision should be distributed unevenly across layers or roles once a uniform budget is no longer sufficient. This decomposition matters because the contribution of the current paper does not sit wholly inside any one of these axes. Instead, it connects them through a shared behavioral viewpoint.

### 2.1 Quantization format: asymmetric K/V design

On the format axis, the key reference point is **KIVI** [KIVI], which argues for asymmetric treatment of Keys and Values: Keys are quantized per channel, whereas Values are quantized per token. This is a foundational result in the low-bit KV literature because it demonstrates that the format should respect structural differences between K and V rather than quantize both sides symmetrically. Later work such as **AsymKV** [AsymKV] and other low-bit variants further explores asymmetric and layer-wise designs.

Our paper should be positioned fairly against this line. We do not claim to have invented a wholly new low-bit K/V format outside the broad design family that KIVI helped establish, nor do we claim decisive numerical victory over KIVI-style baselines. The contribution here is different. We reinterpret part of that asymmetric space through a **behavior-centric lens**, asking why such asymmetry makes sense from the perspective of attention preservation and what becomes possible once the resulting behavior-derived profile is reused beyond calibration.

### 2.2 Calibration signal: from numerical proxies to behavior-sensitive objectives

On the calibration axis, most pipelines still rely on numerical proxies such as MSE, percentile clipping, or related tensor-reconstruction criteria. These objectives are natural, useful, and in many mild regimes entirely adequate. However, they do not directly represent the object that ultimately matters for generation quality: whether the attention computation itself is distorted in ways that change model behavior.

This is where behavior-oriented calibration enters. A behavior-sensitive view asks not only whether quantized tensors remain close in Euclidean terms, but whether the *functional role* of Keys and Values inside attention remains stable. In the present work, this idea is instantiated as **behavior-aligned calibration**. The paper's claim, however, is intentionally narrower than a simple “KL beats MSE” story. The current INT8 evidence supports the role of behavior as a meaningful design object and a stable source of calibration artifacts, but not a universal superiority claim over numeric proxies.

### 2.3 Allocation policy: mixed precision and layer-wise budgeting

The third axis concerns **allocation**. Once a single uniform precision is insufficient, the problem becomes one of deciding where the limited high-precision budget should be spent. Here the closest prior lines are mixed-precision and layer-wise allocation methods, including sensitivity-aware or gradient-based approaches such as **KVTuner** [KVTuner], **KVmix** [KVmix], and related work on structured KV protection. These methods establish that unequal layer importance is real and that layer-wise budget assignment is a central part of the design space.

Our paper is aligned with that insight but differs in emphasis. We do not primarily contribute a stronger optimizer for per-layer bit assignment. Instead, we contribute a **framework-level connection**: the same behavior-derived profile that supports calibration can also guide allocation. This matters because it turns allocation from a purely heuristic search problem into a profile-driven policy problem. At the same time, we explicitly avoid claiming that this profile produces a universal winner policy.

### 2.4 Adjacent lines: attention-driven control and token-level memory selection

A conceptually adjacent line studies token-level KV retention or eviction rather than quantization. Methods such as **H2O** [H2O], **SnapKV** [SnapKV], and more recent attention-driven or saliency-aware memory selectors such as **AhaKV** [AhaKV] use attention-derived signals to determine which cached content should be retained under a budget. These methods do not solve the same problem as quantization, but they are relevant because they reinforce the broader point that **attention-derived signals can be operationally useful compression signals**.

We therefore treat this line as supportive rather than directly competitive. Eviction decides *what to keep*; quantization decides *how precisely to keep it*. Their budgets are different, but the underlying intuition overlaps: attention behavior can provide more faithful guidance than purely generic numeric surrogates.

### 2.5 Positioning of this paper

This positioning clarifies what the present paper is and is not. It is **not** a KIVI replacement paper, because it does not claim broad numerical victory over KIVI-style runtime asymmetric quantization. It is **not** a pure mixed-precision allocator paper, because the allocator results are intentionally interpreted as **regime-dependent** rather than as a universal policy. It is **not** a paper whose sole novelty is auto-k, because auto-k is presented as a downstream extension of a broader framework.

Instead, the paper contributes a **behavior-centric framework** that links calibration and allocation through reusable artifacts and shared behavioral interpretation. It contributes an **INT8 canonical validated instance** that grounds this framework in a clean deployment path. It contributes a **regime-based empirical reading** that resists the temptation to turn every result into a winner table. And it contributes **auto-k** as a profile-aware extension that makes behavior-guided allocation more automated without claiming universal optimality.

> **Table placeholder (Table 1): Prior Work Positioning Matrix**
>
> Columns: `Primary axis`, `Representative methods`, `What they solve well`, `What they do not claim`, `Relation to this paper`. Rows should cover format-oriented work such as KIVI and AsymKV, calibration-oriented work, layer-wise allocation methods such as KVTuner and KVmix, and attention-driven memory-selection methods such as H2O and SnapKV.

This is the fairest and most defensible novelty claim available under the current evidence. The paper's contribution is not that one method wins everywhere. It is that **behavior** provides a coherent design object for understanding, calibrating, and allocating KV precision, and that the resulting empirical reality is best read through regimes rather than universal superiority.

## 3. A Behavior-Guided Framework for KV Cache Quantization and Allocation

### 3.1 Principle: behavior as the design object

The framework begins from a simple observation: in KV cache quantization, the object that should be analyzed and protected is not merely tensor fidelity, but **attention behavior**. Keys and Values are not passive stored arrays. They are intermediates whose perturbations change attention logits, alter softmax weights, and ultimately shift generation. The purpose of the framework is therefore to make that behavioral object explicit and reusable across different stages of the quantization pipeline.

This does not imply that every stage optimizes the same scalar loss in the same way. The framework is layered by design. Some stages directly use behavior-sensitive objectives to produce calibration artifacts; later stages consume those artifacts and their summaries to make budget decisions. This separation is not a weakness. It is what allows the paper to distinguish **behavior-aligned calibration** from **behavior-guided allocation** and to speak precisely about the role of each.

### 3.2 Artifact structure: calibration artifact vs. policy artifact

The method revolves around two offline artifacts and one runtime consumption path. The first artifact is a **calibration artifact**, produced by the offline calibration pipeline. It stores quantization parameters and provenance metadata. The second artifact is a **policy artifact**, produced by the allocation stage. It stores layer-wise precision assignments and, in the case of auto-k, candidate and recommended protection budgets.

This distinction is central. The calibration artifact answers the question: *how should a given quantizer behave when applied?* The policy artifact answers a different question: *where should higher precision be spent under a constrained budget?* Keeping these two objects separate keeps the method auditable and prevents the paper from collapsing calibration and allocation into one vague optimization story.

> **Figure placeholder (Figure 2): Behavior-Guided Framework Figure**
>
> Show two artifact paths: `(1) calibration artifact: scales / group sizes / clipping / inv_tau / provenance` and `(2) policy artifact: per-layer bits / protected layers / candidate_ks / recommended_k`, both flowing into mixed-precision runtime routing.

### 3.3 Behavior-aligned calibration

Behavior-aligned calibration operates on sampled attention-side quantities and produces a frozen calibration artifact. In the current implementation, the calibration pipeline collects per-layer query, key, and value samples, searches over quantization hyperparameters such as clipping percentiles and grouping granularity, and then serializes the selected static scales together with auxiliary quantities such as `inv_tau` where needed. The artifact also records provenance information, including model identity, revision, seed, calibration dataset, and search configuration.

Conceptually, this stage remains tied to behavior rather than to generic tensor reconstruction alone. Its purpose is to ground quantization decisions in how quantization perturbs attention-side computation. However, this is also where the paper's scope must remain precise. In the present evidence base, especially in INT8, behavior-aware calibration does **not** justify a universal statement that one scalar loss always dominates MSE. The right statement is weaker and more useful: behavior-aligned calibration produces a reproducible, auditable artifact whose design rationale is anchored in attention behavior.

### 3.4 INT8 as the canonical validated instance

INT8 serves as the **canonical validated instance** of the framework. It is the most controlled regime in which the framework can be traced end to end: calibration produces an artifact, the runtime consumes that artifact, and fused decode execution can be validated inside one technically coherent path. That is why INT8 remains central in the rewritten paper even though it is not the most aggressive compression target.

The role of INT8 is therefore methodological rather than triumphalist. It validates that the framework is executable and auditable. It does not validate a universal superiority claim such as “behavior-based calibration beats MSE everywhere.” This distinction is important enough that the experiments section should make it explicit in table form.

### 3.5 Behavior-guided allocation

Once the question changes from calibration to mixed-precision allocation, the relevant problem changes with it. The allocator is not deciding what clipping percentile or group size to use. It is deciding **which layers deserve higher precision** under a limited budget. In the current framework, that decision is guided by a **behavior-derived layer sensitivity profile** extracted from the calibration stage.

The current allocator uses per-layer `k_scale` aggregation as the primary sensitivity proxy. This choice is motivated by a recurring empirical observation: Key-side perturbations often dominate downstream distortion more strongly than Value-side perturbations. By aggregating calibrated `k_scale` values to the layer level, the allocator obtains a compact profile that ranks where precision is most likely to matter. That ranking can then be converted into top-k, threshold-based, heuristic, uniform, random-control, or auto-k policies under one shared interface.

This is why the allocator is described as **behavior-guided** rather than behavior-aligned. The allocation stage does not directly re-optimize the original behavior loss for every candidate policy. Instead, it consumes an upstream behavior-derived artifact and turns that artifact into a budget decision. The distinction keeps the paper honest: allocation is informed by behavior, but it is not the same problem as direct calibration search.

### 3.6 Auto-k as a profile-aware budget proposer

The fixed-k setting exposed a structural problem in early allocator experiments: a hand-picked protection budget is often too brittle to transfer across families. A `k` that performs well on one model may be too conservative or too aggressive on another. This is the practical motivation for **auto-k**. Auto-k does not redefine the framework; it operationalizes the sensitivity profile by turning it into a reusable budget suggestion.

In the current implementation, auto-k is coverage-based. Given the sorted sensitivity profile, it asks how many top-sensitive layers are needed to cover a target fraction of the total sensitivity mass. This produces candidate protection budgets, a recommended default, and a selected budget that can be serialized into the policy artifact. The important point is interpretive: auto-k is a **budget proposer**, not a global optimum oracle. It compresses the search space into a small, behavior-informed set of likely budgets.

### 3.7 Runtime routing and extensibility

At runtime, the engine may consume both a calibration artifact and, for mixed-precision cache execution, an optional policy artifact. The runtime resolves the active per-layer bit schedule from the policy artifact and routes each layer through the corresponding quantization and dequantization path in the mixed KV cache. If no policy artifact is provided, it falls back to a global bit setting.

This separation also creates a clean extensibility path. Because the runtime already distinguishes quantizer parameters from policy routing, the same interface can later host **K/V-asymmetric allocation** or **prompt-adaptive policy selection** without changing the conceptual structure of the paper. These directions remain future-facing in the current manuscript, but the framework already anticipates them.

## 4. Experiments and Findings

### 4.1 Evidence tiers and experimental stance

We begin by making the evidence boundary explicit. The current draft is written at the **candidate-main** level. This means the available evidence is sufficient to support stable empirical readings, paper restructuring, and a framework-level narrative. It does **not** mean that all current numerical tables are final-ready. A clean-provenance rerun is still required before exploratory-produced assets can be promoted to final main-paper compare tables.

This distinction shapes the writing in this section. The goal is not to declare one globally optimal policy. The goal is to identify what the current data can support without over-reading it. In practice, this means emphasizing `stable reading`, `cannot over-interpret`, and compare-set governance rather than winner-style rhetoric.

### 4.2 INT8 canonical validated instance: what it validates and what it does not

The INT8 path is the cleanest end-to-end validation of the framework. It shows that behavior-aligned calibration can produce a deployable artifact, that the runtime can consume that artifact, and that the resulting path can be integrated with fused decode execution in one auditable chain. This is why INT8 remains central even though the paper is also concerned with more aggressive low-bit settings.

The key boundary is equally important. INT8 validates the **framework path**, not a broad superiority claim over standard numeric objectives. The safe reading is therefore: INT8 demonstrates that a behavior-centric calibration-and-runtime pipeline is real, reproducible, and deployable. The unsafe reading would be: INT8 proves that KL-based calibration dominates MSE in general. The current draft explicitly rejects the latter.

> **Table placeholder (Table 2): INT8 Claim Boundary Table**
>
> Columns: `Question`, `Evidence in current paper`, `Safe reading`, `Unsafe reading`. This table should make explicit that INT8 validates the framework path but does not establish universal `KL > MSE`.

### 4.3 Regime-dependent allocation is the main empirical message

Once the focus shifts from calibration to mixed-precision allocation, the strongest empirical message is not universal superiority but **regime dependence**. Allocation quality varies with model family, scale, and task mix. This is precisely why the earlier fixed-k story became unstable as more families and scales entered the compare set. The rewritten paper therefore treats regime identification, rather than single-method victory, as the allocator line's central empirical contribution.

The 7B setting remains one of the strongest findings because it exposes a meaningful aggregation split in a way that is both distinctive and interpretable. Rather than treating it as a universal allocation law, the paper uses it to demonstrate that allocator behavior can change structurally even within one behavior-guided framework. Its value lies in being a regime-defining result rather than a global theorem.

The 8B setting plays a different role. It marks the point where the old fixed-k story stops being clean. Wider fixed budgets can still perform well, but they no longer produce a straightforward monotonic narrative. This makes 8B the place where the paper most naturally transitions from hand-picked fixed-k intuition to profile-aware budget proposal. The stable reading is that auto-k becomes a competitive extension here. The unsafe reading would be that 8B already proves auto-k is the best policy.

The 14B setting strengthens another message: **heuristic and uniform baselines remain serious competitors**. This is not an embarrassment to hide. It is part of the paper's strongest reading. When large models exhibit a broad high-quality band across several policies, the allocator problem should be interpreted as a constrained regime problem rather than as a contest against weak baselines.

Mistral provides the cleanest explicit positive evidence for auto-k in the current compare set. It is the model on which auto-k most clearly reaches the top of the observed range while remaining compatible with the broader regime-based reading. The stable reading is therefore not “auto-k wins everywhere,” but “auto-k has now moved from conceptual extension to empirically supported extension, with its cleanest explicit win concentrated in Mistral.”

> **Table placeholder (Table 3): Cross-Model Regime Summary Table**
>
> Suggested columns: `Model`, `What stands out`, `Stable reading`, `Cannot over-interpret`, `Role in paper`. Avoid any winner, rank, or gap-to-best language.

> **Figure placeholder (Figure 3): Family Regime Map**
>
> A qualitative map locating 7B, 8B, 14B, Mistral, and 3B by dominant allocator behavior, heuristic competitiveness, and budget-band width.

### 4.4 Heuristic is a strong baseline, not a strawman

One of the most important corrections in the rewritten paper is the treatment of positional heuristics. Earlier versions risked implying that heuristic allocation was merely a weak baseline waiting to be surpassed by behavior-guided policies. The current evidence does not support that reading. In several settings, heuristic policies remain highly competitive, and in some tasks they can even define the effective quality ceiling of the compare set.

This strengthens the allocator story rather than weakening it. Once heuristic is treated seriously, the empirical message changes from “our allocator wins” to “allocator quality is itself regime-dependent.” The value of behavior-derived profiling then becomes clearer: it does not merely beat a weak control, but explains when strong positional priors remain adequate and when they fail.

### 4.5 Auto-k is a strong extension, not the theory center

Auto-k appears in this paper because fixed-k sweeps are brittle and difficult to transfer across families. Its purpose is to translate behavior-guided sensitivity profiles into actionable budget suggestions. In that sense, auto-k is a natural downstream method once the paper accepts that allocation is a profile-sensitive policy problem rather than a one-shot globally tuned constant.

The most stable current sentence is: **auto-k is a profile-aware budget proposer with real cross-model support, but explicit wins are still primarily Mistral-specific.** This formulation fits the current compare set. On 8B, auto-k is competitive and clearly stronger than the weaker fixed-budget families, but it does not take first place. On 14B, it sits in the top-quality tier without becoming the universal best. On Mistral, it provides the strongest explicit positive case. On 3B, it remains informative but is not the main story.

### 4.6 The 3B anomaly: early-layer bottleneck and first-layer rescue

The 3B setting reveals a qualitatively different operating regime and should be written as such. The main phenomenon is not that auto-k performs well. The main phenomenon is that the model exhibits a sharp **early-layer bottleneck**, to the extent that first-layer rescue becomes disproportionately important. In this regime, policies that protect the wrong positional region can fail badly, while a behavior-guided choice that prioritizes the earliest layer recovers quality in a way that is more revealing than a generic cross-model comparison.

This makes 3B one of the most valuable findings in the new paper. It shows that allocator behavior is not only family-dependent in a smooth sense, but can also cross into qualitatively different regimes. The correct interpretation remains local, however. The paper should state that 3B reveals an anomaly or special regime, not a universal small-model law.

> **Figure placeholder (Figure 4): 3B First-Layer Rescue Figure**
>
> Show the contrast between first-layer protection and heuristic mid-layer protection, together with the interpretation that 3B exhibits a heavy early-layer bottleneck.

### 4.7 Provenance and evidence governance

The current paper line is intentionally strict about provenance. The audited data are strong enough to support a `candidate-main` narrative, but they were produced under exploratory conditions at the result-production layer. For that reason, the paper uses them to support regime structure, anomaly interpretation, and qualitative ordering, while explicitly refusing to elevate them to final main-table status before clean-provenance coverage.

This is not a side note. It is part of the paper's methodological discipline. By separating exploratory-produced evidence from clean-produced evidence, the paper avoids a common failure mode in which a structurally sound narrative is undermined by overconfident ranking rhetoric. The strongest current message is already available without violating that boundary.

> **Table placeholder (Table 4): Compare-Set Governance Table**
>
> Columns: `Asset`, `Allowed role in current paper`, `Not allowed`, `Evidence tier`, `Promotion path`. This table should explicitly exclude smoke runs, low-information tasks, and recursively mixed assets from the main claim path.

## 5. Discussion, Limitations, and Future Work

The rewritten paper should be explicit about what it has established and what it has not. It has established that **behavior** is a useful unified analysis and design principle for KV cache quantization. It has established that the INT8 path provides a clean canonical validation route for this framework. And it has established that allocator outcomes are best interpreted through **regime-dependent** readings rather than universal laws. These are already substantial claims.

At the same time, several limitations remain. First, the present draft is still a **candidate-main** narrative rather than a final-ready result release. Clean-provenance reruns are still required before exploratory-produced assets can become main-paper final tables. Second, auto-k remains a bounded extension rather than a settled replacement policy. Its strongest explicit win is currently model-specific, and its broader value lies more in automation and profile reuse than in universal quality dominance. Third, the current paper does not yet convert all behavior-side observations into stronger role-specific budget assignment at runtime.

These limitations point naturally to the next set of extensions. The most immediate is **K/V-asymmetric allocation**, which would turn the observed imbalance between Key-side and Value-side fragility into a role-specific bit-budget policy. The second is **quality-cost Pareto analysis**, which is necessary if the allocator line is to mature from a quality-only narrative into a true budget-allocation method reasoning jointly about latency, memory, and quality. The third is **prompt-adaptive policy selection**, where the current static policy artifact could be complemented by a prompt- or task-conditioned selector.

The point of naming these directions is not to smuggle them into the current evidence. Quite the opposite: it is to keep the paper honest. The current draft leaves these directions as explicit interfaces rather than premature claims.

## 6. Conclusion

This paper argues that KV cache quantization should be organized around **attention behavior** rather than around numerical reconstruction error alone. From that starting point, it presents a **behavior-centric framework** that links calibration and allocation through behavior-derived artifacts and policy decisions. The cleanest validation of this framework is provided by an **INT8 canonical validated instance**, which demonstrates that behavior-grounded calibration can be made auditable and deployable without forcing an unwarranted superiority claim over standard numeric objectives.

On the allocation side, the paper's most stable empirical message is that mixed-precision KV allocation is **regime-dependent**. Model family, scale, and task shape which policies remain competitive, and positional heuristics must be treated as strong baselines rather than as strawmen. Within this landscape, **auto-k** emerges as a meaningful profile-aware extension: it turns behavior-derived profiles into budget suggestions and is most clearly positive on Mistral, but it does not yet justify a universal winner interpretation.

The contribution of the rewritten paper is therefore not a single dominating method. It is a more durable structure for the problem: behavior as the central design object, INT8 as the canonical validation route, regime-dependent allocation as the correct empirical reading, and auto-k as a bounded but valuable extension. This framing is more faithful to the current evidence and more resilient under serious technical review.

## Appendix Notes For Revision

### Main-text figure and table set

1. **Figure 1**: Behavior-Centric Thesis Argument Map
2. **Table 1**: Prior Work Positioning Matrix
3. **Figure 2**: Behavior-Guided Framework Figure
4. **Table 2**: INT8 Claim Boundary Table
5. **Table 3**: Cross-Model Regime Summary Table
6. **Figure 3**: Family Regime Map
7. **Figure 4**: 3B First-Layer Rescue Figure
8. **Table 4**: Compare-Set Governance Table

### Supporting-only or appendix assets

1. Provenance ladder
2. Extend-task triage table
3. Auto-k range proposer schematic
4. Heuristic baseline reposition summary

### Claim-boundary checklist

- Do **not** write `KL > MSE` as an established global result.
- Do **not** write `RoleAlign > KIVI-style`.
- Do **not** write `auto-k is the best policy across all models`.
- Do **not** write any `winner`, `rank #1`, or `gap to best` rhetoric before clean-provenance coverage.
- Keep Mistral as the strongest current positive case for auto-k, not as proof of universality.
- Keep 3B as an anomaly or regime result, not as a general law.
