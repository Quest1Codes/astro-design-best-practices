"""JIL blocks -> typed Instance model (jobs, boxes, machines, resources, xinsts, ...).

Deterministic; reads files only.

Semantics encoded [AS p.2400 JIL; p.2549 job_type; p.2552 default CMD; p.2874 machine type]:
  - Blocks are applied in file order; a later `update_job` merges into an earlier `insert_job`
    and is recorded in `modified_by`. `override_job` is a one-shot, next-run-only override and is
    kept separately in `instance.overrides` (never merged). `delete_*` marks `deleted=True`.
  - Missing job_type -> CMD. Aliases c/b/f -> CMD/BOX/FW.
  - Unknown job types / attributes / object kinds are captured, never dropped.
  - Attribute values are normalised per registry value_type (see `_normalize`).
"""
from __future__ import annotations

import re
from pathlib import Path

from . import registry
from .conditions import try_parse
from .lexer import Block, tokenize
from .models import (
    IO, SLA, Alerting, Attr, Box, Calendar, GenericObject, GlobalVar, Instance, Job, Load, Machine,
    Provenance, Resource, Schedule, Unknowns, Xinst,
)
from .boxes import build_tree

_BOOL_TRUE = {"1", "y", "yes", "true"}
_BOOL_FALSE = {"0", "n", "no", "false"}
_HHMM_RE = re.compile(r"^\d{1,2}:\d{2}$")


def _to_bool(raw: str) -> bool | None:
    r = raw.strip().lower().strip('"')
    if r in _BOOL_TRUE:
        return True
    if r in _BOOL_FALSE:
        return False
    return None


def _to_int(raw: str) -> int | None:
    m = re.match(r"^\s*(-?\d+)", raw)
    return int(m.group(1)) if m else None


def _csv(raw: str) -> list[str]:
    return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]


def _normalize(name: str, raw: str, vt: str) -> tuple[object, list[str]]:
    warnings: list[str] = []
    r = raw.strip()
    if vt == "bool":
        b = _to_bool(r)
        if b is None:
            warnings.append(f"{name}: expected Y/N/1/0, got {raw!r}")
        return b, warnings
    if vt == "int":
        v = _to_int(r)
        if v is None:
            warnings.append(f"{name}: expected integer, got {raw!r}")
        return v, warnings
    if vt == "int_list":
        vals = []
        for p in _csv(r):
            v = _to_int(p)
            if v is None:
                warnings.append(f"{name}: non-integer item {p!r}")
            else:
                vals.append(v)
        return vals, warnings
    if vt in ("hhmm_list", "hhmm"):
        vals = _csv(r.strip('"'))
        for v in vals:
            if not _HHMM_RE.match(v):
                warnings.append(f"{name}: bad HH:MM {v!r}")
        return (vals if vt == "hhmm_list" else (vals[0] if vals else None)), warnings
    if vt == "list":
        return [p.lower() for p in _csv(r.strip('"'))], warnings
    if vt == "csv_list":
        return _csv(r), warnings
    if vt == "time_range":
        parts = [p.strip() for p in r.strip('"').split("-")]
        if len(parts) == 2:
            return (parts[0], parts[1]), warnings
        warnings.append(f"{name}: expected HH:MM-HH:MM, got {raw!r}")
        return None, warnings
    if vt == "machine_list":
        return _csv(r), warnings
    if vt == "permission":
        return [p.strip() for p in r.split(",") if p.strip()], warnings
    if vt == "owner":
        return r, warnings
    if vt == "resources":
        # resources: (name, QUANTITY=n, FREE=Y|N) [, (...)]  [AS p.2680]
        items = []
        for grp in re.findall(r"\(([^)]*)\)", r):
            fields = [f.strip() for f in grp.split(",")]
            item = {"name": fields[0] if fields else None}
            for f in fields[1:]:
                if "=" in f:
                    k, v = f.split("=", 1)
                    item[k.strip().lower()] = v.strip()
            items.append(item)
        if not items and r:
            items.append({"name": r})
        return items, warnings
    return r, warnings


class _AttrIndex:
    def __init__(self):
        self.job_attrs = registry.attributes()
        self.obj_attrs = registry.object_attributes()

    def lookup(self, name: str, for_object: str = "job") -> dict | None:
        if for_object == "job":
            return self.job_attrs.get(name) or self.obj_attrs.get(name)
        return self.obj_attrs.get(name) or self.job_attrs.get(name)


def _attrs_from_block(block: Block, idx: _AttrIndex, unknowns: Unknowns, owner_name: str,
                      for_object: str = "job") -> tuple[dict[str, Attr], dict[str, str], list[str]]:
    attrs: dict[str, Attr] = {}
    extras: dict[str, str] = {}
    warnings: list[str] = []
    for ra in block.attrs:
        if ra.key.startswith("_"):
            continue
        spec = idx.lookup(ra.key, for_object)
        if spec is None:
            extras[ra.key] = ra.raw
            unknowns.attributes.setdefault(ra.key, []).append(owner_name)
            continue
        value, w = _normalize(ra.key, ra.raw, spec.get("value_type", "str"))
        warnings.extend(w)
        if ra.key == "envvar" and ra.key in attrs:  # repeatable
            prev = attrs[ra.key]
            prev.value = (prev.value if isinstance(prev.value, list) else [prev.value]) + [value]
            continue
        attrs[ra.key] = Attr(ra.key, ra.raw, value, True, spec.get("pdf_page"), spec.get("family"), w)
    return attrs, extras, warnings


def _get(attrs: dict[str, Attr], name: str, default=None):
    a = attrs.get(name)
    return a.value if a is not None and a.value is not None else default


def _build_job(block: Block, prov: Provenance, idx: _AttrIndex, unknowns: Unknowns) -> Job:
    attrs, extras, warnings = _attrs_from_block(block, idx, unknowns, block.name)
    jt_raw = attrs["job_type"].raw if "job_type" in attrs else None
    job_type, known = registry.resolve_job_type(jt_raw)
    if not known:
        unknowns.job_types.setdefault(job_type, []).append(block.name)

    # attribute-on-unsupported-job-type check
    for a in attrs.values():
        spec = idx.lookup(a.name)
        sup = spec.get("supported_job_types") if spec else None
        if isinstance(sup, list) and sup and job_type not in sup and a.name != "job_type":
            warnings.append(f"{a.name} is documented for {sup}, not {job_type} [AS p.{spec.get('pdf_page')}]")

    cond_raw = _get(attrs, "condition")
    cond_ast, cond_err = (None, None)
    if cond_raw:
        cond_ast, cond_err = try_parse(cond_raw)
        if cond_err:
            unknowns.condition_parse_failures.append({"job": block.name, "condition": cond_raw, "error": cond_err})

    sched = Schedule(
        date_conditions=bool(_get(attrs, "date_conditions", False)),
        days_of_week=_get(attrs, "days_of_week", []),
        start_times=_get(attrs, "start_times", []),
        start_mins=_get(attrs, "start_mins", []),
        run_window=_get(attrs, "run_window"),
        run_calendar=_get(attrs, "run_calendar"),
        exclude_calendar=_get(attrs, "exclude_calendar"),
        timezone=_get(attrs, "timezone"),
        must_start_times=_get(attrs, "must_start_times", []),
        must_complete_times=_get(attrs, "must_complete_times", []),
    )
    sla = SLA(
        term_run_time=_get(attrs, "term_run_time"),
        max_run_alarm=_get(attrs, "max_run_alarm"),
        min_run_alarm=_get(attrs, "min_run_alarm"),
        n_retrys=_get(attrs, "n_retrys"),
        max_exit_success=_get(attrs, "max_exit_success"),
        success_codes=_get(attrs, "success_codes", []),
    )
    machine = _get(attrs, "machine", [])
    load = Load(job_load=_get(attrs, "job_load"), priority=_get(attrs, "priority"),
                resources=_get(attrs, "resources", []), machine=machine if isinstance(machine, list) else [machine])
    alerting = Alerting(
        alarm_if_fail=_get(attrs, "alarm_if_fail"),
        alarm_if_terminated=_get(attrs, "alarm_if_terminated"),
        alarm_if_success=_get(attrs, "alarm_if_success"),
        send_notification=_get(attrs, "send_notification"),
        notification_emails=_get(attrs, "notification_emails", []),
        notification_msg=_get(attrs, "notification_msg"),
        svcdesk={k[len("svcdesk_"):]: a.raw for k, a in attrs.items() if k.startswith("svcdesk_")},
    )
    env = _get(attrs, "envvar", [])
    io = IO(std_in_file=_get(attrs, "std_in_file"), std_out_file=_get(attrs, "std_out_file"),
            std_err_file=_get(attrs, "std_err_file"), profile=_get(attrs, "profile"),
            envvar=env if isinstance(env, list) else [env])
    perm = _get(attrs, "permission", [])
    return Job(
        name=block.name, job_type=job_type, job_type_known=known, attrs=attrs, provenance=prov,
        box_name=_get(attrs, "box_name"), command=_get(attrs, "command"), owner=_get(attrs, "owner"),
        application=_get(attrs, "application"), group=_get(attrs, "group"),
        description=_get(attrs, "description"), condition_raw=cond_raw, condition=cond_ast,
        condition_error=cond_err, schedule=sched, sla=sla, load=load, alerting=alerting, io=io,
        box_terminator=_get(attrs, "box_terminator"), job_terminator=_get(attrs, "job_terminator"),
        box_success=_get(attrs, "box_success"), box_failure=_get(attrs, "box_failure"),
        auto_hold=_get(attrs, "auto_hold"), auto_delete=_get(attrs, "auto_delete"),
        permission=perm if isinstance(perm, list) else [perm], extras=extras, warnings=warnings,
    )


def _merge_update(target: Job, upd: Job, prov: Provenance) -> None:
    """Apply update_job semantics: only attributes present in the update change."""
    for k, a in upd.attrs.items():
        target.attrs[k] = a
    target.extras.update(upd.extras)
    target.modified_by.append(prov)
    # rebuild derived views from merged attrs by re-running the builder on a synthetic block
    # (cheap and keeps one code path): done by caller via rebuild().


def _rebuild_from_attrs(job: Job, idx: _AttrIndex, unknowns: Unknowns) -> Job:
    block = Block(kind="insert_job", name=job.name, header_line=job.provenance.line)
    from .lexer import RawAttr
    for a in job.attrs.values():
        block.attrs.append(RawAttr(a.name, a.raw, job.provenance.line))
    for k, v in job.extras.items():
        block.attrs.append(RawAttr(k, v, job.provenance.line))
    rebuilt = _build_job(block, job.provenance, idx, Unknowns())  # don't double-count unknowns
    rebuilt.modified_by = job.modified_by
    rebuilt.deleted = job.deleted
    return rebuilt


def _build_machine(block: Block, prov: Provenance, idx: _AttrIndex, unknowns: Unknowns) -> Machine:
    attrs, extras, _ = _attrs_from_block(block, idx, unknowns, block.name, "other")
    raw = {k: a.raw for k, a in attrs.items()}
    members = [a.raw for a in block.attrs if a.key == "machine"]
    return Machine(
        name=block.name, type=raw.get("type"), opsys=raw.get("opsys"), node_name=raw.get("node_name"),
        agent_name=raw.get("agent_name"), max_load=_to_int(raw["max_load"]) if "max_load" in raw else None,
        factor=float(raw["factor"]) if "factor" in raw and re.match(r"^[\d.]+$", raw["factor"]) else None,
        members=members, port=_to_int(raw["port"]) if "port" in raw else None,
        encryption_type=raw.get("encryption_type"), description=raw.get("description"),
        extras=extras, provenance=prov,
    )


def _build_resource(block: Block, prov: Provenance) -> Resource:
    raw = {a.key: a.raw for a in block.attrs}
    return Resource(name=block.name, res_type=raw.get("res_type"),
                    amount=_to_int(raw["amount"]) if "amount" in raw else None,
                    machine=raw.get("machine"), description=raw.get("description"), provenance=prov)


def _build_xinst(block: Block, prov: Provenance) -> Xinst:
    raw = {a.key: a.raw for a in block.attrs}
    return Xinst(name=block.name, xtype=raw.get("xtype"), xmachine=raw.get("xmachine"),
                 xport=_to_int(raw["xport"]) if "xport" in raw else None,
                 xcrypt_type=raw.get("xcrypt_type"), xmanager=raw.get("xmanager"), provenance=prov)


def _build_calendar(block: Block, prov: Provenance) -> Calendar:
    from .calendars import parse_date_tokens
    tokens: list[str] = []
    for a in block.attrs:
        tokens.extend(_csv(a.raw) if a.key in ("dates", "date") else [f"{a.key}: {a.raw}"])
    dates = parse_date_tokens(tokens)
    return Calendar(name=block.name, dates=dates, source="insert_calendar", provenance=prov)


# ------------------------------------------------------------------------------ public API

def parse_text(text: str, *, file: str = "<memory>", instance: str = "DEFAULT",
               into: Instance | None = None) -> Instance:
    inst = into or Instance(id=instance)
    idx = _AttrIndex()
    for block in tokenize(text):
        prov = Provenance(file, block.header_line, block.index, instance, block.kind)
        kind = block.kind
        if kind in ("insert_job", "update_job"):
            job = _build_job(block, prov, idx, inst.unknowns)
            if kind == "insert_job" or block.name not in inst.jobs:
                if kind == "update_job":
                    job.warnings.append("update_job for a job not previously inserted in this export")
                inst.jobs[block.name] = job
            else:
                existing = inst.jobs[block.name]
                _merge_update(existing, job, prov)
                inst.jobs[block.name] = _rebuild_from_attrs(existing, idx, inst.unknowns)
        elif kind == "override_job":
            inst.overrides.append({"job": block.name, "attrs": {a.key: a.raw for a in block.attrs},
                                   "provenance": prov.as_dict()})
        elif kind == "delete_job":
            if block.name in inst.jobs:
                inst.jobs[block.name].deleted = True
                inst.jobs[block.name].modified_by.append(prov)
            else:
                inst.warnings.append(f"delete_job for unknown job {block.name!r} ({file}:{block.header_line})")
        elif kind in ("insert_machine", "update_machine"):
            m = _build_machine(block, prov, idx, inst.unknowns)
            if kind == "update_machine" and block.name in inst.machines:
                old = inst.machines[block.name]
                for f in ("type", "opsys", "node_name", "agent_name", "max_load", "factor", "port",
                          "encryption_type", "description"):
                    if getattr(m, f) is None:
                        setattr(m, f, getattr(old, f))
                m.members = m.members or old.members
            inst.machines[block.name] = m
        elif kind == "delete_machine":
            inst.machines.pop(block.name, None)
        elif kind in ("insert_resource", "update_resource"):
            inst.resources[block.name] = _build_resource(block, prov)
        elif kind == "delete_resource":
            inst.resources.pop(block.name, None)
        elif kind in ("insert_xinst", "update_xinst"):
            inst.xinsts[block.name] = _build_xinst(block, prov)
        elif kind == "delete_xinst":
            inst.xinsts.pop(block.name, None)
        elif kind == "insert_calendar":
            inst.calendars[block.name] = _build_calendar(block, prov)
        elif kind.startswith(("insert_", "update_")) and kind != "unknown":
            objkind = kind.split("_", 1)[1]
            inst.objects[f"{objkind}:{block.name}"] = GenericObject(
                objkind, block.name, {a.key: a.raw for a in block.attrs}, prov)
        elif kind.startswith("delete_"):
            inst.objects.pop(f"{kind.split('_', 1)[1]}:{block.name}", None)
        else:  # unknown
            sub = next((a.raw for a in block.attrs if a.key == "_subcommand"), "unknown")
            inst.unknowns.object_kinds.setdefault(sub, []).append(block.name)
            inst.objects[f"unknown:{block.name}"] = GenericObject(
                "unknown", block.name, {a.key: a.raw for a in block.attrs}, prov)
    return inst


def parse_files(paths: list[Path], instance: str = "DEFAULT", into: Instance | None = None) -> Instance:
    inst = into or Instance(id=instance)
    for p in paths:
        parse_text(p.read_text(errors="replace"), file=str(p), instance=instance, into=inst)
    finalize(inst)
    return inst


def finalize(inst: Instance) -> None:
    """Build boxes and resolve references. Idempotent."""
    inst.boxes = build_tree(inst.jobs)
    for box in inst.boxes.values():
        if box.inferred:
            inst.unknowns.unresolved_refs.append(
                {"kind": "box_name", "from": ",".join(box.children), "to": box.name})
    machine_names = set(inst.machines)
    for job in inst.jobs.values():
        if job.condition is not None:
            for ref in job.condition.referenced_job_names:
                if ref not in inst.jobs:
                    inst.unknowns.unresolved_refs.append({"kind": "condition", "from": job.name, "to": ref})
        for m in job.load.machine:
            if machine_names and m not in machine_names:
                inst.unknowns.unresolved_refs.append({"kind": "machine", "from": job.name, "to": m})
        for cal in (job.schedule.run_calendar, job.schedule.exclude_calendar):
            if cal and cal not in inst.calendars:
                inst.unknowns.unresolved_refs.append({"kind": "calendar", "from": job.name, "to": cal})
        for res in job.load.resources:
            if res.get("name") and inst.resources and res["name"] not in inst.resources:
                inst.unknowns.unresolved_refs.append({"kind": "resource", "from": job.name, "to": res["name"]})
