---
name: unit-commit
description: Use after completing a functional unit. Update iteration.md, run targeted verification, stage changes semantically (no git add .), commit, then trigger repo-hygiene.
---

# Unit Commit Skill

## Pre-conditions
- The functional unit is complete and verifiable.

## Workflow
1) Update `iteration.md` with:
   - What changed, commands run, test results, and intended commit message.
2) Run the smallest sufficient verification set for THIS unit.
   - If any failure: invoke `$debug-iterate` and return here after fix.
3) Stage files in semantic groups (NEVER `git add .`):
   - Prefer explicit paths.
4) Commit:
   - Use message format: `feat|fix|refactor|test|docs|chore: ...`
   - If commit touches many concerns, split into multiple commits.
5) Immediately run `$repo-hygiene`.
6) **Memory checkpoint** (conditional — skip for routine changes):
   - Fixed CRITICAL/HIGH bug → append root cause + fix to `debugging-patterns.md` in Memory
   - Completed experiment phase milestone → update `experiment-state.md` in Memory
   - Other routine changes → skip this step
