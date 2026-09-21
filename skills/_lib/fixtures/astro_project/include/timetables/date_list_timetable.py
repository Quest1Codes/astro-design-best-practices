"""Shipped once per Astro project by translate_calendars.py's Timetable stubs (spec §7.1).

A minimal custom Timetable that fires on an explicit list of dates read from a sibling
`include/calendars/<name>.txt` file (one `YYYY-MM-DD` or `MM/DD/YYYY` date per line) rather than
a cron expression -- the target for any AutoSys job whose calendar
`_lib.autosys_jil.calendars.cron_equivalent()` could not prove cron-equivalent.

Usage in a scaffolded DAG:

    from include.timetables.date_list_timetable import DateListTimetable

    @dag(schedule=DateListTimetable("include/calendars/some_job.txt"), catchup=False, ...)
    def some_job_dag():
        ...

NEEDS_EXEC_CHECK: this module was authored without a live Airflow 3.3 environment available to
import-check it (no `apache-airflow` installed in this session -- see skills/docs/HANDOFF.md §5
on missing tooling access). The `Timetable`/`DagRunInfo`/`DataInterval` API surface matches
Airflow's documented custom-timetable pattern as of this project's training-time knowledge, but
has not been verified against a real `astro dev parse`. Run `dag_quality_gate.py` against a real
project before trusting this file in production.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from airflow.timetables.base import DagRunInfo, DataInterval, Timetable


def _parse_date_line(line: str) -> date | None:
    line = line.strip()
    if not line:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(line, fmt).date()
        except ValueError:
            continue
    return None


class DateListTimetable(Timetable):
    """Fires once per date listed in `date_file_path`, at `fire_time` (default midnight UTC)."""

    def __init__(self, date_file_path: str, fire_time: str = "00:00"):
        self.date_file_path = date_file_path
        hh, mm = (int(x) for x in fire_time.split(":"))
        self._fire_hour, self._fire_minute = hh, mm
        self._dates = self._load_dates()

    def _load_dates(self) -> list[date]:
        path = Path(self.date_file_path)
        if not path.exists():
            return []
        dates = [d for d in (_parse_date_line(line) for line in path.read_text().splitlines()) if d]
        return sorted(set(dates))

    def _next_after(self, d: date) -> date | None:
        for candidate in self._dates:
            if candidate > d:
                return candidate
        return None

    def next_dagrun_info(self, *, last_automated_data_interval, restriction):
        if last_automated_data_interval is not None:
            last_date = last_automated_data_interval.end.date()
        elif restriction.earliest is not None:
            last_date = restriction.earliest.date() - timedelta(days=1)
        else:
            return None

        next_date = self._next_after(last_date)
        if next_date is None:
            return None
        if restriction.latest is not None and next_date > restriction.latest.date():
            return None

        from pendulum import DateTime, timezone as pendulum_tz
        start = DateTime(next_date.year, next_date.month, next_date.day,
                         self._fire_hour, self._fire_minute, tzinfo=pendulum_tz("UTC"))
        end = start.add(days=1)
        return DagRunInfo(run_after=end, data_interval=DataInterval(start=start, end=end))
