---
name: astro-design-best-practices
description: >
  Production-grade Astro/Airflow architecture and design-best-practice guidance
  for teams migrating from AutoSys (CA WA AE), organized by design concern
  (scheduler/DAG design, executor/worker architecture, metadata DB, security,
  observability, CI/CD, config/secrets, HA/DR, regulatory/compliance, and
  more) rather than by JIL construct. Use this skill when the question is
  "how should we architect this on Astro," not "what does this JIL attribute
  map to" — the companion `migrating-autosys-*` skills cover the latter.
metadata:
  author: Quest1
  version: "0.1.0"
  status: "in progress — 20 of 130 planned topics shipped"
  source_project: astro-design-best-practices
---

# astro-design-best-practices

## Overview

130 planned topic files across 19 clusters (see `tasks/README.md` in this repo
for the full roadmap and the axis relevance matrix), each produced by the
Researcher → Human Source Check → Generator → Critic → Human Sign-off
pipeline defined in `AGENTS.md`. Every claim in every file traces to a
`## Sources` section; every recommendation that bridges an AutoSys mechanism
to an Astro/Airflow design is marked `{syn: ...}` and built transparently
from cited facts, per `AGENTS.md` Design Principle #6.

**Topics 001-020 (all of Cluster 1 — Scheduler & DAG Design, plus the first 7
of Cluster 2 — Executor & Worker Architecture) were generated autonomously,
with the mandatory Human Source Check and Human Sign-off gates explicitly
skipped per direct instruction** — a fresh-context Critic pass was still run
on each batch (001-010: `research/cluster-1-topics-001-010-critic-report.md`;
011-020: `research/topics-011-020-critic-report.md`), and found real defects
in both batches — including, in the second batch, two outright `FAIL`
verdicts on files that had fabricated specific numbers or cited a source that
didn't actually support the claim. All findings were fixed directly in the
shipped files. Nothing in either batch has had a human open the cited
sources, run the `NEEDS_EXEC_CHECK` items, or formally sign off. Treat every
file in both batches as **draft-quality, Critic-checked but not
human-verified**, until someone completes `.agents/signoff-checklist.md` for
each.

## Reference Files — Cluster 1: Scheduler & DAG Design

- `reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md` — config-driven DAG generation for estates too large to hand-write one DAG per box; estate-scale decision table.
- `reference/scheduler-and-dag/dag-versioning-and-change-management.md` — Airflow 3 DAG bundles/versioning vs. JIL's in-place mutation model; Git-backed bundle recommendation.
- `reference/scheduler-and-dag/scheduler-ha-and-leader-election.md` — Airflow's active-active scheduler HA vs. AutoSys's primary/shadow/tie-breaker model.
- `reference/scheduler-and-dag/dag-parsing-performance-budget.md` — `min_file_process_interval`/`parsing_processes` tuning, tied directly to the DAG-factory topic's top-level-code rule.
- `reference/scheduler-and-dag/taskgroups-vs-separate-dags.md` — extends the imported skill's box→DAG decision tree with the concurrency-isolation signal.
- `reference/scheduler-and-dag/cross-dag-dependencies-datasets-vs-triggerdagrun-vs-externaltasksensor.md` — Asset (formerly Dataset) vs. `TriggerDagRunOperator` vs. `ExternalTaskSensor`, mapped onto AutoSys cross-box condition patterns.
- `reference/scheduler-and-dag/dynamic-task-mapping-design.md` — `.partial()`/`.expand()` design for AutoSys's runtime job-cloning pattern.
- `reference/scheduler-and-dag/custom-timetable-design-for-autosys-calendars.md` — custom `Timetable` design for `run_calendar`/`exclude_calendar`, extending the imported skill's calendar rules.
- `reference/scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md` — Airflow 3's SLA removal (replaced by experimental Deadline Alerts in 3.1) and the new `catchup=False` default; **flags a staleness conflict in the imported `alerting-and-sla.md` file, not yet corrected**.
- `reference/scheduler-and-dag/idempotency-and-retry-design.md` — `n_retrys` → `retries` migration requires an idempotency classification step JIL never had.
- `reference/scheduler-and-dag/concurrency-controls-pools-and-max-active-runs.md` — Pools vs. `max_active_runs` mechanics, mapped onto `machine-load-and-virtual-resources` cluster's AutoSys `max_load`/`job_load`/virtual-resource concepts.
- `reference/scheduler-and-dag/naming-and-tagging-conventions-at-scale.md` — `dag_id`/`tags` mapped onto AutoSys's `box_name` (structural) vs. `group`/`application` (cross-cutting classification) two-axis model.
- `reference/scheduler-and-dag/one-off-and-ad-hoc-job-design.md` — Params/`dag_run.conf` design for genuinely one-off jobs, kept separate from the DAG-factory's recurring-box config schema.

Cluster 1 (Scheduler & DAG Design, 13 topics) is now complete.

## Reference Files — Cluster 2: Executor & Worker Architecture (in progress, 7 of 11)

- `reference/executor-and-worker/celeryexecutor-vs-kubernetesexecutor-decision-framework.md` — decision table keyed off AutoSys `machine:` pinning patterns and job-volume burstiness.
- `reference/executor-and-worker/worker-queue-segregation-mirroring-machine-groups.md` — classifies *why* AutoSys machine groups existed before translating them into Astro worker queues, rather than a 1:1 machine→queue mapping.
- `reference/executor-and-worker/autoscaling-design-for-bursty-batch-workloads.md` — min/max/concurrency sizing for AutoSys-shaped batch-window bursts.
- `reference/executor-and-worker/per-task-resource-requests-and-limits.md` — `executor_config`/`pod_override` sizing from AutoSys machine-tier signals; a Critic pass caught and corrected an inverted claim about Kubernetes' actual admission-time failure behavior.
- `reference/executor-and-worker/node-affinity-and-taints-for-specialized-jobs.md` — taints/tolerations vs. soft affinity, mapped onto *why* a job was machine-pinned, not just that it was.
- `reference/executor-and-worker/keda-based-autoscaling.md` — the specific autoscaling formula and polling/cool-down mechanics; **contains an unresolved `NEEDS_EXEC_CHECK`** on a real ambiguity between two different cool-down figures found in different sources.
- `reference/executor-and-worker/hybrid-executor-strategy.md` — distinguishes `CeleryKubernetesExecutor` (queue-level routing) from `KubernetesPodOperator` (operator-level, executor-independent) as two genuinely different hybrid mechanisms.

## Known open items

- A fresh-context Critic pass found and fixed 6 real defects across this batch (wrong parameter name, two unsupported citations, one citation-number swap, one now-outdated sub-claim, one already-resolvable `NEEDS_EXEC_CHECK`) — see `research/cluster-1-topics-001-010-critic-report.md`. What remains open genuinely requires a human running something real, not just re-reading:
  - `dag-factory-pattern-for-large-estates.md` — confirm `is_paused_upon_creation` behaves as documented (an open Airflow GitHub issue questions its reliability).
  - `scheduler-ha-and-leader-election.md` — the "2+, up to 4 schedulers" guidance is sourced from Astronomer *Software* v0.37 docs; re-confirm against current Cloud/Hybrid.
  - `dag-level-sla-and-catchup-backfill-policy.md` — confirm Deadline Alerts' production-readiness on the actual target Astro Runtime version (still marked experimental upstream).
- The 011-020 batch's Critic pass found and fixed 5 more defects, including **2 outright FAILs** (see `research/topics-011-020-critic-report.md`): a fabricated polling-interval/cool-down number in `keda-based-autoscaling.md`, and two claims in `per-task-resource-requests-and-limits.md` cited to a source that supported neither (one was corrected — and in the process, found to be *backwards*: real Kubernetes behavior is a clean admission-time rejection, not a silent stuck pod — the other was removed entirely since no real source could be found). What remains open:
  - `keda-based-autoscaling.md` — a genuine, unresolved ambiguity between the Airflow Helm chart's general `cooldownPeriod: 30`s default and separate KEDA documentation describing a 300s/5-minute cool-down specific to scale-to-zero. Needs resolving against a real deployed `ScaledObject`, not further documentation research.
- `dag-level-sla-and-catchup-backfill-policy.md` flags that the imported `skills/migrating-autosys-to-astronomer/reference/alerting-and-sla.md` needs a correction (its "Airflow 3: SLA callbacks" line is stale — SLA was removed in 3.0, confirmed independently by both the original research and the Critic pass). Not fixed here; that's a different skill's file.
- `SETUP-4` (seed source list) and `SETUP-6` (formal scaffold task) were done informally as part of generating this batch, not as their own gated tasks — see `tasks/README.md` for the formal tracker state.
