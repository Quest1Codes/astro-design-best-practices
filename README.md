# Astro Design Best Practices

> A production-grade knowledge base for migrating **CA AutoSys Workload Automation** to **Astronomer (Astro) & Apache Airflow** — 126 architecture reference guides across 19 technical domains, built and verified by a multi-agent research pipeline.

---

## At a Glance

| Metric | Value |
|---|---|
| **Reference guides shipped** | 126 across 19 clusters |
| **Migration skills included** | 5 (1 core + 4 topology companions) |
| **Agentic pipeline stages** | Researcher → Generator → Critic → Ship |
| **Source verification** | Every claim traced to Broadcom, Astronomer, or Apache Airflow docs |

---

## What This Repo Contains

### 🧠 Agent Skills (`.agents/skills/`)

Five specialized skill packages that AI coding agents (or human engineers) can load for AutoSys-to-Airflow migration work:

| Skill | Purpose |
|---|---|
| **`migrating-autosys-to-astronomer/`** | Core migration workflow — JIL inventory, job classification, condition/calendar translation, box-by-box cutover |
| **`migrating-autosys-k8s-to-astronomer/`** | Companion for estates already running on Kubernetes |
| **`migrating-autosys-mainframe-boundary-to-astro/`** | Companion for jobs touching mainframe data (MFT / Connect:Direct / JCL) |
| **`migrating-autosys-onprem-distributed-to-astro-cloud/`** | Companion for large on-prem Unix/Windows agent fleets |
| **`astro-design-best-practices/`** | **Target-side architecture design** — the 126-file reference library (this project's main output) |

### 📚 Architecture Reference Library (`reference/`)

126 detailed, critic-verified guides organized into 19 clusters:

<details>
<summary><b>Cluster 1 — Scheduler & DAG Design</b> (13 files)</summary>

- DAG factory pattern for large estates
- Box-job hierarchy → TaskGroups vs. separate DAGs
- Cross-DAG dependencies (Datasets vs. TriggerDagRunOperator vs. ExternalTaskSensor)
- Custom timetable design for AutoSys calendars
- Concurrency controls, pools, and max active runs
- DAG parsing performance budget
- Dynamic task mapping design
- Idempotency and retry design
- DAG-level SLA and catchup/backfill policy
- DAG versioning and change management
- Naming and tagging conventions at scale
- One-off and ad-hoc job design
- Scheduler HA and leader election
</details>

<details>
<summary><b>Cluster 2 — Executor & Worker Architecture</b> (7 files)</summary>

- CeleryExecutor vs. KubernetesExecutor decision framework
- Worker queue segregation mirroring machine groups
- Hybrid executor strategy
- Per-task resource requests and limits
- Node affinity and taints for specialized jobs
- Autoscaling design for bursty batch workloads
- KEDA-based autoscaling
</details>

<details>
<summary><b>Cluster 3 — Metadata DB & State</b> (8 files)</summary>

- PostgreSQL sizing and instance class selection
- Connection pooling with PgBouncer
- Metadata DB growth at scale
- Metadata retention and cleanup policy
- Custom XCom backend design
- Read replica strategy for reporting
- Backup and point-in-time recovery
- DB migration strategy across Airflow upgrades
</details>

<details>
<summary><b>Cluster 4 — Security & Multi-Tenancy</b> (10 files)</summary>

- Workspace and Deployment boundary design
- RBAC role shape design (mirrored from EEM entitlements)
- SSO / OAuth integration design
- Secrets backend selection
- Connection scoping and least privilege
- API token & service account lifecycle management
- Encryption at rest and in transit
- Network isolation and VPC peering
- Audit log design for access and actions
- Federated vs. centralized self-service design
</details>

<details>
<summary><b>Cluster 5 — CI/CD & Environment Topology</b> (10 files)</summary>

- Dev / staging / prod Deployment topology
- Branching strategy for DAG code
- Astro CLI deploy pipeline design
- DAG testing and parse gates before merge
- Environment promotion process
- Rollback strategy design
- GitOps design for DAG deployment
- Feature flagging for gradual DAG rollout
- Local development environment standards
- Multi-region deployment topology at scale
</details>

<details>
<summary><b>Cluster 6 — Config & Secrets</b> (6 files)</summary>

- Variables vs. Connections vs. Secrets Backend decision framework
- Config-as-code for DAG factory inputs
- Per-environment variable scoping
- Environment-specific connection management
- Secret rotation strategy
- Global variable sprawl remediation
</details>

<details>
<summary><b>Cluster 7 — Observability & Alerting</b> (10 files)</summary>

- `on_failure_callback` design patterns
- Astronomer Alerts routing and escalation
- Astronomer Observe integration
- SLA miss detection and escalation
- Metrics export (Prometheus / Datadog)
- Dashboard design for stakeholder visibility
- Log architecture (remote storage and retention)
- Alert fatigue and deduplication strategy
- Incident ticket automation
- OpenLineage data lineage integration
</details>

<details>
<summary><b>Cluster 8 — HA & Disaster Recovery</b> (5 files)</summary>

- Scheduler HA — what Astro provides vs. what you design
- Multi-region DR strategy
- Backup cadence and RTO/RPO design
- DR runbook design
- Chaos and failure testing strategy
</details>

<details>
<summary><b>Cluster 9 — Regulatory & Compliance</b> (7 files)</summary>

- Access control granularity for regulated data
- Audit trail immutability design
- Data lineage for regulatory reporting
- Data retention and erasure lifecycle design
- Vertical: Financial Services (SOX / Basel / AML)
- Vertical: Healthcare (HIPAA)
- Vertical: Government (FedRAMP / data residency)
</details>

<details>
<summary><b>Cluster 10 — Integration & Enterprise Mesh</b> (6 files)</summary>

- ERP batch integration patterns
- Mainframe boundary (Astro-side architecture)
- Ticketing and ITSM integration design
- EDI and file-transfer integration patterns
- SIEM export integration design
- BI and reporting layer integration
</details>

<details>
<summary><b>Cluster 11 — Migration Execution & Coexistence</b> (4 files)</summary>

- Dual-run / shadow DAG architecture
- Cutover architecture per box
- Rollback architecture during cutover
- Data reconciliation architecture for parity verification
</details>

<details>
<summary><b>Cluster 12 — Cost & Capacity Governance</b> (4 files)</summary>

- Capacity planning from job count and schedule density
- Autoscaling cost optimization patterns
- Cost allocation and chargeback design
- Idle resource reclamation design
</details>

<details>
<summary><b>Cluster 13 — Governance & Operating Model</b> (6 files)</summary>

- Centralized vs. federated operating model
- DAG ownership and support model design
- Legacy job deprecation process
- Training enablement for AutoSys ops staff
- Documentation-as-code strategy
- Vendor lock-in and exit strategy design
</details>

<details>
<summary><b>Cluster 14 — Multi-Instance & Cross-Instance</b> (5 files)</summary>

- Multi-instance topology mapping
- Cross-instance dependencies → Dataset / REST patterns
- CA CCI cross-instance → cross-Deployment triggering
- Job classification (group/application) → tagging & namespacing
- Multi-timezone (`autotimezone`) → Pendulum design
</details>

<details>
<summary><b>Cluster 15 — Machine Load & Virtual Resources</b> (4 files)</summary>

- `max_load` / `job_load` → Airflow Pools sizing
- Virtual resources → Airflow Pools and DAG concurrency
- Virtual machine groups → executor queue design
- `QUE_WAIT` → queued-state observability
</details>

<details>
<summary><b>Cluster 16 — Native Security & Credentials</b> (4 files)</summary>

- CA EEM → Astro RBAC / IdP provider design
- `autosys_secure` bootstrap → Astro RBAC bootstrap
- PAM credential vaulting → Astro Secrets Backend
- RSA Identity Governance access review → periodic review design
</details>

<details>
<summary><b>Cluster 17 — Reporting & Forecasting</b> (3 files)</summary>

- Forecast feature capability gap design (explicit gap)
- `autorep` → Airflow metadata-DB reporting
- Cross-instance console → multi-Deployment dashboard design
</details>

<details>
<summary><b>Cluster 18 — Native ERP & Web-Service Agents</b> (5 files)</summary>

- SAP Application Job → Airflow SAP provider / `SAPRfcOperator`
- PeopleSoft agent → custom Airflow operator
- Oracle E-Business Suite agent → custom operator via `OracleHook`
- `job_type: WS` (SOAP/REST) → `HttpOperator` design
- AEWS REST API → Airflow REST API parity
</details>

<details>
<summary><b>Cluster 19 — Container-Native & Legacy Precision</b> (9 files)</summary>

- K8s container-agent → `KubernetesPodOperator`
- Multi-container pod exec parity (explicit gap)
- Legacy machine-type inventory cleanup (`n`/`l`/`L`/`r` → `a`-type)
- Client surface inventory (`jil`/`autorep`/`sendevent`/WCC/AEWS) → Astro parity mapping
- Event Server RDBMS dialect → metadata-DB migration source
- Native DB job type → SQL operator design
- `HAPollInterval` heartbeat → Airflow scheduler HA design
- `EP_ROLLOVER` alarm → Astro failover alerting
- Job history / audit trail → metadata-DB migration design
</details>

### 🤖 Agentic Pipeline (`.agents/`)

Every reference file was built through a 4-stage verification pipeline:

```
Researcher  →  Generator  →  Critic  →  Ship
   (facts)      (draft)     (verify)   (publish)
```

| Stage | Agent File | What It Does |
|---|---|---|
| **Researcher** | `.agents/researcher.md` | Gathers citable facts from Broadcom, Astronomer, and Apache Airflow docs |
| **Generator** | `.agents/generator.md` | Drafts the reference file using only verified facts with provenance markers (`[F#]`, `{syn: ...}`) |
| **Critic** | `.agents/critic.md` | Verifies citations, checks for hallucinated facts or missing provenance |
| **Sign-off** | `.agents/signoff-checklist.md` | Final human review checklist |

### 📋 Task Tracker (`tasks/`)

- [`tasks/README.md`](tasks/README.md) — Full 130-topic roadmap, the Axis Relevance Matrix, and phased build order
- `tasks/001-*.md` — Sample task file (template for all 130 topics)
- `tasks/SETUP-*.md` — Infrastructure setup tasks (repo scaffolding, skill imports, source lists)

### 🔬 Pipeline Work Artifacts (`.work/`)

Raw outputs from the agentic pipeline for each topic — researcher notes, generator drafts, and critic reports. Useful for auditing how a specific reference file was produced.

---

## Repository Structure

```
astro-design-best-practices/
├── README.md                          ← You are here
├── AGENTS.md                          ← Pipeline design, principles, how to run each stage
├── tasks/
│   └── README.md                      ← Full 130-topic roadmap & axis relevance matrix
├── .agents/
│   ├── researcher.md                  ← Stage 1: Research agent instructions
│   ├── generator.md                   ← Stage 2: Generator agent instructions
│   ├── critic.md                      ← Stage 3: Critic agent instructions
│   ├── signoff-checklist.md           ← Stage 4: Human sign-off checklist
│   └── skills/
│       ├── astro-design-best-practices/
│       │   ├── SKILL.md               ← Indexed catalog of all 126 reference guides
│       │   └── reference/             ← 19 cluster directories, 126 .md files
│       ├── migrating-autosys-to-astronomer/
│       │   ├── SKILL.md               ← Core JIL migration workflow
│       │   ├── reference/             ← mapping.md, conditions, calendars, etc.
│       │   └── scripts/               ← jil_inventory.py (JIL parser)
│       ├── migrating-autosys-k8s-to-astronomer/
│       ├── migrating-autosys-mainframe-boundary-to-astro/
│       └── migrating-autosys-onprem-distributed-to-astro-cloud/
└── .work/                             ← Pipeline artifacts (researcher/generator/critic outputs)
```

---

## Where to Start

| If you want to... | Go to... |
|---|---|
| **Understand the migration workflow** | [`.agents/skills/migrating-autosys-to-astronomer/SKILL.md`](.agents/skills/migrating-autosys-to-astronomer/SKILL.md) |
| **Browse all 126 architecture guides** | [`.agents/skills/astro-design-best-practices/SKILL.md`](.agents/skills/astro-design-best-practices/SKILL.md) |
| **See how a JIL construct maps to Airflow** | [`.agents/skills/migrating-autosys-to-astronomer/reference/mapping.md`](.agents/skills/migrating-autosys-to-astronomer/reference/mapping.md) |
| **Parse a JIL export automatically** | [`python3 .agents/skills/migrating-autosys-to-astronomer/scripts/jil_inventory.py`](.agents/skills/migrating-autosys-to-astronomer/scripts/jil_inventory.py) |
| **Understand the agentic pipeline** | [`AGENTS.md`](AGENTS.md) |
| **See the full 130-topic roadmap** | [`tasks/README.md`](tasks/README.md) |

---

## Scope

**In scope**: Producing a verified, sourced knowledge base for AutoSys → Astro/Airflow migrations.

**Out of scope**: Consuming this knowledge base (e.g., wiring into report generation, an MCP server, or any downstream tooling). See [`tasks/README.md`](tasks/README.md) for details.
