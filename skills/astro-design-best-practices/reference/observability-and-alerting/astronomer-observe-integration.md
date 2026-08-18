# Astronomer Observe Integration

AutoSys reporting (e.g., via WCC) was primarily job-centric. Astro Observe shifts the paradigm to **data-centric observability**, treating pipelines as "data products" and monitoring their overall health, timeliness, and cost rather than just individual task success/failure.

## What is Astro Observe?

Astro Observe is an observability layer built directly into the Astro platform [B1][B4]. It bridges orchestration and data quality by providing:
- **Data Products**: Logical groupings of related assets (DAGs, Snowflake tables, BigQuery datasets) across multiple deployments [B1][B6].
- **Business SLAs**: Dashboards tracking data freshness and delivery times against defined business agreements [B7][B8].
- **Real-Time Lineage**: Visual dependency graphs powered by OpenLineage [B5][B9].
- **AI Log Summaries**: Automated synopses of failures with prescriptive troubleshooting steps [B10].

## Why use Observe over standard Airflow UI?

| Feature | Airflow UI | Astro Observe |
|---|---|---|
| Focus | Job/Task execution state | End-to-end Data Product health |
| SLA tracking | Task-level timeout/SLA miss | Product-level freshness and delivery SLA |
| Cross-deployment | Single deployment only | Spans multiple Deployments and Workspaces |
| Lineage | Basic task dependencies | Full data asset lineage (tables, datasets) |
| Cost visibility | None | Correlates compute (e.g. Snowflake) with pipeline activity [B1] |

## Implementation steps

Because Astro Observe is natively integrated into Astro, setup is minimal compared to third-party tools:

1. **Enable OpenLineage**: Ensure the OpenLineage provider is active (it is enabled by default on Astro Runtime) to populate the foundational lineage graph.
2. **Define Data Products**: In the Astro UI, create Data Products by grouping the critical end-state tables or dashboards. Observe will automatically infer the upstream DAGs based on lineage [B1][B15].
3. **Set SLAs**: Define the required freshness (e.g., "Data must be updated by 8:00 AM daily").
4. **Configure Alerts**: Route SLA warnings and breaches to stakeholders via Slack or email [B11].

## Observability design for AutoSys migrants

For teams accustomed to tracking critical paths in AutoSys (e.g., using Cross-Box conditions or AAI):
- Do not attempt to recreate complex cross-box SLA alarms using raw Airflow callbacks.
- Instead, map the *business outcome* of those critical paths to a **Data Product** in Astro Observe.
- Monitor the Data Product's SLA. This provides a cleaner abstraction and prevents alert fatigue from intermediate task failures.

## Sources

[B1, B6] Astronomer Docs — Astro Observe overview: https://www.astronomer.io/docs/astro/observe (accessed 2026-08-08)
[B4, B5, B9] DBTA — Astronomer announces Astro Observe capabilities (accessed 2026-08-08)
[B7, B8, B10, B11] Astronomer Docs — Data Products and SLAs (accessed 2026-08-08)
