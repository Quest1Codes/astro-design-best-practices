# Per-Task Resource Requests/Limits (`executor_config`)

AutoSys has no per-job resource request/limit concept comparable to Kubernetes — a job either ran on a machine sized adequately for it (an operational/provisioning concern, decided once per machine) or it didn't. Under KubernetesExecutor, resource sizing becomes a per-task, per-DAG-code concern, which is a real design shift, not just a syntax change.

## Core mechanics

- Per-task CPU/memory requests and limits are set via `pod_override` inside a task's `executor_config`, constructing a Kubernetes `V1Pod`/`V1Container` with `V1ResourceRequirements` [F1].
- Astro's documented pattern for configuring tasks under the Kubernetes executor uses this same `executor_config`/`pod_override` mechanism [F2].
- **Corrected per Critic pass**: an earlier draft of this file cited a GitHub discussion for two "known sharp edge" claims that, on direct inspection of the full thread, does not actually contain either claim. Replaced below with a properly-sourced version of the first claim, and the second claim removed entirely rather than kept on a citation that doesn't support it (per `AGENTS.md`'s escalation path: defer a claim with no real source, don't ship it under a citation that only looks like support).
- If a task's resource `requests` exceed its `limits`, Kubernetes rejects the Pod at admission time with a clear `403 Forbidden` error naming the violated constraint — this is a **clean rejection**, not a silent stuck pod [F3]. (This corrects the earlier draft's claim that this failure mode was unclear/silent — the real Kubernetes behavior is the opposite: an explicit, immediate admission-time error.) Validate `requests <= limits` at DAG-authoring time (e.g. a lint check in CI, see the CI/CD cluster) so this surfaces before merge rather than as a runtime admission failure, even though the runtime failure itself is at least clear when it happens.

## {syn: F1,F2} Design guidance — sizing from AutoSys machine assignment

The source estate's `machine:` assignment already encodes a rough resource-tier signal — a job pinned to a specifically-provisioned "heavy" machine was implicitly saying "this needs more resources than the general pool." Use that signal as the *starting point* for `executor_config` sizing, not the final answer:

1. Group translated jobs by their original machine's provisioned capacity (if that data is available from the platform team) into a small number of resource tiers (e.g. small/medium/large), rather than hand-tuning `executor_config` per job — this keeps the number of distinct pod resource profiles manageable at scale.
2. Treat the AutoSys-derived tier as a first guess, not a guarantee — AutoSys machine sizing often reflected historical/organizational reasons (which team owned the box) as much as actual resource need. Validate the first few real runs' actual resource consumption against the assigned tier before treating it as correct estate-wide.

## Sources

- [F1] GitHub — apache/airflow Discussion #22717, "KubernetesExecutor Set Request and Limit CPU/Memory" (worked `pod_override`/`executor_config` code examples): https://github.com/apache/airflow/discussions/22717 (tier 3 — community discussion on the project's own repo, not a formal doc page; corrected per Critic pass to cite only what this thread actually contains — worked examples, not the two sharp-edge claims previously attributed to it)
- [F2] Astronomer Docs — Configure tasks to run with the Kubernetes executor: https://www.astronomer.io/docs/astro/kubernetes-executor (tier 1)
- [F3] Kubernetes official docs — Limit Ranges (requests-exceed-limits admission-time rejection, `403 Forbidden` with constraint-violation message): https://kubernetes.io/docs/concepts/policy/limit-range/ (tier 2 — foundational Kubernetes documentation, added per Critic pass to replace the unsupported citation)
