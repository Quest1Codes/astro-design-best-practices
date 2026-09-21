"""Read-only access to the generated AutoSys 12.0 registries (JSON files in this directory)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_HERE = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    path = _HERE / name
    if not path.exists():
        raise FileNotFoundError(
            f"{name} missing -- run `python3 -m autosys_jil.registry.build_registry --corpus research/autosys-12.0`"
        )
    return json.loads(path.read_text())


def job_types() -> dict:
    return _load("job_types.json")


def attributes() -> dict:
    return _load("attributes.json")


def object_attributes() -> dict:
    return _load("object_attributes.json")


def states() -> dict:
    return _load("states.json")


def events() -> dict:
    return _load("events.json")


@lru_cache(maxsize=None)
def aliases() -> dict[str, str]:
    out: dict[str, str] = {}
    for code, spec in job_types().items():
        for a in spec.get("aliases", []):
            out[a.lower()] = code
    return out


def resolve_job_type(raw: str | None) -> tuple[str, bool]:
    """Return (canonical_code, known). Missing job_type defaults to CMD [AS p.2552]."""
    if raw is None or raw.strip() == "":
        return "CMD", True
    r = raw.strip()
    if r.lower() in aliases():
        return aliases()[r.lower()], True
    up = r.upper()
    if up in job_types():
        return up, True
    return up, False


def registry_version() -> str:
    """Stable identifier for the registry content (counts + first/last keys)."""
    jt, at = job_types(), attributes()
    return f"jt{len(jt)}-at{len(at)}"
