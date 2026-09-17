# Multi-Instance Topology Mapping: $AUTOSERV/$AUTOUSER → Astro Workspace/Deployment

AutoSys's multi-instance model provides environment isolation through per-instance identifiers. Each install is identified by a unique 3-character ID — the default being `ACE`, with common practice using `DEV`, `UAT`, `PRD`, etc. Each instance has its own `$AUTOSERV` environment variable (the instance name), its own `$AUTOUSER` directory (containing instance-specific configuration), and its own independent Event Server (database) and Scheduler process [B1].

This is the fundamental isolation unit in AutoSys. When migrating to Astro, this maps cleanly to the Astro hierarchy.

## Topology Mapping

{syn: AutoSys instance → Astro Deployment (same isolation level); AutoSys $AUTOSERV → Astro Deployment name}

| AutoSys Concept | Astro Equivalent | Notes |
|---|---|---|
| **Instance** (e.g., `PRD`) | **Deployment** | One-to-one isolation: separate scheduler, separate metadata DB, separate workers [B2]. |
| **`$AUTOSERV`** | Deployment name / Deployment ID | The Deployment name in Astro uniquely identifies the Airflow environment. |
| **`$AUTOUSER` directory** | Deployment's `Dockerfile` + `requirements.txt` | The Deployment's image definition controls environment configuration [B2]. |
| **Event Server** (instance DB) | Airflow Metadata DB (per-Deployment, managed by Astro) | Each Deployment has its own isolated metadata DB; there is no cross-Deployment shared state [B2]. |
| **Instance Scheduler** (`PRD_SCH`) | Deployment Scheduler | Each Deployment runs its own scheduler pod. |
| **Instance-level security (CA EEM)** | Astro RBAC at Workspace/Deployment level | Access policies are set per Workspace. **Correction**: an earlier draft of this row described Deployment-level access as purely inheriting from Workspace RBAC — that oversimplifies it. Astro's RBAC is hierarchical and *additive*: a Deployment Admin role and custom Deployment roles are assignable independently of Workspace role, and (on Runtime 3.1-12+) DAG-level roles add a further, independently-assignable layer beneath Deployment. A user's effective access is the union of their Workspace role plus any Deployment- and DAG-scoped roles, not a single inherited value [B3]. |

## Environment Topology Decision

| AutoSys Pattern | Recommended Astro Pattern |
|---|---|
| **3 instances** (DEV, UAT, PRD) with same job set | **3 Deployments** within the same Workspace (if same team) or across separate Workspaces (if different teams own each env) [B2]. |
| **Multiple `$AUTOSERV` per business domain** | **One Workspace per domain**, with one Deployment per environment (e.g., `finance/finance-dev`, `finance/finance-prod`). |
| **Single production instance** (`PRD`) hosting all jobs | **Multiple Deployments** segregated by domain/cost center within a shared Workspace — avoid a monolith Deployment for all production jobs [B2]. |

## Sources

[B1] Broadcom / CA AutoSys Workload Automation Documentation — Instance model, `$AUTOSERV`, `$AUTOUSER`, per-instance Event Server and Scheduler architecture (accessed 2026-08-11)
[B2] Astronomer Docs — Astro architecture, access control architecture (Organization/Workspace/Deployment hierarchy and RBAC): https://www.astronomer.io/docs/astro/astro-architecture#access-control-architecture (tier 1, added on doc-verification review)
[B3] Astronomer Docs — Astro user permissions reference (hierarchical, additive RBAC; Deployment Admin and custom Deployment roles; Dag-level roles on Runtime 3.1-12+): https://www.astronomer.io/docs/astro/user-permissions (tier 1, added on doc-verification review — corrects the pure-inheritance framing above)
