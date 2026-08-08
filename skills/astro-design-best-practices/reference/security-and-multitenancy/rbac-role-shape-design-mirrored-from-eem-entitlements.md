# RBAC Role-Shape Design Mirrored from EEM Entitlements

AutoSys's EEM (Enterprise Event Manager) managed access via entitlements — typically mapping to job groups or applications. Astro's RBAC model is hierarchical and additive: roles at Organization level cascade down, and Workspace/Deployment roles provide scoped, independent control.

This topic covers the target role shape design. For the EEM-vs-native-provider migration mechanics (how to onboard existing EEM entitlement groups), see topic 110 in Cluster 16.

## Astro RBAC hierarchy

```
Organization roles  →  apply across all Workspaces
Workspace roles     →  apply within one Workspace
Deployment roles    →  apply to one specific Deployment
DAG-level roles     →  apply to individual DAGs (Astro Runtime 3.1-12+)
```

Permissions are **additive**: if a user holds multiple roles, the highest permission wins [B2]. Organization Owners inherit Workspace Owner permissions for every Workspace in the org [B4].

## Role inventory

### Organization roles

| Role | Scope | EEM analogy |
|---|---|---|
| **Organization Owner** | Full control: settings, billing, security, audit logs, all Workspaces [B4] | EEM superadmin |
| **Organization Billing Admin** | Subscriptions, invoices, usage reports [B3] | Finance/procurement role |
| **Organization Observe Admin/Member** | Observability platform access | Monitoring team |
| **Organization Member** | Profile only; no Workspace access by default [B4] | EEM "view only" with no group entitlements |

### Workspace roles

| Role | Scope |
|---|---|
| **Workspace Owner** | Full admin: create/delete Deployments, manage all users [B6][B7] |
| **Workspace Operator** | Operational tasks: trigger DAGs, manage connections |
| **Workspace Author** | Create and edit DAG code/projects |
| **Workspace Member** | Interact with existing resources; read-heavy [B4] |
| **Workspace Accessor** (Preview) | Restricted read-only access [B4] |

### Deployment and DAG-level roles

| Level | Use case |
|---|---|
| Deployment role | Restrict individual users to a single Deployment within a shared Workspace |
| DAG-level role | Restrict access to specific DAGs within a shared Deployment (Astro Runtime 3.1-12+) [B6][B8] |

## EEM → Astro role mapping pattern

| EEM entitlement pattern | Astro role shape |
|---|---|
| Job group owner (full control of a group) | Workspace Owner on the team's Workspace |
| Job group operator (trigger/monitor only) | Workspace Operator |
| Read-only auditor across all groups | Organization Member + Workspace Member on each Workspace |
| Service account for CI/CD automation | Workspace-level API token with Workspace Operator or Author scope |

## Org model (Axis D — H rating)

| Org model | Role design implication |
|---|---|
| **One AutoSys instance per BU** | Each BU becomes a Workspace; BU admins get Workspace Owner; enterprise admins get Org Owner |
| **Shared enterprise-wide instance** | Multiple Workspaces; a Platform team holds Org Owner; team leads get Workspace Owner |
| **Federated self-service** | Teams provision Workspaces via Terraform/API; CI/CD service accounts use Deployment-scoped tokens |

## Key design principle

> Use **Teams** in Astro to group users and assign workspace roles at the group level [B4]. This mirrors EEM's group-entitlement model and avoids per-user role management at scale.

## Sources

[B2, B4] Astronomer Docs — Astro user permissions: https://www.astronomer.io/docs/astro/user-permissions (accessed 2026-08-08)
[B3] Astronomer Docs — Organization roles reference (accessed 2026-08-08)
[B6, B7] Astronomer Docs — Workspace roles reference (accessed 2026-08-08)
[B8] Astronomer Docs — DAG-level access control: https://www.astronomer.io/docs/astro/dag-level-permissions (accessed 2026-08-08)
