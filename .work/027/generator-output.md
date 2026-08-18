# Generator Output — 027

## Draft reference file

# Metadata Retention and Cleanup Policy

AutoSys stored job history in the Event Server RDBMS — typically managed by a DBA team with standard RDBMS retention policies set outside AutoSys. Airflow's metadata DB has no equivalent built-in purge mechanism: it accumulates historical `dag_run`, `task_instance`, `log`, `xcom`, and related records indefinitely unless an explicit retention policy is designed [B1].

Without cleanup, tables exceeding ~50 GiB produce observable symptoms: slow scheduler heartbeat queries, sluggish DAG parsing, UI pagination timeouts [B8]. The cleanup must be designed before the table reaches that threshold, not after.

## Cleanup command reference

The supported cleanup tool is `airflow db clean` [B2]:

```bash
# Dry run first — always
airflow db clean \
  --clean-before-timestamp "2025-01-01 00:00:00+00:00" \
  --dry-run

# Archive mode (default): moves rows to archive tables, reclaim later
airflow db clean \
  --clean-before-timestamp "2025-01-01 00:00:00+00:00"

# Direct delete (no archive): immediately removes rows; requires VACUUM to reclaim space
airflow db clean \
  --clean-before-timestamp "2025-01-01 00:00:00+00:00" \
  --skip-archive
```

Key CLI options [B3]:

| Option | Effect |
|---|---|
| `--clean-before-timestamp` | Required. Rows created before this timestamp are eligible for removal |
| `--tables` | Comma-separated list of tables to clean; defaults to all supported high-churn tables |
| `--dry-run` | Preview without deleting; always run first |
| `--skip-archive` | Delete immediately instead of moving to archive tables |

> The command always preserves the most recent non-manually-triggered `DagRun` for each DAG to maintain scheduling continuity [B6].

## Archive → VACUUM lifecycle

```
airflow db clean           → rows moved to archive tables [B4]
airflow db export-archived → optional: export archive for audit/compliance before drop [E1]
airflow db drop-archived   → delete archive tables to reclaim DB space [B4]
VACUUM (PostgreSQL)        → return space to the OS [B5]
```

**Without `VACUUM`**, PostgreSQL does not return deleted space to the OS [B5]. Schedule `VACUUM` (or `AUTOVACUUM` tuning) alongside the cleanup run.

## High-churn tables to monitor

`dag_run` · `task_instance` · `job` · `log` · `rendered_task_instance_fields` · `xcom` [B7]

Monitor these tables' row counts and disk usage on a recurring schedule (weekly or monthly depending on estate scale).

## Deployment model dispatch (Axis A — H rating)

| Deployment model | Recommended cleanup mechanism |
|---|---|
| **Astronomer Software (self-managed)** | Configure automated CronJob via `astronomer.houston.cleanupAirflowDb` in `values.yaml` [A1-1] *(verify key name against current version — NEEDS_EXEC_CHECK)* |
| **Astro Hosted** | Build a maintenance DAG using an Airflow plugin that exposes `airflow db clean`; tasks in Airflow 3 cannot access the DB directly [A1-2][B9] |

## Estate scale table (Axis B — H rating)

| Estate scale | Cleanup cadence | Cutoff window | Mode |
|---|---|---|---|
| Small | Monthly | 90 days [B-S1] | Archive mode + quarterly `VACUUM` |
| Mid | Bi-weekly | 90 days | Archive + export before drop |
| Large / high throughput | Weekly | 90 days (adjust if audit requirements allow shorter) [B-S2] | `--skip-archive` + `VACUUM` in low-traffic window [B-S3] |

## Compliance callout (Axis E — M rating)

Before cleaning `dag_run` and `task_instance` tables in regulated environments (SOX, HIPAA), confirm whether any audit trail retention requirement applies [E1]. If so:
1. Run `airflow db export-archived` to export the archive before dropping it.
2. Store the export in a compliance-designated, immutable storage location.
3. Then run `airflow db drop-archived`.

## Sources
- [B1, B7, B8, B9, A1-2] Astronomer Learn — airflow-database: https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08)
- [B2, B3, B4, B6, E1] Apache Airflow CLI docs — `airflow db clean` (accessed 2026-08-08)
- [B5] PostgreSQL VACUUM docs / Airflow Summit DB maintenance talk (accessed 2026-08-08)
- [B-S1, B-S2, B-S3, A1-1] Astronomer DB maintenance / Software Helm chart docs (accessed 2026-08-08)

Citation marker → row mapping: all markers map to identically-named rows in researcher-output.md.

## Gaps noticed
- `astronomer.houston.cleanupAirflowDb` key name in `values.yaml` (A1-1): flagged `NEEDS_EXEC_CHECK`.

## Size check
Draft reference file: ~4,100 characters. Within target.
