# Executor and autoscaling

## The decision this reference supports

Airflow needs one executor choice for the target Deployment (predominantly KubernetesExecutor or CeleryExecutor, possibly mixed via `KubernetesPodOperator` for specific tasks under either). Pick it from the workload shape recorded in the core skill's `manifest.json`, not from whatever pattern the source AutoSys-on-k8s deployment happened to use — a custom job-launching approach on the source side is not necessarily evidence of what Airflow should do, since AutoSys's own job-to-pod model doesn't map 1:1 onto either Airflow executor.

## Signals to pull from `manifest.json`

- **Task count and box size**: many small, short command jobs per box → CeleryExecutor (or KubernetesExecutor with care taken on per-task pod startup overhead) tends to fit better than spinning a full pod per tiny task.
- **Resource heterogeneity**: jobs with wildly different resource needs (one job needs 8GB RAM, another needs 256MB) → KubernetesExecutor's per-task pod sizing is a natural fit; CeleryExecutor's fixed worker sizing wastes resources on the small jobs or starves the large ones.
- **Isolation requirements**: jobs needing strict dependency isolation (conflicting Python/library versions between jobs) → KubernetesExecutor (or `KubernetesPodOperator` per task) gives per-task images; CeleryExecutor workers share one image per queue.
- **Burstiness**: a nightly batch window with high concurrency followed by long idle periods → favors autoscaling (KEDA-backed CeleryExecutor workers, or KubernetesExecutor's natural scale-to-zero-per-task characteristic) over a fixed-size pool.

## What the source estate's autoscaling tells you (and doesn't)

A custom autoscaler or HPA object found in the k8s export tells you what the *source* needed to scale (agent pod count, or a custom job-runner deployment) — it does not tell you what the *target* needs, because the unit being scaled is different (AutoSys agent pods vs. Airflow workers/task pods). Use it only as evidence of the workload's burstiness pattern (when did it scale up, by how much, how often), then apply that pattern to sizing Airflow's own autoscaling (KEDA ScaledObject watching queue depth, for CeleryExecutor; or KubernetesExecutor's inherent per-task scaling, tuned via parallelism/pool settings).

## Mixed executor is normal

Different boxes/DAGs can reasonably use different executors or per-task overrides (`executor_config` on the KubernetesExecutor, or task-level `queue=` under Celery) — don't force one estate-wide executor choice if the workload genuinely has both a large population of small, homogeneous jobs (Celery-friendly) and a smaller population of large or isolation-sensitive jobs (Kubernetes-friendly). Record the choice and its rationale per domain/box in the report, same discipline as the core skill's condition-string equivalence rows.

## Validating the choice

Don't finalize an executor/autoscaling choice from the workload-shape analysis alone — pilot it (Phase 3 in SKILL.md) against a real slice of the migrated DAGs and confirm actual pod startup latency, queue time, and resource utilization match expectations before committing the whole estate to one model.
