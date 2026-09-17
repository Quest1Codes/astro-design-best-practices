# OpenLineage / Data-Lineage Integration

AutoSys tracked job dependencies but lacked insight into the actual data assets (tables, files, partitions) being moved. OpenLineage solves this by emitting metadata about what data a task reads and writes, enabling a true "data supply chain" view.

## Astro's native OpenLineage integration

Astro provides built-in, first-class support for OpenLineage [B1]:
- **Pre-installed**: Astro Runtime includes the OpenLineage Airflow Provider (`apache-airflow-providers-openlineage`).
- **Zero-config capture**: Astro automatically captures lineage events from compatible Airflow operators and sends them to Astro Observe for visualization.
- **Real-time visibility**: Lineage graphs in Astro Observe update in real time, showing dependencies between DAGs, tasks, and the underlying data assets (e.g., Snowflake tables, BigQuery datasets).

## Implementation best practices

### 1. Strategic rollout
Do not attempt to map every pipeline immediately. Focus first on business-critical pipelines (e.g., those feeding executive dashboards or regulatory reports). Once the value is proven on high-impact paths, expand coverage.

### 2. Namespace consistency
If you are exporting OpenLineage data to an external catalog (like Atlan, DataHub, or a custom Marquez instance), ensure each Airflow instance uses a unique, consistent namespace. Reusing namespaces across dev/prod or different BUs will cause data collisions in the lineage graph.

### 3. Handle temporary tables
Pipelines that create and drop temporary tables can clutter the lineage graph. **Correction**: an earlier draft of this file cited a specific environment variable (`AIRFLOW__ASTRO_SDK__OPENLINEAGE_EMIT_TEMP_TABLE_EVENT`) for suppressing temp-table events. On doc-verification review, no such variable appears in Astro's current OpenLineage configuration reference, and it's namespaced under the deprecated Astro Python SDK (which isn't compatible with Airflow 3) rather than the OpenLineage provider itself — treat the earlier claim as unsupported/likely fabricated, not as a working config. The real, currently-documented OpenLineage environment variables are `OPENLINEAGE_NAMESPACE`, `OPENLINEAGE__FACETS__ENVIRONMENT_VARIABLES`, `AIRFLOW__OPENLINEAGE__EXECUTION_TIMEOUT`, and `AIRFLOW__CORE__TASK_SUCCESS_OVERTIME` [B2]. None of these is a direct temp-table-event suppressor; if filtering temp tables from the lineage graph is a real requirement, treat it as a `NEEDS_EXEC_CHECK` against the OpenLineage Airflow provider's own facet/extractor configuration rather than assuming a dedicated Astro-side switch exists.

### 4. Custom operators and Facets
If your teams write custom Airflow operators, ensure they implement the `get_openlineage_facets_on_complete` method. This allows custom logic to emit standard lineage events.
You can also use OpenLineage "facets" to attach custom operational metadata (e.g., data quality scores, PII flags) directly to the lineage events.

## Remote Execution considerations

If using Remote Execution Agents (hybrid architecture):
- Ensure the agent's network can route outbound lineage events to the Astro control plane.
- Use a dedicated Deployment API Token scoped to the **Deployment Observe Ingest** role to authenticate the OpenLineage emitter — a real, current Astro role template limited to `deployment.observability.event.create` and `deployment.observability.metrics.create` [B3]. **Verified** on Critic-pass follow-up: this claim initially carried no citation and looked similar to the earlier retracted temp-table variable, but checked out as real, not invented.

## Local testing

Before deploying, developers can validate lineage emission locally using the Astro CLI by setting the transport to `console` in the local `.env` file:
`AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "console"}'`
This prints the JSON lineage events to the terminal for debugging.

## Sources

[B1] Astronomer Docs — Configure OpenLineage on Astro (pre-installed OpenLineage Airflow Provider, zero-config capture): https://www.astronomer.io/docs/astro/observe-openlineage (tier 1) — **NEEDS_EXEC_CHECK**: the file's original B1 URL (`/docs/astro/data-lineage`) was not independently re-verified on this review; this URL is the current live page confirmed to cover the same content.
[B2] Astronomer Docs — Configure OpenLineage on Astro (real environment variables: `OPENLINEAGE_NAMESPACE`, `OPENLINEAGE__FACETS__ENVIRONMENT_VARIABLES`, `AIRFLOW__OPENLINEAGE__EXECUTION_TIMEOUT`, `AIRFLOW__CORE__TASK_SUCCESS_OVERTIME`): https://www.astronomer.io/docs/astro/observe-openlineage (tier 1, added on doc-verification review to replace the fabricated temp-table variable)
[B-Custom] Apache Airflow Providers OpenLineage Docs (accessed 2026-08-08)
[B3] Astronomer Docs — Deployment role templates ("Deployment Observe Ingest: allows a user entity permissions to ingest OpenLineage events and metrics") and Deployment role reference (`deployment.observability.event.create`, `deployment.observability.metrics.create`): https://www.astronomer.io/docs/astro/customize-deployment-roles#deployment-role-templates and https://www.astronomer.io/docs/astro/deployment-role-reference#deployment-observability (tier 1, added on Critic-pass review)
