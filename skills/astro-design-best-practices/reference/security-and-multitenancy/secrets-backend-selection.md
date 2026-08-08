# Secrets-Backend Selection

AutoSys stored job credentials in its RDBMS (encrypted at the DB level, managed by the DBA team) or in OS-level keystores. Airflow's connection and variable storage has three tiers; the choice of tier is a security architecture decision, not a convenience choice.

## Airflow secret lookup priority

When a secrets backend is configured, Airflow resolves connections and variables in this order [B5]:
```
1. Secrets backend (external provider)  ← highest priority
2. Environment variables
3. Airflow metadata database (UI-stored)
```

## Backend option matrix

| Backend | Supported on Astro | Auth model | Best fit |
|---|---|---|---|
| **Astro Environment Manager** | Hosted + Private Cloud | Astro-native | Any Astro deployment; cross-Deployment sharing [B3] |
| **HashiCorp Vault** | All [B1] | Token / AppRole / Kubernetes auth | Multi-cloud or hybrid estates; dynamic secrets needed |
| **AWS Secrets Manager** | All [B1] | IAM roles (Workload Identity) | AWS-native estates |
| **AWS SSM Parameter Store** | All [B1] | IAM roles | Lighter-weight AWS secret storage; no auto-rotation built-in |
| **GCP Secret Manager** | All [B1] | Workload Identity / service account | GCP-native estates |
| **Azure Key Vault** | All [B1] | Managed Identity | Azure-native estates |
| **Environment variables** | All | Static, plaintext | Non-sensitive config only; not recommended for credentials [B3] |
| **Metadata DB** | All | Fernet-encrypted at rest | Development/prototype only; avoid in production [B3] |

## Selection guidance

| If your estate is… | Choose |
|---|---|
| Fully Astro Hosted, single cloud provider | Astro Environment Manager + cloud-native backend (AWS/GCP/Azure) |
| Multi-cloud or hybrid | HashiCorp Vault (platform-agnostic, dynamic secrets) |
| Needing automated credential rotation | HashiCorp Vault or AWS Secrets Manager (both support rotation) |
| Regulated (SOX/HIPAA) requiring audit trail per secret access | HashiCorp Vault (per-access audit log) or cloud-native with CloudTrail/Cloud Audit Logs |

## Naming convention (required for auto-discovery)

Airflow locates secrets in the backend by path. Standard paths [B5]:
```
airflow/connections/<conn_id>
airflow/variables/<variable_key>
```
Configure the backend's `connections_prefix` and `variables_prefix` to match, or use your backend's native prefix convention.

## Common pitfall: `Variable.get()` in top-level DAG code

Never call `Variable.get()` or connection lookups in top-level DAG file code. This forces the scheduler to query the backend on every parse cycle, causing performance degradation [B3]. Use Jinja templating (`{{ var.value.my_key }}`) to defer lookup to task execution.

## Deployment model (Axis A — H rating)

| Deployment model | Secrets configuration |
|---|---|
| **Astro Hosted** | Configure per-Deployment in Astro UI; Astro Environment Manager is the first-choice |
| **Astro Private Cloud / Remote Execution** | Secrets backend must also be accessible from the Remote Execution Agent's network [B6][B7] |
| **Self-managed** | Configure `airflow.cfg` `[secrets]` section; manage auth credentials for the backend separately |

## Compliance callout (Axis E — H rating)

For SOX/HIPAA/FedRAMP, use a backend that provides per-access audit logging (Vault audit log, AWS CloudTrail, GCP Cloud Audit Logs). The Airflow metadata DB provides no access-per-secret audit trail.

## Sources

[B1] Astronomer Docs — Configure a secrets backend: https://www.astronomer.io/docs/astro/secrets-backend (accessed 2026-08-08)
[B3] Astronomer Learn — Connections, variables, and secrets: https://www.astronomer.io/docs/learn/connections (accessed 2026-08-08)
[B5] Apache Airflow Docs — Secrets backend: https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/ (accessed 2026-08-08)
[B6, B7] Astronomer Docs — Remote Execution secrets configuration (accessed 2026-08-08)
