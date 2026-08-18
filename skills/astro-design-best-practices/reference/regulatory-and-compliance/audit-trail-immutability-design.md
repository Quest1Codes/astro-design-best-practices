# Audit-Trail Immutability Design

Airflow's metadata database tracks every task run, DAG run, and user action — but this data is mutable by default. For SOX, AML, and other regulatory frameworks, "immutability" must be achieved architecturally, not assumed from the platform. This file describes how to design a defensible, tamper-proof audit trail on Astro.

## Two Distinct Audit Trails

Regulated Airflow deployments must manage **two separate audit layers**:

| Audit Layer | What It Captures | Default Retention (Astro Cloud) |
|---|---|---|
| **Astro Control Plane Audit Log** | Administrative actions (user management, deployment config, API access, login events) with actor, action, timestamp, and outcome [B1]. | 90 days [B1]. |
| **Airflow Execution Log** | Task-level execution history: who triggered a DAG, what ran, what succeeded/failed. Stored in the metadata DB and object storage. | Configurable; requires explicit policy. |

## Achieving Immutability

Neither log is tamper-proof in its default location. Immutability is achieved by **exporting to WORM storage**:

1. **Export Astro Audit Logs**: Use the Astro UI or CLI (NDJSON export) to ship control plane audit events to your centralized SIEM or immutable storage on a scheduled basis [B1].
2. **Configure WORM Storage**: Write logs to storage with Write-Once-Read-Many (WORM) policies:
   - AWS S3 Object Lock (Governance or Compliance mode)
   - Google Cloud Storage bucket lock policies
   - Azure Immutable Blob Storage
3. **Separate Storage Access from Platform Access**: The team that administers the Astro platform must NOT have permissions to delete or modify the audit log storage bucket. This enforces the separation of duties required by SOX Section 404 [B1][B2].

## Long-Term Retention

SOX typically requires 7-year audit retention. Astro's internal 90-day retention means you must implement an **automated export pipeline** to cold/archival WORM storage (e.g., AWS S3 Glacier with Object Lock) [B1].

## Cryptographic Integrity (Advanced)

For frameworks requiring proof of non-tampering:
- Ingest logs into a SIEM that performs **hash chaining** on ingested records (e.g., Splunk, Microsoft Sentinel). This provides an independent, cryptographically verifiable record that logs have not been silently altered [B2].

## OpenLineage as a Supplementary Data Audit Trail

For SOX and AML use-cases where auditors need to trace the provenance of data feeding into financial reports, OpenLineage (pre-installed in Astro Runtime via `apache-airflow-providers-openlineage`) provides an automated, real-time graph of what data moved where and when — supplementing the control-plane audit log with data-layer evidence [B2].

## Sources

[B1] Astronomer Docs — Astro audit log structure, export format (NDJSON), and 90-day retention policy (accessed 2026-08-10)
[B2] Astronomer Docs & SOX compliance guidance — WORM storage, separation of duties, OpenLineage for data-layer audit (accessed 2026-08-10)
