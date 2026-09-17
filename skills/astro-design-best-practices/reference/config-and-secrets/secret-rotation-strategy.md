# Secret Rotation Strategy

Migrating from AutoSys to Airflow presents an opportunity to modernize credential management. Hardcoding secrets or storing them in a database requiring manual updates is an anti-pattern. 

The industry standard for Airflow deployments on Astronomer is to integrate a **Secrets Backend** (e.g., AWS Secrets Manager, HashiCorp Vault, Azure Key Vault) [B1][B2].

## Why Secrets Backends solve the rotation problem

Airflow is designed to integrate seamlessly with external secrets managers.
- **Dynamic Retrieval**: Airflow fetches the secret from the backend *at runtime*, right when the task executes [B3][B4]. 
- **Zero-Downtime Rotation**: Because Airflow does not cache secrets in its metadata database, you do not need to restart the Airflow Scheduler or Webserver when a password changes [B3][B4]. 

## Designing the Rotation Strategy

1. **Automate Rotation in the Backend**: Use the native capabilities of your secrets manager (e.g., AWS Secrets Manager's automatic rotation for RDS databases). Airflow is a passive consumer [B5].
2. **Dynamic Secrets (Advanced)**: If using HashiCorp Vault, implement dynamic secrets. Vault generates short-lived, unique credentials on the fly for each Airflow task run. The secret expires immediately after use, effectively eliminating the need for periodic manual rotation [B6].

## Security Best Practices

| Domain | Best Practice |
|---|---|
| **Authentication** | Use **Workload Identity** (e.g., IAM Roles for Service Accounts) to authenticate the Airflow worker to the Secrets Backend. Avoid passing a static "master key" to Airflow [B7][B8]. |
| **Permissions** | Follow the principle of least privilege. The Airflow deployment should only have read access to the specific paths/keys it needs [B7][B8]. |
| **Local Development** | Never commit secrets to Git. Use a local, `.gitignore`d `.env` file when running `astro dev start` to simulate the secrets backend locally [B9]. |

## Sources

[B1, B2] Astronomer Docs — Configure a secrets backend: https://www.astronomer.io/docs/astro/secrets-backend (tier 1, URL added on citation review)
[B3, B4] Apache Airflow Docs — Secrets backend (retrieval mechanics): https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/ (tier 2, URL added on citation review)
[B5] AWS Docs — Secrets Manager automated rotation (third-party cloud provider docs, out of scope for Astronomer docs MCP; not re-verified on this pass)
[B6] HashiCorp Vault Docs — Dynamic Secrets integration with Airflow (third-party docs, out of scope for Astronomer docs MCP; not re-verified on this pass)
[B7, B8] Astronomer Docs — Authorize Deployments to your cloud, Workload Identity (least-privilege authentication to secrets backends): https://www.astronomer.io/docs/astro/authorize-deployments-to-your-cloud (tier 1, URL added on citation review)
[B9] Astronomer Docs — Use connections locally (`astro dev start`, local development with Environment Manager objects): https://www.astronomer.io/docs/cli/v1.45/local-connections (tier 1, URL added on citation review)
