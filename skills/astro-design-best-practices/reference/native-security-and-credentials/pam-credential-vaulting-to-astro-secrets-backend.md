# PAM Credential-Vaulting Integration → Astro Secrets-Backend Design

AutoSys integrated with **Symantec/Broadcom PAM (Privileged Access Manager)** as its credential vault for job-execution credentials. PAM stored the privileged passwords used by AutoSys agent processes to authenticate to databases, APIs, and remote systems during job execution — preventing credentials from being embedded in JIL or shell scripts [B1].

In Airflow/Astro, the equivalent architectural role is played by a **Secrets Backend** — an external credential store that Airflow consults at runtime to resolve Connections and Variables.

## Supported Secrets Backends on Astro

| Backend | Environment Variable Class | Use Case |
|---|---|---|
| **HashiCorp Vault** | `airflow.providers.hashicorp.secrets.vault.VaultBackend` | On-prem or cloud-agnostic; closest PAM equivalent [B2]. |
| **AWS Secrets Manager** | `airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend` | AWS-native; recommended for AWS-hosted Astro Private Cloud [B2]. |
| **GCP Secret Manager** | `airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend` | GCP-native [B2]. |
| **Azure Key Vault** | `airflow.providers.microsoft.azure.secrets.key_vault.AzureKeyVaultBackend` | Azure-native [B2]. |

## Configuration

Set two Deployment-level environment variables in Astro (non-secret, configuration only):

```
AIRFLOW__SECRETS__BACKEND = airflow.providers.hashicorp.secrets.vault.VaultBackend
AIRFLOW__SECRETS__BACKEND_KWARGS = {"connections_path": "airflow/connections", "variables_path": "airflow/variables", "url": "https://vault.internal.company.com"}
```

Store the Vault authentication token or IAM role binding separately via Astro's environment variable secrets [B2].

## Airflow Secret Resolution Order (Cascading Lookup)

When a task requests `conn_id="finance_db"`, Airflow resolves it in this order [B2]:
1. **Secrets Backend** (Vault / Secrets Manager — this is where PAM-vaulted creds live)
2. **Environment Variables** (`AIRFLOW_CONN_FINANCE_DB=...`)
3. **Airflow Metadata DB** (Connections stored via Airflow UI)

For production PAM-equivalent security: credentials must live **exclusively in the Secrets Backend**. Do not store production credentials in the Airflow UI or environment variables.

## Key Design Rules

| Rule | Rationale |
|---|---|
| **Secrets Backend is read-only from Airflow's perspective** | `Variable.set()` writes to the metadata DB, not the external backend. Manage credential lifecycle directly in Vault/Secrets Manager [B2]. |
| **Use Workload Identity where possible** | AWS IAM roles or GCP Workload Identity instead of long-lived service account keys to authenticate Airflow to the secrets backend [B2]. |
| **Standardize path prefixes** | `airflow/connections/<conn_id>` and `airflow/variables/<key>` are the conventional paths; configure `connections_path` and `variables_path` in `BACKEND_KWARGS` to match [B2]. |
| **Enable audit logging on the vault** | The vault's access log is the equivalent of PAM's privileged session recording — required for SOX/audit compliance [B2]. |

## Sources

[B1] Broadcom AutoSys / Symantec PAM Documentation — PAM credential vaulting for AutoSys job-execution credentials (accessed 2026-08-11)
[B2] Astronomer Docs & Apache Airflow Docs — Secrets Backend configuration, supported backends (Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault), `AIRFLOW__SECRETS__BACKEND` env var, resolution order, read-only behavior of `Variable.set()` (accessed 2026-08-11)
