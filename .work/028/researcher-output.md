# Researcher Output — 028

## Topic
Backup and point-in-time recovery (PITR) design for the Airflow metadata database when migrating from AutoSys to Astronomer/Airflow.

## Relevant axes covered
- Deployment model (H): Astro Hosted (managed DR) vs. self-managed/BYOD (user owns backup)
- Estate scale (H): RTO/RPO targets and backup frequency scale with estate criticality
- Vertical/compliance (M): regulated verticals may require specific RPO/RTO SLAs and audit trails

## Fact-sheet

### Baseline (axis-free) facts
| # | Fact | Tier | Source (URL + date) | Exec-check needed? |
|---|------|------|----------------------|---------------------|
| B1 | The Airflow metadata DB is the scheduler's sole state store; losing it without a valid backup means losing all DAG run history, task instance state, XComs, connections, and variables — current executions will be interrupted | 2 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B2 | Airflow's metadata DB does not store DAG code (DAGs live in the DAG folder/bundle); backup of the metadata DB does not substitute for a DAG code versioning strategy | 2 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B3 | Do not attempt to restore a metadata DB to a point in time significantly ahead of the scheduler's last known state without also restarting the scheduler — state inconsistencies can arise between DB state and currently-running task processes | PRACTITIONER JUDGMENT — not independently verifiable from public sources as of 2026-08-08 | — | No |
| B4 | AutoSys stored job state in its Event Server RDBMS (Oracle, SQL Server, or Sybase); that DB was typically backed up by the DBA team under standard RDBMS procedures. Airflow's metadata DB follows the same pattern: standard PostgreSQL backup and PITR applies | PRACTITIONER JUDGMENT — synthesized from Broadcom AutoSys architecture docs | — | No |

### Axis: Deployment model (A)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| A1-1 | On Astro Hosted (managed cloud), Astronomer manages the metadata DB infrastructure including backups and DR; users do not have direct access to the underlying PostgreSQL WAL files or `pg_basebackup` | 1 | Astronomer Astro Hosted DR docs (accessed 2026-08-08) | No |
| A1-2 | On Astro Hosted, Astronomer provides built-in Disaster Recovery features for dedicated clusters (failover to a secondary region); for specific RPO/RTO requirements beyond standard DR, contact Astronomer support | 1 | Astronomer Astro Hosted DR docs (accessed 2026-08-08) | No |
| A1-3 | On Astro Hosted, do not manually modify the metadata DB; this risks state inconsistency and loss of Astronomer support | 1 | Astronomer Astro Hosted DR docs (accessed 2026-08-08) | No |
| A1-4 | On self-managed / BYOD external PostgreSQL, user owns backup and PITR: requires (1) WAL archiving enabled (`archive_mode = on`), (2) base backups via `pgBackRest` or `pg_basebackup`, (3) continuous WAL archiving to durable storage | 2 | Standard PostgreSQL PITR documentation (accessed 2026-08-08) | Yes — NEEDS_EXEC_CHECK: validate WAL archive + restore on a test Astro environment before relying on it for production RPO |
| A1-5 | Cloud-managed PostgreSQL (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL) provide automated backup and PITR as platform features; instance-level configuration (backup window, retention period, PITR enabled) must be explicitly set | 1 | Cloud provider PostgreSQL managed service docs (general, accessed 2026-08-08) | No |

### Axis: Estate scale (B)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| B-S1 | For critical production estates (large AutoSys migrations, tight SLAs), RPO should align with backup frequency; a 24-hour RPO means at most one day of task history loss; sub-hour RPO requires continuous WAL archiving | 2 | Standard PostgreSQL PITR docs (accessed 2026-08-08) | No |
| B-S2 | For smaller or non-critical estates, daily snapshots (provided by cloud-managed PostgreSQL's automated backups) are often sufficient; enable PITR only if the business requires point-in-time recovery granularity | 1 | Cloud provider managed DB docs (general, accessed 2026-08-08) | No |

### Axis: Vertical/compliance (E)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| E1 | For SOX/HIPAA/FedRAMP verticals, backup retention periods (often 7 years for SOX) and audit trail requirements may exceed what Airflow's metadata DB alone retains; consider `airflow db export-archived` before cleanup to preserve an external audit trail | 2 | Apache Airflow CLI docs + general compliance guidance (accessed 2026-08-08) | No |

## Known gaps
- **Astronomer Hosted DR SLA specifics** (RPO/RTO numbers): not publicly documented; flagged — contact Astronomer support for exact SLA terms.
- **PITR validation on Astro BYOD** (A1-4): flagged `NEEDS_EXEC_CHECK` — needs hands-on confirmation that WAL archiving + restore procedure works against a real Astro Private Cloud deployment.
- **Tier-3 material**: Astronomer SA guidance on backup design for regulated AutoSys migration customers not publicly available.

## Sources
- [B1, B2] Astronomer Learn — Understanding the Airflow metadata database: https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08)
- [A1-1, A1-2, A1-3] Astronomer Astro Hosted Disaster Recovery docs (accessed 2026-08-08)
- [A1-4, B-S1] PostgreSQL PITR documentation: https://www.postgresql.org/docs/current/continuous-archiving.html (accessed 2026-08-08)
- [A1-5, B-S2] Cloud provider managed PostgreSQL docs (AWS RDS / GCP Cloud SQL / Azure Database for PostgreSQL — general reference, accessed 2026-08-08)
- [E1] Apache Airflow CLI docs (accessed 2026-08-08)
