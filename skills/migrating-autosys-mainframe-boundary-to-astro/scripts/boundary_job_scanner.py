#!/usr/bin/env python3
"""Flag likely mainframe-boundary jobs in a jil_inventory.py manifest.

Heuristic only: matches z/OS-style dataset naming conventions, known MFT/
Connect:Direct keyword references, FT job types, and gateway-suggestive
hostnames across each job's command, watch_file, machine, and raw_extra
values. A flag here is NOT a confirmed boundary job -- SKILL.md Phase 2
requires platform-team confirmation for every flagged job. Likewise,
silence from this scanner is not proof a job isn't boundary-related --
obscure or renamed conventions won't match.

Usage:
    python3 boundary_job_scanner.py --manifest manifest.json --out boundary_manifest.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

# z/OS dataset names are conventionally all-caps, dot-separated qualifiers,
# each up to 8 characters, e.g. PROD.FINANCE.DAILY.EXTRACT. This is a
# heuristic shape match, not a validation of real z/OS naming rules.
DSN_PATTERN = re.compile(r"\b[A-Z0-9$#@]{1,8}(?:\.[A-Z0-9$#@]{1,8}){2,}\b")

MFT_KEYWORDS = re.compile(
    r"\b(connect[:_-]?direct|ndm|cpwd|mft|sterling|gxs|mainframe|z/?os|jcl|jes|racf|cics)\b",
    re.IGNORECASE,
)

GATEWAY_HOST_HINTS = re.compile(r"\b(\w*mft\w*|\w*gateway\w*|\w*zos\w*|\w*mainframe\w*|\w*ndm\w*)\b", re.IGNORECASE)


def collect_text_fields(job: dict):
    """All string values worth scanning for a given job record."""
    fields = []
    for key in ("command", "machine"):
        if job.get(key):
            fields.append((key, job[key]))
    schedule = job.get("schedule") or {}
    # watch_file lives in known_attributes for job_type f, raw_extra otherwise
    known = job.get("known_attributes") or {}
    if known.get("watch_file"):
        fields.append(("watch_file", known["watch_file"]))
    extra = job.get("raw_extra") or {}
    for k, v in extra.items():
        if isinstance(v, str):
            fields.append((f"raw_extra.{k}", v))
    return fields


def scan_job(job: dict):
    signals = []
    fields = collect_text_fields(job)

    for field_name, value in fields:
        if DSN_PATTERN.search(value):
            signals.append(f"dataset_naming_pattern in {field_name}: {value}")
        if MFT_KEYWORDS.search(value):
            signals.append(f"mft_or_mainframe_keyword in {field_name}: {value}")
        if GATEWAY_HOST_HINTS.search(value):
            signals.append(f"gateway_hostname_hint in {field_name}: {value}")

    job_type = (job.get("job_type") or "").lower()
    if job_type == "ft":
        signals.append("job_type_ft")
    if job_type == "f" and job.get("known_attributes", {}).get("watch_file"):
        # already covered by dataset/keyword scan above if it matches, but
        # file-watcher jobs are worth a lower-confidence generic flag too
        pass

    signals = sorted(set(signals))
    if not signals:
        confidence = None
    elif len(signals) == 1 and signals[0] == "job_type_ft":
        confidence = "low"  # FT alone is common and not necessarily mainframe-related
    elif len(signals) == 1:
        confidence = "medium"
    else:
        confidence = "high"

    return signals, confidence


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, required=True, help="manifest.json from migrating-autosys-to-astronomer")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run jil_inventory.py from "
              "migrating-autosys-to-astronomer first", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(args.manifest.read_text())
    jobs = manifest.get("jobs", [])

    flagged = []
    for job in jobs:
        signals, confidence = scan_job(job)
        if confidence is None:
            continue
        flagged.append({
            "job": job["name"],
            "signals": signals,
            "confidence": confidence,
            "status": "flagged",
            "confirmed": None,  # true / false / null (pending), set during Phase 2
            "classification": "pending",
        })

    boundary_manifest = {
        "source_manifest": str(args.manifest),
        "jobs": flagged,
        "summary": {
            "total_jobs_scanned": len(jobs),
            "flagged_count": len(flagged),
            "by_confidence": {
                level: len([f for f in flagged if f["confidence"] == level])
                for level in ("high", "medium", "low")
            },
        },
        "note": ("Every flagged job needs platform-team confirmation (SKILL.md Phase 2) before being "
                 "treated as a real boundary job. Scanner silence on a job is not proof it isn't one -- "
                 "this is a keyword/pattern heuristic, not a definitive classifier."),
    }

    indent = 2 if args.pretty else None
    args.out.write_text(json.dumps(boundary_manifest, indent=indent))
    print(f"Wrote {args.out}: {len(flagged)}/{len(jobs)} jobs flagged as possible boundary jobs "
          f"({boundary_manifest['summary']['by_confidence']})", file=sys.stderr)


if __name__ == "__main__":
    main()
