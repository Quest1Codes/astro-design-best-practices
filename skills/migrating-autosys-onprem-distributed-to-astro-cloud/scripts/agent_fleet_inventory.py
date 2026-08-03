#!/usr/bin/env python3
"""Derive a per-machine execution-topology worksheet from a jil_inventory.py manifest.

AutoSys has no standard textual export for its machine/agent registry the way
JIL covers jobs -- machine facts (OS, agent version, what's locally installed)
live in WCC/the AE database or a platform team's own records. This script
derives what it CAN from manifest.json (job manifest.json produced by the
migrating-autosys-to-astronomer skill): which machines are referenced, by how
many jobs, and heuristic OS/cross-machine flags -- then optionally merges a
platform-supplied registry CSV (columns: machine_name,os,agent_version,
ip_or_hostname,notes).

This script NEVER assigns a final Hosted/Hybrid/Bridge disposition -- it
surfaces evidence for a human/agent judgment call (reference/
execution-topology-mapping.md), because that decision depends on compliance
and cost tradeoffs the script cannot see.

Usage:
    python3 agent_fleet_inventory.py --manifest manifest.json --out topology_manifest.json
    python3 agent_fleet_inventory.py --manifest manifest.json --machines-csv registry.csv --out topology_manifest.json
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

WINDOWS_HINTS = re.compile(r"\.exe\b|\.bat\b|\.ps1\b|\\\\|[A-Za-z]:\\\\", re.IGNORECASE)
UNIX_HINTS = re.compile(r"\.sh\b|^#!/|/opt/|/usr/|/home/", re.IGNORECASE)


def guess_os(commands):
    """Heuristic only -- confirm against the registry CSV or platform team."""
    text = " ".join(c for c in commands if c)
    win_score = len(WINDOWS_HINTS.findall(text))
    unix_score = len(UNIX_HINTS.findall(text))
    if win_score and not unix_score:
        return "windows"
    if unix_score and not win_score:
        return "unix"
    if win_score and unix_score:
        return "mixed-signals"
    return "unknown"


def load_registry_csv(path: Path):
    rows = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"machine_name"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            print(f"error: {path} must have at least a 'machine_name' column "
                  f"(found: {reader.fieldnames})", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            rows[row["machine_name"]] = row
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, required=True, help="manifest.json from migrating-autosys-to-astronomer")
    parser.add_argument("--machines-csv", type=Path, default=None,
                         help="Optional platform-supplied registry CSV: machine_name,os,agent_version,ip_or_hostname,notes")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run jil_inventory.py from "
              "migrating-autosys-to-astronomer first", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(args.manifest.read_text())
    jobs = manifest.get("jobs", [])

    # box membership, for cross-referencing which box(es) a machine's jobs sit in
    job_to_boxes = {}
    for box in manifest.get("boxes", []):
        for child in box.get("children", []):
            job_to_boxes.setdefault(child, []).append(box["name"])

    machines = {}

    def get_entry(name):
        return machines.setdefault(name, {
            "name": name,
            "job_count": 0,
            "jobs": [],
            "boxes": set(),
            "commands": [],
            "flags": [],
            "has_raw_extra": False,
        })

    for job in jobs:
        # FT jobs commonly carry their machine identity as from_machine/to_machine
        # inside raw_extra rather than a top-level machine: attribute (that's
        # exactly why those land in raw_extra in the first place) -- fall back
        # to those so an FT job isn't silently invisible to this inventory.
        job_type = (job.get("job_type") or "").lower()
        extra = job.get("raw_extra") or {}
        if job.get("machine"):
            relevant_machines = [job["machine"]]
        elif job_type == "ft":
            relevant_machines = [m for m in (extra.get("from_machine"), extra.get("to_machine")) if m]
            if not relevant_machines:
                continue
        else:
            continue

        for m in relevant_machines:
            entry = get_entry(m)
            entry["job_count"] += 1
            entry["jobs"].append(job["name"])
            entry["boxes"].update(job_to_boxes.get(job["name"], []))
            if job.get("command"):
                entry["commands"].append(job["command"])
            if job.get("raw_extra"):
                entry["has_raw_extra"] = True
                entry["flags"].append(
                    f"job '{job['name']}' carries unverified raw_extra attributes "
                    f"{sorted(job['raw_extra'])} -- often encodes machine-to-machine "
                    "transfer specifics relevant to this skill's networking plan"
                )
            if job_type == "ft":
                for partner in relevant_machines:
                    if partner != m:
                        entry["flags"].append(
                            f"ft_partner_machine: {partner} -- confirm network path jointly with this machine"
                        )
            cond_analysis = job.get("condition_analysis")
            if cond_analysis and cond_analysis.get("referenced_jobs"):
                for ref in cond_analysis["referenced_jobs"]:
                    ref_job = next((j for j in jobs if j["name"] == ref["job"]), None)
                    if ref_job and ref_job.get("machine") and ref_job["machine"] != m:
                        entry["flags"].append(
                            f"condition references job '{ref['job']}' on machine "
                            f"'{ref_job['machine']}' -- cross-machine dependency, plan network "
                            "path between the two if they land in different targets"
                        )

    registry = load_registry_csv(args.machines_csv) if args.machines_csv else {}
    csv_only = []

    result_machines = []
    for name, entry in sorted(machines.items()):
        reg = registry.pop(name, None)
        os_guess = reg["os"] if reg and reg.get("os") else guess_os(entry["commands"])
        os_confidence = "registry" if (reg and reg.get("os")) else "heuristic"
        record = {
            "name": name,
            "job_count": entry["job_count"],
            "jobs": entry["jobs"],
            "boxes": sorted(entry["boxes"]),
            "os_guess": os_guess,
            "os_guess_confidence": os_confidence,
            "agent_version": reg.get("agent_version") if reg else None,
            "ip_or_hostname": reg.get("ip_or_hostname") if reg else None,
            "registry_notes": reg.get("notes") if reg else None,
            "flags": sorted(set(entry["flags"])),
            "recommended_target": "needs-review",
            "classification": "pending",
            "status": "pending",
        }
        result_machines.append(record)

    # anything left in registry had no jobs referencing it in this manifest slice
    for name, reg in registry.items():
        csv_only.append({"name": name, **reg})

    topology_manifest = {
        "source_manifest": str(args.manifest),
        "source_registry_csv": str(args.machines_csv) if args.machines_csv else None,
        "machines": result_machines,
        "registry_only_machines": csv_only,
        "summary": {
            "machine_count": len(result_machines),
            "registry_only_count": len(csv_only),
        },
    }

    indent = 2 if args.pretty else None
    args.out.write_text(json.dumps(topology_manifest, indent=indent))
    print(f"Wrote {args.out}: {len(result_machines)} machines from manifest, "
          f"{len(csv_only)} registry-only machines with no jobs in this manifest", file=sys.stderr)
    if csv_only:
        print("  registry-only machines (decommissioned, or outside this export's scope -- confirm):",
              file=sys.stderr)
        for m in csv_only:
            print(f"    {m['name']}", file=sys.stderr)


if __name__ == "__main__":
    main()
