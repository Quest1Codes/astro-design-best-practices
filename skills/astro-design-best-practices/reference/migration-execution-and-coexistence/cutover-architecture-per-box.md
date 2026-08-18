# Cutover Architecture Per Box

An AutoSys "box" represents a group of jobs with shared dependencies that execute as a logical unit. In Airflow, the equivalent is typically a DAG (or a set of DAGs within a domain). Cutover must be planned at the box/domain level — not job-by-job — to avoid leaving broken cross-job dependencies in a half-migrated state.

## Pre-Conditions for Cutover

A domain/box is eligible for cutover only when all of the following are true:
- The shadow Airflow DAG has passed N consecutive reconciliation cycles (see topic 088).
- All downstream cross-domain dependencies have been mapped (AutoSys `CONDITION` dependencies that reference this box).
- The cutover window (low-traffic period) is agreed upon with business owners.
- The rollback plan is documented and pre-tested (see topic 090).

## The Cutover Sequence (Per Box/Domain)

### Step 1: Quiesce the AutoSys Box
- At the start of the cutover window, set all AutoSys jobs in the target box to `ON_HOLD` [B1][B2].
- Do **not** deactivate or delete them — `ON_HOLD` preserves the ability to revert instantly.
- Confirm the last successful AutoSys run completed without errors and its output is in the expected production location.

### Step 2: Cut Cross-Domain Dependencies

For any downstream boxes in AutoSys that depended on the completion of this box:
- **Option A** (AutoSys dependency remains): Create a custom Airflow operator or sensor that polls AutoSys's API or status file to confirm the AutoSys upstream job state. Use an `ExternalTaskSensor` pattern pointing at a proxy task [B1].
- **Option B** (Dependency migrated together): If the downstream box is also being cut over in the same window, use Airflow **Datasets** or `ExternalTaskSensor` to wire the Airflow-to-Airflow dependency [B1][B2].

### Step 3: Unpause the Airflow DAG

- Set the Airflow DAG's `is_paused = False` (via Airflow UI or API: `PATCH /api/v1/dags/{dag_id}`) [B3].
- Ensure the DAG is now writing to the **production target** (not the shadow path).
- Confirm the first production Airflow run completes successfully.

### Step 4: Validate

- Confirm downstream AutoSys jobs that depend on this box's output are receiving the Airflow-produced data correctly.
- Run a final reconciliation check against the last AutoSys run.

### Step 5: Observe (2–4 Production Cycles)

- Keep AutoSys `ON_HOLD` (not decommissioned) for the next 2–4 production cycles.
- Only after the Airflow DAG proves stable should the AutoSys box be permanently decommissioned.

## Cross-Box Dependency Management During Partial Migration

When Box A (in Airflow) depends on Box B (still in AutoSys):
- Create an Airflow task that calls AutoSys's job status API or checks for a completion sentinel file to confirm Box B finished before proceeding [B1].
- Avoid tight coupling: the check should be a deferrable sensor (to avoid blocking a worker slot) [B3].

## Sources

[B1] Enterprise migration guidance — AutoSys `ON_HOLD` state management, cross-domain dependency handling (accessed 2026-08-11)
[B2] Apache Airflow Docs — Datasets, ExternalTaskSensor, and cross-DAG dependency patterns (accessed 2026-08-11)
[B3] Apache Airflow REST API Docs — `PATCH /api/v1/dags/{dag_id}` for programmatic pause/unpause (accessed 2026-08-11)
