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
  status: "in progress — 10 of 130 planned topics shipped"
  source_project: astro-migration-skills
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

**Current batch (topics 001-010, Cluster 1 — Scheduler & DAG Design) was
generated autonomously, with the mandatory Human Source Check and Human
Sign-off gates explicitly skipped per direct instruction** — a fresh-context
Critic pass was still run (full report: `research/cluster-1-topics-001-010-critic-report.md`;
summary of fixes applied: `research/cluster-1-topics-001-010-fact-sheet.md`),
but nothing in this batch has had a human open the cited sources, run the
`NEEDS_EXEC_CHECK` items, or formally sign off. Treat every file in this
batch as **draft-quality, Critic-checked but not human-verified**, until
someone completes `.agents/signoff-checklist.md` for each.

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

## Known open items

- A fresh-context Critic pass found and fixed 6 real defects across this batch (wrong parameter name, two unsupported citations, one citation-number swap, one now-outdated sub-claim, one already-resolvable `NEEDS_EXEC_CHECK`) — see `research/cluster-1-topics-001-010-critic-report.md`. What remains open genuinely requires a human running something real, not just re-reading:
  - `dag-factory-pattern-for-large-estates.md` — confirm `is_paused_upon_creation` behaves as documented (an open Airflow GitHub issue questions its reliability).
  - `scheduler-ha-and-leader-election.md` — the "2+, up to 4 schedulers" guidance is sourced from Astronomer *Software* v0.37 docs; re-confirm against current Cloud/Hybrid.
  - `dag-level-sla-and-catchup-backfill-policy.md` — confirm Deadline Alerts' production-readiness on the actual target Astro Runtime version (still marked experimental upstream).
- `dag-level-sla-and-catchup-backfill-policy.md` flags that the imported `skills/migrating-autosys-to-astronomer/reference/alerting-and-sla.md` needs a correction (its "Airflow 3: SLA callbacks" line is stale — SLA was removed in 3.0, confirmed independently by both the original research and the Critic pass). Not fixed here; that's a different skill's file.
- `SETUP-4` (seed source list) and `SETUP-6` (formal scaffold task) were done informally as part of generating this batch, not as their own gated tasks — see `tasks/README.md` for the formal tracker state.
