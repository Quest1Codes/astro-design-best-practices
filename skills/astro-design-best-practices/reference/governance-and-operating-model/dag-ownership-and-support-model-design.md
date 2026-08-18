# DAG-Ownership and Support-Model Design

In AutoSys, a central ops team "owned" all jobs. In Airflow at scale, every DAG needs an explicit, named owner — not just a team but a human or rotation who is accountable for on-call response. Undocumented ownership is the root cause of the most frustrating production incidents.

## Ownership Mechanics in Airflow

- **`owner` field in `default_args`**: Surfaced in the Airflow UI on the DAGs page and task list. Use a team alias (e.g., `finance-eng`) or individual user ID [B1].
- **`tags`**: Use consistent DAG tags to enable filtering across the UI: `env:prod`, `domain:finance`, `sla:critical`. Tags allow on-call engineers to quickly scope their view.
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
- Set SLAs at the task level using `sla` parameter in individual operators to alert *before* a deadline breach, not after [B1].

## Anti-Patterns to Avoid

| Anti-Pattern | Consequence |
|---|---|
| `owner = "airflow"` | Anonymous ownership — no one is accountable |
| Runbook in external Confluence page only | Page will be out of sync; ignored during incidents |
| DAG-level `email_on_failure` to a distribution list | Alert fatigue; no one takes ownership |

## Sources

[B1] Apache Airflow Docs — `owner` field, `tags`, `sla`, `on_failure_callback` (accessed 2026-08-11)
[B2] Airflow community best practices — `doc_md` runbook pattern (accessed 2026-08-11)
