# Calendars and scheduling → Timetables

AutoSys schedules a job/box through a combination of attributes rather than a single cron string:

| JIL attribute | Meaning |
|---|---|
| `days_of_week` | e.g. `mo,tu,we,th,fr`, `all`, `last` (last day of month) |
| `start_times` | One or more `"HH:MM"` times per eligible day |
| `run_window` / `start_mins` | Interval-based scheduling within a window instead of fixed times |
| `run_calendar` | Name of a custom calendar (defined via a separate `insert_calendar:` block) — the job runs on `days_of_week` **intersected with** this calendar's dates (commonly a "business days" calendar) |
| `exclude_calendar` | Name of a calendar whose dates are subtracted from eligibility (commonly a holiday calendar) |
| `date_conditions: 1` | Turns on date-based scheduling at all (as opposed to being purely condition-triggered with no schedule of its own) |

## Translation approach

1. **Pure `days_of_week` + `start_times`, no calendars** → a standard cron expression, or Airflow's built-in weekday helpers. MECH.
2. **`run_calendar`/`exclude_calendar` present** → a custom `Timetable` subclass that encodes the calendar's date list (or computes it, if the calendar follows a rule like "US business days"). Do not try to force this into a cron string — cron cannot express arbitrary calendar exclusions. JUDG: decide whether the calendar's dates are static (hardcode/load from a data file shipped with the DAG) or computed (implement the holiday rule in code). Prefer loading from data if the source calendar was itself a maintained list — reproducing exact dates matters more than reproducing the reasoning behind them.
3. **`run_window`/interval-based** → Airflow doesn't have a direct "run every N minutes within this window" timetable out of the box; implement as a custom `Timetable` or, if the interval is simple (e.g., every 15 minutes between 06:00-18:00), a cron string with a time range is sometimes sufficient — verify against actual AutoSys behavior (does it run AT the window boundaries or only strictly between them?) before assuming equivalence.
4. **A box with `date_conditions: 1` whose children have no schedule of their own** → the schedule lives on the box/DAG; children are pure tasks with no independent Timetable.
5. **A job with no `date_conditions` and only a `condition:`** → purely event/dependency-driven, no schedule at all on the Airflow side either (`schedule=None`), triggered via the Dataset/TriggerDagRunOperator mechanism decided in `reference/conditions-and-dependencies.md`.

## Calendar data itself

If the JIL export includes `insert_calendar:` blocks with explicit date lists, extract them verbatim into a data file (e.g. `include/calendars/business_days.txt`) that the custom Timetable reads — do not hand-retype dates, and do not assume "business days" means the same thing as a generic Mon-Fri-minus-US-holidays calendar until the actual excluded dates are diffed against that assumption. Record any mismatch as an equivalence-row delta.

## What to verify, not assume

Exact calendar semantics (e.g., whether a job scheduled on an excluded date shifts to the next eligible day or simply doesn't run that cycle) vary by AutoSys configuration and are worth confirming against the customer's actual observed behavior (or `autorep -J <job> -q` history) rather than assumed from the attribute names alone.
