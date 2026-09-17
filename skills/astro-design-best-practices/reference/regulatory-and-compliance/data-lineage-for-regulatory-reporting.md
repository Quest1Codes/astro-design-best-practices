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
| **SOX** | {syn: B1} The underlying technical capability — automated, always-current lineage tracking of what data fed which output — is real and platform-verified [B1]; applying it as SOX evidence of "no unauthorized transformation" is this file's own inference, not a claim from a dedicated SOX-lineage source. **Correction**: an earlier draft cited this row to [B3], an unverified blog post; retargeted to the actual verified capability. |
| **AML / Basel** | {syn: B1} Same correction as above — the lineage-tracing capability is real [B1]; the specific AML/Basel-compliance framing is this file's own applied inference, not a dedicated source's claim. |
| **GDPR** | Identifies exactly where PII flows across systems — critical for scoping erasure requests (see topic 075) [B2]. |
| **DORA / BCBS 239** | {syn: B1} Same pattern: OpenLineage's real lineage-tracking capability [B1] applied by inference to DORA/BCBS 239 reporting-accuracy requirements — no dedicated source for the regulatory-specific framing exists; **correction**: an earlier draft had zero citation on this row at all. |

## Impact Analysis

When a data quality issue is discovered upstream (e.g., a corrupted source table), OpenLineage lineage graphs allow you to rapidly identify all downstream datasets and regulatory reports affected — dramatically reducing the time to communicate impact to compliance teams [B1][B2].

## Sources

[B1] Astronomer Docs — Configure OpenLineage on Astro (pre-installed OpenLineage Airflow Provider, zero-config capture, Astro Observe): https://www.astronomer.io/docs/astro/observe-openlineage (tier 1, URL added on citation review)
[B2] OpenLineage.io — Airflow Listener API integration, supported operators, and backend compatibility (no Astronomer Docs match — this is third-party openlineage.io content, out of scope for the Astronomer docs MCP; not re-verified on this pass)
[B3] Astronomer Blog — Data lineage for financial services compliance (no Astronomer Docs match found on this pass — likely a specific blog post not indexed by the docs search; verify separately)
