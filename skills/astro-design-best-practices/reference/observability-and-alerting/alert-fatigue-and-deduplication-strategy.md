# Alert-Fatigue and Deduplication Strategy

In AutoSys, noisy alarms were often suppressed manually at the console or via static rules. In Airflow, frequent task retries, downstream cascade failures, and transient network issues can quickly lead to alert fatigue, causing teams to ignore critical notifications.

An effective strategy shifts from reactive, task-based alerting to observability-driven, deduplicated incident management.

**Citation note**: an earlier draft of this file had no inline `[Bn]` or `{syn:}` markers anywhere in the body — every claim below traced only to the bare Sources list, which fails the project's own zero-tolerance traceability standard even though the underlying facts were separately spot-checked as accurate. Markers added below on Critic-pass review.

## 1. Architectural deduplication

Airflow itself does not natively deduplicate alerts across tasks [B-Airflow]. Deduplication must be handled either at the DAG level or in the aggregation layer:

| Strategy | Implementation |
|---|---|
| **Incident Aggregation Layer** (Recommended) | Route alerts to PagerDuty or Opsgenie. Use "deduplication keys" (e.g., `dag_id` + `execution_date`) so multiple task failures in the same run update a single incident rather than paging 50 times [B-Industry]. |
| **Astro Observe** | Monitors data products rather than individual tasks. An SLA breach on a data product triggers one alert, even if 5 upstream tasks failed [B-Observe]. |
| **DAG-level vs. Task-level** | Use DAG-level callbacks (`on_failure_callback` on the `@dag`) instead of per-task callbacks to ensure only one alert fires when the DAG ultimately fails [B-Airflow]. |

## 2. Preventing "Flappy" alerts

If a task is configured with retries (`retries=3`), a naive `on_failure_callback` might alert on every retry attempt.
- **Fix**: The default behavior of `on_failure_callback` only triggers when all retries are exhausted [B-Airflow]. Do not use `on_retry_callback` for paging alerts; reserve it for silent logging or custom cleanup logic.
- **Airflow 2.9+ feature — correction**: an earlier draft of this file said `max_consecutive_failed_dag_runs` "requires a custom sensor or callback logic to inspect DB state." That's wrong — it's a built-in `DAG()`/`@dag` constructor parameter (`max_consecutive_failed_dag_runs=3`, experimental as of 2.9) that the scheduler itself enforces, automatically disabling the DAG after N consecutive failed runs — no custom sensor, callback, or DB inspection needed [B-MaxFailedRuns].

## 3. Astronomer-specific tooling

Astronomer provides tools to centralize and reduce noise:
- **Astro Alerts**: Configure alerts via the Astro UI at the Deployment/Workspace level. This centralizes notification management and makes it easier to mute or adjust thresholds without pushing code changes [B-Observe].
- **Astro Observe**: For business-critical pipelines, group DAGs into "Data Products". Monitor the Data Product's SLA rather than the individual Airflow tasks. This aligns alerts with actual business impact (e.g., "Sales Dashboard is late" vs. "Task `extract_sales` failed") [B-Observe].

## 4. Operational feedback loops

Alerts must be treated as code that requires maintenance:
- **Tiering**: Only page (P1/P2) for issues requiring immediate human intervention. Route P3/P4 warnings to a low-priority Slack channel or email.
- **Context enrichment**: Every alert must include actionable context. Ensure the alert payload includes a direct link to the failed DAG run in the Astro UI (`{{ ti.log_url }}`) and a link to the relevant runbook.
- **Pruning**: If an alert frequently triggers but requires no action, it is noise. Fix the underlying flakiness, increase the timeout/retries, or downgrade the alert severity.

## Sources

[B-Industry] PagerDuty / Opsgenie documentation on deduplication keys and incident correlation (accessed 2026-08-08)
[B-Observe] Astronomer Docs — Create a data product in Astro Observe: https://www.astronomer.io/docs/astro/create-data-products (tier 1)
[B-Airflow] Apache Airflow Docs — Callbacks and retries: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html (tier 2)
[B-MaxFailedRuns] Apache Airflow Docs — `max_consecutive_failed_dag_runs` DAG parameter (experimental since 2.9.0; scheduler automatically disables the DAG after N consecutive failed runs, no custom logic required): https://airflow.apache.org/docs/apache-airflow/3.0.0/_api/airflow/models/dag/index.html (tier 2, added on Critic-pass review — corrects the "requires custom sensor/callback" claim above)
