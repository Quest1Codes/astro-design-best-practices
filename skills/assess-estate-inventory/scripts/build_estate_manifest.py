#!/usr/bin/env python3
"""Parse every collected discovery artifact into one `estate_manifest.json` [spec §6.2].

Deterministic: given the same input files, output is byte-identical (evidence `received_at`
timestamps excepted). Reads files only; never contacts a live AutoSys or Astro system.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §6.2 (this script's spec)
  - `_lib/autosys_jil/parser.py` (JIL parsing), `calendars.py` (autocal_asc), `config.py`
    (config.$AUTOSERV / agentparm.txt), `manifest.py` (serialization, redaction, evidence,
    validation)

Multiple `--instance ID=path.jil` flags for the same ID are applied in the given order (JIL
ordering semantics: later update_job/override_job blocks modify earlier definitions) [plan §11.4].

Usage:
    python3 build_estate_manifest.py \\
        --instance ACE=jobs.jil --instance ACE=machines.jil --instance PRD=prd.jil \\
        --autocal ACE=calendars_export.txt --globals ACE=globals.txt \\
        --config ACE=config.ACE --agentparm ACE=agentparm.txt \\
        --evidence evidence.json --nfr answers.yaml \\
        --out estate_manifest.json [--no-redact] [--strict]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import calendars as calendars_mod  # noqa: E402
from autosys_jil import config as config_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil.models import Estate, Instance  # noqa: E402
from autosys_jil.parser import finalize, parse_text  # noqa: E402


def _parse_kv_list(items: list[str]) -> list[tuple[str, str]]:
    out = []
    for item in items:
        if "=" not in item:
            print(f"error: expected INSTANCE=path, got {item!r}", file=sys.stderr)
            sys.exit(1)
        instance, path = item.split("=", 1)
        out.append((instance, path))
    return out


def build(args) -> Estate:
    estate = Estate()

    for instance_id, path in _parse_kv_list(args.instance or []):
        inst = estate.instances.setdefault(instance_id, Instance(id=instance_id))
        text = Path(path).read_text(errors="replace")
        parse_text(text, file=path, instance=instance_id, into=inst)

    for instance_id, path in _parse_kv_list(args.autocal or []):
        inst = estate.instances.setdefault(instance_id, Instance(id=instance_id))
        cals = calendars_mod.parse_autocal_asc(Path(path).read_text(errors="replace"))
        inst.calendars.update(cals)

    for instance_id, path in _parse_kv_list(args.globals or []):
        inst = estate.instances.setdefault(instance_id, Instance(id=instance_id))
        # autorep -G output: "Global Name  Value  Last Changed" columns, fixed-width like autorep -M.
        from autosys_jil.models import GlobalVar
        text = Path(path).read_text(errors="replace")
        for line in text.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2 and parts[0] not in ("Global", "___"):
                inst.globals[parts[0]] = GlobalVar(name=parts[0], value=parts[1].strip())

    for instance_id, path in _parse_kv_list(args.config or []):
        inst = estate.instances.setdefault(instance_id, Instance(id=instance_id))
        inst.config = config_mod.parse_config_autoserv(Path(path).read_text(errors="replace"))

    for instance_id, path in _parse_kv_list(args.agentparm or []):
        inst = estate.instances.setdefault(instance_id, Instance(id=instance_id))
        ap = config_mod.parse_agentparm(Path(path).read_text(errors="replace"))
        machine_hint = Path(path).stem
        inst.agent_capabilities[machine_hint] = sorted(config_mod.agent_capabilities(ap))

    for inst in estate.instances.values():
        finalize(inst)

    if args.evidence and Path(args.evidence).exists():
        payload = json.loads(Path(args.evidence).read_text())
        from autosys_jil.models import Evidence
        for e in payload.get("evidence", []):
            estate.evidence.append(Evidence(**e))

    if args.nfr and Path(args.nfr).exists():
        import yaml
        estate.nfr = yaml.safe_load(Path(args.nfr).read_text()) or {}

    if not args.no_redact:
        redact_hits = manifest_mod.redact(estate)
        estate.notes["redaction_hits"] = redact_hits

    return estate


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instance", action="append", metavar="ID=path.jil",
                    help="repeatable; applied in order per instance")
    ap.add_argument("--autocal", action="append", metavar="ID=calendars.txt")
    ap.add_argument("--globals", action="append", metavar="ID=globals.txt")
    ap.add_argument("--config", action="append", metavar="ID=config.AUTOSERV")
    ap.add_argument("--agentparm", action="append", metavar="ID=agentparm.txt")
    ap.add_argument("--evidence", type=Path, default=None)
    ap.add_argument("--nfr", type=Path, default=None)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--no-redact", action="store_true",
                    help="refused unless --out is under a .work/ directory (plan §11.6)")
    ap.add_argument("--strict", action="store_true", help="exit nonzero if any unknowns/validation problems")
    args = ap.parse_args(argv)

    if not args.instance:
        print("error: at least one --instance ID=path.jil is required", file=sys.stderr)
        return 1

    if args.no_redact and ".work" not in args.out.resolve().parts:
        print("error: --no-redact is refused when writing outside a .work/ directory (plan §11.6)",
              file=sys.stderr)
        return 1

    estate = build(args)

    problems = manifest_mod.validate(estate)
    total_unknowns = sum(
        len(inst.unknowns.job_types) + len(inst.unknowns.attributes)
        + len(inst.unknowns.condition_parse_failures) + len(inst.unknowns.unresolved_refs)
        for inst in estate.instances.values()
    )

    manifest_mod.to_json(estate, args.out, tool="build_estate_manifest.py")

    total_jobs = sum(len(inst.jobs) for inst in estate.instances.values())
    print(f"wrote {args.out}: {len(estate.instances)} instance(s), {total_jobs} job(s), "
          f"{total_unknowns} unknown(s), {len(problems)} validation problem(s)", file=sys.stderr)
    for p in problems[:20]:
        print(f"  validate: {p}", file=sys.stderr)

    if args.strict and (total_unknowns or problems):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
