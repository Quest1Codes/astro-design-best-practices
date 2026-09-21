#!/usr/bin/env python3
"""Generate a Terraform skeleton (Astro provider resources) from `manifest.architecture`
[spec §7.5].

Deterministic: given the same manifest, output is byte-identical.
Reads the manifest and writes local `.tf` files only; never contacts a live Astro control plane
or applies anything -- this is a skeleton for a human to review and `terraform apply` themselves.

Every value needing human input (API tokens, exact naming approval, existing-resource IDs for a
brownfield import) is marked with a `# HUMAN INPUT REQUIRED` comment, never a fabricated
placeholder value that looks real.

Usage:
    python3 generate_terraform_skeleton.py --manifest estate_manifest.json --out terraform/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402

_WORKSPACE_TF = '''# HUMAN INPUT REQUIRED: confirm this naming convention against
# reference/workspaces-and-deployments.md and any existing dag_conventions_scan.py findings.
resource "astro_workspace" "{tf_name}" {{
  name        = "{name}"
  description = "Migrated from AutoSys instance {instance}"
}}
'''

_DEPLOYMENT_TF = '''resource "astro_deployment" "{tf_name}" {{
  name          = "{name}"
  workspace_id  = astro_workspace.{workspace_tf_name}.id
  executor      = "{executor}"  # from manifest.architecture.decisions.executor
  # HUMAN INPUT REQUIRED: confirm worker queue names/sizes against
  # manifest.architecture.sizing.worker_fleet (basis: {worker_fleet_basis})
  scheduler_size = "{scheduler_size}"
}}
'''

_TEAM_TF_HEADER = '''# HUMAN INPUT REQUIRED: cross-check against rbac_map.py's proposal
# (reference/identity-and-rbac.md) before applying -- this is a structural skeleton only.
'''

_API_TOKEN_TF = '''# HUMAN INPUT REQUIRED: create manually via the Astro UI/CLI; do not commit a real
# token value to source control. This resource block is a placeholder for where the reference
# would go once created.
# resource "astro_api_token" "{tf_name}" {{ ... }}
'''


def _tf_safe(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def generate(estate) -> dict[str, str]:
    arch = estate.architecture if isinstance(estate.architecture, dict) else {}
    decisions = arch.get("decisions", {})
    sizing = arch.get("sizing", {})
    executor = decisions.get("executor", {}).get("choice", "CeleryExecutor")
    scheduler_size = sizing.get("scheduler_size", {}).get("value", "small")
    worker_fleet = sizing.get("worker_fleet", {})

    files: dict[str, str] = {}
    for inst_id in estate.instances:
        ws_name = f"{inst_id.lower()}-migrated"
        ws_tf_name = _tf_safe(ws_name)
        files[f"workspace_{ws_tf_name}.tf"] = _WORKSPACE_TF.format(
            tf_name=ws_tf_name, name=ws_name, instance=inst_id)

        for env in ("dev", "staging", "prod"):
            dep_name = f"{inst_id.lower()}-{env}"
            dep_tf_name = _tf_safe(dep_name)
            files[f"deployment_{dep_tf_name}.tf"] = _DEPLOYMENT_TF.format(
                tf_name=dep_tf_name, name=dep_name, workspace_tf_name=ws_tf_name,
                executor=executor, scheduler_size=scheduler_size,
                worker_fleet_basis=worker_fleet.get("basis", "not sized yet"))

    files["teams.tf"] = _TEAM_TF_HEADER
    files["api_tokens.tf"] = _API_TOKEN_TF.format(tf_name="placeholder")
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    if not estate.architecture:
        print("error: manifest has no architecture{} -- run recommend_architecture.py/size_target.py first",
              file=sys.stderr)
        return 1

    files = generate(estate)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (args.out / name).write_text(content)

    print(f"wrote {len(files)} Terraform file(s) to {args.out} -- review every "
          f"'HUMAN INPUT REQUIRED' comment before applying", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
