# Cross-DAG Dependencies: Assets vs. TriggerDagRunOperator vs. ExternalTaskSensor

The internal reference file `conditions-and-dependencies.md` already establishes *when* a condition string crossing box boundaries signals that two boxes should become two separate DAGs [P1]. This file is the next decision: once that's true, which of Airflow's three cross-DAG mechanisms to use.

## Naming note

What Airflow 2.x called a **Dataset** is renamed **Asset** in Airflow 3 — "changed in version 3.0: the concept was previously called Dataset" [F1]. Since this skill targets Airflow 3/Astro Runtime 3.3+, use "Asset" throughout; older tutorials and blog posts (including some cited here) still say "Dataset" for the same mechanism.

## The three mechanisms

| Mechanism | Model | Best for |
|---|---|---|
| Asset (formerly Dataset) | Event-driven, push-based: an upstream task updates an Asset, any DAG scheduled on that Asset triggers automatically [F2] | A downstream DAG that should run whenever the upstream's output changes, especially on an irregular cadence [F2] |
| `TriggerDagRunOperator` | Explicit push: an auxiliary task in the upstream DAG directly triggers one or more named downstream DAGs [F3] | One upstream DAG that needs to kick off one or more specific downstream DAGs — the most flexible/direct linking mechanism [F3] |
| `ExternalTaskSensor` | Pull-based polling: the downstream DAG waits, repeatedly checking whether an upstream task has completed [F3] | Only when a hard wait-and-poll is genuinely required — a standard sensor occupies a worker slot for its entire wait, which risks worker starvation at scale in a cloud/Astro deployment [F4] |

## {syn: P1,F2,F3,F4} Decision guidance for AutoSys cross-box conditions

- `condition: s(job_in_other_box)` where the referencing box just needs "the other box's output is ready," regardless of exact timing → **Asset**. This matches AutoSys's own semantics best: the box didn't care exactly *when* the dependency ran, only that it succeeded [P1].
- A box that AutoSys explicitly kicks off out-of-band today (`sendevent -E FORCE_STARTJOB`, or on a calendar independent of its nominal parent) [P1] → **`TriggerDagRunOperator`**, since this is already an explicit push in the source system, not an implicit "whenever ready" relationship.
- A genuine hard-wait requirement with no available Asset-based redesign → **`ExternalTaskSensor`**, but only as a fallback — default to Asset-based design per the guidance above [F4], and if a sensor is unavoidable, use deferrable-sensor mode rather than a standard blocking sensor to avoid occupying a worker slot for the whole wait (deferrable operators are a general Airflow capability; verify the specific sensor has a deferrable variant before relying on this).

## Estate-scale callout

At large scale, prefer Asset-based linking over `TriggerDagRunOperator` fan-out where the choice is otherwise close — Assets decouple the upstream DAG from needing to know every downstream DAG name explicitly, which matters once an estate has enough cross-box dependencies that a `TriggerDagRunOperator` task would need to name dozens of downstream DAGs.

## Sources

- [F1] Apache Airflow docs — Asset Definitions ("Changed in version 3.0: previously called Dataset"): https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/assets.html (tier 2)
- [F2] Astronomer Docs — Cross-DAG dependencies (Asset/Dataset event-driven triggering): https://www.astronomer.io/docs/learn/cross-dag-dependencies (tier 1)
- [F3] Astronomer Docs — Cross-DAG dependencies (`TriggerDagRunOperator`, `ExternalTaskSensor` push/pull comparison): same as F2 (tier 1)
- [F4] Astronomer Docs — Cross-DAG dependencies (sensor worker-slot/starvation caveat in cloud deployments): same as F2 (tier 1)
- [P1] Project-internal — `skills/migrating-autosys-to-astronomer/reference/conditions-and-dependencies.md` (cross-box condition signal)
