#!/usr/bin/env python3
"""Run `_lib.commands.analyze()` over every job's command/watch_file/std_*_file/profile, and
cluster near-duplicate commands into templates [spec §6.2, plan §11.2].

Deterministic: given the same manifest, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Writes `manifest.commands{}` (per job) and `manifest.command_summary{}` (interpreters,
template_clusters, hidden-control-flow edges, environment coupling, credential exposure counts,
scripts-to-fetch list). Never stores a credential VALUE, only pattern name + span (see
`_lib.commands.CredentialHit`).

Usage:
    python3 command_analysis.py --manifest estate_manifest.json [--scripts-out scripts_to_fetch.txt]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import commands as commands_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402


def compute_commands(estate) -> tuple[dict, dict]:
    per_job: dict = {}
    interpreter_hist: Counter = Counter()
    os_hint_hist: Counter = Counter()
    all_hidden: list[dict] = []
    all_credential_hits = 0
    env_coupling_jobs: set[str] = set()
    scripts_to_fetch: set[str] = set()
    cluster_input: dict[str, str] = {}

    for inst_id, inst in estate.instances.items():
        for job in inst.jobs.values():
            if job.deleted:
                continue
            key = f"{inst_id}:{job.name}"
            fields = {
                "command": job.command,
                "watch_file": job.attrs.get("watch_file").value if job.attrs.get("watch_file") else None,
                "std_in_file": job.io.std_in_file, "std_out_file": job.io.std_out_file,
                "std_err_file": job.io.std_err_file, "profile": job.io.profile,
            }
            analyses = {}
            for field_name, value in fields.items():
                if not value or not isinstance(value, str):
                    continue
                a = commands_mod.analyze(value)
                analyses[field_name] = a.as_dict()
                interpreter_hist[a.interpreter] += 1
                os_hint_hist[a.os_hint] += 1
                all_credential_hits += len(a.credential_hits)
                if a.abs_paths or a.unc_paths or a.mapped_drives:
                    env_coupling_jobs.add(key)
                for edge in a.hidden_control_flow:
                    all_hidden.append({"job": key, "kind": edge.kind, "event": edge.event,
                                       "target_job": edge.job, "raw": edge.raw})
                if a.script_path and not a.script_path.startswith("%%"):
                    scripts_to_fetch.add(a.script_path)

            if job.command:
                cluster_input[key] = job.command
            if analyses:
                per_job[key] = analyses

    clusters = commands_mod.cluster_templates(cluster_input)

    summary = {
        "interpreters": dict(interpreter_hist),
        "os_hints": dict(os_hint_hist),
        "hidden_control_flow_edges": all_hidden,
        "credential_hit_total": all_credential_hits,
        "environment_coupling_job_count": len(env_coupling_jobs),
        "environment_coupling_jobs": sorted(env_coupling_jobs),
        "template_clusters": [c.as_dict() for c in clusters],
        "scripts_to_fetch": sorted(scripts_to_fetch),
    }
    return per_job, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--scripts-out", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    per_job, summary = compute_commands(estate)
    estate.commands = per_job
    estate.command_summary = summary
    manifest_mod.to_json(estate, args.manifest, tool="command_analysis.py")

    if args.scripts_out:
        args.scripts_out.write_text("\n".join(summary["scripts_to_fetch"]) + "\n")

    print(f"updated {args.manifest}: {len(per_job)} job(s) analyzed, "
          f"interpreters={summary['interpreters']}, "
          f"{len(summary['hidden_control_flow_edges'])} hidden control-flow edge(s), "
          f"{summary['credential_hit_total']} credential hit(s) (never stored), "
          f"{len(summary['template_clusters'])} template cluster(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
