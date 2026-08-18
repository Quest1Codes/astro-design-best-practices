# Ticketing and ITSM Integration Design (ServiceNow / PagerDuty)

Replacing AutoSys's built-in alarm/notification system with an enterprise-grade ITSM integration is a common migration requirement. The recommended architecture uses a **hub-and-spoke model**: Airflow fires events to PagerDuty, and PagerDuty syncs to ServiceNow. This avoids brittle point-to-point integration between Airflow and ServiceNow.

## Recommended Architecture

```
Airflow (on_failure_callback)
    → PagerDuty (deduplication + on-call routing)
        → ServiceNow (incident/ticket creation via PagerDuty-ServiceNow ITSM Integration)
```

**Why not Airflow → ServiceNow directly?**
A direct Airflow→ServiceNow integration requires managing ServiceNow API authentication, mandatory-field mapping, data policies, and retry logic inside Airflow. PagerDuty handles all of this and adds deduplication — preventing the same DAG failure from creating multiple duplicate tickets during retries [B1][B2].

## Implementation: Airflow → PagerDuty

Use the `apache-airflow-providers-pagerduty` package [B1]:

```python
from airflow.providers.pagerduty.notifications.pagerduty import send_pagerduty_notification

with DAG(
    dag_id="critical_pipeline",
    on_failure_callback=[
        send_pagerduty_notification(
            summary="DAG {{ dag.dag_id }} failed on task {{ ti.task_id }}",
            severity="critical",
            source="Airflow",
            dedup_key="{{ dag.dag_id }}-{{ ti.task_id }}",  # Prevents duplicate incidents on retry
            integration_key="YOUR_PAGERDUTY_ROUTING_KEY"
        )
    ],
):
    ...
```

The `dedup_key` parameter is critical: it ties the PagerDuty event to a specific DAG+task combination, so retries do not create a flood of duplicate incidents [B1].

## PagerDuty → ServiceNow Sync

Enable the official **PagerDuty for ServiceNow** integration from the ServiceNow Store [B2]:
- Set the sync mode to **"Auto"** so PagerDuty incidents are automatically converted to ServiceNow tickets [B2].
- Map mandatory ServiceNow fields (assignment group, impact, urgency) using ServiceNow's **Inbound Field Rules** to prevent ticket creation failures caused by missing required fields [B2].

## Alert Severity Mapping

| Airflow Event | PagerDuty Severity | ServiceNow Priority |
|---|---|---|
| SLA miss (non-critical) | `warning` | P3/Low |
| Task failure (retrying) | `warning` | P3/Low |
| DAG-level failure (no retries left) | `critical` | P1/High |
| DR / infrastructure-level failure | `critical` | P1/Critical |

## Sources

[B1] `apache-airflow-providers-pagerduty` Docs — `send_pagerduty_notification`, `dedup_key` parameter (accessed 2026-08-10)
[B2] PagerDuty Docs — PagerDuty-ServiceNow ITSM Integration, Auto-sync, and field mapping (accessed 2026-08-10)
