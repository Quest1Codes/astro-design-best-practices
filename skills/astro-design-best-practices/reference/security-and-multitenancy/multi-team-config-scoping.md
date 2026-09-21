---
topic: multi-team-config-scoping
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals:
  - multi_owner
  - multi_instance
---

# Multi-Team Config Scoping

> CORRECTED: An earlier draft of this file recommended upstream Airflow 3's experimental
> "Multi-Team" mode (team-scoped configuration/DAG-bundle isolation within a single Airflow
> environment) as a lower-overhead alternative to per-BU Workspaces/Deployments. **This was
> wrong.** Astronomer's own docs state plainly that "the Airflow 3 multi-team model isn't
> supported on Astro" — Astro provides tenant isolation through Organizations, Workspaces, and
> Deployments instead [B13]. This matches the correction already made in the sibling file
> `federated-vs-centralized-self-service-design.md`; that file's Workspace/Deployment
> decomposition is the actual mechanism for team separation on Astro, not a fallback.

## The AutoSys starting point

Many AutoSys estates isolate business units by running one AutoSys **instance** per BU — each with
its own Event Server, agent fleet, and `$AUTOSERV`. This is a strong isolation boundary (separate
database, separate process) but an expensive one to operate at scale. `federated-vs-centralized-self-service-design.md`
covers the Astro-side decomposition: one Workspace (or Deployment) per BU.

## Why there is no cheaper within-Deployment alternative

Unlike upstream Apache Airflow, Astro does not expose a within-Deployment, multi-team config- or
RBAC-scoping mechanism as a substitute for separate Workspaces/Deployments — even for BUs whose
isolation needs are logical/reporting-only rather than compliance-driven. A *shared* AutoSys
instance with `group`/`application`-based logical separation (see
`multi-instance-and-cross-instance/job-classification-group-application-to-tagging-namespacing.md`
for that JIL-side classification model) maps onto Astro as `tags` within a shared Deployment, not
as a distinct isolation tier — `tags` give UI filtering, not RBAC or resource isolation.

## Decision guidance

| AutoSys topology signal | Astro-side recommendation |
|---|---|
| True instance-per-BU, each with independent HA/DR/compliance requirements | Workspace- or Deployment-per-BU (`federated-vs-centralized-self-service-design.md`) |
| Single shared instance, `group`/`application` used only for logical/reporting separation, no independent compliance requirement per BU | Still a shared Deployment with `tags` for logical grouping — there is no supported lighter-weight team-scoping mechanism within one Deployment on Astro; if per-team RBAC or resource isolation matters, that requires a separate Workspace or Deployment, not config scoping |
| Mixed — some BUs need hard isolation (compliance, blast-radius), others don't | Hybrid: hard-isolation BUs get their own Deployment; the remainder share one Deployment with `tags`-based logical grouping only |

## What doesn't change

Regardless of which decomposition is chosen, the underlying RBAC design
(`rbac-role-shape-design-mirrored-from-eem-entitlements.md`) and secrets scoping
(`connection-scoping-and-least-privilege.md`) still apply per team/BU — multi-team config scoping
narrows *where* the isolation boundary sits, it doesn't remove the need to design least-privilege
access within whatever boundary is chosen.

## Sources

- [P1] Project-internal — `skills/astro-design-best-practices/reference/security-and-multitenancy/federated-vs-centralized-self-service-design.md`
- [P2] Project-internal — `skills/astro-design-best-practices/reference/multi-instance-and-cross-instance/job-classification-group-application-to-tagging-namespacing.md`
- [B13] Astronomer Docs — Airflow feature support on Astro ("The Airflow 3 multi-team model isn't supported on Astro"): https://www.astronomer.io/docs/astro/airflow-feature-support (tier 1, verified via astronomer-docs)
