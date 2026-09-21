#!/usr/bin/env python3
"""Generate the machine-readable AutoSys 12.0 registries from the extracted PDF corpus.

Deterministic: same corpus + same overlays -> byte-identical JSON.
Reads files only; never contacts the network.

Sources:
  - research/autosys-12.0/jil-job-definitions.txt   (job_type attribute page, every "<name> Attribute --" block)
  - research/autosys-12.0/jil-other-objects.txt      (machine/resource/xinst/... attributes)
  - research/autosys-12.0/system-states.txt          (job states)
  - research/autosys-12.0/commands.txt               (sendevent -E event names)
  - registry/job_type_families.yaml, registry/attribute_families.yaml (hand overlays)

Outputs (in this directory):
  job_types.json, attributes.json, states.json, events.json

Usage:
    python3 -m autosys_jil.registry.build_registry --corpus research/autosys-12.0 [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LINE_RE = re.compile(r"^\[p\.(\d+)\] (.*)$")
ATTR_HEADING_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s+Attribute\s*-{1,2}\s*(.*)$")
ATTR_HEADING_ALT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?:Attribute)?\s*--\s*(.*)$")
JOBTYPE_BULLET_RE = re.compile(r"^•\s+([A-Z0-9]+)\s+(?:--|–)\s+(.+)$")
JOBTYPE_PAREN_RE = re.compile(r"\(([A-Z][A-Z0-9]{1,11})\)")
EVENT_RE = re.compile(r"\b(?:sendevent\s+-E\s+|-E\s+)([A-Z][A-Z_]{3,})\b")
STATE_WORDS = [
    "INACTIVE", "ACTIVATED", "STARTING", "RUNNING", "SUCCESS", "FAILURE", "TERMINATED", "RESTART",
    "QUE_WAIT", "WAIT_REPLY", "ON_HOLD", "ON_ICE", "ON_NOEXEC", "PEND_MACH", "SUSPENDED", "RESWAIT",
    "REFRESH_DEPENDENCIES", "REFRESH_FILEWATCHER",
]

# Hand-maintained state semantics (the doc's state pages are prose; this is the checked digest).
STATE_TABLE = {
    "INACTIVE": ("Job has never run or was reset; not eligible until conditions/schedule met", False, "none"),
    "ACTIVATED": ("Box started; job waiting for its own starting conditions", False, "scheduled"),
    "STARTING": ("Event processor initiated start; agent not yet reported RUNNING", False, "queued"),
    "RUNNING": ("Process is executing on the agent", False, "running"),
    "SUCCESS": ("Exit code within success range (0 or <= max_exit_success / in success_codes)", True, "success"),
    "FAILURE": ("Exit code outside success range", True, "failed"),
    "TERMINATED": ("Killed (KILLJOB), box terminated it, or agent lost", True, "failed"),
    "RESTART": ("Application-level failure; scheduler will retry (n_retrys)", False, "up_for_retry"),
    "QUE_WAIT": ("Eligible to start but waiting for machine load / priority", False, "queued"),
    "WAIT_REPLY": ("Waiting for a manual REPLY_RESPONSE", False, "none (HITL redesign)"),
    "ON_HOLD": ("Held by operator; will NOT start; dependents wait", False, "paused (dependents blocked)"),
    "ON_ICE": ("Iced by operator; removed from flow; dependents treat as SUCCESS", False, "paused (dependents proceed)"),
    "ON_NOEXEC": ("Runs through the flow without executing; marked SUCCESS", False, "skipped-as-success"),
    "PEND_MACH": ("Machine offline/unreachable; waiting", False, "queued (no worker)"),
    "SUSPENDED": ("Suspended via SUSPENDJOB", False, "none"),
    "RESWAIT": ("Waiting for a virtual resource", False, "queued (pool slot)"),
    "REFRESH_DEPENDENCIES": ("Transient: re-evaluating dependencies", False, "n/a"),
    "REFRESH_FILEWATCHER": ("Transient: file watcher refresh", False, "n/a"),
}


def read_corpus(path: Path) -> list[tuple[int, str]]:
    out = []
    for raw in path.read_text(errors="replace").splitlines():
        m = LINE_RE.match(raw)
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


# --------------------------------------------------------------------------- job types

def build_job_types(lines: list[tuple[int, str]], overlay: dict) -> dict:
    """Find the job_type attribute block and harvest its bullet list."""
    start = None
    for i, (_, text) in enumerate(lines):
        if text.strip().startswith("job_type Attribute"):
            start = i
            break
    if start is None:
        raise SystemExit("job_type attribute heading not found in corpus")

    found: dict[str, tuple[str, int]] = {}
    for page, text in lines[start:start + 400]:
        m = JOBTYPE_BULLET_RE.match(text.strip())
        if m:
            found[m.group(1)] = (m.group(2).strip(), page)
        if text.strip().startswith("Default: CMD"):
            break

    families = overlay["families"]
    code_to_family = {}
    for fam, spec in families.items():
        for code in spec["types"]:
            code_to_family[code] = (fam, spec["translation_ref"])

    result: dict[str, dict] = {}
    all_codes = set(found) | set(code_to_family)
    for code in sorted(all_codes):
        name, page = found.get(code, (overlay["names"].get(code, code), None))
        fam, ref = code_to_family.get(code, ("unclassified", None))
        result[code] = {
            "name": overlay["names"].get(code, name),
            "family": fam,
            "translation_ref": ref,
            "aliases": sorted(a for a, c in overlay["aliases"].items() if c == code),
            "pdf_page": page,
            "in_12_0_doc": page is not None,
        }
    for code, spec in overlay.get("not_in_12_0", {}).items():
        result[code] = {
            "name": spec["name"], "family": spec["family"], "translation_ref": spec["translation_ref"],
            "aliases": [], "pdf_page": None, "in_12_0_doc": False, "note": spec.get("note"),
        }
    return result


# --------------------------------------------------------------------------- attributes

def infer_value_type(syntax: str, default: str | None, limits: str | None) -> str:
    s = (syntax or "").lower()
    if re.search(r"\b(y\s*\|\s*n|1\s*\|\s*0|yes\s*\|\s*no)\b", s):
        return "bool"
    if "hh:mm" in s:
        return "hhmm_list" if "," in s or "..." in s else "hhmm"
    if limits and re.match(r"^\s*-?\d+\s*-\s*\d+", limits):
        return "int"
    if default and re.fullmatch(r"-?\d+", default.strip()):
        return "int"
    if "|" in s and s.count("|") >= 1 and len(s) < 120:
        return "enum"
    return "str"


def family_for(name: str, fam_overlay: dict) -> str:
    for fam, names in fam_overlay["explicit"].items():
        if name in names:
            return fam
    for prefix, fam in fam_overlay["prefixes"].items():
        if name.startswith(prefix):
            return fam
    return "misc"


def build_attributes(lines: list[tuple[int, str]], fam_overlay: dict, object_kind: str = "job") -> dict:
    # locate headings
    heads: list[tuple[int, int, str, str]] = []  # (line_idx, page, name, title)
    for i, (page, text) in enumerate(lines):
        t = text.strip()
        m = ATTR_HEADING_RE.match(t)
        if not m:
            continue
        name = m.group(1)
        # skip obvious prose false-positives: heading must start at column 0 in the source
        if text.startswith(" "):
            continue
        heads.append((i, page, name, m.group(2).strip()))

    result: dict[str, dict] = {}
    for n, (idx, page, name, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        block = [t for _, t in lines[idx + 1:end]]
        joined = "\n".join(block)

        # supported job types
        supported: list[str] | str = []
        requirement = "optional"
        sj = re.search(r"Supported Job Types?\n(.*?)(?:\nSyntax\n|\Z)", joined, re.S)
        seg = sj.group(1) if sj else "\n".join(block[:25])
        if re.search(r"\ball job types\b", seg, re.I):
            supported = "ALL"
        else:
            supported = sorted(set(JOBTYPE_PAREN_RE.findall(seg)))
        if re.search(r"\brequired\b", seg, re.I):
            requirement = "required"
        syntax_end = joined.find("\nExample")
        param_block = joined if syntax_end < 0 else joined[:syntax_end]
        # syntax
        syntax = None
        sx = re.search(r"This attribute has the following format:\n\s*(.+)", joined)
        if sx:
            syntax = sx.group(1).strip()
        default = None
        dm = re.search(r"^\s*Default:\s*(.+)$", param_block, re.M)
        if dm:
            default = dm.group(1).strip()
        limits = None
        lm = re.search(r"^\s*Limits:\s*(.+)$", param_block, re.M)
        if lm:
            limits = lm.group(1).strip()

        vt = fam_overlay["value_types"].get(name) or infer_value_type(syntax or "", default, limits)
        entry = {
            "title": title,
            "object": object_kind,
            "supported_job_types": supported,
            "requirement": requirement,
            "syntax": syntax,
            "value_type": vt,
            "default": default,
            "limits": limits,
            "pdf_page": page,
            "family": family_for(name, fam_overlay),
        }
        if name in result:
            # same attribute documented twice (different job types): merge job types, keep first page
            prev = result[name]
            if isinstance(prev["supported_job_types"], list) and isinstance(supported, list):
                prev["supported_job_types"] = sorted(set(prev["supported_job_types"]) | set(supported))
            prev.setdefault("also_pdf_pages", []).append(page)
        else:
            result[name] = entry
    return result


# --------------------------------------------------------------------------- states / events

def build_states(lines: list[tuple[int, str]]) -> dict:
    pages: dict[str, int] = {}
    for page, text in lines:
        for w in STATE_WORDS:
            if re.search(rf"\b{w}\b", text) and w not in pages:
                pages[w] = page
    out = {}
    for state in STATE_WORDS:
        desc, terminal, af = STATE_TABLE[state]
        out[state] = {"description": desc, "terminal": terminal, "airflow_equivalent": af,
                      "pdf_page": pages.get(state)}
    return out


def build_events(lines: list[tuple[int, str]]) -> dict:
    # The sendevent reference lists events as bullets and in "-E event" examples; union both
    # with the canonical list so a layout quirk cannot drop a real event.
    canonical = ["STARTJOB", "FORCE_STARTJOB", "KILLJOB", "RESTARTJOB", "RESUMEJOB", "SUSPENDJOB",
                 "SEND_SIGNAL", "DELETEJOB", "CHK_BOX_TERM", "JOB_ON_HOLD", "JOB_OFF_HOLD", "JOB_ON_ICE",
                 "JOB_OFF_ICE", "JOB_ON_NOEXEC", "JOB_OFF_NOEXEC", "CHANGE_STATUS", "CHANGE_PRIORITY",
                 "REPLY_RESPONSE", "RESEND_EXTERNAL_STATUS", "REFRESH_EXTINST", "SET_GLOBAL", "MACH_OFFLINE",
                 "MACH_ONLINE", "MACH_UNQUAL_OFFLINE", "RELEASE_RESOURCE", "COMMENT", "ALARM", "STOP_DEMON",
                 "AGGREGATE", "REFRESH_BROKER", "REFRESH_AUTH_HOST"]
    events: dict[str, int | None] = {ev: None for ev in canonical}
    for page, text in lines:
        for ev in EVENT_RE.findall(text):
            if ev == "EVENT":
                continue
            if events.get(ev) is None:
                events[ev] = page
        for ev in canonical:
            if events[ev] is None and re.search(rf"\b{ev}\b", text):
                events[ev] = page
    control = {"STARTJOB", "FORCE_STARTJOB", "KILLJOB", "RESTARTJOB", "RESUMEJOB", "SUSPENDJOB",
               "SEND_SIGNAL", "DELETEJOB", "CHK_BOX_TERM"}
    hold = {"JOB_ON_HOLD", "JOB_OFF_HOLD", "JOB_ON_ICE", "JOB_OFF_ICE", "JOB_ON_NOEXEC", "JOB_OFF_NOEXEC"}
    state = {"CHANGE_STATUS", "CHANGE_PRIORITY", "REPLY_RESPONSE", "RESEND_EXTERNAL_STATUS",
             "REFRESH_EXTINST"}
    glob = {"SET_GLOBAL"}
    machine = {"MACH_OFFLINE", "MACH_ONLINE", "MACH_UNQUAL_OFFLINE", "RELEASE_RESOURCE"}
    misc = {"COMMENT", "ALARM", "STOP_DEMON", "AGGREGATE", "REFRESH_BROKER", "REFRESH_AUTH_HOST"}
    out = {}
    for ev in sorted(events):
        cat = ("control" if ev in control else "hold-ice" if ev in hold else "state" if ev in state
               else "global" if ev in glob else "machine-resource" if ev in machine
               else "admin" if ev in misc else "other")
        out[ev] = {"category": cat, "pdf_page": events[ev],
                   "hidden_control_flow": ev in control | hold | state | glob}
    return out


# --------------------------------------------------------------------------- main

def dump(path: Path, data: dict) -> str:
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--check", action="store_true", help="exit 1 if committed JSON differs from regenerated")
    args = ap.parse_args(argv)

    jt_overlay = yaml.safe_load((HERE / "job_type_families.yaml").read_text())
    fam_overlay = yaml.safe_load((HERE / "attribute_families.yaml").read_text())

    job_lines = read_corpus(args.corpus / "jil-job-definitions.txt")
    other_lines = read_corpus(args.corpus / "jil-other-objects.txt")
    state_lines = read_corpus(args.corpus / "system-states.txt")
    cmd_lines = read_corpus(args.corpus / "commands.txt")

    outputs = {
        "job_types.json": build_job_types(job_lines, jt_overlay),
        "attributes.json": build_attributes(job_lines, fam_overlay, "job"),
        "object_attributes.json": build_attributes(other_lines, fam_overlay, "other"),
        "states.json": build_states(state_lines),
        "events.json": build_events(cmd_lines),
    }
    rc = 0
    for fname, data in outputs.items():
        text = dump(HERE / fname, data)
        target = HERE / fname
        if args.check:
            if not target.exists() or target.read_text() != text:
                print(f"STALE: {fname}", file=sys.stderr)
                rc = 1
        else:
            target.write_text(text)
        print(f"{fname}: {len(data)} entries")
    return rc


if __name__ == "__main__":
    sys.exit(main())
