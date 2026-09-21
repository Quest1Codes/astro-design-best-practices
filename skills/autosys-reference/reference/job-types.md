---
topic: job-types
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2425, 2459, 2469, 2547, 2549, 2550, 2551, 2552, 2848, 2855]
last_verified: 2026-09-17
confidence: mixed
signals: [erp_sap, zos, hadoop, windows]
---

# JIL job types

## Default and aliases [AS p.2550-2552]

- `job_type` is **optional**; if omitted, the job is `CMD` [AS p.2550].
- Backward-compatible single-letter aliases: `c` → `CMD`, `f` → `FW`, `b` → `BOX` [AS p.2552].
  In AutoSys r11+ these must be exact (`b`/`box`, `c`/`cmd`, `f`/`fw`) — the legacy
  first-character-only matching from Unicenter AutoSys JM no longer works [AS p.2552].
- `_lib.autosys_jil.registry.resolve_job_type()` implements this exactly (case-insensitive
  alias lookup, default to `CMD`).

## Coverage note (read before trusting a page citation below)

The canonical `job_type` attribute enum [AS p.2550-2552] lists 53 of AutoSys's job types on one
page pair. Several real job types are documented elsewhere in the PDF under their own attribute
pages rather than in that enum (`WBSVC`, `WOL`, `WSDOC`, `SQL`, `ZOS`, `ZOSM`, `ZOSDST` — each
independently verified below with its own page). **Three job types this table's family grouping
expects (`SQLAGENT`, `SQOOP`, `CMDMACHINE`) do not appear anywhere in the ingested 12.0 corpus**
under any spelling — `_lib/autosys_jil/registry/job_type_families.yaml` includes them because
they are documented for other AutoSys/CA Workload Automation releases or plugin guides not part
of this PDF. Treat those three as `PRACTITIONER JUDGMENT — not independently verifiable as of
2026-09-17`: real in some AutoSys estates, but not something this skill can cite a 12.0 page for.
`job_types.json`'s `in_12_0_doc` field is conservative in the *other* direction — it is `false`
for some job types (like `WBSVC`) that this file's per-type citations below confirm are, in fact,
documented, just not in that one specific enum list. Trust this file's per-row citation over the
raw registry flag.

## Core [AS p.2551 enum, individual pages noted]

| Code | Name | Notes |
|---|---|---|
| `CMD` | Command | Default job type. Runs a command/script on a real or virtual machine. [AS p.2550] |
| `BOX` | Box | Container for other jobs/boxes; no command of its own. [AS p.2551] |
| `CMDMACHINE` | Command (machine-selected at run time) | PRACTITIONER JUDGMENT — not found in the 12.0 corpus; treat as unverified for this doc version. |

## File watch / trigger [AS p.2551]

| Code | Name |
|---|---|
| `FW` | File Watcher — watches for a file matching a pattern. |
| `FT` | **File Trigger** — event-driven file watch via the agent. **Not** a transfer type — do not confuse with `FTP`/`SCP` (the existing `mapping.md` line 17 in the pre-refactor skill got this wrong). |

## File transfer [AS p.2551]

| Code | Name |
|---|---|
| `FTP` | File Transfer Protocol |
| `SCP` | Secure Copy |

## Database

| Code | Name | Page |
|---|---|---|
| `SQL` | SQL | [AS p.2549] (listed among `job_terminator`'s supported job types; not in the main enum) |
| `DBPROC` | Database Stored Procedure | [AS p.2551] |
| `DBMON` | Database Monitor | [AS p.2551] |
| `DBTRIG` | Database Trigger | [AS p.2551] |
| `SQLAGENT` | SQL Server Agent Job | PRACTITIONER JUDGMENT — not found in the 12.0 corpus. |

## OS monitors [AS p.2551]

| Code | Name |
|---|---|
| `OMCPU` | CPU Monitoring |
| `OMD` | Disk Monitoring |
| `OMEL` | Windows Event Log Monitoring |
| `OMIP` | IP Monitoring |
| `OMP` | Process Monitoring |
| `OMS` | Windows Service Monitoring |
| `OMTF` | Text File Reading and Monitoring |

## Web and messaging

| Code | Name | Page |
|---|---|---|
| `HTTP` | HTTP | [AS p.2551] |
| `WBSVC` | Web Service RPC/Encoded | [AS p.2459, p.2468-2469] |
| `WSDOC` | Web Service Document/Literal | [AS p.2546-2547] |
| `JMSPUB` | JMS Publish | [AS p.2551] |
| `JMSSUB` | JMS Subscribe | [AS p.2551] |
| `JMXMAG` | JMX-MBean Attribute Get | [AS p.2551] |
| `JMXMAS` | JMX-MBean Attribute Set | [AS p.2551] |
| `JMXMC` | JMX-MBean Create Instance | [AS p.2551] |
| `JMXMOP` | JMX-MBean Operation | [AS p.2551] |
| `JMXMREM` | JMX-MBean Remove Instance | [AS p.2551] |
| `JMXSUB` | JMX-MBean Subscribe | [AS p.2551] |
| `SNMPGET` | SNMP Value Get | [AS p.2551] |
| `SNMPSET` | SNMP Value Set | [AS p.2551] |

## ERP (SAP / PeopleSoft / Oracle EBS) [AS p.2551]

| Code | Name |
|---|---|
| `SAP` | SAP R/3 |
| `SAPBDC` | SAP Batch Input Session |
| `SAPBWIP` | SAP BW InfoPackage |
| `SAPBWPC` | SAP BW Process Chain |
| `SAPDA` | SAP Data Archiving |
| `SAPEVT` | SAP Event Monitor |
| `SAPJC` | SAP Job Copy |
| `SAPPM` | SAP Process Monitor |
| `PS` | PeopleSoft |
| `OASG` | Oracle E-Business Suite Single Request |
| `OASET` | Oracle E-Business Suite Request Set |
| `OACOPY` | Oracle E-Business Suite Copy Single Request |

## Java [AS p.2551]

| Code | Name |
|---|---|
| `POJO` | Plain Old Java Object |
| `ENTYBEAN` | Entity Bean |
| `SESSBEAN` | Session Bean |
| `JAVARMI` | Java Remote Method Invocation |

## Hadoop

| Code | Name | Page |
|---|---|---|
| `HDFS` | Hadoop HDFS | [AS p.2551] |
| `HIVE` | Hadoop Hive | [AS p.2551] |
| `PIG` | Hadoop Pig | [AS p.2551] |
| `OOZIE` | Hadoop Oozie Workflow | [AS p.2551] |
| `SQOOP` | Hadoop Sqoop | PRACTITIONER JUDGMENT — not found in the 12.0 corpus. |

## Platform (mainframe / IBM i / remote exec)

| Code | Name | Page |
|---|---|---|
| `I5` | i5/OS | [AS p.2551] |
| `ZOS` | z/OS Regular | [AS p.2549] |
| `ZOSM` | z/OS Manual | [AS p.2549] |
| `ZOSDST` | z/OS Data Set Trigger | [AS p.2848-2849] |
| `MICROFOCUS` | Micro Focus | [AS p.2551] |
| `PROXY` | Remote Execution | [AS p.2551] |
| `WOL` | Wake on LAN | [AS p.2425] |
| `K8S` | Kubernetes container job | **AutoSys 12.1+, not in this 12.0 corpus.** `astro-design-best-practices`'s `container-native-and-legacy-precision` cluster already assumes it exists; keep that cluster's `confidence: mixed` until a 12.1 source is ingested (plan §10 decision #5). |

Custom z/OS integration is a distinct migration concern from the rest of the estate — see
`migrate-topology-mainframe-boundary`, which detects `ZOS`/`ZOSM`/`ZOSDST` by job type first
(definitive) and pattern-matches everything else (heuristic).

## PAM / Informatica [AS p.2551]

| Code | Name |
|---|---|
| `PAPROC` | Process Automation Process Execution |
| `PAREQ` | Process Automation Start Request Form |
| `INFORMATICA` | Informatica |

## Custom job types [AS p.2855]

`insert_job_type` defines a customer-specific job type backed by a script/command the
administrator registers — used when none of the built-in types fit (e.g. wrapping a proprietary
tool). `_lib.autosys_jil.parser` stores these as `GenericObject(kind="job_type", ...)` in
`Instance.objects`; a job using a custom type is `job_type_known=False` unless it happens to
collide with a built-in code, and is recorded in `Instance.unknowns.job_types` so the assessment
can surface it as its own row rather than lumping it in with genuinely-unrecognized/typo'd job
types. Cross-check `Instance.objects` for a matching `job_type:<name>` entry before treating an
unknown job type as an error rather than a legitimate customer extension.
