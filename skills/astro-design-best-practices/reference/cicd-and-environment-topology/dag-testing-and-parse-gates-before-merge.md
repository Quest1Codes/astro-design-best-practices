# DAG Testing and Parse Gates Before Merge

AutoSys JIL validation often happened *after* import, relying on the `chk_auto_up` utility or runtime failures. In Airflow, pushing syntax errors to the metadata database can crash the Scheduler. 

A rigorous "Parse Gate" in your CI/CD pipeline prevents broken code from ever reaching the Astro platform.

## The testing pyramid

Your CI/CD pipeline should enforce a layered testing strategy on every Pull Request (PR) [B1].

### 1. Parse / Integrity check (The absolute minimum)

The CI runner must execute `astro dev parse`.
- **What it does**: Checks for basic Python syntax errors, import errors, and structural DAG validity (e.g., cyclic dependencies).
- **Mechanism**: The CI pipeline fails immediately if this command returns a non-zero exit code.
- **Why it matters**: It is fast, safe, and guarantees the DAG will at least load into the Airflow UI without crashing the parsing loop.

### 2. Unit testing (Custom logic validation)

Use `pytest` to validate business logic without requiring a running Airflow cluster [B2].
- **Astronomer Best Practices Repo**: Astronomer maintains a public `best_practices_pytests` repository. Import these tests to enforce standards (e.g., ensuring `catchup=False` is set globally, checking for hardcoded secrets, validating naming conventions).
- **Custom Operators**: If you write custom operators in `plugins/`, they must have unit tests.

### 3. Ephemeral Integration testing (High-risk changes)

For massive refactors or Airflow version upgrades, parsing is not enough; you need to ensure the task actually executes.
- **Implementation**: The CI pipeline triggers the creation of an **Ephemeral Astro Deployment** [B3]. The PR code is pushed to this temporary environment, tests run against real (non-production) data sources, and the deployment is destroyed when the PR merges.

## "Fail Fast" pipeline design

Do not run expensive integration tests if basic parsing fails. Structure your GitHub Actions / GitLab CI yaml so that the `astro dev parse` step is the very first gate. 

> **Important Note on `DagBag` tests**: If your `pytest` suite uses `DagBag` to load DAGs, ensure the CI environment mocks required Airflow Variables and Connections. Otherwise, the tests will fail with "Variable X does not exist" simply because the CI runner isn't connected to the database.

## Sources

[B1] Astronomer Docs — Validating and testing DAGs (accessed 2026-08-08)
[B2] Astronomer GitHub (`best_practices_pytests`) — Example testing suites (accessed 2026-08-08)
[B3] Astronomer Docs — CI/CD ephemeral deployments (accessed 2026-08-08)
