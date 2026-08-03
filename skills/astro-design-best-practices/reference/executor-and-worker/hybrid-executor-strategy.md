# Hybrid Executor Strategy (Celery + Kubernetes for Outliers)

Most AutoSys estates have a large mass of similar, lightweight jobs and a small number of genuine outliers (unusually heavy, needing isolation, or needing specific hardware). Forcing the whole estate onto one executor to accommodate the outliers — or accepting the outliers' poor fit under a Celery-only setup — are both worse than routing the minority of unusual jobs differently.

## Core mechanics — two distinct hybrid mechanisms, not one

- **`CeleryKubernetesExecutor`**: a single Deployment-wide executor setting that runs both CeleryExecutor and KubernetesExecutor simultaneously; a task's `queue` attribute determines which one handles it — default is Celery, tasks assigned the `kubernetes` queue run in their own pod [F1]. This is an *executor-level* choice.
- **`KubernetesPodOperator`**: a specific operator that runs its task in a dedicated Kubernetes pod *regardless of which executor the DAG's other tasks use* — it doesn't require `CeleryKubernetesExecutor` at all, since it manages its own pod directly rather than relying on the executor to route it [F2]. This is an *operator-level* choice, usable even under a pure CeleryExecutor Deployment.

## {syn: F1,F2} Decision guidance — which hybrid mechanism fits

| Signal | Recommendation |
|---|---|
| A whole functional category of jobs (an entire worker queue's worth, per `worker-queue-segregation-mirroring-machine-groups.md`) needs pod-level isolation | `CeleryKubernetesExecutor`, routing that queue's tasks to the `kubernetes` queue [F1] — this is a queue-level routing decision, matching an existing structural grouping. |
| A handful of individual outlier tasks scattered across otherwise-Celery-appropriate DAGs need pod isolation, without justifying a whole separate queue | `KubernetesPodOperator` used directly for just those specific tasks [F2] — no executor-level change needed, no new worker queue to provision and tune. |
| The estate is small enough that CeleryExecutor alone is sufficient for everything | Neither — don't introduce Kubernetes-executor complexity (a second execution path to operate, monitor, and reason about) without an actual population of outlier jobs that need it. |

## What this replaces from AutoSys

AutoSys handled "most jobs run anywhere, a few need a specific machine" the same way regardless of how many outliers there were — every job got an explicit `machine:` assignment, uniform mechanism, no scale-dependent choice. Airflow's two hybrid mechanisms exist precisely because that uniformity isn't free here: `KubernetesPodOperator` per-task is the lower-overhead choice for a handful of outliers, while `CeleryKubernetesExecutor`'s queue-level routing is the better fit once "a few outliers" becomes "a whole functional category." Making this choice deliberately, based on actual outlier count and whether they cluster into an existing queue grouping, is itself new work the AutoSys-side design never had to do.

## Sources

- [F1] Apache Airflow docs — CeleryKubernetesExecutor (`queue`-based routing, default-to-Celery behavior): https://airflow.apache.org/docs/apache-airflow-providers-celery/stable/celery_kubernetes_executor.html (tier 2)
- [F2] Apache Airflow docs — Kubernetes Executor / `KubernetesPodOperator` (operator-level pod execution, independent of the DAG's configured executor): https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/kubernetes_executor.html (tier 2)
