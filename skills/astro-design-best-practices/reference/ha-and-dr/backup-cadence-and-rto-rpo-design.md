# Backup Cadence and RTO/RPO Design

RTO/RPO targets and backup responsibilities differ significantly between **Astro Cloud** (managed SaaS) and **Astro Private Cloud** (self-hosted). This is a critical distinction: teams migrating from AutoSys must understand where platform-managed vs. customer-managed responsibility begins.

## Astro Cloud (Managed SaaS)

On Astro's managed platform with the cross-region DR feature enabled. **Requires the Enterprise Business Critical tier and a dedicated cluster** — this is a hard gate, not available on shared clusters or lower tiers, and an earlier draft of this file didn't state that constraint [B4]. The feature is also currently documented as **Preview** as of its most recent release notes; confirm current GA status before treating these targets as a committed SLA [B5]:

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

[B1] Astronomer Docs — Disaster recovery, RTO/RPO targets: https://www.astronomer.io/docs/astro/disaster-recovery#rto-and-rpo (tier 1, URL added on citation review)
[B2] Astronomer Docs — Prepare for disaster recovery, Task Logs Replication SLA: https://www.astronomer.io/docs/astro/disaster-recovery-prepare#task-logs-replication-sla (tier 1, URL added on citation review)
[B3] Astronomer Docs — Astronomer Software disaster recovery (Velero-based backup/restore recommendation): https://www.astronomer.io/docs/astro-private-cloud/v-0-37/disaster-recovery (tier 1, URL added on citation review)
[B4] Astronomer Docs — Disaster recovery (Enterprise Business Critical tier requirement, dedicated clusters only): https://www.astronomer.io/docs/astro/disaster-recovery (tier 1, added on doc-verification review)
[B5] Astronomer Docs — Release notes, March 11 2026 (cross-region DR documented as Preview): https://www.astronomer.io/docs/astro/release-notes#march-11-2026 (tier 1, added on doc-verification review)
