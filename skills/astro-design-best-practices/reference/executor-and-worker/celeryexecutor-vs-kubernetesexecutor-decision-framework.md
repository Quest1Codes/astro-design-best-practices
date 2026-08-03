# CeleryExecutor vs. KubernetesExecutor Decision Framework

AutoSys dispatches every job to a named `machine:` — a persistent agent process on a specific host. Airflow's executors replace that model entirely; neither Celery nor Kubernetes workers are "a specific machine" in the AutoSys sense, and the choice between them is an architecture decision made once per estate (or per worker queue — see `worker-queue-segregation...md`), not per job.

## Core mechanics

- **CeleryExecutor**: a queued executor — tasks go to a Celery broker (e.g. Redis) and are picked up by a pool of long-running Celery worker processes [F1].
- **KubernetesExecutor**: a containerized executor — every task instance runs in its own individual Kubernetes Pod, created and torn down per task [F1].
- CeleryExecutor requires additional infrastructure (a broker); KubernetesExecutor doesn't need a broker but requires cluster access [F1].
- **When CeleryExecutor fits better**: task start-up time matters, and tasks don't need runtime isolation or heavy dedicated resources [F1].
- **When KubernetesExecutor fits better**: tasks need runtime isolation (no competing for CPU/memory with other tasks, since each runs in its own pod) or are resource-intensive with per-task CPU/memory control needed [F1].
- {syn: F1} On genuinely bursty workloads, this difference implies a resource-utilization advantage for KubernetesExecutor: Celery requires a fixed pool of long-running workers regardless of whether there's work to do, while Kubernetes pods only exist while a task runs. (Corrected per Critic pass: this was previously cited to [F2] as if that source stated the comparison directly — it doesn't; F2 discusses per-pod startup overhead and, in one place, argues the *opposite* emphasis, that CeleryExecutor is more efficient "at super high volume since it can run multiple tasks on a single worker." The bursty-workload conclusion above is this file's own synthesis from F1's core mechanics, not an independent empirical finding from F2 — treat it as reasoned inference, not a settled comparative benchmark.)
- **`CeleryKubernetesExecutor`**: both executors run simultaneously on the same Deployment; a task's `queue` attribute determines which one handles it — tasks default to Celery workers, but a task assigned to the `kubernetes` queue runs in its own pod instead [F3].

## {syn: F1,F2} Decision table for an AutoSys estate

| Signal from the source estate | Recommendation |
|---|---|
| Most jobs are short, high-frequency, similar resource footprint (typical AutoSys `CMD` jobs) [F1] | CeleryExecutor as the default — start-up latency matters more than per-job isolation at this profile. |
| A meaningful subset of jobs were pinned to specific high-memory/high-CPU machines via `machine:` [F1] | KubernetesExecutor (or `CeleryKubernetesExecutor` routing just that subset — see `hybrid-executor-strategy.md`) for that subset, since per-task resource isolation is exactly what dedicated-machine pinning was approximating in AutoSys. |
| The estate's job volume is highly bursty (heavy overnight batch, near-idle daytime) {syn: F1} | KubernetesExecutor (or the Kubernetes-routed portion of a hybrid setup) avoids the idle-worker-pool cost during low-volume periods, per the reasoning above — not an independently benchmarked claim, see the corrected note in "Core mechanics." |
| Steady, predictable volume across the day | CeleryExecutor's fixed worker pool is not a material cost disadvantage here, and its lower per-task start-up latency is a genuine benefit. |

## Sources

- [F1] Astronomer Docs — Apache Airflow Executors (CeleryExecutor vs. KubernetesExecutor comparison): https://www.astronomer.io/docs/learn/airflow-executors-explained (tier 1)
- [F2] Astronomer Blog — The New KubernetesExecutor: https://www.astronomer.io/blog/the-new-kubernetesexecutor/ (tier 1) — corrected per Critic pass: covers per-pod startup overhead and notes CeleryExecutor is more efficient "at super high volume since it can run multiple tasks on a single worker"; does **not** state the bursty-workload resource-utilization comparison this file previously attributed to it.
- [F3] Apache Airflow docs — CeleryKubernetesExecutor (`queue`-based routing between the two executors): https://airflow.apache.org/docs/apache-airflow-providers-celery/stable/celery_kubernetes_executor.html (tier 2)
