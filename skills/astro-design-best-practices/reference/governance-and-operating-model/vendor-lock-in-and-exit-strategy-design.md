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
2. **Export variables, and handle Connections separately**: `astro deployment variable list --deployment-id <id> --save` exports Deployment **environment variables**. **Correction**: an earlier draft of this step described it as exporting "connections and variables" together — it does not; Airflow Connections aren't covered by this command. Connections stored in the metadata DB need a separate export path (e.g. `airflow connections export` run against the Deployment, or reading directly from your Secrets Backend if that's the system of record) [B2][B3]. Store the output in Git (secrets redacted; retrieve from Secrets Backend).
3. **Target environment**: Provision a standard Airflow deployment using the official Helm chart on any Kubernetes cluster (EKS, GKE, AKS, on-prem K8s) [B2].
4. **CI/CD pipeline**: Replace Astro-specific CI/CD steps (e.g., `astro deploy`) with standard Docker build + Helm deploy steps. The rest of the pipeline (DAG tests, parse checks) is identical [B2].
5. **Metadata DB**: Provision a new PostgreSQL instance; run `airflow db migrate` to create the schema. Task history is **not** migrated (not worth the schema compatibility risk) [B2].

## Design Rules to Maintain Portability

- **Develop locally with `astro dev start`**: The local environment is Docker-based and reproduces the same Airflow version without any Astronomer infrastructure [B1].
- **Avoid hardcoding Astro-specific environment variables** in DAG logic.
- **Manage Deployments via Terraform**: IaC definitions are portable to other providers with minimal changes [B1].
- **Never depend on Astronomer-only APIs inside DAG code**: Your DAG code must be executable on vanilla Airflow.

## Sources

[B1] Astronomer Docs — Create an Astro project (`astro dev init` directory structure: `dags/`, `Dockerfile`, `requirements.txt`, `plugins/`): https://www.astronomer.io/docs/cli/v1.43/develop-project#create-an-astro-project (tier 1, added on doc-verification review); testing environments (local vs. Deployment): https://www.astronomer.io/docs/astro/dags-overview#testing-environments (tier 1, added on doc-verification review)
[B2] Astronomer Learn — Airflow object storage (`ObjectStoragePath` cloud-agnostic abstraction): https://www.astronomer.io/docs/learn/airflow-object-storage-tutorial (tier 1, added on doc-verification review). The Helm chart deployment and Connections/Variables export portions of this citation are Apache Airflow OSS content (airflow.apache.org) not indexed in the astronomer-docs MCP corpus — not independently re-verified on this pass.
[B3] Apache Airflow CLI reference — `airflow connections export` (exports Connections from the metadata DB; distinct from `astro deployment variable list`, which only covers Deployment environment variables): https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#export_1 (tier 2, added on doc-verification review — corrects the overstatement above)
