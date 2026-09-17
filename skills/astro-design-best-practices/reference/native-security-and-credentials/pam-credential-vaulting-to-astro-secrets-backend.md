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

When a task requests `conn_id="finance_db"`, Airflow resolves it in this order [B2][B3]:
1. **Secrets Backend** (Vault / Secrets Manager — this is where PAM-vaulted creds live)
2. **Astro Environment Manager** — an Astro-specific tier between the Secrets Backend and raw environment variables. **Correction**: an earlier draft of this file listed only 3 tiers and omitted this one; current Astronomer docs confirm 4 tiers in this exact order [B3].
3. **Environment Variables** (`AIRFLOW_CONN_FINANCE_DB=...`)
4. **Airflow Metadata DB** (Connections stored via Airflow UI)

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
[B2] Astronomer Docs — Configure a Secrets Backend on Astro (supported backends, `AIRFLOW__SECRETS__BACKEND` env var, read-only behavior of `Variable.set()`): https://www.astronomer.io/docs/astro/secrets-backend (tier 1, URL added on citation-hygiene review)
[B3] Astronomer Docs — Secrets backend, "How Airflow finds Connections or Variables" (4-tier resolution order: Secrets Backend → Astro Environment Manager → Environment Variables → Metadata DB): https://www.astronomer.io/docs/astro/secrets-backend#how-airflow-finds-connections-or-variables (tier 1, added on doc-verification review — corrects the 3-tier claim above, and is consistent with `config-and-secrets/environment-specific-connection-management.md` elsewhere in this skill)
