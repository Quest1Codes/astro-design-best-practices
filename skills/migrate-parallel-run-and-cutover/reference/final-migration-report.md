---
topic: final-migration-report
family: migration
skill: migrate-parallel-run-and-cutover
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Final migration report

The migration-side counterpart to `assess-assessment-report`'s pre-migration deliverable —
written once the estate (or a wave of it) has actually been cut over and decommissioned, not
before. Structure (kept from the pre-refactor base skill's Phase 7, still accurate):

## Sections

1. **Every job/box's final disposition** — what it actually became, cross-referenced against
   `manifest.scores`'s original assessment-time disposition; note any that changed during
   translation (a JUDG unit that turned out to need REDESIGN, for instance) and why.
2. **All condition-string equivalence rows** — `translate_conditions.py`'s output, human-reviewed
   and finalized, not the first-draft recommendations.
3. **NONE/REDESIGN losses, stated plainly** — same discipline as the assessment report's Risk
   section: a REDESIGN item's actual delta from AutoSys behavior gets named specifically, not
   generalized into "some jobs needed custom handling."
4. **The calendar map** — which jobs ended up cron, which needed a Timetable, and the actual
   `include/calendars/*.txt` data files shipped.
5. **The deferred list, with reasons** — every unit still `deferred` at report time, per
   `_lib.autosys_jil.status`'s discipline (a `deferred` state always carries a reason).
6. **Parity evidence** — the parity-cycle history (`reference/parity-cycles.md`) that justified
   each box's `go` decision, not just the final "it passed."
7. **Decommission evidence** — per `reference/decommission.md`, confirmation of history archive,
   agent/EEM cleanup, and scream-test completion for every decommissioned box.

## What makes this different from the assessment report

The assessment report (`assess-assessment-report`) is a **prediction** — scores, effort
estimates, architecture recommendations, all made before any translation happened. This report is
an **account of what actually happened** — real parity data, real cutover dates, real deltas
discovered during translation that the assessment couldn't have predicted from JIL alone. Where
the two disagree (an estimated MECH job that turned out to need real judgment, an effort estimate
that proved too low), state the discrepancy explicitly — this is exactly the
kind of signal that should feed `research/effort-calibration/*.md` for the next engagement's
scoring-rule calibration (plan §11.9).
