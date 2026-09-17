# DB Migration Strategy Across Airflow Upgrades

Upgrading Airflow—especially moving between major versions like Airflow 2 to Airflow 3—involves significant database schema migrations. A disciplined strategy is required to prevent data corruption and extended downtime.

## Pre-migration checklist

Before initiating any Airflow upgrade or database migration [B1]:
1. **Backup**: Always snapshot the metadata DB. If a migration leaves the DB in an inconsistent state, restoring from backup is the only reliable recovery path.
2. **Clean up old metadata**: Run `airflow db clean` to archive and delete obsolete history (e.g., old XComs and logs). A smaller database migrates significantly faster and reduces the risk of timeouts during schema alterations.
3. **Resolve DAG errors**: Run `airflow dags reserialize` to ensure there are no `DuplicateIdException` or parsing errors that might complicate the upgrade.

## Migration execution strategy

| Migration Type | Approach |
|---|---|
| **Minor Version Upgrades** | Typically handled automatically on Astro via `astro deploy` with an updated runtime image. Ensure no active deployments are interrupted during the brief migration window [B2]. |
| **Major Version (Airflow 2 → 3)** | Avoid in-place upgrades. Because Airflow 3 is a rearchitecture (e.g., workers no longer connect to the DB directly), a "fresh database" approach is recommended to ensure a clean transition [B1][B3]. |

## Handling downtime and component states

When performing manual migrations (self-managed) or executing major architectural shifts:
- **Stop all components**: The scheduler, webserver, and triggerer must be shut down during the DB migration to prevent concurrent writes that could corrupt the schema during transition [B4].
- **API Server Introduction (Airflow 3)**: Be aware that Airflow 3 introduces a new API server for worker communication. The migration process will disrupt tasks currently in-flight; schedule the upgrade during a strict maintenance window [B1][B3].

## Deployment model (Axis A — H rating)

| Deployment model | Migration execution |
|---|---|
| **Astro Hosted** | Automatic during image deployment. If a migration pod enters `CrashLoopBackOff`, check logs immediately; it may indicate a stuck migration requiring manual intervention [B2]. |
| **Self-managed** | Fully manual. Stop all services, backup DB, run `airflow db migrate` (or `upgradedb`), and restart services [B4]. |

## Sources

[B1, B3] Astronomer Docs — Upgrade to Airflow 3 on Astro: https://www.astronomer.io/docs/astro/airflow3/upgrade-af3 (tier 1, URL added on citation review)
[B2] Astronomer Docs — `astro deployment airflow upgrade` CLI command: https://www.astronomer.io/docs/cli/v1.45/astro-deployment-airflow-upgrade (tier 1, URL added on citation review)
[B4] Apache Airflow Docs — Upgrading the database (canonical OSS upgrade-check reference; not independently re-verified on this pass): https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading.html (tier 2)
