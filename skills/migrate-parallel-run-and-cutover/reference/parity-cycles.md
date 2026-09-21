---
topic: parity-cycles
family: migration
skill: migrate-parallel-run-and-cutover
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Parity cycles

## What is compared

Per `reconcile_runs.py`, joined via `traceability.json` (never by naming convention — plan
§11.7's own stated risk):

- **Status**: did the run reach the same terminal outcome (success/failure)?
- **Duration**: is the runtime within an acceptable delta of the AutoSys baseline
  (`--max-duration-delta-pct` on `parity_check.py`, reused here)?
- **Exit code**: does the exit code match, accounting for any `max_exit_success`/`success_codes`
  translation already applied?
- **Outputs** (where observable): file checksums/row counts, computed from the AutoSys run's own
  output, not re-derived independently — independent re-derivation can mask a bug present in both
  the old and new logic identically (same principle as
  `migrate-jil-to-airflow-translation/reference/validation.md`'s Gate 4).

## Thresholds by criticality

PRACTITIONER JUDGMENT — these are v1 starting points, not cited figures.

| Criticality signal | Min clean cycles before `go` |
|---|---|
| `MECH` disposition, no `sla`/`hitl` flags | 2 |
| `JUDG` disposition, or any `sla` flag | 3 |
| `REDESIGN` disposition, or `hidden_flow`/`multi_deployment` flags | 5, plus explicit sign-off from the job's owning team |
| Flagged `dead` or `dead_low_confidence` by `score_estate.py` | Confirm decommission candidacy directly with the platform team instead of running parity cycles at all — see `reference/decommission.md` |

## N cycles by schedule frequency

A "cycle" is one occurrence of the job's own actual schedule, not a fixed calendar period — a
monthly close job needs N *monthly* runs (N months of soak), not N runs squeezed into a shorter
window by re-triggering out of cadence. Re-triggering out of cadence tests the code, not the
real operational conditions (data volume/timing variance across a real cycle) that matter for a
genuine go/no-go call.

## Recording results

Each cycle's `reconcile_runs.py` output (`parity_cycle_<n>.json`) accumulates as
`cutover_gate.py`'s input — never discard a cycle's raw comparison once produced, even a clean
one; the go/no-go decision needs to see the whole run of clean cycles, not just a count.
