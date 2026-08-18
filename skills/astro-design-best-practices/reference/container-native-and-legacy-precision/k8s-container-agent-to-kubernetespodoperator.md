# AutoSys Kubernetes/OpenShift Container-Agent Feature Parity → KubernetesPodOperator Design

AutoSys has a native Kubernetes/OpenShift job type that submits containerized workloads directly to a K8s cluster via the Kubernetes API — no traditional agent process needs to run inside the container. AutoSys defines a "Connection Profile" pointing to the cluster's API endpoint; the Kubernetes job type then creates a Kubernetes Job object to run the container [B1].

Airflow's `KubernetesPodOperator` (KPO) is the direct functional equivalent — it dynamically creates a Kubernetes Pod per task execution using the Kubernetes API.

## Feature Parity Mapping

{syn: AutoSys Kubernetes job type → Airflow `KubernetesPodOperator`; AutoSys Connection Profile (cluster endpoint) → Kubernetes Connection (`kubernetes_conn_id`)}

| AutoSys K8s Feature | Airflow KPO Equivalent |
|---|---|
| **K8s job type** | `KubernetesPodOperator` |
| **Connection Profile (cluster API URL + auth)** | `kubernetes_conn_id` in KPO (or in-cluster config) |
| **Container image** | `image` parameter |
| **Container command / args** | `cmds` and `arguments` parameters |
| **Namespace** | `namespace` parameter |
| **Resource limits (CPU/memory)** | `container_resources` with `k8s.V1ResourceRequirements` |
| **Environment variables** | `env_vars` parameter |
| **Pull policy** | `image_pull_policy` parameter |

## KubernetesPodOperator Pattern

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

run_containerized_job = KubernetesPodOperator(
    task_id="run_finance_etl",
    image="company-registry/finance-etl:2026.08",
    cmds=["python", "-m", "etl.main"],
    arguments=["--batch-date", "{{ ds }}"],
    namespace="airflow-jobs",
    name="finance-etl-{{ ds_nodash }}",   # Pod name must be unique per run
    image_pull_policy="Always",
    container_resources=k8s.V1ResourceRequirements(
        requests={"cpu": "1", "memory": "2Gi"},
        limits={"cpu": "2", "memory": "4Gi"},
    ),
    env_vars=[k8s.V1EnvVar(name="ENV", value="production")],
    get_logs=True,
    do_xcom_push=False,
)
```

## Key Differences from AutoSys K8s Job Type

| Aspect | AutoSys K8s Job Type | Airflow KPO |
|---|---|---|
| **Execution unit** | Kubernetes Job (manages pod restart) | Kubernetes Pod (KPO handles retry logic) |
| **Result capture** | External — job exit code | XCom via `/airflow/xcom/return.json` in the container |
| **Failure handling** | AutoSys retries at job level | Airflow `retries` parameter on operator |
| **Log streaming** | Via AutoSys log capture | `get_logs=True` streams to Airflow task logs |

## Sources

[B1] Broadcom AutoSys Documentation — Kubernetes/OpenShift job type, Connection Profile for cluster API endpoint, native K8s Job object creation (accessed 2026-08-18)
[B2] Apache Airflow Docs / CNCF Kubernetes Provider — `KubernetesPodOperator`, `container_resources`, `env_vars`, `get_logs`, `do_xcom_push`, `kubernetes_conn_id` (accessed 2026-08-18)
