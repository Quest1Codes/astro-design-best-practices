# DAG Parsing Performance Budget

AutoSys has no equivalent concept — job/box definitions live in the Event Server as data and are read on demand by the scheduler, not re-parsed as code on a fixed interval. Every AutoSys estate migrating to Airflow inherits a genuinely new operational concern: DAG files are Python, and Python gets re-executed on a schedule just to discover what DAGs exist.

## Core mechanics

- Airflow re-executes every file in the DAGs folder on a fixed cadence, `min_file_process_interval`, which defaults to 30 seconds [F1].
- Any top-level code that calls an external system (an API, a database, a network request) or does non-trivial computation runs on *every* parse cycle, not just when the DAG is actually triggered — this is the single most common source of scheduler overload in a large estate [F2].
- `parsing_processes` controls how many DAG files the scheduler parses in parallel; Astronomer's guidance is roughly 2x available scheduler vCPUs [F3].
- Raising `min_file_process_interval` reduces parse-cycle CPU load but delays how quickly a DAG-file change (including a factory-regenerated file) becomes visible in the UI and schedulable — an explicit tradeoff, not a free win [F1].

## Estate-scale decision table

| Estate size | Recommendation |
|---|---|
| Hundreds of jobs | Default `min_file_process_interval` (30s) and default `parsing_processes` are almost certainly fine; don't tune preemptively. |
| Thousands of jobs, factory-generated | {syn: F1,F2} Audit the DAG-factory's top-level code path specifically for any I/O (the most common culprit: a factory that queries a config database or calls an API at parse time instead of reading a pre-exported file) [F2] — remove it before tuning `parsing_processes`/`min_file_process_interval`, since fixing the actual I/O cost is a bigger win than parallelizing around it. |
| Tens of thousands of jobs, factory-generated | {syn: F3} At this scale, raise `parsing_processes` toward the 2x-vCPU guideline as a scheduler-sizing input (not just a config tweak — it implies scheduler pod/node sizing) [F3], and treat `min_file_process_interval` as a deliberate tradeoff decision made with the platform team, not left at default by omission. |

## {syn: F2} Design guidance

This directly follows from the DAG-factory pattern (`dag-factory-pattern-for-large-estates.md`): the factory's own design rule — export complex per-box metadata to a file rather than computing it in top-level code — *is* the primary DAG-parsing-performance lever for a large AutoSys estate. These two topics should be read together; a factory that violates the "no I/O at parse time" rule will surface as a parsing-performance problem regardless of any scheduler-sizing tuning applied afterward.

## Sources

- [F1] Astronomer Docs — DAG writing best practices (`min_file_process_interval`): https://www.astronomer.io/docs/learn/dag-best-practices (tier 1)
- [F2] Apache Airflow docs — Best Practices (top-level code / external-call guidance): https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html (tier 2)
- [F3] Astronomer Docs — rightsizing Airflow on Astro (`parsing_processes` sizing, ~2x vCPUs) — corrected citation, per Critic pass: not on the `dag-best-practices` page it was originally attributed to: https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (tier 1)
