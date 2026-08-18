# Per-Environment Variable Scoping

Managing variables across Dev, Staging, and Prod environments is critical for preventing cross-environment contamination. Hardcoding environment-specific logic (`if env == 'dev': path = 'x'`) inside DAG files is a major anti-pattern.

Astronomer provides specific scoping mechanisms to handle environment variables effectively.

## Scoping Strategy

| Scope Level | Implementation | Best For |
|---|---|---|
| **Workspace Level** | **Astro Environment Manager** | Shared configurations that must be identical across multiple Deployments (e.g., a shared timezone setting, common non-sensitive API endpoints) [B1]. |
| **Deployment Level** | **Astro UI "Environment" Tab** | Variables specific to a single environment (e.g., pointing the `Staging` deployment to the staging database). These override Workspace-level variables [B1]. |
| **DAG Level** | **DAG `default_args`** | Pipeline-specific configurations. Keeps configs modular and version-controlled with the DAG logic [B2]. |
| **Code / Container Level** | **Dockerfile** | Static configuration (e.g., `AIRFLOW__CORE__DAG_CONCURRENCY`). Stored in plaintext and version-controlled [B3]. |
| **Local Level** | **Local `.env` file** | Used by `astro dev start`. Must be added to `.gitignore` to prevent secret leakage into version control [B4]. |

## Masking Sensitive Variables

If you must use Airflow Variables (via the UI or environment variables) instead of a Secrets Backend, you can instruct Airflow to mask their values in the UI and logs.
- Include a sensitive substring in the variable name, such as `_KEY`, `_SECRET`, `_PASSWORD`, or `_TOKEN`. Airflow automatically redacts these from plain text view [B3].

## The "Top-Level Code" Anti-Pattern

Never use `Variable.get()` or `os.getenv()` at the top level of your DAG file (outside of a task).
- **Why**: The scheduler parses all DAG files every 30 seconds. A top-level `Variable.get()` triggers a database query or Secrets Backend API call *every single time the file is parsed*, causing severe performance degradation and potential rate-limiting from your secrets provider [B3].
- **Solution**: Use Jinja templating (`{{ var.value.my_var }}`) inside operators to defer the lookup until task execution [B2].

## Sources

[B1] Astronomer Docs — Astro Environment Manager and variable scoping (accessed 2026-08-08)
[B2, B3] Apache Airflow Docs — Best practices for Variables and Jinja templating (accessed 2026-08-08)
[B4] Astronomer Docs — Local development configuration (accessed 2026-08-08)
