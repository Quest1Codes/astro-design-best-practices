# Dev/Staging/Prod Deployment Topology

AutoSys instances were typically massive, shared environments. "Dev" and "Prod" were entirely different physical servers, often shared by the entire enterprise. Airflow is not natively multi-tenant; a single bad DAG in a shared environment can crash the scheduler for everyone.

**Astronomer best practice is to use multiple, isolated Airflow Deployments** for each environment lifecycle stage (Dev, Staging, Prod) within an Astro Workspace [B1][B2].

## Deployment separation

| Environment | Purpose | Infrastructure Strategy |
|---|---|---|
| **Development** | Sandbox for active building | **Permanent**: Single small deployment linked to a `develop` branch. Enable *Deployment Hibernation* (currently a **Preview** feature [B3]) to scale resources to zero when not in use, saving costs.<br>**Ephemeral**: CI/CD spins up a temporary preview deployment per PR, destroyed on merge [B4]. |
| **Staging** | UAT, integration testing, dry-runs | **Permanent**: Matches production scale and configuration (minus production secrets). Mapped to `staging` or `release` branch. |
| **Production** | Live workloads | **Permanent**: High-availability setup, highly optimized autoscaling. Mapped strictly to the `main` branch. |

## "Noisy Neighbor" isolation

By giving different environments their own Deployments, you achieve physical isolation. A memory-leak in a Dev DAG will only crash the Dev Scheduler pod, leaving Staging and Production completely unaffected [B1][B5]. 

## Environment variables and connections

Do not hardcode environment differences in your DAG code (e.g., `if env == 'prod': ...`). 
- Maintain identical DAG code across all environments.
- Use **Workspace Environment Managers** (or Deployment-level variables) in the Astro UI to define connections. 
- Example: The connection ID `data_warehouse` exists in all three deployments, but points to `snowflake_dev` in the Dev Deployment, and `snowflake_prod` in the Prod Deployment [B6].

## Sources

[B1, B2, B5] Astronomer Docs — Multi-tenancy in Airflow: https://www.astronomer.io/docs/learn/airflow-multi-tenancy (tier 1)
[B3] Astronomer Docs — Deployment resources, hibernate a development Deployment: https://www.astronomer.io/docs/astro/deployment-resources#hibernate-a-development-deployment (tier 1)
[B4] Astronomer Docs — Automate preview Deployments with any CI/CD tool: https://www.astronomer.io/docs/astro/ci-cd-templates/preview-deployments (tier 1)
[B6] Astronomer Docs — Manage Airflow connections, variables, and environment variables: https://www.astronomer.io/docs/astro/manage-connections-variables (tier 1)
