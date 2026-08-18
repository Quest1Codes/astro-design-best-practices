# Alert-Fatigue and Deduplication Strategy

In AutoSys, noisy alarms were often suppressed manually at the console or via static rules. In Airflow, frequent task retries, downstream cascade failures, and transient network issues can quickly lead to alert fatigue, causing teams to ignore critical notifications.

An effective strategy shifts from reactive, task-based alerting to observability-driven, deduplicated incident management.

## 1. Architectural deduplication

Airflow itself does not natively deduplicate alerts across tasks. Deduplication must be handled either at the DAG level or in the aggregation layer:

| Strategy | Implementation |
|---|---|
| **Incident Aggregation Layer** (Recommended) | Route alerts to PagerDuty or Opsgenie. Use "deduplication keys" (e.g., `dag_id` + `execution_date`) so multiple task failures in the same run update a single incident rather than paging 50 times. |
| **Astro Observe** | Monitors data products rather than individual tasks. An SLA breach on a data product triggers one alert, even if 5 upstream tasks failed. |
| **DAG-level vs. Task-level** | Use DAG-level callbacks (`on_failure_callback` on the `@dag`) instead of per-task callbacks to ensure only one alert fires when the DAG ultimately fails. |

## 2. Preventing "Flappy" alerts

If a task is configured with retries (`retries=3`), a naive `on_failure_callback` might alert on every retry attempt.
- **Fix**: The default behavior of `on_failure_callback` only triggers when all retries are exhausted. Do not use `on_retry_callback` for paging alerts; reserve it for silent logging or custom cleanup logic.
- **Airflow 2.6+ features**: Use `max_consecutive_failed_dag_runs` (requires a custom sensor or callback logic to inspect DB state) to only alert if a fast-polling DAG fails multiple times in a row, rather than alerting every 5 minutes.

## 3. Astronomer-specific tooling

Astronomer provides tools to centralize and reduce noise:
- **Astro Alerts**: Configure alerts via the Astro UI at the Deployment/Workspace level. This centralizes notification management and makes it easier to mute or adjust thresholds without pushing code changes.
- **Astro Observe**: For business-critical pipelines, group DAGs into "Data Products". Monitor the Data Product's SLA rather than the individual Airflow tasks. This aligns alerts with actual business impact (e.g., "Sales Dashboard is late" vs. "Task `extract_sales` failed").

## 4. Operational feedback loops

Alerts must be treated as code that requires maintenance:
- **Tiering**: Only page (P1/P2) for issues requiring immediate human intervention. Route P3/P4 warnings to a low-priority Slack channel or email.
- **Context enrichment**: Every alert must include actionable context. Ensure the alert payload includes a direct link to the failed DAG run in the Astro UI (`{{ ti.log_url }}`) and a link to the relevant runbook.
- **Pruning**: If an alert frequently triggers but requires no action, it is noise. Fix the underlying flakiness, increase the timeout/retries, or downgrade the alert severity.

## Sources

[B-Industry] PagerDuty / Opsgenie documentation on deduplication keys and incident correlation (accessed 2026-08-08)
[B-Observe] Astronomer Docs — Astro Observe Data Products (accessed 2026-08-08)
[B-Airflow] Apache Airflow Docs — Callbacks and retries (accessed 2026-08-08)
