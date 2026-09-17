# Forecast Feature (What-If Scheduling) → Capability Gap Design

> **Explicit Gap**: Airflow has no native equivalent to AutoSys Forecast. This document describes the gap precisely, why "use the Airflow UI Gantt chart" is not an adequate answer, and what a real design for this capability looks like on Astro.

## What AutoSys Forecast Actually Does

AutoSys Forecast is a **forward-looking simulation engine** — not a historical view [B1]:
- Given a time window (e.g., "this Saturday 02:00–06:00"), it projects which jobs would be scheduled to run, their expected start/end times (based on historical duration statistics), and which jobs would be delayed or miss their SLAs if a maintenance window were imposed.
- Output: a Gantt-chart-style report showing projected job timelines for the simulated period.
- Use case: capacity planning, maintenance window negotiation, SLA impact analysis before a change window.

## Why Airflow's Gantt Chart Is Not the Equivalent

| AutoSys Forecast | Airflow Gantt Chart |
|---|---|
| **Forward-looking** (future simulation) | **Backward-looking** (past run visualization) |
| Cross-DAG / cross-instance view | Single-DAG view only |
| Simulates a hypothetical time range | Shows actual historical run durations |
| Produces SLA impact report | Shows execution timeline for one DAG run |

The Airflow Gantt chart is an observability tool, not a planning tool [B2]. Telling users to "use the Gantt chart" in response to a Forecast gap question is an incorrect answer.

## Design Options for the Forecast Capability Gap

### Option 1: Scheduled Simulation DAG (Recommended for Simple Cases)

Build a DAG that queries the Airflow metadata DB for scheduled DAG runs in a future time window and cross-references historical average durations to estimate completion times:

```python
# Pseudocode — Forecast simulation DAG
@task
def project_dag_runs(window_start: datetime, window_end: datetime):
    # Query dag_run for scheduled_date between window_start and window_end
    # Join task_instance to get avg(duration) by task_id from last N runs
    # Output projected end times and SLA breach probability
    ...
```

Store projections in a BI-accessible table (Snowflake, BigQuery) and visualize in Grafana or your BI tool. Refresh nightly [B2].

### Option 2: Astro Observe + Custom Metrics (Recommended for Enterprise SLA Planning)

- Use **Astro Observe** to track historical task duration statistics across all Deployments [B2].
- Export `task_instance` duration metrics to a time-series database (Prometheus + Grafana).
- Build a Grafana forecast dashboard using predicted completion bands (p50/p95 of historical duration per task).
- For maintenance window negotiation: query scheduled DAG runs via the Airflow REST API for the candidate window and overlay with duration estimates.

### Option 3: External Tool Integration

For organizations that require true what-if scheduling as part of their ITSM change management process:
- Use a change management tool (ServiceNow Change module) that calls the Airflow REST API to enumerate scheduled DAGs in a candidate maintenance window.
- Automated impact report: list of DAGs that would be interrupted, their SLA deadlines, and downstream consumers.

## Important Design Note: Maintenance Windows in Airflow

AutoSys maintenance windows suspended agent execution. In Airflow, the equivalent is:
- **Pausing the affected DAGs** before the maintenance window. **Correction**: an earlier draft of this file cited `astro deployment dag pause <dag_id> --deployment-id <id>` as an Astro CLI command; no such subcommand exists in the current CLI reference. The actual mechanism is the Airflow REST API — `PATCH` the DAG resource with `is_paused: true` [B3].
- Unpausing after the window (same `PATCH` mechanism, `is_paused: false`).
- Automate pause/unpause via the Airflow REST API in your ITSM runbook, authenticated with a Deployment API token [B2][B3].

## Sources

[B1] Broadcom AutoSys Documentation — Forecast feature: forward-looking schedule simulation, Gantt-chart output for maintenance-window planning, SLA impact analysis (accessed 2026-08-18)
[B2] Astronomer Docs — Astro Observe (cross-Deployment data products, asset/task duration metrics): https://www.astronomer.io/docs/astro/astro-observe (tier 1, URL added on citation-hygiene review). The Airflow Gantt chart's observability-not-forecasting distinction is standard Apache Airflow UI documentation (airflow.apache.org), not indexed in the astronomer-docs MCP scope — not independently re-verified on this pass.
[B3] Astronomer Docs — Airflow API on Astro, pausing a DAG via `PATCH` to the `dag` resource on the `/api/v2` endpoint (Airflow 3): https://www.astronomer.io/docs/astro/airflow-api#pause-a-dag (tier 1, added on doc-verification review — corrects the fabricated `astro deployment dag pause` CLI command above)
