---
topic: cross-instance-dependencies-to-dataset-rest-patterns
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: 
  - cross_instance
---

# Cross-Instance Job Dependencies → Asset/REST-Based Cross-Deployment Dependencies

In AutoSys, cross-instance job dependencies were expressed as `CHANGE_STATUS` events sent from one instance's Event Server to a remote instance's Event Server. A job in instance `UAT` could declare a dependency on a job in instance `PRD` completing successfully — the `UAT` scheduler would wait for the remote status signal before starting the dependent job [B1].

Airflow has no shared global event bus between isolated Deployments. The migration replaces this with either polling (`ExternalTaskSensor`) or data-driven triggering via Assets (formerly Datasets).

## Migration Decision: Which Pattern?

The choice between `ExternalTaskSensor` and Airflow Assets depends on what the cross-instance dependency actually represents:

| Cross-Instance Dependency Type | Recommended Airflow Pattern |
|---|---|
| **Job B in Instance 2 must wait for Job A in Instance 1 to reach `SUCCESS`** — pure status signal | `ExternalTaskSensor` [B2] |
| **Job B in Instance 2 must wait for data produced by Job A in Instance 1 to be available** — data readiness | Airflow Assets (Airflow 2.4+) [B2] |
| **Job A in Instance 1 must actively kick off Job B in Instance 2** — push trigger | `TriggerDagRunOperator` or REST API call [B2] |

## Pattern 1: ExternalTaskSensor

```python
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream_dag = ExternalTaskSensor(
    task_id="wait_for_upstream_completion",
    external_dag_id="upstream_dag_in_other_deployment",
    external_task_id="final_task_id",
    mode="reschedule",  # Do not block worker slot while waiting
    # execution_delta or execution_date_fn required if schedules differ
    execution_delta=timedelta(hours=1),
)
```

> **Critical gotcha**: `ExternalTaskSensor` by default requires an exact match on `execution_date`. If the upstream and downstream DAGs run on different schedules, you **must** specify `execution_delta` or `execution_date_fn` — otherwise the sensor will wait forever for a `logical_date` that never exists in the upstream DAG [B2].

## Pattern 2: Airflow Assets (Data-Centric Dependency)

> PRACTITIONER JUDGMENT: the class behind this feature was renamed to `Asset` in Airflow 3.0 (see
> naming note in `scheduler-and-dag/cross-dag-dependencies-datasets-vs-triggerdagrun-vs-externaltasksensor.md`).
> The import path below (`airflow.sdk`) reflects Airflow 3's Task SDK namespace convention but was
> not re-verified against a live Airflow 3.3.1 environment this session — confirm the exact import
> path before shipping this code.

Upstream DAG signals data readiness:
```python
from airflow.sdk import Asset

my_asset = Asset("s3://prod-bucket/finance/daily_output/")

@task(outlets=[my_asset])
def produce_output():
    # write data to S3
    ...
```

Downstream DAG triggers on asset update:
```python
with DAG(dag_id="downstream_consumer", schedule=[my_asset]):
    ...
```

The downstream DAG triggers automatically when the upstream DAG marks the asset as updated — no polling, no shared DB required [B2].

## Cross-Deployment Complication

If the two DAGs live in **different Astro Deployments** (isolated metadata DBs), `ExternalTaskSensor` cannot natively reach across Deployments because it queries the local metadata DB. Options:

1. **REST-based bridge**: Use a custom sensor that calls the upstream Deployment's REST API to check DAG run status (authenticated HTTP polling).
2. **Shared sentinel location**: Upstream writes a completion flag to a shared S3 path or database; downstream uses an `S3KeySensor` or DB sensor to detect it — equivalent to the old sentinel-file pattern.

## Sources

[B1] Broadcom AutoSys Documentation — Cross-instance `CHANGE_STATUS` events, remote Event Server communication (accessed 2026-08-11)
[B2] Astronomer Learn — Implement cross-DAG dependencies (`ExternalTaskSensor`, `TriggerDagRunOperator`, dataset/asset-driven scheduling as the three implementation patterns): https://www.astronomer.io/docs/learn/cross-dag-dependencies#implement-cross-dag-dependencies (tier 1, added on doc-verification review); cross-deployment dependencies specifically (Astro Alerts and Airflow Asset REST triggering, since `ExternalTaskSensor`/`TriggerDagRunOperator` only work within one Deployment): https://www.astronomer.io/docs/astro/best-practices/cross-deployment-dependencies (tier 1, added on doc-verification review)
