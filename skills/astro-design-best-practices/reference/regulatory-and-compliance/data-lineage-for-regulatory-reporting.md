# Data Lineage for Regulatory Reporting

Regulatory auditors increasingly require organizations to demonstrate not just *that* data was processed, but *how*: where did it originate, what transformations occurred, and which reports consumed it? OpenLineage is the industry standard for answering these questions automatically within Airflow pipelines.

## OpenLineage on Astro Runtime

Astro Runtime includes `apache-airflow-providers-openlineage` pre-installed [B1]. No additional installation is needed. OpenLineage integrates via the **Airflow Listener API**, hooking into task lifecycle events (START, SUCCESS, FAIL) to emit lineage events in real-time without requiring custom code in DAG operators [B1][B2].

## What Gets Captured Automatically

For operators with native OpenLineage support (BigQueryOperator, SnowflakeOperator, SparkSubmitOperator, and others), the following is captured automatically:
- **Input datasets**: The tables/files read by the task, including their schema.
- **Output datasets**: The tables/files written by the task, including schema.
- **Job metadata**: The DAG ID, task ID, run ID, and timing.
- **Data quality facets**: Row counts, null counts, and schema changes (for supported operators) [B2].

## Backend: Marquez, Atlan, and Others

OpenLineage is an **open standard** — the lineage events are backend-agnostic [B1][B2]. You can forward events to:
- **Marquez** (open-source, self-hosted): Simple lineage graph UI.
- **Astronomer Astro Observe**: Astro's native observability layer aggregates OpenLineage metadata alongside DAG health metrics.
- **Commercial data catalogs** (Atlan, Alation, DataHub): For enterprise governance platforms that serve both engineers and compliance officers.

## Regulatory Use Cases

| Regulation | How OpenLineage Supports It |
|---|---|
| **SOX** | Proves the provenance of data feeding financial reports; demonstrates no unauthorized transformation occurred in the pipeline [B3]. |
| **AML / Basel** | Traces customer data flowing into risk-scoring models; proves inputs weren't tampered with [B3]. |
| **GDPR** | Identifies exactly where PII flows across systems — critical for scoping erasure requests (see topic 075) [B2]. |
| **DORA / BCBS 239** | Provides automated, audit-ready data lineage for systemic risk reporting accuracy requirements. |

## Impact Analysis

When a data quality issue is discovered upstream (e.g., a corrupted source table), OpenLineage lineage graphs allow you to rapidly identify all downstream datasets and regulatory reports affected — dramatically reducing the time to communicate impact to compliance teams [B1][B2].

## Sources

[B1] Astronomer Docs — OpenLineage integration with Astro Runtime (accessed 2026-08-10)
[B2] OpenLineage.io — Airflow Listener API integration, supported operators, and backend compatibility (accessed 2026-08-10)
[B3] Astronomer Blog — Data lineage for financial services compliance (accessed 2026-08-10)
