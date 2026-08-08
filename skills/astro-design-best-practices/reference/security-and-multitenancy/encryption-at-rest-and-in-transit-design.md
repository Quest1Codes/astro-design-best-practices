# Encryption at Rest and in Transit Design

AutoSys used OS/RDBMS-level encryption (TDE on Oracle/SQL Server for the Event Server DB; OS-level TLS for agent-to-server communications). Astro enforces encryption by default at the platform level; user design decisions are limited to key management and Fernet key rotation in self-managed contexts.

## Astro's default encryption posture (Hosted)

### In transit

| Layer | Mechanism |
|---|---|
| All control plane ↔ data plane traffic | mTLS mesh |
| Internal data plane service communication | TLS 1.2 + strong ciphers |
| External client ↔ Astro (UI, CLI, API) | TLS 1.2/1.3 |
| Certificates | Auto-renewed every 90 days by Astronomer's certificate management platform |

Astro enforces encryption for all data in motion across control and data planes [B-transit].

### At rest

| Data | Mechanism |
|---|---|
| All data on disk (DB backups, temp query files) | AES-256 [B-rest] |
| Data plane volumes | Server-side encryption; keys managed by cloud provider (AWS KMS, GCP KMS, Azure Key Vault) |
| Secrets in the data plane (etcd) | AES-256 encrypted etcd cluster [B-rest] |

**Astro Hosted is "secure by default"** — no user configuration required for baseline encryption.

## Fernet key design (self-managed and BYOD contexts)

Airflow uses a Fernet key (`fernet_key` in `airflow.cfg`) to encrypt passwords and sensitive variables stored in the metadata DB:
- Algorithm: AES-128-CBC + HMAC-SHA256
- Required on: self-managed Astronomer Software or any deployment where connections/variables are stored in the metadata DB

### Key management design

| Practice | Implementation |
|---|---|
| Never hardcode in `airflow.cfg` | Inject via environment variable or secrets backend |
| Rotation without downtime | Set `fernet_key` to a comma-separated list: `new_key,old_key` — Airflow decrypts with old key and re-encrypts with new key |
| Store the key | In a secrets manager (Vault, AWS SM, GCP SM), not in source code or CI/CD logs |

> On Astro Hosted, Fernet key management is handled by Astronomer; users do not configure it directly.

## Customer-managed keys (BYOK)

For regulated environments requiring customer ownership of encryption keys:
- Use BYOD external PostgreSQL with cloud provider BYOK (AWS RDS with AWS KMS CMK; GCP Cloud SQL with CMEK; Azure Database for PostgreSQL with CMK)
- This requires the BYOD path (see topic 025 and topic 028)
- {syn: BYOK-practitioner-note — Astro Hosted does not currently expose a documented BYOK option for the managed metadata DB; verify with Astronomer SA for your specific compliance requirement}

## Deployment model (Axis A — H rating)

| Deployment model | User encryption design responsibilities |
|---|---|
| **Astro Hosted (standard or dedicated)** | None — Astronomer manages; certificates auto-renewed |
| **Astro Hosted + BYOD PostgreSQL** | Own cloud provider KMS config; own backup encryption; own BYOK if required |
| **Self-managed Astronomer Software** | Own Fernet key management, own TLS certificate rotation, own DB encryption config |

## Compliance standard mapping

| Standard | Encryption requirement | Astro coverage |
|---|---|---|
| SOC 2 Type II | Encryption in transit + at rest | ✓ [B-cert] |
| HIPAA | PHI encrypted in transit + at rest | ✓ [B-cert]; BAA required |
| PCI-DSS | Strong cryptography for card data | ✓ [B-cert] |
| GDPR | Data protection by design | ✓ |
| FedRAMP | FIPS 140-2 approved ciphers | `NEEDS_EXEC_CHECK` — confirm FedRAMP authorization status and FIPS cipher support directly with Astronomer for your specific deployment type |

## Sources

[B-transit, B-rest] Astronomer Docs — Security overview (encryption): https://www.astronomer.io/docs/astro/security (accessed 2026-08-08)
[Fernet] Apache Airflow Docs — Fernet key: https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/fernet.html (accessed 2026-08-08)
[B-cert] Astronomer Docs — Compliance certifications: https://www.astronomer.io/docs/astro/compliance (accessed 2026-08-08)
[BYOK] Cloud provider KMS docs — AWS KMS CMK for RDS / GCP CMEK for Cloud SQL / Azure CMK for PostgreSQL (accessed 2026-08-08)
