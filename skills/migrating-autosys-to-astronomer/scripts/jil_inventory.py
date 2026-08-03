#!/usr/bin/env python3
"""Parse a JIL export into a JSON migration manifest.

Read-only: this script never talks to a live AutoSys instance, only a JIL
text export. It enumerates every job/box/calendar it finds; classifying each
record (MECH/JUDG/REDESIGN/NONE, per reference/mapping.md) is a separate,
human/agent judgment step done after this runs -- every record starts
classification: "pending".

Usage:
    python3 jil_inventory.py estate.jil --out manifest.json
    python3 jil_inventory.py estate.jil --out manifest.json --pretty
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Job types with stable, well-documented JIL syntax across recent AutoSys/
# WA AE releases. Anything else is flagged for manual verification rather
# than assumed -- see SKILL.md hard rule 5 ("do not invent JIL syntax").
KNOWN_JOB_TYPES = {"c", "cmd", "b", "box", "f", "ft"}

# Attributes whose meaning and translation target are documented in
# reference/*.md. Anything not in this set is still captured (in
# raw_extra), just flagged as unverified.
KNOWN_ATTRIBUTES = {
    "job_type", "command", "machine", "owner", "permission",
    "condition", "box_name", "box_terminator",
    "date_conditions", "days_of_week", "start_times", "start_mins",
    "run_window", "run_calendar", "exclude_calendar",
    "alarm_if_fail", "alarm_if_terminate", "term_run_time",
    "notification_msg", "notification_emails",
    "std_out_file", "std_err_file", "description",
    "watch_file", "watch_interval",
}

BLOCK_HEADER_RE = re.compile(
    r"^(insert_job|update_job|insert_calendar|delete_job)\s*:\s*(\S+)(.*)$",
    re.IGNORECASE,
)
ATTR_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$")


def strip_comments(text: str) -> str:
    """Remove C-style /* ... */ comments, including multi-line ones."""
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def split_kv(line: str):
    m = ATTR_RE.match(line.strip())
    if not m:
        return None
    key, value = m.group(1).lower(), m.group(2).strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return key, value


def parse_blocks(raw_text: str):
    """Split a JIL export into (block_type, name, attribute_lines) tuples."""
    text = strip_comments(raw_text)
    lines = [l for l in text.splitlines() if l.strip()]

    blocks = []
    current = None

    for line in lines:
        header = BLOCK_HEADER_RE.match(line.strip())
        if header:
            if current is not None:
                blocks.append(current)
            block_type = header.group(1).lower()
            name = header.group(2)
            rest_of_header = header.group(3)
            current = {"block_type": block_type, "name": name, "lines": []}
            if rest_of_header.strip():
                # header line often carries a second attribute, e.g.
                # "insert_job: name   job_type: c"
                current["lines"].append(rest_of_header.strip())
        else:
            if current is not None:
                current["lines"].append(line.strip())
            # lines before any block header (rare stray content) are dropped
    if current is not None:
        blocks.append(current)
    return blocks


CONDITION_FUNC_RE = re.compile(r"\b([sfnd])\s*\(\s*([^)]+?)\s*\)", re.IGNORECASE)


def analyze_condition(condition: str):
    """Extract referenced jobs and flag boolean complexity in a condition string."""
    refs = []
    for func, job in CONDITION_FUNC_RE.findall(condition):
        refs.append({"function": func.lower(), "job": job.strip()})
    has_or = bool(re.search(r"\bor\b", condition, re.IGNORECASE))
    has_and = bool(re.search(r"\band\b", condition, re.IGNORECASE))
    if has_or:
        complexity = "or_present"  # REDESIGN candidate, see conditions-and-dependencies.md
    elif has_and and len(refs) > 1:
        complexity = "and_only"
    elif len(refs) <= 1:
        complexity = "single"
    else:
        complexity = "unknown"
    functions_used = sorted({r["function"] for r in refs})
    return {
        "referenced_jobs": refs,
        "complexity": complexity,
        "functions_used": functions_used,
    }


def build_job_record(block):
    attrs = {}
    for line in block["lines"]:
        kv = split_kv(line)
        if kv is None:
            continue
        key, value = kv
        attrs[key] = value

    job_type = attrs.get("job_type", "").strip().lower()
    known_type = job_type in KNOWN_JOB_TYPES

    known_attrs = {k: v for k, v in attrs.items() if k in KNOWN_ATTRIBUTES}
    raw_extra = {k: v for k, v in attrs.items() if k not in KNOWN_ATTRIBUTES}

    record = {
        "name": block["name"],
        "block_type": block["block_type"],
        "job_type": job_type or None,
        "job_type_verified": known_type,
        "box_name": attrs.get("box_name"),
        "command": attrs.get("command"),
        "machine": attrs.get("machine"),
        "owner": attrs.get("owner"),
        "condition": attrs.get("condition"),
        "condition_analysis": analyze_condition(attrs["condition"]) if attrs.get("condition") else None,
        "schedule": {
            "date_conditions": attrs.get("date_conditions"),
            "days_of_week": attrs.get("days_of_week"),
            "start_times": attrs.get("start_times"),
            "start_mins": attrs.get("start_mins"),
            "run_window": attrs.get("run_window"),
            "run_calendar": attrs.get("run_calendar"),
            "exclude_calendar": attrs.get("exclude_calendar"),
        },
        "alerting": {
            "alarm_if_fail": attrs.get("alarm_if_fail"),
            "alarm_if_terminate": attrs.get("alarm_if_terminate"),
            "term_run_time": attrs.get("term_run_time"),
            "notification_msg": attrs.get("notification_msg"),
            "notification_emails": attrs.get("notification_emails"),
        },
        "description": attrs.get("description"),
        "known_attributes": known_attrs,
        "raw_extra": raw_extra,
        "classification": "pending",
        "target": None,
        "status": "pending",
    }
    return record


def build_calendar_record(block):
    return {
        "name": block["name"],
        "block_type": block["block_type"],
        "raw_lines": block["lines"],
        "classification": "pending",
        "status": "pending",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jil_file", type=Path, help="Path to a JIL export")
    parser.add_argument("--out", type=Path, required=True, help="Output manifest JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the output JSON")
    args = parser.parse_args()

    if not args.jil_file.exists():
        print(f"error: {args.jil_file} not found", file=sys.stderr)
        sys.exit(1)

    raw_text = args.jil_file.read_text(errors="replace")
    blocks = parse_blocks(raw_text)

    jobs = []
    calendars = []
    warnings = []

    for block in blocks:
        if block["block_type"] in ("insert_job", "update_job"):
            record = build_job_record(block)
            if not record["job_type_verified"]:
                warnings.append(
                    f"job '{record['name']}': job_type '{record['job_type']}' is not in the "
                    "known-stable set (c/cmd/b/box/f/ft) -- verify against the customer's "
                    "AutoSys version before assuming its Airflow mapping"
                )
            if record["raw_extra"]:
                warnings.append(
                    f"job '{record['name']}': unrecognized attributes {sorted(record['raw_extra'])} "
                    "captured in raw_extra -- verify meaning before translating (common for FT jobs)"
                )
            jobs.append(record)
        elif block["block_type"] == "insert_calendar":
            calendars.append(build_calendar_record(block))
        elif block["block_type"] == "delete_job":
            warnings.append(f"delete_job block for '{block['name']}' found -- confirm this job is truly gone, not just marked for deletion in a stale export")

    # Reconstruct box membership: children declare box_name pointing at their parent.
    box_names = {j["name"] for j in jobs if (j["job_type"] or "") in ("b", "box")}
    boxes = {name: {"name": name, "children": []} for name in box_names}
    for job in jobs:
        parent = job.get("box_name")
        if parent:
            if parent not in boxes:
                warnings.append(
                    f"job '{job['name']}' declares box_name '{parent}' but no matching box job "
                    "was found in this export -- likely a partial/stale export"
                )
                boxes[parent] = {"name": parent, "children": [], "inferred": True}
            boxes[parent]["children"].append(job["name"])

    manifest = {
        "source_file": str(args.jil_file),
        "jobs": jobs,
        "boxes": list(boxes.values()),
        "calendars": calendars,
        "warnings": warnings,
        "summary": {
            "job_count": len(jobs),
            "box_count": len(boxes),
            "calendar_count": len(calendars),
            "warning_count": len(warnings),
        },
    }

    indent = 2 if args.pretty else None
    args.out.write_text(json.dumps(manifest, indent=indent))

    print(f"Wrote {args.out}: {len(jobs)} jobs, {len(boxes)} boxes, {len(calendars)} calendars, "
          f"{len(warnings)} warnings", file=sys.stderr)
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
