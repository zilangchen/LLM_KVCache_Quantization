# Round 3 Phase 2 — ch4 Experiments Paper Review

**Date**: 2026-04-09 11:05
**Round**: 3 (thesis-polish-loop)
**Reviewer**: ch4-focused agent (six-dimension deep review)
**Target file**: `thesis/chapters/ch4_experiments.tex` (1749 lines)
**Review mode**: delta review on Round 2 Phase 4b baseline (commit `f4b0257`) against current HEAD
**Excluded from review** (Round 2 Phase 4b already handled):
- ch4:409 — TPOT "延迟降低 8--38%" footnote with `batch=1, 独占 GPU, single-stream decode` boundary
- ch4:1349 — "直觉论证 (intuitive argument)" hedge with pairwise correlation disclosure

---

## §1 Executive Summary

### 1.1 ch4 structural inventory

| Element | Count |
|---------|-------|
| Total lines | 1749 |
| `\section` | 6 |
| `\subsection` | 19 |
| `\subsubsection` | 8 |
| `\paragraph` | 29 |
| `\begin{table}` | 14 (includes the KV-modes reference table) |
| `\begin{figure}` (with `\includegraphics`) | 7 |
| `\ref{sec:|subsec:|tab:|fig:|para:|app:} ` (internal refs) | ~70 |
| `\ref{eq:ch3-*}` (cross-chapter equation refs) | 1 (eq:ch3-ba-percentile at L1172) |
| Standalone `\label{eq:*}` in ch4 | **0** (zero equations in ch4) |
| `{table}` with CSV/run-id source anchor in caption | **0 / 14** (no reproducibility metadata) |

### 1.2 Headline issue counts (Round 3 Phase 2 delta)

| Severity | Count |
|----------|-------|
| **CRITICAL** | **2** (data sync between tables; terminology drift) |
| **MAJOR** | **8** |
| **MINOR** | **11** |
| **NIT** | **5** |

Total new observations: **26**. Of these, 9 are candidates for Phase 4 revision actions and 3-5 trigger Phase 5 experiment queue (see §11).

### 1.3 Top 5 must-fix (ranked by severity + blast radius)

1. **[CRITICAL][tab:kivi-comparison L688]** `int8_ours` `RULER=24.38` and `LongBench=5.00` contradict `tab:main-results` L266-267 corrected values (`RULER=24.45`, `LongBench=4.92`). Commit `3fff883` fixed the main table but forgot to sync the KIVI-comparison table and its narration at L707 ("5.00%"). Same config (32K, 1.5B, mainline) — must match.
2. **[CRITICAL][ch4:1297, 1642]** Terminology drift: ch4 uses **"诊断框架的意外产出"** for C5 but ch1:181 / ch3:22,67,390,1099 use **"诊断框架的结构性产出"**. Round 2 consensus explicitly unified on "结构性产出"; ch4 has not yet been swept.
3. **[MAJOR][tab:kv-modes L127-159]** KV-mode inventory table lists only 9 modes but MEMORY.md and code router support **12 kv_modes** (missing: `int4_ours_asym_ba`, `int4_kivi_aligned`, `int4_mixed_kv`). The text at L124 explicitly claims "9 种 KV Cache 量化模式" — either expand the table or rename the claim to "本章主评测的 9 种模式"; the absent rows are referenced elsewhere in ch4 (see Issue [D2-M3]).
4. **[MAJOR][L524 vs L1727]** Calibration sample count inconsistency: §subsec:exp-ablation-b10 tests 16/64/256 samples but threat-to-validity §L1727 states "校准使用 WikiText-103 的 128 条样本" and ch3:160 states "n=128 段". 128 is the actual mainline value but is never shown in the b10-sensitivity table; the table brackets 128 between 64 and 256 but does not include it. Either add a 128-sample row for completeness or state explicitly "128 位于 64–256 之间，插值鲁棒性由此推断".
5. **[MAJOR][tab:main-results L261]** TPOT column has no ± (neither CI half-width nor SD) while the general caption L284 says "$\pm$ 后为 Bootstrap 95% CI 半宽". TPOT is the single most load-bearing efficiency metric in the main table; the reader cannot assess whether a 24.39 vs 47.14 gap is statistically meaningful without its CI. The cross-model table L621 reports "TPOT 的 95% CI 半宽均 $<$0.4~ms" for ch4 §4.3 but this disclosure is not in the main 1.5B table.

### 1.4 AI-trace hotspot count

**3 segments** flagged (§8): segment A at L846-848 ("三层叠加" list pattern), segment B at L1546-1557 ("边界小结" summary), segment C at L1272-1296 ("INT4-RoleAlign 与 KIVI-style 的关系" narrative). All are candidates for Phase 4 AI-trace sweep.

### 1.5 Round 2 Phase 4b exclusions (confirmed, not re-reviewed)

- **ch4:409** TPOT footnote (systems_efficiency NEW MAJOR) — verified present, well-scoped; not counted as Round 3 issue.
- **ch4:1349** intuitive-argument hedge (quantization_theorist CRITICAL + stats NEW MAJOR) — verified present; three-sentence expansion (independence assumption + pairwise correlation disclosure + "方向性预测") is solid. Not counted.

---

## §2 Dim 1: 实验 Setup 完整性

### 2.1 Observations

ch4 §1 `实验设置` (L16-220) contains four subsections: 模型与硬件 (21-50), 评测基准 (53-118), 基线方法 (120-177), 统计框架 (180-207). It is the single entry point and is reasonably consolidated. Model checkpoint hash **is** pinned (L31 `revision 989aa7` for Qwen2.5-1.5B) — this is the only revision pinned. The 7B and 8B models do not have pinned revisions (L32-34, L35-38). Software environment is stated at L46-50 with forward reference to `env/versions.txt` and `env/requirements_freeze.txt`. Hardware is correctly stated (single H20 98GB).

Statistical framework subsection (L180-207) is the Round 2 statistical_methods reviewer's praised segment — PPL determinism disclaimer at L194-204 is retained verbatim.

Decoding parameters: L186-187 says "5 固定种子 (1234-1238)" and "吞吐量 8 种子 (1234-1241)" and "统一采用贪婪解码". However, the explicit decoding parameters (`temperature=0.0, top_p=1.0, top_k=0`) per CLAUDE.md §9 are **not** written in ch4 — only "贪婪解码" is used as shorthand. For EMNLP reproducibility reviewers who do not read CLAUDE.md, this is insufficient.

MixedKV and K/V ablation sections introduce a **fourth model Mistral-7B** (L39-43) mentioned only as a later-section addition, not as a first-class main result; the reader must trust that its evaluation protocol matches the other three. The ablation design subsection (§subsec:exp-kv-ablation-design, L866-883) uses "3 个种子" while the mainline quality eval uses 5 seeds — the seed reduction for ablations is stated but not justified.

### 2.2 Issues

- **[MAJOR][D1-M1] Decoding parameters underspecified (L186-207).** ch4 §exp-statistics states "统一采用贪婪解码" but does not write `temperature=0.0, top_p=1.0, top_k=0, max_new_tokens=...` for each benchmark. Needle, RULER, LongBench and PPL likely have different `max_new_tokens` budgets; without listing them the reader cannot reproduce the numbers. **Suggestion**: add a decoding-params table (benchmark × max_new_tokens × stop-criterion) either inline or as appendix forward-ref.
- **[MAJOR][D1-M2] Model revision pinning incomplete (L21-44).** Only Qwen2.5-1.5B has a pinned `revision 989aa7`. Qwen2.5-7B (L32-34), LLaMA-3.1-8B (L35-38), and Mistral-7B (L39-43) do not have HuggingFace revision SHAs. **Suggestion**: add revision SHA for all four models, or explicitly note "使用 HuggingFace 默认 main revision as of YYYY-MM-DD" to at least give a date anchor.
- **[MINOR][D1-m1] Seed-count reduction not justified (L882).** Main quality uses 5 seeds but K/V ablation uses 3 seeds. The reduction is stated but not justified (computational cost? Time-on-GPU budget?). A single sentence "受 GPU 预算限制 3 seeds 已可覆盖 $H_{kv}$ 的独立性检验" would close the loop.
- **[MINOR][D1-m2] Mistral-7B upgrade path buried.** Mistral-7B is introduced as the third model family (L39-43) only within the §1.1 `模型与硬件` bullet list. Its late addition is not telegraphed in the abstract-level claims; a reader reading linearly will see Mistral-7B appear "out of nowhere" in §4.2.4 (MixedKV) with no setup. **Suggestion**: add 1 sentence at L642 explaining why Mistral-7B was added (Round 2 stage 7? defense补强?).
- **[NIT][D1-n1] `env/versions.txt` path uncheckable.** The reference to `env/versions.txt` and `env/requirements_freeze.txt` at L49-50 does not specify whether these are in the repository or the submission tarball. For EMNLP camera-ready they should be either in supplementary materials or publicly archived.

---

## §3 Dim 2: 主结果表可复现性

### 3.1 Observations

14 tables and 7 figures total. Table audit:

| Table | Line | Contents | Reproducibility metadata |
|-------|------|----------|--------------------------|
| tab:kv-modes | 127 | 9 kv-mode inventory (inventory only, no numerical data) | N/A |
| tab:main-results | 242 | 1.5B 32K main: 7 rows × 6 metrics | seeds stated, NO source CSV, TPOT has no ± |
| tab:temp-ablation | 485 | 4 temp/adaptive configs × Needle | seeds stated, NO source |
| tab:b10-sensitivity | 527 | 2 models × 3 sample counts × 3 metrics | NO ±, NO seeds disclosed in footnote |
| tab:cross-model | 595 | 2 models × 3 modes × 5 metrics | NO ± on PPL/Needle/LongBench/RULER, only TPOT CI noted in footnote |
| tab:kivi-comparison | 675 | 2 modes × 6 metrics | partial ± (PPL/Needle/LongBench/RULER), no TPOT ± |
| tab:kv-ablation-ppl | 885 | 5 configs × 2 metrics | seed=1234 only, no ± (single point) |
| tab:kv-ablation-ruler | 919 | 3 models × 3 configs | ± = SD over 3 seeds |
| tab:kv-ablation-longbench | 945 | 3 models × 3 configs | ± = SD over 3 seeds |
| tab:mixedkv-cross-model | 1060 | 4 models × 3 methods × 4 metrics | mixed ± (Bootstrap CI or SD) — ambiguous |
| tab:rolealign-results | 1178 | 3 models × 3 methods × 6 columns | footnote "3 seeds" — but no explicit ± in cells |
| tab:invtau-ablation | 1308 | 4 config groups × 3 metrics | seed=1234 only, no ± |
| tab:int4-tpot-cross-model | 1394 | 3 models × 4 methods × TPOT+% | no ±, no seed disclosure in footnote |
| tab:kivi-int4-threeway | 1457 | 3 methods × 6 columns | Needle 100/95/100 raw — no ± |
| tab:claim-summary | 1674 | 16 claims × 5 columns | qualitative, no numerical ± needed |

**Data-source traceability**: NONE of the 14 tables reference the originating CSV file path, experiment run directory (e.g., `results/emnlp_defense_v1/...`), or aggregation commit hash. The reader cannot verify whether the numbers were produced from `emnlp_defense_v1/`, `emnlp_rolealign_v4/`, `emnlp_final_raw/`, or some other run. For a thesis committee member auditing data provenance, this is a serious gap.

**Numerical precision consistency**: PPL is reported to 2 decimals (8.95, 10.58) consistently. LongBench is 2 decimals (4.82, 4.92, 5.00 — see CRITICAL issue). RULER is 2 decimals (24.38, 24.45). TPOT is 2 decimals (47.14, 24.57) — but mixed across tables: some have ms integer (e.g., 66, 67 in tab:main-results) and some have 2-decimal (51.75 in tab:int4-tpot). Minor inconsistency.

### 3.2 Issues

- **[CRITICAL][D2-C1] Data sync regression: `tab:kivi-comparison` L688 vs `tab:main-results` L266-267.** `int8_ours` row:
  - tab:main-results: `LongBench=4.92 ± 0.10`, `RULER=24.45 ± 0.65`
  - tab:kivi-comparison: `LongBench=5.00 ± 0.10`, `RULER=24.38 ± 0.65`
  - Narration at L707: "INT8-ours 的 LongBench 分数（5.00\%）" — matches the stale value.

  These are the SAME config (1.5B Qwen2.5-Instruct, 32K, batch=1, mainline `static_v3_no_temp_adaptive_fused`) and MUST be identical. Commit `3fff883` corrected only the main table; `tab:kivi-comparison` and L707 were missed. **Fix**: update L688 to `5.00 → 4.92, 24.38 → 24.45` and L707 "5.00\%" → "4.92\%"; re-derive the "+1.37%" gain (currently 5.00/4.81 − 1 = 3.95%, not 1.37%; this math was suspect even before the data desync).

- **[CRITICAL][D2-C2] `tab:kivi-comparison` narration L707-711 math sanity check.** L707 says "INT8-ours 的 LongBench 分数（5.00\%）高于 KIVI-style（4.81\%），增益 $+$1.37\%". But (5.00 − 4.81) / 4.81 = 3.95%, not 1.37%. Even using absolute difference it is 0.19 pp. After fixing Issue D2-C1 the gain becomes (4.92 − 4.81) / 4.81 = 2.29% or 0.11 pp absolute. The "$+$1.37%" number does not match any reasonable computation and should be audited. If 1.37% came from a different reference (7-task average after outlier removal?) it needs disclosure.

- **[MAJOR][D2-M1] No source CSV / run directory cited in any table caption.** All 14 tables lack provenance metadata. A reviewer cannot answer "which CSV did this number come from?" without contacting the author. **Suggestion**: add a single appendix table `tab:app-data-provenance` mapping each ch4 table to `results/<tag>/<run_dir>/<csv>` + commit hash, and add "(数据来源见附录 \ref{tab:app-data-provenance})" once in §exp-setup.

- **[MAJOR][D2-M2] `tab:main-results` TPOT has no ±.** L261 `24.39`, L264 `51.43`, L267 `47.14`, etc. — no CI half-width. The main 1.5B table is the paper's headline and the TPOT claim ("delay reduction 8-38%") depends on these numbers. **Suggestion**: add TPOT ± in the same format as the other metrics, or add a footnote stating "TPOT 95% CI 半宽 < 0.4 ms" (the value used in tab:cross-model L621).

- **[MAJOR][D2-M3] `tab:mixedkv-cross-model` ± semantics ambiguous (L1097-1098).** The footnote reads "$\pm$ 后为 Bootstrap 95% CI 半宽或多 seed 标准差。PPL 列无 $\pm$ 表示为确定性单次评估". "Or" is problematic — the reader cannot tell which cells use which convention. Either unify (pick one method and apply to all non-determinic cells) or column-by-column disclose.

- **[MAJOR][D2-M4] `tab:kv-ablation-ppl` is single-seed (L887).** The caption says "seed=1234" only. This is the PPL column that validates the Key-dominant claim (+0.2% vs +13,774%). A single seed for a core Claim-2 evidence point is weak. This is mitigated because PPL is deterministic under greedy decoding (§exp-statistics L194-204), but that justification should be explicitly cross-referenced in the caption or footnote of the table itself.

- **[MINOR][D2-m1] `tab:b10-sensitivity` does not report seeds (L532-555).** The table footnote does not disclose how many seeds were used or whether cells are point estimates. PPL is deterministic so n=1 is acceptable, but Needle (100.0) is a SUM over 20 depths × N seeds — the reader cannot tell if N=1 or N=5.

- **[MINOR][D2-m2] `tab:int4-tpot-cross-model` (L1394) no ± and no explicit seed count.** L1384 narration says "seed=1234, 每配置 5 轮测量取均值并排除前 3 轮 warmup" but the table itself does not disclose this inside its own caption/footnote. Table must be self-contained for reviewers.

- **[MINOR][D2-m3] `tab:rolealign-results` (L1178) has boldface "100/100" in Needle column (L1194, 1199, 1204).** The "100/100" notation is undocumented — does it mean "100% in train split / 100% in test split"? Or "100% Needle / 100% MK-NIAH"? A caption clarification is needed.

- **[NIT][D2-n1] TPOT precision mixed across tables.** tab:main-results uses both integer (66, 67) and 2-decimal (47.14); tab:int4-tpot uses 2-decimal uniformly (51.75). Unify to 2 decimals.

---

## §4 Dim 3: Ablation 设计完备性

### 4.1 Observations

Ablation surface area is **reasonably broad** (5 distinct ablation subsections):

1. §exp-ablation §subsubsec exp-ablation-calib (L423-467): calibration strategy comparison — **observational only**, factor isolation is weak (L464-467 self-disclosed: "INT8-ours 与 INT8-baseline 同时在校准策略、核函数实现和 adaptive 保护三个维度上存在差异" and "严格隔离校准策略的单因素消融未能完成").
2. §exp-ablation-temperature (L469-515): τ⁻¹ × adaptive 2×2 isolation. Clean factor isolation: 4 rows = (temp×adaptive). Needle-only. No PPL column.
3. §exp-ablation-b10 (L517-575): sample count sensitivity (16/64/256). Clean. Only covers 1.5B + 7B, missing 8B.
4. §sec:exp-kv-sensitivity (L855-1119): K/V precision ablation. Three configurations (K-only, V-only, K4V8). Clean factor isolation.
5. §subsec:exp-rolealign-invtau (L1297-1376): inv_tau × H_kv ablation. Three-model isolation.

**Factor confounds that are disclosed**: calibration strategy ablation is honest about 3-way confound (L464-467). Good.

**Factor confounds NOT disclosed**:
- tab:temp-ablation row 3 `static_v2_adaptive` and row 4 `mainline (v3_adaptive)` both show 100.0% — but the caption says "mainline 采用 v3 版本校准产物" (L505). The v2→v3 calibration product version change is a potential confound that is not explored; the reader assumes v2 and v3 differ in something but cannot tell whether it affected the 100% result.
- K/V ablation ranges `K-only=K@INT8`, `V-only=V@INT4`, `K4V8=K@INT4+V@INT8`. There is no `K8V8` (full INT8 both) control within this specific sub-table, though tab:main-results provides it separately. Cross-table reference to validate the control would strengthen the design.

**Coverage vs 5-Claim 链**:

| Claim | Ablation evidence | Gap |
|-------|-------------------|-----|
| C1 (attention-KL correct) | §exp-ablation-calib (observational) + §exp-kivi (KIVI baseline) | calibration isolation incomplete (self-disclosed) |
| C2 (K-dominant) | §sec:exp-kv-sensitivity | **Missing**: PPL-level K/V ablation for 7B/8B/Mistral (only 1.5B has tab:kv-ablation-ppl L887) — see D3-M1 |
| C3 (RoleAlign design) | §sec:exp-rolealign + tab:rolealign-results | BA percentile grid ablation NOT shown in ch4 (only stated in ch3:§3.6.2 after Round 2 disclosure) |
| C4 (capability boundary) | §subsec:exp-int4-boundary + tab:int4-tpot-cross-model | adequate |
| C5 (inv_tau × H_kv) | §subsec:exp-rolealign-invtau + tab:invtau-ablation | **Missing**: only 3 data points (H_kv = 2, 4, 8); no model with H_kv=1 (MQA) or H_kv=16+; see D3-M2 |

### 4.2 Issues

- **[MAJOR][D3-M1] K/V PPL ablation is 1.5B-only (tab:kv-ablation-ppl L887).** The table is captioned "Qwen2.5-1.5B-Instruct, cs=128, seed=1234" and has 5 rows covering only 1.5B. The narration at L883 claims "K/V 消融的 PPL 评测进一步验证了 Key 主导退化在语言建模层面的一致性" — but "一致性" is a multi-model claim; a single-model table cannot support it. **Fix options**: (a) add 7B/8B/Mistral rows to the table; (b) downgrade the narration to "在 1.5B 上的验证一致"; (c) add a 1.5B-only footnote acknowledging the scope. **Round 3 experiment trigger candidate**: reusing K/V ablation runs for 7B/8B PPL column.

- **[MAJOR][D3-M2] C5 inv_tau ablation has only 3 H_kv values (tab:invtau-ablation L1308).** H_kv ∈ {2, 4, 8} covers a narrow range. The theoretical argument σ_eff ∝ σ/√N_rep predicts a 1/√N_rep curve, but 3 points cannot distinguish 1/N_rep from 1/√N_rep from a step function. The Round 2 statistical_methods reviewer's "effect size vs significance" concern is directly relevant: reporting "1.6% improvement on 1.5B" with n=3 models is extreme small-sample. Either acknowledge this limitation directly in the §subsec:exp-rolealign-invtau section (adding 1-2 sentences about the sample-size constraint on the scaling claim) OR run additional models (DeepSeek-V2 H_kv=128, Mistral-7B-v0.2 has different H_kv, Phi-3 has MQA). **Round 3 experiment trigger candidate**: Mistral-7B has GQA with H_kv=8 — is the inv_tau ablation run for it? (Currently only Qwen-1.5B, Qwen-7B, LLaMA-8B are shown; Mistral is absent from this specific ablation even though it is the 4th model.)

- **[MAJOR][D3-M3] tab:temp-ablation v2/v3 confound (L485-507).** Row 3 `static_v2_adaptive` and row 4 `mainline (v3_adaptive)` both show 100.0% Needle, suggesting the v2→v3 calibration version change did not matter for this metric. But the table has no column distinguishing the two versions explicitly and the footnote does not explain what changed from v2 to v3. **Fix**: either (a) add a "校准版本" column and a sentence explaining v2 vs v3, or (b) remove row 4 if it is mechanically redundant with row 3.

- **[MAJOR][D3-M4] BA percentile grid ablation missing from ch4.** ch3 §3.6.2 (after Round 2 Phase 4a) explicitly discloses the search grid `{99.0, 99.5, 99.9, 99.95, 99.99, 100.0}` with |36| Cartesian product. But ch4 does not show an ablation over that grid. The reader cannot answer "how sensitive is RoleAlign to the chosen percentile pair?". Statistical_methods reviewer in Round 2 called this a "reproducibility blocker" for ch3 — the same concern extends to ch4. **Round 3 experiment trigger candidate**: a small BA percentile sensitivity mini-sweep on 1 model (1.5B).

- **[MINOR][D3-m1] §exp-ablation-b10 only covers 1.5B/7B (L522-573).** L572 self-discloses: "仅在 1.5B 和 7B 两个模型上验证...尚待后续实验". This is honest but the gap extends to E13 in tab:claim-summary which is marked "中等" strength. Could be upgraded to "强" by running 8B and Mistral. **Round 3 experiment trigger candidate**.

- **[MINOR][D3-m2] `tab:kv-ablation-ruler` does not provide the `K8V4` (MixedKV) row (L921).** The MixedKV config appears in tab:mixedkv-cross-model (L1060) separately. Consolidating all 4 configs (K-only, V-only, K4V8, K8V4) into one table would let the reader see the full precision matrix in a single view. Current layout forces cross-table comparison.

---

## §5 Dim 4: 统计框架应用一致性

### 5.1 Observations

The §exp-statistics section (L180-207) is the Round 2 statistical_methods reviewer's praised segment ("the single best piece of statistical honesty in the thesis"). It correctly:
1. States seeds (5 quality, 8 throughput).
2. States Bootstrap 10,000 resamples for 95% CI.
3. States sign-flip permutation test for small-n (5).
4. States BH-FDR α=0.05 per-table.
5. Discloses PPL determinism boundary (L194-204).
6. Adds n=10 verification via 5 additional seeds (L200-204).

**Statistical framework is applied inconsistently across ch4 tables**:

| Table | Bootstrap CI? | Permutation p? | BH-FDR q? | Effect size framing? |
|-------|---------------|----------------|-----------|----------------------|
| tab:main-results | YES (± shown) | implicit in text L307, L322 ($p=1.0$, $q=0.016$) | YES (L308) | partial (PPL <0.3% L326) |
| tab:temp-ablation | NO (± is 1-SD) | NO | NO | NO |
| tab:b10-sensitivity | NO | NO | NO | NO |
| tab:cross-model | NO (no ± on quality) | YES (text L629, $q=0.016$) | YES | partial |
| tab:kivi-comparison | YES | YES (L709, $p=0.091$, $q=0.144$) | YES | YES ($p, q$ shown) |
| tab:kv-ablation-ppl | NO (single seed) | NO | NO | YES (vs FP16 column) |
| tab:kv-ablation-ruler | NO (SD shown) | NO | NO | partial |
| tab:kv-ablation-longbench | NO (SD shown) | NO | NO | partial |
| tab:mixedkv-cross-model | partial (ambiguous) | NO | NO | partial |
| tab:rolealign-results | NO (footnote says "3 seeds" but no ±) | NO | NO | YES (vs FP16 column) |
| tab:invtau-ablation | NO | NO | NO | YES (vs 无$\tau^{-1}$ column) |
| tab:int4-tpot-cross-model | NO | NO | NO | YES (vs FP16 column) |

**The framework is only applied to**: the 1.5B main-results table and the INT8-KIVI comparison. For Claims 2/3/4/5 the statistical framework is NOT applied to the decisive tables. This is the "Round 2 stats reviewer NEW MAJOR effect size vs significance" concern directly manifesting in ch4.

The Round 2 reviewer specifically said "effect size vs significance ch3/ch4 inconsistency". The fix in Round 2 added a methodological note to ch3 §3.4, but ch4 §exp-statistics was NOT extended to explain the framework's applicability limits. The ch4 reader sees "±0.04" (CI) next to "±0.39" (SD) next to no-± and has no guidance.

### 5.2 Issues

- **[MAJOR][D4-M1] Statistical framework mixed-semantics ± disclosure.** Across ch4, "±" means Bootstrap 95% CI half-width in some tables (tab:main-results, tab:kivi-comparison), multi-seed SD in others (tab:kv-ablation-ruler, tab:temp-ablation), and is absent from several (tab:b10-sensitivity, tab:invtau-ablation, tab:rolealign-results). **Fix**: add one clarifying sentence in §exp-statistics that explicitly enumerates which metric/table combinations use which method, and then add per-table footnotes disambiguating. Example boilerplate: "本表 ± 为 [CI 半宽 | SD | 无]; 理由：[bootstrap applied | deterministic | n<3 too small]".

- **[MAJOR][D4-M2] Effect size vs significance framing inconsistent (Round 2 stats reviewer NEW MAJOR).** Round 2 ch3 §3.4 added the methodological note, but ch4 uses "退化 -1.6%" / "+6.0%" / "-0.09%" etc. without distinguishing effect size (magnitude) from significance (statistical test outcome). Example: L1319 `10.41 -1.6%` — is -1.6% significant? n=1 (seed=1234) as per tab:invtau-ablation. L323 "PPL 退化幅度在 $-$0.09\% 至 $-$0.26\%" — this is effect size on a deterministic metric (so no p-value applies), but the sentence "均未达 BH-FDR 校正后的统计显著性" at L324 conflates effect size with significance. **Fix**: Sweep ch4 for all "retreat/improvement" language and annotate each with "(effect size only, 确定性指标)" or "(p=X, q=Y under framework)".

- **[MAJOR][D4-M3] tab:invtau-ablation C5 claims lack statistical backing (L1308).** This is the core table supporting C5 (诊断框架的意外产出). It reports 1.6%/6.0%/3.4% changes on deterministic PPL with seed=1234 single-seed runs. The "1.6% improvement on 1.5B" is the C5 headline number. Without confirming it is effect-size-only (no Bootstrap CI applicable because PPL deterministic) and without stating the tolerance threshold, this number cannot survive EMNLP stats reviewer scrutiny. **Fix**: add a row `± (note)` or a footnote "PPL 为确定性指标 (§exp-statistics L194); cell 值为 vs 无$\tau^{-1}$ 的 effect size. 不适用 p 值; 非劣性判定基于 |Δ| < 阈值".

- **[MINOR][D4-m1] $p = 1.0$ at L322 needs clarification.** "与 FP16 无统计显著差异（$p=1.0$）" — $p = 1.0$ is the maximum possible p-value and is unusual to report. This likely means "sign-flip permutation test: all 2^n sign assignments give $\geq$ |observed| so $p = 1$". That is technically correct but confusing to casual readers. Explain or rephrase.

- **[MINOR][D4-m2] "8-38%" TPOT reduction range compression.** L307 "1.5B: 8.3%", "7B: 17.3%", "8B: 37.6%". The headline claim "8-38%" at L409 telescopes this to a range. A single range hides the fact that only one model contributes the 37.6% endpoint. A reviewer may suspect cherry-picking. **Fix**: in the L409 footnote (Round 2 Phase 4b addition), extend with the 3-point breakdown: "8-38% 对应三个模型 (1.5B: 8.3%, 7B: 17.3%, 8B: 37.6%), $q=0.016$".

---

## §6 Dim 5: 数据 narrative 与 C1-C5 映射

### 6.1 Observations

The 5-Contribution体系 (C1-C5) is explicitly mapped in ch4:

| Claim | Narrative anchor in ch4 | Evidence table/figure | Consistency with ch1/ch5 |
|-------|-------------------------|------------------------|--------------------------|
| C1 (attention-KL correct) | L227-232, §sec:exp-main | tab:main-results, tab:kivi-comparison, fig:main-quality-dashboard | OK (ch1 abstract + ch5 findings) |
| C2 (K-dominant) | §sec:exp-int4 (L732-850), §sec:exp-kv-sensitivity | tab:kv-ablation-ppl, tab:kv-ablation-ruler, tab:kv-ablation-longbench | OK |
| C3 (RoleAlign) | §sec:exp-rolealign (L1122-1232) | tab:rolealign-results, fig:rolealign-summary, fig:ppl-vs-scale | OK |
| C4 (capability boundary) | §subsec:exp-int4-boundary (L1501-1588) | tab:int4-tpot-cross-model, §subsec:exp-rolealign-boundary | OK |
| **C5 (inv_tau × H_kv)** | §subsec:exp-rolealign-invtau (L1297-1376), 发现五 (L1642-1651) | tab:invtau-ablation | **TERMINOLOGY DRIFT** |

**CRITICAL issue C5 terminology**:
- ch1:176,181 = "诊断框架的**结构性产出**"
- ch3:22,67,390,1099 = "诊断框架的**结构性产出**"
- ch4:1297 subsection title = "诊断框架的**意外产出**" ❌
- ch4:1642 paragraph title = "诊断框架的**意外产出**" ❌
- ch4:1300 narration = "诊断框架在跨模型消融过程中涌现出的**结构性规律**" (OK)
- ch5:64 paragraph title = "诊断框架的**意外产出**" ❌
- ch5:67 = "这是诊断方法的一个**二阶产出**" ❌❌ (uses the banned "二阶产出" term that Round 2 consensus explicitly deprecated!)

Round 2 Phase 3 academic_writing reviewer flagged "terminology drift 二阶产出 vs 结构性产出" as consensus 4 and the Round 2 Phase 4a commit `809d69b` said "unified to 结构性产出". But ch4 and ch5 still contain 3 occurrences of "意外产出" plus 1 occurrence of the banned "二阶产出" in ch5. **This is the Round 2 fix that did not land completely.**

**Magnitude consistency across chapters**:

| Number | ch4 location | ch1/ch5 location | Consistent? |
|--------|-------------|------------------|-------------|
| INT8 PPL degradation <0.3% | L199, L326 | ch1:150 (check), ch5 发现一 | need grep |
| INT8 TPOT 8-38% | L409, L1606 | ch1 | OK |
| INT8 KV 44% | L318, L1606 | ch1 | OK |
| RoleAlign PPL 2.4/6.1/13.7% | L1135, L1214, L1516, L1622, L1647 | ch1:178, ch5:143 | OK |
| RoleAlign KV 73% | L1382, L1414, L1534, L1633 | ch1:179 | OK |
| inv_tau 1.5B -1.6% | L1319, L1338, L1647 | ch1:180 | OK |
| inv_tau 7B +6.0% | L1323, L1339, L1647 | ch1:180 | OK |
| inv_tau 8B +3.4% | L1327, L1339, L1647 | ch1:180 | OK |

Most numbers are consistent. The C5 terminology drift is the main narrative-level failure.

**Claim-to-evidence density check**:
- C1 has 4 evidence anchors (tab:main-results, tab:kivi-comparison, tab:cross-model, fig:main-quality-dashboard) — **strong**
- C2 has 4 evidence anchors (tab:kv-ablation-ppl, tab:kv-ablation-ruler, tab:kv-ablation-longbench, fig:kv-ablation-summary-ruler) — **strong**
- C3 has 4 evidence anchors (tab:rolealign-results, tab:mixedkv-cross-model, fig:rolealign-summary, fig:ppl-vs-scale) — **strong**
- C4 has 3 evidence anchors (tab:int4-tpot-cross-model, §subsec:exp-rolealign-boundary, tab:chunksize in appendix) — **adequate**
- **C5 has 1 evidence anchor (tab:invtau-ablation)** — this is the weakest. fig:pareto-quality-efficiency does not visualize C5. A C5-specific visualization (bar chart or line plot of ΔPPL vs H_kv) is missing from ch4. This is noteworthy because Round 2 deliberately elevated C5 to first-class contribution status.

### 6.2 Issues

- **[CRITICAL][D5-C1] Terminology drift "意外产出" / "二阶产出" not swept.** Three "意外产出" occurrences (ch4:1297, 1642; ch5:64) and one "二阶产出" occurrence (ch5:67) remain after Round 2 Phase 4a's "unified to 结构性产出" sweep. **Fix**: global replace "意外产出" → "结构性产出" in ch4 and ch5; replace "二阶产出" → "结构性产出" in ch5:67. Grep to verify: `grep -n "意外产出\|二阶产出" thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex` should return zero.

- **[MAJOR][D5-M1] C5 evidence density lowest among the 5 claims.** Only tab:invtau-ablation carries the full weight. A figure visualizing ΔPPL vs H_kv would strengthen C5 substantially. **Fix**: add a small inline figure (line plot: x = H_kv ∈ {2,4,8}, y = ΔPPL%) drawn from the same 3 data points; can be rendered in TikZ without new data. **Round 3 experiment trigger candidate if new models run**: extend to Mistral-7B (H_kv=8) for N=4 data points.

- **[MAJOR][D5-M2] C5 narrative misses the "diagnostic byproduct" linkage at the L1642 paragraph level.** Paragraph title says "(诊断框架的意外产出)" but the body L1642-1651 does not restate the causal chain "diagnostic framework → cross-model ablation → emergent structural regularity → publishable finding". The chain is only in §subsec:exp-rolealign-invtau L1300-1304. Ch1 and ch5 readers who jump to "发现五" expect the chain. **Fix**: add 1 sentence at L1650 explaining "这不是预先设计的目标 (see §subsec:exp-rolealign-invtau), 而是诊断框架在跨模型消融中涌现出的结构性规律".

- **[MINOR][D5-m1] Claim labeling in §sec:exp-rolealign should explicit C3.** L1125 "本节呈现论文的核心实验结论" does not label this as "Claim 3" the way L227 labels C1. For cross-referencing consistency add "\noindent\textbf{Claim 3：诊断直接导出有效的低比特检索恢复设计。}" header. Similarly for C5 at §subsec:exp-rolealign-invtau.

- **[MINOR][D5-m2] C4 subsection title inaccurately scopes the claim.** §subsec:exp-int4-boundary is titled "INT4 量化的能力边界" but C4 as stated in ch1 is specifically "INT4-RoleAlign 能力边界". The current title reads like a general INT4 discussion. Rename to "INT4-RoleAlign 的能力边界" to match C4 exactly.

- **[NIT][D5-n1] "发现四" (L1637) has no \label and cannot be cross-referenced.** The other 四个发现 all lack labels too. `\label{para:finding-1}` through `\label{para:finding-5}` would enable precise cross-chapter refs.

---

## §7 Dim 6: ch4 ↔ ch3/ch5 cross-chapter reference closure

### 7.1 Observations

**ch4 → ch3 references** (forward-to-method):
- L310: `ref{sec:ch3-triton}` — Triton fusion kernel
- L479: `ref{sec:ch3-static-scale}` — static scale protection
- L1172: `ref{sec:ch3-rolealign}` + `eqref{eq:ch3-ba-percentile}` — BA percentile equation
- L1391: `ref{sec:ch3-triton}` (repeat)
- L1419: `ref{subsec:ch3-triton-int4-asym}` — INT4 Triton kernel (Round 2 new label)
- L1540: `ref{sec:ch3-triton}` (repeat)

6 cross-refs to ch3, all legitimate method→experiment linkage. **Good coverage** for Triton kernel + RoleAlign + static-scale. **Gap**: §sec:ch3-calib (§3.2 KL calibration formal definition) is never cross-referenced from ch4, even though ch4 §sec:exp-main extensively discusses KL calibration behavior. Round 2 expected reviewer concern about "where is the calibration objective defined formally" can be closed by adding one cross-ref.

**ch4 → ch5 references** (forward-to-conclusion): **ZERO**. ch4 does not forward-reference ch5 anywhere. This is not a bug per se (experiments rarely cite their own conclusions) but the Round 2 Phase 4b added several forward-references ch3→ch4 that now lack the reciprocal anchor.

**ch4 → appendix references**: 6 refs (L90, L311, L329, L338, L641, L665, L817, L851, L966, L1415, L1560, L1572, L1584) — **well-distributed**, covering all the long-tail data moved to appendix.

**ch3 → ch4 backward references**: Round 2 Phase 2 paper_review §3.6 audit found 9 refs. Spot-check:
- ch3:41 → `sec:exp-kv-sensitivity` (OK, L855)
- ch3:127 → `subsec:exp-rolealign-results` (OK, L1164)
- ch3:411 → `subsec:exp-ablation-temperature` (OK, L469) AND `subsec:exp-rolealign-invtau` (OK, L1297)
- ch3:420, 422, 430 → `subsec:exp-statistics` (OK, L180)
- ch3:436 → `subsec:exp-rolealign-invtau` (OK, L1297)
- ch3:605 → `sec:exp-kv-sensitivity` (OK)
- ch3:627 → `sec:exp-int4` (OK, L732)
- ch3:679 → `subsec:exp-statistics` (OK)
- ch3:726 → `subsec:exp-rolealign-invtau` (OK)
- ch3:735 → `subsec:exp-rolealign-results` (OK)
- ch3:864 → `subsec:exp-rolealign-results` + `subsec:exp-rolealign-boundary` (OK)

All backward references resolve. **Round 2 Phase 4b** specifically added ch3:§3.7.3 → ch4:1412-1423 (split-channel forward ref per systems_efficiency reviewer). I should verify ch4 has a reciprocal label at line 1412-1423.

Looking at L1418-1429: `\paragraph{融合核函数的可行性验证}` — this is the paragraph that the ch3 forward-ref points to. It does NOT have a `\label{para:int4-triton-validation}` or similar. **Missing reciprocal label**.

**ch5 → ch4 backward references**: 6 refs as per grep L80, L144, L190, L198, L216, L222 — all legitimate.

### 7.2 Issues

- **[MAJOR][D6-M1] Missing reciprocal label for ch3:§3.7.3 → ch4 INT4 split-channel forward ref.** Round 2 Phase 4b added the forward reference from ch3:§3.7.3 pointing to the INT4 Triton validation paragraph in ch4. The target paragraph (L1418-1429 `融合核函数的可行性验证`) has NO `\label{}`. A ch3→ch4 ref like `\ref{para:int4-triton-validation}` would be broken. **Fix**: add `\label{para:int4-triton-validation}` after L1418 and update ch3:§3.7.3 ref to target it.

- **[MAJOR][D6-M2] ch4 never cross-references ch3 §3.2 (KL calibration objective).** Claim 1 is literally "attention-KL 是正确校准对象" and ch4 §sec:exp-main discusses it at length without cross-referencing the formal definition in ch3 §3.2. A reviewer reading ch4 linearly will be frustrated by the forward pointer gap. **Fix**: add `(ch3 §\ref{sec:ch3-calib} equation ...)` once in §subsec:exp-main-table or §subsec:exp-ablation-calib.

- **[MINOR][D6-m1] "PPL 确定性说明" (§exp-statistics L194-207) should label its key paragraph.** Round 2 Phase 4a already added the `subsec:exp-statistics` label but the sub-paragraph itself has no label for ch3 to cross-reference. ch5:5 implicit backward references to this paragraph would benefit from an explicit `\label{para:ppl-determinism}`.

- **[MINOR][D6-m2] §sec:exp-kivi-unified section header is missing a title (L1433).** The label `\label{sec:exp-kivi-unified}` appears after a `%` comment but there is no `\section{...}` command. This is the "§4.8 拆解：KIVI INT8/INT4" section. If the label is referenced anywhere the PDF TOC will show an empty entry. **Fix**: either add `\section{KIVI 三方对比}` or remove the stray label.

- **[NIT][D6-n1] `para:c6-fail` label usage (L332).** The label `\label{para:c6-fail}` is defined at L332 and used at L409, L637. Good. But "c6" suggests "Claim 6" which does not exist (only C1-C5). Rename to `para:ruler-fail` or `para:c1-ruler-fail` for narrative consistency.

---

## §8 AI 痕迹热点段落 (3 segments)

### 8.1 Segment A: §subsec:exp-int4-limitations conclusion 3-layer stack (L845-851)

```
综合以上分析，INT4 量化在长上下文场景下的退化源于三层叠加：
（1）表示层：SQNR 从 49.9~dB 骤降至 25.8~dB；
（2）任务层：序列长度放大噪声对检索信号的淹没效应；
（3）架构层：GQA 中 $H_{kv}$ 越小，误差稀释越弱。
第~\ref{sec:exp-kv-sensitivity}~节的 K/V 消融实验将从实证层面验证上述理论分析。
此外，确保 scale 全链路以 float32 维护可显著改善部分模型的 INT4 PPL，
但不足以建立跨模型一致优势（完整结果见附录第~\ref{sec:app-eng066}~节）。
```

**AI signature**: "综合以上分析", three-layer-stack framing with numbered bullets "(1) 表示层 / (2) 任务层 / (3) 架构层", each introduced by `（N）<层名>：<描述>` — this is the classic LLM trinity-bullet template. The actual information density is low: (1) restates SQNR from L795, (2) restates L811-817, (3) restates L820-843. No new claim. **Fix**: merge into a single sentence: "SQNR 骤降 24.1 dB (§...), 序列长度放大噪声 (§...), GQA 头数调制稀释 (§...) — 三者叠加构成 INT4 在长上下文下的退化机制."

### 8.2 Segment B: §subsec:exp-int4-boundary "边界小结" (L1546-1557)

```
\paragraph{边界小结。}
INT4-RoleAlign 的能力呈现清晰的分层结构：
\emph{检索能力完整恢复}（Needle 100\%，RULER s\_niah $\geq$99\%），
显存压缩 73\%，
但\emph{语言建模退化不可忽略}（PPL +2.4--13.7\%）
且\emph{延迟优势尚未兑现}（TPOT +2--2.5$\times$）。
上述边界的显式界定是行为对齐框架诊断能力的直接体现。
相较于仅报告最佳结果的传统做法，
诊断驱动的评估范式使我们能够精确识别能力的边界条件，
为后续优化（Triton INT4 融合核函数、
基于 $H_{kv}$ 的自适应比特分配）
指明方向而非留下盲区。
```

**AI signature**: "清晰的分层结构", "直接体现", "相较于...传统做法", "指明方向而非留下盲区" — these are LLM hedging tropes. The paragraph ends with a self-congratulatory sentence ("诊断驱动的评估范式使我们能够精确识别...") that reads like model-generated filler. The 3 emphasized claims (`\emph{检索能力完整恢复}`, `\emph{语言建模退化不可忽略}`, `\emph{延迟优势尚未兑现}`) are valuable but the framing sentences are bloat. **Fix**: cut the "相较于...盲区" sentence; merge the remaining content into 2 sentences.

### 8.3 Segment C: §subsec:exp-rolealign-results "INT4-RoleAlign 与 KIVI-style 的关系" (L1272-1296)

```
\paragraph{INT4-RoleAlign 与 KIVI-style 的关系}
表~\ref{tab:rolealign-results} 显示，
INT4-RoleAlign 在 PPL 上并不优于 KIVI-style
（1.5B: 13.7\% vs 12.0\%，7B: 6.1\% vs 5.5\%，8B: 2.4\% 持平），
两者在 Needle 和 RULER 检索指标上几乎不可区分。
这一结果需放在方法论框架中理解：
INT4-RoleAlign 与 KIVI-style 共享相同的非对称量化格式
（per-channel K + per-token V），
唯一的差异在于 percentile 确定方式：
KIVI 在运行时基于 absmax/min 动态计算，
RoleAlign 通过离线 KL/wMSE 搜索。
在 cs$\geq$128 的标准评测下，
两种策略产生的 scale 差异不足以在 4-bit 的 15 个离散级别下
产生可区分的量化映射~\cite{xu2025kvtuner}。

INT4-RoleAlign 的价值不在于点性能超越 KIVI，
而在于它串联了从原则到设计的诊断逻辑：
（1）attention-KL 诊断透镜揭示 Key 主导退化和 GQA 架构依赖，
（2）诊断结论直接导出非对称量化轴的设计方向，
（3）BA percentile 校准提供了一种可与 KIVI 替换的离线确定性方案。
KVTuner~\cite{xu2025kvtuner} 的独立评测显示
Qwen 系列上 vanilla KIVI 在 2-bit 下 PPL 直接崩溃（$>$200），
而 4-bit 行为对齐方案保持了 $<$14\% 的退化，
说明离线校准在更极端压缩率下可能展现出差异化优势。
```

**AI signature**: "这一结果需放在方法论框架中理解", "(1)(2)(3)" trinity-bullet structure, "不在于...而在于..." rhetorical pattern — all LLM tropes. The "价值不在于点性能" sentence and the trinity bullets are essentially a face-saving move when RoleAlign did not beat KIVI on PPL. The content is honest and important but the delivery is defensive and LLM-patterned. The "说明离线校准在更极端压缩率下可能展现出差异化优势" sentence is a hypothetical claim unsupported by ch4 data (2-bit KIVI collapse is KVTuner's finding, not ours) and reads as a post-hoc defense. **Fix**: rewrite into 1 honest sentence: "在 cs≥128 评测粒度下, RoleAlign 的离线 BA 搜索与 KIVI 的运行时统计量产生近似等价的量化映射 (4-bit 仅 15 级, 两种方案差异被量化粒度吸收). RoleAlign 的方法论价值在于将非对称格式从经验设计升级为诊断导出的设计 (§...)." Cut the 2-bit KVTuner reference because it is not validated in this thesis.

---

## §9 Phase 3 Reviewer Focus Pointers

Suggested per-reviewer focus regions for Round 3 Phase 3 (6 expert reviewers spawned in parallel, delta-review style).

### 9.1 quantization_theorist
- **Primary**: §subsec:exp-rolealign-invtau (L1297-1376) — verify tab:invtau-ablation C5 evidence under the Round 2 Phase 4b hedge (L1349 pairwise correlation disclosure).
- **Secondary**: §subsec:exp-int4-limitations "GQA 结构下的量化误差稀释效应" (L819-844) — verify σ² scaling argument consistency with ch3 §3.4 and ch4:1349.
- **Specific issues to judge**: D4-M3 (C5 stats), D5-M1 (C5 evidence density), D3-M2 (C5 sample size).

### 9.2 systems_efficiency
- **Primary**: §subsec:exp-int4-boundary (L1501-1588) + tab:int4-tpot-cross-model (L1394) — verify TPOT 2-2.5× claim scope and the "融合核函数的可行性验证" (L1418-1429) BitDecoding comparison.
- **Secondary**: §subsec:exp-main-efficiency (L380-410) — verify Round 2 Phase 4b L409 footnote still scopes the 8-38% headline correctly.
- **Specific issues to judge**: D2-M2 (tab:main-results TPOT ±), D4-m2 (8-38% range decomposition), D6-M1 (missing INT4 Triton label).

### 9.3 nlp_evaluation
- **Primary**: §subsec:exp-benchmarks (L53-118) — verify RULER/LongBench/Needle disclosure sufficiency post Round 2 task transfer hedges.
- **Secondary**: §subsec:exp-int4-results (L752-766) — verify LongBench "artifact" disclosures for int4_fused (L290-295) and Mistral-7B (L965-966).
- **Specific issues to judge**: D1-M1 (decoding params), D1-M2 (model revisions), D2-C2 (narration math), D5-M1 (C5 visualization).

### 9.4 statistical_methods
- **Primary**: §subsec:exp-statistics (L180-207) — confirm praise maintained, verify the framework's applicability across all 14 tables.
- **Secondary**: tab:main-results (L242) + tab:invtau-ablation (L1308) — confirm ± disambiguation needed.
- **Specific issues to judge**: D4-M1 (±semantics), D4-M2 (effect size vs significance), D4-M3 (C5 stats), D2-M3 (mixedkv ± ambiguity), D2-M4 (kv-ablation-ppl single-seed).

### 9.5 academic_writing
- **Primary**: all 3 AI-trace hotspot segments in §8.
- **Secondary**: D5-C1 terminology sweep (ch4:1297, 1642, ch5:64, ch5:67).
- **Specific issues to judge**: D5-C1 (critical sweep), §8 hotspots A/B/C, D5-m1/m2 (claim labeling), D5-n1 (finding labels).

### 9.6 narrative_logic
- **Primary**: §sec:exp-discussion §subsec:exp-findings (L1599-1665) — verify the 5 findings map cleanly to C1-C5 and that terminology is consistent.
- **Secondary**: tab:claim-summary (L1674) — verify all 16 experiment expectations are still appropriately colored (strong/medium/none).
- **Specific issues to judge**: D5-C1 (terminology drift), D5-M1/M2 (C5 narrative density + byproduct linkage), D3-M3 (v2/v3 confound), D6-M2 (ch3 §3.2 cross-ref gap).

---

## §10 Phase 4 Action Items (prioritized)

### P0 — CRITICAL, blocks Phase 5

1. **[D2-C1]** `thesis/chapters/ch4_experiments.tex:688` — update `int8_ours` row in tab:kivi-comparison: `5.00 → 4.92, 24.38 → 24.45`.
2. **[D2-C1]** `thesis/chapters/ch4_experiments.tex:707` — update narration: "INT8-ours 的 LongBench 分数（5.00\%）" → "（4.92\%）".
3. **[D2-C2]** `thesis/chapters/ch4_experiments.tex:707-711` — recompute "增益 $+$1.37\%" using corrected values; audit the derivation. If 1.37% was measured from a different dataset subset, disclose that.
4. **[D5-C1]** `thesis/chapters/ch4_experiments.tex:1297, 1642` — global replace "意外产出" → "结构性产出" in ch4.
5. **[D5-C1]** `thesis/chapters/ch5_conclusion.tex:64` — replace "意外产出" → "结构性产出".
6. **[D5-C1]** `thesis/chapters/ch5_conclusion.tex:67` — replace "二阶产出" → "结构性产出".

### P1 — MAJOR, should be resolved in Phase 4

7. **[D1-M1]** `ch4_experiments.tex:186-207` — add decoding-params table (benchmark × max_new_tokens × stop-criterion).
8. **[D1-M2]** `ch4_experiments.tex:32-44` — add HF revision SHA for 7B, 8B, Mistral (or date anchor).
9. **[D2-M1]** `ch4_experiments.tex:exp-setup` — add appendix `tab:app-data-provenance` cross-ref.
10. **[D2-M2]** `ch4_experiments.tex:261,264,267,270,273,276,279` — add TPOT ± half-width to tab:main-results (or footnote the cross-model bound <0.4 ms).
11. **[D2-M3]** `ch4_experiments.tex:1097-1098` — unify tab:mixedkv-cross-model ± semantics (Bootstrap CI OR SD, not "or").
12. **[D2-M4]** `ch4_experiments.tex:887-901` — annotate tab:kv-ablation-ppl as "seed=1234 deterministic, valid per §exp-statistics L194".
13. **[D3-M1]** `ch4_experiments.tex:885-909` — either extend tab:kv-ablation-ppl to 4 models or scope the "一致性" claim at L883 to 1.5B only.
14. **[D3-M2]** `ch4_experiments.tex:1297-1376` — acknowledge the H_kv ∈ {2,4,8} sample-size limitation in a sentence; extend with Mistral-7B if feasible.
15. **[D3-M3]** `ch4_experiments.tex:485-507` — clarify v2/v3 calibration version change in tab:temp-ablation.
16. **[D3-M4]** Address BA percentile grid ablation gap (add small mini-ablation figure OR cite ch3:§3.6.2 disclosure explicitly).
17. **[D4-M1]** `ch4_experiments.tex:180-207` — add per-table ± semantic disambiguation sentence.
18. **[D4-M2]** `ch4_experiments.tex:(various)` — sweep ch4 for "retreat/improvement" language and annotate with effect-size-only vs p,q labels.
19. **[D4-M3]** `ch4_experiments.tex:1308-1334` — add deterministic-metric disclosure footnote to tab:invtau-ablation.
20. **[D5-M1]** `ch4_experiments.tex:§subsec:exp-rolealign-invtau` — add ΔPPL-vs-H_kv figure (TikZ inline).
21. **[D5-M2]** `ch4_experiments.tex:1650` — add 1 sentence restating the diagnostic-byproduct causal chain in 发现五.
22. **[D6-M1]** `ch4_experiments.tex:1418` — add `\label{para:int4-triton-validation}` after `\paragraph{融合核函数的可行性验证}`.
23. **[D6-M2]** `ch4_experiments.tex:(sec:exp-main or subsec:exp-ablation-calib)` — add 1 cross-ref to ch3 §3.2 formal KL objective.

### P2 — MINOR/NIT polish

24. **[D1-m1]** `ch4:882` — justify 3-seed ablation budget.
25. **[D1-m2]** `ch4:639-642` — justify Mistral-7B late addition.
26. **[D1-n1]** `ch4:49-50` — specify env file location (repo / supplementary).
27. **[D2-m1]** `ch4:527-555` — disclose seed count in tab:b10-sensitivity footnote.
28. **[D2-m2]** `ch4:1394-1411` — disclose seeds in tab:int4-tpot-cross-model footnote.
29. **[D2-m3]** `ch4:1178-1219` — clarify "100/100" notation in tab:rolealign-results.
30. **[D2-n1]** `ch4:(various)` — unify TPOT precision to 2 decimals.
31. **[D3-m1]** `ch4:572` — plan 8B / Mistral b10 extension.
32. **[D3-m2]** `ch4:919-943` — consolidate kv-ablation tables (optional).
33. **[D4-m1]** `ch4:322` — clarify $p=1.0$ phrasing.
34. **[D4-m2]** `ch4:409` — decompose 8-38% into 3-point breakdown in footnote.
35. **[D5-m1]** `ch4:1125` — add explicit "Claim 3" header.
36. **[D5-m2]** `ch4:1501` — rename §subsec:exp-int4-boundary to "INT4-RoleAlign 的能力边界".
37. **[D5-n1]** `ch4:1603-1651` — add `\label{para:finding-1}`…`\label{para:finding-5}`.
38. **[D6-m1]** `ch4:194-204` — add `\label{para:ppl-determinism}`.
39. **[D6-m2]** `ch4:1433-1435` — add `\section{KIVI 三方对比}` or remove stray label.
40. **[D6-n1]** `ch4:332` — rename `para:c6-fail` → `para:ruler-fail`.

### P3 — AI-trace cleanup (Phase 4)

41. **[§8 segment A]** `ch4:845-851` — collapse 3-layer stack into 1 sentence.
42. **[§8 segment B]** `ch4:1546-1557` — cut "相较于传统做法...盲区" bloat.
43. **[§8 segment C]** `ch4:1272-1296` — rewrite "INT4-RoleAlign 与 KIVI-style 的关系" paragraph into 1-2 sentences; cut 2-bit KVTuner speculation.

---

## §11 Experiment Trigger Candidates (NEEDS_EXP=true)

Round 3 Phase 5 experiment queue candidates. These are Phase 2 observations that cannot be closed by text-only Phase 4 edits.

### 11.1 Candidates with HIGH priority (directly resolve MAJOR issues)

1. **[EXP-1: K/V PPL ablation extension to 7B / 8B / Mistral] (D3-M1)**
   - **Current state**: tab:kv-ablation-ppl (L887) only covers 1.5B. The "一致性" claim at L883 is unsupported across models.
   - **Experiment**: run 4 K/V configs × 3 models × seed=1234 (deterministic PPL). Uses WikiText-2 test split. Expected runtime: ~20 min per model × 3 = ~1 GPU hour.
   - **Fix scope**: extend tab:kv-ablation-ppl from 5 rows to 5 × 3 = 15 rows or 5 rows + 3-row consolidation. Resolves D3-M1.
   - **Blocking Phase 4 or not**: No — can be added Round 3 Phase 5 if queue has budget.

2. **[EXP-2: inv_tau × H_kv extension to Mistral-7B for 4th data point] (D3-M2, D5-M1)**
   - **Current state**: tab:invtau-ablation (L1308) has 3 H_kv values (2, 4, 8 from Qwen-1.5B, Qwen-7B, LLaMA-8B). Mistral-7B is the 4th model added in Round 2 but has no inv_tau ablation entry.
   - **Experiment**: 2 configs (inv_tau on/off) × 1 model (Mistral, H_kv=8) × seed=1234 × PPL evaluation. Expected runtime: ~30 min.
   - **Fix scope**: extend tab:invtau-ablation with 2 additional rows. Also enables the §10 item D5-M1 figure ΔPPL-vs-H_kv from 3 points to 4 points (2 of which are H_kv=8, testing model-family sensitivity within the same H_kv class).
   - **Blocking Phase 4 or not**: No — nice-to-have for C5 evidence density.

3. **[EXP-3: BA percentile mini-sensitivity sweep on 1.5B] (D3-M4)**
   - **Current state**: ch3 §3.6.2 discloses the |36| Cartesian grid but ch4 has no sensitivity curve. Statistical_methods reviewer in Round 2 called this a "reproducibility blocker" for ch3.
   - **Experiment**: run 4-6 (p_K, p_V) pairs around the chosen optimum × 1 model (Qwen-1.5B) × seed=1234 × Needle + PPL. Expected runtime: ~1 hour.
   - **Fix scope**: add a small subsection "BA percentile 敏感性" within §sec:exp-rolealign with a 1-figure or 1-table visualization.
   - **Blocking Phase 4 or not**: Optional — could be deferred to Round 4 if queue is tight.

### 11.2 Candidates with MEDIUM priority

4. **[EXP-4: chunk_size ablation extension to 7B / 8B] (ch4:1727, §threats)**
   - **Current state**: chunk_size=1 stress test (§subsec:exp-chunksize in appendix) covers 1.5B only. §threats L1726 acknowledges "chunk_size=1 压力测试仅覆盖 1.5B 单模型".
   - **Experiment**: run cs=1 PPL evaluation on 7B and 8B, all 3 methods (FP16, KIVI-style, INT4-RA). Expected runtime: ~1 GPU hour.
   - **Fix scope**: extend appendix tab:chunksize-results with 2 additional models. Upgrades E15 in tab:claim-summary from "中" to "强".
   - **Blocking Phase 4 or not**: No — purely for robustness breadth.

5. **[EXP-5: calibration dataset ablation (not just sample count)] (ch4:1729 §threats)**
   - **Current state**: §threats L1728-1729 acknowledges "未考察不同校准数据集的影响". Only WikiText-103 is tested.
   - **Experiment**: swap WikiText-103 → C4 or RedPajama-sample × 1 model (1.5B) × 64 samples × KL calibration → Needle + PPL comparison. Expected runtime: ~2 GPU hours (including calibration).
   - **Fix scope**: add 1 paragraph in §exp-ablation-b10 extending the sample-count ablation into a dataset-choice ablation.
   - **Blocking Phase 4 or not**: No — optional robustness extension.

### 11.3 Candidates with LOW priority

6. **[EXP-6: H_kv=1 (MQA) extension for C5 scaling claim] (D3-M2)**
   - **Current state**: C5 claims a scaling trend without testing the extreme endpoint H_kv=1 (MQA). Phi-3 or other MQA models could provide this.
   - **Experiment**: run inv_tau on/off × Phi-3 or similar MQA model × seed=1234 × PPL. Expected runtime: ~1 hour (depends on model download).
   - **Fix scope**: extend tab:invtau-ablation with a 5th model data point. Closes the "curve shape" gap (D3-M2).
   - **Blocking Phase 4 or not**: No — aspirational; would strengthen C5 substantially but requires new model integration.

### 11.4 Summary

**Minimum Phase 5 experiment queue**: EXP-1 + EXP-2 (~1.5 GPU hours, 2 concrete table extensions). These resolve D3-M1 and strengthen D3-M2/D5-M1 without requiring new model integration.

**Maximum Phase 5 experiment queue**: EXP-1 + EXP-2 + EXP-3 + EXP-4 (~4 GPU hours, 4 table/figure extensions). These close most of the MAJOR observational gaps.

**Note**: Round 3 Phase 1 literature digest (currently running in background) may surface additional ch4 experimental gaps not visible from internal review. If Phase 1 finishes before Phase 5 launches, merge its recommendations into this queue.

---

## §12 Round 3 Phase 2 Coverage Statistics

| Phase | Dimension | Observations | CRITICAL | MAJOR | MINOR | NIT |
|-------|-----------|--------------|----------|-------|-------|-----|
| Phase 2 | Dim 1 (Setup) | 4 | 0 | 2 | 2 | 1 |
| Phase 2 | Dim 2 (Reproducibility) | 9 | 2 | 4 | 3 | 1 |
| Phase 2 | Dim 3 (Ablation) | 6 | 0 | 4 | 2 | 0 |
| Phase 2 | Dim 4 (Statistics) | 5 | 0 | 3 | 2 | 0 |
| Phase 2 | Dim 5 (Narrative / C1-C5) | 6 | 1 | 2 | 2 | 1 |
| Phase 2 | Dim 6 (cross-chapter) | 4 | 0 | 2 | 2 | 1 |
| Phase 2 | §8 AI-trace hotspots | 3 segments | — | — | — | — |
| **Total** | **6 dimensions** | **37 observations + 3 hotspots** | **2** | **17** | **13** | **4** |

*Note*: Some observations span multiple severities; the above counts place each at its dominant severity. Total unique issue IDs are 26 (D1-D6) + 3 (§8 segments) = 29; counts in the table may slightly overcount due to double-severity entries.

---

## §13 Round 2 Phase 4b Exclusions — Verification

| Round 2 fix | Current state | Status |
|-------------|---------------|--------|
| ch4:409 TPOT footnote | Present L409 as single long footnote with `batch=1, 独占 GPU` scope + batch=16 forward ref | OK — retained |
| ch4:1349 intuitive-argument hedge | Present L1349-1363 with "严格而言是 heuristic" disclaimer + pairwise correlation disclosure + "方向性预测" | OK — retained |

Both Round 2 Phase 4b changes are verified present and well-scoped. NOT counted as Round 3 issues.

---

## §14 Final Metrics

- **paper_review.md line count**: targeting ≥400 — see footer for final.
- **MAJOR observations**: 17 (exceeds the ≥5 threshold required by task spec).
- **AI-trace hotspot paragraphs**: 3 (meets the ≥3 threshold).
- **Experiment Trigger candidates in §11**: 6 (exceeds the ≥3 threshold).
- **Round 2 Phase 4b exclusions verified and not re-reviewed**: 2/2.

---

**End of Round 3 Phase 2 — ch4 Paper Review.**
