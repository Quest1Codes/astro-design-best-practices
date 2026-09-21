---
topic: dag-testing-and-parse-gates-before-merge
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# DAG Testing and Parse Gates Before Merge

AutoSys JIL validation often happened *after* import, relying on the `chk_auto_up` utility or runtime failures. In Airflow, pushing syntax errors to the metadata database can crash the Scheduler. 

A rigorous "Parse Gate" in your CI/CD pipeline prevents broken code from ever reaching the Astro platform.

## The testing pyramid

Your CI/CD pipeline should enforce a layered testing strategy on every Pull Request (PR) [B1].

### 1. Parse / Integrity check (The absolute minimum)

The CI runner must execute `astro dev parse`.
- **What it does**: Checks for basic Python syntax errors, import errors, and successful DAG rendering. **Correction**: an earlier draft of this file also attributed cyclic-dependency detection to `astro dev parse`; current docs describe `astro dev parse` as syntax/import-error checking only. Cyclic-dependency detection is covered separately, as part of the `astro dev pytest` example test suite (a `test_dag_example.py`-style "Dags have no cycles" test) — see the Unit testing section below.
- **Mechanism**: The CI pipeline fails immediately if this command returns a non-zero exit code.
- **Why it matters**: It is fast, safe, and guarantees the DAG will at least load into the Airflow UI without crashing the parsing loop.

### 2. Unit testing (Custom logic validation)

Use `pytest` to validate business logic without requiring a running Airflow cluster [B2].
- **`astro dev pytest`**: Astronomer's own example test suite (`test_dag_example.py`) includes structural checks beyond syntax — including a "Dags have no cycles" test — alongside business-logic checks like requiring `catchup=False`, retries, and tags. Import/adapt these tests to enforce standards rather than relying on `astro dev parse` for structural validity.
- **Custom Operators**: If you write custom operators in `plugins/`, they must have unit tests.

### 3. Ephemeral Integration testing (High-risk changes)

For massive refactors or Airflow version upgrades, parsing is not enough; you need to ensure the task actually executes.
- **Implementation**: The CI pipeline triggers the creation of an **Ephemeral Astro Deployment** [B3]. The PR code is pushed to this temporary environment, tests run against real (non-production) data sources, and the deployment is destroyed when the PR merges.

## "Fail Fast" pipeline design

Do not run expensive integration tests if basic parsing fails. Structure your GitHub Actions / GitLab CI yaml so that the `astro dev parse` step is the very first gate. 

> **Important Note on `DagBag` tests**: If your `pytest` suite uses `DagBag` to load DAGs, ensure the CI environment mocks required Airflow Variables and Connections. Otherwise, the tests will fail with "Variable X does not exist" simply because the CI runner isn't connected to the database.

## Sources

[B1] Astronomer Docs — Set up CI/CD, test and validate Dags: https://www.astronomer.io/docs/astro/set-up-ci-cd#test-and-validate-dags-in-your-ci/cd-pipeline (tier 1)
[B2] Astronomer GitHub (`best_practices_pytests`) — Example testing suites (accessed 2026-08-08)
[B3] Astronomer Docs — Automate preview Deployments with any CI/CD tool: https://www.astronomer.io/docs/astro/ci-cd-templates/preview-deployments (tier 1)
