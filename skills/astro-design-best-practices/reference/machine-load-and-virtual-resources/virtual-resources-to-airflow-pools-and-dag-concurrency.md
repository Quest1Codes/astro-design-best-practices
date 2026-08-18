# Named Virtual Resources (Semaphore-Style Throttling) → Airflow Pools/max_active_tis_per_dag

AutoSys "virtual resources" are named, abstract concurrency tokens — they are entirely independent of machine load. A virtual resource named `DB_CONNECTIONS` with a count of `10` means that at most 10 jobs holding that resource can run simultaneously, regardless of which machines they run on or what `max_load` those machines have [B1]. This is a **semaphore pattern**: the resource is not a physical thing; it is a named counter.

This is the purest mapping to Airflow Pools. A Pool is exactly a named concurrency counter.

## Concept Mapping

{syn: AutoSys virtual resource → Airflow Pool (named concurrency semaphore)}

| AutoSys Virtual Resource Concept | Airflow Equivalent | Notes |
|---|---|---|
| **Named virtual resource** (e.g., `DB_CONNECTIONS`) | **Named Airflow Pool** (e.g., `db_connections_pool`) | One-to-one [B2]. |
| **Virtual resource count** (e.g., `10`) | **Pool slot count** (e.g., `10`) | The concurrency ceiling [B2]. |
| **Job acquiring the resource** | Task with `pool="db_connections_pool"` | Default `pool_slots=1` — consumes 1 token [B2]. |
| **Global throttle (shared across all machines)** | Pool is global across the Deployment | All tasks in the Deployment share the same Pool counter [B2]. |

## Airflow Additional Controls (No AutoSys Equivalent)

AutoSys virtual resources throttle only at the resource level. Airflow provides two additional concurrency control levers that have no AutoSys virtual resource equivalent:

| Parameter | Scope | Effect |
|---|---|---|
| **`max_active_tasks_per_dag`** | Per-DAG | Limits total concurrent tasks *within one DAG* across all its active runs [B2]. |
| **`max_active_runs_per_dag`** | Per-DAG | Limits how many simultaneous DAG runs can be active for one DAG [B2]. |

Use these in combination with Pools:
- **Pool**: throttles access to a shared external resource (database connections, API rate limit).
- **`max_active_tasks_per_dag`**: prevents a single DAG from monopolizing the worker fleet.
- **`max_active_runs_per_dag`**: prevents schedule backfill from spawning too many concurrent runs during catch-up.

## Migration Decision Tree

```
Is the AutoSys virtual resource protecting a shared EXTERNAL resource
(database, API, message queue)?
  → YES: Create a named Airflow Pool matching the resource name and count.

Is the resource protecting against DAG-internal runaway parallelism?
  → YES: Use max_active_tasks_per_dag instead of (or in addition to) a Pool.

Does the same resource apply to ALL jobs across all instances/domains?
  → YES: The Pool is global to the Deployment — all DAGs in the Deployment share it.
       Consider whether the throttle should be at Deployment level (Pool)
       or domain level (Pool per domain with appropriate slot count).
```

## Sources

[B1] Broadcom AutoSys Documentation — Virtual resource definition (named semaphore counter, independent of machine load), per-job resource acquisition (accessed 2026-08-11)
[B2] Apache Airflow Docs — Pools, `max_active_tasks_per_dag`, `max_active_runs_per_dag` DAG parameters (accessed 2026-08-11)
