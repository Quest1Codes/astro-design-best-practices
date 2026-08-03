# Task 002 — Import Mentor-Authored Companion Skills

**Phase**: 0 — Repo Foundation
**Priority**: P0 (blocking)
**Status**: MERGED

---

## Description

The mentor had already authored 4 Claude-Code-style skills inside Shinro's tree, at
`shinro/apps/api/agents/autosys_astronomer/skills/autosys-astronomer-expert/skills/`
(a somewhat accidental nesting — they ended up under an unrelated report-narrative
skill's directory because that's where the folder already existed). Bring them into
this repo as the starting point, at the top level where they belong, so this repo is
the single home for all skill content going forward rather than split across two repos.

## Deliverables

- `skills/migrating-autosys-to-astronomer/` — base migration skill (SKILL.md, README.md, reference/, scripts/)
- `skills/migrating-autosys-k8s-to-astronomer/`
- `skills/migrating-autosys-mainframe-boundary-to-astro/`
- `skills/migrating-autosys-onprem-distributed-to-astro-cloud/`

All copied verbatim — no content changes in this task. `.DS_Store` files excluded.

## Acceptance Criteria

- [x] All 4 skill directories present under `skills/` at the top level (not nested under an unrelated skill's subfolder, unlike the Shinro copy)
- [x] Each retains its `SKILL.md`, `README.md`, `reference/*.md`, and `scripts/*.py` unchanged
- [x] No `.DS_Store` or other OS artifacts copied over

## Dependencies

- 001

## Follow-up

Shinro's copies at the old path should eventually be treated as the stale mirror once
this repo is established as canonical (per `AGENTS.md`'s "Key rule" in Repository
Structure) — not deleted as part of this task; that's a separate decision for whoever
owns the Shinro repo.

## References

- `shinro/apps/api/agents/autosys_astronomer/skills/autosys-astronomer-expert/skills/` (source)
