# Feature-Flagging for Gradual DAG Rollout

AutoSys lacked native feature-flagging; new job streams were typically created with unique names or put on "ON ICE" until ready. In Airflow, gradual rollouts and A/B testing of pipelines can be achieved using native architectural features rather than maintaining duplicate DAGs.

## Strategies for gradual rollout

There is no single "Feature Flag" button in Airflow. Rollouts are handled via versioning, variables, or fast deployment cycles.

### 1. Airflow 3 DAG Versioning (Recommended)
Airflow 3 tracks code versions natively [B1][B2].
- When code changes, a new DAG version is tracked. 
- You can monitor the success rate of the new version compared to the old one via the UI. If the new version introduces instability, you have a clear audit trail of which version executed which task [B1][B4].

### 2. Logic-based flags (Airflow Variables)
For simple toggles (e.g., enabling a new downstream reporting task), use Airflow Variables combined with standard Python `if` statements [B5].

```python
from airflow.models import Variable

# Fetched at runtime to determine path
is_new_feature_enabled = Variable.get("enable_new_report", default_var="false") == "true"

with DAG(...) as dag:
    base_task = ...
    if is_new_feature_enabled:
        new_report_task = ...
        base_task >> new_report_task
```
- **Benefit**: You can toggle the logic instantly via the Astro UI without pushing code or rebuilding images.
- **Warning**: Do not put the `Variable.get()` call at the top level of the DAG (outside the task or without Jinja) as it will crash the metadata DB at scale (see topic 031).

### 3. DAG-only deploys (Fast iteration)
Use the Astro CLI's `astro deploy --dags` command to rapidly push modified DAGs to a staging environment without restarting the scheduler [B6]. This tightens the feedback loop for testing new logic.

### 4. The Safety Net: Deploy Rollbacks
If a feature rollout in production fails, rely on Astronomer's **Deploy Rollbacks** feature (see topic 059) to instantly revert the environment to the previous known-good state via the UI [B7][B8].

## Best practice sequence

1. **Gate**: Write the new logic gated behind an Airflow Variable.
2. **Test**: Run `dag.test()` in CI/CD [B10][B11].
3. **Deploy**: Push to production via CI/CD. The logic remains dormant because the variable defaults to `false`.
4. **Rollout**: Change the Variable to `true` in the Astro UI. Monitor the next run.
5. **Revert (if needed)**: Change the Variable back to `false`.

## Sources

[B1, B2, B3, B4] Astronomer Docs — Airflow 3.0 DAG Versioning (accessed 2026-08-08)
[B5] Astronomer Docs — Using Airflow Variables for dynamic logic (accessed 2026-08-08)
[B6] Astronomer Docs — DAG-only deploys (accessed 2026-08-08)
[B7, B8, B9] Astronomer Docs — Deploy Rollbacks (accessed 2026-08-08)
[B10, B11] Apache Airflow Docs — Testing DAGs natively (accessed 2026-08-08)
