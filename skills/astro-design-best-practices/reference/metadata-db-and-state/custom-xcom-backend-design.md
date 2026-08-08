# Custom XCom Backend Design

AutoSys passed limited state between jobs via global variables. Airflow uses XComs (Cross-Communication) to pass data between tasks. By default, XComs are serialized and stored in the metadata database. 

For production environments passing payloads larger than simple strings or small dictionaries (e.g., Pandas DataFrames, large JSON), a **Custom XCom Backend** leveraging cloud object storage (S3, GCS, Azure Blob) is mandatory [B1].

## Why the default backend fails at scale

Storing large blobs in the PostgreSQL metadata DB causes:
- Database bloat and rapid storage exhaustion.
- Severe performance degradation (slow scheduling, UI timeouts) due to massive I/O load.
- Hard size limits (PostgreSQL restricts single rows to ~1GB, but performance degrades well before that) [B1].

## The `Common IO` provider implementation

The officially supported and recommended path on Astro is using the `airflow.providers.common.io.xcom.backend.XComObjectStorageBackend` [B2].

### Configuration

Set the following in the Airflow environment:

| Variable | Value | Purpose |
|---|---|---|
| `AIRFLOW__CORE__XCOM_BACKEND` | `airflow.providers.common.io.xcom.backend.XComObjectStorageBackend` | Enables the custom backend |
| `AIRFLOW__COMMON_IO__XCOM_OBJECTSTORAGE_PATH` | `s3://your-bucket/xcoms/` | The URI for storage |
| `AIRFLOW__COMMON_IO__XCOM_OBJECTSTORAGE_THRESHOLD` | `1048576` (1 MB) | **Best Practice**: Creates a hybrid setup. Small XComs (<1MB) stay in the DB for speed; large ones offload to S3 [B2]. |
| `AIRFLOW__COMMON_IO__XCOM_OBJECTSTORAGE_COMPRESSION` | `gzip` or `snappy` | Optional: reduces storage and transfer costs |

## Design best practices

1. **References over Raw Data**: Even with an S3 backend, avoid serializing massive datasets. It is better to write the data to S3 directly within the task code and pass only the S3 URI path via XCom to the downstream task [B1].
2. **Bucket Lifecycle Policy**: XCom objects in S3/GCS will accumulate. Configure a cloud bucket lifecycle policy to automatically delete objects older than 30 days to control costs [B1].
3. **Idempotency**: XComs are cleared from the metadata DB on task retry, but orphaned files may remain in object storage if a task fails midway. Lifecycle policies mitigate this.
4. **Security / IAM**: The Airflow worker executing the task must have Read/Write IAM permissions to the target bucket via Workload Identity (see topic 036) [B1].

## Sources

[B1, B2] Astronomer Best Practices & Apache Airflow Docs — Custom XCom Backends and Object Storage integration (accessed 2026-08-08)
