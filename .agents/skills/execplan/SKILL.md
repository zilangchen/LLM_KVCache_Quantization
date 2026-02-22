---
name: execplan
description: Use when starting any task that may change code. Draft an ExecPlan using .agents/PLANS.md, summarize it, ask for APPROVE PLAN, and do not code before approval.
---

# ExecPlan Skill

## Workflow
1) Locate `.agents/PLANS.md`. If missing, propose adding it and embed required sections in chat.
2) Search the repo to ground understanding (reuse patterns, list relevant files).
3) Create or update `.agents/execplans/<YYYY-MM-DD>_<slug>.md`.
4) Post a structured plan summary in chat:
   - Goals / Non-goals / Deliverables / Acceptance criteria / Verification plan / Risks / Questions.
5) Ask for `APPROVE PLAN`. Stop.
