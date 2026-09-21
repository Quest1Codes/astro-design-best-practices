"""Calendars and schedule expansion.

Deterministic; no I/O (callers pass text).

Facts encoded:
  - `autocal_asc` manages custom calendars; `-l` lists dates one per line as MM/DD/YYYY
    (optional HH:MM) [AS commands: autocal_asc].
  - Scheduling attributes [AS p.2456 days_of_week; p.2758 start_times/start_mins; p.2690 run_window;
    p.2689 run_calendar; p.2464 exclude_calendar; p.2790 timezone; p.2455 date_conditions]:
      * `date_conditions: 1` enables date-based starts.
      * `days_of_week` (mo,tu,we,th,fr,sa,su | all) picks eligible weekdays.
      * `run_calendar` INTERSECTS eligibility with a custom calendar's dates.
      * `exclude_calendar` REMOVES dates.
      * `start_times` = explicit HH:MM list; `start_mins` = minutes past every hour;
        `run_window` restricts `start_mins` starts to a window.
      * `timezone` overrides the instance/server timezone for this job.
  - Cron cannot express arbitrary calendar dates; `cron_equivalent()` returns a cron string only
    when the expansion over the horizon is exactly reproduced by that cron.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import Calendar, Job

_DOW = {"su": 6, "mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5}
_DOW_CRON = {0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "0"}  # cron: 0=Sunday
_DATE_RES = [
    (re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+\d{1,2}:\d{2})?$"), "mdy"),
    (re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T]\d{1,2}:\d{2})?$"), "ymd"),
]


def parse_date_tokens(tokens: list[str]) -> list[date]:
    out: set[date] = set()
    for tok in tokens:
        t = tok.strip().strip('"')
        for rx, kind in _DATE_RES:
            m = rx.match(t)
            if not m:
                continue
            a, b, c = (int(m.group(i)) for i in (1, 2, 3))
            try:
                out.add(date(c, a, b) if kind == "mdy" else date(a, b, c))
            except ValueError:
                pass
            break
    return sorted(out)


def parse_autocal_asc(text: str, default_name: str | None = None) -> dict[str, Calendar]:
    """Parse `autocal_asc -l` style output. Supports multi-calendar dumps with `Calendar: NAME` headers."""
    cals: dict[str, list[str]] = {}
    current = default_name
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^(?:Calendar(?: Name)?|calendar)\s*[:=]?\s*(\S+)", s, re.I)
        if m and not re.match(r"^\d", s):
            current = m.group(1)
            cals.setdefault(current, [])
            continue
        if current is None:
            continue
        cals.setdefault(current, []).append(s)
    return {name: Calendar(name=name, dates=parse_date_tokens(toks), source="autocal_asc")
            for name, toks in cals.items()}


def classify_calendar(cal: Calendar, holidays: set[date] | None = None) -> str:
    """weekday_only | weekday_minus_holidays | month_end | month_start | arbitrary | empty."""
    if not cal.dates:
        return "empty"
    ds = cal.dates
    start, end = ds[0], ds[-1]
    span = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    weekdays = {d for d in span if d.weekday() < 5}
    if set(ds) == weekdays:
        return "weekday_only"
    if holidays and set(ds) == weekdays - holidays:
        return "weekday_minus_holidays"
    if all((d + timedelta(days=1)).day == 1 for d in ds):
        return "month_end"
    if all(d.day == 1 for d in ds):
        return "month_start"
    return "arbitrary"


def _tz(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or "UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def eligible_dates(job: Job, calendars: dict[str, Calendar], start: date, end: date) -> list[date]:
    s = job.schedule
    if not s.date_conditions:
        return []
    dows = set(range(7)) if "all" in s.days_of_week else {_DOW[d] for d in s.days_of_week if d in _DOW}
    if not s.days_of_week and s.run_calendar:
        dows = set(range(7))
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    out = [d for d in days if d.weekday() in dows]
    if s.run_calendar:
        cal = calendars.get(s.run_calendar)
        allowed = set(cal.dates) if cal else set()
        out = [d for d in out if d in allowed]
    if s.exclude_calendar:
        cal = calendars.get(s.exclude_calendar)
        excl = set(cal.dates) if cal else set()
        out = [d for d in out if d not in excl]
    return out


def _times_for_day(job: Job) -> list[time]:
    s = job.schedule
    times: list[time] = []
    for hhmm in s.start_times:
        h, m = hhmm.split(":")
        times.append(time(int(h), int(m)))
    if s.start_mins:
        lo, hi = (0, 23)
        if s.run_window:
            lo = int(s.run_window[0].split(":")[0])
            hi = int(s.run_window[1].split(":")[0])
        hours = range(lo, hi + 1) if lo <= hi else list(range(lo, 24)) + list(range(0, hi + 1))
        for h in hours:
            for m in s.start_mins:
                times.append(time(h, m))
    return sorted(set(times))


def expand(job: Job, calendars: dict[str, Calendar], start: date, end: date,
           default_tz: str | None = None) -> dict:
    """Concrete run instants and DST flags for [start, end]."""
    tzname = job.schedule.timezone or default_tz or "UTC"
    tz = _tz(tzname)
    instants: list[datetime] = []
    dst_gap: list[str] = []
    dst_overlap: list[str] = []
    for d in eligible_dates(job, calendars, start, end):
        for t in _times_for_day(job):
            naive = datetime.combine(d, t)
            aware = naive.replace(tzinfo=tz)
            # gap: local time does not exist (spring forward) -> fold-insensitive check
            back = aware.astimezone(ZoneInfo("UTC")).astimezone(tz)
            if back.replace(tzinfo=None) != naive:
                dst_gap.append(naive.isoformat())
            elif aware.replace(fold=1).utcoffset() != aware.utcoffset():
                dst_overlap.append(naive.isoformat())
            instants.append(aware)
    return {
        "timezone": tzname,
        "count": len(instants),
        "first": instants[0].isoformat() if instants else None,
        "last": instants[-1].isoformat() if instants else None,
        "instants": [i.isoformat() for i in instants],
        "dst_gap_instants": dst_gap,
        "dst_overlap_instants": dst_overlap,
    }


def cron_equivalent(job: Job, calendars: dict[str, Calendar], start: date, end: date) -> str | None:
    """Return a cron string that reproduces the expansion exactly, else None.

    Only weekday-based schedules with explicit start_times (or start_mins without run_window)
    are cron-expressible; any run_calendar/exclude_calendar makes it non-expressible unless
    the calendar happens to equal the weekday set (checked by expansion equality)."""
    s = job.schedule
    if not s.date_conditions or not (s.start_times or s.start_mins):
        return None
    expected = {i for i in expand(job, calendars, start, end)["instants"]}
    dows = set(range(7)) if "all" in s.days_of_week else {_DOW[d] for d in s.days_of_week if d in _DOW}
    if not dows:
        return None
    dow_field = "*" if len(dows) == 7 else ",".join(_DOW_CRON[d] for d in sorted(dows))
    candidates: list[str] = []
    if s.start_times and not s.start_mins:
        hours = sorted({int(t.split(":")[0]) for t in s.start_times})
        mins = sorted({int(t.split(":")[1]) for t in s.start_times})
        if len(hours) * len(mins) == len(s.start_times):
            candidates.append(f"{','.join(map(str, mins))} {','.join(map(str, hours))} * * {dow_field}")
    elif s.start_mins and not s.start_times and not s.run_window:
        candidates.append(f"{','.join(map(str, sorted(s.start_mins)))} * * * {dow_field}")
    for cron in candidates:
        if _cron_fire_set(cron, job, start, end) == expected:
            return cron
    return None


def _cron_fire_set(cron: str, job: Job, start: date, end: date) -> set[str]:
    mins_f, hours_f, _, _, dow_f = cron.split()
    mins = [int(x) for x in mins_f.split(",")]
    hours = list(range(24)) if hours_f == "*" else [int(x) for x in hours_f.split(",")]
    dows = set(range(7)) if dow_f == "*" else {k for k, v in _DOW_CRON.items() if v in dow_f.split(",")}
    tz = _tz(job.schedule.timezone)
    out: set[str] = set()
    d = start
    while d <= end:
        if d.weekday() in dows:
            for h in hours:
                for m in mins:
                    out.add(datetime.combine(d, time(h, m)).replace(tzinfo=tz).isoformat())
        d += timedelta(days=1)
    return out
