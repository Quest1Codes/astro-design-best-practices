# Custom Timetable Design for AutoSys-Calendar Equivalents

The internal reference file `calendars-and-scheduling.md` already establishes *when* a JIL calendar (`run_calendar`/`exclude_calendar`) requires a custom Timetable rather than a cron string [P1]. This file covers how to actually build that Timetable well.

## Core mechanics

- A custom Timetable is Airflow's mechanism for scheduling logic that cron/`timedelta` cannot express — Airflow's own documentation names exactly the shapes AutoSys calendars produce: non-Gregorian-calendar schedules, rolling/overlapping data intervals, and schedules with "holes" between runs (which neither cron nor `timedelta` can represent, since both assume continuous intervals) [F1].
- To implement one, subclass `Timetable` and implement two methods: `next_dagrun_info` and `infer_manual_data_interval` [F2].
- Airflow's own guidance is explicit that you should *not* reach for a custom Timetable when a cron expression or `timedelta` is sufficient — it's a tool for the cases that genuinely can't be expressed those ways, not a default [F1].

## {syn: P1,F1,F2} Design guidance, extending the existing calendar-translation rules

The internal guidance already splits AutoSys calendars into "static date list, load from data" vs. "computed rule, implement in code" [P1]. Map that split onto the Timetable implementation directly:

| AutoSys calendar shape | Timetable implementation |
|---|---|
| Static, maintained date list (`insert_calendar:` block with explicit dates) [P1] | `next_dagrun_info` reads the date list from a data file shipped alongside the DAG (per P1's "extract verbatim, don't hand-retype" rule) — the Timetable class itself stays generic/reusable, and each calendar becomes a different data file, not a different class. |
| Computed rule (e.g. "US business days") [P1] | `next_dagrun_info` implements the rule directly — this is the one case where writing calendar logic in Python is appropriate rather than a data-loading concern. |
| `run_window`/interval-based scheduling [P1] | Custom Timetable, since Airflow has no built-in "every N minutes within a window" schedule shape [P1] — confirm against actual observed AutoSys behavior at the window boundary (inclusive/exclusive) before implementing, per P1's existing "verify, don't assume" guidance. |

## Reuse across the estate

Since `next_dagrun_info`/`infer_manual_data_interval` is the same two-method contract regardless of which specific calendar it encodes [F2], a single generic "date-list-driven Timetable" class that takes a data-file path as a constructor argument can serve every AutoSys calendar that's a static list — avoid writing one bespoke Timetable subclass per calendar name when the actual logic (read dates from a file, compute next eligible date) is identical across all of them. Reserve genuinely distinct Timetable subclasses for calendars whose *rule* differs (a computed holiday calendar vs. a static list), not for every differently-named calendar.

## Sources

- [F1] Apache Airflow docs — Timetables (when a custom Timetable is needed vs. cron/timedelta): https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html (tier 2)
- [F2] Apache Airflow docs — Customizing DAG Scheduling with Timetables (`next_dagrun_info`/`infer_manual_data_interval` contract): https://airflow.apache.org/docs/apache-airflow/stable/howto/timetable.html (tier 2)
- [P1] Project-internal — `skills/migrating-autosys-to-astronomer/reference/calendars-and-scheduling.md` (calendar→Timetable translation rules)
