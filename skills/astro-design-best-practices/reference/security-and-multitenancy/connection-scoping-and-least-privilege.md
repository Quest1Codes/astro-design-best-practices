# Connection Scoping and Least Privilege

AutoSys job credentials were typically embedded in JIL (`machine:`, `login:`) or managed by the OS at the agent level — there was no concept of connection scoping across job boundaries. Airflow connections are global within a Deployment by default, which creates an implicit privilege expansion risk: any DAG author can reference any connection, including ones intended for other teams.

## The scoping problem

In a shared Deployment:
- Connection `prod_database_rw` is visible to all DAG authors
- A misconfigured or malicious DAG can use it without restriction
- There is no native per-DAG connection restriction below the RBAC level

Mitigation strategies, in order of decreasing isolation:

| Strategy | Isolation level | How |
|---|---|---|
| **Separate Deployment per team** | Strongest — connection pool is scoped to one team | Each team's Deployment has its own connection namespace |
| **DAG-level RBAC** (Astro Runtime 3.1-12+) | Logical — restricts which users can trigger which DAGs | Limits blast radius but doesn't prevent code from referencing shared connections |
| **Naming conventions + secrets backend scoping** | Weak — relies on discipline | Prefix connections by team (`finance_db_rw`, `ops_db_ro`) and document ownership |

Astronomer explicitly recommends separate Deployments over shared instances for teams with distinct security requirements [B4][B5].

## Least-privilege design for worker IAM/service accounts

Airflow workers execute tasks that connect to external systems. The worker's identity (service account / IAM role) determines what cloud resources it can reach.

| Risk pattern | Mitigation |
|---|---|
| Workers use a broad IAM role granting access to all data | Scope the worker's Workload Identity to only the cloud resources the Deployment's DAGs actually need |
| Static credentials in connections | Replace with Workload Identity / IAM role-based auth where the cloud provider supports it |
| Shared worker role across multiple Deployments | Give each Deployment its own Workload Identity binding |

## Workload Identity (recommended for cloud resources)

Astro supports Workload Identity on AWS, GCP, and Azure [B3]. This eliminates static `AWS_ACCESS_KEY_ID` / `GCP_SERVICE_ACCOUNT_JSON` style credentials in connections:

```
Astro Deployment (worker pod)
  → Kubernetes Service Account
  → Cloud Provider IAM role binding (IRSA / Workload Identity Federation)
  → Target resource (S3, BigQuery, Blob Storage)
```

Benefits: no static credential rotation, no credential in metadata DB, cloud-native audit trail per call.

## Connection storage decision table

| Storage location | Security level | Use case |
|---|---|---|
| Secrets backend (Vault, AWS SM, etc.) | Highest | Production; regulated environments [B3] |
| Astro Environment Manager | High | Astro Hosted production |
| Environment variable | Moderate | Non-sensitive or temp config |
| Airflow metadata DB (UI) | Low (Fernet-encrypted) | Development / prototype only [B3] |

## Org model (Axis D — H rating)

| Org model | Connection scoping approach |
|---|---|
| **Per-team Deployments** | Connection namespace is already isolated; least-privilege is enforced at the Deployment level |
| **Shared Deployment (multi-team)** | Use DAG-level RBAC + connection naming conventions + secrets backend path prefixes per team |

## Sources

[B3] Astronomer Learn — Connections, variables, and secrets best practices: https://www.astronomer.io/docs/learn/connections (accessed 2026-08-08)
[B4, B5] Astronomer Docs — Multi-tenancy in Airflow: https://www.astronomer.io/docs/learn/airflow-multi-tenancy (accessed 2026-08-08)
[B-Workload Identity] Astronomer Docs — Workload Identity: https://www.astronomer.io/docs/astro/authorize-deployments-to-your-cloud (accessed 2026-08-08)
