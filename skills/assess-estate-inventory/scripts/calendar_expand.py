#!/usr/bin/env python3
"""Expand every scheduled job's calendar to concrete run instants over a date range, and
determine cron-expressibility, calendar class, and DST sensitivity [spec §6.2].

Deterministic: given the same manifest and date range, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Writes `manifest.schedules{}`: per job, run-instant count/first/last, `cron_expressible` (bool),
calendar class, and any DST gap/overlap instants. This is the deterministic input behind "cron
vs. Timetable" translation decisions (`migrate-jil-to-airflow-translation`) -- never guess that
call by eye, always run this script.

Usage:
    python3 calendar_expand.py --manifest estate_manifest.json --from 2026-01-01 --to 2026-12-31 [--md schedules.md]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import calendars as calendars_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402


def compute_schedules(estate, start: date, end: date) -> dict:
    out: dict = {}
    for inst_id, inst in estate.instances.items():
        default_tz = inst.config.get("TimeZone")
        for job in inst.jobs.values():
            if job.deleted or not job.schedule.date_conditions:
                continue
            key = f"{inst_id}:{job.name}"
            expansion = calendars_mod.expand(job, inst.calendars, start, end, default_tz)
            cron = calendars_mod.cron_equivalent(job, inst.calendars, start, end)

            cal_class = None
            if job.schedule.run_calendar and job.schedule.run_calendar in inst.calendars:
                cal_class = calendars_mod.classify_calendar(inst.calendars[job.schedule.run_calendar])

            out[key] = {
                "job": job.name, "instance": inst_id,
                "count": expansion["count"], "first": expansion["first"], "last": expansion["last"],
                "timezone": expansion["timezone"],
                "cron_expressible": cron is not None,
                "cron": cron,
                "calendar_class": cal_class,
                "dst_gap_instants": expansion["dst_gap_instants"],
                "dst_overlap_instants": expansion["dst_overlap_instants"],
                "run_calendar": job.schedule.run_calendar,
                "exclude_calendar": job.schedule.exclude_calendar,
            }
    return out


def render_md(schedules: dict, start: date, end: date) -> str:
    lines = [f"# Schedule expansion ({start.isoformat()} to {end.isoformat()})", ""]
    lines.append("| Job | Runs | Cron-expressible | Calendar class | DST flags |")
    lines.append("|---|---|---|---|---|")
    for key, s in sorted(schedules.items()):
        dst = []
        if s["dst_gap_instants"]:
            dst.append(f"{len(s['dst_gap_instants'])} gap")
        if s["dst_overlap_instants"]:
            dst.append(f"{len(s['dst_overlap_instants'])} overlap")
        lines.append(f"| {key} | {s['count']} | {'yes' if s['cron_expressible'] else 'no'} | "
                     f"{s['calendar_class'] or ''} | {', '.join(dst) or ''} |")
    non_cron = sum(1 for s in schedules.values() if not s["cron_expressible"])
    lines.append("")
    lines.append(f"**{non_cron}/{len(schedules)} jobs are NOT cron-expressible** "
                 f"(need a Timetable, not a cron schedule).")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--from", dest="from_date", type=date.fromisoformat, required=True)
    ap.add_argument("--to", dest="to_date", type=date.fromisoformat, required=True)
    ap.add_argument("--md", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1
    if args.to_date < args.from_date:
        print("error: --to must be >= --from", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    estate.schedules = compute_schedules(estate, args.from_date, args.to_date)
    manifest_mod.to_json(estate, args.manifest, tool="calendar_expand.py")

    if args.md:
        args.md.write_text(render_md(estate.schedules, args.from_date, args.to_date))

    non_cron = sum(1 for s in estate.schedules.values() if not s["cron_expressible"])
    print(f"updated {args.manifest}: {len(estate.schedules)} scheduled job(s), "
          f"{non_cron} not cron-expressible", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
