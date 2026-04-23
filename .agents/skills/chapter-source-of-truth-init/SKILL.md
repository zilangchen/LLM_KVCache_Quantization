---
name: chapter-source-of-truth-init
description: >
  Initialize a thesis chapter's Writing and Draft source-of-truth workflow.
  Use when a chapter lacks its own "This is Chapter X Writing.md" and/or
  "Chapter X Draft.md", or when you need to set up the chapter-level
  structure, boundaries, review protocol, and handoff rules before
  integrating body text. This skill reads AGENTS.md, CLAUDE.md,
  objective.md, story/workbench files, the current chapter tex, and
  mature chapter templates, then produces an ExecPlan and, after approval,
  creates the chapter-specific Writing/Draft source-of-truth files.
---

# Chapter Source-of-Truth Init

## When to Use

Use this skill when the user wants to:

- initialize a chapter's `Writing` / `Draft` source-of-truth
- create `This is Chapter X Writing.md`
- create `Chapter X Draft.md`
- establish chapter structure, section responsibilities, boundaries, and review protocol before drafting body text

Do not use this skill for routine section-by-section body integration after the chapter source-of-truth already exists. Use `chapter-draft-integration` for that.

## Required Inputs

Before planning, locate and read the relevant project files:

1. `AGENTS.md`
2. `CLAUDE.md` if present
3. `objective.md`
4. thesis story / workbench files that freeze chapter roles
5. current chapter `tex`
6. mature template chapters' `Writing` / `Draft` files

At minimum, identify:

- `chapter_id` such as `2`, `3`, `5`
- current chapter tex path
- story path
- target writing path
- target draft path
- template chapter files, if any

## Workflow

### Phase 0: Read-Only Positioning

Do not modify files yet. Determine:

- what job this chapter serves in the full thesis
- how current `tex` differs from the frozen story
- which existing chapter files are templates for workflow form, not content
- whether the user wants both `Writing` and `Draft`, or only one layer first

### Phase 1: ExecPlan Gate

If the task will create or edit files, you must first output an ExecPlan and wait for `APPROVE PLAN`.

The plan must cover:

- problem statement
- alignment with `objective.md` and story/workbench
- goals and non-goals
- constraints and assumptions
- concrete files to create or update
- acceptance criteria
- verification commands
- risks and boundary cases
- open questions
- milestones

### Phase 2: Build the Writing Layer

After approval, create `This is Chapter X Writing.md`.

The `Writing` file should:

- freeze chapter structure
- define section responsibilities and non-responsibilities
- define figure/table strategy
- define formula density and bridge discipline where relevant
- define relative-to-current-tex rewrite actions
- define chapter-specific boundary rules

Do not fake completed prose. Start with structure, then upgrade each section into actionable construction entries.

Recommended section-entry granularity:

- section title
- section responsibilities
- what this section must not do
- best paragraph structure
- formula plan
- figure/table plan
- rewrite actions relative to current tex
- target reader impression

### Phase 3: Build the Draft Layer

Only create `Chapter X Draft.md` if the user approved it for this phase.

The `Draft` file should contain:

- document identity and current status
- current review baseline
- source-of-truth file list
- file responsibility boundaries
- frozen chapter structure overview
- high-risk frozen wording rules
- current tex inconsistency list
- external draft intake rules
- review protocol
- integration area
- final write-back blocks

The `Draft` file is a review-and-integration container, not final tex.

## Output Rules

When reporting the initialization result, include:

1. changed files
2. verification commands
3. actual verification result
4. iteration / commit / repo hygiene status
5. next recommended step

## Boundary Rules

- Do not directly rewrite chapter `tex` during initialization unless the user explicitly changes scope.
- Do not change thesis story files without explicit approval.
- Do not copy another chapter's semantics; only reuse workflow form.
- Do not treat current `tex` as the sole source-of-truth if story/workbench already froze a newer structure.
- If the user only wants `Writing` first, do not create `Draft`.

## Validation

After file creation, verify with commands like:

```bash
test -f "docs/This is Chapter X Writing.md"
test -f "docs/Chapter X Draft.md"   # only if this phase includes Draft
rg -n '^## |^### ' "docs/This is Chapter X Writing.md"
rg -n '^## |^### ' "docs/Chapter X Draft.md"   # only if created
git status --short -- "docs/This is Chapter X Writing.md" "docs/Chapter X Draft.md" "<chapter-tex>"
```

## Do Not

- do not skip ExecPlan for file-creation tasks
- do not silently absorb story/tex conflicts
- do not write body prose as if the chapter is already complete
- do not directly sync to `tex` as part of initialization
