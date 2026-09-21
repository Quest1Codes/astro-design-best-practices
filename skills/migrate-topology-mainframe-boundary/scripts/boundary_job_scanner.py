#!/usr/bin/env python3
"""Flag likely mainframe-boundary jobs in an `_lib.manifest` estate manifest [spec §7.4].

Deterministic: given the same manifest, output is byte-identical.
Reads files only; never contacts a live AutoSys, Astro, or mainframe endpoint.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §7.4 (this script's spec: job-type match first, then
    `commands.analyze` hosts/paths + dataset-name regex)
  - [AS p.2549] native z/OS job types: `ZOS`, `ZOSM`, `ZOSDST` -- these are the only job types
    that name a mainframe boundary directly; everything else is a heuristic keyword/pattern
    match, never a confirmed classification.

A flag here is NOT a confirmed boundary job -- SKILL.md Phase 2 requires platform-team
confirmation for every flagged job. Likewise, silence from this scanner is not proof a job isn't
boundary-related -- obscure or renamed conventions won't match.

Usage:
    python3 boundary_job_scanner.py --manifest estate_manifest.json --out boundary_manifest.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import commands as commands_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402

# Native z/OS job types [AS p.2549] -- these ARE the mainframe boundary by definition, no
# heuristic needed.
NATIVE_ZOS_JOB_TYPES = {"ZOS", "ZOSM", "ZOSDST"}

# z/OS dataset names are conventionally all-caps, dot-separated qualifiers, each up to 8
# characters, e.g. PROD.FINANCE.DAILY.EXTRACT. This is a heuristic shape match, not a
# validation of real z/OS naming rules.
DSN_PATTERN = re.compile(r"\b[A-Z0-9$#@]{1,8}(?:\.[A-Z0-9$#@]{1,8}){2,}\b")

MFT_KEYWORDS = re.compile(
    r"\b(connect[:_-]?direct|ndm|cpwd|mft|sterling|gxs|mainframe|z/?os|jcl|jes|racf|cics)\b",
    re.IGNORECASE,
)

GATEWAY_HOST_HINTS = re.compile(r"\b(\w*mft\w*|\w*gateway\w*|\w*zos\w*|\w*mainframe\w*|\w*ndm\w*)\b", re.IGNORECASE)


def _text_fields(job) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    if job.command:
        fields.append(("command", job.command))
    for m in job.load.machine:
        fields.append(("machine", m))
    watch_file = job.attrs.get("watch_file")
    if watch_file and isinstance(watch_file.value, str):
        fields.append(("watch_file", watch_file.value))
    for k, v in job.extras.items():
        fields.append((f"extras.{k}", v))
    return fields


def scan_job(job) -> tuple[list[str], str | None]:
    signals: list[str] = []

    if job.job_type in NATIVE_ZOS_JOB_TYPES:
        signals.append(f"native_zos_job_type: {job.job_type} [AS p.2549]")

    for field_name, value in _text_fields(job):
        if DSN_PATTERN.search(value):
            signals.append(f"dataset_naming_pattern in {field_name}: {value}")
        if MFT_KEYWORDS.search(value):
            signals.append(f"mft_or_mainframe_keyword in {field_name}: {value}")
        if GATEWAY_HOST_HINTS.search(value):
            signals.append(f"gateway_hostname_hint in {field_name}: {value}")

    if job.command:
        analysis = commands_mod.analyze(job.command)
        for host in analysis.hosts:
            if GATEWAY_HOST_HINTS.search(host):
                signals.append(f"gateway_hostname_hint in command hosts: {host}")

    if job.job_type in ("FT", "FTP", "SCP", "FW"):
        signals.append(f"job_type_{job.job_type.lower()}")

    signals = sorted(set(signals))
    if not signals:
        confidence = None
    elif any(s.startswith("native_zos_job_type") for s in signals):
        confidence = "high"
    elif len(signals) == 1 and signals[0].startswith("job_type_"):
        confidence = "low"  # a bare transfer/watch job type alone is common and not necessarily mainframe-related
    elif len(signals) == 1:
        confidence = "medium"
    else:
        confidence = "high"

    return signals, confidence


def scan_estate(estate) -> dict:
    flagged = []
    total = 0
    for inst_id, inst in estate.instances.items():
        for job in inst.jobs.values():
            if job.deleted:
                continue
            total += 1
            signals, confidence = scan_job(job)
            if confidence is None:
                continue
            flagged.append({
                "instance": inst_id, "job": job.name, "job_type": job.job_type,
                "signals": signals, "confidence": confidence,
            })

    by_confidence = {level: len([f for f in flagged if f["confidence"] == level])
                     for level in ("high", "medium", "low")}
    return {
        "generated_by": manifest_mod.generated_by("boundary_job_scanner.py"),
        "jobs": flagged,
        "summary": {"total_jobs_scanned": total, "flagged_count": len(flagged),
                    "by_confidence": by_confidence},
        "note": ("Every flagged job needs platform-team confirmation (SKILL.md Phase 2) before being "
                 "treated as a real boundary job. Scanner silence on a job is not proof it isn't one -- "
                 "this is a keyword/pattern heuristic (plus the definitive ZOS/ZOSM/ZOSDST job-type "
                 "match [AS p.2549]), not a universal classifier."),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True,
                    help="estate_manifest.json from assess-estate-inventory's build_estate_manifest.py")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    result = scan_estate(estate)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(f"wrote {args.out}: {result['summary']['flagged_count']}/{result['summary']['total_jobs_scanned']} "
          f"jobs flagged as possible boundary jobs ({result['summary']['by_confidence']})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
