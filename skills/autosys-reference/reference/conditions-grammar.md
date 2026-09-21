---
topic: conditions-grammar
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2435, 2436, 2437, 2438, 2439, 2440, 2441]
last_verified: 2026-09-17
confidence: cited
signals: [or_conditions, lookback, cross_instance, mutex_n]
---

# `condition:` grammar [AS p.2435 "condition Attribute -- Define Starting Conditions for a Job"]

Implemented in full by `_lib/autosys_jil/conditions.py`; every production below has a
corresponding test in `_lib/autosys_jil/tests/test_conditions.py`, including the PDF's own
worked examples.

## Grammar

```
expr        := term (("AND" | "OR") term)*
term        := "(" expr ")" | status_fn | exitcode_fn | value_fn
status_fn   := STATUS "(" jobref ["," lookback] ")"
STATUS      := success|s | failure|f | done|d | notrunning|n | terminated|t
exitcode_fn := "exitcode" "(" jobref ["," lookback] ")" op INT
value_fn    := "VALUE" "(" GLOBAL_NAME ")" op literal
jobref      := JOBNAME ["^" INSTANCE]
lookback    := HHHH "." MM | INT
op          := "=" | "!=" | "<" | ">" | "<=" | ">="
```

`AND`/`OR` may be written as words or symbols (`&`, `|`), case-insensitively; spacing around
conditions and delimiters is optional; a job name containing `:` is escaped with `\`
[AS p.2436]. Parentheses force precedence and the AutoSys engine evaluates left to right
[AS p.2436] — `_lib.conditions` uses conventional AND-over-OR precedence and records `depth`
for a human reviewer, since the PDF does not state a documented precedence outside explicit
parentheses.

## Case rule [AS p.2437]

> You can use uppercase or lowercase characters to define conditions. You cannot mix case.

`success(JobA)` and `SUCCESS(JobA)` are both legal; `Success(JobA)` is a parse error. Enforced by
`conditions.py`'s `_Parser.term()`.

## Status functions [AS p.2436-2437]

| Function | Short form | True when `job_name`'s status is |
|---|---|---|
| `success` | `s` | `SUCCESS` |
| `failure` | `f` | `FAILURE` |
| `done` | `d` | `SUCCESS`, `FAILURE`, or `TERMINATED` |
| `notrunning` | `n` | anything **except** `STARTING`, `RUNNING`, `WAIT_REPLY`, `RESTART`, or `SUSPENDED` |
| `terminated` | `t` | `TERMINATED` (killed) |

`notrunning` is the AutoSys-native mutex primitive — the PDF's own example uses it to keep a DB
dump and a file backup from running concurrently: `condition: notrunning(DB_DUMP) AND
notrunning(BACKUP)` [AS p.2438]. When translating, decide per use: is this genuinely expressing
"X must complete before Y" (a dependency → `trigger_rule`/Asset), or "X and Y must never overlap"
(a mutex → an Airflow `pool` with 1 slot, or task-level locking)? See
`migrate-jil-to-airflow-translation/reference/conditions-and-dependencies.md`.

`max_exit_success` changes what counts as `success()`: a job exiting with a code `<=
max_exit_success` is treated as `SUCCESS`; everything else as `FAILURE`. All other status values
are internally determined and not configurable [AS p.2437].

## Exit-code and global-variable functions [AS p.2439-2440]

```
exitcode(job_name) op value          -- e.g. exitcode(JobA) = 4
VALUE(global_name) op value          -- e.g. VALUE(OK_TO_RUN) > 2
```

`op` is one of `= != < > <= >=`. A global-variable value must evaluate true to satisfy the
dependency; global names are up to 64 chars (`a-zA-Z0-9._#-`); comparison values up to 100 chars,
quoted if they contain spaces [AS p.2440].

## Look-back [AS p.2440-2441]

Applies to job-status, cross-instance, and exit-code conditions — **not** to `VALUE()`
[AS p.2436, p.2440]. Syntax: `status(job_name, HHHH.MM)` or `exitcode(job_name, HHHH.MM) op
value`; `HHHH` is 0-9999 hours, `MM` is 0-59 minutes (write `00.30` for "30 minutes", not `.30`
— AutoSys parses `30` alone as 30 *hours*) [AS p.2441]. A literal `:` may be used instead of `.`
if escaped: `success(JobA,01\:00)`.

Two values carry special meaning:

- **`0`** — look at the condition job's last end time and the dependent job's last end time; the
  condition is satisfied only if the condition job has run *since* the dependent job's own last
  run. This is "did this run since I last ran," not "did this ever run."
- **`9999`** — look back indefinitely (pre-4.5.1 default behavior); equivalent to specifying no
  look-back at all.

`_lib.conditions.Status.lookback` / `ExitCode.lookback` carries the raw `"HHHH.MM"` or `"N"`
string; `_lib.history.sla_breaches()` and related stats do not currently interpret look-back
semantics — that is a translation-time decision (`ExternalTaskSensor(execution_date_fn=...)` vs.
an Asset with a time window), not an assessment-time one.

## Cross-instance dependencies [AS p.2438-2439]

`condition: status(JOB_NAME^INS)` — `^` marks the job as residing on another instance; `INS` is
the external instance's 3-uppercase-alphanumeric ID. Requires a matching `insert_xinst` block for
that instance to be a fully resolved reference (unresolved cross-instance refs are recorded in
`Instance.unknowns.unresolved_refs` with `kind: "condition"`). Multiple cross-instance
dependencies are allowed in one condition.

```
condition: success(jobA) AND success(jobB^PRD)
```

## Undefined-job rule [AS p.2436]

> If you specify a condition for an undefined job, the condition evaluates as false and any jobs
> dependent on the condition do not run.

`_lib.parser.finalize()` records every condition reference to a job not present in the export
(`unresolved_refs`, `kind: "condition"`) — the assessment must distinguish "genuinely undefined"
from "defined in a different JIL file not included in this export" before treating either as a
real defect.

## Worked examples (verbatim from the PDF, all covered by `test_conditions.py`)

```
condition: success(JobB)
condition: (success(JobA) AND success(JobB)) OR (done(JobD) AND done(JobE))
condition: failure(JobA,00.30) AND success(JobC^XYZ,01.30)
condition: notrunning(DB_DUMP) AND notrunning(BACKUP)
condition: exitcode(JobA) = 4
condition: VALUE(OK_TO_RUN)>2
condition: success(BACKUP) AND value(TODAY)=Friday
```
