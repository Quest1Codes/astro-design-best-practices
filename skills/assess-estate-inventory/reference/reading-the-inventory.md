---
topic: reading-the-inventory
family: assessment
skill: assess-estate-inventory
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: practitioner-judgment
signals: []
---

# Reading the inventory

PRACTITIONER JUDGMENT throughout — these are pattern-recognition heuristics for interpreting
`inventory_stats.py`/`condition_graph.py`/`command_analysis.py`/`history_stats.py` output, not
independently verifiable facts. Record your interpretation in `manifest.notes.inventory`,
separately from the generated numbers themselves.

## Job-type histogram

- **> 20% `OM*` (OS monitor) job types** → a monitoring/infrastructure-watching culture; expect
  mostly `NONE`/`REDESIGN` dispositions for that slice (these don't belong in an orchestrator),
  and flag it as a stay-signal candidate for Prometheus/Datadog rather than a migration target.
- **High `FT`/`FW` share** → file-driven architecture; check `command_analysis.py`'s hidden
  control-flow edges closely, since file-watch-triggered chains often have manual restart
  patterns baked into operational habit that won't show up in JIL alone.
- **`SAP*`/`PS`/`OA*` presence** → route to `autosys-reference/reference/job-types.md`'s ERP
  family and flag early for a specialist review; these translations are rarely MECH.

## Attribute histogram

- **High `must_complete_times`/`must_start_times` usage** → SLA-mature estate; cross-check
  against `history_stats.py`'s `sla_breaches` — a large gap between "SLA attributes declared" and
  "SLA attributes actually met" is a finding worth stating plainly in the report, not softening.
- **High `job_load` usage with `priority >= 1`** → the estate genuinely load-balances; trust
  `max_load`/`job_load` arithmetic for sizing. Low usage → `max_load` is decorative; size from
  `history.concurrency_curve` instead (see `autosys-reference/reference/machines-load-and-resources.md`).

## Machine concentration

A small number of machines carrying a disproportionate share of jobs (check
`inventory_stats.machine_histogram`) are both a migration-wave anchor (many jobs move together)
and a risk concentration (any environment-specific issue on that machine blocks a large slice).
Cross-reference with `machine_load_pressure` for real (not just nominal) hot spots.

## Owner concentration ("bus factor")

A small number of `owner` values covering most jobs is an operational risk independent of the
migration itself — worth naming in the report's risk section, and a reason to over-invest in
documentation/runbooks for that owner's domain during cutover.

## Box depth distribution

Deeply nested boxes (depth ≥ 3) are harder to decompose cleanly into DAG/TaskGroup boundaries —
expect more `JUDG`-disposition boxes at depth, not more `MECH`. A box with only one child
(`single_child` in `box_metrics`) is often either legacy scaffolding (worth questioning whether it
should exist at all post-migration) or a placeholder for planned-but-never-added siblings.

## Condition shapes

From `condition_graph.py`'s edge kinds and `commands.leaves`' `shape` property (surfaced per-job
in the manifest, not the graph script itself):

- **High OR-condition count** → REDESIGN-heavy by the scoring rules (`cond.or_present: +3`) —
  these rarely map to a single Airflow trigger_rule cleanly.
- **Look-back conditions present** → needs a per-job decision (`ExternalTaskSensor` with
  `execution_date_fn` vs. an Asset with a time window) — never treat as MECH by default.
- **Cross-instance edges** → confirms genuine multi-instance topology; check `nfr.compliance`
  answers for whether that reflects a real organizational/regulatory boundary that should persist
  as separate Astro Deployments, or is incidental and could consolidate.

## Calendars

- **Low `cron_expressible` rate** (from `calendar_expand.py`) → expect significant Timetable
  authoring effort, not a quick cron mapping. State the rate plainly in the report; it's a direct
  effort-estimate input.
- **DST gap/overlap instants present** on a job → flag explicitly; a job whose schedule silently
  shifts an hour twice a year is a real operational surprise if not carried forward deliberately.

## Command interpreters and hidden control flow

- **`unknown` interpreter on a large fraction of jobs** → likely non-script commands (binary
  invocations, data file paths in `watch_file`) — not automatically a problem, but worth a manual
  spot-check on a sample before assuming coverage is fine.
- **Any hidden `sendevent` edges** → this is the "#1 source of surprise in migrations" per this
  project's own audit — treat every one as a real dependency edge for wave-planning purposes,
  equal weight to a JIL-visible `condition:`.
- **`template_clusters` with ≥ 5 members** → dag-factory / dynamic-task-mapping candidates; name
  them explicitly as an efficiency opportunity in the report, not just a translation detail.

## History (when collected)

- **Concurrency peaks far exceeding average** → size for the peak, not the average; a
  job-count-only estimate systematically under-sizes bursty estates.
- **Dead-job candidates** → cheapest possible migration outcome (decommission, don't translate);
  confirm with the platform team before finalizing, since "no run in window" can also mean
  "runs only on a specific rare trigger."
- **High manual-intervention counts concentrated on a few jobs/users** → strong REDESIGN/HITL
  signal, and a direct indicator of operational load that migration should actually reduce, not
  just replicate.

## What to ask the customer next

Any of the above that surprises you is worth a direct question before the report is finalized —
`inventory_stats.py`/`condition_graph.py` surface facts, but the estate's actual operational
culture (why 40% of jobs are `OMTF`, why one team owns everything) is something only the customer
can confirm.
