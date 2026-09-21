---
topic: scheduling-attributes
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2455, 2456, 2457, 2464, 2471, 2579, 2690, 2691, 2692, 2759, 2760, 2791, 2792]
last_verified: 2026-09-17
confidence: cited
signals: [calendar_not_cron, run_window, must_complete_times]
---

# Scheduling attributes

`_lib/autosys_jil/calendars.py` implements `eligible_dates()`/`expand()`/`cron_equivalent()`
against this grammar; `test_calendars.py` covers each rule below.

## `date_conditions` — the master switch [AS p.2455]

`date_conditions: y|n` (default `n`) controls whether AutoSys pays attention to *any* of:
`autocal_asc` calendars, `days_of_week`, `exclude_calendar`, `must_complete_times`,
`must_start_times`, `run_calendar`, `run_window`, `start_mins`, `start_times`, `timezone`. A job
with all of those set but `date_conditions: n` (or unset) simply ignores them all — this is a
common "why doesn't this job run on its documented schedule" root cause when reading raw JIL.

## `days_of_week` [AS p.2456-2457]

```
days_of_week: day [,day...]
days_of_week: all
```

Requires `start_times` or `start_mins` to also be set — `days_of_week` alone does not schedule
anything. **Has no effect when `run_calendar` is also set** [AS p.2456] — and per `run_calendar`'s
own page, specifying *both* `days_of_week` and `run_calendar` in the same job is documented to
make AutoSys **ignore both and raise an error** [AS p.2690]. Treat a job with both attributes set
as a defect to flag, not a schedule to trust.

Day values: `mo tue we th fr sa su` per the attribute's own option list [AS p.2456] — but the
PDF's own worked example on the same page writes `days_of_week: mo, tu, we, th, fr` (`tu`, not
`tue`) [AS p.2457], and every real customer export encountered by this project uses `tu`.
`_lib.calendars._DOW` accepts `tu` (matching real-world usage and the worked example), not `tue`
— note this if a customer's export happens to use the full `tue` spelling; the mapping in code
would need a one-line addition, not currently present.

## `start_times` / `start_mins` [AS p.2759-2760]

- `start_times: "HH:MM"[,...]` — explicit times of day.
- `start_mins: "MM"[,...]` — minutes-past-every-hour (e.g. `"0,15,30,45"` for a quarter-hourly
  job); combines with `run_window` to restrict which hours count.

## `run_window` [AS p.2691-2692]

Controls **only when a job may start**, not when it stops, and is **not itself a starting
condition** — a job still needs `date_conditions`/`days_of_week`/etc. or a `condition:` to become
eligible; `run_window` then narrows *when within eligibility* it's allowed to actually start.

```
run_window: "HH:MM-HH:MM"
```

May span midnight (e.g. `"23:00-02:00"`) but cannot exceed 24 hours. If the job becomes eligible
outside the window:

- Current time closer to the **next** window's start → AutoSys schedules a future `STARTJOB` for
  that window.
- Current time closer to the **previous** window's end → the job's status becomes `INACTIVE` for
  that cycle — it does not run today.

This distinction matters for a box: if `JobA` (run_window `02:00-04:00`) sits in a box that
starts at `04:05`, `JobA` goes `INACTIVE` and the box completes without it; if the box starts at
`16:05`, `JobA` gets a `STARTJOB` scheduled for `02:00` the *next* day and the box stays open
until then [AS p.2691, worked example]. A migration must decide, per job, whether this
"INACTIVE-and-skip vs. wait-until-tomorrow" behavior is deliberate SLA logic to preserve
(Deadline Alert + explicit skip) or an artifact to simplify away — this is not something
`translate_calendars.py` can decide for you.

## Calendars: `run_calendar` / `exclude_calendar` [AS p.2690, p.2471]

- `run_calendar: calendar_name` — the job runs on every date in the named custom calendar (at
  the times in `start_times`/`start_mins`, which **override** any time encoded in the calendar
  itself). The calendar must already exist, created via `autocal_asc` [AS p.2690] — this is why
  discovery must collect `autocal_asc -l` output, not assume `insert_calendar` blocks are present
  (see `assess-estate-discovery/reference/artifact-checklist.md`).
- `exclude_calendar: calendar_name` — removes dates from eligibility (e.g. a holiday calendar).
- Mutually exclusive with `days_of_week` (see above) — never both.

## `timezone` [AS p.2791-2792]

```
timezone: zone
```

Up to 50 characters (`a-zA-Z0-9/-_`, case-insensitive, no spaces/periods — colon-containing
values like `"IST-5:30"` must be quoted). Resolved against the `ujo_timezones` table, falling
back to the OS's own timezone database; if unresolved after 5 lookup attempts the job **fails**
[AS p.2792]. A job with no `timezone` set runs in the scheduler's own timezone, not UTC and not
necessarily the target machine's timezone [AS p.2791] — this is a common source of "the migrated
DAG fires an hour off" bugs if the Astro Deployment's `pendulum` timezone isn't set to match
explicitly per DAG. DST handling is per-zone (a job's configured zone may shift DST on a
different date than the scheduler's own zone) [AS p.2791-2792] — `calendars.expand()` flags
spring-forward gaps and fall-back overlaps explicitly rather than silently picking one instant.

## `must_start_times` / `must_complete_times` [AS p.2579 and analog]

SLA-style deadlines, not scheduling triggers — a job can be scheduled correctly and still breach
one. Feed directly into `history.sla_breaches()` (observed vs. declared) and, on the target side,
Deadline Alerts — see `migrate-jil-to-airflow-translation/reference/alerting-and-sla.md`.

## Manual override: hold instead of a run window [AS p.2691]

The PDF explicitly notes `sendevent`-driven `JOB_ON_HOLD`/`JOB_OFF_HOLD` as an *alternative* way
to block a job from starting during specific hours, instead of `run_window`. If discovery finds
scripted/scheduled `sendevent -E JOB_ON_HOLD` calls (a form of hidden control flow — see
`_lib.commands`), treat them as the estate's real run-window logic even where the JIL's own
`run_window` attribute is absent or looks unused.
