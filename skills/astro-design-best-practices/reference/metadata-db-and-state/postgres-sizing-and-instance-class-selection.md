# Postgres Sizing and Instance-Class Selection

AutoSys stored job state in its Event Server RDBMS (Oracle, SQL Server, or Sybase), managed by a DBA team under standard enterprise DB procedures. {syn: B4-autosys-comparison — this is a practitioner-level mapping from AutoSys architecture documentation and industry knowledge; no single public tier-1 source explicitly documents the Event Server RDBMS types in detail.} Airflow's metadata database replaces that role: it is the scheduler's sole source of truth for DAG run history, task instance status, XComs, connections, and variables [B2]. Every Airflow component writes to it continuously; it is not a reporting store — it is a live operational dependency.

The key design fork is whether the DB is **Astronomer-managed** (Astro Hosted) or **user-managed** (self-managed/BYOD). These have completely different sizing responsibility models.

## Deployment model decision table (Axis A — H rating)

| Deployment model | DB ownership | Instance-class responsibility | Key constraint |
|---|---|---|---|
| **Astro Hosted** (cloud) | Astronomer-managed | None — Astronomer provisions and scales automatically [A1-1][A1-2] | Size Airflow components (scheduler, workers) in the Astro UI; DB scales implicitly |
| **Astro Private Cloud / Software — internal DB** | Astronomer-managed per deployment | None | Same as Hosted |
| **Astro Private Cloud / Software — BYOD external DB** | User-owned | User selects instance class; `skipAirflowDatabaseProvisioning: true` [A1-3] | Must also supply own connection pooling — Astronomer's internal PgBouncer is bypassed [A1-5] |

## Rightsizing on Astro Hosted (Axis A — managed path)

On Astro Hosted, DB sizing is not a direct user control. Use Deployment Metrics in the Astro UI to rightsize the Airflow *component* resources (scheduler, workers). Astronomer recommends a 50–75% CPU and memory utilization target range [B5]:

| Metric | Action |
|---|---|
| Consistently < 50% CPU or memory | Decrease component resources (over-provisioned) |
| Between 50–75% | No change needed |
| Consistently > 75% | Increase component resources |

## Instance-class guidance for BYOD external PostgreSQL (Axis A — user-managed path)

| Estate scale (Axis B) | Starting point | Rationale |
|---|---|---|
| Small (< 500 boxes migrated) | General-purpose instance (e.g. AWS `db.t3.medium`, 2 vCPU / 4 GiB) | Default throughput sufficient for low DAG/task volume |
| Mid (500–5,000 jobs) | General-purpose larger (e.g. `db.t3.large` / `db.m6g.large`, 2–4 vCPU / 8–16 GiB) | Monitor I/O and connection saturation; add PgBouncer before upsizing [B-S2] |
| Large (> 5,000 jobs, high throughput) | Memory-optimized preferred (e.g. `db.r6g.large` or larger) {syn: B-S3-practitioner-judgment} | DB buffer cache working set benefits more from memory than CPU at high task throughput |

> **Note on large-estate sizing**: the memory-optimized preference is `PRACTITIONER JUDGMENT — not independently verifiable from public sources`. Validate with an Astronomer SA or by load-testing with realistic DAG/task volume before committing to a class.

## Compliance callout (Axis E — M rating)

Regulated verticals (SOX, HIPAA, FedRAMP) may require **BYOD external PostgreSQL** for data residency or sovereignty requirements. When using BYOD, all DB security controls transfer to the user:
- Encryption-at-rest (configure at the cloud provider or OS level)
- RBAC / network isolation (VPC, security groups, IAM policies)
- Audit logging (enable `pgaudit` or cloud-native DB audit logging)
- Backup and PITR (see `reference/metadata-db-and-state/backup-and-point-in-time-recovery.md`)

## Tables to monitor

Airflow does not auto-purge metadata. The following tables grow indefinitely without a retention policy [B6][B-S4]:

`dag_run` · `task_instance` · `job` · `log` · `rendered_task_instance_fields` · `xcom`

See `reference/metadata-db-and-state/metadata-retention-and-cleanup-policy.md` for the cleanup design.

## What this does not cover

- Connection pooling sizing → `reference/metadata-db-and-state/connection-pooling-with-pgbouncer.md`
- Backup and PITR → `reference/metadata-db-and-state/backup-and-point-in-time-recovery.md`
- DB migration strategy across Airflow upgrades → topic 030

## Sources

[B1] Apache Airflow docs — Set up a Database Backend: https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html (accessed 2026-08-08)
[B2] Astronomer Learn — Understanding the Airflow metadata database: https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08)
[B5, A1-1, A1-2] Astronomer Docs — Rightsizing Airflow resources on Astro: https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (accessed 2026-08-08)
[A1-3, A1-5, B-S2] Astronomer PgBouncer/configuration docs (accessed 2026-08-08)
[B4] Astronomer PgBouncer configuration docs — SQLAlchemy pool defaults (accessed 2026-08-08)
[B6, B-S4] Astronomer Learn — airflow-database (high-churn tables) (accessed 2026-08-08)
