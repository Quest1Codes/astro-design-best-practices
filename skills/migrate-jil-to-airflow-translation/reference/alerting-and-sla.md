---
topic: alerting-and-sla
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2407, 2408]
last_verified: 2026-09-17
confidence: mixed
signals: [must_complete_times, svcdesk]
---

# Alerting and SLAs → callbacks, Deadline Alerts, Astro Observe

REWRITE ← the pre-refactor skill's `alerting-and-sla.md` (which was itself already stale —
Airflow's legacy per-task SLA keyword argument is removed in Airflow 3; this file never
references it). Deadline Alerts (3.1+) are the closest native replacement; verify their current
GA/experimental status against Astronomer's docs before committing a design to them
(`confidence: mixed` — this refactor did not have live MCP access).

| JIL attribute | Meaning | Airflow/Astro target | Disposition |
|---|---|---|---|
| `alarm_if_fail: 1` | Alert on failure [AS p.2408] | `on_failure_callback` on the task/DAG, wired to the shop's existing channel; or an Astro Alert if the target is Astro | MECH |
| `alarm_if_terminated: 1` | Distinguish "failed" from "terminated" [AS p.2408] | Airflow doesn't distinguish these the same way; both surface as task `failed`. NONE with a documented alternative: rely on the task's exception/log content, don't try to reconstruct AutoSys's exact taxonomy | NONE (documented alternative) |
| `alarm_if_success: 1` | Alert on success | `on_success_callback` / Astro Alert | MECH |
| `term_run_time` | Max allowed runtime before AutoSys kills the job | `execution_timeout` | MECH |
| `max_run_alarm` / `min_run_alarm` | Duration-based alarm thresholds | A callback measuring `ti.duration` against the threshold, or a Deadline Alert if its current capability covers duration-based triggers (verify) | JUDG |
| `must_start_times` / `must_complete_times` | Hard SLA deadlines [`autosys-reference/reference/scheduling-attributes.md`] | Deadline Alerts (3.1+, verify GA status), or a callback comparing `ti.end_date` against the deadline as a fallback | JUDG |
| `max_exit_success` / `success_codes` | Redefines what counts as SUCCESS [AS p.2437 note] | `BashOperator(skip_on_exit_code=...)` / custom exit-code handling in the task — **must** be translated consistently with any `exitcode()` condition on the same job (`reference/conditions-and-dependencies.md`), not independently | MECH/JUDG |
| `notification_msg` / notification emails | Alert content/routing on specific attributes | `on_failure_callback`/`on_success_callback`/`on_retry_callback`, or an Astro Alert rule | MECH |
| `svcdesk_*` attributes | ITSM ticket integration | Wire the callback/Astro Alert to the ITSM tool identified in `assess-astro-target-architecture`'s `alerting_itsm` decision | JUDG |
| Box-level `alarm_if_fail` | Alert on the box's overall failure, not any one child | A callback at the DAG level (box-as-a-whole), not per-task | JUDG — decide whether to also keep per-task alerts if operational practice actually pages on the specific child that failed |

## What to check before assuming parity

Alert *routing* (who gets paged, through which channel) is organizational configuration, not
recoverable from JIL alone — get the routing table from the platform team as a separate input
(`assess-estate-discovery/reference/stakeholder-questions.md`'s on-call-model question), not
inferred from the job definition. Wiring the actual integration is
`migrate-astro-platform-buildout/reference/alerting-and-observability-wiring.md`'s job, not this
skill's — this file only decides the per-job translation target.
