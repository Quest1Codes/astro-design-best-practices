# Researcher Output — 027

## Topic
Metadata retention and cleanup policy for the Airflow metadata database — design when migrating from AutoSys to Astronomer/Airflow.

## Relevant axes covered
- Deployment model (H): Astro Hosted vs. self-managed affect how cleanup is triggered
- Estate scale (H): larger estates accumulate metadata faster and need more aggressive/frequent cleanup
- Vertical/compliance (M): regulated verticals may have audit retention requirements that conflict with aggressive cleanup

## Fact-sheet

### Baseline (axis-free) facts
| # | Fact | Tier | Source (URL + date) | Exec-check needed? |
|---|------|------|----------------------|---------------------|
| B1 | Airflow does **not** automatically purge historical data from the metadata DB; without an explicit retention policy, tables grow indefinitely | 1 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B2 | The official cleanup command is `airflow db clean --clean-before-timestamp "<YYYY-MM-DD HH:MM:SS+00:00>"`; this is the safe, supported way to remove old records | 2 | https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html (accessed 2026-08-08) | No |
| B3 | `airflow db clean` supports: `--clean-before-timestamp` (required cutoff), `--tables` (comma-separated list; defaults to all supported tables), `--dry-run` (preview without deleting), `--skip-archive` (delete immediately vs. move to archive tables first) | 2 | Apache Airflow CLI docs (accessed 2026-08-08) | No |
| B4 | By default (without `--skip-archive`), `airflow db clean` moves records to archive tables rather than deleting them immediately; archive tables must then be cleared with `airflow db drop-archived` to reclaim actual disk space | 2 | Apache Airflow CLI docs (accessed 2026-08-08) | No |
| B5 | After `DROP` or `DELETE` operations on PostgreSQL, disk space is not immediately reclaimed; a PostgreSQL `VACUUM` (or `VACUUM FULL`) must be run to return space to the OS | 2 | Standard PostgreSQL documentation / Airflow Summit talk on DB maintenance (accessed 2026-08-08) | No |
| B6 | The command preserves the most recent non-manually-triggered `DagRun` for each DAG to maintain scheduling continuity — it does not completely wipe all history | 2 | Apache Airflow CLI docs (accessed 2026-08-08) | No |
| B7 | High-churn tables that benefit most from regular cleanup: `dag_run`, `task_instance`, `job`, `log`, `rendered_task_instance_fields`, `xcom` | 1 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B8 | When tables exceed ~50 GiB, symptoms include: slow scheduling (scheduler heartbeat queries time out), sluggish DAG parsing, UI pagination timeouts | 1 | Astronomer DB maintenance docs (accessed 2026-08-08) | No |
| B9 | In Airflow 3, tasks cannot directly access the metadata DB via SQLAlchemy; cleanup logic that previously used `PythonOperator` with direct DB queries must be replaced with CLI-driven approaches or Airflow plugins exposing `db clean` | 2 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B10 | AutoSys stored job history in its Event Server RDBMS; that history was typically retained indefinitely or managed by DBA policy outside AutoSys itself. Migrating teams often have no equivalent cleanup concept for Airflow's metadata and need to build one fresh | PRACTITIONER JUDGMENT — not independently verifiable from public sources as of 2026-08-08 | — | No |

### Axis: Deployment model (A)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| A1-1 | On Astronomer Software (self-managed), an automated cleanup CronJob can be configured via `astronomer.houston.cleanupAirflowDb` in the platform `values.yaml` | 1 | Astronomer Software Helm chart docs (accessed 2026-08-08) | Yes — NEEDS_EXEC_CHECK: confirm the exact `values.yaml` key against current Astronomer Software version |
| A1-2 | On Astro Hosted, the recommended approach is to trigger `airflow db clean` via a maintenance DAG using an Airflow plugin, since tasks in Airflow 3 cannot access the DB directly | 1 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |

### Axis: Estate scale (B)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| B-S1 | Conservative recommended cutoff for retention: 90 days (`--clean-before-timestamp` 90 days prior to current date); this prevents removal of data needed for active pipelines or near-term backfills | 1 | Astronomer DB maintenance docs (accessed 2026-08-08) | No |
| B-S2 | For large estates with high DAG/task throughput, more frequent cleanup cadence (e.g. weekly vs. monthly) prevents tables from reaching the ~50 GiB symptom threshold | 1 | Astronomer DB maintenance docs (accessed 2026-08-08) | No |
| B-S3 | At very large scale, prefer `--skip-archive` and run `VACUUM` during low-traffic windows to avoid secondary bloat from archive tables | 1 | Astronomer DB maintenance docs (accessed 2026-08-08) | No |

### Axis: Vertical/compliance (E)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| E1 | Before cleaning `dag_run` and `task_instance` tables, confirm whether any compliance requirement mandates audit trail retention (SOX, HIPAA, etc.); if so, export archived data with `airflow db export-archived` before running `airflow db drop-archived` | 2 | Apache Airflow CLI docs (accessed 2026-08-08) | No |

## Known gaps
- **Exact `values.yaml` key** for Astronomer Software cleanup CronJob (A1-1): flagged `NEEDS_EXEC_CHECK` — key name may vary across Astronomer Software versions.
- **Tier-3 material**: Astronomer SA guidance on retention policies for regulated verticals with AutoSys migration history not publicly available.

## Sources
- [B1, B7, B8, B9, A1-2] Astronomer Learn — Understanding the Airflow metadata database: https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08)
- [B2, B3, B4, B6, B9, E1] Apache Airflow CLI reference / `airflow db clean` docs (accessed 2026-08-08)
- [B5] PostgreSQL VACUUM documentation / Airflow Summit DB maintenance talk (accessed 2026-08-08)
- [B-S1, B-S2, B-S3, A1-1] Astronomer DB maintenance / Software Helm chart docs (accessed 2026-08-08)
