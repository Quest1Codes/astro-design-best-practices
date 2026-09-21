---
topic: troubleshooting
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [windows]
---

# Troubleshooting: known failure classes

KEEP ← the pre-refactor skill's `troubleshooting.md`, appended with the new defects this
refactor's own audit found. This file grows as real migrations hit real failures. Each entry:
symptom, root cause, fix-the-class (not the instance) response — per the "fix classes, not
instances" hard rule.

## "Box succeeded in Airflow but the equivalent AutoSys box would have failed"

**Cause**: AutoSys box failure semantics depend on `box_terminator` and which children are
marked as affecting the box's overall status — not every child job failure necessarily fails the
box. A naive TaskGroup translation treats every child's failure as box-failing.

**Fix the class**: check each child's role in the box's overall status before assuming "any
child fails → box fails" is correct. Record the actual rule used per box in the manifest.

## "Condition string references a job that no longer exists in the export"

**Cause**: stale or partial JIL export, or the referenced job was deleted but the condition
string wasn't cleaned up (`Instance.unknowns.unresolved_refs`, `kind: "condition"`).

**Fix the class**: don't silently drop the condition. Flag the record `deferred (reason:
condition references unknown job <name> — confirm with platform team whether this is stale)`.
Per `assess-estate-inventory/reference/unknowns-and-escalation.md`, AutoSys itself evaluates an
undefined-job condition as `false` — that may be intentional; don't guess.

## "notrunning() condition translated to max_active_runs, but the job still runs concurrently in practice"

**Cause**: the `notrunning()` clause was checking a *different* job's running state, not this
job's own — `notrunning()` guards can reference any job, not just self. A `max_active_runs` fix
only addresses self-referential `notrunning()`.

**Fix the class**: for cross-job `notrunning()` clauses, use a shared Airflow `Pool` capacity 1
across both DAGs/tasks involved, not a per-DAG `max_active_runs`.

## "Calendar-driven schedule fires on a date the source job didn't run"

**Cause**: the custom Timetable's calendar data file is out of sync with the actual
`run_calendar`/`exclude_calendar` combination, or `cron_equivalent()` was bypassed and a
hand-written cron string used instead.

**Fix the class**: never hand-write a cron string for a calendar-driven job — always go through
`translate_calendars.py`, which only emits cron when `cron_equivalent()` proves exact equivalence
over the horizon. Diff the generated schedule's next N fire dates against `autorep` history
(or `history_stats.py`'s output, if collected) before trusting a custom Timetable.

## "FT/attribute not recognized by the inventory script"

**Cause**: file-transfer job JIL attributes and any customer-specific extension are the least
standardized surface across AutoSys/WA AE versions/shops.

**Fix the class**: `_lib.autosys_jil.parser` captures unrecognized attributes into
`Job.extras`/`Instance.unknowns.attributes` rather than dropping them — check those before
translating an FT/FTP/SCP job, and verify the actual attribute meaning against the customer's
current export or the platform team rather than assuming it matches an older version's syntax.

## "`exitcode()` condition lost in translation" (new, this refactor)

**Cause**: `exitcode()` and `max_exit_success`/`success_codes` were translated independently by
different people/passes, producing a contradiction (e.g. the condition checks for exit code 4
while `max_exit_success` was set assuming 4 means success).

**Fix the class**: always translate a job's `exitcode()` conditions and its
`max_exit_success`/`success_codes` attributes together, in the same pass — see
`reference/alerting-and-sla.md`'s note on this.

## "Look-back window ignored" (new, this refactor)

**Cause**: a look-back condition (`success(job,00.30)`) was translated as a plain upstream edge,
dropping the time-bound semantics entirely.

**Fix the class**: `translate_conditions.py` flags every look-back condition with
`needs_decision: true` specifically so it can't be silently accepted as a plain edge — if a
generated equivalence row for a look-back condition shows a plain edge as the target, that's a
review miss, not a valid translation.

## "Hidden `sendevent` in a script started a job Airflow doesn't know about" (new, this refactor)

**Cause**: a `sendevent -E FORCE_STARTJOB` call embedded inside another job's `command:` string
creates a real dependency with zero JIL representation — plan's own audit calls this the "#1
source of surprise in migrations."

**Fix the class**: `command_analysis.py`'s `hidden_control_flow` findings are not optional
reading — every hidden edge gets an explicit `TriggerDagRunOperator`/Asset edge or a documented,
reasoned removal, same discipline as a JIL-visible `condition:`.

## "Windows command scheduled on a Linux worker" (new, this refactor)

**Cause**: Astro workers are Linux; a `.bat`/`.ps1`/`cmd /c` command (flagged `os_hint: windows`
by `command_analysis.py`) has no default execution target.

**Fix the class**: every `os_hint: windows` job needs one of the three explicit options in
`reference/job-types/core-cmd-box.md`'s Windows section (containerize with PowerShell Core on
Linux, bridge via `SSHOperator`/WinRM to a residual Windows host, or re-platform) — never
scaffold a `BashOperator` for a Windows command and hope.
