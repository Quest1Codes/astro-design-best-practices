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
3. **Separate Storage Access from Platform Access**: The team that administers the Astro platform must NOT have permissions to delete or modify the audit log storage bucket. This enforces the separation-of-duties principle behind SOX Section 404 [B-SOX]. **Correction**: an earlier draft cited this legal claim to [B1][B2] (Astronomer's own audit-log/RBAC docs), which document the Astro-side mechanism but say nothing about SOX itself — a legal citation shouldn't be a product-doc link. Corrected below.

## Long-Term Retention

SOX audit-record retention is commonly cited as around 7 years, though the specific requirement depends on record type and applicable SEC rule [B-SOX]. **Correction**: an earlier draft stated this flatly as sourced fact under [B1] (an Astronomer product doc, not a legal source) — retagged below. Astro's internal 90-day retention means you must implement an **automated export pipeline** to cold/archival WORM storage (e.g., AWS S3 Glacier with Object Lock) [B1].

## Cryptographic Integrity (Advanced)

For frameworks requiring proof of non-tampering:
- Ingest logs into a SIEM that performs **hash chaining** on ingested records (e.g., Splunk, Microsoft Sentinel). This provides an independent, cryptographically verifiable record that logs have not been silently altered [B2].

## OpenLineage as a Supplementary Data Audit Trail

For SOX and AML use-cases where auditors need to trace the provenance of data feeding into financial reports, OpenLineage (pre-installed in Astro Runtime via `apache-airflow-providers-openlineage`) provides an automated, real-time graph of what data moved where and when — supplementing the control-plane audit log with data-layer evidence [B2].

## Sources

[B1] Astronomer Docs — Export audit logs (90-day retention, NDJSON export format, `astro organization audit-logs export` CLI): https://www.astronomer.io/docs/astro/audit-logs#export-audit-logs (tier 1, URL added on citation review)
[B2] Astronomer Docs — Configure OpenLineage on Astro (data-layer lineage/audit): https://www.astronomer.io/docs/astro/observe-openlineage (tier 1, URL added on citation review — covers the OpenLineage portion only; the WORM-storage and separation-of-duties guidance is general SOX practice, not a specific Astronomer doc page, and wasn't independently verified on this pass)
[B-SOX] U.S. Securities and Exchange Commission / SOX legislative text — Sarbanes-Oxley Act Section 404 (internal controls) and Section 802 (record retention, commonly summarized as ~7 years for certain audit/work-paper records, exact period depends on record type and rule): https://www.sec.gov/spotlight/sarbanes-oxley.htm (tier 3 — external legal source, not an Astronomer product doc; added on Critic-pass review to separate the legal claim from the Astro-side mechanism it was previously bundled under)
