#!/usr/bin/env python3
"""Run `_lib.history` stats over collected run-history/event-archive artifacts and write
`manifest.history{}` [spec §6.2, plan §11.1].

Deterministic: given the same manifest and history/event files, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Accepts run history as either a DBA CSV export (`ujo_job_runs`-shaped, preferred) or `autorep`
text-report output; events similarly as a CSV (`ujo_event`-shaped) or omitted entirely (manual-
intervention stats are simply unavailable without it -- not an error).

Usage:
    python3 history_stats.py --manifest estate_manifest.json \\
        --history runs.csv|runs.txt [--history-format csv|autorep] \\
        [--events events.csv] [--columns map.yaml] [--window 90] [--dead-window 30]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import history as history_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402


def load_runs(path: Path, fmt: str, columns_map: dict | None) -> list:
    text_or_bytes = path.suffix.lower()
    if fmt == "csv" or text_or_bytes == ".csv":
        return history_mod.parse_run_history_csv(path, columns_map)
    return history_mod.parse_autorep_r(path.read_text(errors="replace"))


def compute_history(estate, runs: list, events: list, window_days: int, dead_window_days: int) -> dict:
    stats = history_mod.job_stats(runs)
    curve = history_mod.concurrency_curve(runs)
    peak = history_mod.events_per_second_peak(events) if events else {"peak": 0, "at": None}
    manual = history_mod.manual_intervention(events) if events else {
        "per_job": {}, "per_source_user": {}, "per_job_by_event": {}, "total": 0}

    all_job_names = [j.name for inst in estate.instances.values() for j in inst.jobs.values()
                     if not j.deleted]
    dead = history_mod.dead_jobs(all_job_names, runs, dead_window_days)

    must_complete: dict[str, list[str]] = {}
    for inst in estate.instances.values():
        for job in inst.jobs.values():
            if job.schedule.must_complete_times:
                must_complete[job.name] = job.schedule.must_complete_times
    breaches = history_mod.sla_breaches(must_complete, runs)

    return {
        "window_days": window_days,
        "run_count": len(runs),
        "event_count": len(events),
        "job_stats": stats,
        "concurrency_curve": curve,
        "events_per_second_peak": peak,
        "manual_intervention": manual,
        "dead_job_candidates": dead,
        "sla_breaches": breaches,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--history", type=Path, required=True)
    ap.add_argument("--history-format", choices=["csv", "autorep"], default=None)
    ap.add_argument("--events", type=Path, default=None)
    ap.add_argument("--columns", type=Path, default=None, help="YAML column-name map for DBA CSV exports")
    ap.add_argument("--window", type=int, default=90, help="days of history represented (metadata only)")
    ap.add_argument("--dead-window", type=int, default=30, dest="dead_window")
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1
    if not args.history.exists():
        print(f"error: {args.history} not found", file=sys.stderr)
        return 1

    columns_map = None
    if args.columns and args.columns.exists():
        import yaml
        columns_map = yaml.safe_load(args.columns.read_text())

    fmt = args.history_format or ("csv" if args.history.suffix.lower() == ".csv" else "autorep")
    runs = load_runs(args.history, fmt, columns_map)

    events = []
    if args.events and args.events.exists():
        events = history_mod.parse_event_archive_csv(args.events, columns_map)

    estate = manifest_mod.from_json(args.manifest)
    estate.history = compute_history(estate, runs, events, args.window, args.dead_window)
    manifest_mod.to_json(estate, args.manifest, tool="history_stats.py")

    h = estate.history
    print(f"updated {args.manifest}: {h['run_count']} run(s), {h['event_count']} event(s), "
          f"{len(h['job_stats'])} job(s) with stats, {len(h['dead_job_candidates'])} dead-job candidate(s), "
          f"{len(h['sla_breaches'])} SLA breach(es), {h['manual_intervention']['total']} manual intervention(s)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
