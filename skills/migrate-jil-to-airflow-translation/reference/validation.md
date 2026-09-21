---
topic: validation
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Validation gates

KEEP ← the pre-refactor skill's `validation.md`, with Gate 2/4/"recording" updated to the new
scripts. Each translated job/box advances through these gates before being marked `complete` in
`estate_manifest.json`. There's no AutoSys-specific static structure to check beyond what DAG
parsing already catches — this relies on standard Airflow/Astro tooling.

## Gate 1: Import

```
astro dev parse
```
or, without a running local environment, a plain `ast.parse()` plus an actual DAG-bag import
check inside an environment with the project's dependencies installed. Catches syntax errors and
import-time exceptions.

## Gate 2: Lint / structure

```
python3 scripts/dag_quality_gate.py --project-dir . --traceability traceability.json
```

Runs `astro dev parse`, `ruff check`, and the DAG-integrity `pytest` suite
(`_lib/fixtures/astro_project/tests/dags/test_dag_integrity.py`): no import errors,
owner/tags/`doc_md` present, no top-level `Variable.get`/DB calls, `catchup` explicit, `retries`
set, every task traceable via `traceability.json`.

## Gate 3: Execution

Run the migrated DAG for a representative logical date/window:
```
airflow dags test <dag_id> <logical_date>
```
Executes tasks locally without needing the full scheduler; surfaces runtime errors (bad
connections, missing variables, wrong paths) that Gate 1/2 can't catch.

## Gate 4: Output parity

```
python3 scripts/parity_check.py --autosys-history runs.csv --airflow-runs airflow_dagruns.json \
    --trace traceability.json --window 14d
```

Joins AutoSys run history to Airflow DAG runs **via `traceability.json`**, not naming
convention (fragile) — per-job status/duration/exit-code comparison table. For jobs outside the
comparison window or with side effects the tool can't observe:

- File-producing jobs: checksum or row-count the output files.
- Database-writing jobs: row counts and, where feasible, checksums of affected rows, computed
  from the AutoSys run's own output — not re-derived from the source system independently, since
  independent re-derivation can mask a bug that exists in both the old and new logic identically.
- Command jobs with no persistent output: compare exit codes and stdout/stderr content
  structurally (not byte-for-byte if timestamps are embedded).

A job with no clean way to verify parity (side effects the migration can't observe) gets
`deferred (reason: no parity signal available)` rather than a guessed `complete`.

## Gate 5: Safe re-run

Confirm the migrated task/DAG is safe to re-run (clear + retry) without double-applying side
effects — AutoSys jobs are often written assuming AutoSys's own retry semantics; verify
idempotency wasn't silently assumed away in translation, especially for file-transfer jobs
(`reference/job-types/file-transfer-ftp-scp.md`) where a naive retry can re-append or
double-deliver a file.

## Recording gate results

```
python3 -m autosys_jil.status --manifest estate_manifest.json advance <unit> --workflow translation --status <state> --note "..."
```

Each unit's history in `manifest.status.translation.units[<key>].history[]` should show which
gates passed and when, not just a final `complete`/`deferred` state — this is what lets
`_lib.autosys_jil.status summary --workflow translation` distinguish "verified complete" from
"marked complete without evidence."
