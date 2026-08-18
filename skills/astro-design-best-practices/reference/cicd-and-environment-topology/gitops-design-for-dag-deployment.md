# GitOps Design for DAG Deployment

AutoSys deployments relied on moving definition files (JIL) and running imports against a database. With Airflow 3 and Astro, deploying DAGs directly from a Git repository via `GitDagBundle` is the recommended best practice for production GitOps workflows.

## The GitDagBundle Architecture

`GitDagBundle` allows Airflow to fetch DAGs directly from a Git repository rather than relying on baking them into a Docker image or using legacy `git-sync` sidecars [B1].

### Benefits of GitOps Bundles
- **Version Tracking**: Airflow natively tracks the history of DAG versions. You can rerun historical tasks using the exact code version that existed at that time.
- **Collision Prevention**: In legacy deployments, a code update mid-run could cause downstream tasks to execute with mismatched code. Bundles lock the version for the duration of the DAG run [B1][B2].
- **Isolation**: Multiple teams can maintain separate Git repositories, which are bundled into distinct logical units within a single Airflow environment.

## GitOps deployment best practices

### 1. Repository Organization
Follow the standard Astro structure, separating DAGs from heavy dependencies:
- `/dags`: Core orchestration logic.
- `/include`: External scripts, SQL queries, configuration JSON.
- `/plugins`: Custom operators and hooks.

### 2. DAG Hashing
Ensure DAG hashing is enabled (the default in Astro Agent 1.8.0+). The scheduler computes a hash of the DAG file and skips processing if the file has not changed. This drastically reduces CPU, memory, and network overhead when fetching from Git [B3].

### 3. Pipeline automation
GitOps requires that Git is the sole source of truth.
- Prevent any manual DAG uploads.
- The CI/CD pipeline pushes verified code to the designated branch (`main`). The Airflow Deployment continuously syncs the `GitDagBundle` from that branch.
- **Exception**: Changes to `requirements.txt` or `Dockerfile` still require a full CI/CD image build and deployment (`astro deploy`), as Python dependencies cannot be fetched dynamically via bundles [B3].

## Bundle selection (Axis B — Estate scale)

| Use Case | Bundle Type | Why |
|---|---|---|
| **Local Development** | `LocalDagBundle` | Rapid iteration on a laptop without committing to Git. |
| **Small / Simple** | Built-in Image deploy | DAGs are baked into the Docker image. Simple, but requires full restarts. |
| **Production / Multi-team** | `GitDagBundle` | Version tracking, isolation, and fast code updates without image rebuilds [B1]. |

## Sources

[B1, B2] Astronomer Docs — Airflow 3 DAG Versioning and Bundles (accessed 2026-08-08)
[B3] Astronomer Docs — GitOps deployment strategies and DAG hashing (accessed 2026-08-08)
