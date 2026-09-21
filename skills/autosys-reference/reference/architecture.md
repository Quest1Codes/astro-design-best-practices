---
topic: architecture
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [446, 447, 448, 449, 450, 451, 453, 874]
last_verified: 2026-09-17
confidence: cited
signals: [multi_instance, brownfield_astro]
---

# AutoSys 12.0 architecture

## Components [AS p.448-451]

| Component | Role |
|---|---|
| **Event server** (database) | Stores every object AutoSys uses — job/machine/calendar definitions and job events. Oracle, Sybase, or Microsoft SQL Server. [AS p.449] |
| **Application server** | Communication interface between the event server and client utilities; receives client requests, queries the event server, returns responses. [AS p.450] |
| **Scheduler** | The daemon/service that actually runs AutoSys: continually scans the event server for events (e.g. `STARTJOB`), checks starting conditions, and instructs the appropriate agent to act. [AS p.450] |
| **Agent** | Installed on every machine that runs jobs; extended by agent plug-ins (Database, Application Services, Oracle, PeopleSoft, SAP, Web Services). Replaces the legacy `auto_remote` agent from Unicenter AutoSys JM 4.5.1/r11. [AS p.450, p.452] |
| **Web UI** + **Web UI Collector** | The GUI; a client of the application server. |
| **Web server** | Apache Tomcat, installed as part of AutoSys setup; hosts web services on port 9443 by default, and talks to CA EEM on port 5250. [AS p.453] |
| **Client** | Any executable that calls the application server's APIs — the CLI utilities (`jil`, `autorep`, ...), Web UI services, or SDK-linked binaries. Does not need a database vendor client installed. [AS p.453] |
| **SDK** | Java and C++ APIs (`asapidoc.jar`, `asapicppdoc.jar`) for building custom clients. [AS p.453] |

## Instance model [AS p.448]

An **instance** is one licensed AutoSys installation running as a server with one or more
clients/agents, with its own scheduler, application server, event server, and web server,
operating independently of any other instance. The instance ID is an uppercase, 3-character
alphanumeric name (default `ACE`), referenced by the `$AUTOSERV` environment variable and set
only at install time. Multiple instances can run on the same computer (e.g. one for production,
one for development) but must have distinct instance IDs.

Schedulers are named `<instance>_SCH` (e.g. `ACE_SCH`) — this naming ensures uniqueness and
traceability of a scheduler across multiple instances. Two running schedulers cannot share an
instance name (non-HA mode), and two primary schedulers cannot share one in HA mode.

{syn: this is why `_lib/autosys_jil/models.py`'s `Estate` is instance-scoped
(`instances: dict[id, Instance]`) rather than a single flat job list — a real assessment is very
often multi-instance, and `job^INST` conditions and `insert_xinst` blocks are meaningless
without that scoping.}

## High availability [AS p.450, p.874]

- **Shadow scheduler**: a second scheduler on a separate computer that takes over if the primary
  fails. Together with the primary this is "high availability" mode.
- **Dual event server mode**: two event servers kept synchronized; AutoSys reads from one and
  writes to both simultaneously, so losing one to hardware/software/network failure loses no
  data. Independent of any database-level replication.
- **Tie-breaker scheduler**: required *only* when HA and dual-event-server modes are combined — a
  third scheduler on a third computer that stays permanently idle, periodically updates its
  heartbeat in the event servers, and resolves contention so a scheduler doesn't take over the
  primary role merely because of a network blip.
- **`HAPollInterval`** config parameter controls the polling cadence in HA mode (seconds between
  status polls). [AS p.874] — see `_lib/autosys_jil/registry/config_params.yaml`.

{syn: this is the direct AutoSys-side analog to the Airflow-side "scheduler HA and leader
election" question — see `astro-design-best-practices/reference/scheduler-and-dag/scheduler-ha-and-leader-election.md`.}

## Event flow [AS p.450]

1. The scheduler continually scans the event server for events.
2. When it finds e.g. a `STARTJOB` event, it checks whether the job's starting conditions
   (`condition:` attribute, calendar/schedule attributes) are satisfied.
3. Based on that, it instructs the relevant agent: start/stop a job, check resources, monitor a
   running job, or run a corrective procedure.
4. The agent executes the action and reports status back via events, which the scheduler
   processes on its next scan.

This is the mechanism a `condition:` string, a `date_conditions`/`start_times` schedule, and a
`sendevent`-driven manual intervention all ultimately go through — see
`reference/conditions-grammar.md`, `reference/scheduling-attributes.md`, and
`_lib/autosys_jil/history.py`'s `MANUAL_INTERVENTION_EVENTS` for the corresponding events.

## What this implies for a migration (pointers only — no recommendations here)

- One AutoSys instance is not automatically one Astro Deployment; the mapping is an
  `astro-target-architecture` decision keyed off instance count, `application`/`group` usage, and
  owner clusters — see `assess-astro-target-architecture/reference/decision-tables.md`.
- HA/dual-event-server concepts map to Astro's own scheduler HA and metadata-DB durability, not a
  1:1 component swap — see `astro-design-best-practices/reference/ha-and-dr/`.
- Agent plug-ins are the AutoSys-side analog of "what can run where" — see
  `_lib/autosys_jil/config.agent_capabilities()` and
  `reference/machines-load-and-resources.md`.
