# Vertical Overlay: Healthcare (HIPAA)

HIPAA compliance for Airflow on Astro follows a **shared responsibility model**: Astronomer secures the platform infrastructure and provides the tools; the customer is responsible for configuring them correctly and signing the required agreements.

## Pre-Conditions (Non-Negotiable)

Before processing Protected Health Information (PHI) in any Airflow pipeline on Astro:

1. **Sign a Business Associate Agreement (BAA) with Astronomer** [B1][B2]. Without a BAA, using Astro to process PHI is a HIPAA violation regardless of your technical controls.
2. **Use a dedicated single-tenant cluster** (Business or Enterprise plan) [B1][B2]. Shared multi-tenant clusters are not eligible for HIPAA workloads. The cluster provides physical and logical isolation of compute, network, and storage.
3. **Confirm cloud provider HIPAA eligibility**: Ensure the underlying cloud provider services used (EC2 instance types, managed DB, object storage) are covered under the cloud provider's own BAA (AWS, GCP, or Azure all offer HIPAA-eligible services) [B1].

## PHI Handling in DAG Design

| Risk | Required Control |
|---|---|
| PHI logged in task logs | Never pass raw PHI values through XComs or render them in operator args. Mask or hash at ingestion [B1][B2]. |
| PHI in Airflow Variables or Connections | Prohibited. Use an external Secrets Backend (Vault, AWS Secrets Manager) [B1][B2]. |
| PHI in DAG `dag_run.conf` | If unavoidable, ensure these values are masked in logs and never stored in the metadata DB beyond task completion. |
| PHI extracted to staging environments | Prefer "query-in-place" architectures that analyze data within the secure warehouse/EHR system rather than extracting and moving PHI [B2]. |

## Encryption Requirements

- **At rest**: AES-256 for all storage (metadata DB, object storage for logs, data lake) [B2].
- **In transit**: TLS 1.2+ for all connections between Airflow components and external systems [B2].

## Minimum Necessary Access

- Apply DAG-level RBAC: only authorized healthcare data engineers should be able to trigger or view PHI-processing pipelines [B1].
- Integrate with your enterprise SSO/IdP (Okta, Entra ID) for centralized identity and access management [B1].
- Enable Astro audit logging and ship to your immutable SIEM for HIPAA audit trail requirements.

## Sources

[B1] Astronomer Docs — HIPAA compliance overview, BAA requirement, and dedicated cluster requirement (accessed 2026-08-10)
[B2] Astronomer Security Docs — PHI handling best practices, encryption standards, and secrets management for healthcare (accessed 2026-08-10)
