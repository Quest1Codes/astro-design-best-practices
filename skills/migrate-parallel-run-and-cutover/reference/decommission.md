---
topic: decommission
family: migration
skill: migrate-parallel-run-and-cutover
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Decommission

Per plan §11.10 — a migration's final phase, gated separately from cutover itself: a box is
`complete` in AutoSys terms only once its history has been preserved for compliance, and either
its definition is actually deleted or an explicit decision to keep AutoSys read-only indefinitely
is recorded.

## History archive

Before deleting anything, confirm the required retention period (`nfr.compliance` answers from
`assess-estate-discovery/reference/stakeholder-questions.md`) and that
`archive_events`/`ujo_job_runs`/`ujo_event` history for the decommissioned box has actually been
archived per that requirement — see
`astro-design-best-practices/reference/regulatory-and-compliance/audit-trail-immutability-design.md`
for the target-side retention design this feeds into.

## Order of operations

1. Confirm the observation window (`reference/parity-cycles.md`/`reference/cutover-runbook.md`)
   is complete and clean.
2. Archive AutoSys run history for the box per the retention requirement above.
3. **EEM/agent uninstall order**: remove the box's EEM policies (if native security, remove
   `owner`/`permission` grants) before uninstalling any agent that was dedicated to running it —
   removing the agent first can leave orphaned EEM references.
4. Align with license end dates (`nfr.autosys_license_end` from discovery) if the decommission is
   part of a broader instance retirement, not just this one box.
5. WCC shutdown (if applicable — only when the entire instance, not just this box, is retiring).
6. DNS/firewall cleanup for any network path that existed solely to support this box's execution.
7. **Scream test**: leave the AutoSys job definition present but disabled (not deleted) for an
   agreed period after cutover, watching for anyone who still expected it to run — genuinely
   delete only after that period passes without incident
   (`astro-design-best-practices/reference/regulatory-and-compliance/data-retention-and-erasure-lifecycle-design.md`
   cluster covers the target-side equivalent).

## Recording

Advance to `decommissioned` in the `cutover` workflow only once every step above is actually
done, not just planned — `_lib.autosys_jil.status summary --workflow cutover` treats
`decommissioned` as terminal, same as `rolled-back(reason)`.
