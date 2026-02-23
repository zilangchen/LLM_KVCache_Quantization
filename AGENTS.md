# AGENTS.md (repo root)

# Project Guidance for Codex

> 详细开发规范见 `CLAUDE.md`（项目规范入口）。本文件为 Codex 兼容的轻量概览。

## Project snapshot

- Project purpose: reproducible KV-cache quantization research pipeline for efficient LLM inference.
- Tech stack: Python 3.12, PyTorch, Transformers, Triton, numpy/pandas/matplotlib.
- Key modules: `src/cache/`, `src/quant/`, `src/kernels/`, `src/engine/`, `scripts/`.
- Architecture docs: `objective.md`, `README.md`, `experiment_sop.md`.
- Review tracker: `review_tracker.md` (root, authoritative file for all code review issues).
- Coding conventions: follow existing style in repo; prefer minimal diffs and explicit reproducibility metadata.

## Agent roles

- **Supervisor** (`.claude/agents/supervisor.md`): 目标驱动持续运行，无固定轮次上限。支持 Execute/Wait/Monitor 三模式自动切换，智能熔断（仅 Execute 模式下无进展才触发）。
- **Developer** (`.claude/agents/developer.md`): 编码/测试/修复执行者，自主 debug+commit+hygiene 流程。
- **Review-Coord** (`.claude/agents/review-coord.md`): 审查协调员，并行调度 7 个专项审查 Agent（D1-D7），结果汇聚到 `review_tracker.md`。

## Commands

| Task | Command |
|------|---------|
| Test | `pytest tests/ -v` |
| Smoke test (GPU) | `python scripts/smoke_test.py --save_output` |
| Dry-run | `python scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run` |

## Repo hygiene rules

- Generated outputs/logs go to `results/<run_tag>/` or `artifacts/` and are usually NOT committed.
- Historical materials go to `development_history/archive_<YYYYMMDD>_<topic>/`.
- Keep top-level clean; update `.gitignore` when needed.
- Never use `git add .` — stage files in semantic groups.
- Commit message format: `feat:` / `fix:` / `refactor:` / `test:` / `docs:` / `chore:`
- If pushing requires network/credentials, ask before `git push`.
