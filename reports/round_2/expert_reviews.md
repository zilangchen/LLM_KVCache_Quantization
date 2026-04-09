# Round 2 Phase 3 — Expert Reviews Summary

**Date**: 2026-04-09
**Round**: 2 (thesis-polish-loop)
**Review mode**: delta review on `reports/round_2/paper_review.md` (Phase 2 produced 542-line full diagnosis)
**Reviewers**: 6 expert sub-agents spawned in parallel (general-purpose subagent_type)

---

## §1 Verdict Matrix

| Reviewer | Verdict | Key Delta |
|----------|---------|-----------|
| quantization_theorist | **CONCERN** | 1 UPGRADE (MAJOR→CRITICAL on inv_tau disclaimer) + 2 UPGRADE MAJOR + **2 NEW MAJOR** (RoleAlign⊃KIVI containment, σ_eff independence gap) |
| systems_efficiency | **PASS** (conditional) | 1 DOWNGRADE (FP8 academic citation MAJOR→MINOR) + 2 UPGRADE MAJOR + **3 NEW MAJOR** (§3.7 forward ref, kernel count reconciliation, TPOT batch boundary) |
| nlp_evaluation | **CONCERN** | **3 NEW MAJOR** (task transfer assumption, WikiText data contamination, Needle scoring / seed disclosure) |
| statistical_methods | **CONCERN** | 1 UPGRADE (BA percentile grid MINOR→MAJOR, reproducibility blocker) + **1 NEW MAJOR** (effect size vs significance ch3/ch4 inconsistency) |
| academic_writing | **CONCERN** | 4 hotspot verdicts: HS1 CONFIRM+upgrade, **HS2 REJECT** (T3 rewrite narrative rift + terminology drift), HS3 DOWNGRADE (run-on not AI trace), HS4 narrow (only L6-8) |
| narrative_logic | **CONCERN** | 1 UPGRADE (ch3 "可选增强" residual) + ch1 C5 integration gap + **1 NEW MAJOR** (ch1 RQ2 architectural anchor missing) + 2 post-hoc defense gaps |

**Overall**: 5 CONCERN + 1 conditional PASS. **No REJECT at document level**. Review-specific REJECT limited to HS2 paragraph rewrite (addressed in Phase 4a commit 809d69b).

---

## §2 Cross-Reviewer Consensus (≥3 reviewers)

### Consensus 1: ch3 §3.4 `σ_eff` / intuitive argument disclaimer
**Reviewers**: quantization_theorist (CRITICAL upgrade), nlp_evaluation (CONFIRM MAJOR), statistical_methods (NEW MAJOR effect size), narrative_logic (post-hoc defense gap)
**→ Phase 4 resolution**: ch3 §3.4 methodological note + independence assumption paragraph (commit 809d69b) + ch4:1349 hedge extend (commit f4b0257)

### Consensus 2: BA percentile grid disclosure
**Reviewers**: quantization_theorist (UPGRADE MAJOR), statistical_methods (UPGRADE MAJOR, reproducibility blocker)
**→ Phase 4 resolution**: ch3 §3.6.2 explicit grid $\{99.0,\,99.5,\,99.9,\,99.95,\,99.99,\,100.0\}$ + |36| Cartesian product + subsection label `subsec:ch3-ba-percentile` (commit 809d69b)

### Consensus 3: ch2 novelty defense (C5 anchor)
**Reviewers**: narrative_logic (P0 "To the best of our knowledge"), Phase 1 literature_digest (AhaKV / AsymKV P0)
**→ Phase 4 resolution**: ch2 §2.5.x "最相近先行工作" paragraph with AhaKV + Softmax-Not-Enough credit+differentiate + "据我们所知, 本文是首个系统报告..." anchor (commit 809d69b)

### Consensus 4: ch3 T9 cleanup residual (pre-existing)
**Reviewers**: academic_writing (terminology drift), narrative_logic (C5 narrative anchor risk)
**→ Phase 4 resolution**: pre-emptively fixed by commit 40b5270 (CRITICAL fix before Phase 3 reviewer deployment)

---

## §3 Single-Reviewer Unique Discoveries (NEW MAJOR)

| Discovery | Reviewer | Impact | Phase 4 commit |
|-----------|----------|--------|----------------|
| **RoleAlign ⊃ KIVI strict containment** | quantization_theorist | C2 principled basis (not hyperparameter sweep) | 809d69b §3.6.2 |
| **σ_eff ∝ σ/√N_rep independence assumption gap** | quantization_theorist | Post-hoc defense boundary | 809d69b ch3 §3.4 + f4b0257 ch4:1349 |
| **Calibration → evaluation task transfer assumption** | nlp_evaluation | EMNLP reviewer attack surface | f4b0257 ch3 §3.2 |
| **WikiText-103 → WikiText-2 data contamination** | nlp_evaluation | Methodology transparency | f4b0257 ch3 §3.2 |
| **§3.7 split-channel validation forward reference** | systems_efficiency | Testability chain | f4b0257 ch3 §3.7.3 |
| **TPOT batch=1 boundary disclosure** | systems_efficiency | Scope honesty | f4b0257 ch4:409 footnote |
| **Effect size vs significance ch3/ch4 inconsistency** | statistical_methods | Statistical framework coherence | 809d69b ch3 §3.4 methodological note |
| **Terminology drift "二阶产出" vs "结构性产出"** | academic_writing | C5 narrative coherence | 809d69b unified to "结构性产出" |
| **ch1 RQ2 architectural anchor missing** | narrative_logic | C5 flows from RQ2 naturally | 809d69b ch1 L130 扩写 |

---

## §4 Key Downgrades (reduced Phase 4 workload)

| Original | Downgrade | Reviewer rationale |
|----------|-----------|---------------------|
| FP8 academic citations needed (Phase 2 MAJOR) | MINOR | systems_efficiency: systems reference (vLLM docs) sufficient, FP8 KV is primarily deployment not academic |
| ch3:622-628 BA percentile bridge AI trace (Phase 2 MEDIUM) | run-on sentence (not AI trace) | academic_writing: length problem, not template problem |
| ch3:6-23 overview (Phase 2 MEDIUM full paragraph) | L6-8 only | academic_writing: only first 3 lines have issues, L9-23 acceptable |

---

## §5 Phase 4 Action Items Executed

### Phase 4a commit `809d69b` (5 files, 263+/37-)

1. ch3 §3.4 inv_tau opening rewrite (AI trace + narrative rift + terminology unification)
2. ch3 §3.4 methodological note paragraph (effect size on deterministic PPL)
3. ch3 §3.4 independence assumption paragraph (σ_eff hedge)
4. ch3 §3.6.2 BA percentile grid explicit disclosure + RoleAlign⊃KIVI containment
5. ch3 §3.6.3 KIVI null case footer
6. ch1 RQ2 expansion (τ⁻¹ × H_kv architectural forward reference)
7. ch1 Contribution 5 rewrite (structural product + causal bridge + hedge)
8. ch1 L196-197 terminology sync
9. ch2 KIVI scope disclaimer
10. ch2 KVQuant Pre-RoPE sentence
11. ch2 AsymKV + PolarQuant + AQUA-KV paragraph
12. ch2 Outlier Tokens Tracing + HeadKV + ChunkKV
13. ch2 §2.5.x AhaKV + Softmax-Not-Enough + "to the best of our knowledge" anchor
14. ch2 §2.6 BitDecoding Tensor-core paragraph
15. ch2 FP8 concrete hooks (vLLM v0.4+ / TensorRT-LLM / Blackwell NVFP4)
16. references.bib 8 new entries

### Phase 4b commit `f4b0257` (4 files, 73+/12-)

17. ch3 §3.2 task transfer assumption paragraph
18. ch3 §3.2 WikiText-103 vs WikiText-2 disclosure
19. ch3 §3.2 v3_quick RULER/LongBench validation gap honesty
20. ch3 §3.7.3 split-channel forward reference + Tensor-core relationship
21. ch3 §3.1 overview L6-8 refactor (drop "承担双重使命" + split long sentence)
22. ch2 symbol consistency sweep (h_Q → H_q, h_{KV} → H_{kv})
23. ch4 L409 TPOT footnote (batch=1 boundary disclosure)
24. ch4:1349 hedge extend (intuitive argument → heuristic under independence assumption)

### Pre-Phase-4 preparation commit `40b5270`

0. ch3 §3.1/§3.2 T9 residual "可选/候选增强" CRITICAL fix (before Phase 3 reviewer deployment)

---

## §6 Compilation Validation

| Phase | PDF pages | undefined refs | undefined citations |
|-------|-----------|----------------|----------------------|
| Baseline | 110 | 0 | 0 |
| After 40b5270 (CRITICAL fix) | 110 | 0 | 0 |
| After 809d69b (Phase 4a) | 113 | 0 | 0 |
| After f4b0257 (Phase 4b) | **115** | 0 | 0 |

Growth: **+5 pages** across all Phase 4 additions (Phase 1 citations + novelty defense + task transfer + hedging + RoleAlign⊃KIVI disclosure + TPOT footnote).

---

## §7 Phase 4 Coverage Statistics

| Phase 2 Severity | Count | Resolved in Phase 4 |
|-------------------|-------|---------------------|
| CRITICAL | 1 | **1/1** (pre-fixed 40b5270) |
| MAJOR | 8 | **8/8** |
| MINOR | 7 | **7/7** |
| NIT | 4 | 3/4 (1 low-priority deferred) |
| Phase 3 consensus | 4 | **4/4** |
| Phase 3 NEW MAJOR | 9 | **9/9** |

**Total issue resolution**: 32/33 (97%).

---

## §8 Deferred / Round 3 Candidates

- NIT polish: minor commit message style (1 item, deferred)
- Formal proof of `σ_eff ∝ σ/√N_rep` with correlated-noise model (future work, explicitly flagged in ch3 §3.4 + ch4:1349)
- Full re-calibration of v3_quick on RULER/LongBench (flagged in ch3 §3.2)
- Tensor-core NVFP4 Triton kernel (BitDecoding comparison as future work, ch3 §3.7.3)
- MQA (H_kv=1) / MLA (DeepSeek) / sub-2-bit regime extensions (literature_digest §5.5)

---

**End of Phase 3 Expert Reviews Summary.**
