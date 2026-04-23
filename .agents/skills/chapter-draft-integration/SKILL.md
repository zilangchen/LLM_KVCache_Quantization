---
name: chapter-draft-integration
description: >
  Review, clean, and integrate one chapter section at a time into
  "Chapter X Draft.md". Use when the user provides external body text,
  LaTeX-ready text, or multi-agent draft output and wants it classified,
  checked against story and "This is Chapter X Writing.md", labeled as
  adopt/revise/reject, minimally cleaned, and written into the Draft
  integration area plus the final write-back block. This skill reads the
  chapter story, Writing source-of-truth, Draft source-of-truth, and
  current chapter tex, and keeps tex write-back disabled unless explicitly
  approved.
---

# Chapter Draft Integration

## When to Use

Use this skill when the user wants to:

- integrate a section draft into `Chapter X Draft.md`
- review external prose against chapter story and writing rules
- decide whether a section should be adopted, revised, or rejected
- maintain a clean "final write-back block" without touching `tex`

Use this skill one section at a time. If the incoming text spans multiple chapter sections, split or reject before integration.

Do not use this skill to initialize a chapter from scratch. Use `chapter-source-of-truth-init` for that.

## Required Inputs

Before editing, read the chapter's review baseline:

1. `AGENTS.md`
2. `CLAUDE.md` if present
3. `objective.md`
4. thesis story / workbench files
5. `This is Chapter X Writing.md`
6. `Chapter X Draft.md`
7. current chapter `tex`

Also collect:

- `chapter_id`
- `section_id` if already known
- incoming draft text
- whether the incoming text is plain prose or LaTeX-ready

## Core Review Baseline

Always judge incoming text against this three-piece source-of-truth:

- thesis story / workbench file
- `This is Chapter X Writing.md`
- `Chapter X Draft.md`

Use current chapter `tex` as the object under audit, not as the only truth source.

## Workflow

### Phase 0: Section Assignment

First determine which section the incoming text belongs to.

If the text:

- cleanly belongs to one section: continue
- mixes multiple sections: split before adoption, or mark `需改写`
- belongs to another chapter: reject or redirect explicitly

### Phase 1: Alignment Review

For the target section, check:

1. whether it aligns with story-level chapter responsibility
2. whether it aligns with `Writing`-level section responsibility and boundaries
3. whether it overreaches into later chapters such as methods, experiments, or system conclusions

### Phase 2: ExecPlan Gate

If the task will modify `Chapter X Draft.md`, output an ExecPlan and wait for `APPROVE PLAN`.

Keep the plan focused on:

- target section
- expected decision label
- planned minimal edits
- write locations inside Draft
- verification commands

### Phase 3: Decision

Only use these labels:

- `采用`
- `采用（经修正后）`
- `需改写`
- `拒绝`

Prefer minimal correction over large rewrites when the direction is already right.

### Phase 4: Minimal Cleaning

Typical acceptable minimal edits:

- tighten over-strong claims
- remove early method declarations
- remove early experiment conclusions
- convert chat-style math into tex-ready form
- replace PDF-number-style references with proper citation placeholders or project citation style
- restore section-local boundary discipline

Do not silently change the argument if it conflicts with story or Writing. State the conflict.

### Phase 5: Draft Write-Back

If the text passes review, update two places in `Chapter X Draft.md`:

1. **Integration area**
   - section title
   - timestamp
   - review decision
   - minimal edit summary
   - cleaned section text

2. **Final write-back block**
   - only the cleaned final text
   - no commentary
   - no decision label
   - no chat residue

## Output Format

For each integration round, report:

1. section assignment
2. alignment review
3. review decision
4. edits applied
5. where the Draft was updated

## Boundary Rules

- Do not directly modify chapter `tex` unless the user explicitly changes the task.
- Do not silently absorb text that conflicts with story or Writing.
- Do not turn a background section into a methods section.
- Do not accept unreviewed external text straight into the final write-back block.
- Do not mix multiple sections in one Draft block.

## Validation

After updating Draft, verify with commands like:

```bash
test -f "docs/Chapter X Draft.md"
rg -n 'Section heading|采用|采用（经修正后）|需改写|拒绝|最终可回写正文块' "docs/Chapter X Draft.md"
git status --short -- "docs/Chapter X Draft.md" "docs/This is Chapter X Writing.md" "<chapter-tex>"
```

Check that:

- the new section appears in the integration area
- the final write-back block is updated only when appropriate
- `tex` remains untouched unless explicitly approved

## Do Not

- do not skip ExecPlan when Draft will be edited
- do not rewrite multiple sections at once by default
- do not let current `tex` override newer story/workbench decisions
- do not turn representative prior-work wording into the thesis method claim
- do not write to `tex` during the integration phase unless the user explicitly authorizes that phase
