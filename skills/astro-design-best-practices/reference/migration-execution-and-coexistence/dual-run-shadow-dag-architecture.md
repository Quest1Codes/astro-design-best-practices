# Dual-Run / Shadow-DAG Architecture During Coexistence

A "big bang" cutover — disabling AutoSys on Friday night and enabling Airflow Monday morning — is the highest-risk migration approach and should be avoided for any production workload with a meaningful SLA. The dual-run / shadow-DAG architecture reduces risk by running both systems in parallel, with Airflow in a "passive" mode until confidence is established.

## Core Principle: AutoSys is Source of Truth Until Cutover

During coexistence, AutoSys retains final authority over production execution. Airflow runs shadow passes but does not own the production outcome until the formal cutover event per domain (see topic 089) [B1][B2].

## Three Coexistence Modes (in sequence)

### Mode 1: AutoSys-Triggered Airflow (Bridge Phase)

AutoSys triggers the Airflow DAG via the **Airflow REST API** upon completion of the upstream box [B1][B3]:

```
AutoSys Box A completes
  → AutoSys Job (HTTP step) calls Airflow API: POST /api/v1/dags/{dag_id}/dagRuns
  → Airflow DAG runs, but writes to a shadow/staging output location
  → AutoSys continues as the production truth
```

Use case: validates Airflow's execution logic and network connectivity without any production impact.

### Mode 2: Side-by-Side Execution (Parity Phase)

Both AutoSys and Airflow run independently on the same trigger (e.g., time-based or file sensor):
- AutoSys writes to the **production target**.
- Airflow writes to a **parallel staging schema or S3 path prefix** (e.g., `s3://prod-bucket/shadow/{dag_id}/`).
- A reconciliation DAG (see topic 088) compares the outputs after each cycle [B1][B2].

This is the critical validation phase. A DAG should not progress to cutover until it passes N consecutive reconciliation cycles with zero discrepancies.

### Mode 3: Airflow-Controlled, AutoSys on Standby (Final Readiness Phase)

Shortly before cutover:
- Airflow DAG is unpaused to write to the **production target**.
- The corresponding AutoSys job is set to `ON_HOLD` but not decommissioned [B2].
- AutoSys remains the rollback mechanism (see topic 090).

## Key Design Rules

| Rule | Rationale |
|---|---|
| **Do not write to the same production target from both systems simultaneously** | Risk of duplicate records, data collisions, or constraint violations [B1]. |
| **Use feature flags (Airflow Variables) to control shadow vs. production output paths** | Enables instant switching between shadow and production mode without a DAG code change [B2]. |
| **Do not decommission AutoSys agents during coexistence** | These are your rollback mechanism. Decommission only after the Airflow DAG has proven stable for at least 2–4 production cycles post-cutover [B2]. |
| **Migrate in logical clusters, not job-by-job** | Dependencies within a business domain should move together to avoid cross-system dependency complexity [B1][B2]. |

## Sources

[B1] Astronomer Docs & Migration Guidance — AutoSys-to-Airflow coexistence patterns (accessed 2026-08-11)
[B2] BatchFoundry / Enterprise migration community — Dual-run architecture, staging output paths, and feature flag kill switches (accessed 2026-08-11)
[B3] Apache Airflow REST API Docs — `POST /api/v1/dags/{dag_id}/dagRuns` endpoint for external triggering (accessed 2026-08-11)
