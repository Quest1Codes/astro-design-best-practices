"""Shared types for per-family emitters."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EmittedTask:
    task_id: str
    code: str  # the task's Python source, already indented for insertion into a DAG body
    imports: list[str] = field(default_factory=list)  # extra import lines the DAG file needs
    todos: list[str] = field(default_factory=list)  # human-readable TODO markers this task needs


def _safe_task_id(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def generic_bash_stub(job, note: str) -> EmittedTask:
    """Fallback emitter for a family with no dedicated emitter yet: a @task.bash stub carrying
    the original command verbatim (already redacted by manifest.redact() upstream) plus a TODO
    naming what's unverified. Never used for REDESIGN/NONE units -- scaffold_dags.py refuses
    those before reaching any emitter."""
    task_id = _safe_task_id(job.name)
    command = (job.command or "").replace('"', '\\"')
    code = f'''
@task.bash(task_id="{task_id}")
def {task_id}():
    # TODO(JUDG:{note}): {job.job_type} has no dedicated emitter yet -- verify this command
    # against reference/job-types/*.md before trusting this stub.
    return "{command}"
'''
    return EmittedTask(task_id=task_id, code=code, todos=[f"{job.job_type} job {job.name!r}: {note}"])
