# Astro CLI Deploy Pipeline Design

AutoSys deployments often involved custom shell scripts, manual JIL imports (`jil < job.jil`), or proprietary promotion tools. Astronomer standardizes this process using the `astro` CLI integrated directly into your CI/CD pipeline (e.g., GitHub Actions, GitLab CI).

## Core deployment strategies

The `astro` CLI provides different deployment modes depending on what has changed in your project. A well-designed CI/CD pipeline intelligently selects the correct command to optimize deployment speed [B1].

| Command | Triggers when | Speed | Effect |
|---|---|---|---|
| `astro deploy` | `Dockerfile`, `requirements.txt`, `plugins/` change | Slowest | Triggers a full Docker image build and restart of all Airflow components. |
| `astro deploy --dags` | Only `dags/` folder changes | Fastest | Bypasses the Docker build. Hot-reloads DAG files without restarting the Scheduler or Workers. |

> **Design principle**: Your CI/CD pipeline should use path-filtering (e.g., `paths: ['dags/**']` in GitHub Actions) to trigger `astro deploy --dags` whenever possible. This significantly reduces deployment times from minutes to seconds [B1][B2].

## Authentication

Never use human user credentials for CI/CD. 
- Create a **Deployment API Token** (or Workspace API Token) in the Astro UI.
- Store this token securely in your CI provider's secrets manager (e.g., GitHub Secrets).
- The `astro` CLI authenticates automatically if the `ASTRO_API_TOKEN` environment variable is set [B3].

## Standard pipeline template (Axis G — CI/CD tool)

Regardless of the CI/CD platform, the pipeline steps must be:

1. **Checkout Code**: Pull the specific branch or commit.
2. **Install Astro CLI**: Download the latest CLI binary.
3. **Parse Gate (Required)**: Run `astro dev parse` or `pytest` to validate DAG integrity before deploying (see topic 055) [B4].
4. **Deploy**: Execute `astro deploy` targeting the specific Deployment ID.

## Sources

[B1, B2] Astronomer Docs & Community — Optimizing deployment speed with `--dags` flag (accessed 2026-08-08)
[B3] Astronomer Docs — Deployment API tokens (accessed 2026-08-08)
[B4] Astronomer Docs — Astro CLI parse validation in CI/CD (accessed 2026-08-08)
