"""File-transfer family: FTP, SCP. Per reference/job-types/file-transfer-ftp-scp.md."""
from __future__ import annotations

from .base import EmittedTask, _safe_task_id


def emit(job) -> EmittedTask:
    task_id = _safe_task_id(job.name)
    command = (job.command or "").replace('"', '\\"')
    code = f'''
@task(task_id="{task_id}")
def {task_id}():
    # TODO(JUDG:protocol-confirm): confirm SFTP is an acceptable target for {job.job_type} with
    # the platform/security team (reference/job-types/file-transfer-ftp-scp.md).
    # TODO(JUDG:secrets-backend): wire a real Connection ID, never a literal credential.
    # Original: {command}
    SFTPOperator(
        task_id="{task_id}_transfer",
        ssh_conn_id="TODO_set_connection_id",
        local_filepath="TODO", remote_filepath="TODO",
        operation="TODO_get_or_put",
    )
'''
    return EmittedTask(task_id=task_id, code=code,
                       imports=["from airflow.providers.sftp.operators.sftp import SFTPOperator"],
                       todos=[f"{job.job_type} job {job.name!r}: protocol confirm + connection + paths needed"])
