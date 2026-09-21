"""Typed vocabulary shared by every AutoSys -> Astronomer script.

Deterministic data holders only; no I/O.

Sources:
  - [AS p.2400] JIL object kinds (jobs, machines, resources, external instances,
    monitors/reports, blobs/globs, job types, connection profiles)
  - [AS p.2435] condition attribute grammar
  - [AS p.2912] system states
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

SCHEMA_VERSION = "2.0"


@dataclass(frozen=True, slots=True)
class Provenance:
    file: str
    line: int
    block_index: int
    instance: str
    subcommand: str  # insert_job / update_job / override_job / delete_job / ...

    def as_dict(self) -> dict[str, Any]:
        return {"file": self.file, "line": self.line, "block_index": self.block_index,
                "instance": self.instance, "subcommand": self.subcommand}


@dataclass(slots=True)
class Attr:
    name: str
    raw: str
    value: Any
    known: bool
    pdf_page: int | None = None
    family: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Schedule:
    date_conditions: bool = False
    days_of_week: list[str] = field(default_factory=list)
    start_times: list[str] = field(default_factory=list)
    start_mins: list[int] = field(default_factory=list)
    run_window: tuple[str, str] | None = None
    run_calendar: str | None = None
    exclude_calendar: str | None = None
    timezone: str | None = None
    must_start_times: list[str] = field(default_factory=list)
    must_complete_times: list[str] = field(default_factory=list)

    @property
    def has_schedule(self) -> bool:
        return self.date_conditions and (bool(self.start_times) or bool(self.start_mins) or bool(self.run_window))


@dataclass(slots=True)
class SLA:
    term_run_time: int | None = None
    max_run_alarm: int | None = None
    min_run_alarm: int | None = None
    n_retrys: int | None = None
    max_exit_success: int | None = None
    success_codes: list[int] = field(default_factory=list)


@dataclass(slots=True)
class Load:
    job_load: int | None = None
    priority: int | None = None
    resources: list[dict[str, Any]] = field(default_factory=list)
    machine: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Alerting:
    alarm_if_fail: bool | None = None
    alarm_if_terminated: bool | None = None
    alarm_if_success: bool | None = None
    send_notification: bool | None = None
    notification_emails: list[str] = field(default_factory=list)
    notification_msg: str | None = None
    svcdesk: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class IO:
    std_in_file: str | None = None
    std_out_file: str | None = None
    std_err_file: str | None = None
    profile: str | None = None
    envvar: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Job:
    name: str
    job_type: str
    job_type_known: bool
    attrs: dict[str, Attr]
    provenance: Provenance
    box_name: str | None = None
    command: str | None = None
    owner: str | None = None
    application: str | None = None
    group: str | None = None
    description: str | None = None
    condition_raw: str | None = None
    condition: Any = None  # conditions.ConditionAST | None
    condition_error: str | None = None
    schedule: Schedule = field(default_factory=Schedule)
    sla: SLA = field(default_factory=SLA)
    load: Load = field(default_factory=Load)
    alerting: Alerting = field(default_factory=Alerting)
    io: IO = field(default_factory=IO)
    box_terminator: bool | None = None
    job_terminator: bool | None = None
    box_success: str | None = None
    box_failure: str | None = None
    auto_hold: bool | None = None
    auto_delete: int | None = None
    permission: list[str] = field(default_factory=list)
    extras: dict[str, str] = field(default_factory=dict)
    modified_by: list[Provenance] = field(default_factory=list)
    deleted: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def is_box(self) -> bool:
        return self.job_type == "BOX"


@dataclass(slots=True)
class Box:
    name: str
    children: list[str] = field(default_factory=list)
    parent: str | None = None
    depth: int = 0
    inferred: bool = False  # referenced by box_name but no BOX job in the export


@dataclass(slots=True)
class Machine:
    name: str
    type: str | None = None  # a (agent, current) / v (virtual) / legacy n,l,L,r  [AS p.2874]
    opsys: str | None = None
    node_name: str | None = None
    agent_name: str | None = None
    max_load: int | None = None
    factor: float | None = None
    members: list[str] = field(default_factory=list)  # virtual machine components
    port: int | None = None
    encryption_type: str | None = None
    description: str | None = None
    extras: dict[str, str] = field(default_factory=dict)
    provenance: Provenance | None = None


@dataclass(slots=True)
class Resource:
    name: str
    res_type: str | None = None  # D (depletable) / R (renewable)  [AS p.2886]
    amount: int | None = None
    machine: str | None = None
    description: str | None = None
    provenance: Provenance | None = None


@dataclass(slots=True)
class Xinst:
    name: str
    xtype: str | None = None
    xmachine: str | None = None
    xport: int | None = None
    xcrypt_type: str | None = None
    xmanager: str | None = None
    provenance: Provenance | None = None


@dataclass(slots=True)
class Calendar:
    name: str
    dates: list[date] = field(default_factory=list)
    source: str = "unknown"  # autocal_asc / insert_calendar / unknown
    provenance: Provenance | None = None


@dataclass(slots=True)
class GlobalVar:
    name: str
    value: str
    last_changed: str | None = None


@dataclass(slots=True)
class GenericObject:
    """monbro, connection profile, blob/glob, job_type definition."""
    kind: str
    name: str
    attrs: dict[str, str]
    provenance: Provenance | None = None


@dataclass(slots=True)
class Unknowns:
    job_types: dict[str, list[str]] = field(default_factory=dict)  # type -> job names
    attributes: dict[str, list[str]] = field(default_factory=dict)  # attr -> job names
    object_kinds: dict[str, list[str]] = field(default_factory=dict)
    condition_parse_failures: list[dict[str, str]] = field(default_factory=list)
    unresolved_refs: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class Instance:
    id: str
    jobs: dict[str, Job] = field(default_factory=dict)
    boxes: dict[str, Box] = field(default_factory=dict)
    machines: dict[str, Machine] = field(default_factory=dict)
    resources: dict[str, Resource] = field(default_factory=dict)
    xinsts: dict[str, Xinst] = field(default_factory=dict)
    calendars: dict[str, Calendar] = field(default_factory=dict)
    globals: dict[str, GlobalVar] = field(default_factory=dict)
    objects: dict[str, GenericObject] = field(default_factory=dict)  # key: f"{kind}:{name}"
    overrides: list[dict[str, Any]] = field(default_factory=list)
    config: dict[str, str] = field(default_factory=dict)
    agent_capabilities: dict[str, list[str]] = field(default_factory=dict)  # machine -> plugin families
    unknowns: Unknowns = field(default_factory=Unknowns)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Evidence:
    path: str
    sha256: str
    kind: str
    size: int
    received_at: str


@dataclass(slots=True)
class Estate:
    instances: dict[str, Instance] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    nfr: dict[str, Any] = field(default_factory=dict)
    # enrichment sections filled by later scripts (kept as plain dicts for JSON round-trip)
    stats: dict[str, Any] = field(default_factory=dict)
    graph: dict[str, Any] = field(default_factory=dict)
    schedules: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, Any] = field(default_factory=dict)
    command_summary: dict[str, Any] = field(default_factory=dict)
    history: dict[str, Any] = field(default_factory=dict)
    scores: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)
    waves: list[dict[str, Any]] = field(default_factory=list)
    brownfield: dict[str, Any] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)
    status: dict[str, Any] = field(default_factory=dict)

    def all_jobs(self):
        for inst in self.instances.values():
            for job in inst.jobs.values():
                yield inst.id, job
