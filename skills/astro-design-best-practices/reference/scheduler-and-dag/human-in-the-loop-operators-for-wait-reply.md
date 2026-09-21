---
topic: human-in-the-loop-operators-for-wait-reply
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Human-in-the-Loop Operators for `WAIT_REPLY`

## The AutoSys starting point

AutoSys has three distinct mechanisms where a job's progress genuinely depends on a human, not
just another job's completion — all real, and none of them optional edge cases in an estate that
uses them:

- **`WAIT_REPLY` state**: a job can enter `WAIT_REPLY` and stay there until an operator issues a
  manual `REPLY_RESPONSE` event — per `autosys-reference/reference/job-states-and-events.md`, this
  is explicitly called out as **"the only state with no automated equivalent"** [AS p.2919].
  `REPLY_RESPONSE` itself is one of the state/priority-mutation `sendevent` calls
  (`autosys-reference/reference/commands.md`).
- **`ZOSM` (z/OS Manual)** job type [AS p.2549]: a mainframe job whose completion is confirmed
  manually rather than detected automatically — carries `auth_string` [AS p.2413],
  `search_btw` [AS p.2732], and `zos_jobname` [AS p.2853] attributes.
- **`PAREQ` (Process Automation Start Request Form)** job type [AS p.2551]: a Process Automation
  job driven by a request-form workflow, with `endpoint_URL` [AS p.2468] and the `pa_*` attribute
  family (`pa_monitor_progress`, `pa_name`, `pa_parameter`, `pa_path`, `pa_trace`) [AS p.2633-2636]
  — this is a forms-driven human-approval pattern, distinct from `WAIT_REPLY`'s simple
  wait-for-any-reply model.

## The Airflow-3 target

> RESOLVED: Airflow 3.1 introduced human-in-the-loop (HITL) task types (`ApprovalOperator`,
> `HITLOperator`) that pause a DAG run and wait for a human response before continuing — the direct
> structural analogue of `WAIT_REPLY`, confirmed via astronomer-docs (`learn/airflow-human-in-the-loop`).
> Response collection works through the Airflow UI or, for a human/entity without UI access, the
> REST API: `GET api/v2/hitlDetails/` (list pending actions), `GET api/v2/hitlDetails/{dag_id}/{dag_run_id}/{task_id}`
> (get one action's detail, including `options`/`params` for structured input), and
> `PATCH api/v2/hitlDetails/{dag_id}/{dag_run_id}/{task_id}` (submit a response — a second submission
> against an already-answered action returns `409`). Timeout/escalation configuration specifics
> remain **NEEDS_EXEC_CHECK** against the target Astro Runtime version — not covered in the
> astronomer-docs pages found this pass.

## Mapping table

| AutoSys mechanism | Airflow 3 HITL pattern | Notes |
|---|---|---|
| `WAIT_REPLY` / `REPLY_RESPONSE` | HITL task, single approve/reject or free-form response | Closest 1:1 — a task pauses, a human supplies the response, the DAG run continues down the path the response selects |
| `ZOSM` manual completion confirmation | HITL task gating the downstream dependency, with the actual mainframe execution handled by whatever this estate's z/OS boundary integration pattern is (see `mainframe-boundary-astro-side-architecture.md`) | The HITL task replaces the manual-confirmation step specifically, not the job execution itself |
| `PAREQ` request-form workflow | HITL task with structured (multi-field) input, or an external forms tool feeding a webhook that resumes the DAG | **Confirmed**: HITL responses support structured, multi-field input via the `params`/`params_input` fields on the `PATCH .../hitlDetails/...` response endpoint — `pa_parameter`'s name/value-pair shape maps onto this directly, not just a bare approve/reject |

## Design guidance

- **Don't default every manual-approval need to a HITL task without checking staleness risk**: a
  paused DAG run holding open for a human response has a different resource/timeout profile than a
  normal task — confirm the target Airflow version's HITL timeout/escalation behavior handles the
  estate's realistic response-time distribution (some `WAIT_REPLY` jobs in a real estate can sit for
  hours or days) before committing to it as the universal replacement.
- **Route the escalation, not just the wait**: AutoSys's `WAIT_REPLY` alone doesn't notify anyone —
  operators typically also relied on `alarm_if_fail`/monitoring dashboards to know a job was
  sitting in `WAIT_REPLY`. A HITL task's pause is silent the same way unless paired with an alert
  (`on_failure_callback-design-patterns.md`'s pattern, adapted to a "waiting on human" condition
  rather than a failure) — otherwise the migration silently drops the operational visibility that
  made `WAIT_REPLY` jobs actually get answered in the source system.
- **If the target Airflow version predates HITL support or the feature is still immature**, fall
  back to an external approval system (ticketing/ITSM, per `ticketing-and-itsm-integration-design.md`)
  triggering a downstream DAG or clearing a sensor, the same fallback pattern this KB uses
  elsewhere for immature-feature risk (see `dag-level-sla-and-catchup-backfill-policy.md`'s
  Deadline Alerts fallback guidance).

## Sources

- [AS p.2919] AutoSys 12.0 documentation — `WAIT_REPLY` job state (research/autosys-12.0/system-states.txt)
- [AS p.2549] AutoSys 12.0 documentation — `ZOSM` job type
- [AS p.2551] AutoSys 12.0 documentation — `PAREQ` job type
- [AS p.2413, p.2732, p.2853] AutoSys 12.0 documentation — `ZOSM` attributes (`auth_string`, `search_btw`, `zos_jobname`)
- [AS p.2468, p.2633-2636] AutoSys 12.0 documentation — `PAREQ`/`pa_*` attributes
- [P1] Project-internal — `skills/autosys-reference/reference/job-states-and-events.md`, `attributes.md`, `job-types.md`
- [B1] Astronomer Docs — Human-in-the-loop in Airflow (`ApprovalOperator`/`HITLOperator`, `hitlDetails` REST API endpoints): https://www.astronomer.io/docs/learn/airflow-human-in-the-loop (tier 1, confirmed via astronomer-docs verification)
- NEEDS_EXEC_CHECK — timeout/escalation configuration specifics on the target Astro Runtime version; not covered in the astronomer-docs pages found this pass.
