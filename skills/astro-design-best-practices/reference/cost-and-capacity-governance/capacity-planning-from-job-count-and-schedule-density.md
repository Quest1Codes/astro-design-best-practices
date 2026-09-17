# Capacity Planning from Job Count and Schedule Density

Migrating from AutoSys means translating "N boxes, M jobs, K calendar schedules" into Airflow compute requirements. This is not a 1:1 mapping. AutoSys was centralized (one scheduler for all); Airflow on Astro is deployment-isolated (each Deployment has its own scheduler and workers).

## Astronomer Unit (AU) Primer

**1 AU = 0.1 vCPU + 0.375 GiB memory** [B1].

All resource allocation on Astro (scheduler, webserver, triggerer, workers) is expressed in AUs. Understanding this baseline is prerequisite to capacity planning.

## Astro Deployment Size Guide (Official Templates)

{syn: AutoSys instance sizing → Astro Deployment template selection}

| Template | Approximate DAG Count | Notes |
|---|---|---|
| **Small** | ~50 DAGs | Single scheduler + single DAG Processor [B1]. |
| **Medium** | ~250 DAGs | Scheduler and DAG Processor are separated. Astronomer recommends **Medium as the minimum for production** [B1]. |
| **Large** | ~1,000 DAGs | Single scheduler; **1 DAG Processor pod, sized at 3 vCPU** — a resource-allocation figure, not a pod count. **Correction**: an earlier draft of this file described this as "3 DAG Processors" (i.e., 3 separate pods), which current docs don't support [B2]. |
| **Extra Large** | ~2,000 DAGs | Single scheduler + **2 separate DAG Processor pods** — this tier is the one that actually runs multiple Dag processor pods [B2]. |

> **Important**: These are starting templates, not hard limits. Monitor actual parse time and scheduler lag in Deployment Analytics and resize accordingly [B1].

## Schedule Density Impact on Scheduler

"Schedule density" = how many DAG runs are triggered per hour. A flat count of DAGs is misleading — 50 DAGs that all trigger at :00 of every hour creates a burst load very different from 50 DAGs spread evenly across the hour.

- For high schedule density (many DAG runs per minute), the scheduler's parse time is the primary bottleneck. Add DAG Processor replicas before adding more scheduler replicas [B1].
- Use Airflow's `AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL` to tune the parse frequency. Lowering this increases scheduler CPU usage [B1].

## Worker Capacity Planning

| Signal | Action |
|---|---|
| Workers frequently hitting memory limits | Upgrade worker type (e.g., A5 → A10 or larger AU size) [B1]. |
| Workers at high CPU saturation | Reduce `WORKER_CONCURRENCY` or upgrade worker type. |
| Queue depth growing faster than tasks complete | Increase maximum worker count in the queue autoscaling config [B1]. |
| Deferrable Operators used heavily | Monitor Triggerer pod. Default Triggerer handles ~1,000 concurrent triggers; add Triggerer replicas if exceeded [B1]. |

## Sources

[B1] Astronomer Docs — Deployment resources, Triggerer (default 1 replica, ~1000 concurrent trigger capacity): https://www.astronomer.io/docs/astro/deployment-resources#triggerer (tier 1, added on doc-verification review); AU definition (1 AU = 0.1 vCPU + 0.375 GiB): https://www.astronomer.io/docs/astro-private-cloud/v-0-37/configure-deployment#select-a-resource-strategy (tier 1, added on doc-verification review)
[B2] Astronomer Docs — Deployment resources, size options (Large = 1 Dag Processor pod at 3 vCPU; Extra Large = 2 Dag Processor pods): https://www.astronomer.io/docs/astro/deployment-resources#size-options (tier 1, added on doc-verification review — corrects the "3 DAG Processors" claim for Large above)
