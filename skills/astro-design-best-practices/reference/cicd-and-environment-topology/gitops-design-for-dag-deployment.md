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
The Dag processor computes a hash of each Dag and caches it; on each processing cycle it compares the current hash against the cached value — if unchanged, it skips re-sending the Dag to the Astro orchestration plane, lowering memory utilization, network bandwidth, and speeding up Dag updates in Deployments with many Dags [B4]. **Correction history**: an earlier draft of this section cited this as "enabled by default in Astro Agent 1.8.0+"; a subsequent doc-verification pass, searching a different page than the one that actually covers it, couldn't confirm it and marked it as likely fabricated. A follow-up pass found the real source: Dag hashing is confirmed real and **enabled by default starting on Astro Agent client release 1.8.0**, disableable via `ASTRO_AGENT_CLIENT_DAG_PROCESSOR__ENABLE_DAG_CACHING=False` [B4]. The original claim was correct; the "likely fabricated" flag itself was the error. Monitor via the `dag_processor_cache_hits_total`, `dag_processor_cache_misses_total`, and `dag_processor_cache_size` metrics [B4].

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

[B1, B2] Astronomer Docs — Airflow feature support on Astro (Dag Versioning / Dag Bundles): https://www.astronomer.io/docs/astro/airflow-feature-support (tier 1) — NEEDS_EXEC_CHECK: not independently re-verified this page covers Dag Bundles specifically; confirm before relying on it
[B3] Astronomer Docs — GitOps deployment strategies (Dag-only deploys via Deploy Dags to Astro): https://www.astronomer.io/docs/astro/deploy-dags (tier 1) — pipeline-automation mechanics specifically not independently re-verified against this page; verify separately
[B4] Astronomer Docs — Configure Dag sources for a Remote Execution Agent, "Dag hashing" (enabled by default starting Astro Agent client release 1.8.0, `ASTRO_AGENT_CLIENT_DAG_PROCESSOR__ENABLE_DAG_CACHING` to disable, cache-hit/miss/size metrics): https://www.astronomer.io/docs/astro/remote-execution/remote-execution-configure-dag-sources#dag-hashing (tier 1, confirmed on follow-up review — restores and correctly sources the original pre-correction claim)
