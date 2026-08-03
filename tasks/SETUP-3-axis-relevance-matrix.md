# Task SETUP-3 — Axis Relevance Matrix

**Phase**: Setup (prerequisite — not one of the 130 numbered topic tasks)
**Priority**: P0 (blocking — every one of the 130 topic tasks reads this)
**Status**: MERGED

---

## Description

Before any topic file gets drafted, decide which of the 7 decision-table axes
(deployment model, estate scale, migration temporal strategy, org model,
vertical/compliance, executor/compute substrate, integration surface) actually
matter to which of the 19 `astro-design-best-practices` clusters (130 topics
total). Without this matrix, a per-topic pipeline run has no way to know which
axes its Researcher brief should cover — it would either ignore axes that
matter or waste effort researching axes that don't change the topic's guidance
at all.

## Deliverables

- The Axis Relevance Matrix in `tasks/README.md` (19 clusters × 7 axes, H/M/L rated)
- Priority rationale explaining why scheduler, executor, security, CI/CD
  topology, and regulatory-compliance clusters are P0

## Acceptance Criteria

- [x] Every cluster × axis cell is rated (no blanks — an unrated cell is
      indistinguishable from "forgot to check")
- [x] At least one cluster has an **H** rating on every axis somewhere (every
      axis has a "home" cluster — otherwise the matrix isn't doing any real
      work)
- [x] The matrix is referenced by name from `AGENTS.md`'s "How to Run the
      Pipeline" section, so a topic brief can point to it directly

## Dependencies

- SETUP-1

## References

- `tasks/README.md` — Axis Relevance Matrix section
- `AGENTS.md` — Design Principles #2 (the companion-skill vs. decision-table
  test that determined these 7 axes don't get their own skills)
