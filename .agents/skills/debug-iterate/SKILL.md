---
name: debug-iterate
description: Use when commands/tests fail or results are unsatisfactory. Diagnose via minimal repro + logs + diff inspection, patch, and rerun until acceptance criteria are met or blocked by missing info.
---

# Debug and Iterate Skill

## Workflow (repeat until pass)
1) Capture failure precisely:
   - Command, exit code, key error lines.
2) Reduce to minimal repro:
   - Narrow failing test / minimal script / smallest input.
3) Diagnose:
   - Inspect recent diff, relevant modules, logs.
4) Patch:
   - Smallest change that can fix root cause.
5) Verify:
   - Rerun minimal repro + relevant tests.
6) If still failing:
   - Iterate; do not abandon early.
7) If blocked:
   - Ask targeted questions with options and recommendations.
