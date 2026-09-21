"""Database family: SQL, DBPROC [AS p.2549, p.2551]. Per
reference/job-types/database-sql-dbproc-dbmon-dbtrig-sqlagent.md. DBMON/DBTRIG/SQLAGENT are
JUDG-heavier (sensor/CDC decisions) and fall through to the generic stub until a real customer
export justifies a dedicated emitter."""
from __future__ import annotations

from .base import EmittedTask, _safe_task_id, generic_bash_stub


def emit(job) -> EmittedTask:
    if job.job_type in ("SQL", "DBPROC"):
        task_id = _safe_task_id(job.name)
        command = (job.command or "").replace('"', '\\"')
        code = f'''
@task(task_id="{task_id}")
def {task_id}():
    # TODO(JUDG:sql-connection): wire a real Connection ID for the target secrets backend --
    # this stub carries the original command as a comment for reference, not as executable SQL.
    # Original: {command}
    hook = SQLExecuteQueryOperator(
        task_id="{task_id}_query",
        conn_id="TODO_set_connection_id",
        sql="-- TODO(JUDG:sql-body): port the original SQL/procedure call here",
    )
'''
        return EmittedTask(task_id=task_id, code=code,
                           imports=["from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator"],
                           todos=[f"SQL job {job.name!r}: connection ID and SQL body need to be filled in"])
    return generic_bash_stub(job, "no-dedicated-emitter-for-dbmon-dbtrig-sqlagent-yet")
