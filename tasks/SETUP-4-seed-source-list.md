# Task SETUP-4 — Seed Source List

**Phase**: Setup (prerequisite — not one of the 130 numbered topic tasks)
**Priority**: P0 (blocking all 130 topic tasks)
**Status**: NOT STARTED

---

## Description

The Researcher agent's source-authority policy (`AGENTS.md` Design Principles #1)
ranks Astronomer official docs and Astro Runtime release notes as tier 1, Airflow
OSS docs/source as tier 2 — but "go find the official docs" is not a specific
enough brief for an autonomous research pass. This task curates the actual seed
URLs per **cluster** (19 total, covering all 130 topics within them) so each
topic's Researcher run starts from known-good tier-1/2 sources instead of
discovering them fresh (and possibly inconsistently) every time.

## Deliverables

- One seed-source list per cluster (19 total), each listing:
  - Astronomer docs pages directly relevant to the cluster's topics
  - Astro Runtime release-notes sections relevant to the cluster (for
    version-sensitive claims)
  - Airflow OSS docs pages / provider source repos relevant to the cluster
- A short note per cluster on where tier-1/2 coverage looks thin, so a
  topic's Researcher brief can flag that gap proactively rather than
  discovering it mid-run

## Acceptance Criteria

- [ ] All 19 clusters have a non-empty seed list
- [ ] Every seed URL is a real, current (not archived/deprecated) page —
      spot-checked before this task is marked done
- [ ] Thin-coverage clusters are named explicitly, not silently absent

## Dependencies

- SETUP-3 (needs the relevance matrix to know which axes' sources to seed, not
  just each cluster's baseline)

## References

- `AGENTS.md` — Design Principles #1 (source-authority tiers)
