#!/usr/bin/env python3
"""Per-job state machine and completeness gate over a boundary_manifest.json.

States (per SKILL.md Phase 2-5):
    flagged -> confirmed -> translate -> trial -> validating -> complete
                        \\-> not-a-boundary-job (terminal, no further work)
                                       \\-> deferred (reason required)

Usage:
    python3 status.py summary [--manifest boundary_manifest.json]
    python3 status.py advance <job> --status <state> [--note "..."] [--manifest ...]
    python3 status.py confirm <job> --result <true|false> [--note "..."] [--manifest ...]
    python3 status.py reopen <job> --reason "..." [--manifest ...]
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_STATES = {
    "flagged", "confirmed", "translate", "trial", "validating",
    "complete", "not-a-boundary-job", "deferred",
}
TERMINAL_STATES = {"complete", "not-a-boundary-job", "deferred"}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        print(f"error: manifest {path} not found -- run boundary_job_scanner.py first", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2))


def find_job(manifest: dict, job_name: str):
    for row in manifest.get("jobs", []):
        if row.get("job") == job_name:
            return row
    return None


def cmd_summary(args):
    manifest = load_manifest(args.manifest)
    rows = manifest.get("jobs", [])
    total = len(rows)
    by_status = {}
    incomplete = []
    deferred_without_reason = []
    unconfirmed_past_flagged = []

    for row in rows:
        status = row.get("status", "flagged")
        by_status[status] = by_status.get(status, 0) + 1
        if status not in TERMINAL_STATES:
            incomplete.append((row.get("job"), status))
        if status == "deferred" and not row.get("deferred_reason"):
            deferred_without_reason.append(row.get("job"))
        if status not in ("flagged", "not-a-boundary-job") and row.get("confirmed") is None:
            unconfirmed_past_flagged.append(row.get("job"))

    print(f"Total flagged jobs: {total}")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")

    ok = True
    if incomplete:
        ok = False
        print(f"\nINCOMPLETE ({len(incomplete)}) -- not yet complete, not-a-boundary-job, or deferred:")
        for name, status in incomplete:
            print(f"  {name}: {status}")
    if deferred_without_reason:
        ok = False
        print(f"\nDEFERRED WITHOUT REASON ({len(deferred_without_reason)}):")
        for name in deferred_without_reason:
            print(f"  {name}")
    if unconfirmed_past_flagged:
        ok = False
        print(f"\nADVANCED WITHOUT PLATFORM-TEAM CONFIRMATION ({len(unconfirmed_past_flagged)}) -- "
              "'confirm' was never run for these:")
        for name in unconfirmed_past_flagged:
            print(f"  {name}")

    if ok:
        print("\nAll flagged jobs resolved (complete / not-a-boundary-job / deferred-with-reason), all confirmed. Clean to report.")
        sys.exit(0)
    else:
        print("\nNot clean -- fix the above before claiming the boundary migration done.")
        sys.exit(1)


def cmd_confirm(args):
    if args.result not in ("true", "false"):
        print("error: --result must be 'true' or 'false'", file=sys.stderr)
        sys.exit(1)
    manifest = load_manifest(args.manifest)
    row = find_job(manifest, args.job)
    if row is None:
        print(f"error: no flagged job named '{args.job}' found", file=sys.stderr)
        sys.exit(1)

    confirmed = args.result == "true"
    row["confirmed"] = confirmed
    history = row.setdefault("history", [])
    history.append({
        "action": "confirm",
        "confirmed": confirmed,
        "note": args.note,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    row["status"] = "confirmed" if confirmed else "not-a-boundary-job"

    save_manifest(args.manifest, manifest)
    print(f"{args.job}: confirmed={confirmed} -> status={row['status']}")


def cmd_advance(args):
    if args.status not in VALID_STATES:
        print(f"error: '{args.status}' is not a valid state ({sorted(VALID_STATES)})", file=sys.stderr)
        sys.exit(1)
    if args.status == "deferred" and not args.note:
        print("error: advancing to 'deferred' requires --note with the reason", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(args.manifest)
    row = find_job(manifest, args.job)
    if row is None:
        print(f"error: no flagged job named '{args.job}' found", file=sys.stderr)
        sys.exit(1)

    if args.status not in ("flagged", "not-a-boundary-job") and row.get("confirmed") is None:
        print(f"error: '{args.job}' has not been confirmed yet -- run 'status.py confirm {args.job} --result true' first",
              file=sys.stderr)
        sys.exit(1)

    history = row.setdefault("history", [])
    history.append({
        "from": row.get("status", "flagged"),
        "to": args.status,
        "note": args.note,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    row["status"] = args.status
    if args.status == "deferred":
        row["deferred_reason"] = args.note

    save_manifest(args.manifest, manifest)
    print(f"{args.job}: -> {args.status}")


def cmd_reopen(args):
    manifest = load_manifest(args.manifest)
    row = find_job(manifest, args.job)
    if row is None:
        print(f"error: no flagged job named '{args.job}' found", file=sys.stderr)
        sys.exit(1)

    history = row.setdefault("history", [])
    history.append({
        "from": row.get("status", "flagged"),
        "to": "flagged",
        "note": f"REOPENED: {args.reason}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    row["status"] = "flagged"
    row["confirmed"] = None
    row.pop("deferred_reason", None)

    save_manifest(args.manifest, manifest)
    print(f"{args.job}: reopened -> flagged ({args.reason})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=Path("boundary_manifest.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="Print status counts; exit nonzero if incomplete")
    p_summary.set_defaults(func=cmd_summary)

    p_confirm = sub.add_parser("confirm", help="Record platform-team confirmation for a flagged job")
    p_confirm.add_argument("job")
    p_confirm.add_argument("--result", required=True, help="true or false")
    p_confirm.add_argument("--note", default=None)
    p_confirm.set_defaults(func=cmd_confirm)

    p_advance = sub.add_parser("advance", help="Advance a confirmed job to a new state")
    p_advance.add_argument("job")
    p_advance.add_argument("--status", required=True)
    p_advance.add_argument("--note", default=None)
    p_advance.set_defaults(func=cmd_advance)

    p_reopen = sub.add_parser("reopen", help="Reopen a job back to flagged/unconfirmed")
    p_reopen.add_argument("job")
    p_reopen.add_argument("--reason", required=True)
    p_reopen.set_defaults(func=cmd_reopen)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
