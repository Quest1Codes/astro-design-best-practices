---
topic: deadline-alerts-status-and-fallbacks
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals:
  - must_complete_times
---

# Deadline Alerts: Status and Fallbacks

This is the dedicated topic for Deadline Alerts — `dag-level-sla-and-catchup-backfill-policy.md`
introduces them alongside the `catchup` default change; `sla-miss-detection-and-escalation.md`
places them in the broader SLA-monitoring spectrum. This file is the single place that tracks
their maturity status and the AutoSys attribute mapping in one spot, so the other two files can
link here instead of repeating it.

## Current status

- The legacy per-task SLA parameter and its miss-callback hook were **removed in Airflow 3.0**,
  not merely deprecated [F1][F4].
- Deadline Alerts, their replacement, are **new in Airflow 3.1** [F1][F2]. A Deadline Alert is
  configured with a reference point, an interval, and a callback to run if the deadline is missed
  [F2].
- As of this KB's last verification pass, Deadline Alerts are still marked **experimental** and
  may change in future releases without warning [F2]. Callback-type support has been evolving
  quickly — `SyncCallback` support was added in Airflow 3.2, after an earlier draft of this KB
  incorrectly stated only asynchronous callbacks were supported [F2]. Given the pace of change,
  **re-verify the exact callback-type support and GA/experimental status against the specific
  target Astro Runtime's actual Airflow version** rather than trusting this file's snapshot.
- Official migration documentation exists specifically for moving from the legacy SLA model to
  Deadline Alerts, with examples designed to replicate old-SLA behavior [F3].

## Mapping from AutoSys's timing-expectation attributes

| AutoSys attribute | Meaning | Deadline Alerts mapping |
|---|---|---|
| `must_complete_times` [AS p.2576] | Job must complete by specific time(s) of day | Closest 1:1 — a Deadline Alert's reference point + interval can express "must complete by X," the same expectation `must_complete_times` encodes |
| `max_run_alarm` [AS p.2561] (default: no maximum set) | Alarm if the job runs longer than N minutes | Also a Deadline Alerts fit — a duration-based deadline from job start, rather than a fixed time-of-day deadline |
| `term_run_time` [AS p.2781] (default: 0, unlimited) | Job is force-terminated after N minutes | **Not** a Deadline Alerts mapping — this is an enforcement action (kill the job), not just an alert. No native Airflow equivalent forcibly kills a task purely on a duration timer independent of `execution_timeout`; use the task-level `execution_timeout` parameter for the enforcement half, and a Deadline Alert (or Astro Alerts duration alert) for the notification half — these are two different Airflow mechanisms doing two different jobs that `term_run_time` conflated into one AutoSys attribute |

## Fallbacks, by maturity risk

Given the experimental status, don't treat Deadline Alerts as the only translation target for
every AutoSys timing expectation. In order of preference if Deadline Alerts aren't mature enough
for the estate's reliability bar on the target Runtime:

1. **Astro Alerts** — platform-level Task Duration/Timeliness alerts, configured in the Astro UI,
   no code dependency on an experimental Airflow feature (`sla-miss-detection-and-escalation.md`'s
   monitoring-spectrum table).
2. **Astro Observe** — Data Freshness SLAs on a Data Product, for cases where the real business
   requirement is "this data must be fresh by X," not "this task must finish by X" — often a better
   fit for `must_complete_times` on jobs whose actual purpose is producing a downstream deliverable.
3. **A custom `on_failure_callback`/monitoring-based duration check** — the least preferred
   fallback, since it reimplements what Deadline Alerts and Astro Alerts already do, but viable as
   a stopgap if neither of the above meets the estate's requirement on the specific target Runtime
   version.

## Design guidance

Mark any unit whose translation depends on Deadline Alerts as `NEEDS_EXEC_CHECK` in this
project's own `translate_conditions.py`/scoring output until someone confirms Deadline Alerts'
current status on the actual target Astro Runtime — this file's status snapshot will drift as the
feature matures, and a `must_complete_times` job silently losing its timing alert because Deadline
Alerts turned out not to be available on the target Runtime is exactly the kind of regression this
project's `Risk` section discipline (`assess-assessment-report`) exists to catch before cutover,
not after.

## Sources

- [AS p.2576] AutoSys 12.0 documentation — `must_complete_times` attribute
- [AS p.2561] AutoSys 12.0 documentation — `max_run_alarm` attribute
- [AS p.2781] AutoSys 12.0 documentation — `term_run_time` attribute
- [F1] Apache Airflow docs — Migrating from SLA to Deadline Alerts (SLA removed in 3.0): https://airflow.apache.org/docs/apache-airflow/stable/howto/sla-to-deadlines.html (tier 2)
- [F2] Apache Airflow docs — Deadline Alerts (new in 3.1, experimental status, `SyncCallback` added in 3.2): https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html (tier 2)
- [F3] Apache Airflow docs — Migrating from SLA to Deadline Alerts (migration examples): same as F1 (tier 2)
- [F4] Apache Airflow docs — Upgrading to Airflow 3 (breaking-changes list, "SLAs: Deprecated and removed; replaced with Deadline Alerts"): https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html (tier 2)
- [P1] Project-internal — `skills/astro-design-best-practices/reference/scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md`, `observability-and-alerting/sla-miss-detection-and-escalation.md`
