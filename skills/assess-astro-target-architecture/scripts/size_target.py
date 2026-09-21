#!/usr/bin/env python3
"""Sizing formulas for the target Astro platform [spec §6.4], each cited to its inputs and, where
one exists, the AutoSys-side page or KB topic it's derived from.

Deterministic: given the same manifest, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Every function returns `{value, basis, inputs}` where `basis` states whether the number is
`observed` (from real history/`max_load`/`job_load`) or `floor` (job-count-only, a lower bound
that must be labeled as such in the report, never presented as a real estimate) -- plan §3.1's
own distinction, enforced structurally here rather than left to prose discipline.

Usage:
    python3 size_target.py --manifest estate_manifest.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402


def pool_slots(estate) -> dict:
    """Pool slots per machine group from max_load/job_load [AS p.2547-2548, p.2872].

    Trustworthy only where job_load is actually set AND priority >= 1 on the referencing jobs
    (see autosys-reference/reference/machines-load-and-resources.md's priority-interaction note)
    -- flagged per machine, never silently assumed reliable.
    """
    pools: dict[str, dict] = {}
    for inst in estate.instances.values():
        job_load_by_machine: dict[str, int] = {}
        priority_set_by_machine: dict[str, bool] = {}
        for job in inst.jobs.values():
            if job.deleted:
                continue
            for m in job.load.machine:
                if job.load.job_load:
                    job_load_by_machine[m] = job_load_by_machine.get(m, 0) + job.load.job_load
                    if job.load.priority and job.load.priority >= 1:
                        priority_set_by_machine[m] = True
        for name, machine in inst.machines.items():
            if machine.max_load:
                sum_load = job_load_by_machine.get(name, 0)
                trustworthy = priority_set_by_machine.get(name, False)
                pools[name] = {
                    "value": machine.max_load,
                    "sum_job_load": sum_load,
                    "basis": "observed" if trustworthy else "floor",
                    "note": None if trustworthy else (
                        "job_load present but priority not set >=1 on referencing jobs -- "
                        "max_load is likely not actually enforced for this machine [AS p.2548]"),
                }
    return pools


def worker_fleet(concurrency_curve: dict, task_duration_p95: dict | None = None) -> dict:
    """Worker fleet sizing from the observed concurrency curve (history_stats.py), not job count.

    `task_duration_p95` (optional, per-job seconds from history_stats.job_stats) refines the
    estimate; without it this returns a `floor` basis result from peak concurrency alone.
    """
    if not concurrency_curve:
        return {"value": None, "basis": "floor", "note": "no concurrency_curve available -- "
                "run history_stats.py first; this is unset, not zero"}
    peak = max(concurrency_curve.values())
    return {
        "value": {"min": max(1, peak // 3), "max": max(1, int(peak * 1.3))},
        "basis": "observed" if task_duration_p95 else "floor",
        "peak_observed_concurrency": peak,
        "note": "min/max derived from observed peak concurrency +/- headroom multiplier "
                "(1.3x); a starting point, not a guarantee -- validate post-cutover "
                "(see reading-the-inventory.md pattern of stating estimates as hypotheses).",
    }


def scheduler_size(dag_count: int, task_count: int, schedule_density_per_hour: float | None) -> dict:
    """Heuristic scheduler sizing: DAG/task count and schedule density (jobs starting per hour).

    PRACTITIONER JUDGMENT thresholds (no cited Astronomer sizing table available in this
    session -- see skills/docs/HANDOFF.md §5 on missing MCP access); re-verify against current
    Astronomer sizing guidance before presenting as a firm recommendation.
    """
    density = schedule_density_per_hour or 0
    if dag_count > 500 or task_count > 5000 or density > 200:
        size = "large"
    elif dag_count > 100 or task_count > 1000 or density > 50:
        size = "medium"
    else:
        size = "small"
    return {"value": size, "basis": "floor" if schedule_density_per_hour is None else "observed",
           "inputs": {"dag_count": dag_count, "task_count": task_count,
                      "schedule_density_per_hour": schedule_density_per_hour}}


def dag_processor_size(dag_count: int, avg_parse_seconds_per_dag: float = 0.5) -> dict:
    """DAG processor sizing floor: dag_count * an assumed per-DAG parse budget.

    `avg_parse_seconds_per_dag` is a stated assumption (default 0.5s), not measured -- always a
    `floor` result; refine with real parse-time measurement against the actual scaffolded DAGs
    once `scaffold_dags.py` (migrate-jil-to-airflow-translation) has run.
    """
    total_seconds = dag_count * avg_parse_seconds_per_dag
    return {"value": {"estimated_total_parse_seconds": total_seconds,
                      "recommendation": "small" if total_seconds < 30 else "medium" if total_seconds < 120 else "large"},
           "basis": "floor", "inputs": {"dag_count": dag_count, "avg_parse_seconds_per_dag": avg_parse_seconds_per_dag}}


def triggerer_size(sensor_count: int) -> dict:
    """Triggerer sizing floor from the count of jobs expected to translate to deferrable sensors
    (FW/file-watch jobs, ExternalTaskSensor-based condition translations)."""
    size = "large" if sensor_count > 500 else "medium" if sensor_count > 100 else "small"
    return {"value": size, "basis": "floor", "inputs": {"sensor_count": sensor_count}}


def db_tier(job_count: int, run_history_volume: int | None, retention_days: int = 90) -> dict:
    """Metadata-DB tier floor from job count and (if known) run-history row volume.

    PRACTITIONER JUDGMENT thresholds -- see scheduler_size's note on missing MCP access.
    """
    if job_count > 5000 or (run_history_volume or 0) > 2_000_000:
        tier = "large"
    elif job_count > 1000 or (run_history_volume or 0) > 200_000:
        tier = "medium"
    else:
        tier = "small"
    return {"value": tier, "basis": "observed" if run_history_volume else "floor",
           "inputs": {"job_count": job_count, "run_history_volume": run_history_volume,
                      "retention_days": retention_days}}


def compute_sizing(estate) -> dict:
    total_jobs = sum(len(i.jobs) for i in estate.instances.values())
    total_boxes = sum(len(i.boxes) for i in estate.instances.values())
    dag_count = total_boxes or total_jobs  # rough floor: one DAG per top-level box, else per job
    curve = estate.schedules.get("concurrency_curve", {}) if isinstance(estate.schedules, dict) else {}
    curve = estate.history.get("concurrency_curve", {}) if isinstance(estate.history, dict) and estate.history.get("concurrency_curve") else curve

    schedule_density = None
    if isinstance(estate.schedules, dict) and estate.schedules:
        counts = [s.get("count", 0) for s in estate.schedules.values() if isinstance(s, dict)]
        if counts:
            schedule_density = sum(counts) / (365 * 24)  # rough runs/hour over a year horizon

    sensor_count = sum(
        1 for inst in estate.instances.values() for j in inst.jobs.values()
        if j.job_type in ("FW", "FT") and not j.deleted
    )

    run_history_volume = None
    if isinstance(estate.history, dict):
        run_history_volume = estate.history.get("run_count")

    return {
        "pool_slots": pool_slots(estate),
        "worker_fleet": worker_fleet(curve),
        "scheduler_size": scheduler_size(dag_count, total_jobs, schedule_density),
        "dag_processor_size": dag_processor_size(dag_count),
        "triggerer_size": triggerer_size(sensor_count),
        "db_tier": db_tier(total_jobs, run_history_volume),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    sizing = compute_sizing(estate)

    arch = estate.architecture if isinstance(estate.architecture, dict) else {}
    arch["sizing"] = sizing
    estate.architecture = arch
    manifest_mod.to_json(estate, args.manifest, tool="size_target.py")

    print(f"updated {args.manifest}: scheduler={sizing['scheduler_size']['value']}, "
          f"db_tier={sizing['db_tier']['value']}, "
          f"worker_fleet={sizing['worker_fleet']['value']}, "
          f"{len(sizing['pool_slots'])} machine pool(s) sized", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
