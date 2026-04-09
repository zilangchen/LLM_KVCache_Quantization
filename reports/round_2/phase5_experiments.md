# Round 2 Phase 5 — Experiment Triggers Report

**Date**: 2026-04-09
**Round**: 2 (thesis-polish-loop)
**Phase**: 5 of 5 (Experiment Triggers)
**Predecessor**: Phase 4 completed across commits `40b5270` (CRITICAL fix) + `809d69b` (Phase 4a) + `f4b0257` (Phase 4b)

---

## §1 Summary

**Result**: **Empty rerun_queue**. Round 2 triggered **zero** new experiments.

Pipeline flow verification: **PASS**. The `state/rerun_queue.json` schema was exercised, the `NEEDS_EXP=true` scan logic was applied to all Phase 2 + Phase 3 findings, and the result is correctly propagated to the state file with explicit `round_2_notes` explaining why the queue is empty.

---

## §2 Why No Experiments?

Round 2 focused on `ch2_related_work.tex` + `ch3_method.tex` (chapter rotation rule: `round mod 4 = 2`). This scope is **text-level**: literature citations, narrative cohesion, novelty defense, terminology consistency, symbol unification, methodological hedging, task-transfer disclosure, and forward-reference audit.

All 20 Phase 2 issues + 13 Phase 3 delta findings fell into one of these categories:

| Category | Count | Example |
|----------|-------|---------|
| New citation insertion | 9 | AhaKV, AsymKV, HeadKV, etc. |
| Narrative / terminology | 6 | "二阶产出" → "结构性产出", ch1 C5 integration |
| Disclaimer / hedging | 5 | inv_tau intuitive argument, σ_eff independence assumption, TPOT boundary |
| Methodological disclosure | 4 | task transfer, WikiText split, v3_quick gap, BA grid |
| Structural refactor | 3 | RoleAlign⊃KIVI containment, ch3 §3.4 rewrite, overview refactor |
| Forward reference / cross-chapter | 3 | ch3 §3.7.3 → ch4, ch4:1349 → ch3 §3.4 |
| AI trace cleanup | 4 | hotspots 1/2/3/4 |
| Symbol sweep | 1 | ch2 h_Q/h_{KV} → H_q/H_{kv} |

**None of these require new experimental data**. They all operate on existing Round 1 + Round 2 Phase 0+1 artifacts (Phase 1 literature digest, Round 1 ablation data, Round 1 paper_tables, v3_quick calibration outputs).

---

## §3 Round 3 Deferred Experimental Candidates

These are **not** Round 2 findings, but they are open questions flagged by Phase 1 (literature_digest §5.5) and Phase 4 (ch3 §3.2 / ch3 §3.4 / ch3 §3.7.3 forward work paragraphs). They are recorded here so Round 3 Phase 0 can read this report and convert them to `NEEDS_EXP=true` candidates if scope permits:

1. **v3_quick 校准产物 RULER/LongBench 对照验证**
   - **Motivation**: Round 1 T7 disclosed that v3_quick Q vector is missing input_layernorm + RoPE processing. INT8 PPL/Needle impact is small (<0.3%), but RULER (13 subtasks) and LongBench (16 real-world tasks) verification is incomplete. Finding 4 (C5) quantitative numbers depend on v3_quick.
   - **Expected command**: `bash scripts/reruns/round3_v3quick_vs_full.sh --calib_file kv_calib_v4_full.json --model_id Qwen/Qwen2.5-1.5B-Instruct --kv_mode int4_ours_asym`
   - **Closure action**: Update ch3 §3.2 calibration version note with comparison table; update Finding 4 PPL numbers if shift > 0.5%.

2. **MQA (H_kv=1) inv_tau 边界验证**
   - **Motivation**: C5 claim is based on $H_{kv} \in \{2, 4, 8\}$. The theoretical prediction ($\sigma_{eff} \propto \sigma/\sqrt{N_{rep}}$) suggests $H_{kv}=1$ (PaLM, original Gemini) should be **the strongest inv_tau beneficiary**. Currently unverified.
   - **Expected command**: `python scripts/eval_ppl.py --model_id google/gemma-2b-mqa --kv_mode int4_ours_asym_ba --calib_file ...`
   - **Closure action**: If MQA model shows inv_tau benefit > H_kv=2 model, strengthen C5 claim in ch1 and ch5. If weak, add MQA as edge case in ch5 limitations.

3. **Correlated noise model for σ_eff**
   - **Motivation**: Phase 3 quantization_theorist identified that `σ_eff ∝ σ/√N_rep` requires independence assumption; in reality, all query heads share the same quantized K tensor. The correlated noise model would give `σ_eff ∝ σ/√(N/(1+(N-1)ρ))`.
   - **Expected command**: analytical/simulation, not a GPU experiment
   - **Closure action**: Paper appendix proof sketch; update ch3 §3.4 + ch4:1349 hedge if closed-form bound is obtained.

4. **Tensor-core NVFP4 comparison with BitDecoding**
   - **Motivation**: ch2 §2.6 + ch3 §3.7.3 now cite BitDecoding as Tensor-core complement to our CUDA-core split-channel. A direct TPOT comparison on identical Blackwell hardware would concretize the "complementary paths" claim.
   - **Expected command**: N/A (requires Blackwell hardware, out of current H20 scope)
   - **Closure action**: Future work in ch5.

5. **MLA (DeepSeek-V2/V3) inv_tau 适用性**
   - **Motivation**: Multi-head Latent Attention reconstructs K from a latent vector. Whether inv_tau framework even applies is an open methodological question.
   - **Expected command**: `python scripts/eval_ppl.py --model_id deepseek-ai/deepseek-v2-lite --kv_mode int4_ours_asym_ba ...`
   - **Closure action**: If applies, add MLA as extension in ch5. If doesn't apply, document as scope limitation.

These are **not** triggered by Round 2. They are recorded as Round 3+ backlog.

---

## §4 State File Updates

- `state/rerun_queue.json`: updated with `round_2_notes` explaining empty queue + Round 3 deferred candidates
- `state/running_experiments.json`: not updated (no new experiments running)

---

## §5 Phase 5 Gate

| Gate item | Status |
|-----------|--------|
| rerun_queue.json schema verified | ✅ (loaded + updated + explicit notes field) |
| Phase 3 NEEDS_EXP scan completed | ✅ (all 33 findings categorized, 0 require experiments) |
| Fail-fast constraint documented | ✅ (command examples in §3 all have explicit --calib_file + --model_id + --kv_mode) |
| Empty queue justified | ✅ (Round 2 scope is ch2/ch3 text-level, no experimental data needed) |
| Round 3 deferred backlog recorded | ✅ (5 candidates in §3) |

**Phase 5 Gate: PASS**

---

## §6 Next Step

Round 2 closing commit will:
1. Update `state/round_counter.json` with `last_completed` timestamp + `total_rounds_completed: 2` + `consecutive_clean_rounds` based on Phase 3 CRITICAL count (all CRIT resolved in Phase 4, so `consecutive_clean_rounds: 1`)
2. Append final iteration.md Timeline entry summarizing Round 2 entire journey
3. Commit all Round 2 reports + state files
4. Exit Round 2 without triggering Round 3 (Round 3 requires user confirmation + chapter rotation moves to `round mod 4 = 3` → ch4)

---

**End of Phase 5 Experiment Triggers Report.**
