# Cross-Instance Enterprise Console Visibility → Astronomer Multi-Deployment Dashboard Design

AutoSys provided cross-instance visibility through its **Workload Control Center (WCC)** — a single GUI that could aggregate status views across multiple AutoSys instances. Operations teams could see job statuses from `PRD`, `UAT`, and `DEV` instances without switching contexts [B1].

In Airflow, each Deployment has its own isolated Airflow UI (webserver). Without a platform layer, cross-Deployment visibility requires manually navigating between separate URLs — this is the default vanilla Airflow experience. Astronomer's platform layer (Astro) addresses this gap.

## What Astro Provides Natively

| AutoSys WCC Feature | Astro Equivalent | Notes |
|---|---|---|
| **Cross-instance job status overview** | **Astro Observe** — cross-Deployment DAG health dashboard | Aggregates status across all Deployments in an Organization [B2]. |
| **Organization-level summary** | **Astro Organization Dashboard** | High-level view of all Workspaces and Deployments; identifies unexpected activity or resource anomalies [B2]. |
| **Per-instance drill-down** | Individual Deployment Airflow UI | Click through from the Organization Dashboard to a specific Deployment's Airflow UI. |
| **Cross-instance SLA tracking** | **Astro Observe** + Astro Alerts | Configure SLA-miss alerts that fire across all Deployments [B2]. |

## Architecture: What "Multi-Deployment Visibility" Means in Practice

```
Astro Organization Dashboard (single pane)
  ├── Workspace: Finance
  │     ├── Deployment: finance-prod → Observe metrics, alert state
  │     └── Deployment: finance-dev → Observe metrics, alert state
  └── Workspace: Operations
        ├── Deployment: ops-prod → Observe metrics, alert state
        └── Deployment: ops-staging → Observe metrics, alert state
```

The Organization Dashboard does **not** provide task-instance-level visibility across Deployments — that requires navigating to each Deployment's Airflow UI. It provides health-signal aggregation (failed DAG runs, SLA breaches, resource anomalies) [B2].

## For Deeper Cross-Deployment Analytics: Export to BI

For organizations that need AutoSys WCC-equivalent depth (e.g., cross-Deployment SLA trend reports, capacity utilization dashboards across all Deployments):

1. **Export metrics** from each Deployment to a central Prometheus instance or time-series DB.
2. **Build a Grafana dashboard** that federates metrics across Deployments — a true enterprise-grade cross-Deployment view.
3. **Export metadata** (dag_run, task_instance) from each Deployment's read replica into a central data warehouse and build cross-Deployment reporting in your BI tool.

On Astro, metrics export is configured per-Deployment under **Deployment → Telemetry** settings [B2].

## Explicit Gap: No Single Cross-Deployment Task Search

There is no Astro feature that lets you search for "all task instances in state FAILED across ALL Deployments simultaneously" in a single query — the metadata DBs are isolated [B2]. The closest approach is:
1. Astro Observe alert aggregation (reactive — fires when something fails).
2. Federated Prometheus query across Deployment metric endpoints (proactive — requires setup).

## Sources

[B1] Broadcom AutoSys Documentation — Workload Control Center (WCC), cross-instance status aggregation, multi-instance GUI management (accessed 2026-08-18)
[B2] Astronomer Docs — Astro Observe, Organization Dashboard, Workspace/Deployment-level health views, Deployment Telemetry export, cross-Deployment alert configuration (accessed 2026-08-18)
