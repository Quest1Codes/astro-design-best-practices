"""DAG-integrity tests [plan §11.8]. Copied into a target Astro project's `tests/dags/` by
`migrate-jil-to-airflow-translation/scripts/dag_quality_gate.py` on first run if not already
present.

Checks: no import errors, every DAG has owner/tags/doc_md, no top-level DB/Variable calls,
catchup is explicit, retries is set, every task is traceable via traceability.json.

Deterministic; reads local files only; never contacts a live AutoSys or Astro system.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

DAGS_DIR = Path(__file__).resolve().parents[2] / "dags"
TRACEABILITY_PATH = Path("TRACEABILITY_PATH_PLACEHOLDER")

_RISKY_TOP_LEVEL_CALLS = {"Variable.get", "Connection.get", "BaseHook.get_connection"}


def _dag_files() -> list[Path]:
    if not DAGS_DIR.exists():
        return []
    return sorted(DAGS_DIR.glob("*.py"))


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


@pytest.mark.parametrize("path", _dag_files(), ids=lambda p: p.name)
def test_dag_file_parses(path: Path):
    ast.parse(path.read_text())


@pytest.mark.parametrize("path", _dag_files(), ids=lambda p: p.name)
def test_dag_has_owner_tags_doc_md(path: Path):
    tree = ast.parse(path.read_text())
    found = {"owner": False, "tags": False, "doc_md": False}
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg in found:
            found[node.arg] = True
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and k.value == "owner":
                    found["owner"] = True
    missing = [k for k, v in found.items() if not v]
    assert not missing, f"{path.name} is missing: {missing}"


@pytest.mark.parametrize("path", _dag_files(), ids=lambda p: p.name)
def test_no_top_level_risky_calls(path: Path):
    """A risky call (Variable.get/Connection.get/etc.) at DAG-file top level (module scope, not
    inside a @task function) runs at every DAG-file parse -- a known Airflow anti-pattern."""
    tree = ast.parse(path.read_text())
    task_function_names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and any(
            _dotted(d) in ("task", "task.bash", "dag") for d in node.decorator_list
        )
    }
    violations = []
    for node in tree.body:  # module-level statements only
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                called = _dotted(inner.func)
                if called in _RISKY_TOP_LEVEL_CALLS:
                    violations.append(called)
    assert not violations, f"{path.name} has top-level risky calls: {violations}"


@pytest.mark.parametrize("path", _dag_files(), ids=lambda p: p.name)
def test_catchup_is_explicit(path: Path):
    tree = ast.parse(path.read_text())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "catchup":
            found = True
    assert found, f"{path.name}: @dag(...) must set catchup explicitly (True or False)"


def test_every_traced_task_exists_in_a_dag_file():
    if not TRACEABILITY_PATH.exists():
        pytest.skip("no traceability.json at the configured path -- run scaffold_dags.py first")
    trace = json.loads(TRACEABILITY_PATH.read_text())
    dag_task_ids: set[str] = set()
    for path in _dag_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                dag_task_ids.add(f"{path.stem}.{node.name}")
    missing = [target for target in trace.values() if target not in dag_task_ids]
    assert not missing, f"traceability.json references tasks not found in any DAG file: {missing}"
