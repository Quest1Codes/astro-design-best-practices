# Log Architecture — Remote Storage and Retention

AutoSys logs were written to the local agent filesystem (`$AUTOSYS/out`) and required manual rotation or collection. Astro's containerized architecture means local pod storage is ephemeral. Therefore, task execution logs must be externalized for persistence, troubleshooting, and compliance.

## Astro logging approaches

Because Astro is built on Kubernetes, it leverages standard cloud-native logging patterns.

| Approach | Description | Use case |
|---|---|---|
| **Object Storage (S3, GCS, Azure Blob)** | Configure Airflow to write completed task logs directly to a cloud bucket. | Standard historical retention; cost-effective. |
| **External Logging via Sidecar** (Recommended) | Export logs using a logging sidecar (e.g., Vector or Fluentd) to an external system (Elasticsearch, Splunk, CloudWatch). | Centralized enterprise observability; real-time indexing. |
| **Real-Time Streaming** | Combine object storage with a Vector sidecar. | Provides "live" log visibility in the Airflow UI while tasks are still running. |

## Storage and retention design

Astro itself does not enforce a rigid platform-wide retention policy for task logs. Retention is managed by the destination storage backend.

### Elasticsearch (common in Astro Private Cloud)
- Use a DaemonSet (like Vector) to collect and index logs.
- **Retention**: Implement Index Lifecycle Management (ILM) to automatically move old indices to "cold" S3 storage or delete them. Do not keep months of task logs in hot Elasticsearch nodes due to cost.

### Object Storage (S3/GCS)
- Airflow UI fetches logs from S3 for viewing.
- **Retention**: Use S3 Lifecycle Policies to transition logs to Glacier after 30 days and delete after the compliance window expires.

### AWS CloudWatch
- Authenticate the Deployment with an IAM role to forward logs to CloudWatch.
- Integrates Astro logs into an existing AWS observability plane.

## Compliance and auditing (Axis E — H rating)

For SOX, HIPAA, or other regulated environments:
1. **Never rely on ephemeral pod storage**. Task logs must be forwarded to immutable, external storage immediately.
2. **Dual-export**: Consider sending logs to a fast-search backend (Elasticsearch) for operational troubleshooting, and simultaneously to a secured, customer-managed S3 bucket for long-term (e.g., 7-year) compliance retention.
3. **Log verbosity**: Avoid setting `AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG` in production. It drastically increases storage costs, slows down query performance, and risks exposing sensitive context data in plaintext logs.

> **Note**: Task execution logs (covered here) are distinct from platform **Audit Logs** (which track user access and Deployment changes, covered in topic 039).

## Sources

[B-Logging Architecture] Astronomer Docs — Export task logs (accessed 2026-08-08)
[B-Elasticsearch] Elastic Docs — Index Lifecycle Management (accessed 2026-08-08)
[B-S3] AWS Docs — S3 Lifecycle Policies (accessed 2026-08-08)
