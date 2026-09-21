"""Core family: CMD [AS p.2550], CMDMACHINE. Per
reference/job-types/core-cmd-box.md. BOX is handled by scaffold_dags.py directly (it becomes a
TaskGroup or a DAG split, not a single task)."""
from __future__ import annotations

from .base import EmittedTask, _safe_task_id, generic_bash_stub


def emit(job) -> EmittedTask:
    if job.job_type == "CMD":
        task_id = _safe_task_id(job.name)
        command = (job.command or "").replace('"', '\\"')
        kwargs = []
        if job.sla.n_retrys:
            kwargs.append(f"retries={job.sla.n_retrys}")
        if job.sla.term_run_time:
            kwargs.append(f"execution_timeout=timedelta(seconds={job.sla.term_run_time})")
        kwargs_str = ", ".join(kwargs)
        code = f'''
@task.bash(task_id="{task_id}"{", " + kwargs_str if kwargs_str else ""})
def {task_id}():
    return "{command}"
'''
        return EmittedTask(task_id=task_id, code=code)
    # CMDMACHINE: PRACTITIONER JUDGMENT, not found in the 12.0 corpus -- always a stub.
    return generic_bash_stub(job, "cmdmachine-runtime-machine-selection-unverified")
