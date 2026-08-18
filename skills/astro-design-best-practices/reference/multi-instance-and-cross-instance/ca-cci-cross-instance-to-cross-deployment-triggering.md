# CA CCI Cross-Instance/Cross-Platform Event Architecture → Astro Cross-Deployment Triggering

AutoSys used **CAICCI (CA Common Communications Interface)** as the transport layer for cross-instance and cross-platform event communication. A job in the `PRD` instance could trigger or depend on a job in the `UAT` instance via CAICCI-routed `sendevent` commands. The receiving instance's Application Server processed the incoming event and updated its own Event Server database [B1].

This proprietary messaging layer has no direct equivalent in Astro. The migration replaces CAICCI with standard HTTP-based mechanisms.

## CAICCI Architecture → Airflow Replacement

{syn: CAICCI `sendevent` → Airflow REST API `POST /api/v1/dags/{dag_id}/dagRuns`}

| AutoSys Mechanism | Airflow / Astro Replacement | Notes |
|---|---|---|
| **CAICCI `sendevent CHANGE_STATUS`** | Airflow REST API: `POST /api/v1/dags/{dag_id}/dagRuns` | HTTP-authenticated DAG trigger from an upstream system [B2]. |
| **Cross-instance wait (status polling)** | `ExternalTaskSensor` with `mode='reschedule'` | Polls the status of a task in another DAG (same Astro deployment or reachable Airflow instance) [B2]. |
| **CA-XPS (z/OS cross-platform scheduling)** | Zowe CLI / SSH + Airflow sensor (see topic 086) | Mainframe boundary integration pattern. |
| **CAICCI-mediated inbound triggers** | Airflow REST API + bearer token auth | Any external system (AutoSys remaining, mainframe, third-party) can trigger an Airflow DAG via REST [B2]. |

## Cross-Deployment Triggering Design on Astro

Astro Deployments do not share a metadata database — they are fully isolated. Cross-Deployment triggering requires using the Airflow REST API (or Astro API) as the communication channel.

### Pattern 1: Direct REST Trigger (Fire-and-Forget)

Upstream Deployment DAG calls the downstream Deployment's API at completion:

```python
from airflow.providers.http.operators.http import SimpleHttpOperator

trigger_downstream = SimpleHttpOperator(
    task_id="trigger_downstream_deployment",
    http_conn_id="downstream_airflow_api",  # Connection pointing to downstream Deployment URL
    method="POST",
    endpoint="/api/v1/dags/downstream_dag_id/dagRuns",
    headers={"Content-Type": "application/json"},
    data='{"conf": {"upstream_run_id": "{{ run_id }}"}}',
)
```

### Pattern 2: Airflow Assets/Datasets (Preferred for Data Dependency)

If the cross-Deployment dependency is really about data readiness (not just job status), use Airflow Datasets. An upstream DAG publishes to a dataset outlet; a downstream DAG is scheduled to trigger when that dataset is updated [B2]. This is the modern replacement for event-based `CHANGE_STATUS` signaling.

## Sources

[B1] Broadcom AutoSys Documentation — CAICCI architecture, cross-instance `sendevent`, Application Server event routing (accessed 2026-08-11)
[B2] Apache Airflow REST API Docs — `POST /api/v1/dags/{dag_id}/dagRuns`, `ExternalTaskSensor`, Airflow Datasets (accessed 2026-08-11)
