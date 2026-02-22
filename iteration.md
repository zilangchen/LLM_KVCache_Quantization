# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## Current Status

- Active objective source: `objective.md`
- Active execution policy: `AGENTS.md`
- Active experiment protocol: `experiment_sop.md`
- Progress log source of truth: `iteration.md`

## Update Rules

1. After each completed functional unit, append one new entry under `Timeline` (latest first).
2. Every entry must include goal, changed files, commands run, outputs, and result quality.
3. If blocked, write explicit blocker and next action.
4. Keep entries concise and auditable; avoid vague summaries.

## Entry Template

### YYYY-MM-DD HH:MM | Workstream Title
- Goal:
- Scope:
- Changed files:
- Commands:
- Outputs:
- Validation:
- Risks / follow-ups:

## Timeline (Latest First)

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
