#!/usr/bin/env python3
"""One parity cycle: AutoSys run history vs. Airflow run history, joined via
`traceability.json` [spec §7.6].

Deterministic: given the same input files, output is byte-identical.
Reads local files only; the Airflow-side data is a customer-collected REST API export, never a
live call from this script.

Writes `parity_cycle_<n>.json` and a delta-by-class summary. Distinct from
`migrate-jil-to-airflow-translation/scripts/parity_check.py`, which runs once during translation
validation over a fixed window -- this script runs repeatedly, once per cutover parity cycle
(see reference/parity-cycles.md), accumulating a track record `cutover_gate.py` reads.

Usage:
    python3 reconcile_runs.py --autosys-history runs.csv --airflow-runs airflow_runs.json \\
        --trace traceability.json --cycle 1 --out parity_cycle_1.json
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
    data = json.loads(path.read_text())
    by_key: dict[str, list[dict]] = {}
    for row in data:
        key = f"{row['dag_id']}.{row['task_id']}"
        by_key.setdefault(key, []).append(row)
    return by_key


def reconcile(autosys_runs: list, airflow_by_key: dict, trace: dict[str, str], cycle: int) -> dict:
    autosys_by_job: dict[str, list] = {}
    for r in autosys_runs:
        autosys_by_job.setdefault(r.job, []).append(r)

    rows = []
    delta_classes: dict[str, int] = {}

    for job_key, target_key in trace.items():
        _, _, job_name = job_key.partition(":")
        a_runs = autosys_by_job.get(job_name, [])
        af_runs = airflow_by_key.get(target_key, [])

        a_status = a_runs[-1].status if a_runs else None
        af_status = af_runs[-1].get("state") if af_runs else None
        status_match = (
            (a_status == "SUCCESS" and af_status == "success") or
            (a_status in ("FAILURE", "TERMINATED") and af_status == "failed")
        ) if a_status and af_status else None

        delta_class = None
        if a_status and not af_status:
            delta_class = "missing_airflow_run"
        elif af_status and not a_status:
            delta_class = "missing_autosys_run"
        elif status_match is False:
            delta_class = "status_mismatch"
        elif status_match is None:
            delta_class = "no_comparable_data"
        else:
            delta_class = "clean"
        delta_classes[delta_class] = delta_classes.get(delta_class, 0) + 1

        rows.append({"job": job_name, "target": target_key, "autosys_status": a_status,
                    "airflow_status": af_status, "delta_class": delta_class})

    return {
        "cycle": cycle, "generated_at": datetime.now().isoformat(), "rows": rows,
        "delta_classes": delta_classes,
        "clean": all(r["delta_class"] == "clean" for r in rows) if rows else False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--autosys-history", type=Path, required=True)
    ap.add_argument("--airflow-runs", type=Path, required=True)
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument("--cycle", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
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

    result = reconcile(autosys_runs, airflow_by_key, trace, args.cycle)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")

    print(f"wrote {args.out}: cycle {args.cycle}, {len(result['rows'])} unit(s), "
          f"clean={result['clean']}, delta classes={result['delta_classes']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
