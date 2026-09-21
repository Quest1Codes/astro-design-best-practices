---
topic: rollback
family: migration
skill: migrate-parallel-run-and-cutover
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2915]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Rollback

## Procedure

The exact reverse of `reference/cutover-runbook.md`'s cut sequence:

1. Pause the Airflow DAG(s).
2. `OFF_ICE` the AutoSys box — this returns it to normal scheduling eligibility
   [`autosys-reference/reference/job-states-and-events.md`].
3. Repoint any inbound callers that were moved to the Airflow REST API back to their AutoSys-side
   entry point (AEWS, `sendevent`), reversing the cutover step that moved them.
4. Confirm the box actually resumes running on its normal AutoSys schedule — don't assume
   `OFF_ICE` alone is sufficient without checking the next scheduled run actually fires.

## Rehearsal (hard rule 2)

Rehearse this procedure **once per wave, before that wave's first `go`** — on a non-critical box
if possible, or as a dry run against the actual target box with both systems confirmed
idempotent-safe for the rehearsal window. A rollback procedure that has only ever been described,
never executed, is not a tested rollback path — this is exactly the same principle as
`migrate-jil-to-airflow-translation/reference/validation.md`'s Gate 5 (safe re-run), applied at
the cutover level instead of the per-task level.

## Rollback triggers

Define, before cutover, what actually triggers a rollback decision — don't leave this to be
decided under incident pressure. Reasonable defaults: a parity break discovered post-cutover that
wasn't caught during the shadow window, an alerting/observability gap that leaves the team blind
post-cutover, or an inbound-caller repointing that turns out to be incomplete. Record the trigger
reason in `_lib.autosys_jil.status`'s `deferred`-equivalent (`rolled-back(reason)`, this
workflow's deferred state) — never a silent revert.

## After a rollback

A rolled-back box returns to the wave-planning backlog (`assess-migration-complexity-scoring/reference/wave-planning.md`)
for re-attempt once the triggering issue is actually fixed — it does not silently disappear from
the migration's scope.
