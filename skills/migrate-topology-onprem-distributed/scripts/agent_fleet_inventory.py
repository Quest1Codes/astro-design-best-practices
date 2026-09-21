#!/usr/bin/env python3
"""Derive a per-machine-group execution-topology worksheet from an `_lib.manifest` estate
manifest [spec §7.2].

Deterministic: given the same manifest, output is byte-identical.
Reads files only; never contacts a live AutoSys, Astro, or network endpoint.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §7.2 (this script's spec: reads manifest machines +
    commands + history; emits per-machine-group jobs, OS, agent plugins, env coupling,
    concurrency peak, FT/FTP partners, cross-machine conditions, hints)
  - [AS p.2873] node_name is a machine's real IP/DNS name; [AS p.2874] machine `type` values

This script NEVER assigns a final Hosted/Hybrid/Bridge disposition -- it surfaces evidence for
a human/agent judgment call (reference/execution-topology-mapping.md), because that decision
depends on compliance and cost tradeoffs the script cannot see.

Usage:
    python3 agent_fleet_inventory.py --manifest estate_manifest.json --out topology_manifest.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import commands as commands_mod  # noqa: E402
from autosys_jil import config as config_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402


def _machines_for_job(job) -> list[str]:
    return list(job.load.machine)


def load_registry_csv(path: Path) -> dict[str, dict]:
    """Optional platform-supplied registry (agent_version, ip_or_hostname, notes) -- facts JIL
    cannot provide at all [plan §11.3; discovery/what-jil-cannot-tell-you.md]."""
    rows: dict[str, dict] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "machine_name" not in reader.fieldnames:
            print(f"error: {path} must have a 'machine_name' column (found: {reader.fieldnames})",
                  file=sys.stderr)
            sys.exit(1)
        for row in reader:
            rows[row["machine_name"]] = row
    return rows


def build_topology(estate, registry: dict[str, dict] | None = None) -> dict:
    registry = dict(registry or {})
    machines: dict[str, dict] = {}

    def entry(name: str) -> dict:
        return machines.setdefault(name, {
            "name": name, "instances": set(), "job_count": 0, "jobs": [], "boxes": set(),
            "job_types": {}, "os_hint_votes": {}, "agent_capabilities": set(),
            "hosts_referenced": set(), "abs_paths": set(), "unc_paths": set(), "mapped_drives": set(),
            "credential_hits": 0, "ftp_transfer_jobs": [], "cross_machine_condition_edges": [],
            "flags": [],
        })

    for inst_id, inst in estate.instances.items():
        agent_caps_by_machine = {
            m: config_mod.agent_capabilities({k: v for k, v in inst.agent_capabilities.items()})
            for m in inst.machines
        } if inst.agent_capabilities else {}

        for job in inst.jobs.values():
            if job.deleted:
                continue
            for m in _machines_for_job(job):
                e = entry(m)
                e["instances"].add(inst_id)
                e["job_count"] += 1
                e["jobs"].append(job.name)
                if job.box_name:
                    e["boxes"].add(job.box_name)
                e["job_types"][job.job_type] = e["job_types"].get(job.job_type, 0) + 1

                if job.command:
                    a = commands_mod.analyze(job.command)
                    e["os_hint_votes"][a.os_hint] = e["os_hint_votes"].get(a.os_hint, 0) + 1
                    e["hosts_referenced"].update(a.hosts)
                    e["abs_paths"].update(a.abs_paths)
                    e["unc_paths"].update(a.unc_paths)
                    e["mapped_drives"].update(a.mapped_drives)
                    e["credential_hits"] += len(a.credential_hits)

                if job.job_type in ("FTP", "SCP", "FT", "FW"):
                    e["ftp_transfer_jobs"].append(job.name)
                    for host in (commands_mod.analyze(job.command).hosts if job.command else []):
                        e["flags"].append(
                            f"job '{job.name}' ({job.job_type}) references host {host!r} in its "
                            "command -- likely transfer partner; confirm network path")

                if job.condition is not None:
                    for ref_name in job.condition.referenced_job_names:
                        ref_job = inst.jobs.get(ref_name)
                        if ref_job is None:
                            continue
                        for ref_machine in _machines_for_job(ref_job):
                            if ref_machine != m:
                                e["cross_machine_condition_edges"].append(
                                    {"from_job": job.name, "to_job": ref_name, "to_machine": ref_machine})

        for name, m in inst.machines.items():
            e = entry(name)
            e["instances"].add(inst_id)
            e["opsys"] = m.opsys
            e["max_load"] = m.max_load
            e["factor"] = m.factor
            e["machine_type"] = m.type
            e["node_name"] = m.node_name
            if name in agent_caps_by_machine:
                e["agent_capabilities"].update(agent_caps_by_machine[name])

    result_machines = []
    for name, e in sorted(machines.items()):
        reg = registry.pop(name, None)
        os_hint_votes = e.pop("os_hint_votes")
        opsys = (reg or {}).get("os") or e.get("opsys")
        if reg and reg.get("os"):
            os_guess, os_confidence = opsys, "platform registry CSV"
        elif e.get("opsys"):
            os_guess, os_confidence = opsys, "machine.opsys [AS p.2873]"
        elif os_hint_votes:
            best = max(os_hint_votes.items(), key=lambda kv: kv[1])
            os_guess = best[0] if best[0] != "unknown" else "unknown"
            os_confidence = "command-heuristic" if os_guess != "unknown" else "unknown"
        else:
            os_guess, os_confidence = "unknown", "unknown"

        result_machines.append({
            "name": name,
            "instances": sorted(e["instances"]),
            "job_count": e["job_count"],
            "jobs": sorted(set(e["jobs"])),
            "boxes": sorted(e["boxes"]),
            "job_types": e["job_types"],
            "os_guess": os_guess,
            "os_guess_confidence": os_confidence,
            "machine_type": e.get("machine_type"),
            "node_name": e.get("node_name"),
            "max_load": e.get("max_load"),
            "factor": e.get("factor"),
            "agent_version": (reg or {}).get("agent_version"),
            "ip_or_hostname": (reg or {}).get("ip_or_hostname"),
            "registry_notes": (reg or {}).get("notes"),
            "agent_capabilities": sorted(e["agent_capabilities"]),
            "hosts_referenced": sorted(e["hosts_referenced"]),
            "abs_paths_sample": sorted(e["abs_paths"])[:10],
            "unc_paths": sorted(e["unc_paths"]),
            "mapped_drives": sorted(e["mapped_drives"]),
            "credential_hits": e["credential_hits"],
            "ftp_transfer_jobs": sorted(set(e["ftp_transfer_jobs"])),
            "cross_machine_condition_edges": e["cross_machine_condition_edges"],
            "flags": sorted(set(e["flags"])),
            "concurrency_peak": (estate.history.get("concurrency_peak_by_machine", {}) or {}).get(name),
            "recommended_target": "needs-review",
            "classification": "pending",
        })

    registry_only = [{"name": name, **reg} for name, reg in registry.items()]

    return {
        "generated_by": manifest_mod.generated_by("agent_fleet_inventory.py"),
        "machines": result_machines,
        "registry_only_machines": registry_only,
        "summary": {"machine_count": len(result_machines), "registry_only_count": len(registry_only)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True,
                    help="estate_manifest.json from assess-estate-inventory's build_estate_manifest.py")
    ap.add_argument("--machines-csv", type=Path, default=None,
                    help="optional platform registry: machine_name,os,agent_version,ip_or_hostname,notes")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    registry = load_registry_csv(args.machines_csv) if args.machines_csv else {}
    topology = build_topology(estate, registry)
    args.out.write_text(json.dumps(topology, sort_keys=True, indent=2) + "\n")
    print(f"wrote {args.out}: {topology['summary']['machine_count']} machine groups", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
