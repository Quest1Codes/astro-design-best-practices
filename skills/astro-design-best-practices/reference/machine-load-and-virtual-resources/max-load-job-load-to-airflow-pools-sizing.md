# max_load/job_load Weighted Machine Queuing → Airflow Pools Sizing Design

AutoSys's `max_load` and `job_load` implement a weighted concurrency model at the machine level. Each agent machine has a `max_load` value (the total capacity in arbitrary units), and each job has a `job_load` value (the units it consumes when running). When the sum of running job `job_load` values on a machine would exceed `max_load`, incoming jobs enter `QUE_WAIT` state [B1]. Critically, these units have no fixed relationship to physical CPU or memory — they are purely a scheduling weight system.

Airflow's **Pools** are the direct equivalent: a Pool has a total slot count (capacity), and each task consumes one or more slots (`pool_slots`).

## Concept Mapping

{syn: AutoSys `max_load` → Airflow Pool total slots; AutoSys `job_load` → Airflow `pool_slots` parameter}

| AutoSys Concept | Airflow Equivalent | Notes |
|---|---|---|
| **`max_load` on a machine** | **Pool's total slot count** | The upper limit of concurrent weighted units [B2]. |
| **`job_load` on a job** | **`pool_slots` parameter on a task** | Default `pool_slots=1`; set higher for "heavier" tasks [B2]. |
| **`QUE_WAIT` status** | Task in `queued` state (pool exhausted) | Task waits until enough slots free up [B2]. |
| **`priority: 0` (bypass queuing)** | `priority_weight` (higher value → picked first) | Airflow uses relative priority ordering, not a bypass flag [B2]. |

## Sizing Formula

If the legacy AutoSys machine had:
- `max_load = 100`
- Heavy jobs with `job_load = 20` (5 can run simultaneously)
- Light jobs with `job_load = 5` (up to 20 can run simultaneously)

Create a Pool with **100 slots**, assign `pool_slots=20` to heavy tasks and `pool_slots=5` to light tasks. The relative throttling ratio is preserved.

```python
heavy_task = BashOperator(
    task_id="heavy_etl",
    bash_command="etl_job.sh",
    pool="machine_A_pool",
    pool_slots=20,   # Equivalent to job_load=20
)

light_task = BashOperator(
    task_id="light_check",
    bash_command="check.sh",
    pool="machine_A_pool",
    pool_slots=5,    # Equivalent to job_load=5
)
```

## Pool Management

- Create Pools via **Airflow UI → Admin → Pools** or CLI: `airflow pools set <pool_name> <slots> "<description>"` [B2].
- Manage Pools as Infrastructure as Code: define them in your Deployment's Terraform or via the Astro API at Deployment creation time [B2].
- The **`default_pool`** in Airflow has 128 slots by default and applies to all tasks not explicitly assigned to a named pool. Do not rely on `default_pool` for throttling — create named pools for each resource group [B2].

## Sources

[B1] Broadcom AutoSys Documentation — `max_load` and `job_load` JIL attributes, `QUE_WAIT` status when machine capacity exceeded, arbitrary unit definition (accessed 2026-08-11)
[B2] Apache Airflow Docs — Pools, `pool_slots` parameter, `priority_weight`, `airflow pools set` CLI command (accessed 2026-08-11)
