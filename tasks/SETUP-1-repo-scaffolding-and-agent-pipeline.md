# Task SETUP-1 — Repo Scaffolding + Agent Pipeline Definitions

**Phase**: Setup (prerequisite — not one of the 130 numbered topic tasks)
**Priority**: P0 (blocking)
**Status**: MERGED

---

## Description

Stand up `astro-migration-skills` as its own git repository, separate from `shinro` — this content is a reusable, partner-facing asset with its own release lifecycle, not something that should live buried inside one Shinro agent's Python package. Define the 4-stage content-generation pipeline (`Researcher → Human Source Check → Generator → Critic → Human Sign-off`) that every future topic file will go through, so no topic gets drafted as an ungrounded one-shot.

## Deliverables

- `AGENTS.md` — pipeline overview, repo structure, design principles (source-authority tiers, the companion-skill-vs-decision-table axis test, per-topic not per-axis pipeline runs), how-to-run instructions, context scoping per agent, failure handling, model assignment, definition of done
- `.agents/researcher.md` — sourced fact-sheet stage
- `.agents/generator.md` — drafts the reference file strictly from the fact-sheet
- `.agents/critic.md` — adversarial fact-check against the fact-sheet, fresh context
- `.agents/signoff-checklist.md` — human gate, executes any flagged execution-checkable claims
- `.gitignore` (`.work/` excluded — transient pipeline coordination, not the deliverable)
- Directory scaffold: `tasks/`, `research/`, `skills/`

## Acceptance Criteria

- [x] `git init` run, repo exists at `/Users/micheal/quest1works/astro-migration-skills`
- [x] `AGENTS.md` documents a pipeline with at least one automated adversarial-verification stage (not just research→generate)
- [x] Each `.agents/*.md` file has a distinct, non-overlapping responsibility — no stage both drafts and verifies
- [x] `AGENTS.md` explicitly states the axis classification test (workflow-changing → companion skill; recommendation-changing → decision table) so it isn't re-derived per topic
- [x] `.work/` is gitignored; `research/` (permanent fact-sheets) is not

## Dependencies

- None (first task)

## References

- Conversation history establishing: don't one-shot ungrounded content; two-stage research→generate has no verification step; the axis classification test; per-topic not per-axis pipeline scoping
