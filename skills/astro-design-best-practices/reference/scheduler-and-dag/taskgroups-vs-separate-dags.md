# TaskGroups vs. Separate DAGs — Decision Criteria

This is the direct architecture-level counterpart to the box→DAG boundary decision already established for AutoSys migrations [P1]; this file adds the Airflow-side mechanics that decision depends on.

## Core mechanics

- A TaskGroup is purely a UI/organizational grouping construct — tasks inside a TaskGroup live on the *same* underlying DAG object [F1]. It is not a scheduling boundary.
- {syn: F1,F1b} `max_active_runs` is a parameter of the `DAG` class itself, not of any task or grouping within it [F1b] — combined with the fact above, this means TaskGroup tasks cannot have a `max_active_runs` independent of their parent DAG, since they are not a separate `DAG` object to begin with. (Corrected per Critic pass: the original citation for this combined claim did not actually state it on the cited page — split into its two supporting facts here instead of one unsupported combined claim.)
- TaskGroups are the only way to dynamically map over a *sequence* of tasks together (e.g. an unknown number of files, each needing several sequential steps) — dynamic task mapping alone only maps single tasks [F2].
- When a set of tasks is owned by a different team or has a materially different schedule than the rest of the DAG, Astronomer's own guidance is to split into separate DAGs connected via Assets (the Airflow 3 name for what were Datasets in 2.x) rather than force them into one DAG with TaskGroups as a visual-only separation [F3].

## Decision table (extends the existing box→DAG tree)

| Signal | Recommendation |
|---|---|
| Same schedule as parent, same owning team, nothing downstream needs to depend on this sub-unit independently [P1] | TaskGroup within the parent DAG. |
| A repeating pattern applied to a dynamic, unknown-length input (e.g. one AutoSys box pattern cloned per file/dataset) [F2] | TaskGroup + dynamic task mapping together — this is the only construct that dynamically maps a *sequence* of steps, not a single task. |
| Different owning team, or a materially different schedule than the parent [F3] | Separate DAG, connected via an Asset (Airflow 3's rename of Dataset — see `cross-dag-dependencies-datasets-vs-triggerdagrun-vs-externaltasksensor.md`) rather than a TaskGroup pretending to be independent. |
| {syn: F1,F1b,P1} A box whose children need their own `max_active_runs` concurrency limit independent of the rest of the parent DAG | Must be a separate DAG, not a TaskGroup — since `max_active_runs` is a per-`DAG`-object setting [F1b] and TaskGroup tasks are not a separate `DAG` object [F1], a box that needs its own concurrency ceiling (e.g. `n()` mutual-exclusion translated per `translation_patterns.md`) cannot get that isolation from a TaskGroup alone. |

## What changes from the original box→DAG framing

The existing decision tree [P1] already covers *when* a box becomes its own DAG vs. a TaskGroup based on scheduling/ownership/dependency signals. This file adds one signal that tree didn't originally have: **concurrency-limit isolation**. A box translated with an `n()`-derived `max_active_runs=1` mutual exclusion (see `translation_patterns.md` in the imported skill, and the `machine-load-and-virtual-resources` cluster) needs that concurrency boundary to be a real DAG boundary — a TaskGroup cannot carry its own `max_active_runs` independent of its parent DAG [F1][F1b].

## Sources

- [F1] Astronomer Docs — Airflow task groups (TaskGroups are UI-only, tasks live on the same DAG object): https://www.astronomer.io/docs/learn/task-groups (tier 1)
- [F1b] Airflow model API reference — `max_active_runs` is a `class DAG` parameter, not task/group-scoped: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html (tier 2) — added per Critic pass; the original draft cited only F1 for this combined claim, but F1 alone does not state the `max_active_runs`/pool-inheritance detail.
- [F2] Astronomer Docs — Airflow task groups (dynamic mapping over sequential steps): same as F1 (tier 1)
- [F3] Astronomer Docs — Airflow task groups (multi-team DAGs → separate DAGs + Assets): same as F1 (tier 1)
- [P1] Project-internal — `skills/migrating-autosys-to-astronomer/reference/mapping.md` (box→DAG boundary decision tree)
