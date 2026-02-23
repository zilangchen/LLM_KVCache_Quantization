# Iteration Log — Archive (2026-02 前期)

> 本文件包含 iteration.md 中 2026-02-23 07:27 及更早的 Timeline 条目。
> 当前活跃进度见 `iteration.md`。

---

### 2026-02-23 07:27 | Phase 4 COMPLETE: Ablation Experiments Finished (70/70 runs)
- **Goal**: Run full ablation experiment matrix on remote GPU
- **Remote execution**: `run_experiments.py --config exp_matrix_ablation_1p5b_v1.yaml --tasks eval_ppl,eval_needle --seeds {1234..1238}`
- **Results**: 14 configs × 5 seeds × 2 tasks = 70 runs, all successful
  - A 节 (校准对比): kl/mse/percentile/percentile_fused/kivi — 5 configs
  - B 节 (温度校正): temp_on/temp_off — 2 configs
  - C 节 (group_size): g16/g32/g64/g128 — 4 configs
  - D 节 (scales): static/adaptive/dynamic — 3 configs
- **Duration**: ~65 min total (06:22 → 07:27), ~13 min per seed
- **Output dir**: `results/runs/ablation_*_s{seed}_ablation_1p5b_s{seed}/`
- **Next**: Phase 5 — full 3-model matrix experiments (1.5B KIVI补跑 → 7B → 8B)

### 2026-02-23 06:19 | Phase 4.1: MSE Calibration Complete + Phase 5 Blockers Resolved
- **Goal**: Generate MSE calibration artifacts for 1.5B model; fix remaining CRITICAL/HIGH blockers for Phase 5
- **Changed files**:
  - `scripts/eval_ppl.py`: Added kivi_style branch in build_kv_cache() + quant_bits parameter (L-1 fix)
  - `scripts/aggregate_results.py`: Added KIVI significance pairings, longbench_official_macro, model_id in sig_specs/ruler_depth_keys (M-1/M-2/M-3/M-4 fix)
  - `iteration.md`: Updated 20+ backlog checkboxes, Phase 4 plan status
- **Remote GPU tasks**:
  - MSE INT8 calibration: `calibrate_behavior.py --loss_function mse --search --quant_bits 8` → artifacts/kv_calib_mse_1p5b_int8.json (41KB)
  - MSE INT4 calibration: `calibrate_behavior.py --loss_function mse --search --quant_bits 4 --int4_search` → artifacts/kv_calib_mse_1p5b_int4.json (64KB)
  - INT8 best: g16/clip=99.5 (p95_mse=0.000956); INT4 best: g16 search across outlier_ratios
- **Commits**: 03ed4a0 (eval_ppl+aggregate fix), 03d2e13 (docs), 9f41659 (backlog checkboxes)
- **Pushed**: 8 commits to origin/main (36921e6..9f41659)
- **Backlog status**: All CRITICAL=0, remaining HIGH=3 (non-blocking: A-5 doc, D-2 design, K-1 usability)
- **Next**: Run ablation experiments (14 configs × 5 seeds × 3 tasks) on remote GPU

### 2026-02-23 23:30 | Phase 4-6 Prep: Bug Fixes + Config Updates + Claims Extension

- **Goal**: Resolve all CRITICAL/HIGH backlog items blocking Phase 4-6, update configs for full matrix, extend thesis report claims.
- **Changed files (BUG FIXES)**:
  - `scripts/calibrate_behavior.py`: Fixed MSE loss aggregation (.mean→.sum), clamp(min=eps), loss_accum normalization, --calib_out default, select_best_trial key check
  - `src/cache/kivi_style_cache.py`: Fixed clear() to reset _k_scale/_k_zp
  - `src/quant/asymmetric_quant.py`: Added percentile range validation (50, 100]
  - `src/engine/generate_loop.py`: Added quant_bits to generate() API
  - `scripts/eval_longbench.py`: Added logging import + logger
- **Changed files (CONFIG UPDATES)**:
  - `configs/exp_matrix.yaml`: +13 KIVI entries, -2 FP16 b24/b32
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml`: +40 entries (long INT4/KIVI + throughput)
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: +40 entries (same)
  - `configs/snapshots/exp_matrix_ablation_1p5b_v1.yaml`: Created, 14 runs
  - `configs/snapshots/final_emnlp2026_v1.yaml`: Created meta-config
- **Changed files (FEATURE)**:
  - `scripts/export_tables_latex.py`: +kivi_style to KV_MODE_ORDER/DISPLAY
  - `scripts/generate_thesis_report.py`: +claims C7-C11
  - `CLAUDE.md`: +Phase gate rule (§4.4), +remote server section (§12)
- **Verification**: compileall 0 errors; all YAML parse OK; 11 ClaimSpecs; 86+14+67+67 matrix runs
- **Backlog resolved**: A1-A4/A6-A7, B1, C1-C2, D1, E1-E4, F1-F3, G1-G2/G4, J1
- **Commit**: pending
- **Next**: commit → rsync → MSE calibration → ablation

### 2026-02-23 22:00 | 项目监管审查：全面代码质量审查
- **Goal**: 作为监管 agent，对当前代码库所有新增/修改模块进行全面审查，发现潜在问题并归档到待办清单
- **Scope**: 6 个并行审查 agent 分别检查 KIVI cache、asymmetric quant、generate_loop、eval 脚本集成、MSE 校准、配置矩阵一致性
- **审查模块与发现数量**:
  - `src/cache/kivi_style_cache.py`: 4 CRITICAL + 3 MEDIUM + 3 LOW
  - `src/quant/asymmetric_quant.py`: 2 CRITICAL + 2 MEDIUM + 1 LOW
  - `src/engine/generate_loop.py`: 2 HIGH + 1 MEDIUM + 1 LOW
  - 评测脚本集成（9 个脚本）: 2 CRITICAL + 2 HIGH + 4 MEDIUM + 1 LOW
  - `scripts/calibrate_behavior.py` MSE: 3 CRITICAL + 4 HIGH + 3 MEDIUM
  - 配置矩阵一致性（3 YAML）: 3 HIGH + 2 MEDIUM + 1 LOW
- **关键发现（阻塞性）**:
  1. MSE 校准实现有根本性 loss 语义错误（mean vs sum 不一致），产物不可信 → 阻塞 Phase 4
  2. percentile < 50 时非对称量化公式翻转 min/max，静默产生错误结果 → 需添加范围校验
  3. export_tables_latex.py 完全缺失 KIVI 显示名和排序 → 阻塞论文表格
  4. eval_longbench.py 引用未定义 logger → 特定条件下 NameError 崩溃
  5. 1.5B 配置缺失 KIVI 条目，7B/8B 缺失吞吐量条目 → 跨模型对比不完整
  6. generate() 高层 API 无法指定 KIVI quant_bits → INT4 KIVI 不可用
- **产出**: 全部问题已写入 `iteration.md` TODO Backlog A-F 节（按模块分类、按严重性排序）
- **Validation**: 审查基于 6 个专业 agent 的独立代码阅读，每个 agent 逐行分析源码
- **Risks / follow-ups**:
  - 所有 CRITICAL/HIGH 问题必须在 Phase 4/5 启动前修复
  - MSE 校准需完整重写 loss 聚合逻辑后才能生成可信产物
  - 建议开发 agent 优先修复 A 节（MSE）和 C 节（percentile 校验），因为这两个影响数值正确性

### 2026-02-23 | Phase 1-Pre/3/4.1: KIVI Baseline + MSE Calibration + Multi-Model Configs

- **Goal**: Implement KIVI-style asymmetric KV cache baseline (Phase 3), MSE calibration loss (Phase 4.1), per-model config files (Phase 0.5), and integrate into all eval scripts. Part of EMNLP 2026 Milestone K-Q execution plan.
- **Changed files (NEW)**:
  - `src/quant/asymmetric_quant.py`: Asymmetric INT8/INT4 quantization with per-channel and per-token axis support, zero-point. Core functions: `quantize_asymmetric_per_channel()` (K cache), `quantize_asymmetric_per_token()` (V cache), and their dequantize counterparts.
  - `src/cache/kivi_style_cache.py`: `KIVIStyleKVCache` class implementing KIVI paper's per-channel K + per-token V asymmetric quantization. Interface-compatible with `INT8KVCache`. Supports INT8 and INT4 via `quant_bits` parameter. Always uses `torch_ref` decode (no Triton fused kernel). K scale computed at prefill, reused at decode.
  - `tests/test_asymmetric_quant.py`: 15 unit tests covering round-trip error, edge cases, INT8/INT4, per-channel/per-token axis, zero-point correctness.
  - `tests/test_kivi_cache.py`: 17 unit tests covering basic append/get, prefill+decode pattern, K scale persistence, V scale independence, capacity growth, interface compatibility.
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml`: Qwen2.5-7B config with core runs + KIVI entries.
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: LLaMA-3.1-8B config with core runs + KIVI entries.
- **Changed files (MODIFIED)**:
  - `src/cache/__init__.py`: Added `KIVIStyleKVCache` export.
  - `src/quant/__init__.py`: Added asymmetric quant function exports.
  - `src/engine/generate_loop.py`: Added `kivi_style` to kv_mode validation, added KIVI cache instantiation branch, added `quant_bits` parameter to `generate_from_ids()`, routed KIVI through baseline dequant-before-attention path.
  - `scripts/eval_ppl.py`, `eval_needle.py`, `eval_longbench.py`, `eval_ruler.py`, `profile_latency.py`, `profile_memory.py`, `run_experiments.py`: Added `kivi_style` to `--kv_mode` choices, added `--quant_bits` passthrough for KIVI INT4/INT8 disambiguation.
  - `scripts/calibrate_behavior.py`: Added `--loss_function {kl,mse}` argument, MSE loss path in `evaluate_quant_candidate()` and `compute_inv_tau()`, MSE objective support in `select_best_trial()`.
- **Verification**: `python3 -m compileall -f scripts/ src/ tests/` → all 34 files compile clean, 0 errors. YAML configs parse OK.
- **Commit**: pending
- **Next steps**:
  - Phase 0: Push to remote, `git pull`, verify 3 models loadable, run smoke tests.
  - Phase 1: Remote validation of LongBench/RULER on all 3 models.
  - Phase 2: Generate calibration artifacts for Qwen2.5-7B and LLaMA-3.1-8B.
  - Phase 4: Generate MSE calibration artifacts, run ablation matrix.
  - Phase 5: Full 3-model × 7 kv_mode × 5 benchmark matrix.

### 2026-02-23 | LongBench Official Metrics + Objective Refinement (Round 2)

- **Goal**: Add LongBench official per-task metrics (Rouge-L, Accuracy, Edit Similarity) to `eval_longbench.py`; change `longbench_score` from uniform token-F1 to official metric macro-average; add snapshot governance rule to objective.md.
- **Trigger**: Second round of ChatGPT review identified that uniform token-F1 across all LongBench tasks deviates from official evaluation protocol. Cross-validated with code: confirmed code did use uniform F1 (not "wrong" but needs explicit justification). Decided to implement official metrics.
- **Changed files**:
  - `scripts/eval_longbench.py`: Added `TASK_OFFICIAL_METRIC` mapping dict (21 tasks), `_lcs_length()`, `_rouge_l()`, `_edit_similarity()`, `_classification_accuracy()`, `_compute_official_metric()`. Updated main loop to compute official metric per sample. Added `official_metric_name` / `official_metric_value` to all 3 CSV outputs (details, task_summary, profile). Changed `longbench_score` from `f1_macro` to `official_macro`.
  - `objective.md`: (1) LongBench 主表汇总协议: rewrote to declare per-task official metrics with mapping table reference; (2) Primary Endpoint #1: changed from "F1-macro" to "official-metric macro"; (3) Added snapshot governance rule under 实验入口 section.
- **ChatGPT 6-point cross-validation summary**:
  - 必改点1 (LongBench metric): ChatGPT factually wrong (code DID use uniform F1), but concern valid → implemented official metrics
  - 必改点2 (RULER alignment): Already done in previous round, ChatGPT saw stale version → no change needed
  - 必改点3 (✅ markers): Would make doc unstable → not changed
  - 必改点4 (PPL chunk): Already covered in current text → not changed
  - 必改点5 (DoD tiering): User previously rejected → respected decision
  - 必改点6 (Snapshot governance): Valid, low cost → added 1 rule
- **Verification**: `python3 -m py_compile scripts/eval_longbench.py` → OK
- **Commit**: pending
- **Risks / follow-ups**:
  - Rouge-L LCS computation is O(n*m) on token lists; for very long predictions may be slow. Mitigated: LongBench answers are typically short.
  - `_edit_similarity` is character-level O(n*m); fine for code completion outputs (typically <500 chars).
  - Need remote smoke test to verify end-to-end with real model outputs.

### 2026-02-23 | RULER 4-Subtask Rewrite + LongBench 7-Task Extension + Objective Review
- Goal: address publishability gaps found during ChatGPT-assisted objective.md review — rewrite RULER eval to implement 4 genuine subtasks (S-NIAH, MK-NIAH, VT, CWE) instead of simplified single-needle retrieval; extend LongBench to 7 tasks; update objective.md with verified suggestions.
- Scope: eval_ruler.py rewrite, eval_longbench.py extension, objective.md revision, pipeline plumbing updates.
- Changed files:
  - `scripts/eval_ruler.py` (full rewrite: 4 RULER subtask generators + task-level scoring + backward-compatible CSV output)
  - `scripts/eval_longbench.py` (fix HF field extraction for context+input pattern; update default tasks to 7)
  - `scripts/run_experiments.py` (add new RULER args: --ruler_tasks, --ruler_mk_num_keys, --ruler_vt_*, --ruler_cwe_*)
  - `scripts/aggregate_results.py` (add ruler_task_summary aggregation)
  - `scripts/run_week5_external_validity_v1.sh` (update RULER and LongBench task params)
  - `objective.md` (PPL 1M tokens, ARR window, revision pin, env version, RULER description, LongBench macro protocol, primary endpoints, stat family, milestone status)
  - `iteration.md`
- Key decisions:
  - RULER: self-implemented task generators following NVIDIA/RULER taxonomy, NOT the official RULER runtime
  - LongBench: 7 tasks = narrativeqa, dureader, hotpotqa, gov_report, vcsum, trec, lcc (EN+ZH coverage)
  - DoD: kept flat (no P0/P1/P2 tiering per user preference)
  - PPL: main results now use target_tokens=1_000_000 (was max_samples=64 ≈ 65K)
  - Primary endpoints capped at 5: LongBench F1-macro, RULER macro-accuracy, Needle pass rate, PPL, TPOT
- Validation:
  - All modified scripts pass `python3 -m py_compile`
  - Local numpy broken (known issue); full test suite must run on remote server
- Risks / follow-ups:
  - LongBench HF loading for dureader/vcsum/trec/lcc untested with real data (needs remote validation)
  - RULER CWE subtask scoring (set matching) needs end-to-end validation with real model
  - RULER case count changed from 96 total to 24 per-task (= 96 total across 4 tasks)
  - Remote smoke test needed before full Week5 run

### 2026-02-22 17:24 | Week5 External-Validity Chain + Remote Smoke Closure
- Goal: complete Week5 engineering upgrade (LongBench/RULER integration + PPL token-floor hardening) and verify the full experiment-to-report pipeline on Remote-Server.
- Scope: add missing eval task implementation, wire runner/strict aggregation/report/latex, fix runtime edge cases discovered in remote smoke.
- Changed files:
  - `scripts/eval_ruler.py`
  - `scripts/eval_ppl.py`
  - `scripts/run_experiments.py`
  - `scripts/check_run_completeness.py`
  - `scripts/aggregate_results.py`
  - `scripts/export_tables_latex.py`
  - `scripts/generate_thesis_report.py`
  - `scripts/run_week5_external_validity_v1.sh`
  - `configs/snapshots/exp_matrix_week5_external_validity_v1.yaml`
  - `tests/test_aggregate_results_stats.py`
  - `iteration.md`
- Commands:
  - local compile: `python3 -m compileall ...`
  - local unit tests: `python3 -m unittest tests/test_run_experiments_resilience.py tests/test_check_run_completeness.py`
  - remote health: `ssh -p 31867 root@region-42.seetacloud.com "echo SSH OK && nvidia-smi -L"`
  - remote smoke (tmux): run `eval_ppl,eval_needle,eval_longbench,eval_ruler` on `fp16_kv_curve_4k` with strict aggregation/export/report
  - remote report regression test: `/root/miniconda3/bin/python -m unittest tests/test_generate_thesis_report.py`
- Outputs:
  - new week5 runner entrypoint: `scripts/run_week5_external_validity_v1.sh`
  - remote smoke package: `results/week5_smoke_remote_r2/` (runs/logs/tables/plots/latex/reports)
  - new aggregated artifacts confirmed: `longbench_summary.csv`, `ruler_summary.csv`, `ruler_depth_summary.csv`, `longbench_task_summary.csv`
- Validation:
  - remote `run_experiments_smoke.json`: 4/4 tasks success (`eval_ppl`, `eval_needle`, `eval_longbench`, `eval_ruler`)
  - strict aggregation completed: `results/week5_smoke_remote_r2/aggregate.log`
  - latex export completed: `results/week5_smoke_remote_r2/export_latex.log`
  - report generation completed after fix: `results/week5_smoke_remote_r2/report.log`
  - fixed two real defects found during smoke:
    - `eval_ppl` token-floor off-by-one (target 4096 -> evaluated 4095) by reserving `target_tokens + 1` input budget
    - `generate_thesis_report.py` crash when `stat_decisions` has no `decision` column (now robust fallback)
- Risks / follow-ups:
  - local host python environment still lacks usable `numpy` runtime (`libcblas.3.dylib` missing); numpy-dependent local tests remain blocked
  - current smoke validates functionality, not statistical claims (single fp16 run only), so claim rows are expected `INCONCLUSIVE`

### 2026-02-22 16:31 | Record C1 Statistical Inconclusive Risk
- Goal: formally record the `C1` long-context TPOT significance issue for planned optimization, without mutating current final package results.
- Scope: add a traceable risk entry with evidence paths, root-cause interpretation, and explicit follow-up rerun action.
- Changed files:
  - `iteration.md`
- Commands:
  - inspect `results/final_journal_v1/reports/claim_validation.csv`
  - inspect `results/final_journal_v1/tables/significance_summary.csv`
  - inspect `results/final_journal_v1/tables/significance_pairs.csv`
- Outputs:
  - documented issue: `C1` is `INCONCLUSIVE` due to `q_value=0.0852` and `p_value=0.0625` at `n_pairs=5`
  - documented interpretation: with current paired exact two-sided test and small `n`, statistical power is insufficient for `q<0.05` despite strong practical gain
  - documented follow-up plan: targeted long-context TPOT补跑（新增 seed 至 n>=8，建议 n=8~10）后重聚合
- Validation:
  - evidence is consistent across `claim_validation.csv` and significance tables
  - current final package integrity unchanged (no rerun/no overwrite)
- Risks / follow-ups:
  - until long-context paired sample size is increased, C1 remains non-definitive for strict significance claims
  - execute targeted补跑 in next optimization iteration and refresh claim gate artifacts

### 2026-02-22 11:02 | SOP Entrypoint Rename
- Goal: switch experiment SOP to a single canonical file `experiment_sop.md` and avoid broken legacy links.
- Scope: rename protocol file, update active guidance references, and provide a legacy redirect note at old path.
- Changed files:
  - `experiment_sop.md` (moved from `docs/final_experiment_protocol.md`)
  - `AGENTS.md`
  - `README.md`
  - `iteration.md`
  - `docs/final_experiment_protocol.md` (legacy redirect notice)
  - `development_record.md` (historical note update)
- Commands:
  - `mv docs/final_experiment_protocol.md experiment_sop.md`
  - replace active references to `experiment_sop.md`
  - create legacy notice at `docs/final_experiment_protocol.md`
- Outputs:
  - unique active SOP entrypoint: `experiment_sop.md`
  - old link path now resolves to a redirect notice instead of missing file
- Validation:
  - active policy and README now point to `experiment_sop.md`
  - no broken path for legacy `docs/final_experiment_protocol.md` access
- Risks / follow-ups:
  - `development_record.md` retains historical old-path text by design

### 2026-02-22 10:55 | Rename Agent Workspace Directory
- Goal: rename the repository agent workspace from `.agent/` to `.agents/` and remove stale path guidance.
- Scope: move directory, update active docs/scripts/global policy references, and re-scan for old path pointers.
- Changed files:
  - `.agents/` (renamed from `.agent/`)
  - `AGENTS.md`
  - `scripts/run_experiments.py`
  - `.agents/execplans/README.md`
  - `.agents/skills/execplan/SKILL.md`
  - `/Users/chenzilang/.codex/AGENTS.md`
  - `development_record.md` (legacy path note)
  - `iteration.md`
- Commands:
  - `mv .agent .agents`
  - replace `.agent/` -> `.agents/` in active guidance files
  - `rg -n "\\.agent/" ...` scans to verify old-path cleanup
- Outputs:
  - single canonical agent workspace path: `.agents/`
- Validation:
  - active guidance now points to `.agents/...`
  - only historical logs may still mention `.agent/` (expected)
- Risks / follow-ups:
  - `development_record.md` keeps legacy strings for historical traceability

### 2026-02-22 10:49 | Workflow Guide Path Fixes
- Goal: prevent broken workflow guidance where agents/users follow a documented path but cannot find files or scripts.
- Scope: align active docs to one remote repo path and remove invalid script reference from skills.
- Changed files:
  - `README.md`
  - `experiment_sop.md`
  - `docs/final_results_summary.md`
  - `docs/thesis_preflight_checklist.md`
  - `.agents/skills/reproducibility/SKILL.md`
  - `.agents/skills/long-running-task/SKILL.md`
  - `iteration.md`
- Commands:
  - replace `/root/autodl-tmp/LLM_KVCache_Quantization` -> `/root/LLM_KVCache_Quantization` in active docs
  - replace invalid `scripts.utils` validation command with `scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run`
  - `rg -n` scans for deprecated paths and missing workflow references
- Outputs:
  - active workflow docs now point to existing canonical paths
  - reproducibility skill no longer references missing `scripts/utils.py`
- Validation:
  - no hits in active files for `.agent/`, `lang.md`, `docs/AGENT_README.md`, `scripts/agent_tools`, or `scripts.utils`
- Risks / follow-ups:
  - `development_record.md` keeps historical legacy references by design (not an active workflow guide)

### 2026-02-22 10:46 | Skill Directory Unification
- Goal: unify skill directories to a single canonical path and verify no active duplicate references remain.
- Scope: consolidate duplicate skill directories into one root and run redundancy scan on active files.
- Changed files:
  - `iteration.md`
  - `.agents/skills/debug-iterate/SKILL.md` (moved)
  - `.agents/skills/execplan/SKILL.md` (moved)
  - `.agents/skills/repo-hygiene/SKILL.md` (moved)
  - `.agents/skills/unit-commit/SKILL.md` (moved)
- Commands:
  - directory consolidation operations for skill folders
  - `rg -n` policy-keyword scans on active files
- Outputs:
  - single skill root for custom skills
- Validation:
  - custom skills centralized and callable from one location
- Risks / follow-ups:
  - `development_record.md` is still historical and contains old path references by design

### 2026-02-22 10:00 | Agent Pipeline Consolidation
- Goal: unify agent execution pipeline and remove duplicated process management.
- Scope: replace `lang.md` with `iteration.md`; deprecate local task lock system; keep one policy path.
- Changed files:
  - `AGENTS.md`
  - `README.md`
  - `objective.md`
  - `iteration.md`
  - `.agents/skills/long-running-task/SKILL.md`
- Commands:
  - `rg -n "lang\\.md|AGENT_README\\.md|agent_tools/agent_cli" ...`
  - file migration and archive operations (see `development_history/archive_20260222_agent_pipeline_cleanup/MANIFEST.md`)
- Outputs:
  - unified policy references
  - archive manifest for deprecated workflow assets
- Validation:
  - active files no longer depend on `lang.md` or local lock CLI
- Risks / follow-ups:
  - historical docs still contain old references inside archive directories (expected)

## Legacy System Issues (Migrated)

| ID | Discovered | Issue | Trigger | Proposed Fix | Status |
|----|------------|-------|---------|--------------|--------|
| 001 | 2026-01-22 | Remote env package versions drift | Running `smoke_test.py` | Pin dependency versions and add startup checks | Tracked |
| 002 | 2026-01-22 | Doc/script/matrix drift causes reproducibility confusion | Aligning `development_record.md` with code and matrix | Enforce single entrypoint and config snapshots | Tracked |
| 003 | 2026-02-08 | Full-concat PPL tokenization creates long warnings and possible memory waste | Running `scripts/eval_ppl.py` | Use chunk/stream tokenization and record `max_length/stride` | Resolved |
| 004 | 2026-02-08 | Long remote runs break with direct SSH sessions | Remote `eval_ppl.py` validation | Use tmux background sessions and persisted logs | Tracked |
