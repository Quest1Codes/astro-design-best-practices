#!/usr/bin/env python3
"""One state machine + completeness gate for every manifest (replaces the four legacy
`migrating-*/scripts/status.py` copies).

Deterministic: given identical manifest content and command, the resulting manifest and exit
code are byte-identical. Reads/writes local files only; never contacts a live AutoSys or Astro.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §1.12 (status.py spec: workflows, CLI, semantics)
  - `workflows.yaml` in this package (the six workflows: assessment, translation, topology,
    k8s-parity, boundary, cutover)
  - Behavioural parity target: skills/migrating-autosys-to-astronomer/scripts/status.py
    ("no silent omissions": deferred requires a reason; `summary` exits nonzero on any
    non-terminal unit or a reason-less deferred)

State is stored under `manifest["status"][workflow]["units"][unit_id]`, independent of the rest
of the manifest layout, so the same engine works whether `manifest` is a full `_lib.manifest`
Estate JSON or a lightweight companion manifest (topology/k8s-parity/boundary scripts each write
their own small JSON file today, per REFACTOR-FILE-SPEC.md §7.2-7.4). This module never
constructs `autosys_jil.models.Estate` -- it only touches the `status` sub-tree via plain dicts.

CLI:
    python3 -m autosys_jil.status summary --workflow translation [--manifest manifest.json]
    python3 -m autosys_jil.status advance <unit-id> --workflow translation --status fix-lint \\
        [--unit-type job] [--note "..."] [--manifest manifest.json]
    python3 -m autosys_jil.status reopen <unit-id> --workflow translation --reason "..." \\
        [--manifest manifest.json]
    python3 -m autosys_jil.status gate <workflow> [--manifest manifest.json]   # exit code only
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

import yaml

_HERE = Path(__file__).resolve().parent
_WORKFLOWS_PATH = _HERE / "workflows.yaml"


class WorkflowError(ValueError):
    pass


def load_workflows() -> dict[str, dict]:
    return yaml.safe_load(_WORKFLOWS_PATH.read_text())


def _workflow(name: str) -> dict:
    workflows = load_workflows()
    if name not in workflows:
        raise WorkflowError(f"unknown workflow {name!r}; known: {sorted(workflows)}")
    return workflows[name]


def load_manifest(path: Path) -> dict:
    if not path.exists():
        print(f"error: manifest {path} not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


def _units(manifest: dict, workflow: str) -> dict[str, dict]:
    status = manifest.setdefault("status", {})
    wf = status.setdefault(workflow, {"units": {}})
    return wf.setdefault("units", {})


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ============================================================================ engine

def advance(manifest: dict, workflow: str, unit_id: str, new_state: str, *,
           unit_type: str | None = None, note: str | None = None,
           disposition: str | None = None) -> dict:
    """Move `unit_id` to `new_state` in `workflow`, recording history. Creates the unit if new.

    Raises WorkflowError if `new_state` is not a valid state for `workflow`, if `new_state` is a
    deferred/rollback state and `note` is empty (parity with the legacy scripts' "deferred
    requires a reason" rule), or if `disposition` is given but not one of the workflow's
    declared `dispositions` (only `k8s-parity` declares any, per its legacy status.py: state and
    disposition are independent dimensions there -- an item can be classified long before it is
    planned/piloted).
    """
    spec = _workflow(workflow)
    if new_state not in spec["states"]:
        raise WorkflowError(f"'{new_state}' is not a valid state for workflow {workflow!r} "
                            f"({spec['states']})")
    if new_state in spec.get("deferred_states", []) and not note:
        raise WorkflowError(f"advancing to {new_state!r} requires a reason (--note/--reason)")
    valid_dispositions = spec.get("dispositions", [])
    if disposition is not None and valid_dispositions and disposition not in valid_dispositions:
        raise WorkflowError(f"'{disposition}' is not a valid disposition for workflow {workflow!r} "
                            f"({valid_dispositions})")

    units = _units(manifest, workflow)
    record = units.setdefault(unit_id, {
        "unit_id": unit_id, "unit_type": unit_type, "state": spec["states"][0],
        "cycle": 0, "history": [],
    })
    if unit_type is not None:
        record["unit_type"] = unit_type

    from_state = record["state"]
    if new_state in spec.get("repeatable", []) and new_state == from_state:
        record["cycle"] = record.get("cycle", 0) + 1
    if disposition is not None:
        record["disposition"] = disposition
    record["history"].append({
        "from": from_state, "to": new_state, "note": note, "timestamp": _now(),
        "cycle": record["cycle"] if new_state in spec.get("repeatable", []) else None,
        "disposition": disposition,
    })
    record["state"] = new_state
    if new_state in spec.get("deferred_states", []):
        record["deferred_reason"] = note
    else:
        record.pop("deferred_reason", None)
    return record


def reopen(manifest: dict, workflow: str, unit_id: str, reason: str) -> dict:
    """Reset a unit back to the workflow's initial state, recording why."""
    spec = _workflow(workflow)
    units = _units(manifest, workflow)
    if unit_id not in units:
        raise WorkflowError(f"no unit {unit_id!r} in workflow {workflow!r}")
    record = units[unit_id]
    initial = spec["states"][0]
    record["history"].append({
        "from": record["state"], "to": initial, "note": f"REOPENED: {reason}", "timestamp": _now(),
        "cycle": None,
    })
    record["state"] = initial
    record["cycle"] = 0
    record.pop("deferred_reason", None)
    return record


def completeness(manifest: dict, workflow: str) -> dict[str, Any]:
    """Compute the summary/gate result for one workflow without mutating the manifest."""
    spec = _workflow(workflow)
    units = _units(manifest, workflow)
    terminal = set(spec.get("terminal", []))
    deferred_states = set(spec.get("deferred_states", []))
    initial_state = spec["states"][0]
    has_dispositions = bool(spec.get("dispositions"))

    by_state: dict[str, int] = {}
    incomplete: list[tuple[str, str]] = []
    deferred_without_reason: list[str] = []
    advanced_without_disposition: list[str] = []
    for unit_id, record in sorted(units.items()):
        state = record.get("state", initial_state)
        by_state[state] = by_state.get(state, 0) + 1
        if state not in terminal:
            incomplete.append((unit_id, state))
        if state in deferred_states and not record.get("deferred_reason"):
            deferred_without_reason.append(unit_id)
        if has_dispositions and state != initial_state and not record.get("disposition"):
            advanced_without_disposition.append(unit_id)

    clean = not incomplete and not deferred_without_reason and not advanced_without_disposition
    return {
        "workflow": workflow, "total": len(units), "by_state": by_state,
        "incomplete": incomplete, "deferred_without_reason": deferred_without_reason,
        "advanced_without_disposition": advanced_without_disposition,
        "clean": clean,
    }


# ============================================================================ CLI

def cmd_summary(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    result = completeness(manifest, args.workflow)
    print(f"Workflow: {result['workflow']}")
    print(f"Total units: {result['total']}")
    for state, count in sorted(result["by_state"].items()):
        print(f"  {state}: {count}")
    if result["incomplete"]:
        print(f"\nINCOMPLETE ({len(result['incomplete'])}) -- not yet in a terminal state:")
        for unit_id, state in result["incomplete"]:
            print(f"  {unit_id}: {state}")
    if result["deferred_without_reason"]:
        print(f"\nDEFERRED WITHOUT REASON ({len(result['deferred_without_reason'])}) "
              f"-- violates 'no silent omissions':")
        for unit_id in result["deferred_without_reason"]:
            print(f"  {unit_id}")
    if result["advanced_without_disposition"]:
        print(f"\nADVANCED WITHOUT A RECORDED DISPOSITION ({len(result['advanced_without_disposition'])}):")
        for unit_id in result["advanced_without_disposition"]:
            print(f"  {unit_id}")
    if result["clean"]:
        print("\nAll units terminal (or deferred-with-reason). Clean to report.")
        sys.exit(0)
    print("\nNot clean -- fix the above before claiming this workflow done.")
    sys.exit(1)


def cmd_advance(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    try:
        record = advance(manifest, args.workflow, args.unit_id, args.status,
                         unit_type=args.unit_type, note=args.note, disposition=args.disposition)
    except WorkflowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    save_manifest(args.manifest, manifest)
    suffix = f" (disposition: {record['disposition']})" if record.get("disposition") else ""
    print(f"[{args.workflow}] {args.unit_id}: -> {record['state']}{suffix}")


def cmd_reopen(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    try:
        record = reopen(manifest, args.workflow, args.unit_id, args.reason)
    except WorkflowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    save_manifest(args.manifest, manifest)
    print(f"[{args.workflow}] {args.unit_id}: reopened -> {record['state']} ({args.reason})")


def cmd_gate(args: argparse.Namespace) -> None:
    """Exit code only (for CI); prints nothing on success, a one-line reason on failure."""
    manifest = load_manifest(args.manifest)
    result = completeness(manifest, args.workflow)
    if result["clean"]:
        sys.exit(0)
    print(f"gate failed for {args.workflow}: {len(result['incomplete'])} incomplete, "
          f"{len(result['deferred_without_reason'])} deferred without reason, "
          f"{len(result['advanced_without_disposition'])} advanced without disposition", file=sys.stderr)
    sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="Print per-workflow status counts; exit nonzero if incomplete")
    p_summary.add_argument("--workflow", required=True, choices=sorted(load_workflows()))
    p_summary.set_defaults(func=cmd_summary)

    p_advance = sub.add_parser("advance", help="Advance a unit to a new state")
    p_advance.add_argument("unit_id")
    p_advance.add_argument("--workflow", required=True, choices=sorted(load_workflows()))
    p_advance.add_argument("--status", required=True, dest="status")
    p_advance.add_argument("--unit-type", default=None)
    p_advance.add_argument("--note", default=None)
    p_advance.add_argument("--disposition", default=None,
                           help="only meaningful for workflows that declare 'dispositions' (currently k8s-parity)")
    p_advance.set_defaults(func=cmd_advance)

    p_reopen = sub.add_parser("reopen", help="Reopen a unit back to the workflow's initial state")
    p_reopen.add_argument("unit_id")
    p_reopen.add_argument("--workflow", required=True, choices=sorted(load_workflows()))
    p_reopen.add_argument("--reason", required=True)
    p_reopen.set_defaults(func=cmd_reopen)

    p_gate = sub.add_parser("gate", help="Exit 0 if the workflow is clean, else 1 (for CI)")
    p_gate.add_argument("--workflow", required=True, choices=sorted(load_workflows()))
    p_gate.set_defaults(func=cmd_gate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0  # unreachable: cmd_* call sys.exit directly, matching legacy script behaviour


if __name__ == "__main__":
    sys.exit(main())
