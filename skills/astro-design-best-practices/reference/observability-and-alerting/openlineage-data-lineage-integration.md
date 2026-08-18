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
Pipelines that create and drop temporary tables can clutter the lineage graph. You can configure the Astro SDK to filter these out by setting the environment variable:
`AIRFLOW__ASTRO_SDK__OPENLINEAGE_EMIT_TEMP_TABLE_EVENT=False`

### 4. Custom operators and Facets
If your teams write custom Airflow operators, ensure they implement the `get_openlineage_facets_on_complete` method. This allows custom logic to emit standard lineage events.
You can also use OpenLineage "facets" to attach custom operational metadata (e.g., data quality scores, PII flags) directly to the lineage events.

## Remote Execution considerations

If using Remote Execution Agents (hybrid architecture):
- Ensure the agent's network can route outbound lineage events to the Astro control plane.
- Use a dedicated Deployment API Token with limited "Observe Ingest" permissions to authenticate the OpenLineage emitter.

## Local testing

Before deploying, developers can validate lineage emission locally using the Astro CLI by setting the transport to `console` in the local `.env` file:
`AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "console"}'`
This prints the JSON lineage events to the terminal for debugging.

## Sources

[B1] Astronomer Docs — OpenLineage integration: https://www.astronomer.io/docs/astro/data-lineage (accessed 2026-08-08)
[B-Custom] Apache Airflow Providers OpenLineage Docs (accessed 2026-08-08)
