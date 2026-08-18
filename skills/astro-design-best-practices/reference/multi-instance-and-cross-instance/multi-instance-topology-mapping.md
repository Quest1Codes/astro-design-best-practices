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
| **Instance-level security (CA EEM)** | Astro RBAC at Workspace/Deployment level | Access policies are set per Workspace; Deployment-level access inherits from Workspace RBAC [B2]. |

## Environment Topology Decision

| AutoSys Pattern | Recommended Astro Pattern |
|---|---|
| **3 instances** (DEV, UAT, PRD) with same job set | **3 Deployments** within the same Workspace (if same team) or across separate Workspaces (if different teams own each env) [B2]. |
| **Multiple `$AUTOSERV` per business domain** | **One Workspace per domain**, with one Deployment per environment (e.g., `finance/finance-dev`, `finance/finance-prod`). |
| **Single production instance** (`PRD`) hosting all jobs | **Multiple Deployments** segregated by domain/cost center within a shared Workspace — avoid a monolith Deployment for all production jobs [B2]. |

## Sources

[B1] Broadcom / CA AutoSys Workload Automation Documentation — Instance model, `$AUTOSERV`, `$AUTOUSER`, per-instance Event Server and Scheduler architecture (accessed 2026-08-11)
[B2] Astronomer Docs — Organization/Workspace/Deployment hierarchy, per-Deployment isolation (scheduler, metadata DB, image), and RBAC (accessed 2026-08-11)
