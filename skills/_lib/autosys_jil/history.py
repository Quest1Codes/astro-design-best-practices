"""Run-history and operational-data analysis [plan §11.1] -- the *runtime* surface a JIL export
alone cannot see: what actually ran, how often it failed, who intervened manually, and whether
SLA attributes reflect reality.

Deterministic; reads files only (callers pass text/rows).

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §1.8 (history.py spec)
  - PDF p.2353-2366 "autorep Command" (`research/autosys-12.0/commands.txt`): summary-report
    columns `Job Name / Last Start / Last End / ST/Ex / Run/Ntry / Pri-Xit` [AS p.2360-2362],
    ST abbreviations [AS p.2361], ES (event state) abbreviations [AS p.2362]. The worked
    examples on those pages are reflowed for print (PDF pagination wraps columns mid-row); the
    parsers below target real, unwrapped `autorep` CLI output -- confirmed flat (no indentation
    nesting: a box's own summary report lists box + every descendant job as sibling rows)
    against the p.2363-2364 `Nightly_Download`/`nebox` examples.
  - plan §11.1: DBA CSV exports of `ujo_job_runs`/`ujo_event`/`ujo_proc_event` are the more
    robust input for a real estate (column names vary by DBA export -- `columns_map` handles
    that); the `-r`/`-d` text-report parsers below are a best-effort fallback when only CLI
    output was collected, and are less robust than the CSV path for exactly that reason.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

# ST column abbreviations -> full state name [AS p.2361].
ST_ABBREV = {
    "AC": "ACTIVATED", "FA": "FAILURE", "IN": "INACTIVE", "NE": "ON_NOEXEC",
    "OH": "ON_HOLD", "OI": "ON_ICE", "PE": "PEND_MACH", "QU": "QUE_WAIT",
    "RE": "RESTART", "RU": "RUNNING", "RW": "RESWAIT", "ST": "STARTING",
    "SU": "SUCCESS", "SP": "SUSPENDED", "TE": "TERMINATED",
}
# ES (event state) column abbreviations [AS p.2362].
ES_ABBREV = {"ER": "Error", "PD": "Processed", "PG": "Processing", "UP": "Unprocessed", "US": "Unsent"}

# Manual-intervention events [plan §11.1]: operator actions that bypass the schedule.
MANUAL_INTERVENTION_EVENTS = {
    "FORCE_STARTJOB", "KILLJOB", "CHANGE_STATUS", "JOB_ON_ICE", "JOB_ON_HOLD",
    "JOB_OFF_ICE", "JOB_OFF_HOLD", "JOB_ON_NOEXEC", "JOB_OFF_NOEXEC",
}

_TS_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}")
_SUMMARY_HEADER_RE = re.compile(r"^Job Name\s+Last Start\s+Last End\s+ST/Ex\s+Run/Ntry", re.I)
_EVENT_HEADER_RE = re.compile(r"^Status/\[Event\]\s+Time\s+Ntry\s+ES", re.I)
_UNDERSCORE_LINE_RE = re.compile(r"^[_\s]+$")
_DASH_LINE_RE = re.compile(r"^[-\s]+$")


def _parse_ts(token: str) -> datetime | None:
    if not token or token.strip("-") == "":
        return None
    try:
        return datetime.strptime(token.strip(), "%m/%d/%Y %H:%M:%S")
    except ValueError:
        return None


def _column_spans(sep_line: str, fill_char: str) -> list[tuple[int, int]]:
    """autorep sizes each column to the widest value AT GENERATION TIME (confirmed against two
    real examples in [AS p.2363-2364] with different column widths for the same report type),
    so a value can exactly fill its column with no inter-column whitespace to split on. The
    underscore ('_', summary reports) or dash ('-', event tables) separator line is generated
    to match those exact widths -- use it to derive fixed column offsets, then slice every data
    row in *this* report by those offsets. The final column's span is extended to end-of-line."""
    spans = [(m.start(), m.end()) for m in re.finditer(re.escape(fill_char) + r"+", sep_line)]
    if spans:
        spans[-1] = (spans[-1][0], 10_000)
    return spans


def _slice_cols(line: str, spans: list[tuple[int, int]]) -> list[str]:
    return [line[a:b].strip() for a, b in spans]


def _split_cols(line: str) -> list[str]:
    """Fallback splitter (no known column spans): runs of >=2 spaces are boundaries. Used only
    when a fixed-width separator line was not found (e.g. a hand-trimmed snippet in a test)."""
    return [c for c in re.split(r"\s{2,}", line.strip()) if c != ""]


@dataclass(slots=True)
class Run:
    job: str
    run_num: int | None
    ntry: int | None
    start: datetime | None
    end: datetime | None
    status: str | None  # canonical state name (ST_ABBREV resolved)
    exit_code: int | None
    machine: str | None = None
    exec_mode_noexec: bool = False  # True when ST/Ex carried the "/NE" suffix

    def as_dict(self) -> dict:
        return {
            "job": self.job, "run_num": self.run_num, "ntry": self.ntry,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "status": self.status, "exit_code": self.exit_code, "machine": self.machine,
            "exec_mode_noexec": self.exec_mode_noexec,
        }


@dataclass(slots=True)
class Event:
    job: str
    event: str
    status: str | None
    time: datetime | None
    source_user: str | None = None
    source_host: str | None = None
    machine: str | None = None
    note: str | None = None

    def as_dict(self) -> dict:
        return {
            "job": self.job, "event": self.event, "status": self.status,
            "time": self.time.isoformat() if self.time else None,
            "source_user": self.source_user, "source_host": self.source_host,
            "machine": self.machine, "note": self.note,
        }


def _parse_summary_row(cols: list[str]) -> Run | None:
    # Job Name | Last Start | Last End | ST/Ex | Run/Ntry | [Pri/Xit]
    if len(cols) < 5 or not cols[0]:
        return None
    job, start_tok, end_tok, st_ex, run_ntry = cols[0], cols[1], cols[2], cols[3], cols[4]
    exit_tok = cols[5] if len(cols) > 5 else None
    m = re.match(r"^(\d+)/(\d+)$", run_ntry)
    if not m:
        return None
    run_num, ntry = int(m.group(1)), int(m.group(2))
    noexec = st_ex.endswith("/NE")
    st_code = st_ex[:-3] if noexec else st_ex
    status = ST_ABBREV.get(st_code)
    exit_code = int(exit_tok) if exit_tok and re.fullmatch(r"-?\d+", exit_tok) else None
    return Run(job=job, run_num=run_num, ntry=ntry, start=_parse_ts(start_tok), end=_parse_ts(end_tok),
              status=status, exit_code=exit_code, exec_mode_noexec=noexec)


def parse_autorep_r(text: str) -> list[Run]:
    """Parse an `autorep -J x -r -N` / plain summary report: one row per job (a box's report
    lists the box and every descendant job as flat sibling rows -- see module docstring)."""
    runs: list[Run] = []
    lines = text.splitlines()
    spans: list[tuple[int, int]] | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if _SUMMARY_HEADER_RE.match(line.strip()):
            # the next non-blank line is the underscore separator that fixes this report's
            # column widths for every data row that follows, until a new header appears.
            if i + 1 < len(lines) and _UNDERSCORE_LINE_RE.match(lines[i + 1]) and lines[i + 1].strip():
                spans = _column_spans(lines[i + 1], "_")
                i += 2
                continue
            spans = None
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        cols = _slice_cols(line, spans) if spans else _split_cols(line)
        run = _parse_summary_row(cols)
        if run is not None:
            runs.append(run)
        i += 1
    return runs


def parse_autorep_d(text: str) -> tuple[list[Run], list[Event]]:
    """Parse an `autorep -J x -d` detail report: job summary rows plus, for each job, its
    `Status/[Event]` event timeline. Best-effort (see module docstring); a DBA CSV export of
    the event archive is the more robust input for production use."""
    runs: list[Run] = []
    events: list[Event] = []
    current_job: str | None = None
    summary_spans: list[tuple[int, int]] | None = None
    event_spans: list[tuple[int, int]] | None = None
    in_event_table = False
    # A multi-job -d report ([AS p.2364] Nightly_Download/Watch_4_file/filter_data/... example)
    # prints the "Job Name/.../Pri-Xit" header only ONCE; later jobs' summary rows appear at the
    # SAME (shallower) indentation as the first one, with no repeated header -- while each job's
    # own event table is indented one level DEEPER. Indentation depth is therefore the signal
    # that tells a bare summary row apart from a continuing event-table row once in_event_table
    # is already True. job_indent/event_indent capture each table's leading-whitespace width.
    job_indent: int | None = None
    event_indent: int | None = None

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if _SUMMARY_HEADER_RE.match(s):
            in_event_table = False
            job_indent = indent
            if i + 1 < len(lines) and _UNDERSCORE_LINE_RE.match(lines[i + 1]) and lines[i + 1].strip():
                summary_spans = _column_spans(lines[i + 1], "_")
                i += 2
                continue
            summary_spans = None
            i += 1
            continue
        if _EVENT_HEADER_RE.match(s):
            in_event_table = True
            event_indent = indent
            if i + 1 < len(lines) and _DASH_LINE_RE.match(lines[i + 1]) and lines[i + 1].strip():
                event_spans = _column_spans(lines[i + 1], "-")
                i += 2
                continue
            event_spans = None
            i += 1
            continue
        if s.startswith("<"):
            if events:
                events[-1].note = s.strip("<>").strip()
            i += 1
            continue

        # Back at (or shallower than) job-row indentation while inside an event table -> this
        # is the next job's summary row, not a continuing event row (no header was reprinted).
        if in_event_table and job_indent is not None and (event_indent is None or indent < event_indent) \
                and indent <= job_indent:
            in_event_table = False

        if not in_event_table:
            cols = _slice_cols(line, summary_spans) if summary_spans else _split_cols(line)
            run = _parse_summary_row(cols)
            if run is not None:
                runs.append(run)
                current_job = run.job
                job_indent = indent
            i += 1
            continue

        # event-table row, possibly a bracketed system/alarm annotation e.g. "[JOBFAILURE] ..."
        cols = _slice_cols(line, event_spans) if event_spans else _split_cols(line)
        if current_job and cols and cols[0]:
            event_name = cols[0].strip("[]")
            time_tok = cols[1] if len(cols) > 1 else ""
            es_tok = cols[3] if len(cols) > 3 else None
            machine = cols[5] if len(cols) > 5 else None
            status = ES_ABBREV.get(es_tok, es_tok) if es_tok else None
            events.append(Event(job=current_job, event=event_name, status=status,
                                time=_parse_ts(time_tok), machine=machine or None))
        i += 1
    return runs, events


def parse_event_archive_csv(path: Path | str, columns_map: dict[str, str] | None = None) -> list[Event]:
    """Parse a DBA CSV export of `ujo_event`/`ujo_proc_event` [plan §11.1].

    `columns_map` maps our field names to the CSV's actual header names (DBAs export
    differently); defaults assume a CSV already using our field names:
    job, event, status, time, source_user, source_host, machine.
    """
    cmap = columns_map or {}

    def col(row: dict, field_name: str) -> str | None:
        return row.get(cmap.get(field_name, field_name))

    events: list[Event] = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            events.append(Event(
                job=col(row, "job") or "", event=col(row, "event") or "",
                status=col(row, "status"), time=_parse_ts(col(row, "time") or ""),
                source_user=col(row, "source_user"), source_host=col(row, "source_host"),
                machine=col(row, "machine"),
            ))
    return events


def parse_run_history_csv(path: Path | str, columns_map: dict[str, str] | None = None) -> list[Run]:
    """Parse a DBA CSV export of `ujo_job_runs` [plan §11.1]. Same `columns_map` convention."""
    cmap = columns_map or {}

    def col(row: dict, field_name: str) -> str | None:
        return row.get(cmap.get(field_name, field_name))

    runs: list[Run] = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            run_num = col(row, "run_num")
            ntry = col(row, "ntry")
            exit_code = col(row, "exit_code")
            runs.append(Run(
                job=col(row, "job") or "",
                run_num=int(run_num) if run_num and run_num.strip().lstrip("-").isdigit() else None,
                ntry=int(ntry) if ntry and ntry.strip().lstrip("-").isdigit() else None,
                start=_parse_ts(col(row, "start") or ""), end=_parse_ts(col(row, "end") or ""),
                status=col(row, "status"),
                exit_code=int(exit_code) if exit_code and exit_code.strip().lstrip("-").isdigit() else None,
                machine=col(row, "machine"),
            ))
    return runs


# ============================================================================ stats

def _percentile(sorted_vals: list[float], pct: float) -> float | None:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * pct
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def job_stats(runs: Iterable[Run]) -> dict[str, dict]:
    """Per-job: run count, p50/p95/max duration (seconds), failure rate, retry rate, last run,
    exit-code histogram [spec §1.8]."""
    by_job: dict[str, list[Run]] = {}
    for r in runs:
        by_job.setdefault(r.job, []).append(r)
    out: dict[str, dict] = {}
    for job, job_runs in by_job.items():
        durations = sorted(
            (r.end - r.start).total_seconds() for r in job_runs if r.start and r.end and r.end >= r.start
        )
        failures = sum(1 for r in job_runs if r.status in ("FAILURE", "TERMINATED"))
        retries = sum(1 for r in job_runs if (r.ntry or 0) > 1)
        last_run = max((r.end or r.start for r in job_runs if r.end or r.start), default=None)
        exitcodes = Counter(r.exit_code for r in job_runs if r.exit_code is not None)
        out[job] = {
            "count": len(job_runs),
            "p50_duration_s": _percentile(durations, 0.50),
            "p95_duration_s": _percentile(durations, 0.95),
            "max_duration_s": max(durations) if durations else None,
            "failure_rate": failures / len(job_runs) if job_runs else 0.0,
            "retry_rate": retries / len(job_runs) if job_runs else 0.0,
            "last_run": last_run.isoformat() if last_run else None,
            "exitcode_hist": {str(k): v for k, v in exitcodes.items()},
        }
    return out


def concurrency_curve(runs: Iterable[Run], bucket: str = "1min") -> dict[str, int]:
    """Number of jobs with an open [start, end) interval in each time bucket.

    `bucket` is `1min` or `1hour`. Returns {bucket_start_isoformat: concurrent_count}, dense
    (every bucket between the earliest start and latest end is present, zeros included) so a
    consumer can plot a continuous curve.
    """
    delta = timedelta(minutes=1) if bucket == "1min" else timedelta(hours=1)
    intervals = [(r.start, r.end) for r in runs if r.start and r.end and r.end >= r.start]
    if not intervals:
        return {}
    earliest = min(s for s, _ in intervals)
    latest = max(e for _, e in intervals)

    def floor_to_bucket(t: datetime) -> datetime:
        if bucket == "1min":
            return t.replace(second=0, microsecond=0)
        return t.replace(minute=0, second=0, microsecond=0)

    counts: Counter = Counter()
    cur = floor_to_bucket(earliest)
    end_bucket = floor_to_bucket(latest)
    while cur <= end_bucket:
        counts[cur] = 0
        cur += delta
    for start, end in intervals:
        b = floor_to_bucket(start)
        end_b = floor_to_bucket(end)
        while b <= end_b:
            counts[b] += 1
            b += delta
    return {k.isoformat(): v for k, v in sorted(counts.items())}


def events_per_second_peak(events: Iterable[Event], window_seconds: int = 1) -> dict:
    times = sorted(e.time for e in events if e.time is not None)
    if not times:
        return {"peak": 0, "at": None}
    counts: Counter = Counter()
    for t in times:
        counts[t.replace(microsecond=0)] += 1
    peak_time, peak_count = max(counts.items(), key=lambda kv: kv[1])
    return {"peak": peak_count, "at": peak_time.isoformat()}


def manual_intervention(events: Iterable[Event]) -> dict:
    """Per-job and per-source-user counts of manual-intervention events [plan §11.1]."""
    per_job: Counter = Counter()
    per_user: Counter = Counter()
    per_job_event: dict[str, Counter] = {}
    for e in events:
        if e.event not in MANUAL_INTERVENTION_EVENTS:
            continue
        per_job[e.job] += 1
        per_job_event.setdefault(e.job, Counter())[e.event] += 1
        if e.source_user:
            per_user[e.source_user] += 1
    return {
        "per_job": dict(per_job),
        "per_source_user": dict(per_user),
        "per_job_by_event": {j: dict(c) for j, c in per_job_event.items()},
        "total": sum(per_job.values()),
    }


def dead_jobs(job_names: Iterable[str], runs: Iterable[Run], window_days: int, *,
             on_hold_ice: dict[str, tuple[str, date]] | None = None, ice_hold_days: int = 30,
             as_of: date | None = None) -> list[dict]:
    """Jobs with no run in `window_days`, or held/iced for more than `ice_hold_days`
    [plan §11.1 decommission_candidates[]].

    `on_hold_ice` optionally maps job -> (state, since_date) for jobs currently ON_HOLD/ON_ICE
    (from the latest manifest snapshot, not from run history).
    """
    today = as_of or date.today()
    last_run: dict[str, date] = {}
    for r in runs:
        ts = r.end or r.start
        if ts is None:
            continue
        d = ts.date()
        if r.job not in last_run or d > last_run[r.job]:
            last_run[r.job] = d

    out: list[dict] = []
    for job in job_names:
        reasons: list[str] = []
        lr = last_run.get(job)
        if lr is None or (today - lr).days > window_days:
            reasons.append(f"no run in {window_days}d (last_run={lr.isoformat() if lr else None})")
        if on_hold_ice and job in on_hold_ice:
            state, since = on_hold_ice[job]
            if (today - since).days > ice_hold_days:
                reasons.append(f"{state} since {since.isoformat()} (> {ice_hold_days}d)")
        if reasons:
            out.append({"job": job, "reasons": reasons})
    return out


def sla_breaches(must_complete_times: dict[str, list[str]], runs: Iterable[Run]) -> list[dict]:
    """Jobs whose observed p95 completion time is later than a declared `must_complete_times`
    entry [plan §11.1: "SLA reality vs. SLA attributes"].

    `must_complete_times` maps job -> list of "HH:MM" strings (Job.schedule.must_complete_times).
    Compares each run's end-of-day wall-clock time against the earliest declared deadline.
    """
    stats = job_stats(runs)
    by_job: dict[str, list[Run]] = {}
    for r in runs:
        by_job.setdefault(r.job, []).append(r)

    out: list[dict] = []
    for job, deadlines in must_complete_times.items():
        if not deadlines or job not in by_job:
            continue
        deadline_minutes = min(int(h) * 60 + int(m) for h, m in (d.split(":") for d in deadlines))
        end_minutes = sorted(
            r.end.hour * 60 + r.end.minute for r in by_job[job] if r.end is not None
        )
        if not end_minutes:
            continue
        p95 = _percentile(end_minutes, 0.95)
        breaches = sum(1 for m in end_minutes if m > deadline_minutes)
        if p95 is not None and p95 > deadline_minutes:
            out.append({
                "job": job, "deadline_minutes": deadline_minutes, "p95_completion_minutes": p95,
                "breach_count": breaches, "run_count": len(end_minutes),
                "breach_rate": breaches / len(end_minutes),
            })
    return out
