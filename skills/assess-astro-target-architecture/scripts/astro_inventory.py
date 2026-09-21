#!/usr/bin/env python3
"""Parse customer-collected `astro` CLI JSON/YAML exports into `manifest.brownfield{}`
[spec §6.4].

Deterministic: given the same input files, output is byte-identical.
Reads files only; never runs `astro` itself or contacts a live Astro control plane -- the
customer collects these exports (`astro deployment list -o json`, `astro deployment inspect
-o yaml`, `astro workspace list -o json`) and hands them over, same read-only discipline as
every other assessment script.

Usage:
    python3 astro_inventory.py --manifest estate_manifest.json \\
        --deployments deployments.json [--deployment-details deploy1.yaml ...] \\
        --workspaces workspaces.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402


def load_json_or_yaml(path: Path):
    text = path.read_text()
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--deployments", type=Path, default=None, help="astro deployment list -o json")
    ap.add_argument("--deployment-details", type=Path, action="append", default=[],
                    help="astro deployment inspect -o yaml, repeatable, one per Deployment")
    ap.add_argument("--workspaces", type=Path, default=None, help="astro workspace list -o json")
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    deployments = load_json_or_yaml(args.deployments) if args.deployments and args.deployments.exists() else []
    details = [load_json_or_yaml(p) for p in args.deployment_details if p.exists()]
    workspaces = load_json_or_yaml(args.workspaces) if args.workspaces and args.workspaces.exists() else []

    runtime_versions = sorted({
        d.get("runtimeVersion") or d.get("runtime_version")
        for d in (deployments if isinstance(deployments, list) else [])
        if isinstance(d, dict) and (d.get("runtimeVersion") or d.get("runtime_version"))
    })
    executors = sorted({
        d.get("executor") for d in (deployments if isinstance(deployments, list) else [])
        if isinstance(d, dict) and d.get("executor")
    })

    brownfield = {
        "deployments": deployments,
        "deployment_details": details,
        "workspaces": workspaces,
        "summary": {
            "deployment_count": len(deployments) if isinstance(deployments, list) else 0,
            "workspace_count": len(workspaces) if isinstance(workspaces, list) else 0,
            "runtime_versions_in_use": runtime_versions,
            "executors_in_use": executors,
        },
    }

    estate = manifest_mod.from_json(args.manifest)
    existing = estate.brownfield if isinstance(estate.brownfield, dict) else {}
    existing.update(brownfield)
    estate.brownfield = existing
    manifest_mod.to_json(estate, args.manifest, tool="astro_inventory.py")

    print(f"updated {args.manifest}: {brownfield['summary']['deployment_count']} deployment(s), "
          f"{brownfield['summary']['workspace_count']} workspace(s), "
          f"runtime versions {runtime_versions}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
