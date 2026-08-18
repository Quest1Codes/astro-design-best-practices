# Global-Variable-Sprawl Remediation

AutoSys deployments often heavily relied on global `%%VAR%%` patterns. A common migration trap is executing a "lift-and-shift," creating thousands of Airflow Variables to replicate this flat, global state. 

This approach cripples Airflow's metadata database and creates maintenance nightmares.

## Remediation Strategies

During the migration assessment phase, identify the *purpose* of each AutoSys variable and refactor it into the appropriate Airflow construct.

### 1. Variables used for Task Communication
- **Legacy**: Job A writes a value to a global `VAR`. Job B reads it.
- **Airflow Solution**: Eliminate the global variable. Use **XComs** (Cross-Communication) to pass data directly between tasks within a DAG run [B1].

### 2. Variables used for Repetitive DAG Configs
- **Legacy**: Every job references a `VAR` for the base file path or retry logic.
- **Airflow Solution**: Use `default_args` within the Python DAG definition. This keeps configurations close to the code, modular, and version-controlled, eliminating DB lookups [B2].

### 3. Variables used for Environment Targeting
- **Legacy**: `%%DB_HOST%%` changes based on the AutoSys instance.
- **Airflow Solution**: Use **Environment Variables** (`os.getenv()`) injected via the CI/CD pipeline or the Astro Environment Manager [B3].

### 4. Variables containing Secrets
- **Legacy**: Passwords or API keys stored as plain text `VAR`.
- **Airflow Solution**: Migrate immediately to an external **Secrets Backend** (e.g., HashiCorp Vault, AWS Secrets Manager) [B4].

## Managing remaining variables

For the variables that genuinely need to remain as global Airflow Variables:
- **Use JSON Structures**: Instead of creating 50 separate variables for a single application (e.g., `app1_host`, `app1_port`, `app1_path`), group them into a single JSON Airflow Variable (`app1_config`). This reduces database queries [B2].
- **Automate Deployment**: Stop managing variables via the Airflow UI ("snowflake" configurations). Manage them as JSON files in your Git repository and deploy them via the Astro CLI or CI/CD pipelines [B3].

## Sources

[B1, B2] Apache Airflow Docs — Best practices for DAG authoring, XComs, and JSON variables (accessed 2026-08-08)
[B3] Astronomer Docs — Managing configurations across environments (accessed 2026-08-08)
[B4] Astronomer Docs — Secrets Backends integration (accessed 2026-08-08)
