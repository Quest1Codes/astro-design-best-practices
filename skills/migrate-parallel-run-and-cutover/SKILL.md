---
name: migrate-parallel-run-and-cutover
description: Final phase of a migration — shadow mode, parity cycles, go/no-go, cutover, observation, rollback if needed, and decommission. Use once migrate-jil-to-airflow-translation has produced quality-gated DAGs and migrate-astro-platform-buildout has a validated platform. AutoSys stays authoritative until go, per box — this is the only phase of the whole migration family with real production blast radius.
---

# Parallel run and cutover

Promoted from a knowledge-base reference cluster to a phased skill this refactor (it was
previously prose-only guidance; the cutover *decision* — go or no-go — is now a deterministic
gate over real parity data, not a judgment call made from vibes). AutoSys stays authoritative
until a box is cut; rollback is always one step away and rehearsed, not assumed to work.

## Requirements

- Quality-gated DAGs from `migrate-jil-to-airflow-translation` (Gate 1-2 clean at minimum) for
  every unit in the wave being cut.
- A validated platform from `migrate-astro-platform-buildout` (gates P1-P6 passed).
- Read access to both AutoSys run history (ongoing, not just the assessment snapshot) and
  Airflow DAG run history for the units being compared.

## Hard rules

1. **AutoSys stays authoritative until `go`.** A shadowed/piloted DAG does not become the source
   of truth for anything downstream until the box has actually cut.
2. **Rollback is rehearsed once per wave before that wave's first `go`.** Not described,
   not assumed — actually exercised (`OFF_ICE` + pause DAG, or the reverse) and confirmed to
   work.
3. **No shared database between the two systems during coexistence.** AutoSys and the migrated
   DAGs write to their own state independently; do not have both systems mutate the same
   downstream table as if the other doesn't exist — this is how duplicate/conflicting writes
   happen during the parity window.
4. **One box/machine-group at a time**, per the wave plan — never the whole estate at once.

## Workflow

### Phase 1: Shadow mode

Deploy the wave's DAGs paused (or genuinely shadowed — running but not treated as authoritative)
per `reference/coexistence-modes.md`. AutoSys continues running unmodified.

### Phase 2: Parity cycles

```
python3 scripts/reconcile_runs.py --autosys-history runs.csv --airflow-runs airflow_runs.json \
    --trace traceability.json --cycle 1 --out parity_cycle_1.json
```

Run once per cycle (cadence per `reference/parity-cycles.md`, matched to the job's own schedule —
a monthly job needs a longer soak than a daily one). Compares status/duration/exit-code per job,
joined via `traceability.json`.

### Phase 3: Go/no-go

```
python3 scripts/cutover_gate.py --manifest estate_manifest.json --box <box_key> \
    --parity-cycles parity_cycle_1.json parity_cycle_2.json ... --min-clean-cycles 3
```

`go` only if: ≥N consecutive clean parity cycles (no unexplained deltas), all upstream boxes are
already `>= cut`, no open `deferred` children, and the rollback rehearsal for this wave is
recorded. Prints the checklist with pass/fail per condition; exit code for CI/gating.

### Phase 4: Cut

Per `reference/cutover-runbook.md`: `ON_ICE` the AutoSys box (dependents proceed as success —
this is deliberate, see `autosys-reference/reference/job-states-and-events.md`'s `ON_HOLD` vs.
`ON_ICE` distinction), unpause the Airflow DAG, repoint any inbound callers (AEWS/REST/
`sendevent` callers found during discovery) at the Airflow REST API.

### Phase 5: Observe

Watch the cut box run for an agreed number of live cycles before calling it `complete` — same
cadence logic as the parity-cycle count, now against real production runs instead of shadow runs.

### Phase 6: Rollback (if triggered)

Per `reference/rollback.md`: `OFF_ICE` the AutoSys box, pause the Airflow DAG. This reverses
Phase 4 exactly — if it doesn't cleanly reverse, the rehearsal (hard rule 2) should have caught
that before this was ever needed for real.

### Phase 7: Decommission

Per `reference/decommission.md`, once a box has run clean in production for its agreed
observation window: history archive for compliance, EEM/agent uninstall order, license
end-date alignment, WCC shutdown, DNS/firewall cleanup, and a "scream test" period. A box is not
`complete` until either its AutoSys definition is deleted or the estate-level decision to keep
AutoSys read-only indefinitely is explicitly recorded — no ambiguous middle state.

### Phase 8: Final migration report

Per `reference/final-migration-report.md`: dispositions, equivalence rows, losses, calendar map,
deferred list, parity evidence, decommission evidence — this is the migration-side counterpart to
`assess-assessment-report`'s pre-migration deliverable.

### Gate

`_lib.autosys_jil.status --manifest estate_manifest.json summary --workflow cutover` must exit 0
(every box `decommissioned` or `rolled-back(reason)`) before the migration is called done.

## Reference routing

| Question | Read |
|---|---|
| Shadow/paused/live coexistence modes | `reference/coexistence-modes.md` |
| What's compared, thresholds, cycle counts | `reference/parity-cycles.md` |
| Per-wave cutover mechanics, `ON_ICE` vs. `ON_HOLD`, inbound-caller repointing | `reference/cutover-runbook.md` |
| Rollback procedure | `reference/rollback.md` |
| Decommission steps | `reference/decommission.md` |
| Final report structure | `reference/final-migration-report.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/reconcile_runs.py` | One parity cycle: AutoSys vs. Airflow run comparison, joined via `traceability.json` |
| `scripts/cutover_gate.py` | Go/no-go checklist: N clean cycles, upstream readiness, rollback rehearsal recorded |
