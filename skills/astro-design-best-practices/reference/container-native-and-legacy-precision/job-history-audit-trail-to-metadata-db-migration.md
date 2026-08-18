# Job-History/Audit-Trail Source Inventory → Astro Metadata-DB Audit/History Migration Design

AutoSys job history and audit trails live in the Event Server database (Oracle, SQL Server, Sybase, or PostgreSQL). The primary tables are job run history records (status, start/end time, exit code, run machine) and audit log entries (who did what via `jil`, `sendevent`, WCC). This data is managed by the **`DBMaint` utility**, which prunes old records on a configurable retention schedule [B1].

Airflow stores its own run history in the metadata DB (`dag_run`, `task_instance` tables). **AutoSys job history cannot be imported into Airflow metadata DB** — the schemas are incompatible and the data semantics are different. The design is: archive AutoSys history to a separate read-only store, and let Airflow metadata DB accumulate its own history from day 1 of migration.

## What to Inventory Before Cutover

| AutoSys Source | Content | Migration Decision |
|---|---|---|
| **Job run history tables** | Execution records (start/end, status, exit code) | Export to data warehouse (BigQuery, Snowflake, S3+Athena) for compliance queries |
| **Event audit log** | Who triggered/changed what via `jil`/`sendevent`/WCC | Export to read-only archive; do not import into Airflow |
| **Global variable history** | Variable value changes over time | Export if needed for audit; current values recreated in Airflow Variables/Secrets |
| **Alarm/alert history** | Historical alerts and acknowledgements | Export for incident retrospectives; no Airflow equivalent store |
| **Agent file system logs** | Job stdout/stderr on agent machines | Collect and archive to S3 before decommissioning agents |

## Retention and Archiving Strategy

### AutoSys Side (Before Cutover)

1. Run a final `DBMaint` pass to prune data older than your retention requirement (e.g., keep 2 years of history).
2. Export the remaining history tables to a portable format (CSV, Parquet) using your source DB's export tool (`expdp` for Oracle, `bcp` for SQL Server).
3. Load to S3 / BigQuery / Snowflake. Partition by `execution_date` for efficient querying.
4. Keep the AutoSys Event Server in **read-only mode** for the "Observation Period" (2–4 cycles) after cutover — do not decommission until the observation period is complete.

### Airflow Side (After Cutover)

Airflow metadata grows continuously. Implement a maintenance DAG to run `airflow db clean` on a regular cadence [B2]:

```python
from airflow.operators.bash import BashOperator

db_cleanup = BashOperator(
    task_id="clean_airflow_metadata",
    bash_command=(
        "airflow db clean "
        "--clean-before-timestamp {{ macros.ds_add(ds, -90) }} "  # Keep 90 days
        "--tables dag_run,task_instance,log,xcom "
        "--yes"
    ),
)
```

Set `--clean-before-timestamp` based on your compliance retention requirement (minimum 90 days recommended; adjust for SOX/audit requirements) [B2].

## Compliance Continuity

For SOX, HIPAA, or other regulated environments:
- The **AutoSys archive** serves as the pre-cutover audit trail.
- The **Airflow metadata DB** (plus CloudWatch/Datadog logs) serves as the post-cutover audit trail.
- Document the cutover date clearly in your compliance evidence — auditors need to know where to look for pre-cutover vs. post-cutover execution records.

## Sources

[B1] Broadcom AutoSys Documentation — Job history tables in the Event Server DB, `DBMaint` utility for history pruning, agent log files at `/opt/CA/WA_AGENT/log/`, audit event records (accessed 2026-08-18)
[B2] Apache Airflow Docs — `airflow db clean` command, `--clean-before-timestamp` parameter, `dag_run`/`task_instance`/`log`/`xcom` tables as primary metadata tables (accessed 2026-08-18)
