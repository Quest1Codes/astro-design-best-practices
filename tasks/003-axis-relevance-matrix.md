# Task 003 — Axis Relevance Matrix

**Phase**: 0 — Repo Foundation
**Priority**: P0 (blocking — every Phase 2/3 task reads this)
**Status**: MERGED

---

## Description

Before any topic file gets drafted, decide which of the 7 decision-table axes
(deployment model, estate scale, migration temporal strategy, org model,
vertical/compliance, executor/compute substrate, integration surface) actually
matter to which of the 9 `astro-design-best-practices` topics. Without this
matrix, a per-topic pipeline run has no way to know which axes its Researcher
brief should cover — it would either ignore axes that matter or waste effort
researching axes that don't change the topic's guidance at all.

## Deliverables

- The Axis Relevance Matrix in `tasks/README.md` (9 topics × 7 axes, H/M/L rated)
- Priority rationale explaining why scheduler, executor, security, CI/CD
  topology, and regulatory-compliance are the P0 baseline topics

## Acceptance Criteria

- [x] Every topic × axis cell is rated (no blanks — an unrated cell is
      indistinguishable from "forgot to check")
- [x] At least one topic has an **H** rating on at least one axis (otherwise
      the matrix isn't doing any real work — every topic would just be
      baseline-only)
- [x] The matrix is referenced by name from `AGENTS.md`'s "How to Run the
      Pipeline" section, so a topic brief can point to it directly

## Dependencies

- 001

## References

- `tasks/README.md` — Axis Relevance Matrix section
- `AGENTS.md` — Design Principles #2 (the companion-skill vs. decision-table
  test that determined these 7 axes don't get their own skills)
