# AEWS REST API Surface Parity → Airflow REST API Design

AutoSys Web Services (AEWS) is the AutoSys **control-plane REST API** — the programmatic interface for triggering jobs, changing job status, querying job state, and managing events in the AutoSys engine. It is distinct from AutoSys's `job_type: WS` (which is an outbound web-service job type). AEWS is inbound: it's how external systems tell AutoSys what to do [B1].

The Airflow REST API (Stable API, introduced in Airflow 2.0) is the direct equivalent — it is the control-plane HTTP API for triggering DAG runs, querying task state, and managing Airflow objects [B2].

## API Surface Parity Mapping

{syn: AEWS `FORCE_START_JOB` → Airflow `POST /api/v1/dags/{dag_id}/dagRuns`}

| AEWS Operation | Airflow REST API Equivalent |
|---|---|
| **`FORCE_START_JOB`** (trigger a job immediately) | `POST /api/v1/dags/{dag_id}/dagRuns` |
| **`ON_ICE`** / **`OFF_ICE`** (hold/release a job) | `PATCH /api/v1/dags/{dag_id}` with `{"is_paused": true/false}` |
| **`KILL_JOB`** (abort a running job) | `DELETE /api/v1/dags/{dag_id}/dagRuns/{dag_run_id}` or `POST .../taskInstances/{task_id}/clearTaskInstances` |
| **`CHANGE_STATUS SUCCESS`** (manually mark success) | `PATCH /api/v1/dags/{dag_id}/updateTaskInstancesState` with `{"state": "success"}` |
| **Query job status** (`autorep -J`) | `GET /api/v1/dags/{dag_id}/dagRuns` |
| **Query task status** | `GET /api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}` |
| **List all jobs** (`autorep -J ALL`) | `GET /api/v1/dags?limit=100&offset=0` |

## Authentication

| AEWS | Airflow REST API |
|---|---|
| CA EEM session token / HTTP Basic (over HTTPS) | HTTP Basic Auth or Bearer token (Astro API token) [B2] |

On Astro, the recommended authentication for REST API access is a **Deployment-scoped API token** (not user credentials):
```bash
curl -X POST "https://<deployment-webserver-url>/api/v1/dags/my_dag/dagRuns" \
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
[B2] Apache Airflow REST API Docs (Stable API, Airflow 2.0+) — DAG run trigger (`POST /dagRuns`), task state update, DAG pause (`PATCH /dags`), `dag_run_id` idempotency, Astro deployment token authentication (accessed 2026-08-18)
