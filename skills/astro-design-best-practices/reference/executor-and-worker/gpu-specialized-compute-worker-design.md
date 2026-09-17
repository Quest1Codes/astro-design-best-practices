# GPU / Specialized-Compute Worker Design

AutoSys handled GPU or other specialized-hardware jobs the same way it handled any hardware constraint: `machine:` pinning to a specific host pool that actually had the resource. Astro's standard worker types (used by the Celery executor and the Astro executor) are general-purpose CPU/memory instances — there is no documented GPU-enabled standard worker type [NEEDS_EXEC_CHECK: not found in the standard worker-type table; treat as unsupported for standard worker queues unless confirmed otherwise]. GPU workloads need one of two genuinely different, both real, patterns.

## {syn: F1,F2} Two real patterns — pick based on execution mode, not preference

- **Pattern A — `KubernetesPodOperator` launching into an external GPU cluster (Hosted execution mode).** Astro's own docs state this directly: "If some of your tasks require specific resources such as a GPU, you might want to run them in a different cluster than your Airflow instance" [F1][F2]. The task runs on Astro as normal, but `KubernetesPodOperator` connects to a separate external Kubernetes cluster (e.g. an EKS/AKS/GKE cluster with a GPU node pool) via a `KubeConfig`/cluster connection and launches the GPU-requiring pod there — the pod spec (including `nvidia.com/gpu` resource requests, on the external cluster) is standard Kubernetes, not an Astro-specific concept [F1]. Requires network connectivity between the Astro Deployment (or Remote Execution Agent) and the external cluster, and cross-cloud-account IAM/workload-identity setup if the external cluster is in a different account [F1].
- **Pattern B — Remote Execution Agent worker with GPU node targeting.** If the estate uses Remote Execution (workers running in customer-managed infrastructure), GPU nodes are an explicitly documented hardware-isolation dimension: each `workers[]` tenant entry configures its own `resources`, `nodeSelector`, `affinity`, and `tolerations`, which Astro's own docs describe as giving that tenant "its own Pod sizes and node groups, such as a dedicated instance type or **GPU nodes**" [F3]. This keeps the GPU-requiring worker pool entirely within infrastructure you already control, rather than bridging to a second Kubernetes cluster.

## Decision table

| Signal from the source estate | Recommendation |
|---|---|
| Execution mode is Hosted (Astro-managed compute), and GPU jobs are a minority of the estate | Pattern A — `KubernetesPodOperator` targeting an external GPU cluster [F1][F2]. Astro's own managed workers stay general-purpose; only the GPU-requiring tasks reach out. |
| Execution mode is Remote Execution (workers already run in your own infrastructure) | Pattern B — configure a dedicated `workers[]` tenant with GPU `nodeSelector`/`affinity`/`tolerations` [F3]. No second cluster to bridge to; the GPU pool is just another worker tenant. |
| A `machine:` pool was pinned for a *non-hardware* reason (team ownership, historical convention) rather than genuine GPU/specialized-compute need | Neither — re-verify the pin is real before building either pattern. See `reference/executor-and-worker/node-affinity-and-taints-for-specialized-jobs.md`'s "What NOT to do" section on defaulting to hard translations of soft AutoSys conventions. |

## What this does not replace

Both patterns are about *where the GPU pod runs*, not how much of it a task requests or how the scheduler avoids placing non-GPU work on GPU nodes — those are `per-task-resource-requests-and-limits.md` (`executor_config`/`pod_override` resource requests) and `node-affinity-and-taints-for-specialized-jobs.md` (taint the GPU pool, tolerate only from GPU-requiring tasks) concerns respectively. This file is specifically about the two structurally different ways to reach GPU compute from an Astro Deployment at all; those two files govern the pod spec once you're on the right pattern.

## Sources

- [F1] Astronomer Docs — Launch a Pod in an EKS cluster on AWS ("If some of your tasks require specific resources such as a GPU, you might want to run them in a different cluster than your Airflow instance"; prerequisites and setup for Hosted vs. Remote execution mode): https://www.astronomer.io/docs/astro/launch-pod-external-cluster-aws (tier 1) — equivalent Azure/GCP guides exist at https://www.astronomer.io/docs/astro/launch-pod-external-cluster-azure and https://www.astronomer.io/docs/astro/launch-pod-external-cluster-gcp
- [F2] Astronomer Learn — `KubernetesPodOperator` guide, "Launching Pods in external clusters" (same GPU-driven external-cluster pattern, from the general KPO reference rather than the cloud-specific setup guide): https://www.astronomer.io/docs/learn/kubepod-operator (tier 1)
- [F3] Astronomer Docs — Remote Execution, "What a tenant isolates" (Hardware isolation dimension explicitly lists "GPU nodes" via `workers[].resources`/`nodeSelector`/`affinity`/`tolerations`): https://www.astronomer.io/docs/astro/remote-execution/remote-execution-isolation#what-a-tenant-isolates (tier 1)
- [F4] Astronomer Learn — Airflow for MLOps, "Pluggable compute" (general framing: "you can run your data engineering tasks on a Spark cluster and your model training tasks on a GPU instance"): https://www.astronomer.io/docs/learn/airflow-mlops (tier 1) — general context only, not a distinct mechanism from F1-F3
- [P1] Task-tracker description (AutoSys `machine:` pinning to specialized hardware pools) — this skill's own `tasks/README.md`, topic 024
