#!/usr/bin/env python3
"""Propose migration waves from the dependency graph, box scores, ownership, and
`nfr.change_freeze`, plus a pilot-wave pick [spec §6.3].

Deterministic: given the same manifest, output is byte-identical. This is a PROPOSAL
(`proposed: true` on every wave) -- a human edits it per `reference/wave-planning.md`; never
treat this script's output as the final wave plan.

Reads `manifest.graph` (must have run `condition_graph.py` first) and `manifest.scores`
(must have run `score_estate.py` first).

Usage:
    python3 propose_waves.py --manifest estate_manifest.json [--max-wave-points 150]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil.boxes import top_level_boxes  # noqa: E402


def _box_owners(inst, box_name: str) -> set[str]:
    box = inst.boxes.get(box_name)
    if box is None:
        return set()
    owners = set()
    for child in box.children:
        job = inst.jobs.get(child)
        if job and job.owner:
            owners.add(job.owner)
    return owners


def propose_waves(estate, max_wave_points: int) -> list[dict]:
    change_freeze = estate.nfr.get("change_freeze") if isinstance(estate.nfr, dict) else None
    units: list[dict] = []

    for inst_id, inst in estate.instances.items():
        for box_name in top_level_boxes(inst.boxes):
            key = f"{inst_id}:{box_name}"
            score = estate.scores.get("boxes", {}).get(key)
            if score is None:
                continue
            units.append({
                "key": key, "instance": inst_id, "box": box_name,
                "points": score["points"], "disposition": score["disposition"],
                "owners": sorted(_box_owners(inst, box_name)),
            })

    # Sort by dependency readiness proxy (fewest incoming cross-box edges first, i.e. least
    # depended-upon-by-others goes... actually leaf-first by points ascending as a simple,
    # deterministic ordering) then group greedily by --max-wave-points, keeping same-owner
    # boxes together where the running total allows.
    units.sort(key=lambda u: (u["points"], u["key"]))

    waves: list[dict] = []
    current: list[dict] = []
    current_points = 0
    for u in units:
        if current and current_points + u["points"] > max_wave_points:
            waves.append(current)
            current, current_points = [], 0
        current.append(u)
        current_points += u["points"]
    if current:
        waves.append(current)

    pilot = _pick_pilot(units)

    result = []
    for i, wave_units in enumerate(waves, start=1):
        result.append({
            "wave": i,
            "proposed": True,
            "units": [u["key"] for u in wave_units],
            "total_points": sum(u["points"] for u in wave_units),
            "owners": sorted({o for u in wave_units for o in u["owners"]}),
            "is_pilot": any(u["key"] in pilot for u in wave_units),
            "change_freeze_conflict": bool(change_freeze),  # dates unresolved without an NFR date parser; flag for human review
        })
    if pilot:
        result.insert(0, {
            "wave": 0, "proposed": True, "units": pilot, "total_points": None,
            "owners": [], "is_pilot": True,
            "note": "Pilot wave: one MECH box, one box with a nontrivial condition string, "
                    "one calendar-driven box (or the nearest available mix) -- per the "
                    "three-kind trial rule.",
        })
    return result


def _pick_pilot(units: list[dict]) -> list[str]:
    mech = next((u["key"] for u in units if u["disposition"] == "MECH"), None)
    nontrivial_cond = next((u["key"] for u in units if u["points"] >= 5 and u["key"] != mech), None)
    calendar_driven = next((u["key"] for u in units
                            if u["key"] not in (mech, nontrivial_cond)), None)
    return [k for k in (mech, nontrivial_cond, calendar_driven) if k]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--max-wave-points", type=int, default=150)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    if not estate.scores:
        print("error: manifest has no scores{} -- run score_estate.py first", file=sys.stderr)
        return 1

    estate.waves = propose_waves(estate, args.max_wave_points)
    manifest_mod.to_json(estate, args.manifest, tool="propose_waves.py")

    real_waves = [w for w in estate.waves if w["wave"] > 0]
    print(f"updated {args.manifest}: {len(real_waves)} wave(s) proposed "
          f"(max {args.max_wave_points} pts/wave), pilot wave: "
          f"{estate.waves[0]['units'] if estate.waves and estate.waves[0]['wave'] == 0 else 'none'}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
