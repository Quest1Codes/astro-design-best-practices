# Node Affinity and Taints for Specialized Jobs

The closest AutoSys equivalent to Kubernetes node affinity/taints is `machine:` pinning to a specific host — but AutoSys pinning is a hard assignment (this job runs on this machine, full stop), while Kubernetes affinity/taints give a spectrum from soft preference to hard requirement, which is a genuinely more expressive tool than what it's replacing.

## Core mechanics

- **Node affinity** is a Pod property that attracts pods toward a set of nodes, expressible as either a preference (soft) or a hard requirement [F1].
- **Taints** are the inverse — applied to a *node*, they repel pods that don't explicitly tolerate them [F1].
- **Tolerations** are applied to a *pod*, allowing the scheduler to place it on a node with a matching taint — taints and tolerations work together so a node can refuse pods that don't declare compatibility with it [F1].
- For Airflow specifically, these are configured per-component (scheduler, workers, KubernetesExecutor pod template, individual triggerer, etc.) via `nodeSelector`/`affinity`/`tolerations`/`topologySpreadConstraints` settings, and per-task via `pod_override` in `executor_config` (same mechanism as resource requests/limits — see `per-task-resource-requests-and-limits.md`) [F2].

## {syn: F1,F2} Design guidance — translating `machine:` pinning

| AutoSys `machine:` pinning reason | Kubernetes translation |
|---|---|
| Job needs specialized hardware unavailable on general nodes (e.g. a specific chip family, local disk type) | **Taint the specialized node pool**, and give only the relevant tasks a matching **toleration** via `pod_override` — this is the closer match to AutoSys's hard-pin behavior, since untainted general nodes remain fully off-limits to non-tolerating tasks by default [F1]. |
| Job merely prefers a certain node pool for cost/locality reasons, but could run elsewhere if needed | **Node affinity as a soft preference**, not a taint/toleration pair — this preserves scheduling flexibility that a hard AutoSys `machine:` pin didn't have, and is usually the *better* outcome, not just an acceptable one, since it lets the scheduler use spare capacity elsewhere when the preferred pool is full. |
| Job needs isolation from noisy-neighbor tasks (a resource-isolation reason, not a hardware-capability reason) | This is better addressed by `per-task-resource-requests-and-limits.md`'s resource requests/limits than by node affinity — affinity/taints control *which nodes* a pod can land on, not how much of a node's resources it's guaranteed once there. |

## What NOT to do

Do not default to hard node affinity (`requiredDuringSchedulingIgnoredDuringExecution`) for every translated `machine:` pin just because AutoSys pinning was itself hard — most AutoSys machine pins existed for organizational/historical reasons (see `worker-queue-segregation-mirroring-machine-groups.md`'s classification table), not genuine hardware requirements, and forcing all of them into hard-affinity translations reintroduces AutoSys's own scheduling rigidity into a platform that doesn't need it.

## Sources

- [F1] Kubernetes official docs — Taints and Tolerations (mechanics, node affinity as preference vs. requirement): https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/ (tier 2 — foundational Kubernetes documentation, not Airflow-specific, but directly authoritative for this mechanism)
- [F2] Airflow community Helm chart docs (`airflow-helm/charts`) — per-component `nodeSelector`/`affinity`/`tolerations` configuration structure: https://github.com/airflow-helm/charts/blob/main/charts/airflow/docs/faq/kubernetes/affinity-node-selectors-tolerations.md (tier 3 — widely-used community Helm chart, not the official Apache Airflow Helm chart or Astronomer docs; the per-task `pod_override` mechanism itself is corroborated by `per-task-resource-requests-and-limits.md`'s tier-1 Astronomer citation, which uses the identical `executor_config`/`pod_override` pattern)
