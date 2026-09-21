#!/usr/bin/env python3
"""Evaluate `decision-tables.yaml` against `estate_manifest.json`, writing
`manifest.architecture.decisions[]` [spec §6.4].

Deterministic: given the same manifest and rules file, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Every decision row carries the KB topic(s) that justify it and a `confidence` -- `mixed`
everywhere an Astro-side capability claim is involved, since this project did not have
Astronomer MCP access when `decision-tables.yaml` was authored (see skills/docs/HANDOFF.md §5).
A human may override any decision with `--override id=choice --reason ...`, recorded and never
silently applied.

Usage:
    python3 recommend_architecture.py --manifest estate_manifest.json
        [--override deployment_model="Hybrid" --reason "customer confirmed private network"]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402


def compute_estate_signals(estate) -> dict:
    total_jobs = sum(len(i.jobs) for i in estate.instances.values())
    machine_names: set[str] = set()
    for inst in estate.instances.values():
        machine_names.update(inst.machines)
        for job in inst.jobs.values():
            machine_names.update(job.load.machine)

    by_flag = {}
    if isinstance(estate.scores, dict):
        by_flag = estate.scores.get("estate", {}).get("by_flag", {})

    os_hints = {}
    if isinstance(estate.command_summary, dict):
        os_hints = estate.command_summary.get("os_hints", {})

    erp_flag_count = by_flag.get("erp", 0)
    zos_present = any(j.job_type in ("ZOS", "ZOSM", "ZOSDST")
                      for inst in estate.instances.values() for j in inst.jobs.values())

    return {
        "job_count_gt2000": total_jobs > 2000,
        "erp_share_high": total_jobs > 0 and (erp_flag_count / total_jobs) > 0.10,
        "svcdesk_flag_count_gt0": by_flag.get("itsm", 0) > 0,
        "many_machine_groups": len(machine_names) >= 10,
        "windows_present": os_hints.get("windows", 0) > 0,
        "zos_present": zos_present,
        "k8s_source_topology": bool(estate.nfr.get("brownfield_astro")) if isinstance(estate.nfr, dict) else False,
    }


def _nfr_check(nfr: dict, key: str, op: str, value=None) -> bool:
    v = nfr.get(key)
    if op == "is_set":
        return v is not None and v != "" and v != []
    if op == "truthy":
        return bool(v)
    if op == "eq":
        return v == value
    return False


def evaluate_decision(spec: dict, nfr: dict, signals: dict) -> dict:
    for rule in spec["rules"]:
        cond = rule["when"]
        matched = False
        if "nfr_key" in cond:
            matched = _nfr_check(nfr, cond["nfr_key"], cond["op"], cond.get("value"))
        elif "estate_signal" in cond:
            matched = bool(signals.get(cond["estate_signal"]))
        if matched:
            return {"id": rule["id"], "choice": rule["choice"], "confidence": rule["confidence"],
                    "reason": rule.get("reason", ""), "kb_topics": spec.get("kb_topics", []),
                    "overridable": True}
    d = spec["default"]
    return {"id": "default", "choice": d["choice"], "confidence": d["confidence"],
            "reason": d.get("reason", ""), "kb_topics": spec.get("kb_topics", []), "overridable": True}


def recommend(estate, rules: dict) -> dict:
    nfr = estate.nfr if isinstance(estate.nfr, dict) else {}
    signals = compute_estate_signals(estate)
    decisions = {}
    for name, spec in rules["decisions"].items():
        decisions[name] = evaluate_decision(spec, nfr, signals)
    kb_routing = sorted({t for d in decisions.values() for t in d["kb_topics"]})
    return {"decisions": decisions, "kb_routing": kb_routing, "signals_used": signals}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--rules", type=Path, default=Path(__file__).parent / "decision-tables.yaml")
    ap.add_argument("--override", action="append", default=[], metavar="ID=CHOICE")
    ap.add_argument("--reason", action="append", default=[], help="paired with --override in order")
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    rules = yaml.safe_load(args.rules.read_text())
    result = recommend(estate, rules)

    for i, ov in enumerate(args.override):
        decision_id, choice = ov.split("=", 1)
        reason = args.reason[i] if i < len(args.reason) else ""
        if decision_id not in result["decisions"]:
            print(f"error: unknown decision id {decision_id!r}", file=sys.stderr)
            return 1
        d = result["decisions"][decision_id]
        d["override"] = {"from": d["choice"], "to": choice, "reason": reason}
        d["choice"] = choice

    existing_arch = estate.architecture if isinstance(estate.architecture, dict) else {}
    existing_arch.update(result)
    estate.architecture = existing_arch
    manifest_mod.to_json(estate, args.manifest, tool="recommend_architecture.py")

    print(f"updated {args.manifest}: {len(result['decisions'])} decision(s) made, "
          f"{len(result['kb_routing'])} KB topic(s) routed", file=sys.stderr)
    for name, d in result["decisions"].items():
        print(f"  {name}: {d['choice']} ({d['confidence']})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
