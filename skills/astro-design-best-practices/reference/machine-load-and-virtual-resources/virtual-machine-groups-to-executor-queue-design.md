# Virtual Machine (Load-Balancing Machine-Group) Definitions → KubernetesExecutor/CeleryExecutor Queue-Group Design

AutoSys "virtual machines" (also called machine groups) are named, logical groupings of real agent machines. When a job is submitted to a virtual machine, AutoSys's scheduler selects one of the underlying real machines based on `max_load`/`job_load` capacity rules — effectively providing load-balanced job routing across a homogeneous pool of agents [B1].

In Airflow, this routing concept maps to **worker queues** (CeleryExecutor) or **Kubernetes node targeting** (KubernetesExecutor), depending on the executor.

## Concept Mapping

{syn: AutoSys virtual machine (machine group) → Airflow worker queue (CeleryExecutor) or node affinity (KubernetesExecutor)}

| AutoSys Concept | Airflow Equivalent | Notes |
|---|---|---|
| **Virtual machine** (logical group name) | **Named worker queue** (e.g., `"heavy_compute"`) | Tasks targeted to a named queue are routed to workers listening on that queue [B2]. |
| **Real machines in the group** | **Worker pods assigned to the queue** | For Celery: workers launched with `--queue heavy_compute`. For K8s: node selector/affinity labels. |
| **AutoSys routing by `max_load`** | **Celery broker distributes to available workers** | The message broker delivers to whichever worker has capacity; you control capacity via `worker_concurrency` [B2]. |
| **All jobs on virtual machine** | **Task `queue` parameter** | `queue="heavy_compute"` in the operator routes the task [B2]. |

## CeleryExecutor Queue-Group Pattern

```python
# Route a compute-heavy task to the "heavy" queue (worker group)
heavy_etl = BashOperator(
    task_id="heavy_etl_job",
    bash_command="etl_main.sh",
    queue="heavy_compute",    # Routes to workers in the heavy_compute worker group
    pool="etl_pool",
    pool_slots=5,
)

# Route a lightweight task to the default queue
light_check = PythonOperator(
    task_id="pre_flight_check",
    python_callable=check_function,
    queue="default",
)
```

Workers for the `heavy_compute` queue are started with:
```bash
airflow celery worker --queues heavy_compute
```

## KubernetesExecutor Pod Targeting

For KubernetesExecutor, routing to specific node groups uses `executor_config` with pod spec overrides:

```python
heavy_task = BashOperator(
    task_id="heavy_task",
    executor_config={
        "pod_override": k8s.V1Pod(
            spec=k8s.V1PodSpec(
                node_selector={"node-type": "compute-optimized"},
            )
        )
    },
)
```

This is the K8s equivalent of routing to a specific machine group in AutoSys.

## Executor Choice Decision

| AutoSys Pattern | Recommended Airflow Executor |
|---|---|
| Fixed pool of persistent agents; high task throughput; low cold-start tolerance | **CeleryExecutor** with named queues |
| Strong isolation per task; varied resource profiles; burst compute | **KubernetesExecutor** with node selectors |
| Mix of high-frequency light tasks + isolated heavy tasks | **CeleryKubernetesExecutor** hybrid |

On Astro, the underlying executor is managed — but worker queue segregation is fully configurable via Deployment worker queue settings [B2].

## Sources

[B1] Broadcom AutoSys Documentation — Virtual machine (machine group) definition, load-balanced job routing among real machines using `max_load`/`job_load` (accessed 2026-08-11)
[B2] Apache Airflow Docs — CeleryExecutor worker queues, `queue` parameter on operators, KubernetesExecutor `executor_config` and node selectors (accessed 2026-08-11)
