# Multi-Timezone Distributed Agent Scheduling (autotimezone) → Airflow pendulum Timezone Design

AutoSys managed multi-timezone scheduling through the `autotimezone` command (which maintained the `ujo_timezones` table) and the per-job `timezone` JIL attribute. AutoSys agents ran in their local timezone; the scheduler translated job start times relative to the agent's timezone using IANA timezone name resolution [B1].

Airflow takes a different approach: **all internal timestamps are stored in UTC**. Timezone handling is the responsibility of the DAG author using the `pendulum` library.

## Core Difference: Scheduler Internal Time

| | AutoSys | Airflow |
|---|---|---|
| **Internal reference time** | Configurable via `autotimezone` (can be non-UTC) | Always UTC [B2] |
| **DST handling** | Automatic via IANA timezone names in JIL | Controlled via `pendulum` timezone-aware `datetime` objects [B2] |
| **Job timezone attribute** | `timezone: US/Eastern` in JIL | `start_date` with `pendulum.timezone("America/New_York")` [B2] |

## Migrating the JIL timezone Attribute

AutoSys JIL:
```
timezone: US/Eastern
start_times: "06:00"
```

Airflow equivalent:

```python
import pendulum

with DAG(
    dag_id="finance.gl.reconciliation.daily",
    schedule="0 6 * * *",  # 06:00 in the DAG's timezone context
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
):
```

The cron expression `0 6 * * *` is resolved as 06:00 **America/New_York** time (EST or EDT depending on DST) — Airflow converts to UTC for storage [B2].

> **Important**: Never use naive (timezone-unaware) `datetime` objects in DAG `start_date`. Always use `pendulum.datetime(..., tz="...")` or `pendulum.today("America/New_York")` [B2].

## DST Edge Cases

### Spring Forward (Gap) — Clocks Jump from 2:00 AM → 3:00 AM

A DAG scheduled at `2:30 AM America/New_York` will encounter a "non-existent" time on the spring-forward night. Airflow's cron scheduler (using `croniter` + `pendulum`) skips the gap and fires the run at the next valid time after 3:00 AM [B2].

**Mitigation**: If a task MUST run at a specific elapsed duration regardless of wall clock (e.g., exactly every 24 hours), use `schedule=timedelta(hours=24)` instead of a cron expression. `timedelta`-based schedules are DST-agnostic [B2].

### Fall Back (Overlap) — Clocks Repeat from 2:00 AM → 1:00 AM

A DAG scheduled at `1:30 AM America/New_York` would appear to have two valid 1:30 AM times on the fall-back night. Airflow avoids double-execution because `logical_date` is always UTC — the UTC timestamp is unique even when the wall-clock time repeats [B2].

## Multi-Timezone Agent Pattern (AutoSys autotimezone Equivalent)

If your migrated pipelines serve teams across multiple timezones, create **separate DAGs per timezone requirement** rather than trying to dynamically shift a single DAG's schedule:

- `finance.apac.report.daily` — `schedule="0 6 * * *", tz="Asia/Tokyo"`
- `finance.emea.report.daily` — `schedule="0 6 * * *", tz="Europe/London"`
- `finance.amer.report.daily` — `schedule="0 6 * * *", tz="America/New_York"`

Each runs at "06:00 local time" for its region without shared-timezone complexity.

## Sources

[B1] Broadcom AutoSys Documentation — `autotimezone` command, `ujo_timezones` table, per-job `timezone` JIL attribute, IANA timezone name support (accessed 2026-08-11)
[B2] Apache Airflow Docs — UTC internal storage, `pendulum` for timezone-aware `start_date`, cron DST gap handling, `timedelta` as DST-agnostic alternative (accessed 2026-08-11)
