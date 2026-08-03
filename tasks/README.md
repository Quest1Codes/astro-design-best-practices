# Astro Migration Skills — Task List

### Roadmap for building the `astro-design-best-practices` knowledge base (100 topics) — plus the 4 imported companion skills — via the Researcher → Generator → Critic → Human Sign-off pipeline defined in `AGENTS.md`

---

## Overview

This folder tracks the roadmap in the same convention as other Quest1 projects: numbered task files with Description/Deliverables/Acceptance Criteria/Dependencies, a phase table, and a task tracker. Unlike a software project, most tasks here are **content-pipeline runs** (execute `AGENTS.md`'s 4-stage pipeline for one topic, producing one `reference/*.md` file) rather than code changes — but they follow the same discipline: no task starts before its dependencies are `MERGED`, and every task has a binary-checkable Acceptance Criteria list.

**Scope of this project**: build the knowledge base itself — 100 topic files, organized into 13 clusters, that together let Quest1 credibly claim a production-grade "Astro Design Best Practices given source AutoSys" skill. This project does **not** include wiring the result into Shinro's assessment-report generation — that's a downstream consumption question for later, noted at the bottom of this file but explicitly not a phase here. Building 100 sourced, verified reference files is the whole job.

Tasks are grouped into phases. Phases 0-1 are foundational and mostly sequential. Phase 2 (the 100 topic tasks) is parallel-safe once Phase 0-1 are done, since each targets an independent file. Phase 3 (axis branches) depends only on its parent Phase 2 task.

---

## Phase 0 — Repo Foundation

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 001 | [Repo Scaffolding + Agent Pipeline Definitions](001-repo-scaffolding-and-agent-pipeline.md) | P0 | None | DONE |
| 002 | [Import Mentor-Authored Companion Skills](002-import-companion-skills.md) | P0 | 001 | DONE |
| 003 | [Axis Relevance Matrix](003-axis-relevance-matrix.md) | P0 | 001 | DONE (this file, below) |
| 004 | [Seed Source List](004-seed-source-list.md) (tier 1/2 URLs per cluster) | P0 | 003 | NOT STARTED |
| 005 | Tier-3 Partner Material Ingestion Path | P1 | 003 | NOT STARTED |

---

## Phase 1 — `astro-design-best-practices` Skill Scaffold

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 006 | Create `skills/astro-design-best-practices/SKILL.md` manifest + the 13 `reference/{cluster}/` subdirectories (empty Reference Files index, filled in as Phase 2 tasks complete) | P0 | 003 | NOT STARTED |

**Note on structure**: with 100 files, a flat `reference/` folder is unwieldy. Files are organized as `reference/{cluster-slug}/{topic-slug}.md` — 13 cluster subdirectories, matching the 13 rows in the Axis Relevance Matrix below.

---

## Phase 2 — The 100 Topic Files (one task each, baseline/axis-free content)

Each task = one full run of the 4-stage pipeline for that topic's **default** guidance (axis branches are Phase 3). All parallel-safe once 004 and 006 are `MERGED`. Priority is set per cluster (see Axis Relevance Matrix notes for rationale), not individually per topic.

### Cluster 1 — Scheduler & DAG Design (P0) — `reference/scheduler-and-dag/`

| # | Topic |
|---|---|
| 007 | DAG-factory pattern for large estates |
| 008 | DAG versioning and change-management strategy |
| 009 | Scheduler HA and leader election |
| 010 | DAG parsing performance budget |
| 011 | TaskGroups vs. separate DAGs — decision criteria |
| 012 | Cross-DAG dependencies: Datasets vs. TriggerDagRunOperator vs. ExternalTaskSensor |
| 013 | Dynamic task mapping design (replacing AutoSys global-variable job cloning) |
| 014 | Custom Timetable design for AutoSys-calendar equivalents |
| 015 | DAG-level SLA and catchup/backfill policy |
| 016 | Idempotency and retry design for translated tasks |
| 017 | Concurrency controls — pools and `max_active_runs` |
| 018 | Naming/tagging conventions at scale |
| 019 | One-off and ad-hoc job design |

### Cluster 2 — Executor & Worker Architecture (P0) — `reference/executor-and-worker/`

| # | Topic |
|---|---|
| 020 | CeleryExecutor vs. KubernetesExecutor decision framework |
| 021 | Worker queue segregation mirroring AutoSys machine groups |
| 022 | Autoscaling design for bursty batch workloads |
| 023 | Per-task resource requests/limits (`executor_config`) |
| 024 | Node affinity/taints for specialized jobs |
| 025 | KEDA-based autoscaling |
| 026 | Hybrid executor strategy (Celery + KubernetesPodOperator for outliers) |
| 027 | Legacy-server access via SSHOperator |
| 028 | Worker capacity-planning methodology |
| 029 | Zombie-task detection and handling |
| 030 | GPU/specialized-compute worker design |

### Cluster 3 — Metadata DB & State Design (P1) — `reference/metadata-db-and-state/`

| # | Topic |
|---|---|
| 031 | Postgres sizing and instance-class selection |
| 032 | Connection pooling with PgBouncer |
| 033 | Metadata retention and cleanup policy |
| 034 | Backup and point-in-time recovery |
| 035 | Read-replica strategy for reporting |
| 036 | DB migration strategy across Airflow upgrades |
| 037 | Metadata DB growth at scale (thousands of DAGs) |
| 038 | Custom XCom backend design |

### Cluster 4 — Security & Multi-Tenancy Design (P0) — `reference/security-and-multitenancy/`

| # | Topic |
|---|---|
| 039 | Workspace/Deployment boundary design (from AutoSys application/sub_application) |
| 040 | RBAC role design mirrored from EEM entitlements |
| 041 | Secrets-backend selection |
| 042 | Connection scoping and least privilege |
| 043 | SSO/OAuth integration design |
| 044 | Network isolation and VPC peering (Hybrid) |
| 045 | Audit-log design for access and actions |
| 046 | Federated vs. centralized self-service design |
| 047 | API token / service-account lifecycle management |
| 048 | Encryption at rest and in transit design |

### Cluster 5 — Observability & Alerting Design (P1) — `reference/observability-and-alerting/`

| # | Topic |
|---|---|
| 049 | `on_failure_callback` design patterns |
| 050 | Astronomer Alerts routing and escalation |
| 051 | Alert-fatigue and deduplication strategy |
| 052 | OpenLineage / data-lineage integration |
| 053 | Astronomer Observe integration |
| 054 | Metrics export (Prometheus/Datadog) |
| 055 | Log architecture — remote storage and retention |
| 056 | SLA-miss detection and escalation (replacing AutoSys alarms) |
| 057 | Incident-ticket automation (replacing Service Desk) |
| 058 | Dashboard design for stakeholder visibility (replacing WCC reporting) |

### Cluster 6 — CI/CD & Environment Topology (P0) — `reference/cicd-and-environment-topology/`

| # | Topic |
|---|---|
| 059 | `astro` CLI deploy pipeline design |
| 060 | Dev/staging/prod Deployment topology |
| 061 | DAG testing and parse gates before merge |
| 062 | Branching strategy for DAG code |
| 063 | Environment promotion process |
| 064 | GitOps design for DAG deployment |
| 065 | Rollback strategy design |
| 066 | Multi-region Deployment topology at scale |
| 067 | Feature-flagging for gradual DAG rollout |
| 068 | Local development environment standards (`astro dev`) |

### Cluster 7 — Config & Secrets Design (P1) — `reference/config-and-secrets/`

| # | Topic |
|---|---|
| 069 | Variables vs. Connections vs. secrets-backend decision framework |
| 070 | Per-environment variable scoping |
| 071 | Global-variable-sprawl remediation (from AutoSys `%%VAR%%` patterns) |
| 072 | Config-as-code for DAG-factory inputs |
| 073 | Secret rotation strategy |
| 074 | Environment-specific connection management |

### Cluster 8 — HA & DR Design (P1) — `reference/ha-and-dr/`

| # | Topic |
|---|---|
| 075 | What Astro provides for free vs. what still needs explicit design |
| 076 | Multi-region DR strategy |
| 077 | Backup cadence and RTO/RPO design |
| 078 | DR runbook design (replacing dual-Event-Server/Shadow-Scheduler runbooks) |
| 079 | Chaos/failure-testing strategy for the new platform |

### Cluster 9 — Regulatory & Compliance Design (P0) — `reference/regulatory-and-compliance/`

| # | Topic |
|---|---|
| 080 | Audit-trail immutability design |
| 081 | Data retention/erasure lifecycle design |
| 082 | Data lineage for regulatory reporting |
| 083 | Access-control granularity for regulated data |
| 084 | Vertical overlay: financial services (SOX/Basel/AML) |
| 085 | Vertical overlay: healthcare (HIPAA) |
| 086 | Vertical overlay: government/public sector (FedRAMP/data residency) |

### Cluster 10 — Integration & Enterprise Mesh Design (P1) — `reference/integration-and-enterprise-mesh/`

| # | Topic |
|---|---|
| 087 | SAP/ERP batch-integration patterns |
| 088 | EDI/file-transfer integration patterns |
| 089 | Ticketing/ITSM integration design (ServiceNow/PagerDuty) |
| 090 | SIEM export integration design |
| 091 | BI/reporting-layer integration |
| 092 | Mainframe-boundary Astro-side architecture (companion to the imported mainframe-boundary skill) |

### Cluster 11 — Migration Execution & Coexistence Architecture (P1) — `reference/migration-execution-and-coexistence/`

| # | Topic |
|---|---|
| 093 | Dual-run/shadow-DAG architecture during coexistence |
| 094 | Data-reconciliation architecture for parity verification |
| 095 | Cutover architecture per box |
| 096 | Rollback architecture during cutover |

### Cluster 12 — Cost & Capacity Governance (P2) — `reference/cost-and-capacity-governance/`

| # | Topic |
|---|---|
| 097 | Cost allocation/chargeback design across Workspaces/Deployments |
| 098 | Capacity planning from job-count and schedule-density |
| 099 | Autoscaling cost-optimization patterns |
| 100 | Idle-resource reclamation design |

### Cluster 13 — Governance & Operating Model (P2) — `reference/governance-and-operating-model/`

| # | Topic |
|---|---|
| 101 | Centralized vs. federated operating model design |
| 102 | DAG-ownership and support-model design (on-call, runbooks) |
| 103 | Legacy-job deprecation process during migration |
| 104 | Documentation-as-code strategy |
| 105 | Training/enablement design for AutoSys ops staff |
| 106 | Vendor lock-in and exit-strategy design |

**Exit criteria**: All 100 files exist under `skills/astro-design-best-practices/reference/`, each Critic-verified and Human-signed-off, `SKILL.md`'s index updated.

---

## Phase 3 — Axis-Branch Layering

One follow-on task per **H-rated cell** in the Axis Relevance Matrix below (M-rated cells are usually a short callout inside the Phase 2 baseline task itself, not a separate task; L-rated cells just need "checked, no branch needed" recorded). Numbered `{parent}a`, `{parent}b`, ... as started, mirroring the PACT `003a`/`004b` convention — not enumerated individually here (100 topics × several H cells each would be premature to schedule before the baselines exist). Do not batch multiple axes into one task.

**Dependency rule**: `NNNx` depends only on `NNN` being `MERGED`.

---

## Axis Relevance Matrix (by cluster)

Rated at the **cluster** level, not per-topic — with 100 topics, a topic-level matrix would be 100×7 and premature before baselines exist. Each topic inherits its cluster's ratings as a starting point; refine per-topic during that topic's own Researcher brief if it turns out to differ from its cluster's default. **H** = real decision table needed, **M** = short callout, **L** = "checked, no branch needed."

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

Every axis has at least one cluster where it's the clear "home" (e.g. org model → Governance & Operating Model / Security; migration-temporal → Migration Execution & Coexistence; integration-surface → Observability/Integration clusters) — confirms none of the 7 axes were forced in without a real load-bearing home.

---

## Task Tracker

Status legend: `NOT STARTED` | `IN PROGRESS` | `IN REVIEW (Critic)` | `IN SIGN-OFF` | `MERGED` | `BLOCKED`

| # | Task | Phase | Status | Owner | Notes |
|---|------|-------|--------|-------|-------|
| 001 | Repo Scaffolding + Agent Pipeline Definitions | 0 | MERGED | — | |
| 002 | Import Mentor-Authored Companion Skills | 0 | MERGED | — | |
| 003 | Axis Relevance Matrix | 0 | MERGED | — | Now cluster-level (13 rows), superseding the earlier 9-mega-topic draft |
| 004 | Seed Source List | 0 | NOT STARTED | — | Blocks all Phase 2 tasks |
| 005 | Tier-3 Partner Material Ingestion Path | 0 | NOT STARTED | — | |
| 006 | `astro-design-best-practices` SKILL.md + 13 cluster subdirectories | 1 | NOT STARTED | — | |
| 007-106 | 100 Phase 2 topic tasks | 2 | NOT STARTED | — | Parallel-safe once 004, 006 merged; see cluster tables above |
| Phase 3 | Axis-branch follow-ons | 3 | NOT STARTED | — | Scheduled per-cluster as Phase 2 baselines complete |

---

## Summary

- **100 topic tasks** (Phase 2), across **13 clusters**, each producing one sourced, Critic-verified, human-signed-off reference file
- **4 companion skills imported** as-is from the mentor's existing work — unchanged, not regenerated by this pipeline
- **1 new skill** (`astro-design-best-practices`) is what Phases 1-3 build, organized as `reference/{cluster}/{topic}.md`
- Every topic task runs the same 4-stage pipeline: `AGENTS.md` is the single source of truth for *how*; this file is the source of truth for *what, in what order*

## Explicitly out of scope for this project

**Wiring this content into Shinro's assessment-report generation is not a phase here.** That's a downstream consumption decision for later, once the knowledge base itself is built and verified — this project's job is the 100 files, not their integration into any one consumer. When that work happens, it belongs in Shinro's own repo (extending `skill_loader.py` the way `autosys-astronomer-expert` already works), not as a phase of this roadmap.

## Source Documents

- `AGENTS.md` — pipeline definition, design principles, agent role files in `.agents/`
- `research/` — permanent per-topic fact-sheets, populated as Phase 2/3 tasks complete
