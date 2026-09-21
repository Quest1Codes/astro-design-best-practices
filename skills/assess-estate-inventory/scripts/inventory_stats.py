#!/usr/bin/env python3
"""Enrich `estate_manifest.json` with histograms and box-metric distributions [spec §6.2].

Deterministic: given the same manifest, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Writes `manifest.stats{}`: job-type/attribute/machine/owner/application/group histograms, box
metrics distribution, machine max_load vs. referencing job_load sums. Schedule density requires
`calendar_expand.py` to have run first (reads `manifest.schedules`, tolerates its absence).

Usage:
    python3 inventory_stats.py --manifest estate_manifest.json [--top N] [--md stats.md]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil.boxes import box_metrics  # noqa: E402
from autosys_jil.registry import attributes as attribute_registry  # noqa: E402


def compute_stats(estate) -> dict:
    job_type_hist: Counter = Counter()
    attr_family_hist: Counter = Counter()
    machine_hist: Counter = Counter()
    owner_hist: Counter = Counter()
    application_hist: Counter = Counter()
    group_hist: Counter = Counter()
    job_load_by_machine: dict[str, int] = {}
    box_metrics_all: dict[str, dict] = {}

    attrs_reg = attribute_registry()

    for inst_id, inst in estate.instances.items():
        for job in inst.jobs.values():
            if job.deleted:
                continue
            job_type_hist[job.job_type] += 1
            for attr_name, attr in job.attrs.items():
                fam = attr.family or attrs_reg.get(attr_name, {}).get("family", "misc")
                attr_family_hist[fam] += 1
            for m in job.load.machine:
                machine_hist[m] += 1
                if job.load.job_load:
                    job_load_by_machine[m] = job_load_by_machine.get(m, 0) + job.load.job_load
            if job.owner:
                owner_hist[job.owner] += 1
            if job.application:
                application_hist[job.application] += 1
            if job.group:
                group_hist[job.group] += 1

        metrics = box_metrics(inst.boxes, inst.jobs)
        for name, m in metrics.items():
            box_metrics_all[f"{inst_id}:{name}"] = m

    machine_load_pressure = {}
    for inst in estate.instances.values():
        for name, machine in inst.machines.items():
            if machine.max_load and name in job_load_by_machine:
                machine_load_pressure[name] = {
                    "max_load": machine.max_load,
                    "sum_job_load_referencing": job_load_by_machine[name],
                    "over_capacity": job_load_by_machine[name] > machine.max_load,
                }

    depth_dist: Counter = Counter(m["depth"] for m in box_metrics_all.values())

    return {
        "job_type_histogram": dict(job_type_hist),
        "attribute_family_histogram": dict(attr_family_hist),
        "machine_histogram": dict(machine_hist),
        "owner_histogram": dict(owner_hist),
        "application_histogram": dict(application_hist),
        "group_histogram": dict(group_hist),
        "box_depth_distribution": {str(k): v for k, v in depth_dist.items()},
        "box_metrics": box_metrics_all,
        "machine_load_pressure": machine_load_pressure,
    }


def render_md(stats: dict, top: int) -> str:
    lines = ["# Inventory stats", ""]

    def table(title: str, hist: dict) -> None:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Value | Count |")
        lines.append("|---|---|")
        for k, v in sorted(hist.items(), key=lambda kv: -kv[1])[:top]:
            lines.append(f"| {k} | {v} |")
        lines.append("")

    table("Job types", stats["job_type_histogram"])
    table("Attribute families", stats["attribute_family_histogram"])
    table("Machines (top by job count)", stats["machine_histogram"])
    table("Owners", stats["owner_histogram"])
    table("Applications", stats["application_histogram"])
    table("Groups", stats["group_histogram"])

    over = {k: v for k, v in stats["machine_load_pressure"].items() if v["over_capacity"]}
    if over:
        lines.append("## Machines where sum(job_load) exceeds max_load")
        lines.append("")
        lines.append("| Machine | max_load | sum(job_load) |")
        lines.append("|---|---|---|")
        for name, v in over.items():
            lines.append(f"| {name} | {v['max_load']} | {v['sum_job_load_referencing']} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--md", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    estate.stats = compute_stats(estate)
    manifest_mod.to_json(estate, args.manifest, tool="inventory_stats.py")

    if args.md:
        args.md.write_text(render_md(estate.stats, args.top))

    total_jobs = sum(len(i.jobs) for i in estate.instances.values())
    print(f"updated {args.manifest}: stats over {total_jobs} jobs, "
          f"{len(estate.stats['job_type_histogram'])} job types, "
          f"{len(estate.stats['machine_load_pressure'])} machines with job_load pressure data",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
