#!/usr/bin/env python3
"""Per-checklist-item state machine and completeness gate over a k8s_parity_manifest.json.

States (per SKILL.md Phase 2-4):
    pending -> classified -> planned -> piloted -> complete
                                       \\-> deferred (reason required)

'classified' means a disposition (direct-port / needs-translation / superseded)
has been recorded via --disposition; the state and the disposition are tracked
separately since an item can be classified long before it's actually planned
or piloted.

Usage:
    python3 status.py summary [--manifest k8s_parity_manifest.json]
    python3 status.py advance <item> --status <state> [--disposition <d>] [--note "..."] [--manifest ...]
    python3 status.py reopen <item> --reason "..." [--manifest ...]
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_STATES = {"pending", "classified", "planned", "piloted", "complete", "deferred"}
VALID_DISPOSITIONS = {"direct-port", "needs-translation", "superseded"}
TERMINAL_STATES = {"complete", "deferred"}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        print(f"error: manifest {path} not found -- run k8s_parity_scan.py first", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2))


def find_item(manifest: dict, item_name: str):
    for row in manifest.get("checklist", []):
        if row.get("item") == item_name:
            return row
    return None


def cmd_summary(args):
    manifest = load_manifest(args.manifest)
    rows = manifest.get("checklist", [])
    total = len(rows)
    by_status = {}
    incomplete = []
    deferred_without_reason = []
    unclassified_past_pending = []

    for row in rows:
        status = row.get("status", "pending")
        by_status[status] = by_status.get(status, 0) + 1
        if status not in TERMINAL_STATES:
            incomplete.append((row.get("item"), status))
        if status == "deferred" and not row.get("deferred_reason"):
            deferred_without_reason.append(row.get("item"))
        if status != "pending" and not row.get("disposition_recorded"):
            unclassified_past_pending.append(row.get("item"))

    print(f"Total checklist items: {total}")
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
    if unclassified_past_pending:
        ok = False
        print(f"\nADVANCED WITHOUT A RECORDED DISPOSITION ({len(unclassified_past_pending)}) -- "
              "direct-port/needs-translation/superseded was never set:")
        for name in unclassified_past_pending:
            print(f"  {name}")

    if ok:
        print("\nAll checklist items complete or deferred-with-reason, all classified. Clean to report.")
        sys.exit(0)
    else:
        print("\nNot clean -- fix the above before claiming the platform migration done.")
        sys.exit(1)


def cmd_advance(args):
    if args.status not in VALID_STATES:
        print(f"error: '{args.status}' is not a valid state ({sorted(VALID_STATES)})", file=sys.stderr)
        sys.exit(1)
    if args.status == "deferred" and not args.note:
        print("error: advancing to 'deferred' requires --note with the reason", file=sys.stderr)
        sys.exit(1)
    if args.disposition and args.disposition not in VALID_DISPOSITIONS:
        print(f"error: '{args.disposition}' is not a valid disposition ({sorted(VALID_DISPOSITIONS)})", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(args.manifest)
    row = find_item(manifest, args.item)
    if row is None:
        print(f"error: no checklist item named '{args.item}' found", file=sys.stderr)
        sys.exit(1)

    if args.disposition:
        row["disposition"] = args.disposition
        row["disposition_recorded"] = True

    history = row.setdefault("history", [])
    history.append({
        "from": row.get("status", "pending"),
        "to": args.status,
        "note": args.note,
        "disposition_at_transition": row.get("disposition"),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    row["status"] = args.status
    if args.status == "deferred":
        row["deferred_reason"] = args.note

    save_manifest(args.manifest, manifest)
    print(f"{args.item}: -> {args.status}" + (f" (disposition: {args.disposition})" if args.disposition else ""))


def cmd_reopen(args):
    manifest = load_manifest(args.manifest)
    row = find_item(manifest, args.item)
    if row is None:
        print(f"error: no checklist item named '{args.item}' found", file=sys.stderr)
        sys.exit(1)

    history = row.setdefault("history", [])
    history.append({
        "from": row.get("status", "pending"),
        "to": "pending",
        "note": f"REOPENED: {args.reason}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    row["status"] = "pending"
    row.pop("deferred_reason", None)

    save_manifest(args.manifest, manifest)
    print(f"{args.item}: reopened -> pending ({args.reason})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=Path("k8s_parity_manifest.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="Print status counts; exit nonzero if incomplete")
    p_summary.set_defaults(func=cmd_summary)

    p_advance = sub.add_parser("advance", help="Advance a checklist item to a new state")
    p_advance.add_argument("item")
    p_advance.add_argument("--status", required=True)
    p_advance.add_argument("--disposition", default=None, help="direct-port / needs-translation / superseded")
    p_advance.add_argument("--note", default=None)
    p_advance.set_defaults(func=cmd_advance)

    p_reopen = sub.add_parser("reopen", help="Reopen a checklist item back to pending")
    p_reopen.add_argument("item")
    p_reopen.add_argument("--reason", required=True)
    p_reopen.set_defaults(func=cmd_reopen)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
