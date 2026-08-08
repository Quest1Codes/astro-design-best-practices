# Audit-Log Design for Access and Actions

AutoSys audit trails were typically managed at the OS/RDBMS level — DBA-controlled DB audit logs or OS-level login records. Astro provides a native, exportable audit log for platform-level events; Airflow's own task execution history in the metadata DB provides the operational data lineage layer.

## What Astro audit logs capture

Astro audit logs track "who did what, where, and when" [B2][B4]:

| Event category | Examples |
|---|---|
| **API events** | Actions from Astro UI, Astro CLI, or internal control plane [B2][B5] |
| **Airflow UI access** | Which users accessed the Airflow UI [B2][B5] |
| **Container registry access** | Users accessing the Astronomer registry via CLI [B2][B5] |
| **Deployment changes** | Deployments created/modified/deleted, code pushes |
| **User/role changes** | User invited, role changed, user removed |

## Retention and export

| Property | Value |
|---|---|
| **Native retention** | 90 days [B1][B2] |
| **Export format** | Newline-delimited JSON (NDJSON) or GZIP [B2][B5] |
| **Export methods** | Astro UI, Astro CLI |
| **Long-term storage** | Export to S3, GCS, or SIEM (Datadog, Splunk) [B6][B1][B3] |

> **90-day native retention is insufficient for most compliance audit requirements** (SOX requires 7 years, HIPAA 6 years). Implement an automated export pipeline to long-term storage before the window expires.

## Two-layer audit architecture

```
Layer 1: Astro platform audit logs
  → captures: who accessed the platform, what deployments/users changed
  → export: NDJSON → S3/SIEM

Layer 2: Airflow task execution history (metadata DB)
  → captures: which DAG ran, which task ran, who triggered it, start/end times, state
  → export: airflow db export-archived + long-term storage (see topic 027)
```

Neither layer alone is sufficient for a complete audit trail.

## Deployment model (Axis A — H rating)

| Deployment model | Audit log access |
|---|---|
| **Astro Hosted** | Access audit logs via Astro UI or CLI; no direct control plane access |
| **Astro Private Cloud** | Same; contact Astronomer for specific Private Cloud audit log paths |

## Compliance standard mapping

| Standard | Audit requirement | Astro coverage |
|---|---|---|
| SOC 2 Type II | Access control events, change management, monitoring | ✓ Platform logs + metadata DB [B1][B7] |
| HIPAA | PHI access audit trail, user access controls | ✓ Platform logs; requires BAA with Astronomer [B7][B10] |
| PCI-DSS | Card data access logs | ✓ [B1] |
| GDPR | Data access and deletion | ✓ Platform logs; requires data mapping |
| SOX (7-year retention) | Change management, access control | ✓ with long-term export |

Astro is certified SOC 2 Type II, HIPAA, PCI-DSS, and GDPR-capable [B1][B7][B8].

## SIEM integration design

```
Astro audit log (NDJSON)
  → scheduled export (CLI or API, e.g. daily)
  → S3 / GCS bucket (as archive)
  → SIEM ingest (Datadog, Splunk, Elasticsearch)
  → alerting rules on suspicious events (privilege escalation, bulk deletions)
```

## Sources

[B1] Astronomer Docs — Security and compliance: https://www.astronomer.io/docs/astro/security (accessed 2026-08-08)
[B2, B5] Astronomer Docs — Audit logs: https://www.astronomer.io/docs/astro/audit-logs (accessed 2026-08-08)
[B3] Astronomer Docs — Export audit logs to external storage (accessed 2026-08-08)
[B4] Kiteworks — Audit log best practices (accessed 2026-08-08)
[B6] Astronomer Docs — SIEM integration (accessed 2026-08-08)
[B7, B10] Astronomer Docs — HIPAA compliance and BAA: https://www.astronomer.io/docs/astro/hipaa-compliance (accessed 2026-08-08)
[B8] NudgeSecurity (independent verification of Astronomer certifications, accessed 2026-08-08)
