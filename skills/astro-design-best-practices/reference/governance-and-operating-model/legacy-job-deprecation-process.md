# Legacy-Job Deprecation Process During Migration

Decommissioning AutoSys jobs is as important as building Airflow DAGs. Jobs left running in AutoSys after their Airflow equivalent is live create confusion, consume licenses, and can cause data duplication. A formal deprecation process prevents "zombie jobs" from lingering indefinitely.

## Deprecation Gate Requirements

A legacy AutoSys job is eligible for deprecation only when all of the following are true:
1. The equivalent Airflow DAG has passed N consecutive reconciliation cycles (see topic 088).
2. All downstream systems have been confirmed to receive data from the Airflow pipeline (not AutoSys).
3. A blast-radius assessment has confirmed no undocumented consumers of the AutoSys job's output remain [B1].
4. The deactivation has been communicated to all stakeholder teams with a defined burn-in period.

## The Deprecation Sequence

### Phase 1: Scream Test (Non-Production First)
Deactivate the AutoSys job in a non-production environment and monitor for complaints or downstream failures for a defined period (1–2 weeks) [B1]. This surfaces undocumented dependencies that were not caught in the dependency audit.

### Phase 2: Deactivation in Production
- Set the AutoSys job to `INACTIVE` (or equivalent suspended state) — **do not delete** [B1].
- Define a burn-in period (typically 2–4 weeks for non-critical jobs; 4–8 weeks for SLA-critical jobs).
- Monitor downstream systems and stakeholder channels for any complaints.

### Phase 3: Archive AutoSys Configuration
Before permanent deletion, export the JIL definition for the job and store it in your version-controlled archive repository [B1]. This satisfies audit trail requirements and provides a rollback reference.

### Phase 4: Permanent Decommission
- Delete the job from AutoSys.
- Remove from the active inventory tracker.
- Document the decommission date, the replacing Airflow DAG ID, and the approver in your migration log.

## Governance Controls

| Control | Purpose |
|---|---|
| **Inventory tracker** (spreadsheet or JIRA board) | Track every job's status: `in-migration`, `parallel-run`, `airflow-active`, `autosys-deactivated`, `decommissioned`. |
| **Mandatory blast-radius assessment** | Prevents decommissioning a job that downstream teams still depend on. |
| **Burn-in period before deletion** | Provides a safety window to catch missed dependencies. |
| **JIL archive in Git** | Enables rollback reference and audit evidence. |

## Sources

[B1] Enterprise migration guidance & Astronomer migration framework — Scream test, burn-in period, blast-radius assessment, and JIL archival (accessed 2026-08-11)
