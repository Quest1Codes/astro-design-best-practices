# QUE_WAIT Visibility and Queue-Depth Monitoring → Airflow Queued-State Observability

In AutoSys, `QUE_WAIT` is an explicit, named job status that appears in the UI and `autorep` output — it tells an operator immediately that a specific job is waiting because the target machine has no available load capacity. The operator can also use `autorep -Q <job_name> -n` to see *why* the job is queued (which machine, which resource) [B1].

Airflow's `queued` state is its equivalent — but the visibility tooling is different and requires deliberate instrumentation.

## Status Mapping

{syn: AutoSys `QUE_WAIT` → Airflow task `queued` state}

| AutoSys | Airflow | Notes |
|---|---|---|
| **`QUE_WAIT` status** | Task state: `queued` | Visible in the Airflow UI DAG Run view and Task Instance list |
| **`autorep -Q -n` (why is it queued?)** | **Admin → Pools** (check pool exhaustion) + Worker logs | No single equivalent command; requires two checks [B2]. |
| **Machine-level queue depth** | `executor.queued_tasks` metric | Published to StatsD/Prometheus by Airflow scheduler [B2]. |
| **`CHANGE_PRIORITY` to expedite** | `priority_weight` (set higher value on the task) | Airflow uses relative priority ordering in the queued task list [B2]. |

## Diagnosing Why a Task is Stuck in `queued`

A task stays `queued` in Airflow for one of three primary reasons:

1. **Pool exhausted**: All slots in the assigned Pool are occupied. Check **Admin → Pools** in the Airflow UI. The pool's "Running" count equals the total slot count.
2. **Worker capacity exhausted**: No worker has an available slot (`worker_concurrency` limit hit). For Astro, check the Deployment Analytics for worker CPU/memory saturation; autoscaler may not have spun up yet.
3. **Scheduler issue**: The scheduler itself is unhealthy (heartbeat lag). Check `scheduler.heartbeats` metric — a drop to zero indicates scheduler is not processing the queue [B2].

## Key Observability Metrics

| Metric | What It Signals | Source |
|---|---|---|
| `executor.queued_tasks` | Tasks submitted to executor but not yet picked up by a worker | Airflow StatsD/Prometheus [B2] |
| `dagrun.schedule_delay` | Time between scheduled start and actual start; high value = scheduler lag | Airflow StatsD/Prometheus [B2] |
| `pool.open_slots.<pool_name>` | Available slots in a named pool; zero means all tasks will queue | Airflow StatsD/Prometheus [B2] |
| `scheduler.heartbeats` | Scheduler health; should be non-zero continuously | Airflow StatsD/Prometheus [B2] |

## Recommended Alerting Rules

Configure alerts on:
- `executor.queued_tasks > <threshold>` sustained for > 5 minutes → worker capacity issue.
- `pool.open_slots.<critical_pool> == 0` sustained for > 10 minutes → pool exhaustion event.
- `scheduler.heartbeats == 0` for > 30 seconds → scheduler down; high-severity alert.

On Astro, route these metrics to Datadog, Prometheus, or a compatible endpoint via the Deployment's **Metrics** configuration [B2].

## Sources

[B1] Broadcom AutoSys Documentation — `QUE_WAIT` status, `autorep -Q -n` for queue diagnosis, `CHANGE_PRIORITY` event (accessed 2026-08-11)
[B2] Apache Airflow Docs & Astronomer Docs — Task `queued` state, `executor.queued_tasks` metric, `pool.open_slots` metric, `scheduler.heartbeats`, StatsD metrics reference (accessed 2026-08-11)
