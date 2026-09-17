# Hybrid Execution Strategy (Outlier Isolation Within a Deployment)

Most AutoSys estates have a large mass of similar, lightweight jobs and a small number of genuine outliers (unusually heavy, needing isolation, or needing specific hardware). Forcing the whole estate onto one executor to accommodate the outliers — or accepting the outliers' poor fit under a single-executor setup — are both worse than routing the minority of unusual jobs differently.

## Correction — this file predates the Astro executor and overstated `CeleryKubernetesExecutor`'s standing

**This file originally framed `CeleryKubernetesExecutor` as a live, recommended mechanism.** A Critic-pass review found two problems with that, confirmed against current docs:

1. **`CeleryKubernetesExecutor` is not a selectable Deployment executor on Astro at all.** Astro's Deployment-executor options — via the Astro UI, CLI `--executor` flag, API `executor` parameter, or Terraform provider — are exactly three: **Astro, Celery, Kubernetes** [F4]. `CeleryKubernetesExecutor` doesn't appear as a fourth option anywhere in that list. It exists as an upstream Apache Airflow concept [F1], but nothing in Astro's own documentation describes configuring it on a Deployment; `NEEDS_EXEC_CHECK` if you need to confirm definitively whether a self-managed Astronomer Software install could still wire it in via custom Helm values.
2. **Astronomer's own docs separately describe it as legacy**: "Two statically coded hybrid executors exist, the CeleryKubernetes Executor and the LocalKubernetes Executor... these executors are rarely used and as of Airflow 2.10 no longer recommended" [F7].

Combined, that means the "queue-level routing via `CeleryKubernetesExecutor`" recommendation below is not a live option to design toward on Astro. It's kept in this file only as historical/upstream-Airflow context — do not recommend it for a new AutoSys migration.

## What to actually use instead, on Astro

- **The Astro executor (Airflow 3.x default)** already supports **worker queues with different worker types**, the same way Celery executor does [F5][F6] — this is the queue-level mechanism to reach for when "a whole functional category of jobs needs isolation or a different resource profile," the scenario the old `CeleryKubernetesExecutor` row below was meant to solve. Segregate that functional category into its own worker queue rather than reaching for a hybrid executor.
- **`KubernetesPodOperator`** remains correct and unaffected by any of the above — it runs its task in a dedicated Kubernetes pod *regardless of which executor the DAG's other tasks use* (Astro, Celery, or Kubernetes), because it manages its own pod directly rather than relying on the executor to route it [F2]. This is still the right mechanism for a handful of individual outlier tasks that don't justify a whole separate queue.

## Core mechanics — two distinct hybrid mechanisms, not one (original framing, `CeleryKubernetesExecutor` row now legacy-only — see correction above)

- **`CeleryKubernetesExecutor`** *(legacy Airflow concept, not a selectable Astro Deployment executor — see correction above)*: a single Deployment-wide executor setting that runs both CeleryExecutor and KubernetesExecutor simultaneously; a task's `queue` attribute determines which one handles it — default is Celery, tasks assigned the `kubernetes` queue run in their own pod [F1]. This is an *executor-level* choice.
- **`KubernetesPodOperator`**: a specific operator that runs its task in a dedicated Kubernetes pod *regardless of which executor the DAG's other tasks use* — it doesn't require `CeleryKubernetesExecutor` at all, since it manages its own pod directly rather than relying on the executor to route it [F2]. This is an *operator-level* choice, usable under any of Astro's three executors, including the Astro executor default.

## {syn: F1,F2,F5,F6} Decision guidance — which hybrid mechanism fits

| Signal | Recommendation |
|---|---|
| A whole functional category of jobs (an entire worker queue's worth, per `worker-queue-segregation-mirroring-machine-groups.md`) needs a different resource profile or isolation | On Astro: a dedicated **worker queue with its own worker type**, under the Astro executor or Celery executor [F5][F6] — not `CeleryKubernetesExecutor`, which isn't selectable on Astro. For genuine pod-level isolation specifically (not just a bigger worker), route that queue's tasks through `KubernetesPodOperator` or run the Deployment's executor as Kubernetes. |
| A handful of individual outlier tasks scattered across otherwise-fine DAGs need pod isolation, without justifying a whole separate queue | `KubernetesPodOperator` used directly for just those specific tasks [F2] — no executor-level change needed, no new worker queue to provision and tune. Works the same regardless of the Deployment's default executor. |
| The estate is small enough that the default executor alone is sufficient for everything | Neither — don't introduce a second execution path to operate, monitor, and reason about without an actual population of outlier jobs that need it. |

## What this replaces from AutoSys

AutoSys handled "most jobs run anywhere, a few need a specific machine" the same way regardless of how many outliers there were — every job got an explicit `machine:` assignment, uniform mechanism, no scale-dependent choice. Airflow's outlier-isolation mechanisms exist precisely because that uniformity isn't free here: `KubernetesPodOperator` per-task is the lower-overhead choice for a handful of outliers, while a dedicated worker queue (with its own worker type, or routed to Kubernetes) is the better fit once "a few outliers" becomes "a whole functional category." Making this choice deliberately, based on actual outlier count and whether they cluster into an existing queue grouping, is itself new work the AutoSys-side design never had to do.

## Sources

- [F1] Apache Airflow docs — CeleryKubernetesExecutor (`queue`-based routing, default-to-Celery behavior; upstream Airflow concept, kept for historical context — see correction above for why this isn't a live Astro recommendation): https://airflow.apache.org/docs/apache-airflow-providers-celery/stable/celery_kubernetes_executor.html (tier 2)
- [F2] Apache Airflow docs — Kubernetes Executor / `KubernetesPodOperator` (operator-level pod execution, independent of the DAG's configured executor): https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/kubernetes_executor.html (tier 2)
- [F4] Astronomer Docs — Deployment executor (Astro's only three selectable Deployment-executor options: Astro, Celery, Kubernetes — via UI, CLI `--executor`, API `executor`, or Terraform): https://www.astronomer.io/docs/astro/deployment-resources#deployment-executor and https://www.astronomer.io/docs/learn/airflow-executors-explained#configure-an-executor-on-astro (tier 1, added on Critic-pass review)
- [F5] Astronomer Docs — Astro executor overview (default for Airflow 3.x Deployments): https://www.astronomer.io/docs/astro/astro-executor#overview (tier 1, added on Critic-pass review)
- [F6] Astronomer Docs — Configure worker queues (per-queue worker type, usable under Astro or Celery executor): https://www.astronomer.io/docs/astro/configure-worker-queues (tier 1, added on Critic-pass review)
- [F7] Astronomer Docs — Apache Airflow Executors ("Two statically coded hybrid executors exist, the CeleryKubernetes Executor and the LocalKubernetes Executor... rarely used and as of Airflow 2.10 no longer recommended"): https://www.astronomer.io/docs/learn/airflow-executors-explained#choose-an-executor (tier 1, added on Critic-pass review)
