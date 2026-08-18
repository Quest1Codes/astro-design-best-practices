# autorep Ad-Hoc Reporting Query Patterns → Airflow Metadata-DB Reporting Design

`autorep` is AutoSys's primary read-only reporting CLI. It queries the AutoSys Event Server (database) and produces formatted text reports about jobs, machines, calendars, and global variables [B1]. It is the tool that operations teams use for ad-hoc operational queries — the equivalent of what you'd do with SQL against the Airflow metadata DB.

## autorep Pattern → Airflow Equivalent

{syn: AutoSys `autorep -J` → Airflow REST API or `dag_run`/`task_instance` table query}

| AutoSys `autorep` Query | Airflow Equivalent |
|---|---|
| `autorep -J ALL -s` (all job statuses) | Airflow UI DAGs list; or REST: `GET /api/v1/dags` + `GET /api/v1/dagRuns` |
| `autorep -J <job_name> -d` (last run detail) | REST: `GET /api/v1/dags/{dag_id}/dagRuns` + `GET /api/v1/taskInstances` |
| `autorep -J <name> -s -r N` (last N runs) | SQL: `SELECT * FROM task_instance WHERE dag_id='...' ORDER BY start_date DESC LIMIT N` |
| `autorep -M <machine>` (machine status) | No direct equivalent; monitor worker pods via Deployment Analytics (Astro) |
| `autorep -c <calendar>` (calendar definition) | No direct equivalent; Airflow timetables are code, not queryable via CLI |
| `autorep -G <var_name>` (global variable value) | REST: `GET /api/v1/variables/{variable_key}` |

## Airflow Metadata DB Key Tables

Airflow stores all scheduling state in PostgreSQL (recommended) [B2]:

| Table | Content | Primary Use |
|---|---|---|
| `dag_run` | Each DAG execution (state, start, end, `logical_date`) | Run history, SLA tracking |
| `task_instance` | Each task execution per DAG run (state, duration, try_number) | Task-level forensics, duration analytics |
| `dag` | DAG definitions registered with the scheduler | Inventory of active DAGs |
| `variable` | Airflow Variables (key-value store) | Current variable state |
| `log` | Event log for Airflow system events | Audit trail |

## Querying Safely: Read Replica Required

**Do NOT run ad-hoc analytics queries against the primary Airflow metadata DB** — the same database the scheduler uses for task state management [B2]. Heavy queries degrade scheduler performance.

Design:
1. Provision a **read replica** of the Airflow metadata PostgreSQL instance.
2. Point all reporting tools (Superset, Metabase, Grafana, custom SQL) to the read replica.
3. On Astro: the metadata DB is managed infrastructure — contact Astronomer support to enable read replica access if needed, or use the REST API as the reporting interface instead.

## Preferred: REST API for Operational Queries

For operational (not analytical) queries — the same use case as `autorep` — use the Airflow REST API [B2]:

```bash
# Equivalent of: autorep -J finance_reconciliation -s
curl -X GET "https://<deployment-url>/api/v1/dags/finance_reconciliation/dagRuns?limit=5" \
  -H "Authorization: Bearer <token>"

# Equivalent of: autorep -G DB_PASSWORD
curl -X GET "https://<deployment-url>/api/v1/variables/DB_PASSWORD" \
  -H "Authorization: Bearer <token>"
```

The REST API is scheduler-safe (reads from a separate FastAPI process, not the scheduler's DB session) [B2].

## Sources

[B1] Broadcom AutoSys Documentation — `autorep` command reference: `-J`, `-M`, `-c`, `-G` flags, `-s` (summary), `-d` (detail), `-r N` (N runs) (accessed 2026-08-18)
[B2] Apache Airflow Docs — Metadata DB schema (`dag_run`, `task_instance`, `variable`), REST API endpoints, PostgreSQL read replica recommendation for reporting (accessed 2026-08-18)
