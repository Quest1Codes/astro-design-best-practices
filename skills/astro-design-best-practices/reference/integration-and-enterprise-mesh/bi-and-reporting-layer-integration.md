# BI and Reporting-Layer Integration

One of the most common data freshness problems in AutoSys-managed shops was dashboards running on static schedules that were decoupled from actual data pipeline completion. Airflow's event-driven model allows BI tool refreshes to be triggered *only after* the upstream data is verified as ready — eliminating "stale dashboard" incidents.

## Core Design: Event-Driven Data-First Refresh

**Anti-pattern**: BI tool refresh is scheduled independently (e.g., Tableau scheduled at 7:00 AM; Airflow ETL finishes at 7:23 AM → 23 minutes of stale data shown to stakeholders).

**Correct pattern**: The BI refresh is the last task in the Airflow DAG, triggered only after all upstream transformations and data quality gates pass [B1].

```
Extract → Transform → DQ Gate → [Trigger BI Refresh] → Alert on failure
```

## Tool-Specific Integration Patterns

| BI Tool | Airflow Integration | Key Notes |
|---|---|---|
| **Looker** | `LookerStartPdtBuildOperator` (via `apache-airflow-providers-google`) | Triggers Persistent Derived Table (PDT) rebuilds directly from a DAG [B1][B2]. |
| **Power BI** | `SimpleHttpOperator` or custom `PowerBIHook` calling the Power BI REST API `refreshes` endpoint | POST to `https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/refreshes` [B1]. |
| **Tableau** | Tableau REST API via `SimpleHttpOperator` or community-built Airflow providers | Trigger `runExtractRefreshTask` on a specific Tableau datasource [B1]. |

Check the [Airflow Registry](https://registry.astronomer.io/) for community-maintained providers before writing custom HTTP calls [B1].

## Write-Audit-Publish (WAP) Pattern

For critical financial or regulatory reporting dashboards:
1. **Write**: Load data into a staging/shadow table.
2. **Audit**: Run validation tasks (row count, schema check, null check, reconciliation against source system).
3. **Publish**: Atomically swap staging into the production table (e.g., `ALTER TABLE ... RENAME TO ...`).
4. **Trigger BI refresh**: Only *after* the publish step succeeds.

This ensures the BI layer never sees half-loaded or invalid data [B1][B2].

## Design Rules

| Rule | Rationale |
|---|---|
| **Disable native BI schedules** | Let Airflow own the refresh schedule entirely. Native schedules in BI tools create race conditions [B1]. |
| **Add a DQ gate before refresh** | Never trigger a dashboard refresh if upstream data quality checks have failed [B1]. |
| **Alert on refresh failure** | BI refresh failures are end-user-visible events; route them to PagerDuty/ServiceNow (see topic 083) [B2]. |

## Sources

[B1] Astronomer Docs & Airflow Registry — Looker, Power BI, and Tableau integration patterns (no confident single-page Astronomer Docs match found on this pass — Astronomer Learn covers Tableau only as a downstream visualization step in a Fivetran tutorial, not a dedicated BI-integration guide; see https://www.astronomer.io/docs/learn/airflow-fivetran#step-9-optional-visualize-your-commits-with-tableau (tier 1) for that narrow case; Looker/Power BI specifics not independently verified)
[B2] Airflow Docs — Write-Audit-Publish pattern and data quality gates (no Astronomer Docs match found on this pass — this is Apache Airflow OSS/community pattern content; verify against airflow.apache.org or the dbt/Cosmos ecosystem directly)
