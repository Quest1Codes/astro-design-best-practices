# Fact-Sheet Record — Topics 011-020 (Cluster 1 finish + Cluster 2 start)

**Process note**: same as the 001-010 batch — generated autonomously, Human Source Check and Human Sign-off gates explicitly skipped per direct instruction. A fresh-context Critic subagent pass was run against all 10 files, live-fetching cited sources rather than trusting them. This batch's Critic pass was noticeably harsher than the first: **2 of 10 files FAILed** (vs. 0 outright fails in the first batch) — see `topics-011-020-critic-report.md` for the full report. All findings were fixed directly in the shipped files.

## Topics covered

011-013 (finishing Cluster 1 — Scheduler & DAG Design): concurrency controls (Pools/`max_active_runs`), naming/tagging conventions, one-off/ad-hoc job design.
014-020 (starting Cluster 2 — Executor & Worker Architecture): CeleryExecutor vs. KubernetesExecutor, worker queue segregation, autoscaling design, per-task resource requests/limits, node affinity/taints, KEDA mechanics, hybrid executor strategy.

## Sources used, by tier (new to this batch — see the 001-010 fact-sheet for sources reused from that batch)

**Tier 1**: Astronomer Docs — Airflow pools, Apache Airflow Executors, Configure worker queues, Configure tasks to run with the Kubernetes executor, Astro executor, The New KubernetesExecutor blog, How to Use KEDA as an Autoscaler blog.

**Tier 2**: Apache Airflow docs — Pools, Params (2.4.0-versioned), Celery Executor, CeleryKubernetesExecutor, Kubernetes Executor (cncf-kubernetes provider); Apache Airflow Helm chart source (`chart/values.yaml`, `worker-kedaautoscaler.yaml`, read directly, not a docs page); Kubernetes official docs — Taints and Tolerations, Limit Ranges; KEDA project docs — ScaledObject specification.

**Tier 3**: GitHub apache/airflow Discussion #22717 (worked `executor_config` code examples only, after Critic correction — see below); Airflow community Helm chart (`airflow-helm/charts`) FAQ page for node-affinity config structure.

**Tier 4 / community, explicitly hedged**: a community blog on `dag_id`/tag naming conventions (marked `PRACTITIONER JUDGMENT`); a community blog on the "Trigger DAG w/ config" UI history (marked `NEEDS_EXEC_CHECK`, since resolved — see below).

**Project-internal**: Broadcom TechDocs "How Job Groupings Are Created" (`group`/`application` attributes, from this project's earlier AutoSys-architecture research, not from a file in this repo) — corrects a citation error where an earlier draft attributed this to `mapping.md`, which doesn't cover it.

## Critic findings and fixes applied (2 FAILs, several PASS WITH NOTES)

1. **Fabricated numbers, contradicted by the only real data point available** (`keda-based-autoscaling.md`, FAIL): the original draft stated a "10-second" polling interval and "5-minute" cool-down, both cited to an Astronomer blog post that (live-fetched, checked three ways) contains neither number. The Critic additionally pulled the actual Apache Airflow Helm chart defaults directly from source (`pollingInterval: 5`, `cooldownPeriod: 30`, in seconds) — different numbers entirely. Rewritten with the real chart defaults, properly cited, and an explicit `NEEDS_EXEC_CHECK` on the genuine ambiguity between the chart's general `cooldownPeriod: 30` and separate KEDA documentation describing a 300-second cool-down specific to scale-to-zero (a different, narrower situation, not the same setting).
2. **Two claims cited to a source that supports neither** (`per-task-resource-requests-and-limits.md`, FAIL): both "known sharp edge" claims (requests-must-not-exceed-limits behavior, and a cross-task resource-bleed report) were cited to a GitHub discussion thread that, read in full (all 8 comments), is just three people posting working code examples — neither claim appears in it. Fixed: the requests/limits claim re-sourced to official Kubernetes docs (which additionally **corrected** the claim itself — the real behavior is a clean `403 Forbidden` admission-time rejection, not a silent stuck pod, which was backwards from the original draft). The cross-task-bleed claim was **removed entirely**, per `AGENTS.md`'s escalation path — neither the original citation nor independent Critic search could locate real support for it, so it's deferred rather than shipped on a citation that only looked like support.
3. **Citation-number mismatch** (`concurrency-controls-pools-and-max-active-runs.md`): `core.max_active_runs_per_dag` is stated on F1, was cited as F3 (which only covers `pool_slots`). Fixed.
4. **Citation overstated as direct empirical support for a claim it was actually the file's own synthesis** (`celeryexecutor-vs-kubernetesexecutor-decision-framework.md` and, in softer form, `autoscaling-design-for-bursty-batch-workloads.md`): the "KubernetesExecutor is more resource-efficient on bursty workloads" comparison was cited to a blog post that, live-fetched, discusses per-pod overhead and in one place argues the *opposite* emphasis (Celery is more efficient at very high steady volume). Re-tagged as `{syn: F1}` — this file's own reasoned inference from the core executor mechanics, not an independent benchmark finding — in both files.
5. **`NEEDS_EXEC_CHECK` closed**: `one-off-and-ad-hoc-job-design.md`'s flag on `show_trigger_form_if_no_params` was independently re-confirmed current by the Critic's own search. Closed.

No smuggled facts were found inside any `{syn: ...}` tag in this batch — the same clean result as the first batch. No cross-file contradictions were found; the `CeleryKubernetesExecutor`/`KubernetesPodOperator` distinction in `hybrid-executor-strategy.md` was independently verified by the Critic directly against Airflow's own source code (`celery_kubernetes_executor.py` docstring).

## What a human reviewer should still do with this batch

Run `.agents/signoff-checklist.md` for each of the 10 files. In particular: `keda-based-autoscaling.md`'s `cooldownPeriod` ambiguity (30s vs. 300s, different scaling scenarios) needs resolving against the actual deployed `ScaledObject` on a real Astro Deployment (`kubectl get scaledobject -o yaml`), not further documentation research — this is exactly the kind of claim `AGENTS.md`'s escalation path expects a human to resolve empirically once documentation-tier sourcing runs out.
