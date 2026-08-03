# Concurrency Controls — Pools and `max_active_runs`

This is the Airflow-side mechanics companion to the AutoSys-side concepts covered in the `machine-load-and-virtual-resources` cluster (`max_load`/`job_load`/virtual resources) — this file covers what Airflow actually gives you to implement those concepts with.

## Core mechanics

- A **Pool** limits execution parallelism across an arbitrary set of tasks; pools are managed in the UI (Admin → Pools) with a name and a number of worker slots [F1].
- Each task occupies one pool slot by default, configurable via `pool_slots` if a task should count as "heavier" than others sharing the same pool [F1][F2].
- Tasks not explicitly assigned a pool go into `default_pool`, initialized with 128 slots [F1].
- **`max_active_runs`** is a *different* mechanism — it limits how many concurrent **DAG runs** (not tasks) a single DAG can have active at once; once the limit is hit, the scheduler stops creating new active runs for that DAG [F1][F3].
- `core.max_active_runs_per_dag` sets the same limit globally, as a default for DAGs that don't set their own [F1] (corrected citation per Critic pass — this specific setting name is stated on F1, not F3, which covers `pool_slots` mechanics only).

## {syn: F1,F2,F3} Design guidance — translating AutoSys's load concepts

- **AutoSys `n()` mutual-exclusion** (only one instance of this job/box running at a time) → `max_active_runs=1` on the DAG — this is a DAG-run-level control, matching `n()`'s "don't start another instance of *this*" semantics exactly.
- **AutoSys named virtual resources** (a semaphore shared across *multiple different* jobs, not just repeated instances of one job) → a Pool, not `max_active_runs` — a Pool is the only mechanism here that limits parallelism across a set of *different* tasks/DAGs sharing a scarce resource, since `max_active_runs` only governs one DAG's own run count.
- **AutoSys `max_load`/`job_load` weighted machine capacity** → `pool_slots` on a per-task basis within a Pool sized to the machine's original `max_load` capacity — a task with a high `job_load` value becomes a task with a higher `pool_slots` value, consuming proportionally more of the Pool's total slots.

## Sources

- [F1] Astronomer Docs — Airflow pools: https://www.astronomer.io/docs/learn/airflow-pools (tier 1)
- [F2] Apache Airflow docs — Pools (`pool_slots` mechanics): https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html (tier 2)
- [F3] Apache Airflow docs — Pools (`max_active_runs`/`core.max_active_runs_per_dag`): same as F2 (tier 2)
