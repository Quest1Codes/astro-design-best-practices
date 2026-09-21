"""Per-job-type-family DAG task emitters, dispatched by `scaffold_dags.py`.

Each emitter module exposes `emit(job) -> EmittedTask` (see `base.py`). Adding a new job type is
adding one function to the matching family module (or a new module + a `FAMILY_EMITTERS` entry
below), not touching `scaffold_dags.py` itself.
"""
from __future__ import annotations

from . import core, database, file_transfer

FAMILY_EMITTERS = {
    "core": core.emit,
    "database": database.emit,
    "file-transfer": file_transfer.emit,
}
