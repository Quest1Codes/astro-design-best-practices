#!/usr/bin/env python3
"""Go/no-go checklist for cutting over one box [spec §7.6].

Deterministic: given the same manifest and parity-cycle files, output is byte-identical.
Reads local files only; never contacts a live AutoSys or Astro system.

`go` only if: >= --min-clean-cycles consecutive clean parity cycles, every upstream box (per
manifest.graph's cross-box edges) is already at or past `cut` in the cutover workflow, no open
`deferred` children, and a rollback rehearsal is recorded for this wave
(`manifest.status.cutover.units[<box>].rollback_rehearsed`, set manually -- this script does not
and cannot verify a rehearsal actually happened, only that someone recorded one).

Usage:
    python3 cutover_gate.py --manifest estate_manifest.json --box ACE:some_box \\
        --parity-cycles parity_cycle_1.json parity_cycle_2.json parity_cycle_3.json \\
        --min-clean-cycles 3
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402


def check(estate, box_key: str, parity_cycles: list[dict], min_clean_cycles: int) -> dict:
    checks: dict[str, dict] = {}

    consecutive_clean = 0
    for cycle in reversed(parity_cycles):  # most recent first
        if cycle.get("clean"):
            consecutive_clean += 1
        else:
            break
    checks["clean_cycles"] = {
        "pass": consecutive_clean >= min_clean_cycles,
        "detail": f"{consecutive_clean} consecutive clean cycle(s) (need >= {min_clean_cycles})",
    }

    upstream_boxes = _upstream_boxes(estate, box_key)
    cutover_units = estate.status.get("cutover", {}).get("units", {}) if isinstance(estate.status, dict) else {}
    upstream_ready = all(
        cutover_units.get(u, {}).get("state") in ("cut", "observed", "decommissioned")
        for u in upstream_boxes
    ) if upstream_boxes else True
    checks["upstream_ready"] = {
        "pass": upstream_ready,
        "detail": f"{len(upstream_boxes)} upstream box(es); all >= cut: {upstream_ready}",
    }

    inst_id, _, box_name = box_key.partition(":")
    inst = estate.instances.get(inst_id)
    open_deferred = []
    if inst and box_name in inst.boxes:
        for child in inst.boxes[box_name].children:
            child_key = f"{inst_id}:{child}"
            unit_state = estate.status.get("translation", {}).get("units", {}).get(child_key, {}) \
                if isinstance(estate.status, dict) else {}
            if unit_state.get("state") == "deferred":
                open_deferred.append(child_key)
    checks["no_open_deferred_children"] = {
        "pass": not open_deferred,
        "detail": f"{len(open_deferred)} deferred child unit(s): {open_deferred}",
    }

    box_unit = cutover_units.get(box_key, {})
    rehearsed = bool(box_unit.get("rollback_rehearsed"))
    checks["rollback_rehearsed"] = {
        "pass": rehearsed,
        "detail": "recorded" if rehearsed else
                  "NOT recorded -- set manifest.status.cutover.units[box].rollback_rehearsed=true "
                  "only after actually rehearsing (reference/rollback.md)",
    }

    go = all(c["pass"] for c in checks.values())
    return {"box": box_key, "go": go, "checks": checks}


def _box_containing(estate, job_key: str) -> str | None:
    """job_key ('INST:name') -> 'INST:box_name' if that job is a box member, else None."""
    inst_id, _, name = job_key.partition(":")
    inst = estate.instances.get(inst_id)
    if not inst:
        return None
    job = inst.jobs.get(name)
    if job and job.box_name:
        return f"{inst_id}:{job.box_name}"
    return None


def _upstream_boxes(estate, box_key: str) -> set[str]:
    """Every OTHER box that a job inside `box_key` has a condition edge pointing into."""
    graph_edges = estate.graph.get("edges", []) if isinstance(estate.graph, dict) else []
    upstream: set[str] = set()
    for e in graph_edges:
        if not e.get("kind", "").startswith("condition"):
            continue
        from_box = _box_containing(estate, e["from"])
        if from_box != box_key:
            continue
        to_box = _box_containing(estate, e["to"])
        if to_box and to_box != box_key:
            upstream.add(to_box)
    return upstream


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--box", required=True, metavar="INSTANCE:box_name")
    ap.add_argument("--parity-cycles", type=Path, nargs="+", required=True)
    ap.add_argument("--min-clean-cycles", type=int, default=3)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found", file=sys.stderr)
        return 1
    for p in args.parity_cycles:
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1

    estate = manifest_mod.from_json(args.manifest)
    cycles = [json.loads(p.read_text()) for p in args.parity_cycles]
    cycles.sort(key=lambda c: c.get("cycle", 0))

    result = check(estate, args.box, cycles, args.min_clean_cycles)

    print(f"Cutover gate for {result['box']}: {'GO' if result['go'] else 'NO-GO'}", file=sys.stderr)
    for name, c in result["checks"].items():
        mark = "PASS" if c["pass"] else "FAIL"
        print(f"  [{mark}] {name}: {c['detail']}", file=sys.stderr)

    return 0 if result["go"] else 1


if __name__ == "__main__":
    sys.exit(main())
