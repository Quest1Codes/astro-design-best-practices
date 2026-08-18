# on_failure_callback Design Patterns

AutoSys triggered alerting natively on job failure without requiring per-job alerting logic. In Airflow, task and DAG failures are handled programmatically via callbacks. Designing these callbacks efficiently is critical for reliable alerting and avoiding scheduler performance degradation.

## Callback levels

Airflow provides callbacks at different scopes. For alerting, the most relevant are:

| Callback | Scope | Trigger condition |
|---|---|---|
| `on_failure_callback` (DAG level) | Global to the DAG | Triggers if the DAG itself fails (e.g., all retries exhausted for a critical task, causing DAG run failure) |
| `on_failure_callback` (Task level) | Specific to the task | Triggers when the specific task fails [B2][B4] |

> **Design principle**: Use DAG-level callbacks for baseline/generic alerting (e.g., "Pipeline X failed"), and task-level callbacks only when a specific task requires a unique response (e.g., a critical database update needing an immediate PagerDuty page) [B2][B4].

## Best practices

1. **Keep it lightweight**: Callbacks execute in the DAG processor or task worker. Complex logic, heavy network calls, or long-running operations in a callback will delay task/DAG finalization and can cause scheduler timeouts [B1].
2. **Use Provider Packages**: Do not write raw `requests.post()` calls for Slack or Teams. Use native `Notifiers` (e.g., `SlackNotifier` from `apache-airflow-providers-slack`) — they are cleaner and handle error edge cases [B10][B11].
3. **Use the `context` dictionary**: Always design the callback to accept the `context` dictionary, which contains `dag_id`, `task_id`, `exception`, and `log_url` for building rich alerts [B2][B3].
4. **List of callbacks (Airflow 2.6+)**: You can pass a list of callback functions (e.g., `on_failure_callback=[alert_slack, log_to_db]`). This allows decoupling notification methods into modular components [B6].

## Example pattern: Layered alerting

```python
from airflow.providers.slack.notifications.slack import send_slack_notification

# 1. Define a generic, reusable notifier
notify_slack = send_slack_notification(
    text="DAG {{ dag.dag_id }} failed on task {{ ti.task_id }}. Logs: {{ ti.log_url }}",
    channel="#data-eng-alerts"
)

# 2. Apply to the DAG for a catch-all baseline
@dag(on_failure_callback=notify_slack, ...)
def my_pipeline():
    
    # 3. Override or add specific callbacks at the task level if needed
    @task(on_failure_callback=[notify_slack, page_on_call])
    def critical_task():
        ...
```

## Error handling in callbacks

If your callback code throws an exception, **the error does not appear in standard task logs**. It will appear in the DAG processor or worker logs, leading to "silent" alerting failures [B6]. Ensure callback logic is robust and wrapped in `try/except` if executing custom logic.

## Sources

[B1] Data Engineer Things — Airflow callbacks: https://dataengineerthings.org (accessed 2026-08-08)
[B2, B3] DataCamp — Airflow alerting best practices (accessed 2026-08-08)
[B4, B10, B11] Astronomer Docs — Airflow notifications (accessed 2026-08-08)
[B6] Apache Airflow Docs — Callbacks (accessed 2026-08-08)
