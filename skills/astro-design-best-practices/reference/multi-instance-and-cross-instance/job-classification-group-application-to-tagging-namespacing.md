# Job Classification via group/application Attributes → Astro Tagging and dag_id Namespacing

AutoSys's `group` and `application` attributes were independent of the `box` hierarchy — they provided a metadata classification layer for filtering jobs in `autorep` reports and GUI views, independent of which box a job was contained in. A job could be in box `ETL_NIGHTLY` but have `application=FINANCE` and `group=BATCH_CRITICAL`. These were free-form text fields [B1].

Airflow has no exact equivalent, but the combination of `tags` and `dag_id` namespacing covers the same ground.

## Attribute Mapping

{syn: AutoSys `group` / `application` → Airflow `tags`; AutoSys `application` scope → Airflow `dag_id` namespace prefix}

| AutoSys Attribute | Airflow Equivalent | Notes |
|---|---|---|
| **`application`** | `dag_id` prefix (e.g., `finance.gl_reconciliation`) + `tags=["finance"]` | `application` defined the owning system. Map to a namespace prefix in `dag_id` AND a tag for filtering [B2]. |
| **`group`** | `tags` (e.g., `tags=["batch-critical", "month-end"]`) | `group` was for operational grouping (priority, batch window). Map to one or more tags [B2]. |
| **`box` hierarchy** | `TaskGroup` (intra-DAG) or separate DAGs (inter-domain) | The box is the scheduling container; `group`/`application` are classification overlays above the box [B2]. |

## dag_id Namespacing Convention

Adopt a hierarchical `dag_id` convention that encodes the `application` and process type:

```
{business_unit}.{application}.{process_type}.{frequency}
```

Examples:
- `finance.gl.reconciliation.daily`
- `hr.payroll.ingestion.monthly`
- `ops.infra.cleanup.weekly`

This makes the `dag_id` self-documenting and prevents collisions when many teams share a single Astro Deployment [B2].

## Tag Convention for Operational Classification

Map AutoSys `group` values to a consistent tag vocabulary and enforce it via code review or `astro dev parse` CI check:

| AutoSys `group` Value | Airflow Tag |
|---|---|
| `BATCH_CRITICAL` | `sla:critical` |
| `MONTH_END` | `cadence:month-end` |
| `FINANCE_REPORTING` | `domain:finance` |
| `NON_PROD` | `env:staging` |

## Filtering in Practice

In the Airflow UI, `tags` are filterable from the DAGs list view — operators can filter to `domain:finance` to see only their team's pipelines, equivalent to the AutoSys `autorep -g FINANCE_REPORTING` pattern.

## Sources

[B1] Broadcom AutoSys Documentation — `group` and `application` JIL attributes, independent of box hierarchy (accessed 2026-08-11)
[B2] Apache Airflow Docs — `tags` parameter on DAG object, `dag_id` naming conventions (accessed 2026-08-11)
