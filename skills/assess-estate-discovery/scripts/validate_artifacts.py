#!/usr/bin/env python3
"""Sniff each received discovery artifact's shape, hash it, and record it as evidence
[spec §6.1].

Deterministic: given the same files, output is byte-identical (`received_at` timestamps
excepted -- see `_lib.autosys_jil.manifest.add_evidence`).
Reads files only; never contacts a live AutoSys or Astro system.

Refuses to classify an unrecognized file kind unless `--allow-unknown` is passed -- silently
absorbing an unrecognized artifact type is exactly the failure mode this script exists to catch.

Usage:
    python3 validate_artifacts.py --received ./received/ --out evidence.json [--allow-unknown]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil.models import Estate  # noqa: E402

_SNIFFERS: list[tuple[str, "callable"]] = []


def sniffer(kind: str):
    def deco(fn):
        _SNIFFERS.append((kind, fn))
        return fn
    return deco


@sniffer("jil_export")
def _is_jil(head: str, name: str) -> bool:
    return "insert_job:" in head or "insert_machine:" in head


@sniffer("autorep_machine_report")
def _is_machine_report(head: str, name: str) -> bool:
    return "machine name" in head.lower() and "max load" in head.lower()


@sniffer("autorep_global_report")
def _is_global_report(head: str, name: str) -> bool:
    return re.search(r"global\s+name", head, re.I) is not None


@sniffer("autocal_asc_export")
def _is_calendar(head: str, name: str) -> bool:
    return re.search(r"^Calendar\s*:", head, re.M) is not None or bool(
        re.search(r"^\d{1,2}/\d{1,2}/\d{4}", head, re.M))


@sniffer("config_autoserv")
def _is_config(head: str, name: str) -> bool:
    return bool(re.search(r"^AUTOSERV\s*=", head, re.M)) or "config." in name.lower()


@sniffer("agentparm")
def _is_agentparm(head: str, name: str) -> bool:
    return "agentparm" in name.lower()


@sniffer("safex_xml")
def _is_safex(head: str, name: str) -> bool:
    return name.lower().endswith(".xml") and ("<policy" in head.lower() or "eem" in head.lower())


@sniffer("run_history_csv_or_report")
def _is_history(head: str, name: str) -> bool:
    if name.lower().endswith(".csv"):
        try:
            cols = {c.strip().lower() for c in head.splitlines()[0].split(",")}
        except IndexError:
            return False
        return bool({"job", "run_num", "start", "end", "status"} & cols)
    return bool(re.search(r"job name.*last start.*last end.*st/ex", head, re.I))


@sniffer("event_archive_csv")
def _is_event_archive(head: str, name: str) -> bool:
    if not name.lower().endswith(".csv"):
        return False
    try:
        cols = {c.strip().lower() for c in head.splitlines()[0].split(",")}
    except IndexError:
        return False
    return bool({"event", "job"} & cols) and "event" in cols


def detect_kind(path: Path) -> str | None:
    try:
        head = path.read_text(errors="replace")[:8000]
    except Exception:
        return None
    for kind, fn in _SNIFFERS:
        try:
            if fn(head, path.name):
                return kind
        except Exception:
            continue
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--received", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--allow-unknown", action="store_true")
    args = ap.parse_args(argv)

    if not args.received.exists():
        print(f"error: {args.received} not found", file=sys.stderr)
        return 1

    estate = Estate()
    unknown: list[str] = []
    for path in sorted(args.received.iterdir()):
        if not path.is_file():
            continue
        kind = detect_kind(path)
        if kind is None:
            unknown.append(path.name)
            if not args.allow_unknown:
                continue
            kind = "unknown"
        manifest_mod.add_evidence(estate, path, kind=kind)

    if unknown and not args.allow_unknown:
        print(f"error: {len(unknown)} file(s) did not match any known artifact shape "
              f"(pass --allow-unknown to include them as kind=unknown):", file=sys.stderr)
        for name in unknown:
            print(f"  {name}", file=sys.stderr)
        return 1

    import json
    payload = {
        "generated_by": manifest_mod.generated_by("validate_artifacts.py"),
        "evidence": [
            {"path": e.path, "sha256": e.sha256, "kind": e.kind, "size": e.size, "received_at": e.received_at}
            for e in estate.evidence
        ],
        "unknown_files": unknown,
    }
    args.out.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(f"wrote {args.out}: {len(estate.evidence)} artifact(s) validated, "
          f"{len(unknown)} unknown", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
