---
name: repo-hygiene
description: Use after each commit (or when repo gets messy). Ensure git status is clean, archive transient artifacts by date+feature, and keep the repository organized.
---

# Repo Hygiene Skill

## Workflow
1) Inspect:
   - `git status`
   - Untracked/transient files (build outputs, logs, datasets, checkpoints).
2) Decide for each item:
   - Archive to `development_history/archive_<YYYYMMDD>_<topic>/`, OR
   - Add to `.gitignore`, OR
   - Delete if safe (ask if uncertain).
3) Enforce structure:
   - Results/metrics under `results/`
   - Calibration artifacts under `artifacts/`
   - Documentation under `docs/`
4) Ensure top-level stays minimal and readable.
5) Confirm repo is clean again.
