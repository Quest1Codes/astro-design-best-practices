# Scheduler HA: What Astro Provides vs. What You Must Design

AutoSys's HA model required explicit architectural planning: a **primary** scheduler, a **shadow** scheduler, a **tie-breaker**, and dual Event Servers — all carefully configured to prevent split-brain. Astro's model collapses most of this complexity into a managed platform capability. Understanding exactly what is provided for free vs. what still requires explicit design decisions prevents over-engineering in some areas and dangerous blind spots in others.

## What AutoSys Required (The Baseline)

{syn: AutoSys primary/shadow/tie-breaker → Astro multi-scheduler replicas}

| AutoSys Concept | Role | What Replaced It in Airflow/Astro |
|---|---|---|
| **Primary Scheduler** | Active job dispatcher | Airflow Scheduler replica 1 (active-active) [B1] |
| **Shadow Scheduler** | Standby, promotes on primary failure | Additional Airflow Scheduler replicas [B1] |
| **Tie-Breaker** | Prevents split-brain in dual Event-Server configs | Eliminated — resolved by Airflow's distributed leader-election via the metadata DB [B1] |
| **Dual Event Servers** | HA for the job state database | Managed PostgreSQL with multi-AZ failover (on Astro Cloud) [B2] |

## What Astro Provides for Free

- **Active-Active Scheduler Model**: Unlike AutoSys's Active-Passive primary/shadow model, Airflow's schedulers run in an **active-active** configuration. Multiple replicas share the scheduling workload concurrently. There is no "promotion" process on failure — other replicas continue operating [B1].
- **Kubernetes-managed Restarts**: Scheduler pods are managed by Kubernetes. If a pod crashes, the Kubernetes scheduler restarts it automatically [B1].
- **No Tie-Breaker Required**: Airflow's leader election uses database row-level locking on the metadata DB, eliminating the need for a separate tie-breaker process [B1].
- **Multi-AZ Data Plane Resilience**: The data plane is built to withstand single-AZ failures automatically, without user intervention [B2].

## What Still Requires Explicit Design Decisions

- **Number of Scheduler Replicas**: Astro does not auto-scale schedulers. You must choose the appropriate replica count based on your DAG parse volume and task throughput. Astronomer recommends starting with 2 replicas for production HA [B1].
- **Scheduler Resource Sizing**: Each scheduler replica requires memory and CPU allocation. Under-provisioning in large estates (e.g., post-AutoSys migrations with thousands of DAGs) leads to parse-loop degradation, not clean failures.
- **Metadata DB Resilience**: On **Astro Private Cloud** (self-hosted), you are responsible for the HA configuration of the underlying PostgreSQL instance (e.g., RDS Multi-AZ, Cloud SQL HA) [B3]. On Astro Cloud (managed), this is handled for you.
- **DAG Idempotency**: The active-active model means a task could theoretically be triggered twice if a scheduler replica fails mid-dispatch. DAGs **must** be idempotent to avoid data duplication in failure scenarios [B4].

## Sources

[B1] Astronomer Docs — Scheduler HA and active-active architecture (accessed 2026-08-10)
[B2] Astronomer Docs — Astro data plane resilience and multi-AZ design (accessed 2026-08-10)
[B3] Astronomer Docs — Astro Private Cloud / Software database HA responsibilities (accessed 2026-08-10)
[B4] Apache Airflow Docs — Idempotency best practices (accessed 2026-08-10)
