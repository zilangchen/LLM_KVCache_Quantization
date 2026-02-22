# AGENTS.md (repo root)

# Project Guidance for Codex

## Project snapshot

- Project purpose: reproducible KV-cache quantization research pipeline for efficient LLM inference.
- Tech stack: Python 3.12, PyTorch, Transformers, Triton, numpy/pandas/matplotlib.
- Key modules: `src/cache/`, `src/quant/`, `src/kernels/`, `src/engine/`, `scripts/`.
- Architecture docs: `objective.md`, `README.md`, `docs/final_experiment_protocol.md`.
- Coding conventions: follow existing style in repo; prefer minimal diffs and explicit reproducibility metadata.

## Mandatory planning gate

- For any non-trivial change (multi-file change, new feature, refactor, or unclear bug):
  - Create or update an ExecPlan in `.agents/execplans/<YYYY-MM-DD>_<slug>.md` following `.agents/PLANS.md`.
  - Present the plan in chat and WAIT for `APPROVE PLAN` before coding.

## Mandatory iteration log + commit workflow

- After EACH completed functional unit:
  1) Update `iteration.md` (append entry).
  2) Run verification commands relevant to that unit.
  3) Commit (small, logical commit; no `wip`) unless user asks not to commit.
- Prefer using skill `$unit-commit` for this workflow.

## Repo hygiene rules (keep repo not messy)

- Generated outputs/logs go to `results/<run_tag>/` or `artifacts/` and are usually NOT committed.
- Historical and deprecated materials go to `development_history/archive_<YYYYMMDD>_<topic>/`.
- Keep top-level clean; move transient files to archive paths and update `.gitignore` when needed.
- After each commit, run `$repo-hygiene`.

## Git discipline

- Never use `git add .`
- Stage files in semantic groups.
- Commit message format: `feat: ...`, `fix: ...`, `refactor: ...`, `test: ...`, `docs: ...`, `chore: ...`
- If pushing requires network/credentials, ask before `git push`.
