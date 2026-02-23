# Iteration Log — Archive (2026-02 前期)

> 本文件包含 iteration.md 中 2026-02-22 17:24 及更早的 Timeline 条目。
> 当前活跃进度见 `iteration.md`。

---

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
