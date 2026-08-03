# Condition strings → Airflow dependencies

AutoSys expresses job dependencies as a boolean expression over other jobs' statuses, set on the `condition:` attribute. This is the single hardest translation surface in a JIL migration because Airflow's native dependency model (task edges + `trigger_rule`) covers the AND-of-successes case cleanly and nothing else natively.

## The four status functions

| Function | Meaning | Airflow equivalent |
|---|---|---|
| `s(job_name)` | job_name last ran to SUCCESS | A normal upstream edge (`upstream >> downstream`), default `trigger_rule="all_success"` |
| `f(job_name)` | job_name last ran to FAILURE | An edge with `trigger_rule="all_failed"` **only if `job_name` is the sole upstream**; with multiple upstreams, Airflow's `all_failed` requires *every* upstream to fail, which is not the same as "this specific one failed" — needs a custom check (see below) |
| `n(job_name)` | job_name is NOT currently running | Usually not a task edge at all — it's a concurrency/mutual-exclusion statement. Translate to `max_active_runs`, a `Pool` with capacity 1, or a `TaskGroup`-level concurrency limit, not a dependency arrow |
| `d(job_name)` | job_name is DONE (terminated, success or failure) | `trigger_rule="all_done"` |

## Single-clause conditions (MECH)

`condition: s(extract_orders)` → a plain upstream edge. This is the common case and should be the majority of a real estate.

## AND-combined conditions (MECH → JUDG)

`condition: s(job_a) and s(job_b)` → two upstream edges into the same task, default `trigger_rule`. Still MECH if every clause is `s()`. Becomes JUDG the moment clauses mix functions (e.g. `s(job_a) and d(job_b)`) — Airflow trigger rules apply per-task, not per-upstream, so a mixed-function AND needs either:
- splitting into two edges with a compatible shared trigger_rule when one exists, or
- a small evaluator task (a `@task` that queries `TaskInstance` state via the Airflow REST API/ORM for each named upstream and returns True/False, gating a `ShortCircuitOperator` immediately downstream).

Record which approach was used per condition string in the migration report — this is exactly the "equivalence row" the SKILL.md hard rules require.

## OR-combined conditions (REDESIGN)

`condition: s(job_a) or s(job_b)` has no native Airflow trigger_rule equivalent when `job_a` and `job_b` are two of several upstreams feeding one task (Airflow's closest built-in, `one_success`, works only if ALL of the task's upstreams are meant to satisfy the same OR — it doesn't let you carve out a subset). Two practical approaches, in order of preference:

1. **Redesign as a Dataset race**: if `job_a` and `job_b` both produce a signal that the downstream genuinely just needs "whichever comes first," have both update the same Dataset and schedule the downstream DAG on that Dataset. This is usually the more idiomatic Airflow 3 shape and avoids polling.
2. **Evaluator task**: same pattern as the mixed-AND case — a task that checks both upstream states via the REST API/ORM and short-circuits accordingly. Use this when the OR is genuinely about "either predecessor's terminal state," not about racing a produced artifact.

Nested boolean trees (`(s(a) or s(b)) and n(c)`) decompose into a combination of the above; write the decomposition into the manifest as its own record so the report can show the source expression next to the exact Airflow implementation chosen.

## Cross-box and cross-DAG conditions

A condition string that references a job in a *different* box than the one currently being translated is a signal for the box → DAG boundary decision (`reference/mapping.md`): if jobs in two different boxes depend on each other by name, those two boxes likely need to become two DAGs linked by a Dataset (preferred) or `TriggerDagRunOperator`/`ExternalTaskSensor` (if a hard wait is truly required), not two TaskGroups pretending to be independent.

## What to write in the manifest per condition string

For every `condition:` attribute encountered:

```json
{
  "job": "load_orders",
  "source_condition": "s(extract_orders) and n(load_orders_prior_run)",
  "classification": "JUDG",
  "target": "edge: extract_orders >> load_orders; n() clause dropped, replaced by max_active_runs=1 on the DAG",
  "delta": "AutoSys re-evaluated n() at trigger time across all history; Airflow's max_active_runs only prevents concurrent runs of THIS dag, which is the intended behavior here — no semantic loss expected, but confirm no other job also gates on load_orders' running state before dropping the clause"
}
```

The `delta` field is not optional even when the delta is "none expected" — state it, so the reviewer knows it was considered rather than missed.
