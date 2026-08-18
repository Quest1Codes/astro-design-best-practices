# Generator Output — 028

## Draft reference file

# Backup and Point-in-Time Recovery

AutoSys's Event Server RDBMS (Oracle, SQL Server, or Sybase) was backed up by a DBA team using standard RDBMS procedures. Airflow's metadata DB plays the same structural role: it is the scheduler's sole state store [B1]. Losing it without a valid backup means losing all DAG run history, task instance state, XComs, connections, and variables — current executions will be interrupted [B1].

**Important**: the metadata DB does not contain DAG code. DAG files live in the DAG folder/bundle; back those up separately (via git / version control) [B2].

## Deployment model decision table (Axis A — H rating)

| Deployment model | Backup ownership | User action |
|---|---|---|
| **Astro Hosted** | Astronomer-managed | Use Astronomer's built-in DR features; do not manually modify the DB [A1-1][A1-3] |
| **Astro Hosted — dedicated cluster** | Astronomer-managed with DR failover | Enable multi-region DR in Astro UI; contact Astronomer for specific RPO/RTO SLAs [A1-2] |
| **Self-managed / BYOD — cloud-managed PostgreSQL** | Cloud provider | Enable automated backups and PITR in your cloud DB console (RDS, Cloud SQL, Azure DB) [A1-5] |
| **Self-managed / BYOD — self-hosted PostgreSQL** | User-owned | Configure WAL archiving + base backups + PITR manually [A1-4] |

## Self-managed PITR setup (Axis A — BYOD path)

For self-hosted PostgreSQL, PITR requires all three components [A1-4]:

```
1. archive_mode = on          (in postgresql.conf — enables WAL archiving)
2. archive_command = '...'    (command to copy each WAL segment to durable storage)
3. Regular base backups        (via pgBackRest or pg_basebackup)
```

> This procedure (A1-4) requires hands-on validation in a non-production Astro environment before relying on it for production RPO. Flagged `NEEDS_EXEC_CHECK`.

## Cloud-managed PostgreSQL PITR checklist (Axis A — cloud BYOD path)

For AWS RDS, GCP Cloud SQL, or Azure Database for PostgreSQL [A1-5]:

- [ ] Automated backups enabled with sufficient retention window (e.g. 7 days minimum; 35 days max on RDS)
- [ ] Point-in-time recovery feature enabled
- [ ] Backup window set to off-peak hours
- [ ] Backup stored in a different availability zone / region from primary

## RPO / RTO planning (Axis B — Estate scale — H rating)

| Estate scale / criticality | RPO target | Recommended backup approach |
|---|---|---|
| Small / non-critical | 24 hours | Daily automated snapshots (cloud provider) [B-S2] |
| Mid / production | 4–8 hours | Cloud-managed PITR with adequate retention window [A1-5] |
| Large / tight SLA | < 1 hour | Continuous WAL archiving to durable storage [B-S1]; cloud-managed PITR or self-managed WAL archiving [A1-4] |

## Compliance callout (Axis E — M rating)

For SOX/HIPAA/FedRAMP verticals, backup retention periods (SOX commonly requires 7 years for financial audit trails) may exceed what Airflow's metadata DB retains operationally [E1]. Before running `airflow db clean` or `airflow db drop-archived`, export archived records to a compliance-designated, immutable storage location using `airflow db export-archived` [E1].

## Key risks

| Risk | Mitigation |
|---|---|
| Restoring DB to a point ahead of the scheduler's last state | Restart the scheduler after restoring; state mismatch between DB and running tasks can cause zombie tasks [B3] |
| No DAG code backup | DAG code versioning is mandatory (git); DB backup alone is insufficient [B2] |
| Assuming Astro Hosted DR covers all RPO needs | Verify Astronomer's actual SLA for your cluster type; for specific RPO/RTO requirements, contact Astronomer support [A1-2] |

## Sources
- [B1, B2] Astronomer Learn — airflow-database: https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08)
- [A1-1, A1-2, A1-3] Astronomer Astro Hosted DR docs (accessed 2026-08-08)
- [A1-4, B-S1] PostgreSQL continuous archiving docs: https://www.postgresql.org/docs/current/continuous-archiving.html (accessed 2026-08-08)
- [A1-5, B-S2] Cloud provider managed PostgreSQL docs — AWS RDS / GCP Cloud SQL / Azure Database for PostgreSQL (accessed 2026-08-08)
- [E1] Apache Airflow CLI docs — `airflow db export-archived` (accessed 2026-08-08)

Citation marker → row mapping: all markers map to identically-named rows in researcher-output.md.

## Gaps noticed
- Astronomer Hosted DR SLA specifics (RPO/RTO numbers) are not publicly documented; flagged — contact Astronomer support.
- BYOD WAL archiving procedure (A1-4) flagged `NEEDS_EXEC_CHECK`.

## Size check
Draft reference file: ~4,000 characters. Within target.
