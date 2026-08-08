# Read-Replica Strategy for Reporting

AutoSys environments often involved querying the event server DB directly for custom reporting, which risked impacting the scheduler's performance. In Airflow, the metadata database (PostgreSQL) is the critical source of truth for the Scheduler, Webserver, and API.

**Astronomer's strict best practice is to never run heavy reporting, analytics, or complex ad-hoc queries directly against the primary production metadata database.**

## Why a read-replica is necessary

Heavy analytics queries (e.g., calculating historical task duration trends across thousands of DAGs) can acquire locks, consume I/O, and starve the Airflow Scheduler of the database resources it needs to queue and execute tasks. This directly impacts operational stability [B1].

## Architectural patterns for reporting

| Pattern | Implementation | Best for |
|---|---|---|
| **Airflow REST API** | Query the API for specific runs/statuses rather than the DB. | Lightweight, operational dashboards. Protects the DB behind the API layer. |
| **Read Replica** (Recommended) | Provision a read replica (e.g., AWS RDS Read Replica) and direct BI tools/Grafana there. | Medium-scale reporting; dashboards requiring SQL access to Airflow state [B1]. |
| **ETL / CDC to Data Warehouse** | Use Debezium or periodic ETL to stream Airflow metadata to Snowflake/BigQuery. | Long-term historical analysis, joining Airflow data with other enterprise datasets [B1]. |

## Deployment model (Axis A — H rating)

| Deployment model | Replica configuration |
|---|---|
| **Astro Hosted (Standard/Dedicated)** | Direct DB access is restricted. Use Astro Observe, the Airflow REST API, or contact Astronomer support if custom replication is strictly required [B1]. |
| **Astro Hosted + BYOD PostgreSQL** | You control the DB. Provision a read replica via your cloud provider (AWS RDS, GCP Cloud SQL) and route reporting traffic to the replica endpoint [B1]. |
| **Self-managed** | Fully supported; standard PostgreSQL physical or logical replication applies. |

## Important constraints

- **Avoid Direct Writes**: Never manually modify the metadata database (INSERT/UPDATE/DELETE). It will compromise Airflow's integrity [B1].
- **Airflow 3 Security**: Airflow 3 restricts direct database access from within task execution (worker pods) to improve security. If tasks need metadata, use the API, not direct SQLAlchemy queries [B2].

## Sources

[B1] Astronomer Docs & Best Practices — Metadata database reporting and replication strategies (accessed 2026-08-08)
[B2] Apache Airflow Docs — Airflow 3 architecture and database isolation (accessed 2026-08-08)
