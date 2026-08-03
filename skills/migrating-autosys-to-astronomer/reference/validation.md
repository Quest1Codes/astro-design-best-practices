# Validation gates

Each translated job/box advances through these gates before being marked `complete` in the manifest. Unlike the Dagster-to-Airflow skill (which ships a bespoke `validate_dag.py` against a live Astro project), this skill relies on standard Airflow/Astro tooling — there's no AutoSys-specific static structure to check beyond what DAG parsing already catches.

## Gate 1: Import

```
astro dev parse
```
or, without a running local environment:
```
python3 -c "import ast; ast.parse(open('dags/<file>.py').read())"
```
plus an actual DAG-bag import (`python3 -m airflow.models.dagbag` style check, or simply importing the module inside an environment with the project's dependencies installed). Catches syntax errors and import-time exceptions.

## Gate 2: Lint / structure

Whatever the target project's existing lint config is (ruff/flake8, `astro dev pytest` structural tests if the scaffold ships any). If the project has no existing lint setup, don't invent one just for the migration — note it as a gap, not a blocker.

## Gate 3: Execution

Run the migrated DAG for a representative logical date/window:
```
airflow dags test <dag_id> <logical_date>
```
This executes tasks locally without needing the full scheduler, and surfaces runtime errors (bad connections, missing variables, wrong paths) that Gate 1 can't catch.

## Gate 4: Output parity

Compare the migrated DAG's output against the still-running AutoSys job's output for the *same* logical window:
- File-producing jobs: checksum or row-count the output files.
- Database-writing jobs: row counts and, where feasible, checksums of affected rows, computed from the AutoSys run's own output — not re-derived from the source system independently, since independent re-derivation can mask a bug that exists in both the old and new logic identically.
- Command jobs with no persistent output: compare exit codes and stdout/stderr content structurally (not byte-for-byte if timestamps are embedded).

A job with no clean way to verify parity (side effects the migration can't observe) gets `deferred (reason: no parity signal available)` rather than a guessed `complete`.

## Gate 5: Safe re-run

Confirm the migrated task/DAG is safe to re-run (clear + retry) without double-applying side effects — AutoSys jobs are often written assuming AutoSys's own retry semantics; verify idempotency wasn't silently assumed away in translation, especially for FT (file transfer) jobs where a naive retry can re-append or double-deliver a file.

## Recording gate results

Each manifest record's `validation` field should list which gates passed and when, not just a final `complete`/`deferred` state — this is what lets `scripts/status.py summary` distinguish "verified complete" from "marked complete without evidence."
