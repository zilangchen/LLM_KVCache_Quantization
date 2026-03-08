---
name: session-handoff
description: End-of-session handoff — summarize state, update Memory files, ensure clean transition to next session.
---

# Session Handoff Skill

## When to Use

Run this skill at the end of a significant work session, especially before:
- Closing a long-running Supervisor session
- Switching to a different phase of work
- Handoff between users or between automated/manual sessions

## Workflow

1) **Gather current state**:
   ```bash
   python scripts/review_tool.py stats
   python scripts/iteration_tool.py stats
   ```

2) **Check experiment state**:
   - Read `experiment-state.md` in Memory — does it reflect current reality?
   - If experiments progressed or completed, update the file.

3) **Check MEMORY.md**:
   - Read MEMORY.md — are "当前阶段", "关键 Bug 状态" sections current?
   - Update if stale (e.g., new CRITICAL bugs, phase transitions, tracker count changes).

4) **Check debugging patterns**:
   - If CRITICAL/HIGH bugs were fixed this session, ensure `debugging-patterns.md` has the root cause + fix.

5) **Output session handoff summary**:
   ```
   === Session Handoff Summary ===
   - review_tracker: <total> issues | <fixed> fixed | <open> open (<crit> CRIT)
   - iteration.md: <lines> lines, <timeline_entries> Timeline entries
   - Approved Plans: <list active plans with status>
   - Memory files updated: <list or "none">
   - Open blockers: <list or "none">
   - Recommended next action: <brief description>
   ```
