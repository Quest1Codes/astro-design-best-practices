#!/usr/bin/env python3
"""Per-unit state machine and completeness gate over a jil_inventory.py manifest.

States (per SKILL.md Phase 4):
    pending -> translate -> fix-import -> fix-lint -> fix-tests -> verify-parity -> complete
                                        \\-> deferred (reason required)

Usage:
    python3 status.py summary [--manifest manifest.json]
    python3 status.py advance <unit-id> --status <state> [--note "..."] [--manifest manifest.json]
    python3 status.py reopen <unit-id> --reason "..." [--manifest manifest.json]
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_STATES = {
    "pending", "translate", "fix-import", "fix-lint", "fix-tests",
    "verify-parity", "complete", "deferred",
}
TERMINAL_STATES = {"complete", "deferred"}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        print(f"error: manifest {path} not found -- run jil_inventory.py first", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2))


def all_units(manifest: dict):
    """Yield (collection_name, record) for every job, box, and calendar record."""
    for job in manifest.get("jobs", []):
        yield "jobs", job
    for box in manifest.get("boxes", []):
        yield "boxes", box
    for cal in manifest.get("calendars", []):
        yield "calendars", cal


def find_unit(manifest: dict, unit_id: str):
    for collection, record in all_units(manifest):
        if record.get("name") == unit_id:
            return collection, record
    return None, None


def cmd_summary(args):
    manifest = load_manifest(args.manifest)
    total = 0
    by_status = {}
    incomplete = []
    deferred_without_reason = []

    for collection, record in all_units(manifest):
        total += 1
        status = record.get("status", "pending")
        by_status[status] = by_status.get(status, 0) + 1
        if status not in TERMINAL_STATES:
            incomplete.append((collection, record.get("name"), status))
        if status == "deferred" and not record.get("deferred_reason"):
            deferred_without_reason.append((collection, record.get("name")))

    print(f"Total units: {total}")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")

    if manifest.get("warnings"):
        print(f"\nInventory warnings carried over from scan: {len(manifest['warnings'])}")

    ok = True
    if incomplete:
        ok = False
        print(f"\nINCOMPLETE ({len(incomplete)}) -- not yet complete or deferred:")
        for collection, name, status in incomplete:
            print(f"  [{collection}] {name}: {status}")
    if deferred_without_reason:
        ok = False
        print(f"\nDEFERRED WITHOUT REASON ({len(deferred_without_reason)}) -- violates 'no silent omissions':")
        for collection, name in deferred_without_reason:
            print(f"  [{collection}] {name}")

    if ok:
        print("\nAll units complete or deferred-with-reason. Clean to report.")
        sys.exit(0)
    else:
        print("\nNot clean -- fix the above before claiming the migration done.")
        sys.exit(1)


def cmd_advance(args):
    if args.status not in VALID_STATES:
        print(f"error: '{args.status}' is not a valid state ({sorted(VALID_STATES)})", file=sys.stderr)
        sys.exit(1)
    if args.status == "deferred" and not args.note:
        print("error: advancing to 'deferred' requires --note with the reason", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(args.manifest)
    collection, record = find_unit(manifest, args.unit_id)
    if record is None:
        print(f"error: no unit named '{args.unit_id}' found in jobs/boxes/calendars", file=sys.stderr)
        sys.exit(1)

    history = record.setdefault("history", [])
    history.append({
        "from": record.get("status", "pending"),
        "to": args.status,
        "note": args.note,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    record["status"] = args.status
    if args.status == "deferred":
        record["deferred_reason"] = args.note

    save_manifest(args.manifest, manifest)
    print(f"[{collection}] {args.unit_id}: -> {args.status}")


def cmd_reopen(args):
    manifest = load_manifest(args.manifest)
    collection, record = find_unit(manifest, args.unit_id)
    if record is None:
        print(f"error: no unit named '{args.unit_id}' found in jobs/boxes/calendars", file=sys.stderr)
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
    print(f"[{collection}] {args.unit_id}: reopened -> pending ({args.reason})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="Print status counts; exit nonzero if incomplete")
    p_summary.set_defaults(func=cmd_summary)

    p_advance = sub.add_parser("advance", help="Advance a unit to a new state")
    p_advance.add_argument("unit_id")
    p_advance.add_argument("--status", required=True)
    p_advance.add_argument("--note", default=None)
    p_advance.set_defaults(func=cmd_advance)

    p_reopen = sub.add_parser("reopen", help="Reopen a unit back to pending")
    p_reopen.add_argument("unit_id")
    p_reopen.add_argument("--reason", required=True)
    p_reopen.set_defaults(func=cmd_reopen)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
