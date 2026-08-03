#!/usr/bin/env python3
"""Per-machine-group state machine and completeness gate over a topology_manifest.json.

States (per SKILL.md Phase 5):
    pending -> assessed -> planned -> piloted -> migrating -> cutover -> complete
                                                             \\-> deferred (reason required)

Usage:
    python3 status.py summary [--manifest topology_manifest.json]
    python3 status.py advance <machine> --status <state> [--note "..."] [--manifest topology_manifest.json]
    python3 status.py reopen <machine> --reason "..." [--manifest topology_manifest.json]
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_STATES = {
    "pending", "assessed", "planned", "piloted", "migrating", "cutover",
    "complete", "deferred",
}
TERMINAL_STATES = {"complete", "deferred"}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        print(f"error: manifest {path} not found -- run agent_fleet_inventory.py first", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2))


def find_machine(manifest: dict, name: str):
    for record in manifest.get("machines", []):
        if record.get("name") == name:
            return record
    return None


def cmd_summary(args):
    manifest = load_manifest(args.manifest)
    machines = manifest.get("machines", [])
    total = len(machines)
    by_status = {}
    incomplete = []
    deferred_without_reason = []
    needs_review_targets = []

    for record in machines:
        status = record.get("status", "pending")
        by_status[status] = by_status.get(status, 0) + 1
        if status not in TERMINAL_STATES:
            incomplete.append((record.get("name"), status))
        if status == "deferred" and not record.get("deferred_reason"):
            deferred_without_reason.append(record.get("name"))
        if record.get("recommended_target") == "needs-review" and status not in ("pending",):
            needs_review_targets.append(record.get("name"))

    print(f"Total machine groups: {total}")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")

    ok = True
    if incomplete:
        ok = False
        print(f"\nINCOMPLETE ({len(incomplete)}) -- not yet complete or deferred:")
        for name, status in incomplete:
            print(f"  {name}: {status}")
    if deferred_without_reason:
        ok = False
        print(f"\nDEFERRED WITHOUT REASON ({len(deferred_without_reason)}):")
        for name in deferred_without_reason:
            print(f"  {name}")
    if needs_review_targets:
        ok = False
        print(f"\nSTILL 'needs-review' TARGET PAST PENDING ({len(needs_review_targets)}) -- "
              "a topology decision (Hosted/Hybrid/Bridge) was never actually recorded:")
        for name in needs_review_targets:
            print(f"  {name}")

    if ok:
        print("\nAll machine groups complete or deferred-with-reason, with recorded targets. Clean to report.")
        sys.exit(0)
    else:
        print("\nNot clean -- fix the above before claiming the topology migration done.")
        sys.exit(1)


def cmd_advance(args):
    if args.status not in VALID_STATES:
        print(f"error: '{args.status}' is not a valid state ({sorted(VALID_STATES)})", file=sys.stderr)
        sys.exit(1)
    if args.status == "deferred" and not args.note:
        print("error: advancing to 'deferred' requires --note with the reason", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(args.manifest)
    record = find_machine(manifest, args.machine)
    if record is None:
        print(f"error: no machine named '{args.machine}' found", file=sys.stderr)
        sys.exit(1)

    if args.target:
        record["recommended_target"] = args.target

    history = record.setdefault("history", [])
    history.append({
        "from": record.get("status", "pending"),
        "to": args.status,
        "note": args.note,
        "target_at_transition": record.get("recommended_target"),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    record["status"] = args.status
    if args.status == "deferred":
        record["deferred_reason"] = args.note

    save_manifest(args.manifest, manifest)
    print(f"{args.machine}: -> {args.status}" + (f" (target: {args.target})" if args.target else ""))


def cmd_reopen(args):
    manifest = load_manifest(args.manifest)
    record = find_machine(manifest, args.machine)
    if record is None:
        print(f"error: no machine named '{args.machine}' found", file=sys.stderr)
        sys.exit(1)

    history = record.setdefault("history", [])
    history.append({
        "from": record.get("status", "pending"),
        "to": "pending",
        "note": f"REOPENED: {args.reason}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    record["status"] = "pending"
    record.pop("deferred_reason", None)

    save_manifest(args.manifest, manifest)
    print(f"{args.machine}: reopened -> pending ({args.reason})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=Path("topology_manifest.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="Print status counts; exit nonzero if incomplete")
    p_summary.set_defaults(func=cmd_summary)

    p_advance = sub.add_parser("advance", help="Advance a machine group to a new state")
    p_advance.add_argument("machine")
    p_advance.add_argument("--status", required=True)
    p_advance.add_argument("--note", default=None)
    p_advance.add_argument("--target", default=None,
                            help="Record/update recommended_target, e.g. hosted / hybrid / bridge")
    p_advance.set_defaults(func=cmd_advance)

    p_reopen = sub.add_parser("reopen", help="Reopen a machine group back to pending")
    p_reopen.add_argument("machine")
    p_reopen.add_argument("--reason", required=True)
    p_reopen.set_defaults(func=cmd_reopen)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
