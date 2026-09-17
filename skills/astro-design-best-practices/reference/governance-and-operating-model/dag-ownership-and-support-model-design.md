# DAG-Ownership and Support-Model Design

In AutoSys, a central ops team "owned" all jobs. In Airflow at scale, every DAG needs an explicit, named owner — not just a team but a human or rotation who is accountable for on-call response. Undocumented ownership is the root cause of the most frustrating production incidents.

## Ownership Mechanics in Airflow

- **`owner` field in `default_args`**: Surfaced in the Airflow UI on the DAGs page and task list. Use a team alias (e.g., `finance-eng`) or individual user ID [B1].
- **`tags`**: Use consistent DAG tags to enable filtering across the UI: `env:prod`, `domain:finance`, `sla:critical` [B1]. Tags allow on-call engineers to quickly scope their view.
- **`doc_md`**: Embed the runbook and ownership contact directly in the DAG's Markdown documentation (rendered in the Airflow UI) [B1][B2].

## Runbook Standard — What Every Critical DAG Must Document

The runbook lives in the DAG's `doc_md` attribute so it is always co-located with the code [B2]:

```python
"""
# Daily Finance Reconciliation DAG
**Owner**: Finance Engineering (finance-eng@company.com)
**On-call channel**: #finance-data-alerts
**SLA**: Must complete by 07:00 UTC

## Impact if Fails
Downstream BI dashboards show stale data; compliance team misses daily reconciliation window.

## Troubleshooting
1. Check if source DB (finance-rds-prod) is reachable.
2. Verify the upstream extraction DAG `finance_extract` completed successfully.
3. All tasks are idempotent — safe to clear and re-run.

## Escalation
Finance Data Lead → VP Engineering
"""
```

## Alert Design

- Every critical DAG must use `on_failure_callback` to fire an alert (PagerDuty or Slack) at the task level — not just at DAG level — so the on-call engineer knows exactly which step failed [B1].
- Include `dag_id`, `task_id`, `execution_date`, and a direct link to the runbook in every alert message.
- **Correction — this was actionable code advice that would break on the target platform**: an earlier draft of this bullet instructed setting SLAs "at the task level using `sla` parameter in individual operators," citing [B1] — but [B1]'s own source note, in this same file's Sources section, explicitly says `sla`/`sla_miss_callback` was removed in Airflow 3 and "don't cite it as current for Airflow 3 Deployments." The body never reflected that caveat. On Airflow 3 / Astro, use Deadline Alerts (Airflow 3.1+) or Astro Alerts' Task Duration/Timeliness alerts instead — see `reference/scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md` elsewhere in this skill for the full replacement pattern [B3].

## Anti-Patterns to Avoid

| Anti-Pattern | Consequence |
|---|---|
| `owner = "airflow"` | Anonymous ownership — no one is accountable |
| Runbook in external Confluence page only | Page will be out of sync; ignored during incidents |
| DAG-level `email_on_failure` to a distribution list | Alert fatigue; no one takes ownership |

## Sources

[B1] Astronomer Learn — Airflow DAG parameters, UI parameters (`tags`) and callback parameters (`on_failure_callback`): https://www.astronomer.io/docs/learn/airflow-dag-parameters#ui-parameters (tier 1, added on doc-verification review); callback parameters: https://www.astronomer.io/docs/learn/airflow-dag-parameters#callback-parameters (tier 1, added on doc-verification review). Note: `sla`/`sla_miss_callback` was removed in Airflow 3 (see `dag-level-sla-and-catchup-backfill-policy.md` elsewhere in this skill) — don't cite it as current for Airflow 3 Deployments.
[B2] Astronomer Learn — Add custom documentation to your Airflow UI (`doc_md` pattern): https://www.astronomer.io/docs/learn/custom-airflow-ui-docs-tutorial#step-3-add-docs-to-your-dag (tier 1, added on doc-verification review)
[B3] Astronomer Docs — Deadline alerts (Airflow 3.1+ SLA replacement) and Astro Alerts Task Duration/Timeliness alerts: https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html and https://www.astronomer.io/docs/astro/alerts (tier 1/2, added on Critic-pass review — replaces the removed `sla` parameter above)
