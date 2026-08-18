# Source Event-Server RDBMS Dialect Considerations → Astro Metadata-DB Migration-Source Design

AutoSys's Event Server database has historically been backed by **Oracle, Microsoft SQL Server, or Sybase** [B1]. Broadcom also introduced the **AutoSys DataMigrator utility** to migrate Event Server data to PostgreSQL [B1]. Understanding which RDBMS dialect backs your AutoSys instance is a pre-migration input — it affects the job-history export strategy and the data shape of any legacy audit archive.

The Airflow metadata database on Astro is **PostgreSQL** (managed by Astronomer) [B2]. There is no migration path that imports AutoSys Event Server history tables directly into the Airflow metadata DB — the schemas are completely different.

## RDBMS Dialect Considerations

| AutoSys Event Server RDBMS | Migration Impact |
|---|---|
| **Oracle** | Job history SQL queries must use Oracle-dialect SQL for extraction; JDBC driver required for history export tooling. |
| **SQL Server** | T-SQL dialect; use `bcp` or SSIS for history export; Windows auth vs. SQL auth matters for tooling access. |
| **Sybase** | Largely end-of-life; Sybase ASE `isql` for data extraction; validate that Broadcom still supports your version before migration. |
| **PostgreSQL** (via DataMigrator) | If AutoSys was already migrated to PostgreSQL, `pg_dump` can be used for history extraction — simplest path. |

## Migration Source Design

### What to Extract from the Event Server Before Cutover

| Source Table | Content | Destination on Astro Side |
|---|---|---|
| Job history / run records | Historical execution records | Export to data warehouse (Snowflake, BigQuery) — NOT the Airflow metadata DB |
| Global variables | Current variable state | Recreate as Airflow Variables or Secrets Backend entries |
| Machine definitions | Agent inventory | Used for migration planning only; no Airflow equivalent |
| Calendar definitions | Business calendar rules | Recreate as Airflow custom timetables or `@monthly`-style schedules |
| Alarm/notification config | Alert routing | Recreate as Airflow `on_failure_callback` configurations |

### What NOT to Import into Airflow Metadata DB

**Do not import AutoSys job history directly into Airflow's `dag_run` or `task_instance` tables.** The schemas are incompatible and the data meanings are different (AutoSys tracks individual job runs; Airflow tracks DAG/task instance runs with different state semantics). Importing legacy history would corrupt the Airflow metadata DB.

**Design decision**: Archive AutoSys job history to a read-only data store (S3 + Athena, BigQuery, Snowflake) for compliance/audit queries. Keep the Airflow metadata DB clean, containing only Airflow-native run history from day 1 of migration.

## Sources

[B1] Broadcom AutoSys Documentation — Event Server RDBMS support (Oracle, SQL Server, Sybase); AutoSys DataMigrator utility for migration to PostgreSQL (accessed 2026-08-18)
[B2] Astronomer Docs — Astro Deployment metadata DB is PostgreSQL (managed); no import path from external RDBMS schemas (accessed 2026-08-18)
