# Task 004 — Seed Source List

**Phase**: 0 — Repo Foundation
**Priority**: P0 (blocking all Phase 2 topic tasks)
**Status**: NOT STARTED

---

## Description

The Researcher agent's source-authority policy (`AGENTS.md` Design Principles #1)
ranks Astronomer official docs and Astro Runtime release notes as tier 1, Airflow
OSS docs/source as tier 2 — but "go find the official docs" is not a specific
enough brief for an autonomous research pass. This task curates the actual seed
URLs per topic so each Phase 2 Researcher run starts from known-good tier-1/2
sources instead of discovering them fresh (and possibly inconsistently) every time.

## Deliverables

- One seed-source list per Phase 2 topic (9 total), each listing:
  - Astronomer docs pages directly relevant to the topic
  - Astro Runtime release-notes sections relevant to the topic (for
    version-sensitive claims)
  - Airflow OSS docs pages / provider source repos relevant to the topic
- A short note per topic on where tier-1/2 coverage looks thin, so the
  Researcher brief can flag that gap proactively rather than discovering it
  mid-run

## Acceptance Criteria

- [ ] All 9 Phase 2 topics have a non-empty seed list
- [ ] Every seed URL is a real, current (not archived/deprecated) page —
      spot-checked before this task is marked done
- [ ] Thin-coverage topics are named explicitly, not silently absent

## Dependencies

- 003 (needs the relevance matrix to know which axes' sources to seed, not just
  the baseline topic's)

## References

- `AGENTS.md` — Design Principles #1 (source-authority tiers)
