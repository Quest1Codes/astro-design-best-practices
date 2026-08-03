# Fact-Sheet Record — Topics 001-010 (Cluster 1: Scheduler & DAG Design)

**Process note**: this batch was generated autonomously in a single session, with the Human Source Check and Human Sign-off gates explicitly skipped per direct instruction. A fresh-context Critic subagent pass **was** run against all 10 files (it independently spot-checked citations by fetching the real source pages, not just trusting them) and found real defects — a wrong parameter name, two citations that didn't actually support their claims, one citation-number swap, and one now-outdated sub-claim. All were fixed directly in the shipped files; see "Critic findings and fixes applied" below. This file is the condensed audit trail — per-fact tiering and citations live in each shipped file's own `## Sources` section.

## Sources used, by tier

**Tier 1 (Astronomer official docs)**:
- DAG writing best practices — https://www.astronomer.io/docs/learn/dag-best-practices
- Dynamically generate DAGs in Airflow — https://www.astronomer.io/docs/learn/dynamically-generating-dags
- Dag Versioning and Dag Bundles — https://www.astronomer.io/docs/learn/airflow-dag-versioning
- Dag versioning (Astro) — https://www.astronomer.io/docs/astro/dag-versioning
- Benefits of the Airflow 2.0 Scheduler — https://www.astronomer.io/blog/airflow-2-scheduler/
- Configure a Deployment on Astronomer Software — https://www.astronomer.io/docs/astro-private-cloud/v-0-37/configure-deployment (flagged `NEEDS_EXEC_CHECK` — Software/v0.37-specific, needs re-confirmation against current Cloud/Hybrid)
- Airflow task groups — https://www.astronomer.io/docs/learn/task-groups
- Cross-DAG dependencies — https://www.astronomer.io/docs/learn/cross-dag-dependencies
- Rerun Airflow Dags and tasks — https://www.astronomer.io/docs/learn/rerunning-dags
- Upgrading Airflow 2 to Airflow 3 checklist — https://www.astronomer.io/blog/upgrading-airflow-2-to-airflow-3-a-checklist-for-2026/

**Tier 2 (Apache Airflow OSS docs)**:
- Dynamic Dag Generation — https://airflow.apache.org/docs/apache-airflow/stable/howto/dynamic-dag-generation.html
- Best Practices — https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- Dag Bundles — https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html
- Dynamic Task Mapping — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html
- Timetables — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html
- Customizing DAG Scheduling with Timetables — https://airflow.apache.org/docs/apache-airflow/stable/howto/timetable.html
- Asset Definitions — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/assets.html
- Migrating from SLA to Deadline Alerts — https://airflow.apache.org/docs/apache-airflow/stable/howto/sla-to-deadlines.html
- Deadline Alerts — https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html
- Upgrading to Airflow 3 — https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html
- AIP-15 Support Multiple-Schedulers (historical design rationale) — https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=103092651

**Tier 4 (used as draft-scaffold only, not a final citation)**:
- A third-party engineering blog's idempotency/retry-count guidance — used only for the general "idempotency required for safe retries" principle (independently corroborated by standard practice), explicitly *not* used for its specific numeric retry-count recommendations, which are marked `PRACTITIONER JUDGMENT — not independently verified` in `idempotency-and-retry-design.md`.

**Project-internal (already-vetted, mentor/prior-session-authored)**:
- `skills/migrating-autosys-to-astronomer/reference/mapping.md`
- `skills/migrating-autosys-to-astronomer/reference/conditions-and-dependencies.md`
- `skills/migrating-autosys-to-astronomer/reference/calendars-and-scheduling.md`
- `skills/migrating-autosys-to-astronomer/reference/global-variables-and-templating.md`
- `skills/migrating-autosys-to-astronomer/reference/alerting-and-sla.md` — **read during this pass and found to contain stale content** (see below)

## Finding surfaced during this research pass: a real conflict in already-shipped content

`alerting-and-sla.md` (imported from the mentor's existing work, not authored in this batch) states "Airflow 3: SLA callbacks" as the SLA-translation target. Confirmed via tier-2 sources above that this is incorrect as of Airflow 3.0: the SLA feature (including `sla_miss_callback`) was **removed** in 3.0 and replaced by **Deadline Alerts**, which are themselves new-and-experimental as of 3.1. `dag-level-sla-and-catchup-backfill-policy.md` documents the corrected guidance and flags the conflict inline; `alerting-and-sla.md` itself was **not edited** — that's a different skill file, out of scope for this batch, and needs its own tracked correction.

## Critic findings and fixes applied

A fresh-context Critic subagent independently fetched and checked source pages rather than trusting citations at face value. It found and these were fixed directly in the shipped files:

1. **Wrong parameter name, zero citation** (`dag-factory-pattern-for-large-estates.md`): the draft invented `paused_as_of_creation=True`; the real Airflow DAG constructor parameter is `is_paused_upon_creation`. Fixed, cited [F7], and flagged `NEEDS_EXEC_CHECK` since an open Airflow GitHub issue (#30615) reports this parameter not always honored reliably.
2. **Citation didn't support the claim** (`taskgroups-vs-separate-dags.md`): the cited Astronomer TaskGroups page does not actually say TaskGroup tasks inherit `max_active_runs`/pool settings. Split into two independently-cited facts (TaskGroups share the parent's `DAG` object + `max_active_runs` is a `DAG`-class parameter) whose combination supports the same conclusion legitimately.
3. **Wrong URL cited twice** (`dag-factory-pattern-for-large-estates.md` and `dag-parsing-performance-budget.md`): the `parsing_processes`/2x-vCPU guidance was attributed to `dag-best-practices`, which doesn't mention it. Re-cited to Astronomer's actual rightsizing doc in both files.
4. **Citation-number swap** (`dag-versioning-and-change-management.md`): the verbatim "structural changes" quote is on F1, was cited as F2. Fixed.
5. **Now-outdated sub-claim** (`dag-level-sla-and-catchup-backfill-policy.md`): "sync callback support planned but not yet available" — current docs show `SyncCallback` shipped in Airflow 3.2. Corrected in place; also attached the official breaking-changes page as a second citation directly on the "SLA removed in 3.0" sentence, since the originally-sole citation discusses migration without using the word "removed."
6. **A `NEEDS_EXEC_CHECK` that was actually already resolved** (`idempotency-and-retry-design.md`): the flagged float-multiplier claim for `retry_exponential_backoff` was already stated verbatim on a source already cited elsewhere in the same file. Closed, no execution check needed.

No smuggled facts were found inside any `{syn: ...}` synthesis tag, and no cross-file contradictions were found. The Critic also independently re-confirmed the `alerting-and-sla.md` conflict below is real, not a false alarm.

## `NEEDS_EXEC_CHECK` items still open after the Critic pass (genuinely require a human, running something real)

1. `scheduler-ha-and-leader-election.md` — the "2+, up to 4 schedulers" guidance is sourced from Astronomer *Software* v0.37 docs; needs re-confirmation against current Cloud/Hybrid deployment settings.
2. `dag-level-sla-and-catchup-backfill-policy.md` — Deadline Alerts' production-readiness (given their stated experimental status) needs confirming against the actual target Astro Runtime version before being relied on for SLA-equivalent translations.
3. `dag-factory-pattern-for-large-estates.md` — confirm `is_paused_upon_creation` actually works as expected on the target Airflow version, given the open GitHub issue questioning its reliability.

## What a human reviewer should still do with this batch

The Critic pass replaces the *automated* half of Human Sign-off's checklist (citation spot-checking), but not the parts that require actually running something real, or a named person's accountability. Run `.agents/signoff-checklist.md` for each of the 10 files: resolve the three `NEEDS_EXEC_CHECK` items above against a real Astro environment, and decide whether to open a follow-up task correcting `alerting-and-sla.md` (confirmed genuinely stale by both this research pass and the independent Critic check).
