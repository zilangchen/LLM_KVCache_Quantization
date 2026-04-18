# Phase 2 Data And Mainline Audit

> Status: `candidate-main audit`, not `final-ready`
>
> Date: `2026-04-19`
>
> Scope:
> - raw-data audit of the currently completed Phase 2.6 waves
> - cross-model auto-k reading
> - 3B anomaly analysis
> - heuristic baseline repositioning
> - extend-task evidence triage
> - theory-support framing for paper closing
>
> This document is a session-level formal audit. It is not a result release page, not a thesis chapter rewrite, and not a replacement for `docs/thesis_upgrade_live_plan.md`.

---

## 0. Executive Summary

### 0.1 One-line verdict

Current evidence is already sufficient to support a defensible `candidate-main` paper line:

> `behavior` is a useful unified analysis and design principle; allocator / auto-k are natural downstream extensions of that framework; the most defensible empirical reading is `family-/scale-/task-dependent regimes`, not universal superiority.

### 0.2 What is already supported

1. `behavior-guided framework` is supported better than `behavior superiority`.
2. `auto-k` is supported as a profile-aware budget proposer, but not as a universal replacement.
3. `3B` provides a genuinely new and theoretically meaningful anomaly: an extreme early-layer bottleneck where `bakv_k1` strongly beats the positional heuristic.
4. `heuristic` is a strong baseline; this strengthens, rather than weakens, the regime-based reading.

### 0.3 What is not yet supported

1. `auto-k is cross-model best`
2. `auto-k is Pareto-superior`
3. `behavior-guided allocation universally beats heuristic / uniform / fixed-k`
4. any `final-ready` claim that treats Phase 2.6 exploratory results as the sole source of final tables

### 0.4 Most important provenance judgment

The audited Phase 2.6 result files are structurally clean, but the remote worktree used to produce them was dirty. Therefore:

- they are good enough for `candidate-main` narrative support and paper restructuring
- they are **not** yet good enough for `final-ready` tables without clean-provenance coverage reruns

---

## 1. Audit Basis

### 1.1 Audited raw assets

This audit used the following remote raw assets from `/root/LLM_KVCache_Quantization`:

- `results/phase2_c2b_llama8b_extended`
- `results/phase2_7b_random_hardening`
- `results/phase2_c3_qwen14b`
- `results/phase2_c4_mistral7b`
- `results/phase2_c4_mistral7b/smoke`
- `results/phase2_batch4_extend_tasks_7b`
- `results/phase2_batch5_extend_tasks_8b`
- `results/phase2_c5_qwen3b`
- `artifacts/allocator/sweep_8b`
- `artifacts/allocator/sweep_14b`
- `artifacts/allocator/sweep_mistral7b`
- `artifacts/allocator/sweep_3b`

The audit also cross-checked earlier local Phase 2 verification assets:

- `results/phase2_c2_local/phase2_verify_all.csv`
- `results/phase2_c2_local/phase2_final_gate.log`
- `results/phase2_diag_local/`

### 1.2 Audit procedure

The session performed the following read-only checks:

1. synced the target result directories and allocator policy JSONs to a local temporary mirror
2. verified expected run counts per wave
3. checked for zero-byte and malformed `csv/json/yaml` files
4. checked `run_id` / `run_name` duplication
5. matched each summary CSV against its `config_snapshot.yaml`, details CSV, profile CSV, and run log
6. reconstructed cross-model policy tables from raw summary CSVs
7. read allocator JSONs to inspect `protected_layers`, `avg_bits`, and `layer_sensitivity`

### 1.3 Provenance note

- all audited Phase 2.6 summary CSV rows carry `git_commit = fa6ab125`
- remote `git rev-parse --short HEAD` reported `fa6ab12`
- remote `git status --short` was clearly dirty at audit time

Therefore the current Phase 2.6 evidence should be treated as:

- `exploratory` at the result-production layer
- `candidate-main` at the narrative / audit layer

---

## 2. Data Asset Audit

### 2.1 Structural completeness

All target waves matched their expected counts.

| Wave | Directory | Expected | Actual | Status |
|---|---|---:|---:|---|
| Wave 1 | `results/phase2_c2b_llama8b_extended` | 30 | 30 | pass |
| Wave 3 | `results/phase2_7b_random_hardening` | 24 | 24 | pass |
| Wave 4 | `results/phase2_c3_qwen14b` | 45 | 45 | pass |
| Wave 5 full | `results/phase2_c4_mistral7b` | 45 | 45 | pass |
| Wave 5 smoke | `results/phase2_c4_mistral7b/smoke` | 6 | 6 | pass |
| Wave 7a | `results/phase2_batch4_extend_tasks_7b` | 36 | 36 | pass |
| Wave 7b | `results/phase2_batch5_extend_tasks_8b` | 40 | 40 | pass |
| Wave 6 | `results/phase2_c5_qwen3b` | 45 | 45 | pass |

Across these 8 directories, the audit read:

- `271` summary CSV rows
- `271` matching details/profile/log bundles
- `70` allocator policy JSONs across four sweeps

### 2.2 File integrity

The audit found:

- `0` zero-byte targeted files
- `0` malformed targeted `csv/json/yaml`
- `0` duplicated `run_id`
- `0` duplicated `run_name`
- `0` missing summary-to-config links

### 2.3 Important caveat: smoke/full mixing

`results/phase2_c4_mistral7b` is safe only if `smoke/` is handled separately.

- top-level full sweep count: `45`
- smoke count: `6`
- recursive count under the whole subtree: `51`

So any recursive `find ... -name 'longbench_task_summary_*.csv'` over `phase2_c4_mistral7b` will overcount by mixing smoke and full. This must not enter paper tables.

### 2.4 Data asset trust tiers

#### can-use-directly

- `results/phase2_c2b_llama8b_extended`
- `results/phase2_c3_qwen14b`
- `results/phase2_c4_mistral7b` top-level full only
- `results/phase2_c5_qwen3b`
- `artifacts/allocator/sweep_8b`
- `artifacts/allocator/sweep_14b`
- `artifacts/allocator/sweep_mistral7b`
- `artifacts/allocator/sweep_3b`

#### can-use-with-caveat

- `results/phase2_7b_random_hardening`
- `results/phase2_batch4_extend_tasks_7b`
- `results/phase2_batch5_extend_tasks_8b`
- `results/phase2_c2_local/phase2_verify_all.csv`
- `results/phase2_diag_local/`

These are useful, but either they are supporting evidence, or they carry interpretation caveats, or they are not the main Phase 2.6 claim path.

#### not-safe-for-main-claim

- `results/phase2_c4_mistral7b/smoke`
- any recursive statistic that mixes Wave 5 full and smoke
- `trec` on current extend-task lines
- `vcsum` on current extend-task lines
- any Phase 2.6 figure/table that is presented as `final-ready` without clean rerun coverage

---

## 3. Mainline Judgment

### 3.1 Strongest currently defensible paper line

The strongest line is:

> `behavior` is the right object to analyze and preserve in KV-cache quantization; the same behavior-derived profile can naturally support calibration, allocation, and automatic budget proposal; empirical results are best understood as family-/scale-/task-dependent regimes rather than as a universal winner story.

### 3.2 Claims that can now be written

1. `behavior` is useful as a unified analysis and design principle.
2. allocator behavior is regime-dependent across family and scale.
3. heuristic is a strong positional baseline, not a strawman.
4. auto-k is a meaningful profile-aware extension with clear empirical value, especially on Mistral.
5. 3B reveals a qualitatively different regime where first-layer rescue matters disproportionately.

### 3.3 Claims that must not be written

1. `behavior-guided allocation universally beats baseline`
2. `auto-k is the cross-model best policy`
3. `auto-k is already the Pareto-optimal allocator`
4. `there exists one fixed k that generalizes across model families`
5. `Phase 2.6 exploratory results are already final-ready`

### 3.4 Claims that need clean-provenance rerun before upgrade

1. any table that directly quotes Phase 2.6 numeric winners in the main paper
2. any comparative claim that uses Wave 1 / 4 / 5 / 6 as final evidence
3. any strong statement about cross-family generalization of auto-k
4. any statement that relies on tight numeric gaps rather than on ordering and regime shape

---

## 4. Auto-K Cross-Model Analysis

### 4.1 Core comparison table

| Model | Best overall | Best auto-k | Gap to best | Best fixed behavior-guided | Best heuristic | Best uniform | Stable reading |
|---|---|---|---:|---|---|---|---|
| 3B | `bakv_k1 = 6.9023` | `bakv_auto_cov80_max = 6.7545` | `-0.1477` | `bakv_k1 = 6.9023` | `heuristic_k3 = 6.7990` | `uniform_int8_k8v8 = 6.8986` | mixed, not best |
| 8B | `bakv_k11 = 9.5214` | `bakv_auto_cov80_max = 9.3543` | `-0.1670` | `bakv_k11 = 9.5214` | `heuristic_k11 = 8.5416` | n/a in Wave 1 | strong extension, not best |
| 14B | `uniform_int4_k4v4 = 7.2345` | `bakv_auto_cov90_max = 7.1501` | `-0.0845` | `bakv_k1 = 7.0583` | `heuristic_k3 = 7.1171` | `uniform_int4_k4v4 = 7.2345` | top-quality tier, not winner |
| Mistral-7B | `bakv_auto_cov80_max = 14.7640` | `bakv_auto_cov80_max = 14.7640` | `0.0000` | `bakv_k5 = 14.2771` | `heuristic_k3 = 14.6036` | `uniform_int8_k8v8 = 14.3784` | strongest auto-k evidence |

### 4.2 The most stable sentence

The most stable description is:

> auto-k is a profile-aware budget proposer with real cross-model support, but explicit wins are still primarily Mistral-specific.

### 4.3 What the raw data actually says

#### 3B

- auto-k is **not** the best overall policy
- auto-k is also **not** better than the best heuristic
- auto-k uses much more average bit budget than `bakv_k1`
- therefore `3B auto-k close second` is too generous as a mainline statement

#### 8B

- `auto_cov80` is the strongest auto-k variant
- it is `+0.8127` above the strongest heuristic in Wave 1
- but still `-0.1670` below `bakv_k11`
- therefore 8B supports `competitive extension`, not `best policy`

#### 14B

- `auto_cov90` is `+0.0917` above the best behavior-guided fixed-k
- it is `+0.0330` above the best heuristic
- but still `-0.0845` below `uniform_int4`
- therefore 14B supports `top-tier quality`, but not universal superiority

#### Mistral-7B

- `auto_cov80` is first overall
- it wins `2/3` tasks and loses only `narrativeqa` to `heuristic_k3`
- it is also better than `uniform_int8_k8v8` while using lower average bits
- this is the cleanest auto-k positive result in the current dataset

### 4.4 Task-level winner pattern

Across the three core tasks:

- `3B`: auto-k wins `0/3`
- `8B`: auto-k wins `0/3`
- `14B`: auto-k wins `1/3`
- `Mistral-7B`: auto-k wins `2/3`

This is why `Mistral-specific winner` is the robust formulation.

### 4.5 Why auto-k is often strong but not universally first

The policy generator selects the smallest protected set reaching a sensitivity coverage target using `k_scale`-derived layer sensitivity.

This gives auto-k two strengths:

1. it avoids hand-picking one brittle fixed `k`
2. it tracks family-specific sensitivity spread better than position heuristics

But it also creates a structural limitation:

1. it optimizes coverage, not marginal quality-per-bit
2. when the profile is extremely sharp, coverage can over-protect too many layers
3. when a model is already robust under low uniform precision, auto-k can spend extra bits without enough return

That is exactly what the current 3B and 14B results show.

---

## 5. 3B Case Study

### 5.1 Core empirical fact

For Qwen-3B:

- `bakv_k1 = 6.9023`
- `heuristic_k1 = 3.4791`
- relative gain = `+98.4%`

Task-level deltas are all positive:

- `gov_report`: `+47.7%`
- `hotpotqa`: `+239.3%`
- `narrativeqa`: `+132.8%`

This is not a mild effect. It is a regime break.

### 5.2 Why `bakv_k1` is special

The 3B sensitivity profile is sharply concentrated:

| Model | Reference policy JSON | Top-1 layer | Top-1 share | Top-5 share | Gini | First-layer rank |
|---|---|---:|---:|---:|---:|---:|
| 3B | `bakv_k1.json` | `0` | `13.53%` | `33.88%` | `0.270` | `1` |
| 8B | `bakv_k11.json` | `29` | `5.79%` | `20.45%` | `0.087` | `32` |
| 14B | `bakv_k1.json` | `30` | `3.88%` | `17.06%` | `0.144` | `9` |
| Mistral-7B | `bakv_auto_cov80_max.json` | `29` | `3.96%` | `18.64%` | `0.076` | `31` |

The key point is not only that 3B is more concentrated. It is that the concentration peak lands exactly on `layer 0`.

### 5.3 Why heuristic k=1 fails catastrophically

The heuristic policy is defined as an equally spaced positional heuristic. For `k=1`, it chooses `num_layers // 2`.

For 3B:

- `bakv_k1` protects `[0]`
- `heuristic_k1` protects `[18]`

This means the heuristic completely misses the dominant sensitivity spike.

### 5.4 Why auto-k does not fully solve 3B

3B auto-k is quality-competitive, but not optimal:

- `bakv_auto_cov80_max = 6.7545`
- it protects `25 / 36` layers
- average bits = `7.125`
- achieved coverage = `80.8%`

This suggests an important mechanism:

> when the profile is dominated by a small number of extremely important layers, a coverage-based allocator can over-spend budget compared with a sharply targeted rescue policy.

### 5.5 Stable theoretical reading

The most defensible explanation is:

1. 3B has a much heavier-tailed layer sensitivity profile than the larger models audited here
2. the dominant spike is at the first layer, not in the usual mid/late region
3. therefore positional heuristics are unusually brittle on 3B
4. behavior-derived targeting is unusually valuable on 3B

### 5.6 What can and cannot be claimed

#### can claim

- 3B exhibits an early-layer bottleneck regime
- first-layer rescue is disproportionately important on 3B
- heuristic can fail badly when its positional prior is misaligned with the actual behavior profile

#### cannot yet claim

- the root cause is definitively `num_key_value_heads`
- the cause is definitively architectural rather than calibration-specific
- the same first-layer regime necessarily extends to all small models

Those are still hypotheses, not established claims.

---

## 6. Heuristic Baseline Repositioning

### 6.1 Heuristic is genuinely strong

The raw data does not support treating heuristic as a weak baseline.

Examples:

- on `14B`, `heuristic_k3 = 7.1171`, only `0.0330` below the best auto-k
- on `Mistral`, `heuristic_k3 = 14.6036`, only `0.1604` below `auto_cov80`
- on `8B` extend tasks, `heuristic_k1` is actually the best average policy over `dureader + lcc`

### 6.2 Why heuristic is often strong

The positional heuristic encodes a real prior:

- many models place substantial sensitivity mass in mid or late layers
- if the profile is broad rather than sharply spiked, evenly spaced protection is already reasonable
- this is why heuristic stays near the front on 14B and Mistral

### 6.3 Why heuristic sometimes fails

Heuristic fails when the real profile is not close to its positional prior.

This happens most clearly on 3B:

- the strongest layer is not central
- the profile is much more concentrated
- missing the first-layer spike is devastating

### 6.4 Paper implication

This strengthens the current mainline, because it supports the statement:

> allocation is a regime-based decision problem, not a trivial contest against a weak baseline.

The paper should therefore say both:

1. heuristic is strong and must be acknowledged as such
2. behavior-derived profiling explains when heuristic is insufficient

---

## 7. Extend-Task Evidence Triage

### 7.1 Signal strength by task

For 7B extend tasks:

- `lcc` range across policies: `9.9555`
- `dureader` range across policies: `8.5334`
- `vcsum` range: `0.0800`
- `trec` range: `0.0000`

For 8B extend tasks:

- `dureader` range across policies: `2.4442`
- `lcc` range across policies: `1.1959`
- `vcsum` range: `0.1667`
- `trec` range: `0.0000`

### 7.2 Evidence tiers

#### primary supporting evidence

- `dureader`

It consistently has real separation and is aligned with the long-context quality question.

#### secondary supporting evidence

- `lcc`

It is informative and non-floor, but currently less central than `dureader`.

#### boundary / disclosure only

- `trec`
- `vcsum`

These should not sit inside the allocator main argument.

### 7.3 Why this matters

The aggregate average over all four extend tasks can be misleading because `trec` and `vcsum` inject almost no allocator information.

For example:

- on `7B`, auto-k looks best over both `all4` and `signal2`
- on `8B`, auto-k is weak on both `all4` and `signal2`

So the real message is not `extend-task confirms auto-k`, but:

> extend-task evidence is heterogeneous, and the only trustworthy allocator signal comes mainly from `dureader`, with `lcc` as secondary support.

---

## 8. Theory Support Framework

This section organizes the most useful theory-facing explanations in a structured form.

### 8.1 Why behavior can serve as a unified analysis principle

#### observation

The allocator policies are generated from calibration-derived `k_scale` profiles, and those profiles meaningfully separate model regimes.

#### mechanism hypothesis

Even when behavior-guided methods do not universally win, the behavior-derived profile still captures where quantization damage is most consequential for downstream decoding.

#### falsifiable implication

If this is false, then:

- behavior-derived sensitivity should not predict useful layer subsets
- heuristic and random policies should be equally good once average bits are matched

#### already-supported evidence

- 3B `bakv_k1` versus `heuristic_k1`
- 8B late-heavy fixed best
- 14B broad high-quality band
- Mistral wide-band auto-k success

#### still-missing evidence

- clean-provenance rerun stability
- explicit quality-cost Pareto comparison
- stronger causal evidence separating K/V role effects from layer-position effects

### 8.2 Why behavior-guided methods still have paper value without universal wins

#### observation

The superiority story failed, but the regime-explanation story remained intact and became sharper with more data.

#### mechanism hypothesis

The contribution is not a single always-best policy. It is the ability to turn calibration artifacts into interpretable allocation decisions across families.

#### falsifiable implication

If this framing is empty, then the framework should not improve explanatory power over plain positional heuristics.

#### already-supported evidence

- heuristic wins in some regimes
- auto-k wins in Mistral but not elsewhere
- 3B exposes a regime where behavior information is critical

### 8.3 Why family-/scale-/task-dependent regimes are likely real

#### observation

Winner identity changes systematically with family and scale, not randomly:

- 3B prefers a sharply targeted first-layer rescue
- 8B prefers a late-heavy fixed policy
- 14B favors a strong low-bit uniform baseline
- Mistral favors a wider coverage-style policy

#### mechanism hypothesis

The underlying sensitivity profiles differ in concentration, location, and spread, which changes the best use of bit budget.

#### falsifiable implication

If regimes are just noise, then profile shape should not line up with winner changes.

#### already-supported evidence

- first-layer rank on 3B is `1`, but `32 / 9 / 31` on 8B / 14B / Mistral
- 3B profile concentration is much sharper than the others

### 8.4 Why auto-k may be more stable than fixed-k but not universal

#### observation

Fixed-k is clearly brittle across families, but coverage-based auto-k is not always first.

#### mechanism hypothesis

Coverage-based selection adapts to profile width, but it still ignores marginal quality-per-bit and runtime cost.

#### falsifiable implication

If a model has an extremely sharp sensitivity spike, a very small fixed rescue can beat coverage-based auto-k.

#### already-supported evidence

- 3B supports exactly this failure mode

### 8.5 Why K/V asymmetric allocation is the natural next step

#### observation

Current allocator decisions still upgrade K and V together at layer level.

#### mechanism hypothesis

If the behavior signal is real, the next natural refinement is not more arbitrary layer heuristics, but disentangling role asymmetry under the same profile-driven framework.

#### already-supported evidence

- the allocator code already computes role-aware K/V sensitivity helpers for L2
- current behavior-guided story already depends on K-side signals more than on pure position

### 8.6 Why Pareto analysis is methodologically critical

#### observation

Many current auto-k wins or near-wins use much higher average bit budgets.

#### mechanism hypothesis

Without quality-cost Pareto analysis, allocator claims remain score comparisons rather than budget-allocation methodology.

#### already-supported evidence

- 3B auto-k loses to `bakv_k1` while spending `+3.0` avg bits
- 14B auto-k beats heuristic slightly, but spends `+3.125` avg bits

### 8.7 Why prompt-adaptive should come after K/V asymmetry and Pareto

#### observation

The current static allocator规律 are not yet fully stabilized in clean provenance.

#### mechanism hypothesis

Dynamic prompt-adaptive control should be layered on top of a stable static allocator story; otherwise it risks re-packaging unstable heuristics as adaptivity.

---

## 9. Writing Recommendations

### 9.1 Introduction

Change the framing from:

- `behavior-guided methods are better than baselines`

to:

- `behavior is a useful unified object for analysis, calibration, and allocation`

### 9.2 Method

Explicitly distinguish:

1. `behavior-aligned calibration`
2. `behavior-guided allocation`
3. `coverage-based auto-k budget proposal`

Do not blur them into a single superiority claim.

### 9.3 Experiments

Reorganize around two layers:

1. `canonical validated instance`
2. `allocator regime study`

Inside allocator results:

- make heuristic strength explicit
- keep auto-k as a strong extension, not the novelty center
- separate `full` from `smoke`
- clearly mark exploratory versus candidate-main evidence

### 9.4 Conclusion

The safest close is:

> the framework is useful, the regimes are real, auto-k is promising, but the current evidence favors conditional regime reading rather than any universal winner law.

### 9.5 Threats / Appendix

Must explicitly include:

- provenance ladder
- smoke/full separation
- low-information extend tasks
- strong-baseline disclosure
- clean-rerun upgrade conditions

### 9.6 Figures worth adding or redrawing

1. cross-model sensitivity concentration / regime map
2. 3B first-layer case study
3. quality versus average bits scatter for 3B / 8B / 14B / Mistral
4. extend-task information-value chart separating `dureader/lcc` from `trec/vcsum`

---

## 10. Minimal Next Actions

### 10.1 If no new experiments are added

The paper can already be written around this line:

- L0: behavior as unified principle
- L1: allocator as regime study
- auto-k as strong extension
- 3B as the most interesting counter-regime

But all Phase 2.6 winner numbers should remain `candidate-main`, not `final-ready`.

### 10.2 If only minimal additional work is allowed

The highest-value next step is **not** to expand tasks.

It is to run clean-provenance reruns on a claim-critical compare set:

- 3B: `bakv_k1`, `heuristic_k1`, `bakv_auto_cov80_max`, `uniform_int8_k8v8`
- 8B: `bakv_k11`, `heuristic_k11`, `bakv_auto_cov80_max`
- 14B: `uniform_int4_k4v4`, `heuristic_k3`, `bakv_auto_cov90_max`
- Mistral-7B: `bakv_auto_cov80_max`, `heuristic_k3`, `uniform_int8_k8v8`

### 10.3 If L2 results arrive later

L2 is most likely to change:

- the strength of the extension story
- the K/V asymmetry explanation
- the Pareto-methodology claim

L2 is **not** likely to justify restoring the old universal-superiority mainline.

---

## 11. Final Claim Ladder

### 11.1 Strongest safe claims

1. `behavior` is useful as a unified analysis and design principle.
2. allocator effectiveness is regime-dependent across family, scale, and task.
3. heuristic is a strong baseline and should be treated as such.
4. auto-k is a meaningful profile-aware extension with strongest current support on Mistral.
5. 3B reveals a sharp early-layer bottleneck regime where behavior-guided rescue is especially valuable.

### 11.2 Exploratory or conditional claims

1. auto-k is a cross-scale strong policy family
2. 14B may indicate that profile-aware proposers become more attractive on broader-band models
3. small-model regimes may be especially sensitive to early-layer rescue

### 11.3 Claims requiring clean rerun before upgrade

1. final numeric winner tables for Phase 2.6
2. tight cross-model ranking comparisons
3. any near-tie interpretation that depends on small numeric gaps

### 11.4 Claims to retire

1. `behavior-guided allocation universally better`
2. `auto-k is already the paper's theoretical center`
3. `one fixed k generalizes across model families`
4. `extend-task 4/4 pass proves allocator generalization`

---

## 12. Bottom Line

Current raw data does not justify a universal-winner paper.

It **does** justify a stronger and more defensible paper:

> a behavior-guided quantization-and-allocation framework paper whose main empirical message is regime structure, not universal superiority, and whose strongest new phenomenon is the 3B early-layer anomaly plus Mistral-specific auto-k success.
