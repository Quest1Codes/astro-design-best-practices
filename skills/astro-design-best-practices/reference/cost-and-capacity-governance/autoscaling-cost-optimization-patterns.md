# Autoscaling Cost-Optimization Patterns

Astro's worker autoscaling is a managed, built-in capability — you do not configure KEDA manually on Astro Cloud. Understanding how the autoscaler behaves and how to design around its edge cases is essential for both cost optimization and pipeline reliability.

## How Astro Worker Autoscaling Works

- Workers scale based on the number of queued and running tasks in the Airflow metadata DB [B1].
- When task queues are empty, workers scale down to **zero** — you pay only for scheduler and webserver compute during idle periods [B1].
- You set **minimum** and **maximum** worker counts per worker queue in the Deployment configuration [B1].
- KEDA is the underlying mechanism on Astro's Kubernetes infrastructure, but it is fully managed — no user configuration required [B1].

> **Note for Astro Private Cloud / Self-Hosted**: If you manage your own Kubernetes deployment, enable KEDA via `workers.celery.keda.enabled=true` in your Helm values. Do **not** enable both KEDA and HPA for the same workload — they will compete and cause erratic scaling [B2].

## Cost-Optimization Patterns

### Pattern 1: Worker Queue Segregation

Separate long-running, expensive tasks from short, lightweight tasks into **dedicated worker queues** [B1]:

| Queue | Worker Size | Min Workers | Max Workers | Use Case |
|---|---|---|---|---|
| `default` | A5 (small) | 0 | 5 | Short tasks, sensors, notifications |
| `heavy` | A20 (large) | 0 | 2 | Spark submits, ML inference, large data loads |

Without segregation, a single long-running task on a large worker blocks the queue for small tasks, and the autoscaler keeps expensive workers alive unnecessarily.

### Pattern 2: Aggressive Scale-Down + Idempotent Tasks

Setting `min_workers=0` on all queues maximizes cost savings but requires that **all tasks be idempotent** [B1][B2]:

- If a worker is terminated mid-task (during scale-down), the task is marked as failed and retried.
- A non-idempotent task retried after partial completion may cause data duplication.
- Design tasks with `INSERT OR REPLACE`, `UPSERT`, or pre-execution existence checks.

### Pattern 3: Dedicated Queue for Long-Running Tasks (No Scale-Down)

For tasks that cannot be safely interrupted (e.g., a 6-hour data load):
- Set `min_workers=1` for the long-running queue to prevent scale-down during execution [B1].
- Accept the cost of keeping that queue warm as a business requirement, not a design failure.

## Key Cost Lever: Deferrable Operators

Deferrable Operators release worker slots while waiting for external conditions (API completion, file arrival). This means you do not need to keep a large worker alive and blocking during long polling waits. Use Deferrable Operators wherever the task is I/O-bound rather than CPU/memory-bound [B1].

## Sources

[B1] Astronomer Docs — Worker autoscaling, scale-to-zero behavior, worker queue min/max configuration, Deferrable Operators (accessed 2026-08-11)
[B2] Apache Airflow Docs — KEDA configuration (`workers.celery.keda.enabled`), HPA/KEDA conflict warning (accessed 2026-08-11)
