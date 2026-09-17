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

- **Number of Scheduler Replicas**: Astro does not auto-scale schedulers, and the replica model differs by deployment type — this is not one uniform "choose a number" decision. On **Astro Private Cloud/Hybrid**, replica count is a real, configurable sizing decision (up to 4 by default) based on DAG parse volume and task throughput [B5]. On **Astro Hosted**, there is no configurable replica count: a Deployment runs a single scheduler by default, and the **High Availability** toggle is a binary on/off switch to exactly two schedulers — there is no "starting with 2 and scaling to 4" path on Hosted [B6]. See `reference/scheduler-and-dag/scheduler-ha-and-leader-election.md` for the full platform split.
- **Scheduler Resource Sizing**: Each scheduler replica requires memory and CPU allocation. Under-provisioning in large estates (e.g., post-AutoSys migrations with thousands of DAGs) leads to parse-loop degradation, not clean failures.
- **Metadata DB Resilience**: On **Astro Private Cloud** (self-hosted), you are responsible for the HA configuration of the underlying PostgreSQL instance (e.g., RDS Multi-AZ, Cloud SQL HA) [B3]. On Astro Cloud (managed), this is handled for you.
- **DAG Idempotency**: The active-active model means a task could theoretically be triggered twice if a scheduler replica fails mid-dispatch. DAGs **must** be idempotent to avoid data duplication in failure scenarios [B4].

## Sources

[B1] Astronomer Docs — Airflow components, high availability (active-active scheduler model; Astro High Availability toggle): https://www.astronomer.io/docs/learn/airflow-components#high-availability (tier 1, resolved on citation review — closes the earlier `NEEDS_EXEC_CHECK`)
[B2] Astronomer Docs — Resilience (Astro control/data plane AZ design, automated backups, cross-region DR): https://www.astronomer.io/docs/astro/resilience (tier 1, resolved on citation review — closes the earlier `NEEDS_EXEC_CHECK`)
[B3] Astronomer Docs — Private Cloud database architecture, PostgreSQL replication ("Astronomer doesn't recommend using internal PostgreSQL instance... use an externally managed database service"): https://www.astronomer.io/docs/astro-private-cloud/v-2-x/database-architecture#postgresql-replication (tier 1, resolved on citation review — closes the earlier `NEEDS_EXEC_CHECK`)
[B4] Apache Airflow Docs — Idempotency best practices (no Astronomer Docs match found on this pass — this is Apache Airflow OSS content not indexed in the Astronomer docs MCP; verify against airflow.apache.org's best-practices guide directly rather than treating this as closed)
[B5] Astronomer Docs — Airflow system components, "Horizontal scaling" (Astro Private Cloud/Hybrid): Scheduler supports up to 4 replicas by default: https://www.astronomer.io/docs/astro-private-cloud/v-2-x/airflow-system-components#horizontal-scaling (tier 1, added on platform-split review)
[B6] Astronomer Docs — Scheduler (Astro Hosted): single scheduler by default; High Availability toggle runs exactly two, not a configurable count: https://www.astronomer.io/docs/astro/deployment-resources#scheduler (tier 1, added on platform-split review)
