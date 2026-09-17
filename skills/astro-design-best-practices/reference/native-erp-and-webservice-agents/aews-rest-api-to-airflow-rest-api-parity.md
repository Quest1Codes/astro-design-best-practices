# AEWS REST API Surface Parity → Airflow REST API Design

AutoSys Web Services (AEWS) is the AutoSys **control-plane REST API** — the programmatic interface for triggering jobs, changing job status, querying job state, and managing events in the AutoSys engine. It is distinct from AutoSys's `job_type: WS` (which is an outbound web-service job type). AEWS is inbound: it's how external systems tell AutoSys what to do [B1].

The Airflow REST API (Stable API, introduced in Airflow 2.0) is the direct equivalent — it is the control-plane HTTP API for triggering DAG runs, querying task state, and managing Airflow objects [B2].

## API Surface Parity Mapping

{syn: AEWS `FORCE_START_JOB` → Airflow `POST /api/v2/dags/{dag_id}/dagRuns`}

| AEWS Operation | Airflow REST API Equivalent |
|---|---|
| **`FORCE_START_JOB`** (trigger a job immediately) | `POST /api/v2/dags/{dag_id}/dagRuns` |
| **`ON_ICE`** / **`OFF_ICE`** (hold/release a job) | `PATCH /api/v2/dags/{dag_id}` with `{"is_paused": true/false}` |
| **`KILL_JOB`** (abort a running job) | `PATCH .../dagRuns/{dag_run_id}/updateTaskInstancesState` (or the Airflow UI's "Mark state as failed" action) with `{"new_state": "failed"}` on the running task instance — **correction**: an earlier draft of this row mapped `KILL_JOB` to `DELETE .../dagRuns/{dag_run_id}` or `.../clearTaskInstances`, which is wrong: `DELETE` on a DagRun removes the *record*, and `clearTaskInstances` resets state for a *re-run* — neither sends a stop signal to a currently-running task/pod. Marking the running task instance's state (which the scheduler/executor interprets as a signal to terminate the process) is the actual mechanism a UI "kill" action uses [B2]. `NEEDS_EXEC_CHECK`: the exact REST endpoint path for a single-task-instance state update on a *running* (not yet terminal) task wasn't independently re-verified on this pass — confirm against the live Airflow 3 API reference before scripting this. |
| **`CHANGE_STATUS SUCCESS`** (manually mark success) | `PATCH /api/v2/dags/{dag_id}/updateTaskInstancesState` with `{"state": "success"}` |
| **Query job status** (`autorep -J`) | `GET /api/v2/dags/{dag_id}/dagRuns` |
| **Query task status** | `GET /api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}` |
| **List all jobs** (`autorep -J ALL`) | `GET /api/v2/dags?limit=100&offset=0` |

## Authentication

| AEWS | Airflow REST API |
|---|---|
| CA EEM session token / HTTP Basic (over HTTPS) | HTTP Basic Auth or Bearer token (Astro API token) [B2] |

On Astro, the recommended authentication for REST API access is a **Deployment-scoped API token** (not user credentials):
```bash
curl -X POST "https://<deployment-webserver-url>/api/v2/dags/my_dag/dagRuns" \
  -H "Authorization: Bearer <deployment-api-token>" \
  -H "Content-Type: application/json" \
  -d '{"conf": {"source_date": "2026-08-18"}}'
```

## Key Differences

| Aspect | AEWS | Airflow REST API |
|---|---|---|
| **Job granularity** | Individual job within a box | Entire DAG run (task-level via separate endpoint) |
| **State model** | `RUNNING`, `SUCCESS`, `FAILURE`, `ON_ICE`, `QUE_WAIT`, etc. | `running`, `success`, `failed`, `queued`, `up_for_retry` |
| **Idempotency of trigger** | `FORCE_START_JOB` is additive; multiple calls start multiple runs | `POST /dagRuns` creates a new run; same `run_id` prevents duplicate if specified |

## Important: Specify `dag_run_id` for Idempotent Triggers

To prevent double-trigger from retry/at-least-once delivery of AEWS events, always supply an explicit `dag_run_id` in REST API triggers [B2]:

```json
{
  "dag_run_id": "manual__finance_reconciliation_20260818",
  "conf": {"batch_date": "2026-08-18"}
}
```

If the same `dag_run_id` is submitted twice, Airflow returns a 409 Conflict — preventing duplicate execution [B2].

## Sources

[B1] Broadcom AutoSys AEWS (AutoSys Web Services) Documentation — `FORCE_START_JOB`, `ON_ICE`/`OFF_ICE`, `KILL_JOB`, `CHANGE_STATUS` events via REST API, AEWS OpenAPI/Swagger surface (accessed 2026-08-18)
[B2] Apache Airflow REST API Docs — DAG run trigger (`POST /dagRuns`), task state update, DAG pause (`PATCH /dags`), `dag_run_id` idempotency, Astro deployment token authentication (accessed 2026-08-18). **Correction**: this file originally labeled the API "Stable API, Airflow 2.0+" and used `/api/v1/` paths throughout (now corrected to `/api/v2/` above). Airflow 3 shipped a new v2 REST API — see Astronomer Docs, Airflow API on Astro: https://www.astronomer.io/docs/astro/airflow-api and the Airflow 3 upgrade guide ("Airflow 3 uses a new v2 version of the Airflow REST API"): https://www.astronomer.io/docs/learn/airflow-upgrade-2-3#other-changes (tier 1, added on doc-verification review). If the target Astro Deployment still runs Airflow 2.x, `/api/v1/` remains correct for that Deployment specifically — treat the version as a per-Deployment fact to confirm, not a global constant.
