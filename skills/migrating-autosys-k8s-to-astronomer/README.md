# migrating-autosys-k8s-to-astronomer

A companion to `migrating-autosys-to-astronomer` for estates where AutoSys already runs containerized on Kubernetes. Because the substrate doesn't change (Kubernetes to Kubernetes), this migration is mostly control-plane and platform parity rather than an execution-topology decision — namespaces, RBAC, network policies, secrets, the executor/autoscaling model, CI/CD, and observability.

## Why this is separate from the on-prem-distributed skill

`migrating-autosys-onprem-distributed-to-astro-cloud` answers "where should this job's execution move to" for a fleet of VM-based agents. This skill starts from a different premise — the estate is already on Kubernetes — so the interesting questions are different: is the existing RBAC/NetworkPolicy model portable, does the existing autoscaling approach map to KEDA or Astro's managed autoscaling, and does the existing CI/CD pipeline (however JIL changes reach the cluster today) map cleanly to `astro deploy`.

## How it works

1. **Scan the existing k8s manifests**: [`scripts/k8s_parity_scan.py`](scripts/k8s_parity_scan.py) parses a YAML export of the AutoSys namespace(s) and checks it against a parity checklist ([`reference/control-plane-parity.md`](reference/control-plane-parity.md)) — namespaces, RBAC, NetworkPolicies, resource limits, Secrets/ConfigMaps, autoscaling objects.
2. **Classify and plan**: for each object found, decide direct-port / needs-translation / superseded. Pick the executor and autoscaling model from the actual workload shape ([`reference/executor-and-autoscaling.md`](reference/executor-and-autoscaling.md)), not a default.
3. **Trial** one namespace end to end: one migrated DAG running under the chosen executor, RBAC and network policy tested for real, CI/CD proven to actually deploy a change.
4. **Migrate** namespace by namespace / environment by environment, tracked by [`scripts/status.py`](scripts/status.py).
5. **Report**: full parity checklist with dispositions, executor decision and rationale, secrets map, CI/CD pipeline, observability mapping.

## Using it

```bash
kubectl get deployments,statefulsets,services,networkpolicies,configmaps,secrets,serviceaccounts,roles,rolebindings,hpa -n autosys -o yaml > k8s-export/autosys-namespace.yaml
claude "Use the migrating-autosys-to-astronomer skill on ~/estate.jil, then the migrating-autosys-k8s-to-astronomer skill against ./k8s-export to plan the platform migration"
```

## What the scan looks like

```
python3 scripts/k8s_parity_scan.py --manifests-dir ./k8s-export --out k8s_parity_manifest.json
```

produces one row per checklist item, each with what was actually found:

```json
{
  "item": "network_policy",
  "found_objects": ["NetworkPolicy/autosys-agent-egress"],
  "disposition": "pending",
  "notes": "1 NetworkPolicy object(s) found -- review pod-selector labels against Airflow's worker/scheduler labels before porting"
}
```

Rows with nothing found in the export are reported too (`found_objects: []`) — an absent NetworkPolicy, for instance, might mean "wasn't needed" or might mean "the export is incomplete"; the skill doesn't guess which.

## Status

First draft. `k8s_parity_scan.py` reads standard Kubernetes YAML (`kind`, `metadata`, `spec`) and needs no live cluster access — it works entirely from an export. Requires PyYAML (`pip install pyyaml`).
