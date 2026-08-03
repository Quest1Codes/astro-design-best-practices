# Task SETUP-5 — Tier-3 Partner Material Ingestion Path

**Phase**: Setup (prerequisite — not one of the 100 numbered topic tasks)
**Priority**: P1
**Status**: NOT STARTED

---

## Description

The Researcher's source-authority policy (`AGENTS.md` Design Principles #1)
treats Astronomer partner/SA material as tier 3 — usable, often the sharpest
real-world guidance available — but explicitly not web-crawlable, since it's
partner-gated content Quest1 has access to through the Astronomer relationship,
not the open internet. Without an explicit ingestion path, every Researcher run
will silently fall back to tiers 1/2/4 and never surface this material at all.

## Deliverables

- A defined manual-ingestion mechanism: where a human drops partner-material
  exports (PDF/deck/transcript) for the Researcher to read, e.g. a
  `research/partner-material/` intake folder
- Instructions in `.agents/researcher.md` updated (if needed) to point at this
  intake location as part of every topic brief, not just the open web

## Acceptance Criteria

- [ ] A concrete intake location exists and is documented
- [ ] `.agents/researcher.md` references it
- [ ] At least one topic's Researcher run demonstrates picking up a tier-3
      item from this path (can be validated alongside the first real Phase 2
      task, doesn't need to block SETUP completion on its own)

## Dependencies

- SETUP-3

## References

- `AGENTS.md` — Design Principles #1 (source-authority tiers, the tier-3 caveat)
