#!/usr/bin/env python3
"""Per-instance discovery checklist: which artifacts are received/validated/missing/waived, and
the exact command to run for anything missing [spec §6.1].

Deterministic: given the same `--received` directory contents and `--nfr` answers, output is
byte-identical. Reads files only; never contacts a live AutoSys or Astro system.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §6.1 (this script's spec)
  - reference/artifact-checklist.md (the artifact list this script walks)
  - reference/stakeholder-questions.md (the `nfr.*` schema `--nfr` is validated against)

Usage:
    python3 discovery_checklist.py --instances ACE,PRD --received ./received/ \\
        [--nfr answers.yaml] --out checklist.json [--md checklist.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402

# (artifact_id, required, command, who, unlocks) -- mirrors reference/artifact-checklist.md.
# `required` is per-instance except where noted.
ARTIFACTS: list[tuple[str, bool, str, str, str]] = [
    ("jil_export", True, "autorep -J ALL -q", "Platform team", "everything -- primary manifest input"),
    ("machine_export", True, "autorep -M ALL -q", "Platform team", "Machine.opsys/max_load/factor"),
    ("globals_export", False, "autorep -G ALL", "Platform team", "VALUE() condition resolution"),
    ("resources_export", False, "autorep -R ALL", "Platform team", "resource-dependency completeness"),
    ("xinst_export", False, "autorep -X ALL", "Platform team", "cross-instance condition resolution"),
    ("calendars_export", False, "autocal_asc -E export.txt -c ALL", "Platform team", "calendar-driven schedule expansion"),
    ("run_history", False, "autorep -J ALL -r -N (or DBA ujo_job_runs export)", "Platform/DBA", "history_stats.py"),
    ("event_archive", False, "archive_events output (or DBA ujo_event export)", "DBA", "manual-intervention frequency"),
    ("config_autoserv", False, "cat $AUTOUSER/config.$AUTOSERV", "Platform team", "config semantic params"),
    ("agentparm", False, "cat .../agentparm.txt (per agent class)", "Platform team", "agent capability inference"),
    ("eem_safex", False, "as_safetool + safex export", "Security team", "rbac_map.py"),
    ("brownfield_astro", False, "astro deployment list -o json (+ inspect, workspace list)", "Customer Astro admin", "astro_inventory.py"),
]

CALENDAR_DEPENDENT_NOTE = (
    "required if any job uses run_calendar/exclude_calendar/date_conditions -- confirm before waiving"
)


def scan_received(received_dir: Path) -> dict[str, list[str]]:
    """Best-effort: which artifact ids does each received file plausibly satisfy, by simple
    filename/content sniff. Real classification is validate_artifacts.py's job; this is only
    used to pre-fill the checklist so a human isn't re-typing what's obviously already there."""
    hints: dict[str, list[str]] = {aid: [] for aid, *_ in ARTIFACTS}
    if not received_dir.exists():
        return hints
    for path in sorted(received_dir.iterdir()):
        if not path.is_file():
            continue
        name = path.name.lower()
        try:
            head = path.read_text(errors="replace")[:4000]
        except Exception:
            head = ""
        if "insert_job:" in head:
            hints["jil_export"].append(path.name)
        elif "machine name" in head.lower() and "max load" in head.lower():
            hints["machine_export"].append(path.name)
        elif "global name" in head.lower():
            hints["globals_export"].append(path.name)
        elif "autoserv" in name or "config." in name:
            hints["config_autoserv"].append(path.name)
        elif "agentparm" in name:
            hints["agentparm"].append(path.name)
        elif "calendar" in name:
            hints["calendars_export"].append(path.name)
        elif "safex" in name or "eem" in name:
            hints["eem_safex"].append(path.name)
        elif "history" in name or "ujo_job_runs" in name:
            hints["run_history"].append(path.name)
        elif "event" in name or "ujo_event" in name:
            hints["event_archive"].append(path.name)
    return hints


def build_checklist(instances: list[str], received_dir: Path, nfr: dict) -> dict:
    hints = scan_received(received_dir)
    rows = []
    for instance in instances:
        for artifact_id, required, command, who, unlocks in ARTIFACTS:
            found = hints.get(artifact_id, [])
            status = "received" if found else "missing"
            rows.append({
                "instance": instance, "artifact": artifact_id, "required": required,
                "command": command, "who": who, "unlocks": unlocks,
                "status": status, "matched_files": found, "waived_reason": None,
            })
    return {
        "generated_by": manifest_mod.generated_by("discovery_checklist.py"),
        "instances": instances,
        "checklist": rows,
        "nfr": nfr,
        "summary": {
            "total": len(rows),
            "received": sum(1 for r in rows if r["status"] == "received"),
            "missing_required": sum(1 for r in rows if r["status"] == "missing" and r["required"]),
        },
    }


def render_md(checklist: dict) -> str:
    lines = ["# Discovery checklist", ""]
    for instance in checklist["instances"]:
        lines.append(f"## Instance {instance}")
        lines.append("")
        lines.append("| Artifact | Required | Status | Command | Who |")
        lines.append("|---|---|---|---|---|")
        for row in checklist["checklist"]:
            if row["instance"] != instance:
                continue
            req = "**required**" if row["required"] else "optional"
            lines.append(f"| {row['artifact']} | {req} | {row['status']} | `{row['command']}` | {row['who']} |")
        lines.append("")
    s = checklist["summary"]
    lines.append(f"**{s['received']}/{s['total']} received, {s['missing_required']} required still missing.**")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instances", required=True, help="comma-separated instance IDs, e.g. ACE,PRD")
    ap.add_argument("--received", type=Path, required=True)
    ap.add_argument("--nfr", type=Path, default=None, help="answers.yaml per reference/stakeholder-questions.md")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path, default=None)
    args = ap.parse_args(argv)

    instances = [i.strip() for i in args.instances.split(",") if i.strip()]
    nfr = yaml.safe_load(args.nfr.read_text()) if args.nfr and args.nfr.exists() else {}

    checklist = build_checklist(instances, args.received, nfr)
    args.out.write_text(json.dumps(checklist, sort_keys=True, indent=2) + "\n")
    if args.md:
        args.md.write_text(render_md(checklist))

    s = checklist["summary"]
    print(f"wrote {args.out}: {s['received']}/{s['total']} received, "
          f"{s['missing_required']} required still missing", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
