---
topic: calendars-and-scheduling
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2456, 2690, 2691, 2692, 2759, 2791]
last_verified: 2026-09-17
confidence: mixed
signals: [calendar_not_cron, run_window, must_complete_times]
---

# Calendars and scheduling → Timetables

REWRITE ← the pre-refactor skill's `calendars-and-scheduling.md`. Full attribute reference:
`autosys-reference/reference/scheduling-attributes.md`. `scripts/translate_calendars.py` makes
the cron-vs-Timetable call **mechanically** via `_lib.autosys_jil.calendars.cron_equivalent()` —
never eyeball this decision; the function proves equivalence over a horizon, a human glancing at
`days_of_week`/`start_times` cannot.

## Translation approach

1. **`cron_equivalent()` returns non-`None`** → use the returned cron string directly. MECH.
   This only happens for `days_of_week` + `start_times`/`start_mins` schedules with no
   calendar/run_window involved — see that function's docstring for the exact conditions.
2. **`run_calendar`/`exclude_calendar` present** (almost always non-cron-expressible) → a custom
   `Timetable` subclass reading the calendar's date list from a data file
   (`include/calendars/<name>.txt`, emitted by `translate_calendars.py` from
   `_lib.autosys_jil.calendars.parse_autocal_asc()`'s output — **not** hand-retyped). Do not try
   to force this into a cron string; cron cannot express arbitrary calendar exclusions. JUDG:
   decide whether the calendar is static (load from the extracted data file — preferred, since
   reproducing exact dates matters more than reproducing the reasoning) or a genuine rule worth
   implementing in code (e.g. "last business day of month," confirmed via
   `_lib.autosys_jil.calendars.classify_calendar()`).
3. **`run_window` present** [AS p.2691-2692] → `run_window` is NOT a starting condition, only a
   start-time constraint layered on top of other eligibility — see
   `autosys-reference/reference/scheduling-attributes.md`'s worked box example (a job whose
   window has closed goes `INACTIVE` for that cycle; a job whose window hasn't opened yet gets a
   future `STARTJOB`). Airflow has no direct "may start only within this window" Timetable
   primitive — implement as a custom `Timetable`, or (for a simple, non-midnight-spanning window)
   a cron string with the window baked in, **only after verifying** whether AutoSys's own
   INACTIVE-and-skip-vs-wait-until-next-window behavior matters here or can be simplified away —
   this is a real semantic decision, not a formality.
4. **A box with `date_conditions: 1` whose children have no schedule of their own** → the
   schedule lives on the box/DAG; children are pure tasks with no independent Timetable.
5. **A job with no `date_conditions`, only a `condition:`** → purely event/dependency-driven,
   `schedule=None` on the Airflow side too, triggered via the Asset/`TriggerDagRunOperator`
   mechanism decided in `reference/conditions-and-dependencies.md`.

## `timezone` [AS p.2791-2792]

A job with no `timezone` set runs in the *scheduler's* timezone, not UTC and not necessarily the
target machine's — set `pendulum` timezone explicitly per DAG rather than relying on the Astro
Deployment's default matching by coincidence. DST handling is per-zone;
`_lib.autosys_jil.calendars.expand()` flags spring-forward gaps and fall-back overlaps in
`manifest.schedules[key]` — check those flags for every calendar-driven job before finalizing a
Timetable, since a schedule that silently shifts an hour twice a year needs a deliberate decision
(reproduce the shift, or normalize it away), not an accident of default behavior.

## `must_start_times` / `must_complete_times`

SLA-style deadlines layered on top of the actual trigger mechanism, not a scheduling trigger
themselves — see `reference/alerting-and-sla.md` for the Deadline Alert translation.

## Calendar data itself

If discovery collected `autocal_asc` export output (see `autosys-reference/reference/commands.md`),
`translate_calendars.py` extracts the exact date list into `include/calendars/<name>.txt` — never
hand-retype dates, and never assume "business days" means generically Mon-Fri-minus-US-holidays
until the actual dates are diffed against that assumption
(`_lib.autosys_jil.calendars.classify_calendar()` does this diff). Record any mismatch as an
equivalence-row delta.

## What to verify, not assume

Exact calendar semantics (does a job scheduled on an excluded date shift to the next eligible day
or simply not run that cycle) vary by configuration — confirm against the customer's actual
observed behavior (`autorep -J <job> -q` history, or `history_stats.py`'s output if collected)
rather than assumed from the attribute names alone.
