# Astro Migration Skills — Task List

### Roadmap for building the `astro-design-best-practices` knowledge base — 100 topics, one task each — via the Researcher → Generator → Critic → Human Sign-off pipeline defined in `AGENTS.md`

---

## Overview

Numbered task files with Description/Deliverables/Acceptance Criteria/Dependencies, a phase table, and a task tracker — same convention as other Quest1 projects. **Task numbering is reserved for the 100 units of actual skill-generation work.** Repo setup, importing the mentor's companion skills, and building the axis matrix are prerequisites the 100 tasks depend on, not tasks themselves — they're tracked as `SETUP-1` through `SETUP-6` so they don't consume slots in the 001-100 sequence.

**One task = one topic = one full run of the 4-stage pipeline = one output file.** E.g. Task 001 ("DAG-factory pattern for large estates") produces exactly `skills/astro-design-best-practices/reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md`, via `Researcher → Human Source Check → Generator → Critic → Human Sign-off`, and nothing else. See `tasks/001-dag-factory-pattern-for-large-estates.md` for the fully worked example every other task file follows.

---

## Setup (prerequisites — not part of the 001-100 sequence)

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| SETUP-1 | [Repo Scaffolding + Agent Pipeline Definitions](SETUP-1-repo-scaffolding-and-agent-pipeline.md) | P0 | None | MERGED |
| SETUP-2 | [Import Mentor-Authored Companion Skills](SETUP-2-import-companion-skills.md) | P0 | SETUP-1 | MERGED |
| SETUP-3 | [Axis Relevance Matrix](SETUP-3-axis-relevance-matrix.md) | P0 | SETUP-1 | MERGED |
| SETUP-4 | [Seed Source List](SETUP-4-seed-source-list.md) (tier 1/2 URLs per cluster) | P0 | SETUP-3 | NOT STARTED |
| SETUP-5 | [Tier-3 Partner Material Ingestion Path](SETUP-5-tier3-partner-material-ingestion-path.md) | P1 | SETUP-3 | NOT STARTED |
| SETUP-6 | [`astro-design-best-practices` Skill Scaffold](SETUP-6-skill-scaffold.md) (SKILL.md + 13 cluster subdirectories) | P0 | SETUP-3 | NOT STARTED |

**Exit criteria**: Task 001 (and every task after it) can start without re-deriving pipeline mechanics, source policy, or where its output file goes.

---

## Phase 1 — The 100 Topic Tasks

Each task = one full run of the 4-stage pipeline for that topic's **default** guidance (axis branches are Phase 2). All parallel-safe once `SETUP-4` and `SETUP-6` are `MERGED` — each targets an independent file. Priority is set per cluster (see the Axis Relevance Matrix below for rationale).

### Cluster 1 — Scheduler & DAG Design (P0) — `reference/scheduler-and-dag/`

| # | Task |
|---|---|
| [001](001-dag-factory-pattern-for-large-estates.md) | DAG-factory pattern for large estates |
| 002 | DAG versioning and change-management strategy |
| 003 | Scheduler HA and leader election |
| 004 | DAG parsing performance budget |
| 005 | TaskGroups vs. separate DAGs — decision criteria |
| 006 | Cross-DAG dependencies: Datasets vs. TriggerDagRunOperator vs. ExternalTaskSensor |
| 007 | Dynamic task mapping design (replacing AutoSys global-variable job cloning) |
| 008 | Custom Timetable design for AutoSys-calendar equivalents |
| 009 | DAG-level SLA and catchup/backfill policy |
| 010 | Idempotency and retry design for translated tasks |
| 011 | Concurrency controls — pools and `max_active_runs` |
| 012 | Naming/tagging conventions at scale |
| 013 | One-off and ad-hoc job design |

### Cluster 2 — Executor & Worker Architecture (P0) — `reference/executor-and-worker/`

| # | Task |
|---|---|
| 014 | CeleryExecutor vs. KubernetesExecutor decision framework |
| 015 | Worker queue segregation mirroring AutoSys machine groups |
| 016 | Autoscaling design for bursty batch workloads |
| 017 | Per-task resource requests/limits (`executor_config`) |
| 018 | Node affinity/taints for specialized jobs |
| 019 | KEDA-based autoscaling |
| 020 | Hybrid executor strategy (Celery + KubernetesPodOperator for outliers) |
| 021 | Legacy-server access via SSHOperator |
| 022 | Worker capacity-planning methodology |
| 023 | Zombie-task detection and handling |
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
| 033 | Workspace/Deployment boundary design (from AutoSys application/sub_application) |
| 034 | RBAC role design mirrored from EEM entitlements |
| 035 | Secrets-backend selection |
| 036 | Connection scoping and least privilege |
| 037 | SSO/OAuth integration design |
| 038 | Network isolation and VPC peering (Hybrid) |
| 039 | Audit-log design for access and actions |
| 040 | Federated vs. centralized self-service design |
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
| 069 | What Astro provides for free vs. what still needs explicit design |
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
| 081 | SAP/ERP batch-integration patterns |
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

**Exit criteria**: All 100 files exist under `skills/astro-design-best-practices/reference/`, each Critic-verified and Human-signed-off, `SKILL.md`'s index updated.

**On individual task files**: only Task 001 is written out in full right now, as the confirmed template (`tasks/001-dag-factory-pattern-for-large-estates.md`). The remaining 99 follow the identical shape (Description grounded in the AutoSys-side problem it solves + why its priority, "How this task gets built" naming the cluster's relevant axes from the matrix below, Deliverables, Acceptance Criteria mirroring `AGENTS.md`'s Definition of Done, Dependencies on `SETUP-4`/`SETUP-6`) — generated just before each is picked up, not all 100 at once up front, per the project's own "don't one-shot" principle.

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

---

## Task Tracker

Status legend: `NOT STARTED` | `IN PROGRESS` | `IN REVIEW (Critic)` | `IN SIGN-OFF` | `MERGED` | `BLOCKED`

| # | Task | Status | Owner | Notes |
|---|------|--------|-------|-------|
| SETUP-1 | Repo Scaffolding + Agent Pipeline Definitions | MERGED | — | |
| SETUP-2 | Import Mentor-Authored Companion Skills | MERGED | — | |
| SETUP-3 | Axis Relevance Matrix | MERGED | — | Cluster-level (13 rows) |
| SETUP-4 | Seed Source List | NOT STARTED | — | Blocks all 100 topic tasks |
| SETUP-5 | Tier-3 Partner Material Ingestion Path | NOT STARTED | — | |
| SETUP-6 | Skill Scaffold | NOT STARTED | — | Blocks all 100 topic tasks |
| 001 | DAG-factory pattern for large estates | NOT STARTED | — | Task file written in full as the confirmed template |
| 002-100 | Remaining topic tasks | NOT STARTED | — | Task files generated per-cluster as work starts, following 001's shape |

---

## Summary

- **100 topic tasks** across **13 clusters** — this is the entire scope of the project
- **6 setup tasks** (`SETUP-1..6`) — prerequisites, not counted among the 100
- **4 companion skills imported** as-is from the mentor's existing work — unchanged, not regenerated by this pipeline
- Every topic task runs the identical 4-stage pipeline: `AGENTS.md` is the source of truth for *how*; this file is the source of truth for *what, in what order*

## Explicitly out of scope for this project

**Consuming this knowledge base — wiring it into Shinro's assessment-report generation, packaging it behind an MCP server, or any other downstream integration — is not a phase here.** This project's job ends at producing 100 sourced, Critic-verified, human-signed-off files. When Shinro (or anything else) is ready to consume them, that's separate work in the consuming project's own repo — for Shinro specifically, it would extend `skill_loader.py` the same way `autosys-astronomer-expert` already works, but that decision and its implementation belong to whoever owns that integration, later, not to this roadmap.

## Source Documents

- `AGENTS.md` — pipeline definition, design principles, agent role files in `.agents/`
- `research/` — permanent per-topic fact-sheets, populated as Phase 1/2 tasks complete
