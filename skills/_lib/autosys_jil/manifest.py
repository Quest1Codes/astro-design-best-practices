"""Estate <-> JSON manifest: serialization, schema versioning, redaction, evidence, validation.

Deterministic: given identical inputs and registry version, output is byte-identical.
Reads files only; never contacts a live AutoSys, Astro, or network endpoint.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §1.11 (manifest.py spec)
  - skills/docs/REFACTOR-FILE-SPEC.md §0.3 (schema versioning: schema_version, generated_by,
    upgrade_v1 for today's jil_inventory.py v1.x output)
  - skills/docs/REFACTOR-PLAN.md §11.6 (redaction on by default; SHA-256 evidence hashing;
    assessment scripts read files only)
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from . import registry
from .commands import credential_patterns
from .conditions import try_parse
from .models import (
    IO,
    SLA,
    SCHEMA_VERSION,
    Alerting,
    Attr,
    Box,
    Calendar,
    Estate,
    Evidence,
    GenericObject,
    GlobalVar,
    Instance,
    Job,
    Load,
    Machine,
    Provenance,
    Resource,
    Schedule,
    Unknowns,
    Xinst,
)

SCHEMA_MAJOR = int(SCHEMA_VERSION.split(".")[0])


class ManifestVersionError(ValueError):
    """Raised when a manifest's schema_version major component is newer than this code supports."""


class ManifestError(ValueError):
    pass


# ============================================================================ redaction
# Credential-pattern regexes: on by default [plan §11.6]. The canonical pattern library lives
# in `commands_patterns.yaml` (owned by commands.py, spec §1.9) so there is exactly one place
# that defines what counts as a credential; this module reuses it to scrub free-text manifest
# fields (command, extras, io.*_file, description) so nothing written to disk carries a live
# secret. The *pattern name* is kept (for the report's compliance finding); the *value* never is.
def default_redact_patterns() -> dict[str, tuple[re.Pattern, int]]:
    return credential_patterns()


DEFAULT_REDACT_PATTERNS: dict[str, tuple[re.Pattern, int]] = credential_patterns()


def _redact_text(text: str | None, patterns: dict[str, tuple[re.Pattern, int]]) -> tuple[str | None, list[str]]:
    if not text:
        return text, []
    hits: list[str] = []
    out = text
    for name, (pat, group_idx) in patterns.items():
        def _sub(m: re.Match, name=name, group_idx=group_idx) -> str:
            hits.append(name)
            value = m.group(group_idx)
            return m.group(0).replace(value, f"«REDACTED:{name}»", 1)
        out = pat.sub(_sub, out)
    return out, hits


def redact(estate: Estate, patterns: dict[str, tuple[re.Pattern, int]] | None = None) -> dict[str, int]:
    """Redact credential-pattern matches in free-text manifest fields, in place.

    Returns a histogram of {pattern_name: hit_count} for the report's compliance finding.
    On by default; callers that need the raw values (never for anything persisted) must copy
    the Estate before calling this and are responsible for not writing that copy to disk.
    """
    pats = patterns if patterns is not None else DEFAULT_REDACT_PATTERNS
    hits: dict[str, int] = {}

    def _count(names: list[str]) -> None:
        for n in names:
            hits[n] = hits.get(n, 0) + 1

    for inst in estate.instances.values():
        for job in inst.jobs.values():
            job.command, h = _redact_text(job.command, pats)
            _count(h)
            job.description, h = _redact_text(job.description, pats)
            _count(h)
            job.io.std_in_file, h = _redact_text(job.io.std_in_file, pats)
            _count(h)
            job.io.std_out_file, h = _redact_text(job.io.std_out_file, pats)
            _count(h)
            job.io.std_err_file, h = _redact_text(job.io.std_err_file, pats)
            _count(h)
            job.io.profile, h = _redact_text(job.io.profile, pats)
            _count(h)
            for k in list(job.extras.keys()):
                job.extras[k], h = _redact_text(job.extras[k], pats)
                _count(h)
            for k, attr in job.attrs.items():
                if isinstance(attr.value, str):
                    attr.value, h = _redact_text(attr.value, pats)
                    _count(h)
                attr.raw, h = _redact_text(attr.raw, pats)
                _count(h)
        for ov in inst.overrides:
            for k, v in list(ov.get("attrs", {}).items()):
                if isinstance(v, str):
                    ov["attrs"][k], h = _redact_text(v, pats)
                    _count(h)
    return hits


# ============================================================================ evidence

def add_evidence(estate: Estate, path: Path | str, kind: str) -> Evidence:
    """Hash an ingested artifact and record it in estate.evidence[] [plan §11.6]."""
    p = Path(path)
    data = p.read_bytes()
    ev = Evidence(
        path=str(p),
        sha256=hashlib.sha256(data).hexdigest(),
        kind=kind,
        size=len(data),
        received_at=datetime.now(timezone.utc).isoformat(),
    )
    estate.evidence.append(ev)
    return ev


# ============================================================================ to_json / from_json

def _dc_to_dict(obj: Any) -> Any:
    """Generic recursive dataclass -> JSON-safe dict/list conversion.

    Handles the flat dataclasses in models.py (Schedule, SLA, Load, Alerting, IO, Machine,
    Resource, Xinst, GlobalVar, GenericObject, Evidence, Provenance, Box) and their nesting.
    date objects become ISO strings; tuples become lists (JSON has no tuple type).
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, date):
        return obj.isoformat()
    if is_dataclass(obj):
        return {f.name: _dc_to_dict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, dict):
        return {str(k): _dc_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dc_to_dict(v) for v in obj]
    return obj


def _attr_to_dict(a: Attr) -> dict:
    return {
        "name": a.name, "raw": a.raw, "value": _dc_to_dict(a.value), "known": a.known,
        "pdf_page": a.pdf_page, "family": a.family, "warnings": list(a.warnings),
    }


def _attr_from_dict(d: dict) -> Attr:
    return Attr(name=d["name"], raw=d["raw"], value=d.get("value"), known=d["known"],
                pdf_page=d.get("pdf_page"), family=d.get("family"), warnings=list(d.get("warnings", [])))


def _provenance_from_dict(d: dict | None) -> Provenance | None:
    if d is None:
        return None
    return Provenance(file=d["file"], line=d["line"], block_index=d["block_index"],
                       instance=d["instance"], subcommand=d["subcommand"])


def _job_to_dict(job: Job) -> dict:
    return {
        "name": job.name, "job_type": job.job_type, "job_type_known": job.job_type_known,
        "attrs": {k: _attr_to_dict(v) for k, v in job.attrs.items()},
        "provenance": job.provenance.as_dict(),
        "box_name": job.box_name, "command": job.command, "owner": job.owner,
        "application": job.application, "group": job.group, "description": job.description,
        "condition_raw": job.condition_raw,
        "condition_summary": job.condition.summary() if job.condition is not None else None,
        "condition_error": job.condition_error,
        "schedule": _dc_to_dict(job.schedule), "sla": _dc_to_dict(job.sla),
        "load": _dc_to_dict(job.load), "alerting": _dc_to_dict(job.alerting), "io": _dc_to_dict(job.io),
        "box_terminator": job.box_terminator, "job_terminator": job.job_terminator,
        "box_success": job.box_success, "box_failure": job.box_failure,
        "auto_hold": job.auto_hold, "auto_delete": job.auto_delete,
        "permission": list(job.permission), "extras": dict(job.extras),
        "modified_by": [p.as_dict() for p in job.modified_by],
        "deleted": job.deleted, "warnings": list(job.warnings),
    }


def _job_from_dict(d: dict) -> Job:
    cond_raw = d.get("condition_raw")
    cond_ast, cond_err = (None, d.get("condition_error"))
    if cond_raw:
        cond_ast, parse_err = try_parse(cond_raw)
        # Prefer the freshly re-derived error (deterministic re-parse); fall back to the
        # persisted one only if re-parsing could not run (should not happen for valid text).
        cond_err = parse_err if parse_err is not None else cond_err
    return Job(
        name=d["name"], job_type=d["job_type"], job_type_known=d["job_type_known"],
        attrs={k: _attr_from_dict(v) for k, v in d.get("attrs", {}).items()},
        provenance=_provenance_from_dict(d["provenance"]),
        box_name=d.get("box_name"), command=d.get("command"), owner=d.get("owner"),
        application=d.get("application"), group=d.get("group"), description=d.get("description"),
        condition_raw=cond_raw, condition=cond_ast, condition_error=cond_err,
        schedule=Schedule(**_schedule_kwargs(d.get("schedule", {}))),
        sla=SLA(**d.get("sla", {})) if d.get("sla") is not None else SLA(),
        load=Load(**d.get("load", {})) if d.get("load") is not None else Load(),
        alerting=Alerting(**d.get("alerting", {})) if d.get("alerting") is not None else Alerting(),
        io=IO(**d.get("io", {})) if d.get("io") is not None else IO(),
        box_terminator=d.get("box_terminator"), job_terminator=d.get("job_terminator"),
        box_success=d.get("box_success"), box_failure=d.get("box_failure"),
        auto_hold=d.get("auto_hold"), auto_delete=d.get("auto_delete"),
        permission=list(d.get("permission", [])), extras=dict(d.get("extras", {})),
        modified_by=[_provenance_from_dict(p) for p in d.get("modified_by", [])],
        deleted=d.get("deleted", False), warnings=list(d.get("warnings", [])),
    )


def _schedule_kwargs(d: dict) -> dict:
    out = dict(d)
    rw = out.get("run_window")
    if rw is not None:
        out["run_window"] = tuple(rw)
    return out


def _machine_from_dict(d: dict) -> Machine:
    return Machine(
        name=d["name"], type=d.get("type"), opsys=d.get("opsys"), node_name=d.get("node_name"),
        agent_name=d.get("agent_name"), max_load=d.get("max_load"), factor=d.get("factor"),
        members=list(d.get("members", [])), port=d.get("port"),
        encryption_type=d.get("encryption_type"), description=d.get("description"),
        extras=dict(d.get("extras", {})), provenance=_provenance_from_dict(d.get("provenance")),
    )


def _resource_from_dict(d: dict) -> Resource:
    return Resource(name=d["name"], res_type=d.get("res_type"), amount=d.get("amount"),
                     machine=d.get("machine"), description=d.get("description"),
                     provenance=_provenance_from_dict(d.get("provenance")))


def _xinst_from_dict(d: dict) -> Xinst:
    return Xinst(name=d["name"], xtype=d.get("xtype"), xmachine=d.get("xmachine"),
                 xport=d.get("xport"), xcrypt_type=d.get("xcrypt_type"), xmanager=d.get("xmanager"),
                 provenance=_provenance_from_dict(d.get("provenance")))


def _calendar_to_dict(c: Calendar) -> dict:
    return {"name": c.name, "dates": [d.isoformat() for d in c.dates], "source": c.source,
            "provenance": c.provenance.as_dict() if c.provenance else None}


def _calendar_from_dict(d: dict) -> Calendar:
    return Calendar(name=d["name"], dates=[date.fromisoformat(s) for s in d.get("dates", [])],
                    source=d.get("source", "unknown"), provenance=_provenance_from_dict(d.get("provenance")))


def _box_to_dict(b: Box) -> dict:
    return {"name": b.name, "children": list(b.children), "parent": b.parent, "depth": b.depth,
            "inferred": b.inferred}


def _box_from_dict(d: dict) -> Box:
    return Box(name=d["name"], children=list(d.get("children", [])), parent=d.get("parent"),
               depth=d.get("depth", 0), inferred=d.get("inferred", False))


def _unknowns_to_dict(u: Unknowns) -> dict:
    return {
        "job_types": {k: list(v) for k, v in u.job_types.items()},
        "attributes": {k: list(v) for k, v in u.attributes.items()},
        "object_kinds": {k: list(v) for k, v in u.object_kinds.items()},
        "condition_parse_failures": [dict(x) for x in u.condition_parse_failures],
        "unresolved_refs": [dict(x) for x in u.unresolved_refs],
    }


def _unknowns_from_dict(d: dict) -> Unknowns:
    return Unknowns(
        job_types={k: list(v) for k, v in d.get("job_types", {}).items()},
        attributes={k: list(v) for k, v in d.get("attributes", {}).items()},
        object_kinds={k: list(v) for k, v in d.get("object_kinds", {}).items()},
        condition_parse_failures=[dict(x) for x in d.get("condition_parse_failures", [])],
        unresolved_refs=[dict(x) for x in d.get("unresolved_refs", [])],
    )


def _instance_to_dict(inst: Instance) -> dict:
    return {
        "id": inst.id,
        "jobs": {k: _job_to_dict(v) for k, v in inst.jobs.items()},
        "boxes": {k: _box_to_dict(v) for k, v in inst.boxes.items()},
        "machines": {k: _dc_to_dict(v) for k, v in inst.machines.items()},
        "resources": {k: _dc_to_dict(v) for k, v in inst.resources.items()},
        "xinsts": {k: _dc_to_dict(v) for k, v in inst.xinsts.items()},
        "calendars": {k: _calendar_to_dict(v) for k, v in inst.calendars.items()},
        "globals": {k: _dc_to_dict(v) for k, v in inst.globals.items()},
        "objects": {k: _dc_to_dict(v) for k, v in inst.objects.items()},
        "overrides": [dict(o) for o in inst.overrides],
        "config": dict(inst.config),
        "agent_capabilities": {k: list(v) for k, v in inst.agent_capabilities.items()},
        "unknowns": _unknowns_to_dict(inst.unknowns),
        "warnings": list(inst.warnings),
    }


def _instance_from_dict(d: dict) -> Instance:
    return Instance(
        id=d["id"],
        jobs={k: _job_from_dict(v) for k, v in d.get("jobs", {}).items()},
        boxes={k: _box_from_dict(v) for k, v in d.get("boxes", {}).items()},
        machines={k: _machine_from_dict(v) for k, v in d.get("machines", {}).items()},
        resources={k: _resource_from_dict(v) for k, v in d.get("resources", {}).items()},
        xinsts={k: _xinst_from_dict(v) for k, v in d.get("xinsts", {}).items()},
        calendars={k: _calendar_from_dict(v) for k, v in d.get("calendars", {}).items()},
        globals={k: GlobalVar(**v) for k, v in d.get("globals", {}).items()},
        objects={k: GenericObject(kind=v["kind"], name=v["name"], attrs=dict(v.get("attrs", {})),
                                   provenance=_provenance_from_dict(v.get("provenance")))
                 for k, v in d.get("objects", {}).items()},
        overrides=[dict(o) for o in d.get("overrides", [])],
        config=dict(d.get("config", {})),
        agent_capabilities={k: list(v) for k, v in d.get("agent_capabilities", {}).items()},
        unknowns=_unknowns_from_dict(d.get("unknowns", {})),
        warnings=list(d.get("warnings", [])),
    )


def generated_by(tool: str, git_sha: str | None = None) -> dict[str, Any]:
    return {"tool": tool, "registry_version": registry.registry_version(), "git_sha": git_sha}


def to_dict(estate: Estate, *, tool: str = "manifest.to_json", git_sha: str | None = None) -> dict:
    """Estate -> a plain JSON-safe dict (top-level manifest layout)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": generated_by(tool, git_sha),
        "instances": {k: _instance_to_dict(v) for k, v in estate.instances.items()},
        "evidence": [_dc_to_dict(e) for e in estate.evidence],
        "nfr": estate.nfr,
        "stats": estate.stats,
        "graph": estate.graph,
        "schedules": estate.schedules,
        "commands": estate.commands,
        "command_summary": estate.command_summary,
        "history": estate.history,
        "scores": estate.scores,
        "architecture": estate.architecture,
        "waves": estate.waves,
        "brownfield": estate.brownfield,
        "notes": estate.notes,
        "status": estate.status,
    }


def to_json(estate: Estate, path: Path | str | None = None, *, tool: str = "manifest.to_json",
           git_sha: str | None = None) -> str:
    """Estate -> JSON text (sort_keys, indent=2, so diffs are stable [spec §0.2]).

    Writes to `path` when given; always returns the text.
    """
    text = json.dumps(to_dict(estate, tool=tool, git_sha=git_sha), sort_keys=True, indent=2) + "\n"
    if path is not None:
        Path(path).write_text(text)
    return text


def from_dict(d: dict) -> Estate:
    ver = str(d.get("schema_version", "1.0"))
    major = int(ver.split(".")[0])
    if major > SCHEMA_MAJOR:
        raise ManifestVersionError(
            f"manifest schema_version {ver} is newer than this code supports ({SCHEMA_VERSION})")
    if major < SCHEMA_MAJOR:
        d = upgrade_v1(d)
    return Estate(
        instances={k: _instance_from_dict(v) for k, v in d.get("instances", {}).items()},
        evidence=[Evidence(**e) for e in d.get("evidence", [])],
        nfr=d.get("nfr", {}),
        stats=d.get("stats", {}),
        graph=d.get("graph", {}),
        schedules=d.get("schedules", {}),
        commands=d.get("commands", {}),
        command_summary=d.get("command_summary", {}),
        history=d.get("history", {}),
        scores=d.get("scores", {}),
        architecture=d.get("architecture", {}),
        waves=d.get("waves", []),
        brownfield=d.get("brownfield", {}),
        notes=d.get("notes", {}),
        status=d.get("status", {}),
    )


def from_json(path: Path | str) -> Estate:
    return from_dict(json.loads(Path(path).read_text()))


# ============================================================================ v1 upgrade

def upgrade_v1(old: dict) -> dict:
    """Upgrade a 1.x manifest (today's `jil_inventory.py` output) to the 2.0 layout.

    v1 shape (from `migrating-autosys-to-astronomer/scripts/jil_inventory.py`): a flat
    `{"jobs": {...}, "boxes": {...}, "unknown_job_types": [...], "unknown_attributes": [...]}`
    with no instance scoping and no `schema_version` at all (treated as "1.0").
    Everything is folded into a single instance named "DEFAULT".
    """
    if "schema_version" in old and int(str(old["schema_version"]).split(".")[0]) >= SCHEMA_MAJOR:
        return old
    v1_jobs = old.get("jobs", {})
    jobs: dict[str, dict] = {}
    for name, jd in v1_jobs.items():
        prov = {"file": jd.get("file", "<v1>"), "line": jd.get("line", 0), "block_index": 0,
                "instance": "DEFAULT", "subcommand": "insert_job"}
        jt = jd.get("job_type", "CMD") or "CMD"
        cond_raw = jd.get("condition")
        jobs[name] = {
            "name": name, "job_type": jt, "job_type_known": jt in registry.job_types(),
            "attrs": {}, "provenance": prov, "box_name": jd.get("box_name"),
            "command": jd.get("command"), "owner": jd.get("owner"), "application": None,
            "group": None, "description": None, "condition_raw": cond_raw,
            "condition_summary": None, "condition_error": None,
            "schedule": {}, "sla": {}, "load": {}, "alerting": {}, "io": {},
            "box_terminator": None, "job_terminator": None, "box_success": None,
            "box_failure": None, "auto_hold": None, "auto_delete": None,
            "permission": [], "extras": {}, "modified_by": [], "deleted": False, "warnings": [],
        }
    unknown_types = old.get("unknown_job_types", [])
    unknown_attrs = old.get("unknown_attributes", [])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": {"tool": "manifest.upgrade_v1", "registry_version": registry.registry_version(),
                          "git_sha": None},
        "instances": {
            "DEFAULT": {
                "id": "DEFAULT", "jobs": jobs, "boxes": {}, "machines": {}, "resources": {},
                "xinsts": {}, "calendars": {}, "globals": {}, "objects": {}, "overrides": [],
                "config": {}, "agent_capabilities": {},
                "unknowns": {
                    "job_types": {t: [] for t in unknown_types},
                    "attributes": {a: [] for a in unknown_attrs},
                    "object_kinds": {}, "condition_parse_failures": [], "unresolved_refs": [],
                },
                "warnings": ["upgraded from schema v1 by manifest.upgrade_v1"],
            }
        },
        "evidence": [], "nfr": {}, "stats": {}, "graph": {}, "schedules": {}, "commands": {},
        "command_summary": {}, "history": {}, "scores": {}, "architecture": {}, "waves": [],
        "brownfield": {}, "notes": {}, "status": {},
    }


# ============================================================================ validation

def validate(estate: Estate) -> list[str]:
    """Schema + referential-integrity checks. Returns a list of problem strings (empty = clean).

    Cross-checks every box_name/condition-job-ref/machine/run_calendar/resources name resolves
    within its instance, or is already listed in unknowns.unresolved_refs (which `finalize()`
    in parser.py populates) [spec §1.11].
    """
    problems: list[str] = []
    for inst_id, inst in estate.instances.items():
        job_names = set(inst.jobs)
        box_names = set(inst.boxes)
        machine_names = set(inst.machines)
        calendar_names = set(inst.calendars)
        resource_names = set(inst.resources)
        already_flagged = {(r["kind"], r["from"], r["to"]) for r in inst.unknowns.unresolved_refs}

        for job in inst.jobs.values():
            if job.box_name and job.box_name not in box_names and job.box_name not in job_names:
                key = ("box_name", job.name, job.box_name)
                if key not in already_flagged:
                    problems.append(f"[{inst_id}] job {job.name!r}: box_name {job.box_name!r} does not resolve")
            if job.condition is not None:
                for ref in job.condition.referenced_job_names:
                    if ref not in job_names and ("condition", job.name, ref) not in already_flagged:
                        problems.append(f"[{inst_id}] job {job.name!r}: condition references unknown job {ref!r}")
            for m in job.load.machine:
                if machine_names and m not in machine_names and ("machine", job.name, m) not in already_flagged:
                    problems.append(f"[{inst_id}] job {job.name!r}: machine {m!r} does not resolve")
            for cal in (job.schedule.run_calendar, job.schedule.exclude_calendar):
                if cal and cal not in calendar_names and ("calendar", job.name, cal) not in already_flagged:
                    problems.append(f"[{inst_id}] job {job.name!r}: calendar {cal!r} does not resolve")
            for res in job.load.resources:
                rn = res.get("name") if isinstance(res, dict) else None
                if rn and resource_names and rn not in resource_names \
                        and ("resource", job.name, rn) not in already_flagged:
                    problems.append(f"[{inst_id}] job {job.name!r}: resource {rn!r} does not resolve")
        for box in inst.boxes.values():
            if box.parent and box.parent not in box_names:
                problems.append(f"[{inst_id}] box {box.name!r}: parent {box.parent!r} does not resolve")
    return problems
