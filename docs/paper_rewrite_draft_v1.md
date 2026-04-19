# Behavior-Guided KV Cache Quantization and Allocation

> Draft status: `candidate-main` rewrite draft, not `final-ready`
>
> Purpose: this is a fresh paper draft in Markdown. It does **not** mirror the legacy LaTeX chapter order or claims.
>
> Citation note: inline references are currently written as named placeholders such as `KIVI`, `KVTuner`, and `KVmix`. They should be mapped back to BibTeX keys during LaTeX migration.

## Alternative Title Candidates

1. **Behavior-Guided KV Cache Quantization and Allocation**
2. **A Behavior-Centric Framework for KV Cache Quantization**
3. **From Behavior-Aligned Calibration to Behavior-Guided Allocation in KV Cache Quantization**

## Abstract

KV cache compression is increasingly necessary for long-context large language model inference, yet its quality loss is not fully explained by numerical reconstruction error alone. In this paper, we argue that **attention behavior** is the more appropriate object to analyze and preserve, and we use it as a unified principle to organize calibration, allocation, and downstream policy design for KV cache quantization. We first instantiate this view in an **INT8 canonical validated instance**, which provides the cleanest end-to-end validation path for behavior-aligned calibration and fused decode execution, while deliberately avoiding the claim that behavior-based calibration universally outperforms standard numeric objectives. We then study mixed-precision KV allocation across multiple model families and scales, and show that the most defensible empirical reading is **regime-dependent**: allocator effectiveness varies with model family, scale, and task, positional heuristics remain strong baselines, and no single fixed protection budget or aggregation rule generalizes across all models. Beyond fixed-budget sweeps, we introduce **auto-k** as a profile-aware budget proposer derived from behavior-guided sensitivity profiles. Auto-k emerges as a strong extension rather than the theory center of the paper: it is competitive across models and most clearly positive on Mistral-7B, while smaller models reveal distinct phenomena such as sharp early-layer bottlenecks. Overall, we present a framework paper whose main message is not universal superiority, but a behavior-centric view of KV cache quantization together with a regime-aware reading of allocation.

## 1. Introduction

Long-context decoding is increasingly constrained by KV cache memory and bandwidth rather than by model weights alone. As sequence length and concurrency rise, KV cache storage grows linearly with context and quickly becomes the dominant runtime bottleneck for decoder-only LLM serving. This makes KV cache compression not a marginal optimization, but a practical requirement for sustaining long-context throughput and multi-request concurrency.

Quantization is therefore a natural response to this bottleneck, but the way it is usually analyzed is incomplete. Most quantization pipelines are organized around numerical proxies such as reconstruction error, clipping loss, or mean squared error. These objectives are useful, but KV cache quantization does not merely perturb stored tensors. It perturbs the Keys and Values that enter attention score computation and softmax normalization, where small perturbations may induce much larger behavioral distortions at generation time. This suggests that the central question is not only how faithfully tensors are reconstructed, but whether the model's **attention behavior** is preserved.

This observation motivates the central position of this paper: **behavior** should be treated as the unified analysis and design principle for KV cache quantization. Under this view, calibration is not only a question of selecting scales and clipping rules, and mixed-precision allocation is not only a question of hand-picking a protection budget. Both should be understood as decisions about how much behavioral distortion a system can tolerate and where that tolerance is most fragile. Framed this way, calibration, allocation, and budget proposal become connected parts of the same pipeline rather than isolated engineering tricks.

We operationalize this view in two layers. The first layer is **behavior-aligned calibration**, which produces deployable calibration artifacts from behavior-sensitive signals and is most cleanly validated in an INT8 setting. The second layer is **behavior-guided allocation**, which uses behavior-derived profiles to decide where higher precision should be preserved under a constrained KV budget. The distinction matters. Calibration determines *how* a given layer is quantized; allocation determines *where* the limited precision budget should be spent. This paper argues that the same behavior-centric lens can organize both layers without collapsing them into a single objective.

The role of INT8 in this paper is intentionally narrow and precise. We use an **INT8 canonical validated instance** as the cleanest path for establishing the framework end to end: calibration, artifact generation, runtime integration, and fused decode execution can all be validated in a setting where the problem is aggressive enough to matter but still controlled enough to attribute. We do **not** use the INT8 result to claim that behavior-based calibration universally dominates MSE. Instead, INT8 serves as the most auditable place to validate the framework itself.

Once the problem shifts from calibration to mixed-precision allocation, the empirical picture becomes more heterogeneous. Across model families, scales, and tasks, allocator behavior is better described by **family-/scale-/task-dependent operating regimes** than by a universal winner story. Some models favor wider protection budgets, some remain highly competitive under strong positional heuristics, and some reveal qualitatively different failure modes. In particular, small models can exhibit sharp early-layer bottlenecks that are almost invisible in larger-family summaries.

This observation changes how we interpret method design. Fixed protection budgets are often too brittle to transfer across models, while positional heuristics are much stronger baselines than a simple behavior-superiority story would suggest. This is precisely why **auto-k** matters in the current paper: not because it already replaces all alternatives, but because it turns behavior-derived profiles into reusable budget suggestions. We present auto-k as a **profile-aware budget proposer** and a strong downstream extension of the framework, not as its theoretical center.

The paper therefore makes four claims. First, it proposes a **behavior-centric framework** for KV cache quantization that unifies calibration and allocation under a common principle. Second, it establishes an **INT8 canonical validated instance** as the cleanest end-to-end validation path for that framework. Third, it argues that allocator outcomes are best read as **regime-dependent**, not universally optimal, and it explicitly repositions heuristic baselines as serious comparators. Fourth, it introduces **auto-k** as a profile-aware extension supported by meaningful but bounded evidence, with its strongest positive results currently concentrated in Mistral and its interpretation further constrained by provenance.

> **Figure placeholder (Figure 1): Behavior-Centric Thesis Argument Map**
>
> Show the paper's logic as `behavior principle -> INT8 canonical validation -> regime-dependent allocation findings -> auto-k extension`, with explicit boundaries saying what is *not* claimed.

The rest of the paper is organized as follows. Section 2 repositions prior work along three design axes: quantization format, calibration signal, and allocation policy. Section 3 presents the behavior-guided framework and clearly separates calibration artifacts from allocation policies. Section 4 reports the empirical findings, emphasizing evidence tiers, stable readings, and explicit claim boundaries. Section 5 discusses limitations and future extensions, including K/V-asymmetric allocation, cost-aware Pareto analysis, and prompt-adaptive policy selection. Section 6 concludes.

## 2. Related Work and Positioning

Existing work on KV cache compression can be better understood by separating three design axes that are often conflated: **quantization format**, **calibration signal**, and **allocation or budget policy**. Some methods primarily innovate on the representation format used for Keys and Values. Others focus on how quantization parameters are chosen. A third group focuses on how precision should vary across layers or roles when the budget is insufficient for uniform treatment. This decomposition is useful because our paper does not introduce a single universally superior format or a single universally superior calibration objective. Instead, it proposes a framework that connects these axes through a shared behavioral viewpoint.

On the format axis, one of the most influential prior works is **KIVI**, which argues for an asymmetric KV design in which Keys are quantized per channel while Values are quantized per token. KIVI is important because it identifies a strong low-bit structural recipe and implements it in a tuning-free, runtime-oriented manner. Our paper does not position itself as having discovered that format independently, nor as having decisively defeated it numerically. Instead, our contribution is to reinterpret part of that design space through a behavior-centered lens: we ask why such asymmetric treatment can make sense from the perspective of attention preservation, and what happens when a behavior-derived offline profile is used to support downstream budget decisions.

On the calibration axis, many pipelines still rely on numeric proxies such as MSE, percentile clipping, or other reconstruction-oriented criteria. These are natural and often effective objectives, especially in milder regimes. However, they do not directly reflect the object that ultimately matters for decoding quality: whether attention computation is distorted in a way that changes generation behavior. The behavior-oriented line of thinking therefore starts from a different question. Instead of asking only how close the quantized tensors remain in Euclidean terms, it asks whether the *functional role* of Keys and Values inside attention is preserved. In our work, this perspective is instantiated as **behavior-aligned calibration**, but we are careful not to claim that it universally dominates numeric objectives in every regime.

The distinction between these two lines is especially important in INT8. In the current evidence base, INT8 supports a strong framework-validation role, but not a broad superiority claim of behavior-based calibration over MSE. This matters for positioning. Our paper should not be read as an attempt to replace all numeric calibration objectives with a single universal behavior loss. It should instead be read as a framework paper that shows why behavior is a meaningful design object and how that object can organize the quantization pipeline.

The third axis, allocation policy, concerns how limited precision budget is distributed. Here the closest prior lines are mixed-precision and layer-wise allocation methods. Recent works such as **KVTuner**, **KVmix**, and related sensitivity-aware allocators recognize that not all layers are equally important and that precision should vary across the network. These methods are highly relevant to our paper. We do not claim to be the first to ask whether KV precision should be allocated unevenly. Our more specific position is that allocation can be driven by **behavior-derived profiles** produced by the same framework that also supports calibration. In that sense, our work is not just another heuristic fixed-k sweep, but an attempt to connect calibration and allocation within a single interpretive structure.

This positioning also clarifies what our paper is **not**. It is not a KIVI replacement paper, because we do not claim broad numerical victory over KIVI-style runtime asymmetric quantization. It is not a pure mixed-precision allocator paper, because the allocator results are intentionally interpreted as regime-dependent rather than as a universal recipe. It is not a paper whose sole novelty is auto-k, because auto-k is framed as a downstream extension of a broader framework. The contribution lies in showing that a behavior-derived view can explain, organize, and constrain all three axes more coherently than a winner-centric narrative would allow.

> **Table placeholder (Table 1): Prior Work Positioning Matrix**
>
> Columns: `Primary axis`, `Representative methods`, `What they solve well`, `What they do not claim`, `Relation to this paper`. Rows should include format-oriented work such as KIVI, calibration-oriented behavior work, and mixed-precision allocation methods such as KVTuner and KVmix.

Our novelty claim is therefore deliberately scoped. We contribute a **behavior-centric framework** that links calibration and allocation through shared profiling logic, an **INT8 canonical validated instance** that grounds this framework in an auditable deployment path, a **regime-based empirical reading** that resists over-generalization, and an **auto-k extension** that makes behavior-guided allocation more automated without claiming universal optimality. This is the fairest way to position the paper against prior work while preserving what is genuinely new.

## 3. A Behavior-Guided Framework for KV Cache Quantization and Allocation

### 3.1 Principle: behavior as the design object

The core principle of this paper is simple: in KV cache quantization, the object that should be analyzed and protected is not merely tensor fidelity, but **attention behavior**. Keys and Values are not passive stored arrays. They are intermediates whose perturbations change attention logits, alter softmax weights, and eventually shift output generation. The framework therefore begins by treating behavioral distortion as the right object for diagnosis and design.

This does not mean that every downstream decision directly optimizes the same behavior loss. Instead, the framework is layered. Some stages directly use behavior-sensitive signals to choose quantization artifacts; later stages consume the artifacts and summaries produced by earlier stages to make budget-allocation decisions. That distinction is what allows us to speak precisely about **behavior-aligned calibration** and **behavior-guided allocation** without pretending that the whole pipeline is a single end-to-end optimizer.

### 3.2 Framework overview: artifacts and decision layers

The framework consists of two offline artifacts and one runtime consumption path. The first artifact is a **calibration artifact**, produced by behavior-aligned calibration. It stores quantization parameters such as scales, clipping choices, group sizes, and, where applicable, auxiliary calibration terms such as `inv_tau`. The second artifact is a **policy artifact**, produced by behavior-guided allocation. It stores layer-wise bit assignments, protected layer indices, and, for auto-k, candidate and recommended budgets.

At runtime, the calibrated quantizer and the allocation policy meet in a mixed-precision KV cache implementation. Calibration tells the system *how* to quantize a given layer or role; allocation tells it *which* layers should remain under higher precision under the given budget. This separation is important for both reproducibility and interpretation. It allows us to keep calibration auditable while also making allocation policies explicit, inspectable, and replaceable.

> **Figure placeholder (Figure 2): Behavior-Guided Framework Figure**
>
> Show two artifact paths: `(1) calibration artifact: scales / group sizes / clipping / inv_tau` and `(2) policy artifact: per-layer bits / protected layers / candidate_ks / recommended_k`, both flowing into mixed-precision runtime routing.

### 3.3 Behavior-aligned calibration

Behavior-aligned calibration operates on sampled attention-side quantities and produces a frozen calibration artifact. In the current implementation, the calibration pipeline collects per-layer query, key, and value samples, searches over quantization hyperparameters such as clipping percentiles and group sizes, and serializes the resulting static scales together with per-head auxiliary terms where needed. The output is a JSON-style artifact that can be consumed later by the runtime without repeating the search.

What matters conceptually is that this calibration stage is still tied to behavior. The search is not organized purely as tensor reconstruction; it is motivated by how quantization changes attention-side behavior. At the same time, the framework is careful about what this means empirically. In particular, the current INT8 evidence does **not** justify the statement that behavior-aligned calibration universally beats MSE. The point of this stage is instead to produce a behavior-grounded, auditable artifact and to establish a clean canonical validation path.

### 3.4 The INT8 canonical validated instance

INT8 is the most controlled setting in which the framework can be validated end to end. At this precision level, the system can demonstrate that a behavior-grounded calibration pipeline, a frozen calibration artifact, and a fused decode runtime can be assembled into one reproducible path. This is why the paper treats INT8 as a **canonical validated instance** rather than as the frontier compression target.

The role of INT8 is therefore mainly methodological. It validates that the framework can produce deployable artifacts and integrate with runtime execution without collapsing into an undefined or purely conceptual proposal. It does **not** serve as the evidence base for a global statement that behavior-based calibration is numerically superior to standard objectives. In the current narrative, INT8 proves that the framework is real; it does not prove that all competing numeric proxies are obsolete.

### 3.5 Behavior-guided allocation

Once the question changes from calibration to mixed-precision allocation, the relevant object also changes. The allocation problem is not “what scale should this group use?” but “where should the limited high-precision budget be spent?” In our framework, that decision is guided by a **behavior-derived layer sensitivity profile** rather than by pure positional heuristics or exhaustive fixed-budget trial-and-error.

The current allocator derives its layer sensitivity from calibration-side artifacts, using per-layer `k_scale` aggregation as the primary proxy. This choice is motivated by the observation that Key-side perturbations often dominate downstream distortion more strongly than Value-side perturbations. The allocator therefore consumes behavior-derived summaries rather than re-optimizing the original behavior loss directly for each policy. This is the reason we describe it as **behavior-guided**, not behavior-aligned: the behavior signal is upstream and causal, but the allocation stage itself is mediated by the profile artifact.

This distinction is essential for correct interpretation. A behavior-guided allocator is not claiming to solve a global KL-optimal allocation problem. It is claiming that behavior-derived information is useful for deciding where precision matters most. That is a weaker but much more defensible statement, and it is the right one for the current evidence.

### 3.6 Auto-k as a profile-aware budget proposer

The fixed-k setting exposed an important weakness in early allocation experiments: a hand-picked protection budget often fails to transfer across models. A protection size that works well on one family may be too conservative or too aggressive on another. This is what motivates **auto-k**. Rather than treating the budget as a manually tuned constant, auto-k uses the layer sensitivity profile to propose a small budget range and a recommended operating point.

In the current implementation, auto-k uses a coverage-style rule over the sorted sensitivity mass. Instead of asking for a globally optimal `k`, it asks how many top-sensitive layers are needed to cover a target fraction of the profile. This produces candidate budgets, a recommended budget, and a concrete selected budget that can be serialized into the policy artifact. Auto-k is therefore best understood as a **profile-aware budget proposer**. It is a meaningful extension because it turns static profiles into reusable decisions, but it is not the theoretical center of the paper and it is not yet justified as a universal replacement for all fixed or heuristic policies.

### 3.7 Runtime routing and extensibility

At runtime, the framework is realized through mixed-precision KV routing. The runtime reads the calibration artifact when static calibration is required and reads the policy artifact when per-layer precision decisions are needed. The mixed KV cache consumes the resulting per-layer bit schedule and applies the corresponding quantization/dequantization path for each layer.

This design is deliberately extensible. Because policy and calibration artifacts are separated, the same runtime interface can later host K/V-asymmetric allocation policies or prompt-adaptive policy selection without changing the conceptual structure of the framework. These extensions remain future-facing in the current paper, but the interface already anticipates them.

## 4. Experiments and Findings

### 4.1 Evidence tiers and experimental stance

Before presenting results, we make the evidence boundary explicit. The current draft is written at the **candidate-main** level. This means the available evidence is sufficient to support a paper restructure, stable empirical readings, and a framework-level narrative. It does **not** mean that all current tables are final-ready, because a clean-provenance rerun is still required before exploratory-produced assets can be promoted to final main-paper compare tables.

This distinction matters because the paper is not trying to win by overly precise ranking language. Our goal in this section is therefore not to declare one globally optimal method, but to identify the most stable readings supported by the current data. These readings concern what the INT8 path validates, which allocator regimes appear stable across model families, where heuristic baselines remain strong, and what role auto-k can currently support.

### 4.2 INT8 canonical validated instance: what it validates and what it does not

The INT8 path is the cleanest end-to-end validation of the framework. It shows that behavior-aligned calibration can produce a deployable artifact, that this artifact can be consumed by the runtime, and that the full path from calibration to fused decode execution is technically coherent. This is why INT8 remains central to the rewritten paper even though it is no longer the most aggressive compression regime.

At the same time, the INT8 section must be read with a strict boundary. It validates the **framework path**, not a broad superiority claim of behavior-based calibration over standard numeric objectives. The current stable reading is therefore: INT8 demonstrates that the behavior-centric framework is real, auditable, and deployable. The unsafe reading would be: INT8 proves that KL-based calibration dominates MSE in general. The draft explicitly rejects the latter.

> **Table placeholder (Table 2): INT8 Claim Boundary Table**
>
> Columns: `Question`, `Evidence in current paper`, `Safe reading`, `Unsafe reading`. This table should make explicit that INT8 validates the framework path but does not establish universal `KL > MSE`.

### 4.3 Regime-dependent allocation is the main empirical message

When the analysis moves from calibration to mixed-precision allocation, the strongest empirical message is not universal superiority but **regime dependence**. Allocation quality depends on model family, model scale, and task mix. This is precisely why a simple global winner story has become unstable as the evidence base expanded. The rewritten paper therefore treats regime identification, rather than single-method victory, as the central empirical contribution of the allocator line.

The 7B setting remains one of the strongest regime findings because it makes the aggregation split visible in a way that is both distinctive and interpretable. Rather than presenting this as a generic allocation law, the paper uses it as evidence that allocator behavior can shift structurally even within the same broad framework. In other words, the 7B result is valuable precisely because it resists collapse into a single fixed rule.

The 8B setting plays a different role. It is the place where the earlier fixed-k story stops looking clean. Wider fixed budgets can still perform well, but the result is no longer easy to summarize as a simple monotonic transfer law. This makes 8B a turning point in the paper's logic: it motivates the move away from hand-picked fixed-k settings and toward profile-aware budget proposal without yet proving that the automatic policy is universally best.

The 14B setting strengthens another message: **heuristic and uniform baselines remain serious competitors**. This is not a weakness to hide. It is part of the paper's best reading. If broad high-quality bands exist in large models, the allocator problem should not be framed as “our method versus trivial baselines,” but as a constrained policy problem where several strong choices coexist and the regime itself becomes the important object of study.

Mistral provides the cleanest positive evidence for auto-k. In the current compare set, it is the model on which auto-k most cleanly reaches the top of the observed range while remaining compatible with the regime-based reading. This does not entitle us to call auto-k a universal winner. What it does justify is a more modest statement: profile-aware budget proposal has moved from a conceptual extension to an empirically supported one, with its strongest explicit support presently concentrated in Mistral.

> **Table placeholder (Table 3): Cross-Model Regime Summary Table**
>
> Suggested columns: `Model`, `What stands out`, `Stable reading`, `Cannot over-interpret`, `Role in paper`. Avoid any winner/rank language.

> **Figure placeholder (Figure 3): Family Regime Map**
>
> A qualitative map showing where 7B, 8B, 14B, Mistral, and 3B fall in terms of dominant allocator behavior, heuristic competitiveness, and budget-band width.

### 4.4 Heuristic is a strong baseline, not a strawman

One of the most important corrections in the rewritten paper is the treatment of positional heuristics. Earlier versions implicitly risked casting heuristic allocation as something behavior-guided policies should trivially dominate. The current evidence does not support that reading. In several settings, heuristic policies remain highly competitive, and in some tasks they can even define the effective quality ceiling of the current compare set.

This strengthens the paper rather than weakening it. Once heuristic is treated as a serious baseline, the empirical message shifts away from “our allocator wins” and toward “allocator quality itself is regime-dependent.” This also makes the emergence of auto-k more meaningful: auto-k is valuable not because it defeats a weak baseline, but because it offers an automated, profile-aware alternative in a landscape where strong hand-designed heuristics already exist.

### 4.5 Auto-k is a strong extension, not the theory center

Auto-k appears in this paper because fixed-k sweeps are increasingly brittle and difficult to transfer across families. Its purpose is to turn behavior-guided sensitivity profiles into actionable budget proposals. In that sense, auto-k is a natural downstream method once the paper accepts that allocation is a profile-sensitive policy problem rather than a one-shot globally tuned constant.

The stable reading of the current evidence is that auto-k is a **strong extension**. It is competitive across models, clearly positive on Mistral, and sufficiently strong to justify inclusion in the main story. The unsafe reading would be that auto-k is already the universal replacement for fixed-k, heuristic, and uniform policies. The data do not support that stronger statement, and the paper does not make it.

### 4.6 The 3B anomaly: early-layer bottleneck and first-layer rescue

The 3B setting reveals a qualitatively different regime and should be written as such. The main phenomenon is not that auto-k performs well. The main phenomenon is that the model exhibits a sharp **early-layer bottleneck**, to the extent that first-layer rescue becomes disproportionately important. In this setting, policies that protect the wrong positional region can fail badly, while a behavior-guided choice that prioritizes the earliest layer can recover quality in a way that is structurally more revealing than a generic cross-model comparison.

This makes 3B one of the most valuable results in the new paper. It demonstrates that allocator behavior is not only family-dependent in a smooth sense, but can also cross into qualitatively different operating regimes. The correct interpretation, however, remains local. The 3B anomaly should be written as a model-specific regime and a theoretically interesting exception, not as a general small-model law.

> **Figure placeholder (Figure 4): 3B First-Layer Rescue Figure**
>
> Show the contrast between first-layer protection and heuristic mid-layer protection, together with the interpretation that 3B exhibits a heavy early-layer bottleneck.

### 4.7 Provenance and evidence governance

The current paper line is intentionally disciplined about provenance. The available data are strong enough to support a `candidate-main` paper narrative, but they were produced under exploratory conditions at the result-production layer. For that reason, the paper uses them to support ordering, regime shape, anomaly interpretation, and structural reading, while explicitly refusing to elevate them to final main-table status before clean-provenance coverage.

This is not a side note; it is part of the contribution discipline. By separating exploratory-produced evidence from clean-produced evidence, the paper avoids the common failure mode in which a structurally correct narrative is undermined by overconfident numeric table rhetoric. The strongest current message is already available without violating that boundary.

> **Table placeholder (Table 4): Compare-Set Governance Table**
>
> Columns: `Asset`, `Allowed role in current paper`, `Not allowed`, `Evidence tier`, `Promotion path`. This table should explicitly keep smoke runs, low-information tasks, and recursive mixed assets out of the main claim path.

## 5. Discussion, Limitations, and Future Work

The rewritten paper should be explicit about what it has established and what it has not. It has established that **behavior** is a useful unified analysis and design principle for KV cache quantization. It has established that the INT8 path provides a clean canonical validation route for this framework. It has also established that allocator results are best interpreted through **regime-dependent** readings rather than universal laws. These are nontrivial claims, and they are already enough to justify the new structure of the paper.

At the same time, several limitations remain. First, the present draft is still a **candidate-main** narrative and not a final-ready result release. Clean-provenance reruns are still required before exploratory-produced assets can become main-paper final tables. Second, auto-k remains an extension rather than a settled replacement policy. Its strongest explicit win is currently model-specific, and its broader value lies more in automation and profile reuse than in universal quality dominance. Third, the current paper does not yet convert all behavior-side observations into stronger role-specific budget assignments at runtime.

These limitations point naturally to the next set of extensions. The most immediate is **K/V-asymmetric allocation**, which would take the already observed imbalance between Key-side and Value-side fragility and translate it into role-specific bit-budget assignment. The second is **quality-cost Pareto analysis**, which is required if the allocator line is to mature from a quality-only narrative into a true budget-allocation method that reasons jointly about latency, memory, and quality. The third is **prompt-adaptive policy selection**, where the current static policy artifact could be replaced or complemented by a prompt- or task-conditioned selector.

The point of naming these directions is not to smuggle them into the current results. Quite the opposite: it is to keep the present paper honest. The current draft leaves these directions as explicit interfaces rather than as premature claims, which is consistent with the framework-first logic of the rewrite.

## 6. Conclusion

This paper argues that KV cache quantization should be organized around **attention behavior** rather than around numerical reconstruction error alone. From that starting point, we present a **behavior-centric framework** that links calibration and allocation through behavior-derived artifacts and policy decisions. The cleanest validation of this framework is provided by an **INT8 canonical validated instance**, which demonstrates that behavior-grounded calibration can be made auditable and deployable without forcing an unwarranted superiority claim over standard numeric objectives.

On the allocation side, the paper's most stable empirical message is that mixed-precision KV allocation is **regime-dependent**. Model family, scale, and task shape which policies remain competitive, and positional heuristics must be treated as strong baselines rather than as strawmen. Within this landscape, **auto-k** emerges as a meaningful profile-aware extension: it turns behavior-derived profiles into budget suggestions and is most clearly positive on Mistral, but it does not yet justify a universal winner interpretation.

The contribution of the rewritten paper is therefore not a single dominating method. It is a more durable structure for the problem: behavior as the central design object, INT8 as the canonical validation route, regime-dependent allocation as the correct empirical reading, and auto-k as a bounded but valuable extension. This framing is both more faithful to the current evidence and more resilient under serious technical review.

## Draft Figure and Table Inventory

### Main text

1. **Figure 1**: Behavior-Centric Thesis Argument Map
2. **Table 1**: Prior Work Positioning Matrix
3. **Figure 2**: Behavior-Guided Framework Figure
4. **Table 2**: INT8 Claim Boundary Table
5. **Table 3**: Cross-Model Regime Summary Table
6. **Figure 3**: Family Regime Map
7. **Figure 4**: 3B First-Layer Rescue Figure
8. **Table 4**: Compare-Set Governance Table

### Appendix or supporting-only

1. Provenance ladder
2. Extend-task triage table
3. Auto-k range proposer schematic
4. Heuristic baseline reposition summary

## Draft Claim Boundary Checklist

- Do **not** write `KL > MSE` as an established global result.
- Do **not** write `RoleAlign > KIVI-style`.
- Do **not** write `auto-k is the best policy across all models`.
- Do **not** write any `winner`, `rank #1`, or `gap to best` rhetoric before clean-provenance coverage.
- Keep Mistral as the strongest current positive case for auto-k, not as proof of universality.
- Keep 3B as an anomaly/regime result, not as a general law.
