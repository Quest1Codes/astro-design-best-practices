# Rollback Strategy Design

In legacy schedulers, rolling back a deployed job often meant manually re-importing an older version of a JIL file. In Astro, deployments are holistic (DAG code, Airflow version, and Python dependencies). Relying on reverting Git commits and waiting for a CI/CD pipeline to rebuild is too slow during a critical production outage.

## The "Deploy Rollbacks" feature

Astronomer provides a native **Deploy Rollbacks** feature in the Astro UI. It acts as an emergency "undo" button for your Airflow environment.

### How it works
- You can instantly revert a Deployment to any previously successful deploy state from the last 90 days [B1][B2].
- A rollback reverts **everything**: DAG code, `requirements.txt`, environment variables (if part of the deploy), and the Astro Runtime version [B1].
- It bypasses the CI/CD pipeline, resolving outages in seconds rather than minutes [B4].

## Rollback strategy and best practices

1. **Use as a Last Resort**: Rollbacks are for emergencies (e.g., a bad deployment is crashing the scheduler or corrupting data). Routine changes should flow forward through the CI/CD pipeline (e.g., reverting the commit in Git and pushing a fix).
2. **Audit Trails**: Always require developers/CI to populate the "Deploy Description" field during normal deployments. When an outage occurs at 3 AM, the on-call engineer needs descriptive tags to identify the correct "known-good" state to roll back to [B1][B9].
3. **Data Idempotency**: A rollback changes the code, but it does not un-do data writes. If a bad DAG ran and inserted bad data, rolling back the code prevents *future* bad data, but you must still manually clean up the database if the tasks were not idempotent [B8].
4. **Intermediate Deploys**: If you deploy Version A, B, and C, and then roll back from C to A, the changes introduced in B are also lost [B4][B5].

## Migrations and major version rollbacks

Rolling back across major Airflow versions (e.g., Airflow 3 down to Airflow 2) is complex. 
- While Astro supports rolling back the Runtime version, down-migrations of the underlying metadata database schema are risky and can result in data loss [B2][B10].
- Always consult Astronomer documentation specific to your Astro Runtime version before executing a rollback across major version boundaries [B1][B12].

## Sources

[B1, B2, B3] Astronomer Docs — Deploy Rollbacks overview (accessed 2026-08-08)
[B4, B5, B6] Astronomer Docs — Rollback permissions and behavior (accessed 2026-08-08)
[B8] Apache Airflow Docs — Idempotency (accessed 2026-08-08)
[B9, B10] Astronomer Docs — Identifying deploy history and DB migrations (accessed 2026-08-08)
