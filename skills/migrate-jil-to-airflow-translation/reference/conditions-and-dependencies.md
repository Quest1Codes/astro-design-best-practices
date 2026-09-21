---
topic: conditions-and-dependencies
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2435, 2436, 2437, 2438, 2439, 2440, 2441]
last_verified: 2026-09-17
confidence: mixed
signals: [or_conditions, lookback, cross_instance, mutex_n, hidden_flow]
---

# Condition strings → Airflow dependencies

REWRITE ← the pre-refactor skill's `conditions-and-dependencies.md` (kept in full — the original
prose on the four status functions and AND/OR translation is accurate and worth reading as-is),
extended for the full grammar this refactor's `_lib.autosys_jil.conditions` implements: a fifth
status function (`terminated`), `exitcode()`, `VALUE()`, look-back, and cross-instance. Full
grammar reference: `autosys-reference/reference/conditions-grammar.md`.
`scripts/translate_conditions.py` produces a first-draft recommendation for every condition
string mechanically; this file is what a human reviews that draft against.

This is the single hardest translation surface in a JIL migration — Airflow's native dependency
model (task edges + `trigger_rule`) covers the AND-of-successes case cleanly and nothing else
natively.

## The five status functions

| Function | Meaning | Airflow equivalent |
|---|---|---|
| `success`/`s` | job_name last ran to SUCCESS | A normal upstream edge, default `trigger_rule="all_success"` |
| `failure`/`f` | job_name last ran to FAILURE | An edge with `trigger_rule="all_failed"` **only if `job_name` is the sole upstream**; with multiple upstreams, `all_failed` requires *every* upstream to fail, not "this specific one" — needs an evaluator task |
| `notrunning`/`n` | job_name is NOT currently in `STARTING`/`RUNNING`/`WAIT_REPLY`/`RESTART`/`SUSPENDED` [AS p.2437] | Usually not a task edge at all — a concurrency/mutex statement. `max_active_runs` (self-referential `n()`) or a shared `Pool` capacity 1 (cross-job `n()` — see `reference/troubleshooting.md`), never a dependency arrow |
| `done`/`d` | job_name is DONE (SUCCESS, FAILURE, or TERMINATED) [AS p.2436] | `trigger_rule="all_done"` |
| `terminated`/`t` | job_name was TERMINATED (killed) [AS p.2437] | No single stock `trigger_rule` distinguishes "killed" from "failed" — an evaluator task checking exit/termination status via the Airflow REST API/ORM, same pattern as mixed-function AND below |

## `exitcode()` [AS p.2439-2440]

```
condition: exitcode(job_a) = 4
```

→ `BranchPythonOperator`/`@task.branch` on an XCom-returned exit code, or (for the common case of
"treat this specific code as success") `BashOperator(skip_on_exit_code=...)`/a custom exit-code
handler. State which approach was used per job — this interacts with `max_exit_success`/
`success_codes` translation (`reference/alerting-and-sla.md`), don't translate the two
independently and risk a contradiction.

## `VALUE()` [AS p.2440]

```
condition: VALUE(OK_TO_RUN) > 2
```

→ an Airflow `Variable`/Asset-event condition check, or an evaluator task reading the value and
short-circuiting. If the global variable is set via `sendevent -E SET_GLOBAL` by another job in
the same run, prefer XCom over a global `Variable` — see
`reference/global-variables-and-templating.md`.

## Look-back [AS p.2440-2441]

```
condition: success(job1,00.30)
condition: success(jobA,0)          -- "since job1's own last run" (special case)
condition: success(jobA,9999)       -- indefinite look-back (same as no look-back at all)
```

→ `ExternalTaskSensor(execution_date_fn=...)` computing the right window, or an Asset with a time
window, delta stated explicitly either way. Never translate a look-back condition as a plain
upstream edge — that silently drops the time-bound semantics. The `0`/`9999` special cases
(`autosys-reference/reference/conditions-grammar.md`) need their own explicit handling, not a
generic HH.MM parse.

## Cross-instance [AS p.2438-2439]

```
condition: success(jobA^PRD)
```

→ a cross-Deployment signal: a cross-Deployment Asset (if both instances migrate to Astro), a
`TriggerDagRunOperator` via the Airflow REST API against the other Deployment, or (if `PRD`
stays on AutoSys during a phased cutover) a sensor polling AutoSys's own status via `autorep`/
AEWS. This is also a topology signal — see `migrate-topology-*` for which family applies once
both sides are known.

## Single-clause conditions (MECH)

`condition: success(extract_orders)` → a plain upstream edge. The common case; should be the
majority of a real estate.

## AND-combined conditions (MECH → JUDG)

`condition: success(job_a) and success(job_b)` → two upstream edges, default `trigger_rule`.
Still MECH if every clause is `success()`. Becomes JUDG the moment clauses mix functions
(e.g. `success(job_a) and done(job_b)`) — trigger rules apply per-task, not per-upstream, so a
mixed-function AND needs either splitting into edges with a compatible shared trigger_rule when
one exists, or a small evaluator task (a `@task` querying TaskInstance state per named upstream,
gating a `ShortCircuitOperator` immediately downstream).

## OR-combined conditions (REDESIGN)

`condition: success(job_a) or success(job_b)` has no native Airflow trigger_rule equivalent when
`job_a`/`job_b` are two of several upstreams and the OR applies to only a subset (Airflow's
`one_success` requires ALL of the task's upstreams to satisfy the same OR). Two approaches, in
order of preference:

1. **Redesign as an Asset race**: if both producers genuinely just need "whichever comes first,"
   have both update the same Asset and schedule the downstream on that Asset. Usually the more
   idiomatic Airflow 3 shape and avoids polling.
2. **Evaluator task**: same pattern as mixed-AND — a task checking both upstream states and
   short-circuiting. Use when the OR is genuinely about terminal state, not a produced artifact.

Nested boolean trees decompose into a combination of the above; write the decomposition into the
manifest as its own record so the report shows the source expression next to the chosen
implementation (`scripts/translate_conditions.py`'s `needs_decision` output does this).

## Hidden `sendevent` edges [plan §11.2]

A `sendevent -E FORCE_STARTJOB`/`KILLJOB`/etc. call embedded **inside another job's command**
(found by `_lib.autosys_jil.commands.analyze()`, surfaced as `hidden_control_flow` in
`manifest.commands`) creates a dependency edge with **no JIL representation to translate at
all**. Treat every one as a real dependency, same weight as a JIL-visible `condition:` — make it
an explicit `TriggerDagRunOperator`/Asset edge, or deliberately remove it with the reason
recorded, never leave it implicit in the migrated code.

## Cross-box and cross-DAG conditions

A condition referencing a job in a *different* box is a signal for the box → DAG boundary
decision (`reference/job-types/core-cmd-box.md`): two boxes whose jobs depend on each other by
name likely need to become two DAGs linked by an Asset (preferred) or
`TriggerDagRunOperator`/`ExternalTaskSensor` (if a hard wait is truly required), not two
TaskGroups pretending to be independent.

## What to write in the manifest per condition string

`translate_conditions.py`'s output row, per condition:

```json
{
  "job": "load_orders",
  "source_condition": "success(extract_orders) and notrunning(load_orders_prior_run)",
  "classification": "JUDG",
  "target": "edge: extract_orders >> load_orders; notrunning() clause dropped, replaced by max_active_runs=1 on the DAG",
  "delta": "AutoSys re-evaluated notrunning() at trigger time across all history; Airflow's max_active_runs only prevents concurrent runs of THIS dag, which is the intended behavior here -- no semantic loss expected, but confirm no other job also gates on load_orders' running state before dropping the clause",
  "needs_decision": false
}
```

`delta` is never optional, even when "none expected" — state it, so the reviewer knows it was
considered rather than missed.
