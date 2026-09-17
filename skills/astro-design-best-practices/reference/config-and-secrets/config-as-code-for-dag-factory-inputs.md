# Config-as-Code for DAG-Factory Inputs

When implementing a DAG Factory pattern (see topic 001) for large-scale AutoSys migrations, pipelines are generated dynamically from configuration files. Managing these input files correctly is critical for performance and maintainability.

## Best Practices for Configuration Files

### 1. Storage and Format
- **Format**: Prioritize **YAML** over JSON for `dag-factory` inputs. YAML supports comments, multi-line strings, and is significantly more readable for complex task definitions [B1].
- **Storage**: Maintain a dedicated directory for configs (e.g., `dags/configs/`). Do not mix config files with the Python scripts that load them [B1].

### 2. Modularity vs. Monoliths
- **Anti-pattern**: Storing the configuration for 10,000 DAGs in a single `master_config.yaml`.
- **Best Practice**: Break configurations down logically by business unit, team, or application (e.g., `finance_pipelines.yaml`, `marketing_pipelines.yaml`). This reduces merge conflicts and makes version control manageable [B1].

### 3. Prevent DB Lookups during Parsing
- **Critical Rule**: Never fetch configuration data from an external database, API, or Airflow Variable during the DAG parsing phase [B2]. 
- **Why**: The scheduler parses all DAG files continuously. A DB query in the top-level loop will crash the scheduler. 
- **Solution**: Export configurations into static YAML files in the `dags/` folder so the scheduler can parse them from the local disk [B2].

## Feature Mapping

| Configuration Need | Implementation |
|---|---|
| Repetitive task parameters | Define a global `default_args` block in the YAML to reduce redundancy [B1]. |
| Complex Python Objects | Use the `__type__` key in YAML to instruct `dag-factory` to instantiate specific Python objects (e.g., `timedelta`) [B1]. |
| Explicit Dependencies | Define execution order using the `dependencies` key to keep task graphs readable [B1]. |

## CI/CD Validation

Treat your YAML configs as code. Add a validation step in your CI/CD pipeline that attempts to parse the YAML files through your generator script *before* deploying to production [B3]. This catches syntax errors and missing keys early.

## Sources

[B1, B2] Astronomer Docs — Use DAG Factory to create dags (YAML structuring, `dag-factory` package): https://www.astronomer.io/docs/learn/dag-factory (tier 1, URL added on citation review)
[B3] Astronomer Docs — Set up CI/CD, test and validate dags in your CI/CD pipeline (Astro CLI pytest/parse checks): https://www.astronomer.io/docs/astro/set-up-ci-cd#test-and-validate-dags-in-your-ci/cd-pipeline (tier 1, URL added on citation review)
