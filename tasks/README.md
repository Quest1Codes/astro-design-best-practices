# Astro Design Best Practices — Task List

### Roadmap for building the `astro-design-best-practices` knowledge base — 130 topics, one task each — via the Researcher → Generator → Critic → Human Sign-off pipeline defined in `AGENTS.md`

---

## Overview

Numbered task files with Description/Deliverables/Acceptance Criteria/Dependencies, a phase table, and a task tracker — same convention as other Quest1 projects. **Task numbering is reserved for the 130 units of actual skill-generation work.** Repo setup, importing the mentor's companion skills, and building the axis matrix are prerequisites those tasks depend on, not tasks themselves — they're tracked as `SETUP-1` through `SETUP-6` so they don't consume slots in the 001-130 sequence.

**One task = one topic = one full run of the 4-stage pipeline = one output file.** E.g. Task 001 ("DAG-factory pattern for large estates") produces exactly `skills/astro-design-best-practices/reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md`, via `Researcher → Human Source Check → Generator → Critic → Human Sign-off`, and nothing else. See `tasks/001-dag-factory-pattern-for-large-estates.md` for the fully worked example every other task file follows.

**Topics 001-100** were the original 13-cluster taxonomy, derived from general reasoning about Astro/Airflow design concerns. **Topics 101-130** were added after actually researching AutoSys's own documentation (Broadcom TechDocs) — every one of them is grounded in a specific, real AutoSys mechanism (an attribute, a utility, a named architecture component) that 001-100 either missed entirely or covered too generically. A handful of the original 100 were also corrected or sharpened in place once the research surfaced the real terminology — see the inline notes on topics 002, 011, 015, 022, 023, 033, 034, 040, 069, and 081 below.

---

## Setup (prerequisites — not part of the 001-100 sequence)

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| SETUP-1 | [Repo Scaffolding + Agent Pipeline Definitions](SETUP-1-repo-scaffolding-and-agent-pipeline.md) | P0 | None | MERGED |
| SETUP-2 | [Import Mentor-Authored Companion Skills](SETUP-2-import-companion-skills.md) | P0 | SETUP-1 | MERGED |
| SETUP-3 | [Axis Relevance Matrix](SETUP-3-axis-relevance-matrix.md) | P0 | SETUP-1 | MERGED |
| SETUP-4 | [Seed Source List](SETUP-4-seed-source-list.md) (tier 1/2 URLs per cluster) | P0 | SETUP-3 | NOT STARTED |
| SETUP-5 | [Tier-3 Partner Material Ingestion Path](SETUP-5-tier3-partner-material-ingestion-path.md) | P1 | SETUP-3 | NOT STARTED |
| SETUP-6 | [`astro-design-best-practices` Skill Scaffold](SETUP-6-skill-scaffold.md) (SKILL.md + 19 cluster subdirectories) | P0 | SETUP-3 | NOT STARTED |

**Exit criteria**: Task 001 (and every task after it) can start without re-deriving pipeline mechanics, source policy, or where its output file goes.

---

## Phase 1 — The 100 Topic Tasks

Each task = one full run of the 4-stage pipeline for that topic's **default** guidance (axis branches are Phase 2). All parallel-safe once `SETUP-4` and `SETUP-6` are `MERGED` — each targets an independent file. Priority is set per cluster (see the Axis Relevance Matrix below for rationale).

### Cluster 1 — Scheduler & DAG Design (P0) — `reference/scheduler-and-dag/`

| # | Task |
|---|---|
| [001](001-dag-factory-pattern-for-large-estates.md) | DAG-factory pattern for large estates |
| 002 | DAG versioning and change-management strategy (git-based DAG file history + bundle/plugin versioning, replacing JIL's `insert_job`/`update_job`/`delete_job` in-place change model) |
| 003 | Scheduler HA and leader election |
| 004 | DAG parsing performance budget |
| 005 | TaskGroups vs. separate DAGs — decision criteria |
| 006 | Cross-DAG dependencies: Datasets vs. TriggerDagRunOperator vs. ExternalTaskSensor |
| 007 | Dynamic task mapping design (replacing AutoSys global-variable job cloning) |
| 008 | Custom Timetable design for AutoSys-calendar equivalents |
| 009 | DAG-level SLA and catchup/backfill policy |
| 010 | Idempotency and retry design for translated tasks |
| 011 | Concurrency controls — pools and `max_active_runs` (the Airflow-side mechanics; see topics 106-107 in Cluster 15 for the AutoSys `max_load`/`job_load`/virtual-resource concepts this design translates from) |
| 012 | Naming/tagging conventions at scale |
| 013 | One-off and ad-hoc job design |

### Cluster 2 — Executor & Worker Architecture (P0) — `reference/executor-and-worker/`

| # | Task |
|---|---|
| 014 | CeleryExecutor vs. KubernetesExecutor decision framework |
| 015 | Worker queue segregation mirroring AutoSys's physical machine/agent role assignment (which machines ran which job types — distinct from the load-balancing "virtual machine" construct, see topic 108) |
| 016 | Autoscaling design for bursty batch workloads |
| 017 | Per-task resource requests/limits (`executor_config`) |
| 018 | Node affinity/taints for specialized jobs |
| 019 | KEDA-based autoscaling |
| 020 | Hybrid executor strategy (Celery + KubernetesPodOperator for outliers) |
| 021 | Legacy-server access via SSHOperator |
| 022 | Worker fleet capacity-planning methodology (aggregate sizing from total job-count and schedule-density — see topic 106 for per-machine `max_load`/`job_load` unit translation specifically) |
| 023 | Zombie-task detection and handling (mirroring AutoSys's `chase` utility's reconciliation model — a job claiming to run but whose process isn't actually alive raises a `PROCESS_MIA` failure) |
| 024 | GPU/specialized-compute worker design |

### Cluster 3 — Metadata DB & State Design (P1) — `reference/metadata-db-and-state/`

| # | Task |
|---|---|
| 025 | Postgres sizing and instance-class selection |
| 026 | Connection pooling with PgBouncer |
| 027 | Metadata retention and cleanup policy |
| 028 | Backup and point-in-time recovery |
| 029 | Read-replica strategy for reporting |
| 030 | DB migration strategy across Airflow upgrades |
| 031 | Metadata DB growth at scale (thousands of DAGs) |
| 032 | Custom XCom backend design |

### Cluster 4 — Security & Multi-Tenancy Design (P0) — `reference/security-and-multitenancy/`

| # | Task |
|---|---|
| 033 | Workspace/Deployment boundary design (from AutoSys's `group` and `application` JIL attributes — the two orthogonal job-classification tags independent of box membership; corrected from an earlier draft that misnamed these "sub_application", which is not real AutoSys terminology) |
| 034 | RBAC role-shape design mirrored from EEM entitlements (the target role model itself; see topic 110 in Cluster 16 for the specific EEM-vs-native-provider migration mechanics) |
| 035 | Secrets-backend selection |
| 036 | Connection scoping and least privilege |
| 037 | SSO/OAuth integration design |
| 038 | Network isolation and VPC peering (Hybrid) |
| 039 | Audit-log design for access and actions |
| 040 | Federated vs. centralized self-service design (mapped from whether the source estate ran one AutoSys instance per business unit vs. one shared instance for the whole enterprise — see topic 101 for the instance-topology mapping itself) |
| 041 | API token / service-account lifecycle management |
| 042 | Encryption at rest and in transit design |

### Cluster 5 — Observability & Alerting Design (P1) — `reference/observability-and-alerting/`

| # | Task |
|---|---|
| 043 | `on_failure_callback` design patterns |
| 044 | Astronomer Alerts routing and escalation |
| 045 | Alert-fatigue and deduplication strategy |
| 046 | OpenLineage / data-lineage integration |
| 047 | Astronomer Observe integration |
| 048 | Metrics export (Prometheus/Datadog) |
| 049 | Log architecture — remote storage and retention |
| 050 | SLA-miss detection and escalation (replacing AutoSys alarms) |
| 051 | Incident-ticket automation (replacing Service Desk) |
| 052 | Dashboard design for stakeholder visibility (replacing WCC reporting) |

### Cluster 6 — CI/CD & Environment Topology (P0) — `reference/cicd-and-environment-topology/`

| # | Task |
|---|---|
| 053 | `astro` CLI deploy pipeline design |
| 054 | Dev/staging/prod Deployment topology |
| 055 | DAG testing and parse gates before merge |
| 056 | Branching strategy for DAG code |
| 057 | Environment promotion process |
| 058 | GitOps design for DAG deployment |
| 059 | Rollback strategy design |
| 060 | Multi-region Deployment topology at scale |
| 061 | Feature-flagging for gradual DAG rollout |
| 062 | Local development environment standards (`astro dev`) |

### Cluster 7 — Config & Secrets Design (P1) — `reference/config-and-secrets/`

| # | Task |
|---|---|
| 063 | Variables vs. Connections vs. secrets-backend decision framework |
| 064 | Per-environment variable scoping |
| 065 | Global-variable-sprawl remediation (from AutoSys `%%VAR%%` patterns) |
| 066 | Config-as-code for DAG-factory inputs |
| 067 | Secret rotation strategy |
| 068 | Environment-specific connection management |

### Cluster 8 — HA & DR Design (P1) — `reference/ha-and-dr/`

| # | Task |
|---|---|
| 069 | What Astro's built-in scheduler HA provides for free vs. what still needs explicit design (mapped from AutoSys's primary/shadow/tie-breaker three-scheduler dual-Event-Server model — see topics 125-126 in Cluster 19 for the specific heartbeat/failover-alarm mechanics this replaces) |
| 070 | Multi-region DR strategy |
| 071 | Backup cadence and RTO/RPO design |
| 072 | DR runbook design (replacing dual-Event-Server/Shadow-Scheduler runbooks) |
| 073 | Chaos/failure-testing strategy for the new platform |

### Cluster 9 — Regulatory & Compliance Design (P0) — `reference/regulatory-and-compliance/`

| # | Task |
|---|---|
| 074 | Audit-trail immutability design |
| 075 | Data retention/erasure lifecycle design |
| 076 | Data lineage for regulatory reporting |
| 077 | Access-control granularity for regulated data |
| 078 | Vertical overlay: financial services (SOX/Basel/AML) |
| 079 | Vertical overlay: healthcare (HIPAA) |
| 080 | Vertical overlay: government/public sector (FedRAMP/data residency) |

### Cluster 10 — Integration & Enterprise Mesh Design (P1) — `reference/integration-and-enterprise-mesh/`

| # | Task |
|---|---|
| 081 | Generic/homegrown ERP batch-integration patterns not covered by AutoSys's own native ERP agents (see Cluster 18, topics 117-119, for the specific SAP/PeopleSoft/Oracle EBS native-agent migrations) |
| 082 | EDI/file-transfer integration patterns |
| 083 | Ticketing/ITSM integration design (ServiceNow/PagerDuty) |
| 084 | SIEM export integration design |
| 085 | BI/reporting-layer integration |
| 086 | Mainframe-boundary Astro-side architecture (companion to the imported mainframe-boundary skill) |

### Cluster 11 — Migration Execution & Coexistence Architecture (P1) — `reference/migration-execution-and-coexistence/`

| # | Task |
|---|---|
| 087 | Dual-run/shadow-DAG architecture during coexistence |
| 088 | Data-reconciliation architecture for parity verification |
| 089 | Cutover architecture per box |
| 090 | Rollback architecture during cutover |

### Cluster 12 — Cost & Capacity Governance (P2) — `reference/cost-and-capacity-governance/`

| # | Task |
|---|---|
| 091 | Cost allocation/chargeback design across Workspaces/Deployments |
| 092 | Capacity planning from job-count and schedule-density |
| 093 | Autoscaling cost-optimization patterns |
| 094 | Idle-resource reclamation design |

### Cluster 13 — Governance & Operating Model (P2) — `reference/governance-and-operating-model/`

| # | Task |
|---|---|
| 095 | Centralized vs. federated operating model design |
| 096 | DAG-ownership and support-model design (on-call, runbooks) |
| 097 | Legacy-job deprecation process during migration |
| 098 | Documentation-as-code strategy |
| 099 | Training/enablement design for AutoSys ops staff |
| 100 | Vendor lock-in and exit-strategy design |

### Cluster 14 — Multi-Instance & Cross-Instance Architecture (P1) — `reference/multi-instance-and-cross-instance/`

*New — grounded in AutoSys's actual instance model (each install has a 3-character instance ID, e.g. the default `ACE`; distinct instances have distinct `$AUTOSERV`/`$AUTOUSER` values and communicate cross-instance rather than being one clustered system) and its `group`/`application` job-classification attributes.*

| # | Task |
|---|---|
| 101 | Multi-instance topology mapping (per-instance `$AUTOSERV`/`$AUTOUSER` separation) to Astro Workspace/Deployment boundaries |
| 102 | CA CCI cross-instance/cross-platform event architecture → Astro cross-Deployment triggering design |
| 103 | Cross-instance job dependency migration (remote `CHANGE_STATUS` events between instance Event Servers) → Dataset/REST-based cross-Deployment dependencies |
| 104 | Job classification via `group`/`application` attributes (independent of box hierarchy) → Astro tagging and `dag_id` namespacing design |
| 105 | Multi-timezone distributed agent scheduling (`autotimezone`) → Airflow DAG timezone (`pendulum`) design and DST edge cases |

### Cluster 15 — Machine Load, Queuing & Virtual Resources (P0) — `reference/machine-load-and-virtual-resources/`

*New — grounded in AutoSys's actual load-management primitives: `max_load`/`job_load` (arbitrary weighted units, no fixed relationship to physical CPU/memory), `QUE_WAIT` status when no machine has capacity, and named "virtual resources" that throttle concurrent jobs like a semaphore, independent of machine load.*

| # | Task |
|---|---|
| 106 | `max_load`/`job_load` weighted machine queuing → Airflow Pools sizing design |
| 107 | Named virtual resources (semaphore-style concurrency throttling, independent of machine load) → Airflow Pools/`max_active_tis_per_dag` design |
| 108 | Virtual machine (load-balancing machine-group) definitions → KubernetesExecutor/CeleryExecutor queue-group design |
| 109 | `QUE_WAIT` visibility and queue-depth monitoring → Airflow queued-state observability design |

### Cluster 16 — Native Security & Credential Architecture (P0) — `reference/native-security-and-credentials/`

*New — grounded in AutoSys's actual security-provider model: CA EEM as the default non-native provider, `autosys_secure` as the system-level security bootstrap command, Symantec PAM as the credential-vaulting integration, and RSA Identity Governance for ACL/access-review automation.*

| # | Task |
|---|---|
| 110 | CA EEM vs. native OS security-provider migration → Astro RBAC provider design |
| 111 | `autosys_secure` system-level security bootstrap → Astro Workspace/Deployment RBAC bootstrap design |
| 112 | PAM (Privileged Access Manager) credential-vaulting integration → Astro secrets-backend design specifically for job-execution credentials |
| 113 | RSA Identity Governance ACL/access-review automation → Astro periodic access-review design |

### Cluster 17 — Reporting, Forecasting & Operational Visibility (P1) — `reference/reporting-and-forecasting/`

*New — grounded in AutoSys's Forecast feature (what-if scheduling with Gantt-chart output for maintenance-window planning) and `autorep`'s read-only reporting surface, both of which have no direct Airflow-native equivalent.*

| # | Task |
|---|---|
| 114 | Forecast feature (what-if scheduling, Gantt-chart maintenance-window planning) → Astro-side design for this capability gap — flag explicitly as no native Airflow equivalent, not just "use the UI" |
| 115 | `autorep` ad-hoc reporting query patterns (job status, run history, machine/calendar/global-variable listings) → Airflow metadata-DB reporting-query design |
| 116 | Cross-instance enterprise console visibility → Astronomer multi-Deployment dashboard design |

### Cluster 18 — Native ERP & Web-Service Integration Agents (P1) — `reference/native-erp-and-webservice-agents/`

*New — grounded in AutoSys's actual out-of-the-box agents for SAP (Application Job type), PeopleSoft, and Oracle E-Business Suite, plus its native `job_type: WS` (SOAP/REST web-service job, no wrapper script) and its own REST web-services API surface (AEWS, OpenAPI/Swagger-documented).*

| # | Task |
|---|---|
| 117 | SAP Application Job agent migration → Airflow SAP provider/operator design |
| 118 | PeopleSoft agent migration → Airflow custom-operator design for PeopleSoft |
| 119 | Oracle E-Business Suite agent migration → Airflow custom-operator design for Oracle EBS |
| 120 | Native Web Services job type (`job_type: WS`, SOAP/REST, no wrapper script) → Airflow `SimpleHttpOperator`/`HttpOperator` design |
| 121 | AEWS REST API surface parity (the AutoSys control-plane's own REST API, distinct from the generic CI/CD API topic in Cluster 6) → Airflow REST API design |

### Cluster 19 — Container-Native Agent & Legacy-Estate Precision (P1) — `reference/container-native-and-legacy-precision/`

*New — grounded in AutoSys's own Kubernetes/OpenShift container-agent feature (a real, current capability, distinct from the imported `migrating-autosys-k8s-to-astronomer` companion skill, which covers AutoSys already *running on* k8s — this cluster is about AutoSys's *own* agent-in-a-container feature and what parity looks like), deprecated machine types, and the dual-Event-Server HA mechanics named in the research for topic 069.*

| # | Task |
|---|---|
| 122 | AutoSys Kubernetes/OpenShift container-agent feature parity → KubernetesPodOperator/CRD-interaction design |
| 123 | Multi-container pod targeted-execution parity (AutoSys can exec into one container of a multi-container pod) → Airflow K8s exec-into-container design |
| 124 | Legacy machine-type inventory (deprecated `n`/`l`/`L`/`r` types, only `a`-type Workload Automation Agent machines current) as a pre-migration cleanup task |
| 125 | AutoSys "client" surface inventory (JIL, `autorep`, `sendevent`, Web UI/WCC, SDK — every executable that talks to the Application Server) → Astro API/CLI/UI parity mapping design |
| 126 | Source Event-Server RDBMS dialect considerations (historically Oracle/SQL Server/Sybase-backed) → Astro metadata-DB migration-source design |
| 127 | Native DB job type execution patterns → Airflow SQL-operator design |
| 128 | Heartbeat/`HAPollInterval` failover-detection mechanics (primary/shadow/tie-breaker scheduler heartbeats, default 15s poll) → Airflow scheduler HA heartbeat/leader-election design |
| 129 | `EP_ROLLOVER` alarm and failover-event handling → Astro failover alerting design |
| 130 | Job-history/audit-trail source inventory (what exists in the old Event Server's job-history tables that needs migrating or archiving) → Astro metadata-DB audit/history migration design |

**Exit criteria**: All 130 files exist under `skills/astro-design-best-practices/reference/`, each Critic-verified and Human-signed-off, `SKILL.md`'s index updated.

**On individual task files**: only Task 001 is written out in full right now, as the confirmed template (`tasks/001-dag-factory-pattern-for-large-estates.md`). The remaining 129 follow the identical shape (Description grounded in the AutoSys-side problem it solves + why its priority, "How this task gets built" naming the cluster's relevant axes from the matrix below, Deliverables, Acceptance Criteria mirroring `AGENTS.md`'s Definition of Done, Dependencies on `SETUP-4`/`SETUP-6`) — generated just before each is picked up, not all 130 at once up front, per the project's own "don't one-shot" principle.

---

## Phase 2 — Axis-Branch Layering

One follow-on task per **H-rated cell** in the Axis Relevance Matrix below, per topic (M-rated cells are usually a short callout inside the Phase 1 task itself — see Task 001's example — not a separate task; L-rated cells just need "checked, no branch needed" recorded by the Critic). Numbered `{parent}a`, `{parent}b`, ... as started (e.g. `001a` = "add coexistence-temporal branching to the DAG-factory topic" if it turns out to need more than Task 001's built-in callout). Not enumerated individually here — premature before Phase 1 baselines exist.

**Dependency rule**: `NNNx` depends only on `NNN` being `MERGED`.

---

## Phase 3 — Maintenance Cadence

| # | Task | Priority | Dependencies |
|---|------|----------|---------------|
| MAINT-1 | Define quarterly re-verification trigger tied to Astro Runtime release notes | P2 | All Phase 1 tasks |

This is the one piece of "later" work that stays in this project's scope rather than being pushed out — keeping the 100 files accurate over time is part of the content's own job, distinct from how/whether anything consumes it (see below).

---

## Axis Relevance Matrix (by cluster)

Rated at the **cluster** level. Each topic inherits its cluster's ratings as a starting point; refine per-topic during that topic's own Researcher brief if it turns out to differ (Task 001's file shows this in practice — Cluster 1 is rated H on estate scale and M on migration-temporal, and the task file names both explicitly). **H** = real decision table needed, **M** = short callout, **L** = "checked, no branch needed."

| Cluster | Deployment model (A) | Estate scale (B) | Migration temporal (C) | Org model (D) | Vertical/compliance (E) | Executor substrate (F) | Integration surface (G) |
|---|---|---|---|---|---|---|---|
| 1. Scheduler & DAG Design | L | **H** | M | L | L | L | L |
| 2. Executor & Worker Architecture | **H** | **H** | L | M | L | **H** | L |
| 3. Metadata DB & State Design | **H** | **H** | L | L | M | L | L |
| 4. Security & Multi-Tenancy Design | **H** | **H** | L | **H** | **H** | L | M |
| 5. Observability & Alerting Design | M | M | L | L | M | L | **H** |
| 6. CI/CD & Environment Topology | **H** | **H** | **H** | **H** | M | L | L |
| 7. Config & Secrets Design | **H** | M | L | M | **H** | L | L |
| 8. HA & DR Design | **H** | M | L | L | M | L | L |
| 9. Regulatory & Compliance Design | M | L | L | L | **H** | L | M |
| 10. Integration & Enterprise Mesh Design | M | M | L | L | M | L | **H** |
| 11. Migration Execution & Coexistence | M | M | **H** | L | L | L | L |
| 12. Cost & Capacity Governance | **H** | **H** | L | M | L | M | L |
| 13. Governance & Operating Model | L | **H** | L | **H** | L | L | L |
| 14. Multi-Instance & Cross-Instance Architecture | M | **H** | M | **H** | L | L | M |
| 15. Machine Load, Queuing & Virtual Resources | L | **H** | L | L | L | **H** | L |
| 16. Native Security & Credential Architecture | **H** | M | L | M | **H** | L | M |
| 17. Reporting, Forecasting & Operational Visibility | M | M | L | L | M | L | **H** |
| 18. Native ERP & Web-Service Integration Agents | L | L | L | L | M | L | **H** |
| 19. Container-Native Agent & Legacy-Estate Precision | **H** | M | M | L | L | **H** | L |

---

## Task Tracker

Status legend: `NOT STARTED` | `IN PROGRESS` | `IN REVIEW (Critic)` | `IN SIGN-OFF` | `MERGED` | `BLOCKED`

| # | Task | Status | Owner | Notes |
|---|------|--------|-------|-------|
| SETUP-1 | Repo Scaffolding + Agent Pipeline Definitions | MERGED | — | |
| SETUP-2 | Import Mentor-Authored Companion Skills | MERGED | — | |
| SETUP-3 | Axis Relevance Matrix | MERGED | — | Cluster-level (13 rows) |
| SETUP-4 | Seed Source List | PARTIAL | — | Done informally for Clusters 1-2 only, as part of generating 001-020 (not run as its own gated task); Clusters 3-19 still NOT STARTED |
| SETUP-5 | Tier-3 Partner Material Ingestion Path | NOT STARTED | — | |
| SETUP-6 | Skill Scaffold | PARTIAL | — | `SKILL.md` + `reference/scheduler-and-dag/` + `reference/executor-and-worker/` exist; remaining 17 cluster subdirectories NOT STARTED |
| 001-013 | Cluster 1 — Scheduler & DAG Design (complete) | CRITIC-REVIEWED, NOT SIGNED OFF | — | Generated + Critic-pass-reviewed autonomously; Human Source Check and Human Sign-off gates explicitly skipped per direct instruction. Two Critic passes (001-010, 011-013 as part of a combined pass) found and fixed real defects — see `research/cluster-1-topics-001-010-critic-report.md` and `research/topics-011-020-critic-report.md`. Several `NEEDS_EXEC_CHECK` items remain, genuinely requiring a human to run something real. Not to be treated as fully verified until `.agents/signoff-checklist.md` is completed per file. |
| 014-020 | Cluster 2 — Executor & Worker Architecture (7 of 11) | CRITIC-REVIEWED, NOT SIGNED OFF | — | Same process as above. This batch's Critic pass found 2 outright `FAIL`s (a fabricated KEDA polling-interval/cool-down figure, and two Kubernetes resource-limit claims cited to a source supporting neither) — both fixed; see `research/topics-011-020-critic-report.md`. One `NEEDS_EXEC_CHECK` remains open (KEDA `cooldownPeriod` ambiguity). |
| 021-100 | Remaining Cluster 2 (4 topics) + Clusters 3-13 | NOT STARTED | — | Task files generated per-cluster as work starts, following 001's shape |
| 101-130 | Cluster 14-19 topic tasks | NOT STARTED | — | Added after researching real AutoSys documentation (Broadcom TechDocs) — see the per-cluster grounding notes above |

---

## Summary

- **130 topic tasks** across **19 clusters** — this is the entire scope of the project
- **6 setup tasks** (`SETUP-1..6`) — prerequisites, not counted among the 130
- **4 companion skills imported** as-is from the mentor's existing work — unchanged, not regenerated by this pipeline
- **30 topics (101-130) and corrections to 10 of the original 100** (topics 002, 011, 015, 022, 023, 033, 034, 040, 069, 081) came from actually researching Broadcom's AutoSys documentation rather than from general reasoning alone — see the individual grounding notes above each new cluster and the inline corrections on those 10 topics
- Every topic task runs the identical 4-stage pipeline: `AGENTS.md` is the source of truth for *how*; this file is the source of truth for *what, in what order*

## Explicitly out of scope for this project

**Consuming this knowledge base — wiring it into Shinro's assessment-report generation, packaging it behind an MCP server, or any other downstream integration — is not a phase here.** This project's job ends at producing 130 sourced, Critic-verified, human-signed-off files. When Shinro (or anything else) is ready to consume them, that's separate work in the consuming project's own repo — for Shinro specifically, it would extend `skill_loader.py` the same way `autosys-astronomer-expert` already works, but that decision and its implementation belong to whoever owns that integration, later, not to this roadmap.

## Source Documents

- `AGENTS.md` — pipeline definition, design principles, agent role files in `.agents/`
- `research/` — permanent per-topic fact-sheets, populated as Phase 1/2 tasks complete
