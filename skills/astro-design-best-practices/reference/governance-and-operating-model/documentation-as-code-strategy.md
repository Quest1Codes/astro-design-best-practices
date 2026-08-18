# Documentation-as-Code Strategy

AutoSys documentation typically lived in Confluence, SharePoint, or Word documents — decoupled from the actual job definitions. This creates chronic drift: the documentation describes the old behavior, not what actually runs. Airflow's `doc_md` attribute solves this by co-locating documentation with the code that defines the pipeline.

## Core Principle: Documentation Lives in the DAG File

Airflow renders Markdown in the UI from the `doc_md` attribute on both DAGs and individual tasks [B1]. This makes the DAG file itself the runbook.

### DAG-Level Documentation

```python
"""
# Daily Finance Reconciliation
**Owner**: Finance Engineering
**Schedule**: Daily @ 01:00 UTC
**SLA**: Complete by 07:00 UTC

## What This Pipeline Does
Reconciles daily transactions from the trading platform against the GL.

## Recovery
All tasks are idempotent. Clear any failed task in the UI and re-run.
"""

with DAG(
    dag_id="finance_daily_reconciliation",
    doc_md=__doc__,
    ...
):
```

The Python module docstring becomes the DAG documentation — the same text visible in both the code review and the Airflow UI [B1].

### Task-Level Documentation

```python
validate_row_count = PythonOperator(
    task_id="validate_row_count",
    python_callable=check_counts,
    doc_md="""
    ### Row Count Validation
    Compares record count in staging vs. source.
    **Failure**: Source DB may be slow. Check RDS CloudWatch metrics.
    **Safe to retry**: Yes — idempotent.
    """,
)
```

## Standard Documentation Header (Enforce via Code Review)

All DAG files must include a standard header block as `doc_md` content covering:
1. **Purpose**: What business process does this pipeline serve?
2. **Owner**: Team alias and Slack channel.
3. **SLA**: Completion deadline.
4. **Dependencies**: What triggers this DAG? What does it depend on?
5. **Recovery**: Is it safe to retry? What manual steps are needed on failure?
6. **Impact if Fails**: Who is affected and how severely?

## Anti-Patterns

| Anti-Pattern | Consequence |
|---|---|
| Documentation only in Confluence | Chronically out of date; invisible during incidents |
| `doc_md` not set at all | On-call engineers have no context in the UI |
| Documentation in comments, not `doc_md` | Not rendered in the Airflow UI — invisible at runtime |

## Sources

[B1] Apache Airflow Docs — `doc_md` attribute for DAG and task documentation, Markdown rendering in Airflow UI (accessed 2026-08-11)
