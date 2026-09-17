# Environment-Specific Connection Management

When promoting DAGs from Development to Production, the code must remain identical. Therefore, you cannot hardcode environment-specific logic (e.g., `db_conn = 'prod_db'`) into the DAG.

Instead, define abstracted connection IDs (e.g., `db_conn = 'data_warehouse'`) and resolve them to environment-specific credentials using deployment-level management strategies.

## Strategies for Connection Resolution

### 1. Astro Environment Manager (Recommended)
Astronomer provides a native Environment Manager in the Astro UI.
- **Centralized Control**: Create a connection once (e.g., `data_warehouse`) at the Workspace level [B1].
- **Per-Deployment Overrides**: Override specific fields for individual Deployments. For example, change the `Host` field to point to the sandbox DB for the Dev deployment, and the production DB for the Prod deployment [B1][B2].

### 2. External Secrets Backend
For organizations mandating strict security controls, use external secrets managers (e.g., AWS Secrets Manager, HashiCorp Vault).
- **Environment Isolation**: Point the Dev Airflow deployment to a `dev-vault` and the Prod Airflow deployment to a `prod-vault` [B3]. 
- **Resolution**: Both environments request the secret path `airflow/connections/data_warehouse`. The backend resolves it to the correct environment credential seamlessly [B4].

### 3. Environment Variables
For non-sensitive connections, you can define them as environment variables on the Deployment.
- **Naming Convention**: `AIRFLOW_CONN_{CONN_ID}` (e.g., `AIRFLOW_CONN_DATA_WAREHOUSE`).
- **Configuration**: Set these in the Astro UI Environment tab per Deployment [B5][B6].

## Local Development Workflow

When developers use `astro dev start`, they need access to development connections without hardcoding them into the repository.
- **Astro CLI Integration**: The CLI can automatically fetch connections defined in the Astro Environment Manager and inject them into the local Airflow instance, eliminating the need to manage local `.env` files manually [B7].

## Sources

[B1, B2] Astronomer Docs — Manage Airflow connections, variables, and environment variables, Astro Environment Manager section (per-Deployment overrides): https://www.astronomer.io/docs/astro/manage-connections-variables#astro-environment-manager (tier 1, URL added on citation review)
[B3, B4] Astronomer Docs — Configure a secrets backend: https://www.astronomer.io/docs/astro/secrets-backend (tier 1, URL added on citation review)
[B5, B6] Astronomer Docs — Manage Airflow connections in Astro (environment-variable-based connections): https://www.astronomer.io/docs/learn/connections (tier 1, URL added on citation review)
[B7] Astronomer Docs — Use connections locally (`astro dev start --deployment-id`, syncing Environment Manager connections to local development): https://www.astronomer.io/docs/cli/v1.45/local-connections (tier 1, URL added on citation review)
