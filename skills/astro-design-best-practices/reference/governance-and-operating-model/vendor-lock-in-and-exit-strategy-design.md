# Vendor Lock-In and Exit-Strategy Design

Choosing Airflow was partly motivated by avoiding AutoSys's proprietary lock-in. But "Airflow" is not the same as "portable Airflow." Astronomer-specific features, cloud-native operator dependencies, and managed metadata create their own lock-in vectors. An explicit exit strategy preserves negotiating leverage and protects the investment in pipeline code.

## Lock-In Vectors: Honest Assessment

| Vector | Lock-In Risk | Mitigation |
|---|---|---|
| **Astronomer-specific executors or runtime extensions** | Medium — if you depend on Astro-only features | Prefer standard executors (KubernetesExecutor, CeleryExecutor); avoid proprietary-only extensions [B1]. |
| **Astro CLI project structure** | Low — follows standard Docker + Airflow conventions | The `Dockerfile`, `requirements.txt`, `dags/`, `plugins/` structure is portable to any Docker-based Airflow deployment [B1][B2]. |
| **Airflow metadata DB content** | Medium — task history, connections, variables are DB-specific | Export connections and variables to YAML/JSON and store in Git. Metadata history is disposable for most teams [B2]. |
| **Cloud-specific operators** | High if overused — `S3Operator`, `GCSOperator` etc. tie you to a cloud | Abstract via Airflow Connections — change connection string, not code. Use `ObjectStoragePath` (Airflow 2.8+) for cloud-agnostic storage operations [B2]. |
| **Open-source Airflow itself** | Low — Apache 2.0 licensed, no vendor controls the project | N/A — open source is the baseline protection |

## Exit Strategy: Moving Off Astronomer

If the decision is made to exit Astronomer and self-host (or move to another managed provider):

1. **DAGs are already portable**: If you followed the Astro CLI project structure, your DAGs, `requirements.txt`, and `Dockerfile` can be deployed to any standard Airflow on Kubernetes without modification [B1][B2].
2. **Export connections and variables**: Use `astro deployment variable list --deployment-id <id> --save` to export. Store the output in Git (secrets redacted; retrieve from Secrets Backend) [B2].
3. **Target environment**: Provision a standard Airflow deployment using the official Helm chart on any Kubernetes cluster (EKS, GKE, AKS, on-prem K8s) [B2].
4. **CI/CD pipeline**: Replace Astro-specific CI/CD steps (e.g., `astro deploy`) with standard Docker build + Helm deploy steps. The rest of the pipeline (DAG tests, parse checks) is identical [B2].
5. **Metadata DB**: Provision a new PostgreSQL instance; run `airflow db migrate` to create the schema. Task history is **not** migrated (not worth the schema compatibility risk) [B2].

## Design Rules to Maintain Portability

- **Develop locally with `astro dev start`**: The local environment is Docker-based and reproduces the same Airflow version without any Astronomer infrastructure [B1].
- **Avoid hardcoding Astro-specific environment variables** in DAG logic.
- **Manage Deployments via Terraform**: IaC definitions are portable to other providers with minimal changes [B1].
- **Never depend on Astronomer-only APIs inside DAG code**: Your DAG code must be executable on vanilla Airflow.

## Sources

[B1] Astronomer Docs — Astro CLI project structure, local development with Docker, and portability guidance (accessed 2026-08-11)
[B2] Apache Airflow Docs — Helm chart deployment, Connections/Variables export, `ObjectStoragePath` abstraction (accessed 2026-08-11)
