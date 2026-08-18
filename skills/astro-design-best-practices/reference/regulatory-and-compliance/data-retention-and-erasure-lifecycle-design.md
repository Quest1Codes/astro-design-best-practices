# Data Retention and Erasure Lifecycle Design

GDPR's Right to be Forgotten and similar data erasure regulations create a specific challenge for orchestration platforms: Airflow stores metadata about pipeline executions, and the pipelines themselves may have processed PII. Both dimensions must be addressed.

## Two Distinct Scopes

| Scope | What It Covers | Airflow's Role |
|---|---|---|
| **Airflow Metadata** | Task instance history, DAG run records, logs, rendered templates that may contain PII [B1]. | `airflow db clean` or Astronomer's built-in DB retention settings to purge records older than N days [B1]. |
| **Pipeline-Processed Data** | Actual PII in the downstream databases, data lakes, and warehouses your DAGs wrote to. | Airflow **orchestrates** the deletion — it does not own the data [B1][B2]. |

## Airflow Metadata Retention

- **`airflow db clean`**: Command-line tool to purge records from the metadata DB beyond a specified `--clean-before-timestamp`. Run this on a scheduled DAG or as part of your retention policy [B1].
- **Log Object Storage Lifecycle**: If logs are externalized to S3 or GCS (recommended practice), configure **object lifecycle policies** to automatically delete logs after the retention period. This prevents PII from persisting in logs indefinitely [B1].

## The "Deletion DAG" Pattern (GDPR Erasure Requests)

Design a dedicated **Erasure DAG** to process Right-to-be-Forgotten requests:
1. **Trigger**: The DAG is triggered via the Airflow API, passing a `user_id` (or equivalent PII key) as a `dag_run.conf` parameter [B2].
2. **Identify**: Query your data catalog or lineage graph (OpenLineage / Marquez) to identify all datasets where that user_id exists [B2].
3. **Delete or Anonymize**: For each dataset, trigger a targeted deletion task (e.g., `DELETE FROM table WHERE user_id = ?`) or replace PII fields with a hash/null [B2].
4. **Verify**: A final task confirms data has been purged from all downstream systems and writes a completion record to the audit log.
5. **Log the Request**: Record the erasure event in your immutable audit store (see topic 074) to demonstrate compliance.

## Anonymization vs. Deletion

In analytical environments, full deletion is often destructive to model history. Consider:
- **Cryptographic erasure**: If PII is encrypted and stored in WORM-storage, delete the encryption key. The data becomes unreadable without needing to modify the storage [B2].
- **Masking/Hashing**: Replace PII values with a consistent hash. This preserves referential integrity for analytics while satisfying erasure obligations.

> **Warning**: Be aware of immutable backups. If PII landed in a database backup or a WORM-protected archive before an erasure request was received, your legal team must have a defined policy for handling this scenario. There is no purely technical solution for pre-existing WORM data containing PII.

## Sources

[B1] Apache Airflow Docs — `airflow db clean` command and metadata retention (accessed 2026-08-10)
[B2] GDPR compliance guidance for Airflow — Erasure DAG patterns, cryptographic erasure, OpenLineage for PII discovery (accessed 2026-08-10)
