---
topic: cutover-runbook
family: migration
skill: migrate-parallel-run-and-cutover
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2912, 2915]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Cutover runbook

MERGE ← `migrate-topology-onprem-distributed/reference/cutover-waves.md`'s "Per-wave cutover
mechanics" and "What 'clean' means" sections (kept in full — the mechanics were already correct
and general, not onprem-specific despite where they used to live).

## Per-box cutover mechanics

1. Confirm the box passed `cutover_gate.py`'s go check (Phase 3) before scheduling a cutover
   date.
2. Put the AutoSys box `ON_ICE` at the agreed cutover time — **not `ON_HOLD`**. `ON_ICE`
   means dependents treat the box as if it succeeded (they proceed); `ON_HOLD` means dependents
   wait [`autosys-reference/reference/job-states-and-events.md`, AS p.2915]. Using the wrong one
   here either stalls unrelated downstream AutoSys work (`ON_HOLD` when `ON_ICE` was intended) or
   silently lets dependents proceed against a box that's actually paused, not succeeded
   (`ON_ICE` used carelessly on a box that hasn't actually been proven to succeed yet).
3. Unpause the corresponding Airflow DAG(s).
4. Repoint any inbound callers found during discovery (AEWS/REST callers, external
   `sendevent` callers — `assess-estate-discovery/reference/what-jil-cannot-tell-you.md`'s
   inbound-callers item) at the Airflow REST API. This step is easy to miss because it's
   organizationally, not technically, tracked — confirm explicitly with whoever owns each caller.
5. Rollback path (`reference/rollback.md`): `OFF_ICE` the AutoSys box, pause the Airflow DAG.
   Tested during Phase 2's rehearsal, not just described.
6. Only after the box has run clean in production for its agreed observation window
   (`reference/parity-cycles.md`'s cycle-count logic, now against live runs) does it move to
   `complete` in the `cutover` workflow — don't decommission the AutoSys definition until then.

## What "clean" means

Not just "didn't error." Confirm:

- **Output parity** (per `migrate-jil-to-airflow-translation/reference/validation.md`'s Gate 4,
  now executed from the actual production location).
- **Alerting actually fired correctly when tested** (platform validation Gate P5, re-confirmed
  in the real cutover context, not just the platform buildout's own test).
- **No downstream consumer was surprised** by a timing or format change — a wave that ran without
  exceptions but silently changed output shape is not clean.

## Sequencing across a wave

Cut boxes within a wave in dependency order (leaf boxes with no other wave-member depending on
them first), not all simultaneously — this bounds the blast radius of any single box's cutover
going wrong to that box alone, not the whole wave.
