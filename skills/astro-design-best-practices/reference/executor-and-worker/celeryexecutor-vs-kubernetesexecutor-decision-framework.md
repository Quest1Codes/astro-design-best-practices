# Executor Decision Framework (Astro / Celery / Kubernetes)

AutoSys dispatches every job to a named `machine:` — a persistent agent process on a specific host. Airflow's executors replace that model entirely; none of Astro's three executors are "a specific machine" in the AutoSys sense, and the choice between them is an architecture decision made once per estate (or per worker queue — see `worker-queue-segregation...md`), not per job.

## Addendum: this file predates the Astro executor — start here

**This file was originally written comparing only CeleryExecutor and KubernetesExecutor**, before the **Astro executor** existed. That gap was flagged in a Critic-pass review of this skill and is fixed below, but the framing throughout the rest of the file still reflects the original two-way comparison — read this section first.

- Astro currently supports **three** executors: **Astro executor**, **Celery executor**, and **Kubernetes executor** [F4].
- **The Astro executor is the default for all new Airflow 3.x Deployments**, and is the *only* executor usable in Remote Execution mode [F5]. It consists of Agents that pull work from an API server, which centrally manages Agent scaling and task-assignment logic — architecturally distinct from Celery (workers pull from a queue) and Kubernetes (the scheduler launches a pod per task) [F5].
- **You are not forced onto it.** Celery and Kubernetes executors remain fully supported, selectable options on Airflow 3.x Deployments (via the Astro UI, CLI `--executor` flag, API, or Terraform), not legacy-only fallbacks [F4][F6]. Celery executor remains "a common default choice for Airflow 2 Deployments on Astro and self-managed Airflow 2 and 3 environments" [F1b]. Kubernetes executor requires Astro Runtime 8.1.0 or later [F4].
- **For a new AutoSys migration landing on Airflow 3.x, the practical default question changes**: start from "does this estate have a specific reason to choose Celery or Kubernetes instead of the Astro executor default," not "Celery vs. Kubernetes" as a first-class choice. The AutoSys-signal decision table below (originally written Celery-vs-Kubernetes) still identifies *when per-task resource isolation matters* — that signal now maps to "stay on Kubernetes executor, or use `KubernetesPodOperator` under the Astro executor default" rather than automatically meaning "choose KubernetesExecutor."
- **`CeleryKubernetesExecutor`** (described below) is Airflow-2-era guidance. Astronomer's own docs now describe the statically-coded hybrid executors (`CeleryKubernetesExecutor`, `LocalKubernetesExecutor`) as "rarely used" and, as of Airflow 2.10, "no longer recommended" [F7]. On Airflow 3.x, prefer the Astro executor with per-queue worker-type segregation, or `KubernetesPodOperator` for individual outlier tasks (see `hybrid-executor-strategy.md`), over `CeleryKubernetesExecutor`.

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
- [F1b] Astronomer Docs — Apache Airflow Executors, CeleryExecutor section ("common default choice for Airflow 2 Deployments on Astro and self-managed Airflow 2 and 3 environments"): https://www.astronomer.io/docs/learn/airflow-executors-explained#celeryexecutor (tier 1, added on Critic-pass review)
- [F4] Astronomer Docs — Deployment executor (Astro supports three executors: Astro, Celery, Kubernetes; Kubernetes requires Astro Runtime 8.1.0+; executor selectable via UI/CLI/API/Terraform): https://www.astronomer.io/docs/astro/deployment-resources#deployment-executor and https://www.astronomer.io/docs/astro/executors-overview#choose-an-executor (tier 1, added on Critic-pass review)
- [F5] Astronomer Docs — Astro executor overview (default for all Airflow 3.x Deployments; only executor usable in Remote Execution mode; Agents pull from an API server vs. Celery's queue-pull and Kubernetes' per-task pod launch): https://www.astronomer.io/docs/astro/astro-executor#overview (tier 1, added on Critic-pass review)
- [F6] Astronomer Docs — Configure an executor on Astro ("The default executor is the AstroExecutor"; CLI `--executor` flag, API `executor` parameter): https://www.astronomer.io/docs/learn/airflow-executors-explained#configure-an-executor-on-astro (tier 1, added on Critic-pass review)
- [F7] Astronomer Docs — Apache Airflow Executors ("Two statically coded hybrid executors exist, the CeleryKubernetes Executor and the LocalKubernetes Executor... these executors are rarely used and as of Airflow 2.10 no longer recommended"): https://www.astronomer.io/docs/learn/airflow-executors-explained#choose-an-executor (tier 1, added on Critic-pass review)
