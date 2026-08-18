# EDI and File-Transfer Integration Patterns

EDI (Electronic Data Interchange) and managed file transfer (MFT) were core batch workloads in AutoSys environments — typically manifesting as JCL steps running FTP/SFTP transfers followed by downstream processing. In Airflow, Airflow handles the orchestration and monitoring; a dedicated MFT layer or cloud-native transfer service handles the actual file mechanics.

## Pattern 1: SFTP ↔ S3 (Internal/Partner File Movement)

The most common pattern: move files between an SFTP server and S3 as part of a data ingestion or outbound delivery pipeline.

| Direction | Operator | Provider Package |
|---|---|---|
| SFTP → S3 | `SFTPToS3Operator` | `apache-airflow-providers-amazon` [B1] |
| S3 → SFTP | `S3ToSFTPOperator` | `apache-airflow-providers-amazon` [B1] |

1. **Trigger**: Use `SFTPSensor` or `S3KeySensor` to wait for a file to arrive before starting processing — making the pipeline event-driven rather than purely time-based [B1][B2].
2. **Transfer**: Use the appropriate operator to move the file.
3. **Process**: Invoke a downstream transformation task (e.g., a Glue job, a Python EDI parser, or a Spark submit).

## Pattern 2: AS2 Integration (Trading-Partner EDI)

Airflow has no native AS2 operator. AS2 (a B2B protocol requiring message signing and MDN receipts) requires a dedicated gateway [B2].

**Recommended architecture**:
1. An **MFT Gateway** (e.g., **AWS Transfer Family**, which supports AS2 natively) handles the AS2 handshake with the trading partner and deposits the raw EDI payload file into S3 [B2].
2. Airflow listens for the file landing in S3 (via `S3KeySensor` or an EventBridge trigger on the S3 event) and orchestrates the downstream EDI transformation and loading pipeline.

This cleanly separates protocol-handling (AS2 gateway) from business logic orchestration (Airflow).

## Key Design Rules

| Rule | Rationale |
|---|---|
| **Use S3 as the central landing zone** | Decouples the transfer mechanism from the transformation compute. Airflow tasks read from S3, not directly from SFTP [B2]. |
| **Add retries to transfer tasks** | SFTP connections are prone to transient network failures; configure `retries=3` with exponential `retry_delay` [B1]. |
| **Store SFTP keys in a Secrets Backend** | SSH private keys must never be hardcoded in DAGs or environment variables. Store in Secrets Manager via an Airflow Connection [B1]. |
| **Use `SFTPSensor` with `mode='reschedule'`** | Waiting for a slow trading partner file can take hours. Reschedule mode avoids blocking the worker slot [B1]. |

## Sources

[B1] Apache Airflow Docs & `apache-airflow-providers-amazon` — `SFTPToS3Operator`, `S3ToSFTPOperator`, `SFTPSensor`, and Sensor modes (accessed 2026-08-10)
[B2] AWS Docs — AWS Transfer Family AS2 support and S3 integration for EDI workflows (accessed 2026-08-10)
