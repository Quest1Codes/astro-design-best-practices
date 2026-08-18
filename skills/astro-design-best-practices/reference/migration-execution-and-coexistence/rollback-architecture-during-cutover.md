# Rollback Architecture During Cutover

A production cutover without a pre-tested, documented rollback plan is a critical risk. The rollback architecture must be executable in **minutes**, not hours — especially for financial batch workloads with hard SLA deadlines.

## Core Principle: Keep AutoSys on Active Standby

The AutoSys environment must remain fully operational (`ON_HOLD` jobs, not decommissioned agents) throughout the cutover window and for the observation period afterward. Decommissioning AutoSys infrastructure before Airflow has proven stable removes the rollback option [B1][B2].

## The Rollback Trigger Decision

Define explicit **Go/No-Go criteria** before the cutover window. If these are not met by a defined time threshold, automatically trigger rollback rather than attempting live fixes during the production window [B1][B2]:

| Condition | Threshold | Action |
|---|---|---|
| First Airflow production run fails | Any failure | Immediate rollback consideration |
| Data volume discrepancy vs. AutoSys baseline | > 0.1% delta on financial data | Rollback if not resolved within 30 min |
| SLA deadline at risk | < 60 min to SLA breach | Trigger rollback immediately |
| Downstream system reports data format error | Any error | Pause and assess |

## Rollback Execution Steps

### Step 1: Stop Airflow Production Writes
- Pause the Airflow DAG immediately: `PATCH /api/v1/dags/{dag_id}` with `{"is_paused": true}` [B3].
- Or toggle the kill-switch Airflow Variable (`ACTIVE_SCHEDULER=autosys`) to redirect output paths via feature flag (see topic 087).

### Step 2: Assess Data State
- Determine how far the Airflow run progressed.
- Run a checksum/reconciliation script against the production target to identify any "orphaned" partial writes from the failed Airflow run [B1][B2].
- If partial data was written to the production target, truncate or delete it to return to the last known-good AutoSys state.

### Step 3: Re-Activate AutoSys
- Release the `ON_HOLD` status on the AutoSys box [B1].
- If AutoSys state is stale (e.g., its last run was N hours ago due to the observation period), trigger a manual run from the last successful completion point.
- Confirm the AutoSys run picks up correctly and produces expected output.

### Step 4: Communicate and Document
- Notify stakeholders of the rollback, the reason, and the estimated time to SLA delivery.
- Document the failure root cause and create a remediation plan.
- Do not reattempt cutover until the root cause is fixed and a new dual-run validation cycle is completed.

## Design Rules for Rollback Readiness

| Rule | Rationale |
|---|---|
| **Never share a metadata DB between AutoSys and Airflow** | DB schema changes during Airflow upgrade may make rollback impossible [B1][B2]. |
| **Do not attempt live hotfixes during a cutover** | Pressure to fix quickly in production introduces new bugs. Roll back first, fix in dev/staging. |
| **Test the rollback in staging before production cutover** | Run a mock cutover-and-rollback drill in a staging environment to validate execution time and completeness [B1]. |
| **Idempotency is mandatory** | Airflow may have partially executed tasks before rollback. AutoSys re-running those same steps must not cause data duplication [B1]. |

## Sources

[B1] Enterprise migration guidance — Rollback architecture, `ON_HOLD` standby, and data integrity during cutover reversal (accessed 2026-08-11)
[B2] BatchFoundry / Enterprise migration community — Go/No-Go criteria, parallel infrastructure, and rollback scripts (accessed 2026-08-11)
[B3] Apache Airflow REST API Docs — `PATCH /api/v1/dags/{dag_id}` for programmatic pause (accessed 2026-08-11)
