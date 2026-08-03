# Troubleshooting: known failure classes

This file grows as real migrations hit real failures. Each entry: the symptom, the root cause, the fix-the-class (not the instance) response. Seed entries below are anticipated from JIL semantics; replace/expand with actually-observed failures as they occur, per SKILL.md's "fix classes, not instances" rule.

## "Box succeeded in Airflow but the equivalent AutoSys box would have failed"

**Cause**: AutoSys box failure semantics depend on `box_terminator` and which children are marked as affecting the box's overall status — not every child job failure necessarily fails the box. A naive TaskGroup translation treats every child's failure as box-failing.

**Fix the class**: when translating a box, check each child's role in the box's overall status (this is not always explicit in JIL and may require asking the platform team or observing `autorep` history) before assuming "any child fails → box fails" is correct. Record the actual rule used per box in the manifest.

## "Condition string references a job that no longer exists in the export"

**Cause**: stale or partial JIL export; the estate has drifted from what's on disk, or the referenced job was deleted but the condition string wasn't cleaned up (this happens in real AutoSys estates).

**Fix the class**: don't silently drop the condition. Flag the record `deferred (reason: condition references unknown job <name> — confirm with platform team whether this is stale)`. Do not guess that it's safe to remove.

## "n() condition translated to max_active_runs, but the job still runs concurrently in practice"

**Cause**: the `n()` clause was checking a *different* job's running state, not this job's own — `n()` guards can reference any job, not just self. A max_active_runs fix only addresses self-referential `n()`.

**Fix the class**: for cross-job `n()` clauses, use a shared Airflow `Pool` with capacity 1 across both DAGs/tasks involved, not a per-DAG `max_active_runs`. Note this distinction in `reference/conditions-and-dependencies.md` usage going forward.

## "Calendar-driven schedule fires on a date the source job didn't run"

**Cause**: the custom Timetable's calendar data file is out of sync with the actual `run_calendar`/`exclude_calendar` combination, or the calendar's date range doesn't extend far enough into the future.

**Fix the class**: always diff the generated schedule's next N fire dates against `autorep` history (or a fresh calendar export) before trusting a custom Timetable — don't validate a calendar Timetable by reading the code, validate it by comparing generated dates.

## "FT job attribute not recognized by the inventory script"

**Cause**: file-transfer job JIL attributes are the least standardized across AutoSys/WA AE versions (per the "do not invent JIL syntax" hard rule).

**Fix the class**: `scripts/jil_inventory.py` captures unrecognized attributes into a record's `raw_extra` field rather than dropping them — check that field for any FT job before translating, and verify the actual attribute meaning against the customer's current Broadcom docs or platform team rather than assuming it matches an older version's syntax.
