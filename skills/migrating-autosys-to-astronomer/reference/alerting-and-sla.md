# Alerting and SLAs → callbacks, Airflow SLAs, Astro Observe

| JIL attribute | Meaning | Airflow/Astro target |
|---|---|---|
| `alarm_if_fail: 1` | Raise an alarm/alert when the job fails | `on_failure_callback` on the task or DAG, wired to the shop's existing alert channel (email/Slack/PagerDuty/webhook); or an Astro Alert (Deployment-level or DAG-level) if the estate is on Astro | MECH |
| `alarm_if_terminate` (job killed/terminated abnormally) | Distinguish "failed" from "terminated" | Airflow doesn't distinguish these the same way; both surface as task FAILED state. Treat as NONE with a documented alternative: rely on the task's exception/log content to distinguish cause, don't try to reconstruct AutoSys's exact status taxonomy | NONE (documented alternative) |
| `term_run_time` (max allowed runtime before AutoSys kills the job) | Airflow task-level `execution_timeout` | MECH |
| `notification_msg` / notification emails on specific job attributes | `on_failure_callback`/`on_success_callback`/`on_retry_callback`, or an Astro Alert rule if available | MECH |
| Box-level `alarm_if_fail` | Alert on the DAG's overall failure state (a callback at the DAG level, not per-task), since a box's alarm is about the box as a whole, not any one child | JUDG — decide whether to also keep per-task alerts if operational practice actually pages on the specific child that failed, not just "the box failed" |
| SLA-style expectations (job expected to complete by a certain time, tracked informally or via a custom monitor job) | Airflow `sla` parameter (Airflow 3: SLA callbacks) or, more robustly, Astro Observe timeliness alerts | JUDG — Airflow's native SLA mechanism has known rough edges; for real SLA enforcement prefer Astro Observe if the target is Astro-hosted |

## What to check before assuming parity

Alert *routing* (who gets paged, through which channel) is organizational configuration, not something recoverable from JIL alone. The JIL export tells you *that* a job alerts; it does not tell you the current PagerDuty/email routing, which typically lives in AutoSys's notification configuration or WCC settings, not the job definition itself. Get the routing table from the platform team as a separate input rather than inferring it — this belongs in the platform-layer phase (SKILL.md Phase 5), not the job-translation phase.
