#!/usr/bin/env python3
"""Scan a Kubernetes manifest export for the AutoSys-on-k8s -> Astronomer-on-k8s
control-plane parity checklist (reference/control-plane-parity.md).

Reads standard Kubernetes YAML (multi-document files are fine) from a
directory export -- no live cluster access needed. Produces one checklist row
per parity item with whatever objects were actually found; it does NOT decide
disposition (direct-port / needs-translation / superseded) -- that is a
human/agent judgment call per reference/control-plane-parity.md.

Requires PyYAML (pip install pyyaml).

Usage:
    python3 k8s_parity_scan.py --manifests-dir ./k8s-export --out k8s_parity_manifest.json
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(1)

CHECKLIST_ITEMS = {
    "namespace": {"kinds": {"Namespace"}, "reference": "control-plane-parity.md#namespaces"},
    "rbac": {"kinds": {"Role", "ClusterRole", "RoleBinding", "ClusterRoleBinding", "ServiceAccount"},
             "reference": "control-plane-parity.md#rbac-roles-rolebindings-serviceaccounts"},
    "network_policy": {"kinds": {"NetworkPolicy"}, "reference": "control-plane-parity.md#networkpolicies"},
    "workload": {"kinds": {"Deployment", "StatefulSet", "DaemonSet", "Pod", "Job", "CronJob"},
                 "reference": "control-plane-parity.md#resource-requestslimits"},
    "config": {"kinds": {"ConfigMap"}, "reference": "control-plane-parity.md#configmaps-and-secrets"},
    "secret": {"kinds": {"Secret"}, "reference": "control-plane-parity.md#configmaps-and-secrets"},
    "autoscaling": {"kinds": {"HorizontalPodAutoscaler", "ScaledObject"},
                     "reference": "control-plane-parity.md#autoscaling-hpa--custom-autoscalers--keda"},
    "ingress": {"kinds": {"Ingress"}, "reference": "control-plane-parity.md#ingress--external-access"},
}


def load_all_objects(manifests_dir: Path):
    objects = []
    warnings = []
    yaml_files = sorted(list(manifests_dir.rglob("*.yaml")) + list(manifests_dir.rglob("*.yml")))
    if not yaml_files:
        warnings.append(f"no .yaml/.yml files found under {manifests_dir}")
    for path in yaml_files:
        try:
            docs = list(yaml.safe_load_all(path.read_text()))
        except yaml.YAMLError as e:
            warnings.append(f"{path}: YAML parse error, skipped ({e})")
            continue
        for doc in docs:
            if not isinstance(doc, dict) or "kind" not in doc:
                continue
            objects.append({
                "kind": doc.get("kind"),
                "name": (doc.get("metadata") or {}).get("name", "<unnamed>"),
                "namespace": (doc.get("metadata") or {}).get("namespace"),
                "source_file": str(path.relative_to(manifests_dir)),
                "labels": (doc.get("metadata") or {}).get("labels", {}),
                "raw": doc,
            })
    return objects, warnings


def resource_limits_summary(objects):
    """Special-case check: do workload objects declare requests/limits at all."""
    findings = []
    for obj in objects:
        if obj["kind"] not in CHECKLIST_ITEMS["workload"]["kinds"]:
            continue
        containers = (
            obj["raw"].get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            if obj["kind"] in ("Deployment", "StatefulSet", "DaemonSet")
            else obj["raw"].get("spec", {}).get("containers", [])
        )
        for c in containers:
            resources = c.get("resources", {})
            has_requests = bool(resources.get("requests"))
            has_limits = bool(resources.get("limits"))
            if not (has_requests and has_limits):
                findings.append(
                    f"{obj['kind']}/{obj['name']} container '{c.get('name', '?')}' "
                    f"missing {'requests' if not has_requests else ''}"
                    f"{' and ' if not has_requests and not has_limits else ''}"
                    f"{'limits' if not has_limits else ''}"
                )
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifests-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if not args.manifests_dir.exists():
        print(f"error: {args.manifests_dir} not found", file=sys.stderr)
        sys.exit(1)

    objects, warnings = load_all_objects(args.manifests_dir)

    checklist = []
    for item_name, spec in CHECKLIST_ITEMS.items():
        found = [obj for obj in objects if obj["kind"] in spec["kinds"]]
        row = {
            "item": item_name,
            "reference": spec["reference"],
            "found_objects": [f"{o['kind']}/{o['name']}" + (f" (ns: {o['namespace']})" if o["namespace"] else "")
                               for o in found],
            "found_count": len(found),
            "disposition": "pending",
            "notes": None,
        }
        if item_name == "network_policy" and found:
            row["notes"] = (f"{len(found)} NetworkPolicy object(s) found -- review pod-selector labels "
                             "against Airflow's worker/scheduler labels before porting")
        elif item_name == "secret" and found:
            row["notes"] = ("Secret objects found -- re-home VALUES into the target secrets backend; "
                             "never copy the Kubernetes Secret object forward, see secrets-and-networkpolicy.md")
        elif item_name == "autoscaling" and found:
            row["notes"] = ("Autoscaling objects found -- use as evidence of workload burstiness only; "
                             "the target's executor/autoscaling choice is a separate decision, see "
                             "executor-and-autoscaling.md")
        elif not found:
            row["notes"] = (f"Nothing found for '{item_name}'. Confirm whether it genuinely wasn't needed "
                             "(e.g., a broader mechanism outside this manifest export covered the same intent) "
                             "or whether the export is incomplete -- do not assume either without checking.")
        checklist.append(row)

    resource_findings = resource_limits_summary(objects)
    if resource_findings:
        warnings.extend([f"resource requests/limits: {f}" for f in resource_findings])

    manifest = {
        "source_dir": str(args.manifests_dir),
        "object_count": len(objects),
        "objects_by_kind": {
            kind: len([o for o in objects if o["kind"] == kind])
            for kind in sorted({o["kind"] for o in objects})
        },
        "checklist": checklist,
        "warnings": warnings,
    }

    indent = 2 if args.pretty else None
    args.out.write_text(json.dumps(manifest, indent=indent))
    print(f"Wrote {args.out}: {len(objects)} objects scanned, {len(checklist)} checklist rows, "
          f"{len(warnings)} warnings", file=sys.stderr)
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
