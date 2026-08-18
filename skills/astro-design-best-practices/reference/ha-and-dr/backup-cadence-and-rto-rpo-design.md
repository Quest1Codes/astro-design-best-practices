# Backup Cadence and RTO/RPO Design

RTO/RPO targets and backup responsibilities differ significantly between **Astro Cloud** (managed SaaS) and **Astro Private Cloud** (self-hosted). This is a critical distinction: teams migrating from AutoSys must understand where platform-managed vs. customer-managed responsibility begins.

## Astro Cloud (Managed SaaS)

On Astro's managed platform with the cross-region DR feature enabled:

| Metric | Target |
|---|---|
| **RTO** | < 1 hour [B1][B2] |
| **RPO** | < 15 minutes (with Task Logs Replication SLA enabled) [B1][B2] |
| **Backup Method** | Continuous cross-region synchronization (warm standby). No manual snapshot cadence to manage [B1]. |

**What Astronomer manages**: Metadata DB replication, task log replication, container image replication to the secondary region [B1].

**What you still own**: Backup of any data your DAGs *write* to external systems (S3, Snowflake, etc.) — these are not in scope for Astro DR.

## Astro Private Cloud (Self-Hosted)

On self-hosted Astronomer Software, the customer is fully responsible for backup and DR design.

### Metadata Database Backup

- **Technology**: PostgreSQL (each Airflow deployment gets its own isolated DB/schema; the Astronomer platform uses a "Houston" database for platform state) [B3].
- **Recommended Approach**: Use managed database services (AWS RDS, GCP Cloud SQL) and enable **Point-in-Time Recovery (PITR)**, which provides near-zero RPO without requiring a manual snapshot schedule [B3].
- **Alternative**: `pg_dump` snapshots on a cron schedule. The frequency directly determines your RPO (e.g., hourly snapshots = up to 1 hour of potential data loss).

### Kubernetes Cluster State Backup

- **Tool**: **Velero** is the Astronomer-recommended tool for backing up Kubernetes resource configurations [B3].
- **Scope**: Backs up K8s object definitions (Deployments, ConfigMaps, Secrets), not the PostgreSQL data itself. Both must be backed up independently.

### Designing Your RTO Target

| RTO Target | Required Design |
|---|---|
| **< 1 hour** | Pre-provisioned secondary cluster + PITR-capable managed DB. |
| **< 4 hours** | Restore from snapshot + cluster reprovisioning via IaC (Terraform). |
| **< 24 hours** | Restore from daily snapshot + manual reprovisioning (acceptable for dev/staging only). |

## Sources

[B1] Astronomer Docs — Astro Cloud Disaster Recovery RTO/RPO targets (accessed 2026-08-10)
[B2] Astronomer Docs — Cross-region DR failover and Task Log Replication SLA (accessed 2026-08-10)
[B3] Astronomer Docs — Astro Private Cloud backup strategy (Velero, PostgreSQL, PITR) (accessed 2026-08-10)
