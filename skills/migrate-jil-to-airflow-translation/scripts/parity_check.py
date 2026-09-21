#!/usr/bin/env python3
"""Compare AutoSys run history against Airflow DAG runs, joined via `traceability.json`
[spec §7.1]. See reference/validation.md Gate 4.

Deterministic: given the same input files, output is byte-identical.
Reads local files only; the Airflow-side data is a customer-collected REST API export
(`airflow dags list-runs` / a REST call the customer makes and saves), never a live call from
this script.

Joins on `traceability.json` (job -> dag_id.task_id), NOT naming convention -- naming-convention
joins are fragile and were explicitly called out as a risk in plan §11.7.

Usage:
    python3 parity_check.py --autosys-history runs.csv --airflow-runs airflow_dagruns.json \\
        --trace traceability.json --window 14d [--max-duration-delta-pct 20] [--require-all-success-parity]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import history as history_mod  # noqa: E402


def load_airflow_runs(path: Path) -> dict[str, list[dict]]:
    """Expects a JSON list of {dag_id, task_id, state, start_date, end_date} (the shape of a
    saved `airflow dags list-runs`/REST API export, flattened to task-instance granularity by
    the customer or a small pre-processing step -- this script doesn't call the API itself)."""
    data = json.loads(path.read_text())
    by_key: dict[str, list[dict]] = {}
    for row in data:
        key = f"{row['dag_id']}.{row['task_id']}"
        by_key.setdefault(key, []).append(row)
    return by_key


def check_parity(autosys_runs: list, airflow_by_key: dict, trace: dict[str, str]) -> dict:
    rows = []
    autosys_by_job: dict[str, list] = {}
    for r in autosys_runs:
        autosys_by_job.setdefault(r.job, []).append(r)

    for job_key, target_key in trace.items():
        _, _, job_name = job_key.partition(":")
        a_runs = autosys_by_job.get(job_name, [])
        af_runs = airflow_by_key.get(target_key, [])

        a_stats = history_mod.job_stats(a_runs).get(job_name, {}) if a_runs else {}
        a_success = sum(1 for r in a_runs if r.status == "SUCCESS")
        af_success = sum(1 for r in af_runs if r.get("state") == "success")

        duration_delta_pct = None
        if a_stats.get("p50_duration_s") and af_runs:
            af_durations = [
                (datetime.fromisoformat(r["end_date"]) - datetime.fromisoformat(r["start_date"])).total_seconds()
                for r in af_runs if r.get("start_date") and r.get("end_date")
            ]
            if af_durations:
                af_p50 = sorted(af_durations)[len(af_durations) // 2]
                if a_stats["p50_duration_s"]:
                    duration_delta_pct = round(
                        100 * (af_p50 - a_stats["p50_duration_s"]) / a_stats["p50_duration_s"], 1)

        rows.append({
            "job": job_name, "target": target_key,
            "autosys_run_count": len(a_runs), "airflow_run_count": len(af_runs),
            "autosys_success_count": a_success, "airflow_success_count": af_success,
            "success_parity": (a_success == af_success) if (a_runs or af_runs) else None,
            "duration_delta_pct": duration_delta_pct,
        })

    return {"rows": rows, "job_count": len(rows)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--autosys-history", type=Path, required=True)
    ap.add_argument("--airflow-runs", type=Path, required=True)
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument("--window", default="14d")
    ap.add_argument("--out", type=Path, default=Path("parity.json"))
    ap.add_argument("--md", type=Path, default=None)
    ap.add_argument("--max-duration-delta-pct", type=float, default=None)
    ap.add_argument("--require-all-success-parity", action="store_true")
    args = ap.parse_args(argv)

    for p in (args.autosys_history, args.airflow_runs, args.trace):
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1

    autosys_runs = history_mod.parse_run_history_csv(args.autosys_history) \
        if args.autosys_history.suffix.lower() == ".csv" \
        else history_mod.parse_autorep_r(args.autosys_history.read_text())
    airflow_by_key = load_airflow_runs(args.airflow_runs)
    trace = json.loads(args.trace.read_text())

    result = check_parity(autosys_runs, airflow_by_key, trace)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    if args.md:
        lines = ["# Parity check", "",
                "| Job | AutoSys runs | Airflow runs | Success parity | Duration delta % |",
                "|---|---|---|---|---|"]
        for r in result["rows"]:
            lines.append(f"| {r['job']} | {r['autosys_run_count']} | {r['airflow_run_count']} | "
                         f"{r['success_parity']} | {r['duration_delta_pct']} |")
        args.md.write_text("\n".join(lines) + "\n")

    failures = []
    if args.require_all_success_parity:
        failures.extend(r["job"] for r in result["rows"] if r["success_parity"] is False)
    if args.max_duration_delta_pct is not None:
        failures.extend(r["job"] for r in result["rows"]
                        if r["duration_delta_pct"] is not None and abs(r["duration_delta_pct"]) > args.max_duration_delta_pct)

    print(f"wrote {args.out}: {result['job_count']} job(s) checked, {len(set(failures))} threshold failure(s)",
          file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
