# SIEM Export Integration Design

SIEM (Security Information and Event Management) integration for Astro involves two distinct log streams that require separate export pipelines: **Astro Control Plane Audit Logs** (administrative actions) and **Airflow Task Logs** (pipeline execution). These require different architectures.

## Log Stream 1: Astro Audit Logs (Control Plane)

Captures: user logins, deployment config changes, API access, workspace modifications.

| Method | Description |
|---|---|
| **Manual / Scheduled CLI export** | `astro organization audit-logs export --organization-name "<name>"` outputs NDJSON [B1]. Schedule this via a cron job or an Airflow DAG that polls on a defined cadence. |
| **Astro Platform API (Automated)** | Poll the Astro Platform API's audit-logs endpoint (`GET /organizations/{organizationId}/audit-logs`, under the platform API grouping) and push results to the SIEM's HTTP ingestion endpoint (e.g., Splunk HEC, Sentinel Data Collector API) [B1][B3]. **Note**: an earlier draft of this row used the path prefix `/platform/v1beta1/...`; the exact version prefix wasn't independently re-confirmed on this review — treat it as a `NEEDS_EXEC_CHECK` and verify against the live Astro API reference before relying on a specific version prefix in an automation script. |

**Recommended approach for near-real-time SIEM**: Use the API polling method on a 5–15 minute cadence from a lightweight Lambda/Cloud Function or a separate dedicated Airflow DAG.

## Log Stream 2: Airflow Task Logs (Execution Plane)

Captures: task start/stop, stdout/stderr of task execution, operator-level logging.

| Method | Mechanism | Best For |
|---|---|---|
| **Vector Sidecar** | A Vector container deployed alongside each Airflow worker pod collects logs and forwards them to Splunk HEC or any compatible SIEM endpoint [B1]. Configured in `values.yaml` under `loggingSidecar`. | Real-time streaming to SIEM. |
| **Remote Object Storage → SIEM Connector** | Configure Airflow `remote_logging` to write task logs to S3/GCS/Azure Blob. Then use the cloud provider's SIEM connector (Splunk Add-on for AWS S3, Sentinel Azure Blob connector) to ingest from storage [B1]. | Batch ingestion; simpler setup. |

## SIEM-Specific Notes

| SIEM | Ingestion Method |
|---|---|
| **Splunk** | HTTP Event Collector (HEC) — for both audit log API polling and Vector sidecar [B1]. |
| **Microsoft Sentinel** | Log Analytics HTTP Data Collector API (for audit logs); Azure Blob Storage Connector (for task logs via remote logging) [B1]. |
| **Elastic/Datadog/Others** | Use the Vector sidecar configured with the appropriate output sink. Vector supports 40+ output targets natively. |

## Security

Store SIEM credentials (Splunk HEC tokens, Sentinel workspace keys) in your Secrets Backend — never in `values.yaml` plaintext or environment variables [B1].

## Sources

[B1] Astronomer Docs — Export audit logs (NDJSON format, CLI export): https://www.astronomer.io/docs/astro/audit-logs#export-audit-logs (tier 1, URL added on citation review). The Vector sidecar configuration for task log forwarding is Astro Private Cloud remote-logging content not independently re-verified with a specific URL on this pass.
[B3] Astronomer Docs — Platform API reference, audit logs endpoint (`GET /organizations/{organizationId}/audit-logs`): https://www.astronomer.io/docs/astro/api (tier 1, added on doc-verification review — flags the version-prefix uncertainty in the row above rather than asserting a specific one)
