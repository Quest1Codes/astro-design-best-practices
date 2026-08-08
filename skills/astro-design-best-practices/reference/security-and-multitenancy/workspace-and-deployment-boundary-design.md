# Workspace and Deployment Boundary Design

AutoSys classified jobs using two orthogonal JIL attributes: `group` (the owning team / functional domain) and `application` (the cross-cutting business application). Neither maps directly to a folder hierarchy or a security boundary — they were classification tags, not isolation containers. Astro introduces a proper three-level hierarchy that replaces this model with genuine security and resource isolation.

## Astro hierarchy

```
Organization
  └── Workspace  (team / business unit boundary)
        └── Deployment  (Airflow environment — scheduler, workers, metadata DB)
```

| Level | Isolation provided | Analogy to AutoSys |
|---|---|---|
| **Organization** | Billing, top-level SSO, org-wide audit logs | The AutoSys installation/server estate |
| **Workspace** | RBAC scope, resource allocation boundary, separate audit trails | AutoSys `group` + `application` — the ownership dimension |
| **Deployment** | Isolated Kubernetes namespace (standard) or dedicated cluster; own metadata DB, own scheduler, own workers | The AutoSys machine/agent set running a group's jobs |

## The primary security design question: Deployment boundary placement

| Scenario | Recommendation | Rationale |
|---|---|---|
| Different teams with different code dependencies or security domains | One Deployment per team | Blast radius isolation — one team's buggy DAG cannot corrupt another's metadata DB [B4] |
| Shared infrastructure, low sensitivity | Multiple teams in one Deployment, using DAG-level RBAC (Astro Runtime 3.1-12+) | Reduces Deployment count but provides only logical separation [B5][B6] |
| High compliance or data residency requirements | Dedicated cluster per Workspace | Physical network/infra isolation; required for VPC peering, PrivateLink [B2][B3] |

> **Astronomer's explicit recommendation**: avoid sharing a single Airflow instance across teams with different security or blast-radius requirements; shared deployments create noisy-neighbor risk and allow privileged DAG code to access the shared metadata DB [B4][B5].

## AutoSys `group` / `application` → Astro mapping

| AutoSys attribute | Astro equivalent | Notes |
|---|---|---|
| `group` (team ownership) | Workspace | Each team/BU gets its own Workspace |
| `application` (cross-cutting business app) | Tag on Deployments or DAG tags | Applications that span teams are represented by tags, not additional hierarchy levels |

## Org model dispatch (Axis D — H rating)

| Org model | Workspace strategy |
|---|---|
| **One AutoSys instance per BU** | One Workspace per BU; own Deployments within each |
| **One shared AutoSys instance enterprise-wide** | Start with Workspaces per major team cluster; decide on Deployment-per-team vs. shared-Deployment-with-DAG-RBAC per team's sensitivity |
| **Federated self-service** | Platform team owns Workspace templates; teams provision own Deployments via CI/CD |

## Authorized Workspaces

Use "Authorized Workspaces" to restrict which clusters a Workspace can deploy to [B11]. This prevents teams from accidentally (or deliberately) deploying to a production-dedicated cluster.

## Sources

[B2, B3] Astronomer Docs — Dedicated clusters and private connectivity: https://www.astronomer.io/docs/astro/create-dedicated-cluster (accessed 2026-08-08)
[B4, B5] Astronomer Docs — Multi-tenancy in Airflow: https://www.astronomer.io/docs/learn/airflow-multi-tenancy (accessed 2026-08-08)
[B6] Astronomer Docs — DAG-level RBAC: https://www.astronomer.io/docs/astro/dag-level-permissions (accessed 2026-08-08)
[B11] Astronomer Docs — Authorized Workspaces: https://www.astronomer.io/docs/astro/authorize-workspaces (accessed 2026-08-08)
