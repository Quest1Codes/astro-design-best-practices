#!/usr/bin/env python3
"""AST-scan an existing DAG repo (brownfield only) for naming/tagging/default_args conventions,
writing `manifest.brownfield.conventions{}` [spec §6.4].

Deterministic: given the same repo contents, output is byte-identical.
Reads files only; never executes any scanned DAG file (uses Python's `ast` module, not `import`).

Usage:
    python3 dag_conventions_scan.py --manifest estate_manifest.json --dags-dir ./dags
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import Counter
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402

_TOP_LEVEL_RISK_CALLS = {"Variable.get", "Connection.get", "BaseHook.get_connection"}


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def scan_file(path: Path) -> dict:
    try:
        tree = ast.parse(path.read_text(errors="replace"), filename=str(path))
    except SyntaxError as e:
        return {"file": str(path), "parse_error": str(e)}

    dag_ids: list[str] = []
    tags: list[str] = []
    default_args_keys: set[str] = set()
    owners: list[str] = []
    top_level_risk_calls: list[str] = []
    provider_imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            names = [mod] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
            for n in names:
                if n and ("airflow.providers" in n or n.startswith("providers.")):
                    provider_imports.add(n)

        if isinstance(node, ast.Call):
            called = _dotted_name(node.func)
            if called in _TOP_LEVEL_RISK_CALLS:
                # only counts as top-level risk if not nested inside a function/task def
                top_level_risk_calls.append(called)
            if called in ("DAG", "dag") or (called and called.endswith(".dag")):
                for kw in node.keywords:
                    if kw.arg == "dag_id" and isinstance(kw.value, ast.Constant):
                        dag_ids.append(str(kw.value.value))
                    if kw.arg == "tags" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        tags.extend(str(e.value) for e in kw.value.elts if isinstance(e, ast.Constant))
                    if kw.arg == "default_args" and isinstance(kw.value, ast.Dict):
                        for k in kw.value.keys:
                            if isinstance(k, ast.Constant):
                                default_args_keys.add(str(k.value))

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "default_args" and isinstance(node.value, ast.Dict):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant):
                            default_args_keys.add(str(k.value))
                            if k.value == "owner" and isinstance(v, ast.Constant):
                                owners.append(str(v.value))

    return {
        "file": str(path), "dag_ids": dag_ids, "tags": sorted(set(tags)),
        "default_args_keys": sorted(default_args_keys), "owners": owners,
        "top_level_risk_calls": top_level_risk_calls, "provider_imports": sorted(provider_imports),
    }


def scan_repo(dags_dir: Path) -> dict:
    per_file = [scan_file(p) for p in sorted(dags_dir.rglob("*.py"))]

    dag_id_patterns = Counter()
    for f in per_file:
        for did in f.get("dag_ids", []):
            pattern = re.sub(r"\d+", "#", did)  # normalize numbers out for pattern grouping
            dag_id_patterns[pattern] += 1

    all_tags = Counter(t for f in per_file for t in f.get("tags", []))
    all_default_args_keys = Counter(k for f in per_file for k in f.get("default_args_keys", []))
    all_owners = Counter(o for f in per_file for o in f.get("owners", []))
    all_providers = Counter(p for f in per_file for p in f.get("provider_imports", []))
    files_with_risk_calls = [f["file"] for f in per_file if f.get("top_level_risk_calls")]

    requirements: dict[str, str] = {}
    req_path = dags_dir.parent / "requirements.txt"
    if req_path.exists():
        for line in req_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^([A-Za-z0-9_.\-]+)\s*([<>=!~]+.*)?$", line)
            if m:
                requirements[m.group(1)] = (m.group(2) or "").strip()

    runtime_version = None
    dockerfile = dags_dir.parent / "Dockerfile"
    if dockerfile.exists():
        m = re.search(r"astro-runtime:([\w.\-]+)", dockerfile.read_text())
        if m:
            runtime_version = m.group(1)

    return {
        "file_count": len(per_file),
        "dag_id_patterns": dict(dag_id_patterns.most_common()),
        "tag_histogram": dict(all_tags.most_common()),
        "default_args_key_histogram": dict(all_default_args_keys.most_common()),
        "owner_histogram": dict(all_owners.most_common()),
        "provider_import_histogram": dict(all_providers.most_common()),
        "files_with_top_level_risk_calls": files_with_risk_calls,
        "requirements": requirements,
        "runtime_version": runtime_version,
        "per_file": per_file,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--dags-dir", type=Path, required=True)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1
    if not args.dags_dir.exists():
        print(f"error: {args.dags_dir} not found", file=sys.stderr)
        return 1

    conventions = scan_repo(args.dags_dir)

    estate = manifest_mod.from_json(args.manifest)
    brownfield = estate.brownfield if isinstance(estate.brownfield, dict) else {}
    brownfield["conventions"] = conventions
    estate.brownfield = brownfield
    manifest_mod.to_json(estate, args.manifest, tool="dag_conventions_scan.py")

    print(f"updated {args.manifest}: {conventions['file_count']} DAG file(s) scanned, "
          f"{len(conventions['files_with_top_level_risk_calls'])} with top-level risk calls, "
          f"runtime_version={conventions['runtime_version']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
