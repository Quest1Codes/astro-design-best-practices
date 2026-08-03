# DAG-Level SLA and Catchup/Backfill Policy

Two version-sensitive Airflow 3 changes both directly affect how AutoSys's SLA-style job-timing expectations [P1] and JIL's implicit "don't run missed cycles" behavior translate — get the version right before designing either.

**Consistency conflict with an already-shipped file, flagged rather than silently worked around**: the imported `alerting-and-sla.md` [P1] currently states "Airflow 3: SLA callbacks" as the target for SLA-style expectations. That is now stale — [F1] confirms the SLA feature (including `sla_miss_callback`) was **removed** in Airflow 3.0, not merely carried forward as "SLA callbacks." This file's guidance below reflects the corrected, current state; `alerting-and-sla.md` needs its own follow-up correction, tracked separately rather than edited in-place here — see `## Sources` for both citations.

## Core mechanics — SLA is gone, replaced by Deadline Alerts

- The legacy SLA feature (`sla`, `sla_miss_callback`) was **removed in Airflow 3.0** [F1][F4] (Critic pass: the official breaking-changes page [F4] states this explicitly — "SLAs: Deprecated and removed; replaced with Deadline Alerts" — attaching it here alongside F1, which discusses the migration path but doesn't use the word "removed" as directly).
- It is replaced by **Deadline Alerts**, new in Airflow 3.1 [F1][F2]. A Deadline Alert is configured with a reference point, an interval, and a callback to run if the deadline is missed [F2].
- Deadline Alerts are explicitly marked **experimental** and may change in future releases without warning [F2]. **Corrected per Critic pass**: an earlier draft of this file stated they "currently support only asynchronous callbacks, with synchronous callback support planned but not yet available" — that is now out of date; current stable docs show `SyncCallback` support was added in Airflow 3.2 [F2]. Given the feature is still experimental and moving quickly, re-verify the exact callback-type support against the target Astro Runtime's actual Airflow version rather than trusting either this file's or the prior draft's snapshot.
- Official migration documentation exists specifically for moving from the legacy SLA model to Deadline Alerts, including examples designed to replicate old-SLA behavior [F3].

## Core mechanics — catchup default changed

- Airflow 3's new DAG defaults are `schedule=None` and `catchup=False` [F4] — a DAG with no explicit `catchup` setting will **not** backfill missed historical runs, which is a behavior change from Airflow 2.x defaults.
- `catchup_by_default` can be set back to `True` at the Airflow config level to restore the old default globally, if needed [F4].

## {syn: P1,F1,F2,F4} Design guidance

- **`alarm_if_fail`/notification-on-failure** [P1] → `on_failure_callback` (see the Observability & Alerting cluster) — this doesn't depend on SLA/Deadline Alerts at all and is unaffected by the removal.
- **SLA-style "job expected to complete by a certain time" expectations** [P1] → this is exactly the Deadline Alerts use case, not `on_failure_callback` — but given Deadline Alerts' explicit experimental status [F2], treat this as **`NEEDS_EXEC_CHECK`**: confirm on the actual target Astro Runtime version that Deadline Alerts are available and stable enough to rely on for production alerting before committing to them as the translation target; if the target version predates 3.1 or the feature is still too immature for the estate's reliability bar, [P1]'s existing fallback recommendation — prefer Astro Observe timeliness alerts over Airflow's own native mechanism — is the safer default regardless of which native mechanism (old SLA or new Deadline Alerts) is technically current.
- **Missed-cycle behavior**: AutoSys's calendar/schedule model doesn't retroactively "catch up" missed runs by default the way pre-3.0 Airflow could — so Airflow 3's new `catchup=False` default [F4] is actually the closer behavioral match to what an AutoSys estate is used to, not a regression. Explicitly setting `catchup=False` per DAG (rather than relying on the global default silently applying) is still good practice for auditability, even though it now matches the platform default.

## Sources

- [F1] Apache Airflow docs — Migrating from SLA to Deadline Alerts (SLA removed in 3.0): https://airflow.apache.org/docs/apache-airflow/stable/howto/sla-to-deadlines.html (tier 2)
- [F2] Apache Airflow docs — Deadline Alerts (new in 3.1, experimental status, async-only callbacks): https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html (tier 2)
- [F3] Apache Airflow docs — Migrating from SLA to Deadline Alerts (migration examples): same as F1 (tier 2)
- [F4] Apache Airflow docs — Upgrading to Airflow 3 (breaking-changes list): explicitly states "SLAs: Deprecated and removed; replaced with Deadline Alerts," and separately documents the catchup/`catchup_by_default` default change, `schedule=None`/`catchup=False` new defaults: https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html (tier 2) — corroborated on the catchup point by Astronomer's own upgrade checklist: https://www.astronomer.io/blog/upgrading-airflow-2-to-airflow-3-a-checklist-for-2026/ (tier 1)
- [P1] Project-internal — `skills/migrating-autosys-to-astronomer/reference/alerting-and-sla.md` (`alarm_if_fail` and SLA-style expectation source semantics) — **flagged stale**: its "Airflow 3: SLA callbacks" line contradicts [F1] and needs its own correction task; not fixed in this file, since that's a different file's content, not this one's.
